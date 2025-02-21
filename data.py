import csv
import random

# Dummy data for protocols
protocols = [
    {"name": "Protocol A", "speed": random.randint(1, 10), "efficiency": random.randint(1, 10), 
     "security": random.randint(1, 10), "packet_loss": random.randint(1, 10)},
    {"name": "Protocol B", "speed": random.randint(1, 10), "efficiency": random.randint(1, 10), 
     "security": random.randint(1, 10), "packet_loss": random.randint(1, 10)},
    {"name": "Protocol C", "speed": random.randint(1, 10), "efficiency": random.randint(1, 10), 
     "security": random.randint(1, 10), "packet_loss": random.randint(1, 10)},
    {"name": "Protocol D", "speed": random.randint(1, 10), "efficiency": random.randint(1, 10), 
     "security": random.randint(1, 10), "packet_loss": random.randint(1, 10)},
    {"name": "Protocol E", "speed": random.randint(1, 10), "efficiency": random.randint(1, 10), 
     "security": random.randint(1, 10), "packet_loss": random.randint(1, 10)},
]

# Write data to a CSV file
with open("protocols.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["name", "speed", "efficiency", "security", "packet_loss"])
    writer.writeheader()
    writer.writerows(protocols)

print("CSV file 'protocols.csv' created successfully!")