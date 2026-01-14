"""
轴配置模块

定义 XYG321-A 三轴平台的轴配置和参数。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from servo_service.motor_control import HomingMethod


class AxisName(Enum):
    """轴名称枚举"""

    Z1 = "Z1"
    Y = "Y"
    Z = "Z"


@dataclass
class AxisConfig:
    """轴配置数据类"""

    name: AxisName
    """轴名称"""

    slave_id: int
    """Modbus 从站地址"""

    model: str
    """电机型号"""

    motor_power: int
    """电机功率 (W)"""

    has_brake: bool
    """是否有抱闸"""

    ball_screw_lead: float
    """丝杠导程 (mm/rev)"""

    max_velocity: float
    """最大速度 (mm/s)"""

    stroke_min: float
    """行程最小值 (mm)"""

    stroke_max: float
    """行程最大值 (mm)"""

    positioning_accuracy: float
    """定位精度 (mm)"""

    repeat_accuracy: float
    """重复定位精度 (mm)"""

    max_payload_horizontal: float
    """最大水平负载 (kg)"""

    max_payload_vertical: float
    """最大垂直负载 (kg)"""

    # 编码器参数 (608Fh)
    encoder_resolution: int = 10000
    """编码器分辨率分子 - 每圈脉冲数 (608Fh:01)"""

    encoder_resolution_denominator: int = 1
    """编码器分辨率分母 - 电机圈数 (608Fh:02)"""

    # 减速比参数 (6091h)
    gear_ratio_numerator: int = 1
    """减速比分子 - 电机轴圈数 (6091h:01)"""

    gear_ratio_denominator: int = 1
    """减速比分母 - 驱动轴圈数 (6091h:02)"""

    # 默认运动参数
    default_velocity: float = 100.0
    """默认速度 (mm/s)"""

    default_acceleration: float = 500.0
    """默认加速度 (mm/s²)"""

    default_deceleration: float = 500.0
    """默认减速度 (mm/s²)"""

    # 回零参数
    homing_velocity_high: float = 50.0
    """回零高速 (mm/s)"""

    homing_velocity_low: float = 10.0
    """回零低速 (mm/s)"""

    homing_acceleration: float = 100.0
    """回零加速度 (mm/s²)"""

    homing_method: Optional[int] = None
    """回零方式 (HomingMethod 枚举值)"""

    homing_timeout: int = 60000
    """回零超时时间 (ms)，默认60秒"""

    velocity_polarity: int = 1
    """速度极性 (1 或 -1，用于修正运动方向)"""

    # DI 配置 (数字输入)
    di1_function: Optional[int] = None
    """DI1 功能编号 (None=不配置)"""

    di1_logic: int = 0
    """DI1 逻辑 (0=低电平有效, 1=高电平有效)"""

    di2_function: Optional[int] = None
    """DI2 功能编号"""

    di2_logic: int = 0
    """DI2 逻辑"""

    di3_function: Optional[int] = None
    """DI3 功能编号"""

    di3_logic: int = 0
    """DI3 逻辑"""

    # 堵转回零参数
    blocking_torque: int = 300
    """堵转回零扭矩阈值 (0.1% 单位，300=30%)"""

    blocking_time: int = 500
    """堵转检测时间 (ms)"""

    # 抱闸配置 (仅当 has_brake=True 时有效)
    brake_do_number: int = 1
    """抱闸使用的 DO 端口号 (默认 DO1)"""

    brake_do_logic: int = 1
    """抱闸 DO 逻辑 (0=低电平释放, 1=高电平释放)"""

    brake_release_delay_ms: int = 500
    """抱闸释放延迟时间 (ms)"""

    brake_auto_control: bool = True
    """是否启用抱闸自动控制 (True=跟随电机使能状态)"""

    @property
    def stroke(self) -> float:
        """有效行程 (mm)"""
        return self.stroke_max - self.stroke_min

    @property
    def mm_per_pulse(self) -> float:
        """每脉冲位移 (mm/pulse)"""
        return self.ball_screw_lead / self.encoder_resolution

    @property
    def pulses_per_mm(self) -> float:
        """每毫米脉冲数 (pulse/mm)"""
        return self.encoder_resolution / self.ball_screw_lead

    def mm_to_pulses(self, mm: float) -> int:
        """
        毫米转脉冲

        Args:
            mm: 毫米值

        Returns:
            脉冲值
        """
        return int(mm * self.pulses_per_mm)

    def pulses_to_mm(self, pulses: int) -> float:
        """
        脉冲转毫米

        Args:
            pulses: 脉冲值

        Returns:
            毫米值
        """
        return pulses * self.mm_per_pulse

    def velocity_mm_to_pulses(self, velocity_mm_s: float) -> int:
        """
        速度: mm/s 转 pulse/s

        Args:
            velocity_mm_s: 速度 (mm/s)

        Returns:
            速度 (pulse/s)
        """
        return int(velocity_mm_s * self.pulses_per_mm)

    def velocity_pulses_to_mm(self, velocity_pulses_s: int) -> float:
        """
        速度: pulse/s 转 mm/s

        Args:
            velocity_pulses_s: 速度 (pulse/s)

        Returns:
            速度 (mm/s)
        """
        return velocity_pulses_s * self.mm_per_pulse

    def is_position_valid(self, position_mm: float) -> bool:
        """
        检查位置是否在有效行程内

        Args:
            position_mm: 位置 (mm)

        Returns:
            是否有效
        """
        return self.stroke_min <= position_mm <= self.stroke_max


# 平台预定义配置
DEFAULT_AXIS_CONFIGS: Dict[AxisName, AxisConfig] = {
    AxisName.Z1: AxisConfig(
        name=AxisName.Z1,
        slave_id=4,
        model="PMMP4010D-485-OHEB-D04",
        motor_power=100,
        has_brake=True,
        brake_do_number=1,
        brake_do_logic=1,  # 高电平释放
        brake_release_delay_ms=500,
        brake_auto_control=True,
        ball_screw_lead=10.0,
        max_velocity=500.0,
        stroke_min=0.0,
        stroke_max=61.0,  # 实测行程
        positioning_accuracy=0.01,
        repeat_accuracy=0.005,
        max_payload_horizontal=20.0,
        max_payload_vertical=10.0,
        encoder_resolution=131072,  # 17-bit absolute encoder (实测 129969, 理论 131072)
        default_velocity=100.0,
        default_acceleration=500.0,
        default_deceleration=500.0,
        homing_velocity_high=20.0,
        homing_velocity_low=4.0,
        homing_acceleration=100.0,
        homing_method=17,  # NEGATIVE_LIMIT_SWITCH: 负限位开关回零
        homing_timeout=60000,
        velocity_polarity=-1,  # 速度方向反转 (点动方向修正)
        # DI 配置
        di2_function=15,  # DI2 = 负限位
        di2_logic=0,  # 低电平有效
        di3_function=14,  # DI3 = 正限位
        di3_logic=0,  # 低电平有效
        # 堵转回零参数
        blocking_torque=300,  # 30%
        blocking_time=500,  # 500ms
    ),
    AxisName.Y: AxisConfig(
        name=AxisName.Y,
        slave_id=2,
        model="CFG5",
        motor_power=100,
        has_brake=False,
        ball_screw_lead=10.0,
        max_velocity=500.0,
        stroke_min=0,
        stroke_max=102,
        positioning_accuracy=0.015,
        repeat_accuracy=0.005,
        max_payload_horizontal=30.0,
        max_payload_vertical=15.0,
        encoder_resolution=10000,
        default_velocity=100.0,
        default_acceleration=500.0,
        default_deceleration=500.0,
        homing_velocity_high=30.0,
        homing_velocity_low=5.0,
        homing_acceleration=100.0,
        homing_method=17,  # NEGATIVE_LIMIT_SWITCH: 负限位回零
        homing_timeout=60000,  # 60秒回零超时
        velocity_polarity=-1,  # 速度方向反转
        # DI 配置 (Z轴限位开关，2026-01-12 验证)
        di2_function=15,  # DI2 = 负限位 (下限位)
        di2_logic=0,  # 低电平有效
        di3_function=14,  # DI3 = 正限位 (上限位)
        di3_logic=0,  # 低电平有效
        # 堵转回零参数
        blocking_torque=300,  # 30%
        blocking_time=500,  # 500ms
    ),
    AxisName.Z: AxisConfig(
        name=AxisName.Z,
        slave_id=3,
        model="CFG4",
        motor_power=100,
        has_brake=True,
        brake_do_number=1,
        brake_do_logic=1,  # 高电平释放
        brake_release_delay_ms=500,
        brake_auto_control=True,
        ball_screw_lead=10.0,
        max_velocity=500.0,
        stroke_min=0.0,
        stroke_max=61.0,
        positioning_accuracy=0.01,
        repeat_accuracy=0.005,
        max_payload_horizontal=20.0,
        max_payload_vertical=10.0,
        encoder_resolution=10000,
        default_velocity=100.0,
        default_acceleration=500.0,
        default_deceleration=500.0,
        homing_velocity_high=30.0,
        homing_velocity_low=5.0,
        homing_acceleration=100.0,
        homing_method=17,  # NEGATIVE_LIMIT_SWITCH: 负限位回零
        homing_timeout=60000,  # 60秒回零超时
        velocity_polarity=-1,  # 速度方向反转
        # DI 配置 (Z轴限位开关，2026-01-12 验证)
        di2_function=15,  # DI2 = 负限位 (下限位)
        di2_logic=0,  # 低电平有效
        di3_function=14,  # DI3 = 正限位 (上限位)
        di3_logic=0,  # 低电平有效
        # 堵转回零参数
        blocking_torque=300,  # 30%
        blocking_time=500,  # 500ms
    ),
}


def get_axis_config(axis: AxisName) -> AxisConfig:
    """
    获取轴配置

    Args:
        axis: 轴名称

    Returns:
        轴配置
    """
    return DEFAULT_AXIS_CONFIGS[axis]


def get_all_axis_configs() -> Dict[AxisName, AxisConfig]:
    """
    获取所有轴配置

    Returns:
        轴配置字典
    """
    return DEFAULT_AXIS_CONFIGS.copy()
