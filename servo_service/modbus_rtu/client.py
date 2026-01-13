"""
Modbus RTU 客户端模块

提供 Modbus RTU 主站通信功能。
"""

import logging
import time
from typing import List, Optional, Union

from ..serial_comm import ReadTimeoutError, SerialPort
from .crc import verify_crc
from .exceptions import (
    CRCError,
    FrameError,
    FunctionCodeMismatchError,
    ModbusError,
    ModbusExceptionResponse,
    NoResponseError,
    SlaveIdMismatchError,
    TimeoutError,
)
from .frame import (
    FunctionCode,
    FrameBuilder,
    ModbusRequest,
    ModbusResponse,
    calculate_response_length,
)

logger = logging.getLogger(__name__)


class ModbusClient:
    """
    Modbus RTU 客户端

    提供线程安全的 Modbus RTU 通信功能。
    """

    # 默认配置
    DEFAULT_TIMEOUT = 0.5  # 500ms
    DEFAULT_RETRIES = 3
    DEFAULT_FRAME_INTERVAL = 0.003  # 3ms (约 3.5 字符时间 @115200)

    def __init__(
        self,
        serial_port: Optional[SerialPort] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        frame_interval: float = DEFAULT_FRAME_INTERVAL,
    ) -> None:
        """
        初始化 Modbus 客户端

        Args:
            serial_port: 串口实例 (可后续通过 connect 设置)
            timeout: 响应超时 (秒)
            retries: 重试次数
            frame_interval: 帧间隔 (秒)
        """
        self._serial = serial_port
        self._timeout = timeout
        self._retries = retries
        self._frame_interval = frame_interval

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._serial is not None and self._serial.is_open

    @property
    def timeout(self) -> float:
        """获取超时设置"""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        """设置超时"""
        self._timeout = value

    @property
    def retries(self) -> int:
        """获取重试次数"""
        return self._retries

    @retries.setter
    def retries(self, value: int) -> None:
        """设置重试次数"""
        self._retries = max(0, value)

    def connect(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        serial_port: Optional[SerialPort] = None,
    ) -> None:
        """
        连接到从站

        Args:
            port: 串口名称
            baudrate: 波特率
            serial_port: 已有的串口实例 (如果提供则忽略 port 和 baudrate)
        """
        if serial_port is not None:
            self._serial = serial_port
        else:
            self._serial = SerialPort(
                port=port,
                baudrate=baudrate,
                timeout=self._timeout,
            )

        if not self._serial.is_open:
            self._serial.open()

        logger.info(f"Modbus 客户端已连接: {self._serial.port_name}")

    def disconnect(self) -> None:
        """断开连接"""
        if self._serial is not None:
            self._serial.close()
            logger.info("Modbus 客户端已断开连接")

    def send_request(
        self,
        request: ModbusRequest,
        expected_length: Optional[int] = None,
    ) -> ModbusResponse:
        """
        发送请求并接收响应

        Args:
            request: Modbus 请求
            expected_length: 预期响应长度 (None 则自动计算)

        Returns:
            ModbusResponse

        Raises:
            ModbusError: 通信错误
        """
        if not self.is_connected:
            raise ModbusError("未连接到从站")

        # 广播请求不需要响应
        if request.is_broadcast:
            self._send_frame(request.to_bytes())
            time.sleep(self._frame_interval)
            return ModbusResponse(
                slave_id=0,
                function_code=request.function_code,
                data=b"",
            )

        last_error: Optional[Exception] = None

        for attempt in range(self._retries + 1):
            try:
                # 清空接收缓冲区
                self._serial.flush_input()  # type: ignore

                # 发送请求
                frame = request.to_bytes()
                self._send_frame(frame)

                # 等待帧间隔
                time.sleep(self._frame_interval)

                # 接收响应
                response = self._receive_response(
                    request.slave_id,
                    request.function_code,
                    expected_length,
                )

                return response

            except (ReadTimeoutError, CRCError, FrameError) as e:
                last_error = e
                logger.warning(
                    f"Modbus 请求失败 (尝试 {attempt + 1}/{self._retries + 1}): {e}"
                )
                if attempt < self._retries:
                    time.sleep(self._frame_interval * 2)
                continue

        # 所有重试都失败
        if isinstance(last_error, ReadTimeoutError):
            raise NoResponseError(request.slave_id, self._retries)
        raise last_error or NoResponseError(request.slave_id, self._retries)

    def _send_frame(self, frame: bytes) -> None:
        """发送帧"""
        if self._serial is None:
            raise ModbusError("串口未初始化")

        logger.debug(f"发送: {frame.hex()}")
        self._serial.write(frame)

    def _receive_response(
        self,
        expected_slave_id: int,
        expected_fc: int,
        expected_length: Optional[int] = None,
    ) -> ModbusResponse:
        """
        接收响应

        Args:
            expected_slave_id: 期望的从站地址
            expected_fc: 期望的功能码
            expected_length: 期望的响应长度

        Returns:
            ModbusResponse
        """
        if self._serial is None:
            raise ModbusError("串口未初始化")

        # 首先读取头部 (slave_id + fc)
        header = self._serial.read_until(2, timeout=self._timeout)
        if len(header) < 2:
            raise TimeoutError(self._timeout, expected_slave_id)

        slave_id = header[0]
        function_code = header[1]

        # 检查从站地址
        if slave_id != expected_slave_id:
            raise SlaveIdMismatchError(expected_slave_id, slave_id)

        # 检查是否为异常响应
        is_exception = (function_code & 0x80) != 0

        if is_exception:
            # 异常响应: 读取 1 字节异常码 + 2 字节 CRC
            remaining = self._serial.read_until(3, timeout=self._timeout)
            raw_data = header + remaining
        else:
            # 正常响应
            if expected_length is not None:
                # 读取剩余数据
                remaining_length = expected_length - 2
                remaining = self._serial.read_until(remaining_length, timeout=self._timeout)
                raw_data = header + remaining
            else:
                # 根据功能码决定读取策略
                raw_data = self._read_response_by_fc(header, function_code)

        logger.debug(f"接收: {raw_data.hex()}")

        # 解析响应
        response = ModbusResponse.from_bytes(raw_data, validate_crc=True)

        # 检查功能码 (不考虑异常标志)
        if not is_exception and (function_code & 0x7F) != (expected_fc & 0x7F):
            raise FunctionCodeMismatchError(expected_fc, function_code, slave_id)

        return response

    def _read_response_by_fc(self, header: bytes, function_code: int) -> bytes:
        """根据功能码读取响应"""
        if self._serial is None:
            raise ModbusError("串口未初始化")

        if function_code in (FunctionCode.READ_HOLDING_REGISTERS, FunctionCode.READ_INPUT_REGISTERS):
            # 读取字节计数
            byte_count_data = self._serial.read_until(1, timeout=self._timeout)
            if len(byte_count_data) < 1:
                raise TimeoutError(self._timeout)

            byte_count = byte_count_data[0]
            # 读取数据 + CRC
            remaining = self._serial.read_until(byte_count + 2, timeout=self._timeout)
            return header + byte_count_data + remaining

        elif function_code in (
            FunctionCode.WRITE_SINGLE_REGISTER,
            FunctionCode.WRITE_MULTIPLE_REGISTERS,
        ):
            # 固定长度: address(2) + value/quantity(2) + CRC(2)
            remaining = self._serial.read_until(6, timeout=self._timeout)
            return header + remaining

        else:
            # 其他功能码尝试读取默认长度
            remaining = self._serial.read_until(6, timeout=self._timeout)
            return header + remaining

    # ==================== 高级 API ====================

    def read_holding_registers(
        self,
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> List[int]:
        """
        读取保持寄存器 (FC=0x03)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            quantity: 读取数量

        Returns:
            寄存器值列表
        """
        request = FrameBuilder.build_read_holding_registers(
            slave_id, start_address, quantity
        )
        expected_length = calculate_response_length(
            FunctionCode.READ_HOLDING_REGISTERS, quantity
        )
        response = self.send_request(request, expected_length)
        response.raise_for_exception()
        return response.get_registers()

    def read_input_registers(
        self,
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> List[int]:
        """
        读取输入寄存器 (FC=0x04)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            quantity: 读取数量

        Returns:
            寄存器值列表
        """
        request = FrameBuilder.build_read_input_registers(
            slave_id, start_address, quantity
        )
        expected_length = calculate_response_length(
            FunctionCode.READ_INPUT_REGISTERS, quantity
        )
        response = self.send_request(request, expected_length)
        response.raise_for_exception()
        return response.get_registers()

    def write_single_register(
        self,
        slave_id: int,
        address: int,
        value: int,
    ) -> None:
        """
        写入单个寄存器 (FC=0x06)

        Args:
            slave_id: 从站地址
            address: 寄存器地址
            value: 寄存器值
        """
        request = FrameBuilder.build_write_single_register(slave_id, address, value)
        expected_length = calculate_response_length(FunctionCode.WRITE_SINGLE_REGISTER)
        response = self.send_request(request, expected_length)
        response.raise_for_exception()

    def write_multiple_registers(
        self,
        slave_id: int,
        start_address: int,
        values: List[int],
    ) -> None:
        """
        写入多个寄存器 (FC=0x10)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            values: 寄存器值列表
        """
        request = FrameBuilder.build_write_multiple_registers(
            slave_id, start_address, values
        )
        expected_length = calculate_response_length(FunctionCode.WRITE_MULTIPLE_REGISTERS)
        response = self.send_request(request, expected_length)
        response.raise_for_exception()

    def read_register(self, slave_id: int, address: int) -> int:
        """
        读取单个保持寄存器

        Args:
            slave_id: 从站地址
            address: 寄存器地址

        Returns:
            寄存器值
        """
        values = self.read_holding_registers(slave_id, address, 1)
        return values[0]

    def write_register(self, slave_id: int, address: int, value: int) -> None:
        """
        写入单个寄存器

        Args:
            slave_id: 从站地址
            address: 寄存器地址
            value: 寄存器值
        """
        self.write_single_register(slave_id, address, value)

    def read_register_32bit(self, slave_id: int, address: int, signed: bool = False) -> int:
        """
        读取 32 位寄存器 (2 个连续寄存器)

        Args:
            slave_id: 从站地址
            address: 起始寄存器地址
            signed: 是否为有符号整数

        Returns:
            32 位值
        """
        values = self.read_holding_registers(slave_id, address, 2)
        # NiMotion 实际使用大端序: 低地址=高字, 高地址=低字
        value = (values[0] << 16) | values[1]

        if signed and value >= 0x80000000:
            value -= 0x100000000

        return value

    def write_register_32bit(
        self,
        slave_id: int,
        address: int,
        value: int,
        signed: bool = False,
    ) -> None:
        """
        写入 32 位寄存器 (2 个连续寄存器)

        Args:
            slave_id: 从站地址
            address: 起始寄存器地址
            value: 32 位值
            signed: 是否为有符号整数
        """
        if signed and value < 0:
            value += 0x100000000

        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF

        # NiMotion 实际使用大端序: 低地址=高字, 高地址=低字
        self.write_multiple_registers(slave_id, address, [high, low])

    def __enter__(self) -> "ModbusClient":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """上下文管理器出口"""
        self.disconnect()
