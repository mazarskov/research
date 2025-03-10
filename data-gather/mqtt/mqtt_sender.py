import time
import argparse
import json
import signal
import sys
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

class MqttSender:
    def __init__(self, broker, port, topic, message_count=0, concurrency=1, duration=0, rate=0, payload_size=100):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.message_count = message_count
        self.concurrency = concurrency
        self.duration = duration
        self.rate = rate  # messages per second per thread
        self.payload_size = payload_size
        self.sent_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True
        self.lock = threading.Lock()

    def generate_payload(self, seq):
        """Generate realistic sensor data payload with specified size"""
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
        
        if padding_size > 0:
            sensor_data["padding"] = "x" * padding_size
            
        return json.dumps(sensor_data)

    def send_messages(self):
        client = mqtt.Client()
        client.connect(self.broker, self.port, 60)
        
        thread_start_time = time.time()
        local_seq = 0
        delay = 1.0 / self.rate if self.rate > 0 else 0

        while self.running:
            with self.lock:
                # Check total message count across all threads
                if self.message_count > 0 and self.sent_messages >= self.message_count:
                    self.stop()
                    break

                timestamp = time.time_ns()
                self.sent_messages += 1
                self.timestamps.append(timestamp)
                
                payload = self.generate_payload(self.sent_messages)
                client.publish(self.topic, payload)
                
                local_seq += 1

                if self.sent_messages % 1000 == 0:
                    elapsed = time.time() - self.start_time if self.start_time else 0
                    rate = self.sent_messages / elapsed if elapsed > 0 else 0
                    print(f"Sent {self.sent_messages} messages, rate: {rate:.2f} msgs/sec")

            # Apply rate limiting per thread
            if self.rate > 0:
                expected_time = thread_start_time + (local_seq / self.rate)
                current_time = time.time()
                sleep_time = max(0, expected_time - current_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            else:
                time.sleep(0.001)  # Small delay to prevent CPU overload

        client.disconnect()

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

    def run(self):
        self.start_time = time.time()
        threads = []
        
        # If rate and duration are specified, calculate total message count
        if self.rate > 0 and self.duration > 0:
            self.message_count = int(self.rate * self.duration * self.concurrency)

        for _ in range(self.concurrency):
            thread = threading.Thread(target=self.send_messages)
            thread.start()
            threads.append(thread)

        if self.duration > 0 and (self.rate == 0 or self.message_count == 0):
            time.sleep(self.duration)
            self.stop()

        for thread in threads:
            thread.join()

def signal_handler(sig, frame):
    print("\nInterrupted by user. Shutting down...")
    sender.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Sender")
    parser.add_argument("--broker", required=True, help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", required=True, help="MQTT topic to publish to")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to send (0 for infinite)")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent senders")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")
    parser.add_argument("--rate", type=float, default=0, help="Messages per second per thread (overrides count if used with time)")
    parser.add_argument("--payload-size", type=int, default=100, help="Size of payload in bytes")

    args = parser.parse_args()

    sender = MqttSender(
        broker=args.broker,
        port=args.port,
        topic=args.topic,
        message_count=args.count,
        concurrency=args.concurrency,
        duration=args.time,
        rate=args.rate,
        payload_size=args.payload_size
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    sender.run()