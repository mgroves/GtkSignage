import os

# Determine if we're in fake/sim mode
USE_FAKE_CEC = os.getenv("CEC_FAKE", "false").lower() == "true"

# Internal state for fake mode
_fake_status = "Off"

try:
    if not USE_FAKE_CEC:
        import cec
        cec_config = cec.libcec_configuration()
        cec_config.strDeviceName = "pyCec"
        cec_config.clientVersion = cec.LIBCEC_VERSION_CURRENT
        adapter = cec.ICECAdapter.Create(cec_config)
        com_ports = adapter.DetectAdapters()
        if com_ports:
            adapter.Open(com_ports[0].strComName)
        else:
            raise Exception("No CEC adapters found")
except Exception as e:
    adapter = None
    if not USE_FAKE_CEC:
        print(f"CEC init error: {e}")
        USE_FAKE_CEC = True

def get_cec_status():
    if USE_FAKE_CEC:
        return _fake_status
    try:
        status = adapter.GetDevicePowerStatus(0)
        return "On" if status == cec.CEC_POWER_STATUS_ON else "Off"
    except Exception as e:
        return f"Error: {e}"

def cec_power_on():
    global _fake_status
    if USE_FAKE_CEC:
        _fake_status = "On"
    else:
        adapter.PowerOnDevices(0)

def cec_power_off():
    global _fake_status
    if USE_FAKE_CEC:
        _fake_status = "Off"
    else:
        adapter.StandbyDevices(0)
