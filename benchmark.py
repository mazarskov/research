import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
import threading

def run_benchmark():
    # Clear previous output
    output_text.delete(1.0, tk.END)
    status_label.config(text="Running benchmark...")

    # Get values from input fields
    message_count = count_entry.get()
    rate = rate_entry.get()
    concurrency = concurrency_entry.get()
    
    # Validate inputs
    try:
        message_count = int(message_count)
        rate = int(rate)
        concurrency = int(concurrency)
    except ValueError:
        status_label.config(text="Error: Please enter valid numbers")
        return

    # Determine script name based on toggle and platform
    script_base = "run_test_no_cpu" if cpu_toggle.get() == 0 else "run_test"
    script_ext = ".bat" if sys.platform.startswith("win") else ".sh"
    script_name = script_base + script_ext

    # Determine protocol directory
    protocol_dirs = {
        "MQTT": "data-gather/mqtt",
        "CoAP": "data-gather/coap",
        "HTTP": "data-gather/http"
    }
    protocol_dir = protocol_dirs[protocol_var.get()]

    # Construct full script path
    script_path = os.path.join(protocol_dir, script_name)

    # Check if script exists
    if not os.path.exists(script_path):
        status_label.config(text=f"Error: {script_path} not found")
        return

    # Ensure script is executable on Unix-like systems
    if not sys.platform.startswith("win") and not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)  # Make script executable
        except PermissionError:
            status_label.config(text=f"Error: Cannot make {script_path} executable")
            return

    # Construct command
    command = [script_path, str(message_count), str(rate), str(concurrency)]

    # Run command in a separate thread to keep UI responsive
    def run_command():
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1  # Line-buffered
            )
            
            # Read output in real-time
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                output_text.insert(tk.END, line)
                output_text.see(tk.END)  # Auto-scroll to end
                root.update_idletasks()  # Update UI

            # Check exit status
            if process.returncode == 0:
                status_label.config(text="Benchmark completed successfully!")
            else:
                status_label.config(text=f"Error: Process exited with code {process.returncode}")
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")
            output_text.insert(tk.END, f"Error: {str(e)}\n")

    # Start the command in a thread
    threading.Thread(target=run_command, daemon=True).start()

# Create main window
root = tk.Tk()
root.title("Benchmark Tool")
root.geometry("600x500")

# Protocol Selection
protocol_frame = ttk.Frame(root)
protocol_frame.pack(pady=10)
ttk.Label(protocol_frame, text="Protocol:").pack()
protocol_var = tk.StringVar(value="MQTT")  # Default to MQTT
protocols = ["MQTT", "CoAP", "HTTP"]
for protocol in protocols:
    ttk.Radiobutton(
        protocol_frame,
        text=protocol,
        value=protocol,
        variable=protocol_var
    ).pack(anchor=tk.W)

# CPU Stats Toggle
cpu_toggle = tk.IntVar(value=0)  # 0 = off (no_cpu), 1 = on (with cpu)
toggle_frame = ttk.Frame(root)
toggle_frame.pack(pady=10)
ttk.Label(toggle_frame, text="CPU Stats:").pack(side=tk.LEFT)
ttk.Checkbutton(toggle_frame, text="Enable", variable=cpu_toggle).pack(side=tk.LEFT)

# Parameter Inputs
params_frame = ttk.Frame(root)
params_frame.pack(pady=10)

# Message Count
ttk.Label(params_frame, text="Message Count:").grid(row=0, column=0, padx=5, pady=5)
count_entry = ttk.Entry(params_frame)
count_entry.insert(0, "100")  # Default value
count_entry.grid(row=0, column=1, padx=5, pady=5)

# Rate
ttk.Label(params_frame, text="Rate:").grid(row=1, column=0, padx=5, pady=5)
rate_entry = ttk.Entry(params_frame)
rate_entry.insert(0, "10")  # Default value
rate_entry.grid(row=1, column=1, padx=5, pady=5)

# Concurrency
ttk.Label(params_frame, text="Concurrency:").grid(row=2, column=0, padx=5, pady=5)
concurrency_entry = ttk.Entry(params_frame)
concurrency_entry.insert(0, "1")  # Default value
concurrency_entry.grid(row=2, column=1, padx=5, pady=5)

# Run Button
run_button = ttk.Button(root, text="Run Benchmark", command=run_benchmark)
run_button.pack(pady=10)

# Output Text Area
output_frame = ttk.Frame(root)
output_frame.pack(pady=10, fill=tk.BOTH, expand=True)
output_text = tk.Text(output_frame, height=10, width=60)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=output_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
output_text.config(yscrollcommand=scrollbar.set)

# Status Label
status_label = ttk.Label(root, text="Ready")
status_label.pack(pady=10)

# Start the application
root.mainloop()