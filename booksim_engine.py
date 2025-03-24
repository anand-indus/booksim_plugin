import os
import re
import shutil
import subprocess
import datetime

# === Config Paths ===

CONFIG_DIR = "/home/param/Desktop/noc_tools/booksim2/src/examples"
BOOKSIM_BINARY = "/home/param/Desktop/noc_tools/booksim2/src/booksim"

CONFIG_MAP = {
    "mesh": "mesh88_lat",
    "torus": "torus88",
    "fat tree": "fattree_config",
    "cmesh": "cmeshconfig",
    "dragonfly": "dragonflyconfig",
    "flatfly": "flatflyconfig",
    "single": "singleconfig"
}

# === STEP 1: Select config based on prompt ===

def select_config_from_prompt(prompt: str):
    prompt = prompt.lower()
    for key in CONFIG_MAP:
        if key in prompt:
            config_file = CONFIG_MAP[key]
            config_path = os.path.join(CONFIG_DIR, config_file)
            return config_path, {"topology": key, "config_file": config_file}
    raise ValueError("No valid topology found in prompt.")

# === STEP 2: Patch config file with updates ===

def customize_config(config_path: str, updates: dict) -> str:
    temp_path = config_path + "_temp"
    shutil.copy(config_path, temp_path)

    with open(temp_path, "r") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        match = re.match(r"^(\w+)\s*=\s*([^;]+);", line.strip())
        if match:
            key, _ = match.groups()
            if key in updates:
                value = str(updates[key]).strip()
                lines[idx] = f"{key} = {value};\n"

    with open(temp_path, "w") as f:
        f.writelines(lines)

    return temp_path

# === STEP 3a: Extract summary metrics from output ===

def extract_metrics_from_output(output: str) -> dict:
    metrics = {}
    for line in output.splitlines():
        line = line.strip()
        if "Packet latency average" in line:
            metrics["avg_latency"] = float(line.split("=")[-1].strip())
        elif "Network latency average" in line:
            metrics["avg_network_latency"] = float(line.split("=")[-1].strip())
        elif "Injected packet rate average" in line:
            metrics["injected_packet_rate"] = float(line.split("=")[-1].strip())
        elif "Accepted packet rate average" in line:
            metrics["accepted_packet_rate"] = float(line.split("=")[-1].strip())
        elif "Injected packet length average" in line:
            metrics["injected_packet_length"] = float(line.split("=")[-1].strip())
        elif "Accepted packet length average" in line:
            metrics["accepted_packet_length"] = float(line.split("=")[-1].strip())
        elif "Hops average" in line:
            metrics["avg_hops"] = float(line.split("=")[-1].strip())
    return metrics

# === STEP 3b: Run Booksim simulation and log everything ===

def run_simulation(config_path: str) -> dict:
    process = subprocess.run(
        [BOOKSIM_BINARY, config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    output = process.stdout
    errors = process.stderr
    returncode = process.returncode

    # --- Save Full Log ---
    os.makedirs("logs", exist_ok=True)
    basename = os.path.basename(config_path).replace("_temp", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/{basename}_{timestamp}.log"

    with open(log_filename, "w") as log_file:
        log_file.write(output)

    metrics = extract_metrics_from_output(output) if returncode == 0 else {}

    return {
        "returncode": returncode,
        "stdout": output,
        "stderr": errors,
        "metrics": metrics,
        "log_file": log_filename
    }

