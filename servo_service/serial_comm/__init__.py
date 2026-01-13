"""
串口通信模块

提供串口设备发现、连接、读写等功能。
"""

from .exceptions import (
    PortAccessError,
    PortConfigError,
    PortNotFoundError,
    PortNotOpenError,
    PortOpenError,
    ReadTimeoutError,
    SerialCommError,
    SerialPortError,
    WriteError,
)
from .port_scanner import PortInfo, PortScanner
from .serial_port import SerialPort

__all__ = [
    # 异常类
    "SerialCommError",
    "SerialPortError",
    "PortNotFoundError",
    "PortOpenError",
    "PortAccessError",
    "PortNotOpenError",
    "ReadTimeoutError",
    "WriteError",
    "PortConfigError",
    # 串口扫描
    "PortInfo",
    "PortScanner",
    # 串口通信
    "SerialPort",
]
