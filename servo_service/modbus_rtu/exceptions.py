"""
Modbus RTU 异常定义模块

定义 Modbus 通信过程中可能发生的各种异常。
"""

from typing import Optional


class ModbusError(Exception):
    """Modbus 通信基础异常类"""

    def __init__(self, message: str, slave_id: Optional[int] = None):
        """
        初始化异常

        Args:
            message: 异常消息
            slave_id: 从站地址
        """
        super().__init__(message)
        self.message = message
        self.slave_id = slave_id

    def __str__(self) -> str:
        return self.message


class ModbusExceptionResponse(ModbusError):
    """Modbus 异常响应

    当从站返回异常功能码时抛出。
    """

    # Modbus 标准异常码
    EXCEPTION_CODES = {
        0x01: "非法功能码",
        0x02: "非法数据地址",
        0x03: "非法数据值",
        0x04: "从站设备故障",
        0x05: "确认 (正在处理)",
        0x06: "从站设备忙",
        0x08: "存储器奇偶校验错误",
        0x0A: "网关路径不可用",
        0x0B: "网关目标设备无响应",
    }

    def __init__(
        self,
        function_code: int,
        exception_code: int,
        slave_id: Optional[int] = None,
    ):
        """
        初始化

        Args:
            function_code: 功能码 (带异常标志)
            exception_code: 异常码
            slave_id: 从站地址
        """
        original_fc = function_code & 0x7F
        exception_name = self.EXCEPTION_CODES.get(exception_code, f"未知异常(0x{exception_code:02X})")
        message = f"Modbus 异常响应: FC=0x{original_fc:02X}, 异常码=0x{exception_code:02X} ({exception_name})"

        super().__init__(message, slave_id)
        self.function_code = function_code
        self.original_function_code = original_fc
        self.exception_code = exception_code
        self.exception_name = exception_name

    @property
    def is_illegal_function(self) -> bool:
        """是否为非法功能码异常"""
        return self.exception_code == 0x01

    @property
    def is_illegal_address(self) -> bool:
        """是否为非法地址异常"""
        return self.exception_code == 0x02

    @property
    def is_illegal_value(self) -> bool:
        """是否为非法数据值异常"""
        return self.exception_code == 0x03

    @property
    def is_device_failure(self) -> bool:
        """是否为设备故障"""
        return self.exception_code == 0x04


class CRCError(ModbusError):
    """CRC 校验错误"""

    def __init__(
        self,
        expected_crc: int,
        received_crc: int,
        slave_id: Optional[int] = None,
    ):
        """
        初始化

        Args:
            expected_crc: 期望的 CRC
            received_crc: 实际收到的 CRC
            slave_id: 从站地址
        """
        message = f"CRC 校验失败: 期望 0x{expected_crc:04X}, 收到 0x{received_crc:04X}"
        super().__init__(message, slave_id)
        self.expected_crc = expected_crc
        self.received_crc = received_crc


class FrameError(ModbusError):
    """帧格式错误"""

    def __init__(
        self,
        message: str = "帧格式无效",
        raw_data: Optional[bytes] = None,
        slave_id: Optional[int] = None,
    ):
        """
        初始化

        Args:
            message: 错误消息
            raw_data: 原始数据
            slave_id: 从站地址
        """
        super().__init__(message, slave_id)
        self.raw_data = raw_data


class ResponseError(ModbusError):
    """响应错误"""

    def __init__(
        self,
        message: str,
        expected_slave_id: Optional[int] = None,
        received_slave_id: Optional[int] = None,
        expected_fc: Optional[int] = None,
        received_fc: Optional[int] = None,
    ):
        """
        初始化

        Args:
            message: 错误消息
            expected_slave_id: 期望的从站地址
            received_slave_id: 实际收到的从站地址
            expected_fc: 期望的功能码
            received_fc: 实际收到的功能码
        """
        super().__init__(message, expected_slave_id)
        self.expected_slave_id = expected_slave_id
        self.received_slave_id = received_slave_id
        self.expected_fc = expected_fc
        self.received_fc = received_fc


class SlaveIdMismatchError(ResponseError):
    """从站地址不匹配错误"""

    def __init__(self, expected_slave_id: int, received_slave_id: int):
        """
        初始化

        Args:
            expected_slave_id: 期望的从站地址
            received_slave_id: 实际收到的从站地址
        """
        message = f"从站地址不匹配: 期望 {expected_slave_id}, 收到 {received_slave_id}"
        super().__init__(
            message,
            expected_slave_id=expected_slave_id,
            received_slave_id=received_slave_id,
        )


class FunctionCodeMismatchError(ResponseError):
    """功能码不匹配错误"""

    def __init__(
        self,
        expected_fc: int,
        received_fc: int,
        slave_id: Optional[int] = None,
    ):
        """
        初始化

        Args:
            expected_fc: 期望的功能码
            received_fc: 实际收到的功能码
            slave_id: 从站地址
        """
        message = f"功能码不匹配: 期望 0x{expected_fc:02X}, 收到 0x{received_fc:02X}"
        super().__init__(
            message,
            expected_slave_id=slave_id,
            expected_fc=expected_fc,
            received_fc=received_fc,
        )


class TimeoutError(ModbusError):
    """Modbus 通信超时"""

    def __init__(
        self,
        timeout: float,
        slave_id: Optional[int] = None,
        message: Optional[str] = None,
    ):
        """
        初始化

        Args:
            timeout: 超时时间（秒）
            slave_id: 从站地址
            message: 自定义消息
        """
        if message is None:
            message = f"Modbus 通信超时 ({timeout}s)"
            if slave_id is not None:
                message += f", 从站地址: {slave_id}"
        super().__init__(message, slave_id)
        self.timeout = timeout


class NoResponseError(ModbusError):
    """无响应错误

    从站未响应请求。
    """

    def __init__(self, slave_id: Optional[int] = None, retries: int = 0):
        """
        初始化

        Args:
            slave_id: 从站地址
            retries: 重试次数
        """
        message = "从站无响应"
        if slave_id is not None:
            message = f"从站 {slave_id} 无响应"
        if retries > 0:
            message += f" (已重试 {retries} 次)"
        super().__init__(message, slave_id)
        self.retries = retries


class BroadcastError(ModbusError):
    """广播错误

    广播请求不应期待响应。
    """

    def __init__(self, message: str = "广播请求无响应"):
        """
        初始化

        Args:
            message: 错误消息
        """
        super().__init__(message, slave_id=0)
