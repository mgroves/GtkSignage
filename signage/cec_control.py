"""
CEC Control Module

Provides simple power status and control helpers for HDMI-CEC.
Supports real and fake (simulated) modes via configuration.
"""

from __future__ import annotations

import logging

from signage.config import get_bool

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

USE_FAKE_CEC = get_bool("cec", "fake", default=False)

# ------------------------------------------------------------
# Internal state (fake mode)
# ------------------------------------------------------------

_fake_status = "Off"

# ------------------------------------------------------------
# Optional CEC initialization
# ------------------------------------------------------------

adapter = None
CEC_AVAILABLE = False

if not USE_FAKE_CEC:
    try:
        import cec

        cec_config = cec.libcec_configuration()
        cec_config.strDeviceName = "GtkSignage"
        cec_config.clientVersion = cec.LIBCEC_VERSION_CURRENT

        adapter = cec.ICECAdapter.Create(cec_config)
        adapters = adapter.DetectAdapters()

        if not adapters:
            raise RuntimeError("No CEC adapters found")

        if not adapter.Open(adapters[0].strComName):
            raise RuntimeError("Failed to open CEC adapter")

        CEC_AVAILABLE = True
        logger.info("CEC control initialized")

    except Exception as e:
        adapter = None
        CEC_AVAILABLE = False
        logger.warning("CEC unavailable, falling back to fake mode: %s", e)
        USE_FAKE_CEC = True


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def get_cec_status() -> str:
    """
    Return current power status as 'On' or 'Off'.
    """
    if USE_FAKE_CEC:
        return _fake_status

    if not CEC_AVAILABLE or not adapter:
        return "Unavailable"

    try:
        status = adapter.GetDevicePowerStatus(0)  # 0 = TV
        return "On" if status == cec.CEC_POWER_STATUS_ON else "Off"
    except Exception as e:
        logger.error("CEC status check failed: %s", e)
        return "Error"


def cec_power_on() -> None:
    """
    Power on the display.
    """
    global _fake_status

    if USE_FAKE_CEC:
        _fake_status = "On"
        logger.debug("CEC fake mode: power ON")
        return

    if not CEC_AVAILABLE or not adapter:
        logger.warning("CEC power on requested but unavailable")
        return

    try:
        adapter.PowerOnDevices(0)
        logger.info("CEC power ON sent")
    except Exception as e:
        logger.error("CEC power ON failed: %s", e)


def cec_power_off() -> None:
    """
    Put the display into standby.
    """
    global _fake_status

    if USE_FAKE_CEC:
        _fake_status = "Off"
        logger.debug("CEC fake mode: power OFF")
        return

    if not CEC_AVAILABLE or not adapter:
        logger.warning("CEC power off requested but unavailable")
        return

    try:
        adapter.StandbyDevices(0)
        logger.info("CEC power OFF sent")
    except Exception as e:
        logger.error("CEC power OFF failed: %s", e)