import time
import argparse
import json
import asyncio
import signal
from aiocoap import Context, Message, Code, resource

class CoapReceiver(resource.Resource):
    def __init__(self, host, port, resource_path, message_count=0, duration=0):
        super().__init__()
        self.host = host
        self.port = port
        self.resource_path = resource_path
        self.message_count = message_count
        self.duration = duration
        self.running = True
        self.received_messages = 0
        self.timestamps = []
        self.start_time = None
        self.context = None
        self.loop = asyncio.get_event_loop()
        self.shutdown_event = asyncio.Event()

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
            asyncio.create_task(self.trigger_shutdown())

        return Message(code=Code.CONTENT, payload=b"OK")

    async def trigger_shutdown(self):
        self.shutdown_event.set()

    async def shutdown_server(self):
        """Graceful server shutdown"""
        if not self.running:
            return

        print("Shutting down server gracefully...")
        self.running = False

        # Generate the report
        self.generate_report()

        # Shut down the CoAP context
        if self.context:
            await self.context.shutdown()
            self.context = None

    def register_signals(self):
        """Register signal handlers using the event loop"""
        def signal_handler():
            print("\nInterrupted by user. Shutting down...")
            asyncio.create_task(self.trigger_shutdown())

        self.loop.add_signal_handler(signal.SIGINT, signal_handler)
        self.loop.add_signal_handler(signal.SIGTERM, signal_handler)

    def generate_report(self):
        """Generate receiver report file"""
        time_elapsed = 0
        if len(self.timestamps) >= 2:
            first_ts = self.timestamps[0]
            last_ts = self.timestamps[-1]
            time_elapsed = (last_ts - first_ts) / 1_000_000_000

        msgs_per_sec = self.received_messages / time_elapsed if time_elapsed > 0 else 0

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

    async def monitor_duration(self):
        """Monitor duration limit"""
        if self.duration <= 0:
            return

        await asyncio.sleep(self.duration)
        if self.running:
            print(f"Duration limit of {self.duration}s reached")
            await self.trigger_shutdown()

    async def run_server(self):
        """Run the CoAP server"""
        # Create and start the server
        root = resource.Site()
        root.add_resource((self.resource_path,), self)
        
        self.context = await Context.create_server_context(root, bind=(self.host, self.port))
        
        self.start_time = time.time()
        print(f"CoAP receiver listening on coap://{self.host}:{self.port}/{self.resource_path}")

        # Register signal handlers
        self.register_signals()

        # Start the duration monitor if needed
        if self.duration > 0:
            asyncio.create_task(self.monitor_duration())

        # Wait until shutdown is triggered
        await self.shutdown_event.wait()

        # Perform cleanup
        await self.shutdown_server()

        # Stop the event loop
        self.loop.stop()

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

    asyncio.run(receiver.run_server())