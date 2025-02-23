import time
import argparse
import json
import signal
import sys
import threading
import paho.mqtt.client as mqtt

class MqttSender:
    def __init__(self, broker, port, topic, message_count=0, concurrency=1, duration=0):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.message_count = message_count
        self.concurrency = concurrency
        self.duration = duration
        self.sent_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True
        self.lock = threading.Lock()

    def send_messages(self):
        client = mqtt.Client()
        client.connect(self.broker, self.port, 60)

        while self.running:
            with self.lock:
                if self.message_count > 0 and self.sent_messages >= self.message_count:
                    self.stop()
                    break

                timestamp = time.time_ns()
                self.sent_messages += 1
                self.timestamps.append(timestamp)

                client.publish(self.topic, f"message {self.sent_messages}")

                if self.sent_messages % 1000 == 0:
                    elapsed = time.time() - self.start_time if self.start_time else 0
                    rate = self.sent_messages / elapsed if elapsed > 0 else 0
                    print(f"Sent {self.sent_messages} messages, rate: {rate:.2f} msgs/sec")

            time.sleep(0.001)

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

    def run(self):
        self.start_time = time.time()
        threads = []

        for _ in range(self.concurrency):
            thread = threading.Thread(target=self.send_messages)
            thread.start()
            threads.append(thread)

        if self.duration > 0:
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

    args = parser.parse_args()

    sender = MqttSender(
        broker=args.broker,
        port=args.port,
        topic=args.topic,
        message_count=args.count,
        concurrency=args.concurrency,
        duration=args.time
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    sender.run()