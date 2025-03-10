import time
import argparse
import json
import signal
import sys
import asyncio
from aiocoap import Context, Message, Code
from datetime import datetime

class CoapSender:
    def __init__(self, host, port, resource, message_count=0, concurrency=1, duration=0, rate=0, payload_size=100):
        self.host = host
        self.port = port
        self.resource = resource
        self.message_count = message_count
        self.concurrency = concurrency
        self.duration = duration
        self.rate = rate
        self.payload_size = payload_size
        self.sent_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True
        self.lock = asyncio.Lock()

    def generate_payload(self, seq):
        sensor_data = {
            "device_id": "sensor-0042",
            "seq": seq,
            "timestamp": datetime.now().isoformat(),
            "readings": {
                "temperature": 13,
                "humidity": 89,
                "pressure": 4,
                "battery": 67,
                "rssi": 0
            },
            "status": {
                "error_code": 0,
                "mode": "normal"
            }
        }
        base_payload = json.dumps(sensor_data)
        current_size = len(base_payload.encode('utf-8'))
        padding_size = max(0, self.payload_size - current_size)
        if padding_size > 0:
            sensor_data["padding"] = "x" * padding_size
        return json.dumps(sensor_data).encode('utf-8')

    async def send_messages(self):
        context = await Context.create_client_context()
        task_start_time = time.time()
        local_seq = 0
        delay = 1.0 / self.rate if self.rate > 0 else 0

        while self.running:
            async with self.lock:
                if self.message_count > 0 and self.sent_messages >= self.message_count:
                    await self.stop()
                    break

                timestamp = time.time_ns()
                self.sent_messages += 1
                self.timestamps.append(timestamp)
                
                payload = self.generate_payload(self.sent_messages)
                request = Message(code=Code.POST, 
                                uri=f"coap://{self.host}:{self.port}/{self.resource}", 
                                payload=payload)
                try:
                    response = await asyncio.wait_for(context.request(request).response, timeout=2)
                    if response.code != Code.CONTENT:
                        print(f"Unexpected response code: {response.code}")
                except asyncio.TimeoutError:
                    print("Request timed out")
                    continue
                except Exception as e:
                    print(f"Error sending message: {e}")
                    continue
                
                local_seq += 1

                if self.sent_messages % 1000 == 0:
                    elapsed = time.time() - self.start_time if self.start_time else 0
                    rate = self.sent_messages / elapsed if elapsed > 0 else 0
                    print(f"Sent {self.sent_messages} messages, rate: {rate:.2f} msgs/sec")

            if self.rate > 0:
                expected_time = task_start_time + (local_seq / self.rate)
                current_time = time.time()
                sleep_time = max(0, expected_time - current_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0.001)

    async def stop(self):
        if not self.running:
            return

        print("Stopping sender...")
        self.running = False
        self.generate_report()

    def generate_report(self):
        time_elapsed = 0
        if len(self.timestamps) >= 2:
            first_ts = self.timestamps[0]
            last_ts = self.timestamps[-1]
            time_elapsed = (last_ts - first_ts) / 1_000_000_000

        msgs_per_sec = self.sent_messages / time_elapsed if time_elapsed > 0 else 0

        print(f"\nSent {self.sent_messages} messages in {time_elapsed:.2f} seconds")
        print(f"Average rate: {msgs_per_sec:.2f} messages/second")

        report = {
            "total_sent": self.sent_messages,
            "timestamps": self.timestamps,
            "start_time": self.timestamps[0] if self.timestamps else 0,
            "end_time": self.timestamps[-1] if self.timestamps else 0,
            "avg_rate_per_sec": msgs_per_sec
        }

        with open("sender_report.txt", "w") as f:
            json.dump(report, f, indent=2)

        print(f"Sender report generated. Total messages sent: {self.sent_messages}")

    async def run(self):
        self.start_time = time.time()
        tasks = []
        
        if self.rate > 0 and self.duration > 0:
            self.message_count = int(self.rate * self.duration * self.concurrency)

        for _ in range(self.concurrency):
            task = asyncio.create_task(self.send_messages())
            tasks.append(task)

        if self.duration > 0 and (self.rate == 0 or self.message_count == 0):
            await asyncio.sleep(self.duration)
            await self.stop()

        await asyncio.gather(*tasks)

def signal_handler(sender):
    async def async_shutdown():
        await sender.stop()
    asyncio.run_coroutine_threadsafe(async_shutdown(), asyncio.get_event_loop())
    time.sleep(1)
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoAP Sender")
    parser.add_argument("--host", default="localhost", help="CoAP server host")
    parser.add_argument("--port", type=int, default=5683, help="CoAP server port")
    parser.add_argument("--resource", default="test", help="CoAP resource path")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to send (0 for infinite)")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent senders")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")
    parser.add_argument("--rate", type=float, default=0, help="Messages per second per task")
    parser.add_argument("--payload-size", type=int, default=100, help="Size of payload in bytes")

    args = parser.parse_args()

    sender = CoapSender(
        host=args.host,
        port=args.port,
        resource=args.resource,
        message_count=args.count,
        concurrency=args.concurrency,
        duration=args.time,
        rate=args.rate,
        payload_size=args.payload_size
    )

    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sender))
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sender))

    asyncio.run(sender.run())