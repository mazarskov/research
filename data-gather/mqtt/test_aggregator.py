import argparse
import json
import statistics
from datetime import datetime

class TestAggregator:
    def __init__(self, sender_file, receiver_file, output_file="aggregated_report.txt"):
        self.sender_file = sender_file
        self.receiver_file = receiver_file
        self.output_file = output_file
        
    def load_reports(self):
        """Load sender and receiver reports"""
        with open(self.sender_file, 'r') as f:
            self.sender_data = json.load(f)
            
        with open(self.receiver_file, 'r') as f:
            self.receiver_data = json.load(f)
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        total_sent = self.sender_data["total_sent"]
        total_received = self.receiver_data["total_received"]
        
        # Calculate packet loss
        if total_sent > 0:
            packet_loss = ((total_sent - total_received) / total_sent) * 100
        else:
            packet_loss = 0
            
        # Calculate transfer speed
        if self.sender_data["timestamps"] and len(self.sender_data["timestamps"]) >= 2:
            sender_first = self.sender_data["timestamps"][0]
            sender_last = self.sender_data["timestamps"][-1]
            duration_ns = sender_last - sender_first
            duration_s = duration_ns / 1_000_000_000
            
            if duration_s > 0:
                transfer_speed = total_sent / duration_s
            else:
                transfer_speed = 0
        else:
            transfer_speed = 0
            
        # Calculate latency if we have received messages
        latencies = []
        if total_received > 0 and len(self.sender_data["timestamps"]) >= total_received:
            # This is a simplification - in a real scenario we'd need message IDs to match
            # For simplicity, we'll assume messages arrive in order
            for i in range(min(total_received, len(self.receiver_data["timestamps"]))):
                if i < len(self.sender_data["timestamps"]):
                    latency = (self.receiver_data["timestamps"][i] - self.sender_data["timestamps"][i]) / 1_000_000  # ns to ms
                    latencies.append(latency)
        
        metrics = {
            "total_sent": total_sent,
            "total_received": total_received,
            "packet_loss_percent": packet_loss,
            "transfer_speed_msgs_per_sec": transfer_speed,
            "latencies_ms": latencies,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "median_latency_ms": statistics.median(latencies) if latencies else 0
        }
        
        return metrics
    
    def generate_report(self):
        """Generate aggregated report"""
        self.load_reports()
        metrics = self.calculate_metrics()
        
        # Format report
        report = f"""HTTP PROTOCOL TEST REPORT
==============================
Total Sent: {metrics['total_sent']}
Total Received: {metrics['total_received']}
Packet Loss: {metrics['packet_loss_percent']:.2f}%
Transfer Speed: {metrics['transfer_speed_msgs_per_sec']:.2f} messages/second

LATENCY STATISTICS:
Average Latency: {metrics['avg_latency_ms']:.2f} ms
Minimum Latency: {metrics['min_latency_ms']:.2f} ms
Maximum Latency: {metrics['max_latency_ms']:.2f} ms
Median Latency: {metrics['median_latency_ms']:.2f} ms

Sent Data:
First message timestamp: {self.format_timestamp(self.sender_data["start_time"])}
Last message timestamp: {self.format_timestamp(self.sender_data["end_time"])}

Received Data:
First message timestamp: {self.format_timestamp(self.receiver_data["start_time"])}
Last message timestamp: {self.format_timestamp(self.receiver_data["end_time"])}
"""

        # Write to file
        with open(self.output_file, 'w') as f:
            f.write(report)
            
        print(f"Aggregated report generated: {self.output_file}")
        print(report)
        
    def format_timestamp(self, ns_timestamp):
        """Format nanosecond timestamp to human-readable format"""
        if ns_timestamp == 0:
            return "N/A"
        seconds = ns_timestamp / 1_000_000_000
        dt = datetime.fromtimestamp(seconds)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Trim to milliseconds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Test Aggregator")
    parser.add_argument("--sender", type=str, required=True, help="Path to sender report file")
    parser.add_argument("--receiver", type=str, required=True, help="Path to receiver report file")
    parser.add_argument("--output", type=str, default="aggregated_report.txt", help="Output file name")
    
    args = parser.parse_args()
    
    aggregator = TestAggregator(
        sender_file=args.sender,
        receiver_file=args.receiver,
        output_file=args.output
    )
    
    aggregator.generate_report()