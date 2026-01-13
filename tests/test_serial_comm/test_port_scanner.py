"""
串口扫描器测试
"""

from unittest.mock import MagicMock, patch

import pytest

from servo_service.serial_comm.port_scanner import PortInfo, PortScanner


class TestPortInfo:
    """测试 PortInfo 数据类"""

    def test_basic_creation(self) -> None:
        """测试基本创建"""
        info = PortInfo(
            device="/dev/ttyUSB0",
            description="USB Serial",
            hwid="USB VID:PID=0403:6001",
        )
        assert info.device == "/dev/ttyUSB0"
        assert info.description == "USB Serial"

    def test_display_name_with_description(self) -> None:
        """测试带描述的显示名"""
        info = PortInfo(
            device="/dev/ttyUSB0",
            description="USB Serial Port",
            hwid="",
        )
        assert info.display_name == "/dev/ttyUSB0 - USB Serial Port"

    def test_display_name_without_description(self) -> None:
        """测试无描述的显示名"""
        info = PortInfo(
            device="/dev/ttyUSB0",
            description="n/a",
            hwid="",
        )
        assert info.display_name == "/dev/ttyUSB0"

    def test_is_usb_true(self) -> None:
        """测试 USB 设备识别"""
        info = PortInfo(
            device="/dev/ttyUSB0",
            description="",
            hwid="",
            vid=0x0403,
            pid=0x6001,
        )
        assert info.is_usb is True

    def test_is_usb_false(self) -> None:
        """测试非 USB 设备"""
        info = PortInfo(
            device="/dev/ttyS0",
            description="",
            hwid="",
        )
        assert info.is_usb is False

    def test_str(self) -> None:
        """测试字符串表示"""
        info = PortInfo(
            device="COM3",
            description="USB Serial",
            hwid="",
        )
        assert str(info) == "COM3 - USB Serial"

    def test_from_list_port_info(self) -> None:
        """测试从 ListPortInfo 创建"""
        mock_info = MagicMock()
        mock_info.device = "/dev/ttyUSB0"
        mock_info.description = "Test Device"
        mock_info.hwid = "USB VID:PID=1234:5678"
        mock_info.manufacturer = "Test Mfg"
        mock_info.product = "Test Product"
        mock_info.serial_number = "12345"
        mock_info.vid = 0x1234
        mock_info.pid = 0x5678

        port_info = PortInfo.from_list_port_info(mock_info)

        assert port_info.device == "/dev/ttyUSB0"
        assert port_info.description == "Test Device"
        assert port_info.manufacturer == "Test Mfg"
        assert port_info.vid == 0x1234
        assert port_info.pid == 0x5678


class TestPortScanner:
    """测试 PortScanner"""

    def test_scan_ports_empty(self) -> None:
        """测试空扫描结果"""
        scanner = PortScanner()

        with patch("serial.tools.list_ports.comports", return_value=[]):
            ports = scanner.scan_ports()
            assert ports == []

    def test_scan_ports_with_results(self) -> None:
        """测试有结果的扫描"""
        scanner = PortScanner()

        mock_port1 = MagicMock()
        mock_port1.device = "/dev/ttyUSB0"
        mock_port1.description = "USB Serial 1"
        mock_port1.hwid = "USB VID:PID=0403:6001"
        mock_port1.manufacturer = None
        mock_port1.product = None
        mock_port1.serial_number = None
        mock_port1.vid = 0x0403
        mock_port1.pid = 0x6001

        mock_port2 = MagicMock()
        mock_port2.device = "/dev/ttyUSB1"
        mock_port2.description = "USB Serial 2"
        mock_port2.hwid = "USB VID:PID=1A86:7523"
        mock_port2.manufacturer = None
        mock_port2.product = None
        mock_port2.serial_number = None
        mock_port2.vid = 0x1A86
        mock_port2.pid = 0x7523

        with patch(
            "serial.tools.list_ports.comports",
            return_value=[mock_port2, mock_port1],
        ):
            ports = scanner.scan_ports()

            # 应该按设备名排序
            assert len(ports) == 2
            assert ports[0].device == "/dev/ttyUSB0"
            assert ports[1].device == "/dev/ttyUSB1"

    def test_is_port_available(self) -> None:
        """测试端口可用性检查"""
        scanner = PortScanner()

        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = ""
        mock_port.hwid = ""
        mock_port.manufacturer = None
        mock_port.product = None
        mock_port.serial_number = None
        mock_port.vid = None
        mock_port.pid = None

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            assert scanner.is_port_available("/dev/ttyUSB0") is True
            assert scanner.is_port_available("/dev/ttyUSB1") is False

    def test_find_port(self) -> None:
        """测试查找端口"""
        scanner = PortScanner()

        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "Test Port"
        mock_port.hwid = ""
        mock_port.manufacturer = None
        mock_port.product = None
        mock_port.serial_number = None
        mock_port.vid = None
        mock_port.pid = None

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            found = scanner.find_port("/dev/ttyUSB0")
            assert found is not None
            assert found.device == "/dev/ttyUSB0"

            not_found = scanner.find_port("/dev/ttyUSB1")
            assert not_found is None

    def test_find_rs485_adapters(self) -> None:
        """测试查找 RS485 适配器"""
        scanner = PortScanner()

        # FTDI FT232 - 已知 RS485 适配器
        mock_ftdi = MagicMock()
        mock_ftdi.device = "/dev/ttyUSB0"
        mock_ftdi.description = "FT232"
        mock_ftdi.hwid = ""
        mock_ftdi.manufacturer = None
        mock_ftdi.product = None
        mock_ftdi.serial_number = None
        mock_ftdi.vid = 0x0403
        mock_ftdi.pid = 0x6001

        # 未知设备
        mock_unknown = MagicMock()
        mock_unknown.device = "/dev/ttyUSB1"
        mock_unknown.description = "Unknown"
        mock_unknown.hwid = ""
        mock_unknown.manufacturer = None
        mock_unknown.product = None
        mock_unknown.serial_number = None
        mock_unknown.vid = 0x9999
        mock_unknown.pid = 0x9999

        with patch(
            "serial.tools.list_ports.comports",
            return_value=[mock_ftdi, mock_unknown],
        ):
            adapters = scanner.find_rs485_adapters()
            assert len(adapters) == 1
            assert adapters[0].device == "/dev/ttyUSB0"

    def test_find_by_vid_pid(self) -> None:
        """测试按 VID:PID 查找"""
        scanner = PortScanner()

        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = ""
        mock_port.hwid = ""
        mock_port.manufacturer = None
        mock_port.product = None
        mock_port.serial_number = None
        mock_port.vid = 0x1A86
        mock_port.pid = 0x7523

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            found = scanner.find_by_vid_pid(0x1A86, 0x7523)
            assert len(found) == 1
            assert found[0].device == "/dev/ttyUSB0"

            not_found = scanner.find_by_vid_pid(0x0000, 0x0000)
            assert len(not_found) == 0

    def test_find_by_serial_number(self) -> None:
        """测试按序列号查找"""
        scanner = PortScanner()

        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = ""
        mock_port.hwid = ""
        mock_port.manufacturer = None
        mock_port.product = None
        mock_port.serial_number = "ABC12345"
        mock_port.vid = None
        mock_port.pid = None

        with patch("serial.tools.list_ports.comports", return_value=[mock_port]):
            found = scanner.find_by_serial_number("ABC12345")
            assert found is not None
            assert found.device == "/dev/ttyUSB0"

            not_found = scanner.find_by_serial_number("XYZ")
            assert not_found is None

    def test_get_available_ports_caching(self) -> None:
        """测试缓存行为"""
        scanner = PortScanner()

        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = ""
        mock_port.hwid = ""
        mock_port.manufacturer = None
        mock_port.product = None
        mock_port.serial_number = None
        mock_port.vid = None
        mock_port.pid = None

        with patch(
            "serial.tools.list_ports.comports",
            return_value=[mock_port],
        ) as mock_comports:
            # 第一次调用
            ports1 = scanner.get_available_ports()
            assert len(ports1) == 1
            assert mock_comports.call_count == 1

            # 第二次调用应该使用缓存
            ports2 = scanner.get_available_ports()
            assert len(ports2) == 1
            assert mock_comports.call_count == 1

            # refresh 应该重新扫描
            scanner.refresh()
            assert mock_comports.call_count == 2

    def test_get_platform_port_prefix(self) -> None:
        """测试平台前缀"""
        with patch("sys.platform", "linux"):
            assert PortScanner.get_platform_port_prefix() == "/dev/ttyUSB"

        with patch("sys.platform", "darwin"):
            assert PortScanner.get_platform_port_prefix() == "/dev/cu."

        with patch("sys.platform", "win32"):
            assert PortScanner.get_platform_port_prefix() == "COM"
