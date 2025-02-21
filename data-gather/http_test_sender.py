import asyncio
import time
import argparse
import json
import signal
import sys
from datetime import datetime
import aiohttp

class AsyncHttpSender:
    def __init__(self, target_url, message_count=0, duration=0, payload_size=100, concurrency=100):
        self.target_url = target_url
        self.message_count = message_count
        self.duration = duration
        self.payload_size = payload_size
        self.concurrency = concurrency
        self.sent_messages = 0
        self.timestamps = []
        self.running = True
        self.semaphore = None  # Will be initialized in run()
        
    def generate_payload(self, seq):
        """Generate realistic sensor data payload"""
        # Simulate temperature sensor data
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
        return sensor_data
    
    async def send_message(self, session, seq):
        """Send a single message and record timestamp"""
        if not self.running:
            return
            
        payload = self.generate_payload(seq)
        
        async with self.semaphore:
            start_time = time.time_ns()
            try:
                async with session.post(self.target_url, json=payload, timeout=2) as response:
                    if response.status == 200:
                        self.sent_messages += 1
                        self.timestamps.append(start_time)
                    else:
                        print(f"Error sending message: HTTP {response.status}")
            except Exception as e:
                # Just continue, don't print every error to avoid console spam at high rates
                pass
    
    async def run(self):
        """Run the sender according to specified parameters"""
        signal.signal(signal.SIGINT, self.handle_interrupt)
        
        # Create connection pool and semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.concurrency)
        
        conn = aiohttp.TCPConnector(limit=self.concurrency, force_close=False, 
                                   limit_per_host=self.concurrency)
        
        timeout = aiohttp.ClientTimeout(total=5, connect=1, sock_connect=1, sock_read=1)
        
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            start_time = time.time()
            seq = 0
            tasks = []
            
            # Run until conditions are met
            while self.running:
                # Check if message count limit reached
                if self.message_count > 0 and seq >= self.message_count:
                    break
                    
                # Check if duration limit reached
                if self.duration > 0 and (time.time() - start_time) >= self.duration:
                    break
                
                # Schedule message sending
                task = asyncio.create_task(self.send_message(session, seq))
                tasks.append(task)
                seq += 1
                
                # Periodically report progress 
                if seq % 1000 == 0:
                    print(f"Scheduled {seq} messages, sent {self.sent_messages} so far")
                
                # Periodically clean up completed tasks
                if len(tasks) > 1000:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
            
            # Wait for all pending tasks to complete
            if tasks:
                await asyncio.wait(tasks)
                
        self.generate_report()
    
    def handle_interrupt(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nInterrupted by user. Shutting down...")
        self.running = False
    
    def generate_report(self):
        """Generate sender report file"""
        time_elapsed = 0
        if len(self.timestamps) >= 2:
            first_ts = self.timestamps[0]
            last_ts = self.timestamps[-1]
            time_elapsed = (last_ts - first_ts) / 1_000_000_000  # ns to seconds
        
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

async def main():
    parser = argparse.ArgumentParser(description="High-Performance HTTP Test Sender")
    parser.add_argument("--url", type=str, required=True, help="Target URL to send messages to")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to send (0 for infinite)")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")
    parser.add_argument("--payload-size", type=int, default=100, help="Size of payload in bytes")
    parser.add_argument("--concurrency", type=int, default=100, help="Number of concurrent connections")
    
    args = parser.parse_args()
    
    sender = AsyncHttpSender(
        target_url=args.url,
        message_count=args.count,
        duration=args.time,
        payload_size=args.payload_size,
        concurrency=args.concurrency
    )
    
    await sender.run()

if __name__ == "__main__":
    asyncio.run(main())