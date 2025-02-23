import time
import argparse
import json
import signal
import sys
import paho.mqtt.client as mqtt

class MqttReceiver:
    def __init__(self, broker, port, topic, message_count=0, duration=0):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.message_count = message_count
        self.duration = duration
        self.received_messages = 0
        self.timestamps = []
        self.start_time = None
        self.running = True

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT Broker with result code {rc}")
        self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        if not self.running:
            return

        timestamp = time.time_ns()
        self.received_messages += 1
        self.timestamps.append(timestamp)

        if self.received_messages % 1000 == 0:
            elapsed = time.time() - self.start_time if self.start_time else 0
            rate = self.received_messages / elapsed if elapsed > 0 else 0
            print(f"Received {self.received_messages} messages, rate: {rate:.2f} msgs/sec")

        if self.message_count > 0 and self.received_messages >= self.message_count:
            self.stop()

    def stop(self):
        if not self.running:
            return

        print("Stopping receiver...")
        self.running = False
        self.client.loop_stop()
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

    def run(self):
        self.start_time = time.time()
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

        if self.duration > 0:
            time.sleep(self.duration)
            self.stop()

        while self.running:
            time.sleep(0.1)

def signal_handler(sig, frame):
    print("\nInterrupted by user. Shutting down...")
    receiver.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Receiver")
    parser.add_argument("--broker", required=True, help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", required=True, help="MQTT topic to subscribe to")
    parser.add_argument("--count", type=int, default=0, help="Number of messages to receive (0 for infinite)")
    parser.add_argument("--time", type=int, default=0, help="Duration to run in seconds (0 for infinite)")

    args = parser.parse_args()

    receiver = MqttReceiver(
        broker=args.broker,
        port=args.port,
        topic=args.topic,
        message_count=args.count,
        duration=args.time
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    receiver.run()