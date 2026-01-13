"""
Modbus RTU 帧构建与解析模块

提供 Modbus RTU 帧的构建、解析和验证功能。
"""

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple, Union

from .crc import append_crc, calculate_crc, verify_crc
from .exceptions import CRCError, FrameError, ModbusExceptionResponse


class FunctionCode(IntEnum):
    """Modbus 功能码"""

    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10

    @property
    def is_read(self) -> bool:
        """是否为读取功能码"""
        return self in (
            FunctionCode.READ_COILS,
            FunctionCode.READ_DISCRETE_INPUTS,
            FunctionCode.READ_HOLDING_REGISTERS,
            FunctionCode.READ_INPUT_REGISTERS,
        )

    @property
    def is_write(self) -> bool:
        """是否为写入功能码"""
        return self in (
            FunctionCode.WRITE_SINGLE_COIL,
            FunctionCode.WRITE_SINGLE_REGISTER,
            FunctionCode.WRITE_MULTIPLE_COILS,
            FunctionCode.WRITE_MULTIPLE_REGISTERS,
        )


@dataclass
class ModbusRequest:
    """Modbus 请求帧"""

    slave_id: int
    """从站地址 (1-247, 0 为广播)"""

    function_code: int
    """功能码"""

    data: bytes
    """数据部分"""

    def to_bytes(self) -> bytes:
        """
        构建完整的请求帧 (包含 CRC)

        Returns:
            完整的帧字节
        """
        frame = bytes([self.slave_id, self.function_code]) + self.data
        return append_crc(frame)

    @property
    def is_broadcast(self) -> bool:
        """是否为广播请求"""
        return self.slave_id == 0

    def __repr__(self) -> str:
        return (
            f"ModbusRequest(slave_id={self.slave_id}, "
            f"fc=0x{self.function_code:02X}, data={self.data.hex()})"
        )


@dataclass
class ModbusResponse:
    """Modbus 响应帧"""

    slave_id: int
    """从站地址"""

    function_code: int
    """功能码"""

    data: bytes
    """数据部分"""

    is_exception: bool = False
    """是否为异常响应"""

    exception_code: int = 0
    """异常码 (仅当 is_exception=True 时有效)"""

    @classmethod
    def from_bytes(cls, raw_data: bytes, validate_crc: bool = True) -> "ModbusResponse":
        """
        从字节数据解析响应帧

        Args:
            raw_data: 原始响应数据 (包含 CRC)
            validate_crc: 是否验证 CRC

        Returns:
            ModbusResponse 实例

        Raises:
            FrameError: 帧格式错误
            CRCError: CRC 校验失败
        """
        if len(raw_data) < 5:  # 最小帧: slave_id + fc + 1 byte data + 2 bytes CRC
            raise FrameError(
                f"响应帧长度不足: 需要至少 5 字节, 实际 {len(raw_data)} 字节",
                raw_data=raw_data,
            )

        if validate_crc:
            if not verify_crc(raw_data):
                # 计算期望的 CRC
                expected_crc = calculate_crc(raw_data[:-2])
                received_crc = raw_data[-2] | (raw_data[-1] << 8)
                raise CRCError(expected_crc, received_crc)

        slave_id = raw_data[0]
        function_code = raw_data[1]
        data = raw_data[2:-2]  # 去掉从站地址、功能码和 CRC

        # 检查是否为异常响应
        is_exception = (function_code & 0x80) != 0
        exception_code = 0

        if is_exception:
            if len(data) >= 1:
                exception_code = data[0]

        return cls(
            slave_id=slave_id,
            function_code=function_code,
            data=data,
            is_exception=is_exception,
            exception_code=exception_code,
        )

    def raise_for_exception(self) -> None:
        """
        如果是异常响应则抛出异常

        Raises:
            ModbusExceptionResponse: 当响应为异常响应时
        """
        if self.is_exception:
            raise ModbusExceptionResponse(
                function_code=self.function_code,
                exception_code=self.exception_code,
                slave_id=self.slave_id,
            )

    def get_registers(self) -> List[int]:
        """
        获取响应中的寄存器值

        用于读取寄存器响应 (FC=0x03, 0x04)。

        Returns:
            寄存器值列表 (16 位无符号整数)

        Raises:
            FrameError: 数据格式错误
        """
        if len(self.data) < 1:
            raise FrameError("响应数据为空", raw_data=self.data)

        byte_count = self.data[0]
        register_data = self.data[1:]

        if len(register_data) != byte_count:
            raise FrameError(
                f"数据长度不匹配: 声明 {byte_count} 字节, 实际 {len(register_data)} 字节",
                raw_data=self.data,
            )

        if byte_count % 2 != 0:
            raise FrameError(
                f"寄存器数据长度必须为偶数: {byte_count}",
                raw_data=self.data,
            )

        registers = []
        for i in range(0, byte_count, 2):
            value = (register_data[i] << 8) | register_data[i + 1]
            registers.append(value)

        return registers

    def __repr__(self) -> str:
        if self.is_exception:
            return (
                f"ModbusResponse(slave_id={self.slave_id}, "
                f"fc=0x{self.function_code:02X}, exception_code=0x{self.exception_code:02X})"
            )
        return (
            f"ModbusResponse(slave_id={self.slave_id}, "
            f"fc=0x{self.function_code:02X}, data={self.data.hex()})"
        )


class FrameBuilder:
    """Modbus 帧构建器"""

    @staticmethod
    def build_read_holding_registers(
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> ModbusRequest:
        """
        构建读取保持寄存器请求 (FC=0x03)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            quantity: 读取数量 (1-125)

        Returns:
            ModbusRequest
        """
        if not 1 <= quantity <= 125:
            raise ValueError(f"读取数量必须在 1-125 之间: {quantity}")

        data = struct.pack(">HH", start_address, quantity)
        return ModbusRequest(
            slave_id=slave_id,
            function_code=FunctionCode.READ_HOLDING_REGISTERS,
            data=data,
        )

    @staticmethod
    def build_read_input_registers(
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> ModbusRequest:
        """
        构建读取输入寄存器请求 (FC=0x04)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            quantity: 读取数量 (1-125)

        Returns:
            ModbusRequest
        """
        if not 1 <= quantity <= 125:
            raise ValueError(f"读取数量必须在 1-125 之间: {quantity}")

        data = struct.pack(">HH", start_address, quantity)
        return ModbusRequest(
            slave_id=slave_id,
            function_code=FunctionCode.READ_INPUT_REGISTERS,
            data=data,
        )

    @staticmethod
    def build_write_single_register(
        slave_id: int,
        address: int,
        value: int,
    ) -> ModbusRequest:
        """
        构建写入单个寄存器请求 (FC=0x06)

        Args:
            slave_id: 从站地址
            address: 寄存器地址
            value: 寄存器值 (0-65535)

        Returns:
            ModbusRequest
        """
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"寄存器值必须在 0-65535 之间: {value}")

        data = struct.pack(">HH", address, value)
        return ModbusRequest(
            slave_id=slave_id,
            function_code=FunctionCode.WRITE_SINGLE_REGISTER,
            data=data,
        )

    @staticmethod
    def build_write_multiple_registers(
        slave_id: int,
        start_address: int,
        values: List[int],
    ) -> ModbusRequest:
        """
        构建写入多个寄存器请求 (FC=0x10)

        Args:
            slave_id: 从站地址
            start_address: 起始地址
            values: 寄存器值列表 (每个值 0-65535)

        Returns:
            ModbusRequest
        """
        quantity = len(values)
        if not 1 <= quantity <= 123:
            raise ValueError(f"写入数量必须在 1-123 之间: {quantity}")

        byte_count = quantity * 2

        # 构建数据: 起始地址(2) + 数量(2) + 字节数(1) + 值(2*N)
        data = struct.pack(">HHB", start_address, quantity, byte_count)
        for value in values:
            if not 0 <= value <= 0xFFFF:
                raise ValueError(f"寄存器值必须在 0-65535 之间: {value}")
            data += struct.pack(">H", value)

        return ModbusRequest(
            slave_id=slave_id,
            function_code=FunctionCode.WRITE_MULTIPLE_REGISTERS,
            data=data,
        )


def calculate_response_length(function_code: int, quantity: int = 0) -> int:
    """
    计算预期响应长度

    Args:
        function_code: 功能码
        quantity: 请求数量 (用于读取请求)

    Returns:
        预期响应字节数 (包含 CRC)
    """
    # 基础长度: slave_id(1) + fc(1) + CRC(2) = 4
    base_length = 4

    if function_code == FunctionCode.READ_HOLDING_REGISTERS:
        # 响应: slave_id(1) + fc(1) + byte_count(1) + data(2*quantity) + CRC(2)
        return base_length + 1 + quantity * 2

    elif function_code == FunctionCode.READ_INPUT_REGISTERS:
        return base_length + 1 + quantity * 2

    elif function_code == FunctionCode.WRITE_SINGLE_REGISTER:
        # 响应: slave_id(1) + fc(1) + address(2) + value(2) + CRC(2)
        return base_length + 4

    elif function_code == FunctionCode.WRITE_MULTIPLE_REGISTERS:
        # 响应: slave_id(1) + fc(1) + address(2) + quantity(2) + CRC(2)
        return base_length + 4

    else:
        # 默认最小响应长度
        return 5


def parse_write_response(response: ModbusResponse) -> Tuple[int, int]:
    """
    解析写入响应

    Args:
        response: ModbusResponse 实例

    Returns:
        (地址, 值或数量)

    Raises:
        FrameError: 数据格式错误
    """
    if len(response.data) < 4:
        raise FrameError(
            f"写入响应数据长度不足: 需要 4 字节, 实际 {len(response.data)} 字节",
            raw_data=response.data,
        )

    address = (response.data[0] << 8) | response.data[1]
    value = (response.data[2] << 8) | response.data[3]

    return address, value
