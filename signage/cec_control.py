import os
import subprocess

# Determine if we're in fake/sim mode
USE_FAKE_CEC = os.getenv("CEC_FAKE", "false").lower() == "true"

# Internal state for fake mode
_fake_status = "Off"

def get_cec_status():
    if USE_FAKE_CEC:
        return _fake_status
    try:
        result = subprocess.run(
            ["cec-client", "-s", "-d", "1"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout.lower()
        if "power status: on" in output:
            return "On"
        elif "power status: standby" in output:
            return "Off"
        return "Unknown"
    except FileNotFoundError:
        return "Error: cec-client not found"
    except Exception as e:
        return f"Error: {e}"

def cec_power_on():
    global _fake_status
    if USE_FAKE_CEC:
        _fake_status = "On"
        return
    subprocess.run(["cec-client", "-s", "-d", "1"], input="on 0", text=True)

def cec_power_off():
    global _fake_status
    if USE_FAKE_CEC:
        _fake_status = "Off"
        return
    subprocess.run(["cec-client", "-s", "-d", "1"], input="standby 0", text=True)
