"""
串口通信异常定义模块

定义串口通信过程中可能发生的各种异常。
"""

from typing import Optional


class SerialCommError(Exception):
    """串口通信基础异常类"""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        初始化异常

        Args:
            message: 异常消息
            details: 详细信息字典
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class SerialPortError(SerialCommError):
    """串口错误基类"""

    def __init__(self, message: str, port_name: Optional[str] = None):
        """
        初始化串口错误

        Args:
            message: 错误消息
            port_name: 串口名称
        """
        super().__init__(message, details={"port_name": port_name})
        self.port_name = port_name


class PortNotFoundError(SerialPortError):
    """串口未找到错误"""

    def __init__(self, port_name: str):
        """
        初始化

        Args:
            port_name: 串口名称
        """
        super().__init__(f"串口 '{port_name}' 未找到", port_name)


class PortOpenError(SerialPortError):
    """串口打开错误"""

    def __init__(self, port_name: str, reason: str = ""):
        """
        初始化

        Args:
            port_name: 串口名称
            reason: 错误原因
        """
        msg = f"无法打开串口 '{port_name}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, port_name)
        self.reason = reason


class PortAccessError(SerialPortError):
    """串口访问权限错误"""

    def __init__(self, port_name: str):
        """
        初始化

        Args:
            port_name: 串口名称
        """
        super().__init__(f"无权限访问串口 '{port_name}'", port_name)


class PortNotOpenError(SerialPortError):
    """串口未打开错误"""

    def __init__(self, port_name: Optional[str] = None):
        """
        初始化

        Args:
            port_name: 串口名称
        """
        msg = "串口未打开"
        if port_name:
            msg = f"串口 '{port_name}' 未打开"
        super().__init__(msg, port_name)


class ReadTimeoutError(SerialCommError):
    """读取超时错误"""

    def __init__(self, timeout: float, expected_bytes: int = 0, received_bytes: int = 0):
        """
        初始化

        Args:
            timeout: 超时时间（秒）
            expected_bytes: 期望读取的字节数
            received_bytes: 实际读取的字节数
        """
        msg = f"读取超时 ({timeout}s)"
        if expected_bytes > 0:
            msg += f", 期望 {expected_bytes} 字节, 收到 {received_bytes} 字节"
        super().__init__(msg, details={
            "timeout": timeout,
            "expected_bytes": expected_bytes,
            "received_bytes": received_bytes
        })
        self.timeout = timeout
        self.expected_bytes = expected_bytes
        self.received_bytes = received_bytes


class WriteError(SerialCommError):
    """写入错误"""

    def __init__(self, message: str = "写入失败", bytes_to_write: int = 0):
        """
        初始化

        Args:
            message: 错误消息
            bytes_to_write: 尝试写入的字节数
        """
        super().__init__(message, details={"bytes_to_write": bytes_to_write})
        self.bytes_to_write = bytes_to_write


class PortConfigError(SerialCommError):
    """串口配置错误"""

    def __init__(self, message: str, parameter: Optional[str] = None, value: Optional[str] = None):
        """
        初始化

        Args:
            message: 错误消息
            parameter: 参数名称
            value: 参数值
        """
        super().__init__(message, details={"parameter": parameter, "value": value})
        self.parameter = parameter
        self.value = value
