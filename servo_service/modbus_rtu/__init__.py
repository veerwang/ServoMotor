"""
Modbus RTU 协议模块

提供 Modbus RTU 通信功能，包括帧构建、CRC 校验、客户端等。
"""

from .client import ModbusClient
from .crc import (
    append_crc,
    calculate_crc,
    calculate_crc_bytes,
    extract_crc,
    verify_crc,
)
from .exceptions import (
    BroadcastError,
    CRCError,
    FrameError,
    FunctionCodeMismatchError,
    ModbusError,
    ModbusExceptionResponse,
    NoResponseError,
    ResponseError,
    SlaveIdMismatchError,
    TimeoutError,
)
from .frame import (
    FrameBuilder,
    FunctionCode,
    ModbusRequest,
    ModbusResponse,
    calculate_response_length,
    parse_write_response,
)

__all__ = [
    # 客户端
    "ModbusClient",
    # CRC
    "calculate_crc",
    "calculate_crc_bytes",
    "verify_crc",
    "append_crc",
    "extract_crc",
    # 帧
    "FunctionCode",
    "ModbusRequest",
    "ModbusResponse",
    "FrameBuilder",
    "calculate_response_length",
    "parse_write_response",
    # 异常
    "ModbusError",
    "ModbusExceptionResponse",
    "CRCError",
    "FrameError",
    "ResponseError",
    "SlaveIdMismatchError",
    "FunctionCodeMismatchError",
    "TimeoutError",
    "NoResponseError",
    "BroadcastError",
]
