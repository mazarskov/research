import asyncio
import time
import argparse
import json
import signal
import sys
from datetime import datetime
import aiohttp

class AsyncHttpSender:
    def __init__(self, target_url, message_count=0, duration=0, rate=0, payload_size=100, concurrency=100):
        self.target_url = target_url
        self.message_count = message_count
        self.duration = duration
        self.rate = rate  # messages per second
        self.payload_size = payload_size
        self.concurrency = concurrency
        self.sent_messages = 0
        self.timestamps = []
        self.running = True
        self.semaphore = None
        
    def generate_payload(self, seq):
        """Generate realistic sensor data payload with specified size"""
        # Base sensor data
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
        
        # Calculate current size and add padding to reach target payload_size
        base_payload = json.dumps(sensor_data)
        current_size = len(base_payload.encode('utf-8'))
        padding_size = max(0, self.payload_size - current_size)
        
        # Add padding data if needed
        if padding_size > 0:
            padding = "x" * padding_size
            sensor_data["padding"] = padding
            
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
            except Exception:
                pass
    
    async def run(self):
        """Run the sender according to specified parameters"""
        signal.signal(signal.SIGINT, self.handle_interrupt)
        
        self.semaphore = asyncio.Semaphore(self.concurrency)
        conn = aiohttp.TCPConnector(limit=self.concurrency, force_close=False, 
                                 limit_per_host=self.concurrency)
        timeout = aiohttp.ClientTimeout(total=5, connect=1, sock_connect=1, sock_read=1)
        
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            start_time = time.time()
            seq = 0
            tasks = []
            
            # Calculate total messages based on rate and duration if rate is specified
            if self.rate > 0 and self.duration > 0:
                self.message_count = int(self.rate * self.duration)
            
            # Calculate delay between messages if rate is specified
            delay = 1.0 / self.rate if self.rate > 0 else 0
            
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
                
                # Apply rate limiting
                if self.rate > 0:
                    expected_time = start_time + (seq / self.rate)
                    current_time = time.time()
                    sleep_time = max(0, expected_time - current_time)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                
                # Progress report
                if seq % 1000 == 0:
                    print(f"Scheduled {seq} messages, sent {self.sent_messages} so far")
                
                # Clean up completed tasks
                if len(tasks) > 1000:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
            
            # Wait for all pending tasks
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

async def main():
    parser = argparse.ArgumentParser(description="High-Performance HTTP Test Sender")
    parser.add_argument("--url", type=str, required=True, help="Target URL to send messages to")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to send (0 for infinite)")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")
    parser.add_argument("--rate", type=float, default=0, help="Messages per second (overrides count if used with time)")
    parser.add_argument("--payload-size", type=int, default=100, help="Size of payload in bytes")
    parser.add_argument("--concurrency", type=int, default=100, help="Number of concurrent connections")
    
    args = parser.parse_args()
    
    sender = AsyncHttpSender(
        target_url=args.url,
        message_count=args.count,
        duration=args.time,
        rate=args.rate,
        payload_size=args.payload_size,
        concurrency=args.concurrency
    )
    
    await sender.run()

if __name__ == "__main__":
    asyncio.run(main())