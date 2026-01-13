"""
NiMotion 伺服电机寄存器定义

基于 CiA402 标准和 NiMotion 伺服电机手册定义寄存器地址。
寄存器地址采用 Modbus 映射格式。
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional


class RegisterAccess(IntEnum):
    """寄存器访问类型"""

    READ_ONLY = 0
    READ_WRITE = 1
    WRITE_ONLY = 2


@dataclass
class RegisterDef:
    """寄存器定义"""

    address: int
    """Modbus 地址"""

    name: str
    """寄存器名称"""

    description: str
    """描述"""

    size: int = 1
    """寄存器数量 (1=16位, 2=32位)"""

    access: RegisterAccess = RegisterAccess.READ_WRITE
    """访问类型"""

    signed: bool = False
    """是否有符号"""

    object_index: Optional[int] = None
    """对象索引 (CiA402)"""

    object_subindex: Optional[int] = None
    """对象子索引"""


class Registers:
    """
    NiMotion 伺服电机寄存器地址定义

    地址映射规则:
    - 对象索引 xxxx:yy 映射到 Modbus 地址
    - 通常: Modbus地址 = (对象索引 - 0x6000) * 0x10 + 子索引
    """

    # ==================== CiA402 控制寄存器 ====================

    # 控制字 (6040h)
    CONTROL_WORD = RegisterDef(
        address=0x0380,
        name="ControlWord",
        description="控制字",
        object_index=0x6040,
        object_subindex=0x00,
    )

    # 状态字 (6041h)
    STATUS_WORD = RegisterDef(
        address=0x0381,
        name="StatusWord",
        description="状态字",
        access=RegisterAccess.READ_ONLY,
        object_index=0x6041,
        object_subindex=0x00,
    )

    # 操作模式设置 (6060h)
    # 注意: 根据 NiMotion 手册，6060h 映射到 Modbus 地址 0x03C2
    MODES_OF_OPERATION = RegisterDef(
        address=0x03C2,
        name="ModesOfOperation",
        description="操作模式设置",
        object_index=0x6060,
        object_subindex=0x00,
    )

    # 操作模式显示 (6061h)
    # 注意: 根据 NiMotion 手册，6061h 映射到 Modbus 地址 0x03C3
    MODES_OF_OPERATION_DISPLAY = RegisterDef(
        address=0x03C3,
        name="ModesOfOperationDisplay",
        description="操作模式显示",
        access=RegisterAccess.READ_ONLY,
        object_index=0x6061,
        object_subindex=0x00,
    )

    # ==================== 位置控制寄存器 ====================

    # 目标位置 (607Ah) - 32位
    # 根据 NiMotion 手册: 607Ah → Modbus 0x03E7
    TARGET_POSITION = RegisterDef(
        address=0x03E7,
        name="TargetPosition",
        description="目标位置",
        size=2,
        signed=True,
        object_index=0x607A,
        object_subindex=0x00,
    )

    # 实际位置 (6064h) - 32位
    # 根据 NiMotion 手册: 6064h → Modbus 0x03C8
    POSITION_ACTUAL_VALUE = RegisterDef(
        address=0x03C8,
        name="PositionActualValue",
        description="实际位置",
        size=2,
        access=RegisterAccess.READ_ONLY,
        signed=True,
        object_index=0x6064,
        object_subindex=0x00,
    )

    # 位置跟随误差 (60F4h) - 32位
    # 根据 NiMotion 手册: 60F4h → Modbus 0x0440
    FOLLOWING_ERROR_ACTUAL = RegisterDef(
        address=0x0440,
        name="FollowingErrorActual",
        description="位置跟随误差",
        size=2,
        access=RegisterAccess.READ_ONLY,
        signed=True,
        object_index=0x60F4,
        object_subindex=0x00,
    )

    # ==================== 速度控制寄存器 ====================

    # 目标速度 (60FFh) - 32位
    # 根据 NiMotion 手册: 60FFh → Modbus 0x0448
    TARGET_VELOCITY = RegisterDef(
        address=0x0448,
        name="TargetVelocity",
        description="目标速度",
        size=2,
        signed=True,
        object_index=0x60FF,
        object_subindex=0x00,
    )

    # 实际速度 (606Ch) - 32位
    # 根据 NiMotion 手册: 606Ch → Modbus 0x03D5
    VELOCITY_ACTUAL_VALUE = RegisterDef(
        address=0x03D5,
        name="VelocityActualValue",
        description="实际速度",
        size=2,
        access=RegisterAccess.READ_ONLY,
        signed=True,
        object_index=0x606C,
        object_subindex=0x00,
    )

    # 轮廓速度 (6081h) - 32位
    # 根据 NiMotion 手册: 6081h → Modbus 0x03F8
    PROFILE_VELOCITY = RegisterDef(
        address=0x03F8,
        name="ProfileVelocity",
        description="轮廓速度",
        size=2,
        object_index=0x6081,
        object_subindex=0x00,
    )

    # ==================== 加减速寄存器 ====================

    # 轮廓加速度 (6083h) - 32位
    # 根据 NiMotion 手册: 6083h → Modbus 0x03FC
    PROFILE_ACCELERATION = RegisterDef(
        address=0x03FC,
        name="ProfileAcceleration",
        description="轮廓加速度",
        size=2,
        object_index=0x6083,
        object_subindex=0x00,
    )

    # 轮廓减速度 (6084h) - 32位
    # 根据 NiMotion 手册: 6084h → Modbus 0x03FE
    PROFILE_DECELERATION = RegisterDef(
        address=0x03FE,
        name="ProfileDeceleration",
        description="轮廓减速度",
        size=2,
        object_index=0x6084,
        object_subindex=0x00,
    )

    # 快速停止减速度 (6085h) - 32位
    # 根据 NiMotion 手册: 6085h → Modbus 0x0400
    QUICK_STOP_DECELERATION = RegisterDef(
        address=0x0400,
        name="QuickStopDeceleration",
        description="快速停止减速度",
        size=2,
        object_index=0x6085,
        object_subindex=0x00,
    )

    # ==================== 转矩控制寄存器 ====================

    # 目标转矩 (6071h)
    # 根据 NiMotion 手册: 6071h → Modbus 0x03DB
    TARGET_TORQUE = RegisterDef(
        address=0x03DB,
        name="TargetTorque",
        description="目标转矩",
        signed=True,
        object_index=0x6071,
        object_subindex=0x00,
    )

    # 实际转矩 (6077h)
    # 根据 NiMotion 手册: 6077h → Modbus 0x03E3
    TORQUE_ACTUAL_VALUE = RegisterDef(
        address=0x03E3,
        name="TorqueActualValue",
        description="实际转矩",
        access=RegisterAccess.READ_ONLY,
        signed=True,
        object_index=0x6077,
        object_subindex=0x00,
    )

    # ==================== 回零控制寄存器 ====================

    # 回零方式 (6098h)
    # 根据 NiMotion 手册: 6098h → Modbus 0x0416
    HOMING_METHOD = RegisterDef(
        address=0x0416,
        name="HomingMethod",
        description="回零方式",
        signed=True,
        object_index=0x6098,
        object_subindex=0x00,
    )

    # 回零高速 (6099h:01) - 32位
    # 根据 NiMotion 手册: 6099h:01 → Modbus 0x0417
    HOMING_SPEED_HIGH = RegisterDef(
        address=0x0417,
        name="HomingSpeedHigh",
        description="回零高速 (搜索开关)",
        size=2,
        object_index=0x6099,
        object_subindex=0x01,
    )

    # 回零低速 (6099h:02) - 32位
    # 根据 NiMotion 手册: 6099h:02 → Modbus 0x0419
    HOMING_SPEED_LOW = RegisterDef(
        address=0x0419,
        name="HomingSpeedLow",
        description="回零低速 (搜索零点)",
        size=2,
        object_index=0x6099,
        object_subindex=0x02,
    )

    # 回零加速度 (609Ah) - 32位
    # 根据 NiMotion 手册: 609Ah → Modbus 0x041B
    HOMING_ACCELERATION = RegisterDef(
        address=0x041B,
        name="HomingAcceleration",
        description="回零加速度",
        size=2,
        object_index=0x609A,
        object_subindex=0x00,
    )

    # ==================== 数字输入输出 ====================

    # 数字输入 (60FDh)
    # 根据 NiMotion 手册: 60FDh → Modbus 0x0447
    DIGITAL_INPUTS = RegisterDef(
        address=0x0447,
        name="DigitalInputs",
        description="数字输入状态",
        size=2,
        access=RegisterAccess.READ_ONLY,
        object_index=0x60FD,
        object_subindex=0x00,
    )

    # 数字输出 (60FEh)
    # 根据 NiMotion 手册: 60FEh → Modbus 0x0449
    DIGITAL_OUTPUTS = RegisterDef(
        address=0x0449,
        name="DigitalOutputs",
        description="数字输出状态",
        size=2,
        object_index=0x60FE,
        object_subindex=0x00,
    )

    # ==================== 错误码 ====================

    # 错误码 (603Fh)
    ERROR_CODE = RegisterDef(
        address=0x0382,
        name="ErrorCode",
        description="错误码",
        access=RegisterAccess.READ_ONLY,
        object_index=0x603F,
        object_subindex=0x00,
    )

    # ==================== 通信配置 ====================

    # 从站地址 (200Ch:02)
    SLAVE_ADDRESS = RegisterDef(
        address=0x0230,
        name="SlaveAddress",
        description="Modbus 从站地址",
        object_index=0x200C,
        object_subindex=0x02,
    )

    # 波特率 (200Ch:03)
    BAUDRATE = RegisterDef(
        address=0x0231,
        name="Baudrate",
        description="通信波特率",
        object_index=0x200C,
        object_subindex=0x03,
    )

    # ==================== 编码器配置 ====================

    # 编码器分辨率 - 增量 (608Fh:01) - 32位
    # 根据 NiMotion 手册: 608Fh:01 → Modbus 0x0408
    ENCODER_RESOLUTION_NUM = RegisterDef(
        address=0x0408,
        name="EncoderResolutionNum",
        description="编码器分辨率-分子 (encoder_increment)",
        size=2,
        object_index=0x608F,
        object_subindex=0x01,
    )

    # 编码器分辨率 - 电机圈数 (608Fh:02) - 32位
    # 根据 NiMotion 手册: 608Fh:02 → Modbus 0x040A
    ENCODER_RESOLUTION_DEN = RegisterDef(
        address=0x040A,
        name="EncoderResolutionDen",
        description="编码器分辨率-分母 (motor_turns)",
        size=2,
        object_index=0x608F,
        object_subindex=0x02,
    )

    # 减速比 - 电机圈数 (6091h:01) - 32位
    # 根据 NiMotion 手册: 6091h:01 → Modbus 0x040C
    GEAR_RATIO_NUM = RegisterDef(
        address=0x040C,
        name="GearRatioNum",
        description="减速比-分子 (motor_revolutions)",
        size=2,
        object_index=0x6091,
        object_subindex=0x01,
    )

    # 减速比 - 轴圈数 (6091h:02) - 32位
    # 根据 NiMotion 手册: 6091h:02 → Modbus 0x040E
    GEAR_RATIO_DEN = RegisterDef(
        address=0x040E,
        name="GearRatioDen",
        description="减速比-分母 (shaft_revolutions)",
        size=2,
        object_index=0x6091,
        object_subindex=0x02,
    )


class ControlWordBits:
    """控制字位定义"""

    SWITCH_ON = 0x0001  # Bit 0: 切换开
    ENABLE_VOLTAGE = 0x0002  # Bit 1: 使能电压
    QUICK_STOP = 0x0004  # Bit 2: 快速停止 (0=激活)
    ENABLE_OPERATION = 0x0008  # Bit 3: 使能操作
    NEW_SET_POINT = 0x0010  # Bit 4: 新设定点/PP模式启动
    CHANGE_SET_IMMEDIATELY = 0x0020  # Bit 5: 立即更改设定点
    ABS_REL = 0x0040  # Bit 6: 绝对/相对位置
    FAULT_RESET = 0x0080  # Bit 7: 故障复位
    HALT = 0x0100  # Bit 8: 暂停

    # 控制字命令组合
    CMD_SHUTDOWN = 0x0006  # 关机
    CMD_SWITCH_ON = 0x0007  # 开机
    CMD_ENABLE_OPERATION = 0x000F  # 使能操作
    CMD_DISABLE_OPERATION = 0x0007  # 禁用操作
    CMD_DISABLE_VOLTAGE = 0x0000  # 禁用电压
    CMD_QUICK_STOP = 0x0002  # 快速停止


class StatusWordBits:
    """状态字位定义"""

    READY_TO_SWITCH_ON = 0x0001  # Bit 0: 准备开机
    SWITCHED_ON = 0x0002  # Bit 1: 已开机
    OPERATION_ENABLED = 0x0004  # Bit 2: 操作已使能
    FAULT = 0x0008  # Bit 3: 故障
    VOLTAGE_ENABLED = 0x0010  # Bit 4: 电压使能
    QUICK_STOP = 0x0020  # Bit 5: 快速停止激活
    SWITCH_ON_DISABLED = 0x0040  # Bit 6: 开机禁用
    WARNING = 0x0080  # Bit 7: 警告
    REMOTE = 0x0200  # Bit 9: 远程控制
    TARGET_REACHED = 0x0400  # Bit 10: 目标到达
    INTERNAL_LIMIT_ACTIVE = 0x0800  # Bit 11: 内部限位激活
    SET_POINT_ACK = 0x1000  # Bit 12: 设定点确认 (PP模式)
    FOLLOWING_ERROR = 0x2000  # Bit 13: 跟随误差

    # 状态机状态掩码
    STATE_MASK = 0x006F  # Bits 0-3, 5, 6

    # 状态机状态值
    STATE_NOT_READY_TO_SWITCH_ON = 0x0000
    STATE_SWITCH_ON_DISABLED = 0x0040
    STATE_READY_TO_SWITCH_ON = 0x0021
    STATE_SWITCHED_ON = 0x0023
    STATE_OPERATION_ENABLED = 0x0027
    STATE_QUICK_STOP_ACTIVE = 0x0007
    STATE_FAULT_REACTION_ACTIVE = 0x000F
    STATE_FAULT = 0x0008


class OperationMode(IntEnum):
    """操作模式定义 (6060h)"""

    PROFILE_POSITION = 1  # PP: 轮廓位置模式
    VELOCITY = 2  # VL: 速度模式
    PROFILE_VELOCITY = 3  # PV: 轮廓速度模式
    PROFILE_TORQUE = 4  # PT: 轮廓转矩模式
    HOMING = 6  # HM: 回零模式
    INTERPOLATED_POSITION = 7  # IP: 插补位置模式
    CYCLIC_SYNC_POSITION = 8  # CSP: 周期同步位置模式
    CYCLIC_SYNC_VELOCITY = 9  # CSV: 周期同步速度模式
    CYCLIC_SYNC_TORQUE = 10  # CST: 周期同步转矩模式


class HomingMethod(IntEnum):
    """回零方式定义 (6098h)"""

    # 正向方式
    POSITIVE_LIMIT_SWITCH = 1  # 使用正限位开关
    POSITIVE_LIMIT_SWITCH_AND_INDEX = 2  # 使用正限位开关和编码器索引
    HOME_SWITCH_POSITIVE = 7  # 使用原点开关 (正向接近)
    HOME_SWITCH_POSITIVE_AND_INDEX = 11  # 使用原点开关和编码器索引 (正向)

    # 负向方式
    NEGATIVE_LIMIT_SWITCH = 17  # 使用负限位开关
    NEGATIVE_LIMIT_SWITCH_AND_INDEX = 18  # 使用负限位开关和编码器索引
    HOME_SWITCH_NEGATIVE = 23  # 使用原点开关 (负向接近)
    HOME_SWITCH_NEGATIVE_AND_INDEX = 27  # 使用原点开关和编码器索引 (负向)

    # 电流方式
    CURRENT_POSITIVE = 33  # 正向堵转回零
    CURRENT_NEGATIVE = 34  # 负向堵转回零

    # 立即设置
    CURRENT_POSITION_AS_HOME = 35  # 将当前位置设为原点

    # 无回零
    NO_HOMING = 0


class ErrorCode(IntEnum):
    """错误码定义"""

    NO_ERROR = 0x0000
    OVER_CURRENT = 0x2310  # 过流
    OVER_VOLTAGE = 0x3210  # 过压
    UNDER_VOLTAGE = 0x3220  # 欠压
    OVER_TEMPERATURE = 0x4310  # 过温
    ENCODER_ERROR = 0x7300  # 编码器错误
    COMMUNICATION_ERROR = 0x8100  # 通信错误
    POSITION_LIMIT = 0x8611  # 位置超限
    FOLLOWING_ERROR = 0x8611  # 跟随误差过大
    MOTOR_BLOCKED = 0xFF01  # 电机堵转
    HALL_ERROR = 0xFF02  # 霍尔错误


# 寄存器地址索引
REGISTER_MAP: Dict[int, RegisterDef] = {
    reg.address: reg
    for name, reg in Registers.__dict__.items()
    if isinstance(reg, RegisterDef)
}
