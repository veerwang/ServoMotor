"""
串口异常类测试
"""

import pytest

from servo_service.serial_comm.exceptions import (
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


class TestSerialCommError:
    """测试 SerialCommError 基类"""

    def test_basic_message(self) -> None:
        """测试基本消息"""
        error = SerialCommError("测试错误")
        assert str(error) == "测试错误"
        assert error.message == "测试错误"
        assert error.details == {}

    def test_with_details(self) -> None:
        """测试带详细信息"""
        error = SerialCommError("测试错误", details={"key": "value"})
        assert error.details == {"key": "value"}


class TestSerialPortError:
    """测试 SerialPortError"""

    def test_with_port_name(self) -> None:
        """测试带端口名"""
        error = SerialPortError("端口错误", port_name="/dev/ttyUSB0")
        assert error.port_name == "/dev/ttyUSB0"
        assert error.details["port_name"] == "/dev/ttyUSB0"


class TestPortNotFoundError:
    """测试 PortNotFoundError"""

    def test_message_format(self) -> None:
        """测试消息格式"""
        error = PortNotFoundError("/dev/ttyUSB0")
        assert "ttyUSB0" in str(error)
        assert error.port_name == "/dev/ttyUSB0"


class TestPortOpenError:
    """测试 PortOpenError"""

    def test_without_reason(self) -> None:
        """测试无原因"""
        error = PortOpenError("/dev/ttyUSB0")
        assert "ttyUSB0" in str(error)
        assert error.reason == ""

    def test_with_reason(self) -> None:
        """测试带原因"""
        error = PortOpenError("/dev/ttyUSB0", "设备忙")
        assert "设备忙" in str(error)
        assert error.reason == "设备忙"


class TestPortAccessError:
    """测试 PortAccessError"""

    def test_message_format(self) -> None:
        """测试消息格式"""
        error = PortAccessError("/dev/ttyUSB0")
        assert "权限" in str(error)
        assert error.port_name == "/dev/ttyUSB0"


class TestPortNotOpenError:
    """测试 PortNotOpenError"""

    def test_without_port_name(self) -> None:
        """测试无端口名"""
        error = PortNotOpenError()
        assert "未打开" in str(error)

    def test_with_port_name(self) -> None:
        """测试带端口名"""
        error = PortNotOpenError("/dev/ttyUSB0")
        assert "ttyUSB0" in str(error)


class TestReadTimeoutError:
    """测试 ReadTimeoutError"""

    def test_basic_timeout(self) -> None:
        """测试基本超时"""
        error = ReadTimeoutError(timeout=0.5)
        assert "0.5" in str(error)
        assert error.timeout == 0.5
        assert error.expected_bytes == 0
        assert error.received_bytes == 0

    def test_with_bytes_info(self) -> None:
        """测试带字节信息"""
        error = ReadTimeoutError(timeout=1.0, expected_bytes=10, received_bytes=5)
        assert "10" in str(error)
        assert "5" in str(error)
        assert error.expected_bytes == 10
        assert error.received_bytes == 5


class TestWriteError:
    """测试 WriteError"""

    def test_default_message(self) -> None:
        """测试默认消息"""
        error = WriteError()
        assert "写入失败" in str(error)

    def test_with_bytes_count(self) -> None:
        """测试带字节数"""
        error = WriteError("写入错误", bytes_to_write=100)
        assert error.bytes_to_write == 100


class TestPortConfigError:
    """测试 PortConfigError"""

    def test_with_parameter(self) -> None:
        """测试带参数信息"""
        error = PortConfigError("无效波特率", parameter="baudrate", value="999999")
        assert error.parameter == "baudrate"
        assert error.value == "999999"
