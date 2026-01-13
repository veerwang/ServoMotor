"""
串口通信类测试
"""

from unittest.mock import MagicMock, patch

import pytest
import serial

from servo_service.serial_comm.exceptions import (
    PortAccessError,
    PortConfigError,
    PortNotFoundError,
    PortNotOpenError,
    PortOpenError,
    ReadTimeoutError,
    WriteError,
)
from servo_service.serial_comm.serial_port import SerialPort


class TestSerialPortInit:
    """测试 SerialPort 初始化"""

    def test_default_config(self) -> None:
        """测试默认配置"""
        port = SerialPort()
        assert port.port_name is None
        assert port.baudrate == 115200
        assert port.is_open is False

    def test_custom_config(self) -> None:
        """测试自定义配置"""
        port = SerialPort(
            port="/dev/ttyUSB0",
            baudrate=9600,
            timeout=0.5,
        )
        assert port.port_name == "/dev/ttyUSB0"
        assert port.baudrate == 9600
        assert port.timeout == 0.5


class TestSerialPortOpen:
    """测试串口打开"""

    def test_open_success(self) -> None:
        """测试成功打开"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()

            assert port.is_open is True
            mock_serial.assert_called_once()

    def test_open_with_port_parameter(self) -> None:
        """测试带端口参数打开"""
        port = SerialPort()

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open("/dev/ttyUSB0")

            assert port.port_name == "/dev/ttyUSB0"
            assert port.is_open is True

    def test_open_no_port_name(self) -> None:
        """测试无端口名时抛出异常"""
        port = SerialPort()

        with pytest.raises(PortOpenError) as exc_info:
            port.open()
        assert "未指定" in str(exc_info.value)

    def test_open_already_open(self) -> None:
        """测试已打开时再次打开"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.open()  # 应该不抛异常，只是警告

            # Serial 只应该被调用一次
            mock_serial.assert_called_once()

    def test_open_port_not_found(self) -> None:
        """测试端口不存在"""
        port = SerialPort(port="/dev/ttyUSB99")

        with patch("serial.Serial") as mock_serial:
            mock_serial.side_effect = serial.SerialException("no such file")

            with pytest.raises(PortNotFoundError):
                port.open()

    def test_open_permission_denied(self) -> None:
        """测试权限被拒绝"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_serial.side_effect = serial.SerialException("permission denied")

            with pytest.raises(PortAccessError):
                port.open()

    def test_open_other_error(self) -> None:
        """测试其他错误"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_serial.side_effect = serial.SerialException("device busy")

            with pytest.raises(PortOpenError):
                port.open()


class TestSerialPortClose:
    """测试串口关闭"""

    def test_close_open_port(self) -> None:
        """测试关闭已打开的端口"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.close()

            mock_instance.close.assert_called_once()
            assert port.is_open is False

    def test_close_not_open_port(self) -> None:
        """测试关闭未打开的端口"""
        port = SerialPort(port="/dev/ttyUSB0")
        port.close()  # 应该不抛异常


class TestSerialPortWrite:
    """测试串口写入"""

    def test_write_success(self) -> None:
        """测试成功写入"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.write.return_value = 5
            mock_serial.return_value = mock_instance

            port.open()
            result = port.write(b"\x01\x02\x03\x04\x05")

            assert result == 5
            mock_instance.write.assert_called_once_with(b"\x01\x02\x03\x04\x05")

    def test_write_not_open(self) -> None:
        """测试未打开时写入"""
        port = SerialPort(port="/dev/ttyUSB0")

        with pytest.raises(PortNotOpenError):
            port.write(b"\x01")

    def test_write_error(self) -> None:
        """测试写入错误"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.write.side_effect = serial.SerialException("write error")
            mock_serial.return_value = mock_instance

            port.open()

            with pytest.raises(WriteError):
                port.write(b"\x01")


class TestSerialPortRead:
    """测试串口读取"""

    def test_read_success(self) -> None:
        """测试成功读取"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.read.return_value = b"\x01\x02\x03"
            mock_serial.return_value = mock_instance

            port.open()
            result = port.read(3)

            assert result == b"\x01\x02\x03"

    def test_read_not_open(self) -> None:
        """测试未打开时读取"""
        port = SerialPort(port="/dev/ttyUSB0")

        with pytest.raises(PortNotOpenError):
            port.read(1)

    def test_read_all_success(self) -> None:
        """测试读取全部数据"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.in_waiting = 5
            mock_instance.read.return_value = b"\x01\x02\x03\x04\x05"
            mock_serial.return_value = mock_instance

            port.open()
            result = port.read_all()

            assert result == b"\x01\x02\x03\x04\x05"

    def test_read_until_success(self) -> None:
        """测试读取直到达到长度"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            # 模拟分两次读取
            mock_instance.read.side_effect = [b"\x01\x02", b"\x03\x04\x05"]
            mock_serial.return_value = mock_instance

            port.open()
            result = port.read_until(expected_length=5, timeout=1.0)

            assert result == b"\x01\x02\x03\x04\x05"

    def test_read_until_timeout(self) -> None:
        """测试读取超时"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.read.return_value = b""  # 没有数据
            mock_serial.return_value = mock_instance

            port.open()

            with pytest.raises(ReadTimeoutError) as exc_info:
                port.read_until(expected_length=5, timeout=0.1)

            assert exc_info.value.expected_bytes == 5
            assert exc_info.value.received_bytes == 0


class TestSerialPortFlush:
    """测试缓冲区清空"""

    def test_flush_input(self) -> None:
        """测试清空输入缓冲区"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.flush_input()

            mock_instance.reset_input_buffer.assert_called_once()

    def test_flush_output(self) -> None:
        """测试清空输出缓冲区"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.flush_output()

            mock_instance.reset_output_buffer.assert_called_once()


class TestSerialPortConfig:
    """测试串口配置"""

    def test_set_baudrate_valid(self) -> None:
        """测试设置有效波特率"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.set_baudrate(9600)

            assert port.baudrate == 9600
            assert mock_instance.baudrate == 9600

    def test_set_baudrate_invalid(self) -> None:
        """测试设置无效波特率"""
        port = SerialPort()

        with pytest.raises(PortConfigError) as exc_info:
            port.set_baudrate(999999)

        assert exc_info.value.parameter == "baudrate"

    def test_configure(self) -> None:
        """测试配置多个参数"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.configure(baudrate=9600, timeout=0.5)

            assert port.baudrate == 9600
            assert port.timeout == 0.5

    def test_timeout_setter(self) -> None:
        """测试超时设置器"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            port.timeout = 0.5

            assert port.timeout == 0.5
            assert mock_instance.timeout == 0.5


class TestSerialPortProperties:
    """测试属性访问"""

    def test_in_waiting(self) -> None:
        """测试输入缓冲区字节数"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.in_waiting = 10
            mock_serial.return_value = mock_instance

            port.open()
            assert port.in_waiting == 10

    def test_out_waiting(self) -> None:
        """测试输出缓冲区字节数"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_instance.out_waiting = 5
            mock_serial.return_value = mock_instance

            port.open()
            assert port.out_waiting == 5

    def test_in_waiting_closed(self) -> None:
        """测试关闭状态下的输入缓冲区"""
        port = SerialPort()
        assert port.in_waiting == 0


class TestSerialPortContextManager:
    """测试上下文管理器"""

    def test_context_manager(self) -> None:
        """测试 with 语句"""
        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            with SerialPort(port="/dev/ttyUSB0") as port:
                assert port.is_open is True

            mock_instance.close.assert_called()


class TestSerialPortRepr:
    """测试字符串表示"""

    def test_repr_closed(self) -> None:
        """测试关闭状态的表示"""
        port = SerialPort(port="/dev/ttyUSB0", baudrate=9600)
        assert "ttyUSB0" in repr(port)
        assert "9600" in repr(port)
        assert "closed" in repr(port)

    def test_repr_open(self) -> None:
        """测试打开状态的表示"""
        port = SerialPort(port="/dev/ttyUSB0")

        with patch("serial.Serial") as mock_serial:
            mock_instance = MagicMock()
            mock_instance.is_open = True
            mock_serial.return_value = mock_instance

            port.open()
            assert "open" in repr(port)
