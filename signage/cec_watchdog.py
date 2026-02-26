"""
CEC Watchdog Module

Controls HDMI-CEC power state based on configured time windows.
CEC support is optional and safely disabled if unavailable.
"""

from __future__ import annotations

import logging
from datetime import datetime, time as dtime

from signage.config import get_bool, get_time

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Optional CEC import
# ------------------------------------------------------------

CEC_AVAILABLE = False
cec_lib = None

try:
    import cec

    cec_config = cec.libcec_configuration()
    cec_config.strDeviceName = "GtkSignage"
    cec_config.bActivateSource = 0
    cec_config.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)

    cec_lib = cec.ICECAdapter.Create(cec_config)

    adapters = cec_lib.DetectAdapters()
    if not adapters:
        logger.warning("No CEC adapters found. CEC disabled.")
    elif not cec_lib.Open(adapters[0].strComName):
        logger.warning("Failed to open CEC adapter. CEC disabled.")
    else:
        CEC_AVAILABLE = True
        logger.info("CEC adapter initialized successfully.")

except ImportError:
    logger.warning("CEC Python module not available. Skipping CEC watchdog.")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def is_now_between(start: dtime, end: dtime) -> bool:
    """
    Check whether current local time falls between start and end.
    Handles windows that cross midnight.
    """
    now = datetime.now().time()

    if start < end:
        return start <= now <= end
    else:
        return now >= start or now <= end


def is_cec_on() -> bool:
    """
    Check whether the display is currently powered on via CEC.
    """
    if not CEC_AVAILABLE or not cec_lib:
        return False

    power = cec_lib.GetDevicePowerStatus(0)  # 0 = TV
    return power == cec.CEC_POWER_STATUS_ON


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def ensure_cec_on_if_needed() -> None:
    """
    Ensure the display is powered on during configured hours.
    Safe no-op if CEC is disabled or unavailable.
    """
    if not CEC_AVAILABLE:
        return

    if not get_bool("cec", "enable", default=False):
        return

    start = get_time("cec", "start", default="10:00")
    end = get_time("cec", "end", default="22:00")

    if is_now_between(start, end):
        if not is_cec_on():
            logger.info("CEC active window: powering ON display.")
            try:
                cec_lib.PowerOnDevices()
            except Exception as e:
                logger.error("CEC power-on failed: %s", e)
        else:
            logger.debug("CEC display already ON.")
    else:
        logger.debug("Outside CEC active window.")