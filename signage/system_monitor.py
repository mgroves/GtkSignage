"""
System Monitor Module

This module provides functions for monitoring system resources like CPU, memory, and temperature.
It uses the psutil library to gather system information.
"""
import os
import platform
import logging
import psutil

# Get logger for this module
logger = logging.getLogger(__name__)

def get_cpu_usage():
    """
    Get the current CPU usage as a percentage.
    
    Returns:
        float: CPU usage percentage (0-100).
    """
    try:
        return psutil.cpu_percent(interval=0.5)
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return None

def get_memory_usage():
    """
    Get the current memory usage.
    
    Returns:
        dict: Memory usage information with the following keys:
            - total: Total physical memory in bytes
            - available: Available memory in bytes
            - used: Used memory in bytes
            - percent: Percentage of memory used (0-100)
    """
    try:
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return None

def get_disk_usage():
    """
    Get the disk usage for the root partition.
    
    Returns:
        dict: Disk usage information with the following keys:
            - total: Total disk space in bytes
            - used: Used disk space in bytes
            - free: Free disk space in bytes
            - percent: Percentage of disk used (0-100)
    """
    try:
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return None

def get_temperature():
    """
    Get the CPU temperature if available.
    
    Returns:
        float or None: CPU temperature in Celsius, or None if not available.
    """
    try:
        # Temperature is not available on all systems
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        
        # Try to find CPU temperature
        # Different systems report temperature differently
        for name, entries in temps.items():
            if any(x.lower() in name.lower() for x in ['cpu', 'core', 'package']):
                return entries[0].current
            
        # If we couldn't find a CPU temperature, return the first one
        if temps:
            first_sensor = next(iter(temps.values()))
            if first_sensor:
                return first_sensor[0].current
                
        return None
    except Exception as e:
        logger.error(f"Error getting temperature: {e}")
        return None

def get_system_info():
    """
    Get basic system information.
    
    Returns:
        dict: System information with the following keys:
            - system: Operating system name
            - node: Network node name
            - release: Operating system release
            - version: Operating system version
            - machine: Machine type
            - processor: Processor type
            - cpu_count: Number of CPUs
            - boot_time: System boot time (timestamp)
    """
    try:
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "boot_time": psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return None

def get_all_stats():
    """
    Get all system statistics in a single call.
    
    Returns:
        dict: All system statistics with the following keys:
            - cpu: CPU usage percentage
            - memory: Memory usage information
            - disk: Disk usage information
            - temperature: CPU temperature in Celsius (if available)
            - system_info: Basic system information
    """
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "temperature": get_temperature(),
        "system_info": get_system_info()
    }