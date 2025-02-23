import time
import argparse
import json
import signal
import sys
import asyncio
from aiocoap import Context, Message, Code

class CoapSender:
    def __init__(self, host, port, resource, message_count=0, concurrency=1, duration=0):
        self.host = host
        self.port = port
        self.resource = resource
        self.message_count = message_count
        self.concurrency = concurrency
        self.duration = duration
        self.sent_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True

    async def send_messages(self):
        context = await Context.create_client_context()

        while self.running:
            if self.message_count > 0 and self.sent_messages >= self.message_count:
                self.stop()
                break

            timestamp = time.time_ns()
            self.sent_messages += 1
            self.timestamps.append(timestamp)

            request = Message(code=Code.POST, uri=f"coap://{self.host}:{self.port}/{self.resource}", payload=b"Hello")
            await context.request(request).response

            if self.sent_messages % 1000 == 0:
                elapsed = time.time() - self.start_time if self.start_time else 0
                rate = self.sent_messages / elapsed if elapsed > 0 else 0
                print(f"Sent {self.sent_messages} messages, rate: {rate:.2f} msgs/sec")

            await asyncio.sleep(0.001)

    def stop(self):
        if not self.running:
            return

        print("Stopping sender...")
        self.running = False
        self.generate_report()
        sys.exit(0)

    def generate_report(self):
        time_elapsed = 0
        if len(self.timestamps) >= 2:
            first_ts = self.timestamps[0]
            last_ts = self.timestamps[-1]
            time_elapsed = (last_ts - first_ts) / 1_000_000_000

        msgs_per_sec = 0
        if time_elapsed > 0:
            msgs_per_sec = self.sent_messages / time_elapsed

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

        for _ in range(self.concurrency):
            task = asyncio.create_task(self.send_messages())
            tasks.append(task)

        if self.duration > 0:
            await asyncio.sleep(self.duration)
            self.stop()

        await asyncio.gather(*tasks)

def signal_handler(sig, frame):
    print("\nInterrupted by user. Shutting down...")
    sender.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoAP Sender")
    parser.add_argument("--host", default="localhost", help="CoAP server host")
    parser.add_argument("--port", type=int, default=5683, help="CoAP server port")
    parser.add_argument("--resource", default="test", help="CoAP resource path")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to send (0 for infinite)")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent senders")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")

    args = parser.parse_args()

    sender = CoapSender(
        host=args.host,
        port=args.port,
        resource=args.resource,
        message_count=args.count,
        concurrency=args.concurrency,
        duration=args.time
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(sender.run())