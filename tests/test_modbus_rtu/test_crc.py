"""
CRC-16 模块测试
"""

import pytest

from servo_service.modbus_rtu.crc import (
    append_crc,
    calculate_crc,
    calculate_crc_bytes,
    extract_crc,
    verify_crc,
)


class TestCalculateCRC:
    """测试 CRC 计算"""

    def test_known_values(self) -> None:
        """测试已知值"""
        # Modbus RTU 标准测试向量
        # 从站地址=0x01, 功能码=0x03, 地址=0x0000, 数量=0x0001
        data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])
        crc = calculate_crc(data)
        assert crc == 0x0A84

    def test_empty_data(self) -> None:
        """测试空数据"""
        crc = calculate_crc(b"")
        assert crc == 0xFFFF  # 初始值

    def test_single_byte(self) -> None:
        """测试单字节"""
        crc = calculate_crc(bytes([0x00]))
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF


class TestCalculateCRCBytes:
    """测试 CRC 字节计算"""

    def test_output_format(self) -> None:
        """测试输出格式 (低字节在前)"""
        data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])
        crc_bytes = calculate_crc_bytes(data)

        assert len(crc_bytes) == 2
        # CRC = 0x0A84, 低字节=0x84, 高字节=0x0A
        assert crc_bytes[0] == 0x84
        assert crc_bytes[1] == 0x0A


class TestVerifyCRC:
    """测试 CRC 验证"""

    def test_valid_frame(self) -> None:
        """测试有效帧"""
        # 带有效 CRC 的帧
        data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])
        frame = append_crc(data)

        assert verify_crc(frame) is True

    def test_invalid_frame(self) -> None:
        """测试无效帧"""
        # 带错误 CRC 的帧
        frame = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0xFF, 0xFF])

        assert verify_crc(frame) is False

    def test_too_short(self) -> None:
        """测试过短帧"""
        frame = bytes([0x01, 0x03])
        assert verify_crc(frame) is False


class TestAppendCRC:
    """测试追加 CRC"""

    def test_append_crc(self) -> None:
        """测试追加 CRC"""
        data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])
        frame = append_crc(data)

        assert len(frame) == len(data) + 2
        assert frame[:-2] == data
        assert verify_crc(frame) is True

    def test_roundtrip(self) -> None:
        """测试往返"""
        original = bytes([0x01, 0x06, 0x03, 0x80, 0x00, 0x0F])
        frame = append_crc(original)

        assert verify_crc(frame) is True
        payload, crc = extract_crc(frame)
        assert payload == original


class TestExtractCRC:
    """测试提取 CRC"""

    def test_extract(self) -> None:
        """测试提取"""
        data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])
        frame = append_crc(data)

        payload, crc = extract_crc(frame)

        assert payload == data
        assert crc == calculate_crc(data)

    def test_too_short(self) -> None:
        """测试过短数据"""
        with pytest.raises(ValueError):
            extract_crc(bytes([0x01, 0x02]))
