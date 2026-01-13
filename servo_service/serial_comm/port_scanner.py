"""
串口扫描模块

提供串口设备的发现和信息获取功能。
"""

import sys
from dataclasses import dataclass
from typing import List, Optional

import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo


@dataclass
class PortInfo:
    """串口信息数据类"""

    device: str
    """设备路径 (如 /dev/ttyUSB0 或 COM1)"""

    description: str
    """设备描述"""

    hwid: str
    """硬件ID"""

    manufacturer: Optional[str] = None
    """制造商"""

    product: Optional[str] = None
    """产品名称"""

    serial_number: Optional[str] = None
    """序列号"""

    vid: Optional[int] = None
    """USB Vendor ID"""

    pid: Optional[int] = None
    """USB Product ID"""

    @classmethod
    def from_list_port_info(cls, info: ListPortInfo) -> "PortInfo":
        """
        从 serial.tools.list_ports 的 ListPortInfo 创建 PortInfo

        Args:
            info: ListPortInfo 对象

        Returns:
            PortInfo 实例
        """
        return cls(
            device=info.device,
            description=info.description or "",
            hwid=info.hwid or "",
            manufacturer=info.manufacturer,
            product=info.product,
            serial_number=info.serial_number,
            vid=info.vid,
            pid=info.pid,
        )

    @property
    def display_name(self) -> str:
        """获取用于显示的名称"""
        if self.description and self.description != "n/a":
            return f"{self.device} - {self.description}"
        return self.device

    @property
    def is_usb(self) -> bool:
        """是否为 USB 串口设备"""
        return self.vid is not None and self.pid is not None

    def __str__(self) -> str:
        return self.display_name


class PortScanner:
    """
    串口扫描器

    用于发现系统中可用的串口设备。
    """

    # 常见的 USB-RS485 适配器 VID:PID
    KNOWN_RS485_ADAPTERS = [
        (0x0403, 0x6001),  # FTDI FT232
        (0x0403, 0x6015),  # FTDI FT231X
        (0x067B, 0x2303),  # Prolific PL2303
        (0x10C4, 0xEA60),  # Silicon Labs CP210x
        (0x1A86, 0x7523),  # QinHeng CH340
        (0x1A86, 0x55D4),  # QinHeng CH9102
    ]

    def __init__(self) -> None:
        """初始化串口扫描器"""
        self._cached_ports: List[PortInfo] = []

    def scan_ports(self, include_links: bool = False) -> List[PortInfo]:
        """
        扫描系统中可用的串口

        Args:
            include_links: 是否包含符号链接 (仅 Linux)

        Returns:
            PortInfo 列表
        """
        ports: List[PortInfo] = []

        for port_info in serial.tools.list_ports.comports(include_links=include_links):
            ports.append(PortInfo.from_list_port_info(port_info))

        # 按设备名排序
        ports.sort(key=lambda p: p.device)

        # 更新缓存
        self._cached_ports = ports

        return ports

    def get_available_ports(self) -> List[PortInfo]:
        """
        获取可用串口列表 (使用缓存)

        Returns:
            PortInfo 列表
        """
        if not self._cached_ports:
            return self.scan_ports()
        return self._cached_ports

    def refresh(self) -> List[PortInfo]:
        """
        刷新串口列表

        Returns:
            更新后的 PortInfo 列表
        """
        return self.scan_ports()

    def is_port_available(self, port_name: str) -> bool:
        """
        检查指定串口是否可用

        Args:
            port_name: 串口名称

        Returns:
            是否可用
        """
        ports = self.scan_ports()
        return any(p.device == port_name for p in ports)

    def find_port(self, port_name: str) -> Optional[PortInfo]:
        """
        查找指定串口

        Args:
            port_name: 串口名称

        Returns:
            PortInfo 或 None
        """
        ports = self.scan_ports()
        for port in ports:
            if port.device == port_name:
                return port
        return None

    def find_rs485_adapters(self) -> List[PortInfo]:
        """
        查找可能的 RS-485 适配器

        Returns:
            可能是 RS-485 适配器的 PortInfo 列表
        """
        ports = self.scan_ports()
        adapters: List[PortInfo] = []

        for port in ports:
            if port.is_usb:
                for vid, pid in self.KNOWN_RS485_ADAPTERS:
                    if port.vid == vid and port.pid == pid:
                        adapters.append(port)
                        break

        return adapters

    def find_by_vid_pid(self, vid: int, pid: int) -> List[PortInfo]:
        """
        根据 VID:PID 查找串口

        Args:
            vid: Vendor ID
            pid: Product ID

        Returns:
            匹配的 PortInfo 列表
        """
        ports = self.scan_ports()
        return [p for p in ports if p.vid == vid and p.pid == pid]

    def find_by_serial_number(self, serial_number: str) -> Optional[PortInfo]:
        """
        根据序列号查找串口

        Args:
            serial_number: 设备序列号

        Returns:
            匹配的 PortInfo 或 None
        """
        ports = self.scan_ports()
        for port in ports:
            if port.serial_number == serial_number:
                return port
        return None

    @staticmethod
    def get_platform_port_prefix() -> str:
        """
        获取当前平台的串口前缀

        Returns:
            串口前缀 (如 '/dev/ttyUSB' 或 'COM')
        """
        if sys.platform.startswith("linux"):
            return "/dev/ttyUSB"
        elif sys.platform == "darwin":
            return "/dev/cu."
        elif sys.platform == "win32":
            return "COM"
        return ""
