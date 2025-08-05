import os
import time
import logging
from datetime import datetime, time as dtime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    import cec

    CEC_AVAILABLE = True

    cec_config = cec.libcec_configuration()
    cec_config.strDeviceName = "GtkSignage"
    cec_config.bActivateSource = 0
    cec_config.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
    cec_lib = cec.ICECAdapter.Create(cec_config)

    if not cec_lib.DetectAdapters():
        logger.warning("No CEC adapters found. CEC control disabled.")
        CEC_AVAILABLE = False
    elif not cec_lib.Open(cec_lib.DetectAdapters()[0].strComName):
        logger.warning("Failed to open CEC adapter. CEC control disabled.")
        CEC_AVAILABLE = False

except ImportError:
    CEC_AVAILABLE = False
    logger.warning("CEC module not available. Skipping CEC watchdog.")


def parse_time(timestr):
    return dtime.fromisoformat(timestr.strip())


def is_now_between(start: dtime, end: dtime) -> bool:
    now = datetime.now().time()
    return start <= now <= end if start < end else now >= start or now <= end


def is_cec_on():
    power = cec_lib.GetDevicePowerStatus(0)  # 0 = TV
    return power == cec.CEC_POWER_STATUS_ON


def ensure_cec_on_if_needed():
    if not CEC_AVAILABLE:
        return

    if os.getenv("CEC_ENABLE", "false").lower() != "true":
        return

    start = parse_time(os.getenv("CEC_START", "10:00"))
    end = parse_time(os.getenv("CEC_END", "22:00"))

    if is_now_between(start, end):
        if not is_cec_on():
            logger.info("CEC within active hours, turning TV ON...")
            cec_lib.PowerOnDevices()
        else:
            logger.debug("CEC already ON.")
    else:
        logger.debug("CEC outside active hours.")
