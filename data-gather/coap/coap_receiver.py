import time
import argparse
import json
import signal
import sys
import asyncio
from aiocoap import Context, Message, Code, resource

class CoapReceiver(resource.Resource):
    def __init__(self, host, port, resource_path, message_count=0, duration=0):
        super().__init__()
        self.host = host
        self.port = port
        self.resource_path = resource_path
        self.message_count = message_count
        self.duration = duration
        self.received_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True

    async def render_post(self, request):
        if not self.running:
            return Message(code=Code.SERVICE_UNAVAILABLE)

        timestamp = time.time_ns()
        self.received_messages += 1
        self.timestamps.append(timestamp)

        if self.received_messages % 1000 == 0:
            elapsed = time.time() - self.start_time if self.start_time else 0
            rate = self.received_messages / elapsed if elapsed > 0 else 0
            print(f"Received {self.received_messages} messages, rate: {rate:.2f} msgs/sec")

        if self.message_count > 0 and self.received_messages >= self.message_count:
            self.stop()

        return Message(code=Code.CONTENT, payload=b"OK")

    def stop(self):
        if not self.running:
            return

        print("Stopping receiver...")
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
            msgs_per_sec = self.received_messages / time_elapsed

        print(f"\nReceived {self.received_messages} messages in {time_elapsed:.2f} seconds")
        print(f"Average rate: {msgs_per_sec:.2f} messages/second")

        report = {
            "total_received": self.received_messages,
            "timestamps": self.timestamps,
            "start_time": self.timestamps[0] if self.timestamps else 0,
            "end_time": self.timestamps[-1] if self.timestamps else 0,
            "avg_rate_per_sec": msgs_per_sec
        }

        with open("receiver_report.txt", "w") as f:
            json.dump(report, f, indent=2)

        print(f"Receiver report generated. Total messages received: {self.received_messages}")

    async def run_server(self):
        self.start_time = time.time()
        root = resource.Site()
        root.add_resource((self.resource_path,), self)

        context = await Context.create_server_context(root, bind=(self.host, self.port))
        print(f"CoAP receiver listening on coap://{self.host}:{self.port}/{self.resource_path}")

        if self.duration > 0:
            await asyncio.sleep(self.duration)
            self.stop()

        while self.running:
            await asyncio.sleep(0.1)

def signal_handler(sig, frame):
    print("\nInterrupted by user. Shutting down...")
    receiver.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoAP Receiver")
    parser.add_argument("--host", default="localhost", help="CoAP server host")
    parser.add_argument("--port", type=int, default=5683, help="CoAP server port")
    parser.add_argument("--resource", default="test", help="CoAP resource path")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to receive (0 for infinite)")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")

    args = parser.parse_args()

    receiver = CoapReceiver(
        host=args.host,
        port=args.port,
        resource_path=args.resource,
        message_count=args.count,
        duration=args.time
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(receiver.run_server())