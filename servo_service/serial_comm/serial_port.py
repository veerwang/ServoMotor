"""
串口通信核心模块

提供线程安全的串口读写操作。
"""

import logging
import threading
import time
from typing import Optional

import serial
from serial import SerialException

from .exceptions import (
    PortAccessError,
    PortConfigError,
    PortNotFoundError,
    PortNotOpenError,
    PortOpenError,
    ReadTimeoutError,
    WriteError,
)

logger = logging.getLogger(__name__)


class SerialPort:
    """
    串口通信类

    提供线程安全的串口操作，包括打开/关闭、读写、配置等功能。
    """

    # 默认配置
    DEFAULT_BAUDRATE = 115200
    DEFAULT_BYTESIZE = serial.EIGHTBITS
    DEFAULT_PARITY = serial.PARITY_NONE
    DEFAULT_STOPBITS = serial.STOPBITS_ONE
    DEFAULT_TIMEOUT = 0.1  # 100ms
    DEFAULT_WRITE_TIMEOUT = 0.1

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = DEFAULT_BAUDRATE,
        bytesize: int = DEFAULT_BYTESIZE,
        parity: str = DEFAULT_PARITY,
        stopbits: float = DEFAULT_STOPBITS,
        timeout: float = DEFAULT_TIMEOUT,
        write_timeout: float = DEFAULT_WRITE_TIMEOUT,
    ) -> None:
        """
        初始化串口

        Args:
            port: 串口名称 (如 /dev/ttyUSB0 或 COM1)
            baudrate: 波特率
            bytesize: 数据位
            parity: 校验位
            stopbits: 停止位
            timeout: 读取超时 (秒)
            write_timeout: 写入超时 (秒)
        """
        self._port_name = port
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._timeout = timeout
        self._write_timeout = write_timeout

        self._serial: Optional[serial.Serial] = None
        self._lock = threading.RLock()
        self._is_open = False

    @property
    def port_name(self) -> Optional[str]:
        """获取串口名称"""
        return self._port_name

    @property
    def baudrate(self) -> int:
        """获取波特率"""
        return self._baudrate

    @property
    def is_open(self) -> bool:
        """检查串口是否已打开"""
        with self._lock:
            return self._is_open and self._serial is not None and self._serial.is_open

    @property
    def timeout(self) -> float:
        """获取读取超时"""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        """设置读取超时"""
        self._timeout = value
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                self._serial.timeout = value

    def open(self, port: Optional[str] = None) -> None:
        """
        打开串口

        Args:
            port: 串口名称 (如果不指定则使用构造函数中的设置)

        Raises:
            PortNotFoundError: 串口不存在
            PortAccessError: 无权限访问
            PortOpenError: 打开失败
        """
        if port is not None:
            self._port_name = port

        if not self._port_name:
            raise PortOpenError("", "未指定串口名称")

        with self._lock:
            if self._is_open:
                logger.warning(f"串口 {self._port_name} 已经打开")
                return

            try:
                self._serial = serial.Serial(
                    port=self._port_name,
                    baudrate=self._baudrate,
                    bytesize=self._bytesize,
                    parity=self._parity,
                    stopbits=self._stopbits,
                    timeout=self._timeout,
                    write_timeout=self._write_timeout,
                )
                self._is_open = True
                logger.info(
                    f"串口 {self._port_name} 已打开 "
                    f"(波特率: {self._baudrate}, 超时: {self._timeout}s)"
                )

            except SerialException as e:
                error_msg = str(e).lower()
                if "no such file" in error_msg or "filenotfounderror" in error_msg:
                    raise PortNotFoundError(self._port_name) from e
                elif "permission" in error_msg or "access" in error_msg:
                    raise PortAccessError(self._port_name) from e
                else:
                    raise PortOpenError(self._port_name, str(e)) from e
            except PermissionError as e:
                raise PortAccessError(self._port_name) from e
            except FileNotFoundError as e:
                raise PortNotFoundError(self._port_name) from e
            except Exception as e:
                raise PortOpenError(self._port_name, str(e)) from e

    def close(self) -> None:
        """关闭串口"""
        with self._lock:
            if self._serial is not None:
                try:
                    if self._serial.is_open:
                        self._serial.close()
                        logger.info(f"串口 {self._port_name} 已关闭")
                except Exception as e:
                    logger.error(f"关闭串口时出错: {e}")
                finally:
                    self._serial = None
                    self._is_open = False

    def write(self, data: bytes) -> int:
        """
        写入数据

        Args:
            data: 要写入的数据

        Returns:
            实际写入的字节数

        Raises:
            PortNotOpenError: 串口未打开
            WriteError: 写入失败
        """
        with self._lock:
            if not self.is_open:
                raise PortNotOpenError(self._port_name)

            try:
                bytes_written = self._serial.write(data)  # type: ignore
                self._serial.flush()  # type: ignore
                logger.debug(f"写入 {bytes_written} 字节: {data.hex()}")
                return bytes_written

            except SerialException as e:
                raise WriteError(str(e), len(data)) from e
            except Exception as e:
                raise WriteError(str(e), len(data)) from e

    def read(self, size: int = 1) -> bytes:
        """
        读取指定字节数的数据

        Args:
            size: 要读取的字节数

        Returns:
            读取到的数据

        Raises:
            PortNotOpenError: 串口未打开
        """
        with self._lock:
            if not self.is_open:
                raise PortNotOpenError(self._port_name)

            try:
                data = self._serial.read(size)  # type: ignore
                if data:
                    logger.debug(f"读取 {len(data)} 字节: {data.hex()}")
                return data

            except Exception as e:
                logger.error(f"读取数据时出错: {e}")
                return b""

    def read_all(self) -> bytes:
        """
        读取所有可用数据

        Returns:
            读取到的数据

        Raises:
            PortNotOpenError: 串口未打开
        """
        with self._lock:
            if not self.is_open:
                raise PortNotOpenError(self._port_name)

            try:
                # 先等待一小段时间让数据到达
                time.sleep(0.01)
                in_waiting = self._serial.in_waiting  # type: ignore
                if in_waiting > 0:
                    data = self._serial.read(in_waiting)  # type: ignore
                    logger.debug(f"读取全部 {len(data)} 字节: {data.hex()}")
                    return data
                return b""

            except Exception as e:
                logger.error(f"读取数据时出错: {e}")
                return b""

    def read_until(
        self,
        expected_length: int,
        timeout: Optional[float] = None,
    ) -> bytes:
        """
        读取数据直到达到指定长度或超时

        Args:
            expected_length: 期望读取的字节数
            timeout: 超时时间 (秒), None 则使用默认超时

        Returns:
            读取到的数据

        Raises:
            PortNotOpenError: 串口未打开
            ReadTimeoutError: 读取超时
        """
        with self._lock:
            if not self.is_open:
                raise PortNotOpenError(self._port_name)

            if timeout is None:
                timeout = self._timeout

            data = b""
            start_time = time.time()

            while len(data) < expected_length:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise ReadTimeoutError(
                        timeout=timeout,
                        expected_bytes=expected_length,
                        received_bytes=len(data),
                    )

                remaining = expected_length - len(data)
                # 设置剩余超时
                self._serial.timeout = max(0.001, timeout - elapsed)  # type: ignore

                try:
                    chunk = self._serial.read(remaining)  # type: ignore
                    if chunk:
                        data += chunk
                except Exception as e:
                    logger.error(f"读取数据时出错: {e}")
                    break

            # 恢复原始超时
            self._serial.timeout = self._timeout  # type: ignore

            if data:
                logger.debug(f"读取 {len(data)} 字节: {data.hex()}")

            return data

    def flush_input(self) -> None:
        """清空输入缓冲区"""
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                self._serial.reset_input_buffer()
                logger.debug("输入缓冲区已清空")

    def flush_output(self) -> None:
        """清空输出缓冲区"""
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                self._serial.reset_output_buffer()
                logger.debug("输出缓冲区已清空")

    def flush(self) -> None:
        """清空所有缓冲区"""
        self.flush_input()
        self.flush_output()

    @property
    def in_waiting(self) -> int:
        """获取输入缓冲区中等待的字节数"""
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                return self._serial.in_waiting
            return 0

    @property
    def out_waiting(self) -> int:
        """获取输出缓冲区中等待的字节数"""
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                return self._serial.out_waiting
            return 0

    def set_baudrate(self, baudrate: int) -> None:
        """
        设置波特率

        Args:
            baudrate: 波特率

        Raises:
            PortConfigError: 配置失败
        """
        valid_baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        if baudrate not in valid_baudrates:
            raise PortConfigError(
                f"不支持的波特率: {baudrate}",
                parameter="baudrate",
                value=str(baudrate),
            )

        self._baudrate = baudrate
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                self._serial.baudrate = baudrate
                logger.info(f"波特率已设置为 {baudrate}")

    def configure(
        self,
        baudrate: Optional[int] = None,
        bytesize: Optional[int] = None,
        parity: Optional[str] = None,
        stopbits: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        配置串口参数

        Args:
            baudrate: 波特率
            bytesize: 数据位
            parity: 校验位
            stopbits: 停止位
            timeout: 超时时间

        Raises:
            PortConfigError: 配置失败
        """
        with self._lock:
            if baudrate is not None:
                self._baudrate = baudrate
                if self._serial:
                    self._serial.baudrate = baudrate

            if bytesize is not None:
                self._bytesize = bytesize
                if self._serial:
                    self._serial.bytesize = bytesize

            if parity is not None:
                self._parity = parity
                if self._serial:
                    self._serial.parity = parity

            if stopbits is not None:
                self._stopbits = stopbits
                if self._serial:
                    self._serial.stopbits = stopbits

            if timeout is not None:
                self._timeout = timeout
                if self._serial:
                    self._serial.timeout = timeout

            logger.info(
                f"串口配置已更新: baudrate={self._baudrate}, "
                f"bytesize={self._bytesize}, parity={self._parity}, "
                f"stopbits={self._stopbits}, timeout={self._timeout}"
            )

    def send_break(self, duration: float = 0.25) -> None:
        """
        发送 Break 信号

        Args:
            duration: 持续时间 (秒)
        """
        with self._lock:
            if self._serial is not None and self._serial.is_open:
                self._serial.send_break(duration)
                logger.debug(f"已发送 Break 信号 ({duration}s)")

    def __enter__(self) -> "SerialPort":
        """上下文管理器入口"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """上下文管理器出口"""
        self.close()

    def __repr__(self) -> str:
        status = "open" if self.is_open else "closed"
        return f"SerialPort({self._port_name}, {self._baudrate}, {status})"
