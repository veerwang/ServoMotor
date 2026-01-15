"""
轴配置模块测试
"""

import pytest

from servo_service.high_level_api.axis_config import (
    AxisConfig,
    AxisName,
    DEFAULT_AXIS_CONFIGS,
    get_all_axis_configs,
    get_axis_config,
)


class TestAxisName:
    """测试轴名称枚举"""

    def test_values(self) -> None:
        """测试枚举值"""
        assert AxisName.X.value == "X"
        assert AxisName.Y2.value == "Y2"
        assert AxisName.Z3.value == "Z3"

    def test_iteration(self) -> None:
        """测试迭代"""
        axes = list(AxisName)
        assert len(axes) == 3


class TestAxisConfig:
    """测试轴配置"""

    def test_stroke(self) -> None:
        """测试行程计算"""
        config = AxisConfig(
            name=AxisName.X,
            slave_id=1,
            model="TEST",
            motor_power=100,
            has_brake=False,
            ball_screw_lead=10.0,
            max_velocity=100.0,
            stroke_min=10.0,
            stroke_max=110.0,
            positioning_accuracy=0.01,
            repeat_accuracy=0.005,
            max_payload_horizontal=10.0,
            max_payload_vertical=5.0,
        )

        assert config.stroke == 100.0

    def test_unit_conversion(self) -> None:
        """测试单位转换"""
        config = AxisConfig(
            name=AxisName.X,
            slave_id=1,
            model="TEST",
            motor_power=100,
            has_brake=False,
            ball_screw_lead=10.0,  # 10mm/rev
            max_velocity=100.0,
            stroke_min=0.0,
            stroke_max=100.0,
            positioning_accuracy=0.01,
            repeat_accuracy=0.005,
            max_payload_horizontal=10.0,
            max_payload_vertical=5.0,
            encoder_resolution=10000,  # 10000 pulses/rev
        )

        # 每脉冲位移 = 10mm / 10000 = 0.001mm
        assert config.mm_per_pulse == 0.001

        # 每毫米脉冲 = 10000 / 10 = 1000
        assert config.pulses_per_mm == 1000.0

        # 25mm = 25000 pulses
        assert config.mm_to_pulses(25.0) == 25000

        # 10000 pulses = 10mm
        assert config.pulses_to_mm(10000) == 10.0

    def test_velocity_conversion(self) -> None:
        """测试速度单位转换"""
        config = AxisConfig(
            name=AxisName.X,
            slave_id=1,
            model="TEST",
            motor_power=100,
            has_brake=False,
            ball_screw_lead=10.0,
            max_velocity=100.0,
            stroke_min=0.0,
            stroke_max=100.0,
            positioning_accuracy=0.01,
            repeat_accuracy=0.005,
            max_payload_horizontal=10.0,
            max_payload_vertical=5.0,
            encoder_resolution=10000,
        )

        # 100mm/s = 100000 pulses/s
        assert config.velocity_mm_to_pulses(100.0) == 100000

        # 50000 pulses/s = 50mm/s
        assert config.velocity_pulses_to_mm(50000) == 50.0

    def test_position_validation(self) -> None:
        """测试位置验证"""
        config = AxisConfig(
            name=AxisName.X,
            slave_id=1,
            model="TEST",
            motor_power=100,
            has_brake=False,
            ball_screw_lead=10.0,
            max_velocity=100.0,
            stroke_min=10.0,
            stroke_max=100.0,
            positioning_accuracy=0.01,
            repeat_accuracy=0.005,
            max_payload_horizontal=10.0,
            max_payload_vertical=5.0,
        )

        assert config.is_position_valid(10.0) is True
        assert config.is_position_valid(50.0) is True
        assert config.is_position_valid(100.0) is True
        assert config.is_position_valid(5.0) is False
        assert config.is_position_valid(105.0) is False


class TestDefaultConfigs:
    """测试默认配置"""

    def test_all_axes_configured(self) -> None:
        """测试所有轴都有配置"""
        for axis in AxisName:
            assert axis in DEFAULT_AXIS_CONFIGS

    def test_get_axis_config(self) -> None:
        """测试获取轴配置"""
        config = get_axis_config(AxisName.Z3)

        assert config.name == AxisName.Z3
        assert config.slave_id == 3
        assert config.has_brake is True

    def test_get_all_axis_configs(self) -> None:
        """测试获取所有配置"""
        configs = get_all_axis_configs()

        assert len(configs) == 3
        assert AxisName.X in configs
        assert AxisName.Y2 in configs
        assert AxisName.Z3 in configs

    def test_x_axis_config(self) -> None:
        """测试 X 轴配置"""
        config = get_axis_config(AxisName.X)

        assert config.slave_id == 1
        assert config.model == "CFG8"
        assert config.motor_power == 200
        assert config.max_velocity == 1000.0

    def test_y_axis_config(self) -> None:
        """测试 Y 轴配置"""
        config = get_axis_config(AxisName.Y2)

        assert config.slave_id == 2
        assert config.model == "CFG5"
        assert config.motor_power == 100

    def test_z_axis_config(self) -> None:
        """测试 Z 轴配置"""
        config = get_axis_config(AxisName.Z3)

        assert config.slave_id == 3
        assert config.model == "CFG4"
        assert config.has_brake is True
