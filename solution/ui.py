import tkinter as tk
from tkinter import ttk
import csv

# Function to read protocol data from CSV
def read_protocols_from_csv(file_path):
    protocols = []
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert numeric fields to integers
            row["speed"] = int(row["speed"])
            row["efficiency"] = int(row["efficiency"])
            row["security"] = int(row["security"])
            row["packet_loss"] = int(row["packet_loss"])
            protocols.append(row)
    return protocols

def calculate_scores(protocols, speed_weight, efficiency_weight, security_weight, packet_loss_weight):
    for protocol in protocols:
        # subtraction because higher=worse in case of packet loss
        packet_loss_score = 10 - protocol["packet_loss"]
        
        weighted_score = (
            protocol["speed"] * speed_weight +
            protocol["efficiency"] * efficiency_weight +
            protocol["security"] * security_weight +
            packet_loss_score * packet_loss_weight
        )
        protocol["score"] = weighted_score

def on_submit():

    speed_weight = speed_slider.get()
    if speed_weight == 0:
        speed_weight = 0.01
    efficiency_weight = efficiency_slider.get()
    security_weight = security_slider.get()
    packet_loss_weight = packet_loss_slider.get()
    
    # Normalizing weigths
    total = speed_weight + efficiency_weight + security_weight + packet_loss_weight
    speed_weight /= total
    efficiency_weight /= total
    security_weight /= total
    packet_loss_weight /= total
    
    calculate_scores(protocols, speed_weight, efficiency_weight, security_weight, packet_loss_weight)
    
    # descending
    sorted_protocols = sorted(protocols, key=lambda x: x["score"], reverse=True)
    
    result_text.delete(1.0, tk.END)  # Clear previous results
    result_text.insert(tk.END, "Best Protocols:\n")
    for protocol in sorted_protocols:
        result_text.insert(tk.END, f"{protocol['name']}: Score = {protocol['score']:.2f}\n")


protocols = read_protocols_from_csv("protocols.csv")

# Create the main window
root = tk.Tk()
root.title("Protocol Selection Tool")

# Create sliders for user priorities
speed_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
efficiency_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
security_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
packet_loss_slider = ttk.Scale(root, from_=1, to=10, orient=tk.HORIZONTAL, length=200)

# Labels for sliders
ttk.Label(root, text="Speed Priority (1-10):").grid(row=0, column=0, padx=10, pady=5)
speed_slider.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Efficiency Priority (1-10):").grid(row=1, column=0, padx=10, pady=5)
efficiency_slider.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Security Priority (1-10):").grid(row=2, column=0, padx=10, pady=5)
security_slider.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, text="Least Packet Loss Priority (1-10):").grid(row=3, column=0, padx=10, pady=5)
packet_loss_slider.grid(row=3, column=1, padx=10, pady=5)

# Submit button
submit_button = ttk.Button(root, text="Submit", command=on_submit)
submit_button.grid(row=4, column=0, columnspan=2, pady=10)

# Text widget to display results
result_text = tk.Text(root, height=10, width=50)
result_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Run the application
root.mainloop()