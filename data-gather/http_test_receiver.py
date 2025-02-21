import time
import argparse
import json
import signal
import sys
import os
from aiohttp import web
import asyncio

class AsyncHttpReceiver:
    def __init__(self, port=8080, message_count=0, duration=0):
        self.port = port
        self.message_count = message_count
        self.duration = duration
        self.running = True
        self.received_messages = 0
        self.timestamps = []
        self.start_time = None
        self.lock = asyncio.Lock()
        self.app_runner = None
        self.shutdown_event = asyncio.Event()
        
    async def handle_message(self, request):
        timestamp = time.time_ns()
        
        async with self.lock:
            self.received_messages += 1
            self.timestamps.append(timestamp)
            
            if self.received_messages % 1000 == 0:
                elapsed = time.time() - self.start_time if self.start_time else 0
                rate = self.received_messages / elapsed if elapsed > 0 else 0
                print(f"Received {self.received_messages} messages, rate: {rate:.2f} msgs/sec")
                
            if self.message_count > 0 and self.received_messages >= self.message_count:
                # Don't call shutdown directly from request handler
                asyncio.create_task(self.trigger_shutdown())
        
        return web.json_response({"status": "ok"})
    
    async def trigger_shutdown(self):
        # Just set the event, don't stop the loop
        self.shutdown_event.set()
        
    async def shutdown_server(self):
        """Graceful server shutdown"""
        if not self.running:
            return
            
        print("Shutting down server gracefully...")
        self.running = False
        
        # First generate the report
        self.generate_report()
        
        # Then cleanup the runner if it exists
        if self.app_runner:
            await self.app_runner.cleanup()
    
    async def monitor_duration(self):
        """Monitor duration limit"""
        if self.duration <= 0:
            return
            
        await asyncio.sleep(self.duration)
        if self.running:
            print(f"Duration limit of {self.duration}s reached")
            await self.trigger_shutdown()
    
    def register_signals(self):
        """Cross-platform signal handling"""
        def signal_handler(*args):
            print("\nInterrupted by user. Shutting down...")
            if asyncio.get_event_loop().is_running():
                asyncio.create_task(self.trigger_shutdown())
                
        # Register for SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def generate_report(self):
        """Generate receiver report file"""
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
    
    async def setup_routes(self, app):
        """Configure server routes"""
        app.add_routes([
            web.post('/', self.handle_message),
            web.post('/message', self.handle_message),
        ])
    
    async def run_server(self):
        """Run the HTTP server"""
        # Create application
        app = web.Application(client_max_size=1024*1024)
        await self.setup_routes(app)
        
        # Register signal handlers
        self.register_signals()
        
        # Start the server
        self.app_runner = web.AppRunner(app)
        await self.app_runner.setup()
        site = web.TCPSite(self.app_runner, '0.0.0.0', self.port)
        
        self.start_time = time.time()
        print(f"HTTP receiver listening on port {self.port}")
        await site.start()
        
        # Start the duration monitor if needed
        if self.duration > 0:
            duration_task = asyncio.create_task(self.monitor_duration())
        
        # Wait until shutdown is triggered
        await self.shutdown_event.wait()
        
        # Clean shutdown
        await self.shutdown_server()

async def main():
    parser = argparse.ArgumentParser(description="Graceful Shutdown HTTP Test Receiver")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to receive (0 for infinite)")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")
    
    args = parser.parse_args()
    
    receiver = AsyncHttpReceiver(
        port=args.port,
        message_count=args.count,
        duration=args.time
    )
    
    await receiver.run_server()

if __name__ == "__main__":
    asyncio.run(main())