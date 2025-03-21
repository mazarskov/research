import tkinter as tk
from tkinter import ttk
import csv

# Function to read protocol data from CSV and extract messages
def read_protocols_from_csv(file_path):
    protocols = []
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            for key in ['avg_latency', 'min_latency', 'max_latency', 'energy', 'power', 'runtime']:
                if row[key] == '-':
                    row[key] = float('inf')
                else:
                    row[key] = float(row[key])
            try:
                row['messages'] = float(row['name'].split('-')[2])
            except (IndexError, ValueError):
                row['messages'] = 0
            protocols.append(row)
    return protocols

def calculate_scores(protocols, latency_weight, efficiency_weight, power_weight, runtime_weight):
    for protocol in protocols:
        latency_score = 10 - (protocol['avg_latency'] / max(p['avg_latency'] for p in protocols if p['avg_latency'] != float('inf')) * 10) if protocol['avg_latency'] != float('inf') else 0
        efficiency_score = 10 - (protocol['energy'] / protocol['messages'] / max(p['energy']/p['messages'] for p in protocols if p['messages'] > 0) * 10) if protocol['messages'] > 0 else 0
        power_score = 10 - (protocol['power'] / max(p['power'] for p in protocols) * 10)
        runtime_score = 10 - (protocol['runtime'] / max(p['runtime'] for p in protocols) * 10)
        
        weighted_score = (
            latency_score * latency_weight +
            efficiency_score * efficiency_weight +
            power_score * power_weight +
            runtime_score * runtime_weight
        )
        protocol["score"] = weighted_score

def get_recommendation(sorted_protocols, top_n=5):
    # Count protocol types in top N results
    top_protocols = sorted_protocols[:min(top_n, len(sorted_protocols))]
    protocol_counts = {'C': 0, 'M': 0, 'H': 0}
    
    for protocol in top_protocols:
        # Extract protocol type from the second part of the name (after first '-')
        try:
            protocol_type = protocol['name'].split('-')[1].upper()
            if protocol_type in protocol_counts:
                protocol_counts[protocol_type] += 1
        except IndexError:
            continue
    
    # Determine the most prevalent protocol
    max_count = max(protocol_counts.values())
    if max_count == 0:
        return "No clear recommendation"
    
    recommended = max(protocol_counts, key=protocol_counts.get)
    protocol_names = {'C': 'CoAP', 'M': 'MQTT', 'H': 'HTTP'}
    return f"Recommended Protocol: {protocol_names[recommended]} (Count: {max_count})"

def on_submit():
    latency_weight = speed_slider.get()
    if latency_weight == 0:
        latency_weight = 0.01
    efficiency_weight = efficiency_slider.get()
    power_weight = power_slider.get()
    runtime_weight = runtime_slider.get()
    
    total = latency_weight + efficiency_weight + power_weight + runtime_weight
    latency_weight /= total
    efficiency_weight /= total
    power_weight /= total
    runtime_weight /= total
    
    calculate_scores(protocols, latency_weight, efficiency_weight, power_weight, runtime_weight)
    
    sorted_protocols = sorted(protocols, key=lambda x: x["score"], reverse=True)
    
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Best Protocols:\n")
    for protocol in sorted_protocols:
        result_text.insert(tk.END, f"{protocol['name']}: Score = {protocol['score']:.2f}\n")
    
    # Update recommendation label
    recommendation = get_recommendation(sorted_protocols, top_n=5)  # Changed to top 5 as per your request
    recommendation_label.config(text=recommendation)

protocols = read_protocols_from_csv("klop.csv")

# Create the main window
root = tk.Tk()
root.title("Protocol Selection Tool")

# Create sliders for user priorities
speed_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
efficiency_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
power_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
runtime_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)

# Labels for sliders
ttk.Label(root, text="Latency Priority (1-10):").grid(row=0, column=0, padx=10, pady=5)
speed_slider.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Efficiency Priority (1-10):").grid(row=1, column=0, padx=10, pady=5)
efficiency_slider.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Power Priority (1-10):").grid(row=2, column=0, padx=10, pady=5)
power_slider.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, text="Runtime Priority (1-10):").grid(row=3, column=0, padx=10, pady=5)
runtime_slider.grid(row=3, column=1, padx=10, pady=5)

# Recommendation label (initially empty)
recommendation_label = ttk.Label(root, text="")
recommendation_label.grid(row=4, column=0, columnspan=2, pady=5)

# Submit button
submit_button = ttk.Button(root, text="Submit", command=on_submit)
submit_button.grid(row=5, column=0, columnspan=2, pady=10)

# Text widget to display results
result_text = tk.Text(root, height=10, width=50)
result_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# Run the application
root.mainloop()