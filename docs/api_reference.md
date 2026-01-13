# API 接口文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | NiMotion 伺服电机控制系统 |
| 文档版本 | 1.0 |
| 创建日期 | 2026-01-09 |

---

## 目录

1. [概述](#1-概述)
2. [ServoService 服务类](#2-servoservice-服务类)
3. [Motor 电机控制类](#3-motor-电机控制类)
4. [轴配置](#4-轴配置)
5. [数据类型](#5-数据类型)
6. [异常类型](#6-异常类型)
7. [Modbus 底层接口](#7-modbus-底层接口)
8. [使用示例](#8-使用示例)

---

## 1. 概述

### 1.1 模块结构

```
servo_service/
├── __init__.py              # 导出主要类
├── service.py               # ServoService 类
├── serial_comm/             # 串口通信 (Layer 1)
├── modbus_rtu/              # Modbus 协议 (Layer 2)
├── motor_control/           # 电机控制 (Layer 3)
└── high_level_api/          # 高级 API (Layer 4)
    ├── motor.py             # Motor 类
    ├── axis_config.py       # 轴配置
    └── types.py             # 数据类型
```

### 1.2 快速开始

```python
from servo_service import ServoService, Axis

# 创建服务并连接
service = ServoService()
service.connect('/dev/ttyUSB0', baudrate=115200)

# 获取 Z 轴电机（默认）
motor = service.get_motor_by_axis(Axis.Z)

# 使能电机
motor.enable()

# 位置运动
motor.set_position_mode()
motor.move_absolute(position=50.0, velocity=100.0)
motor.wait_for_position_reached(timeout=10.0)

# 断开连接
motor.disable()
service.disconnect()
```

### 1.3 导入

```python
# 主要类
from servo_service import ServoService, Motor

# 枚举类型
from servo_service import Axis, OperationMode, HomingMethod

# 数据类型
from servo_service import MotorStatus, AxisConfig, FaultInfo

# 异常类型
from servo_service import (
    ServoMotorError,
    CommunicationError,
    ModbusTimeoutError,
    MotorFaultError
)

# 轴配置
from servo_service import AXIS_CONFIGS
```

---

## 2. ServoService 服务类

### 2.1 类定义

```python
class ServoService:
    """
    伺服电机服务类

    提供统一的服务接口，封装底层通信和控制功能。
    支持多轴控制（X/Y/Z），默认控制 Z 轴。

    Attributes:
        is_connected (bool): 连接状态

    Example:
        >>> service = ServoService()
        >>> service.connect('/dev/ttyUSB0')
        >>> motor = service.get_motor_by_axis(Axis.Z)
        >>> motor.enable()
        >>> service.disconnect()
    """
```

### 2.2 连接管理

#### connect

```python
def connect(
    self,
    port: str,
    baudrate: int = 115200,
    timeout: float = 0.1
) -> bool:
    """
    连接到串口设备

    Args:
        port: 串口名称
            - Linux: '/dev/ttyUSB0', '/dev/ttyACM0'
            - Windows: 'COM3', 'COM4'
            - macOS: '/dev/tty.usbserial-xxx'
        baudrate: 波特率，默认 115200
            支持: 9600, 19200, 38400, 57600, 115200, 256000, 500000, 1000000
        timeout: 通信超时时间（秒），默认 0.1

    Returns:
        连接成功返回 True

    Raises:
        SerialPortError: 串口打开失败
        ValueError: 参数无效

    Example:
        >>> service.connect('/dev/ttyUSB0', baudrate=115200)
        True
    """
```

#### disconnect

```python
def disconnect(self) -> None:
    """
    断开连接

    关闭串口，释放资源。调用前建议先去使能所有电机。

    Example:
        >>> motor.disable()
        >>> service.disconnect()
    """
```

#### is_connected

```python
@property
def is_connected(self) -> bool:
    """
    获取连接状态

    Returns:
        已连接返回 True，否则返回 False
    """
```

#### scan_ports

```python
@staticmethod
def scan_ports() -> List[PortInfo]:
    """
    扫描可用串口

    Returns:
        可用串口信息列表

    Example:
        >>> ports = ServoService.scan_ports()
        >>> for port in ports:
        ...     print(f"{port.device}: {port.description}")
        /dev/ttyUSB0: USB Serial Port
    """
```

### 2.3 电机获取

#### get_motor_by_axis

```python
def get_motor_by_axis(self, axis: Axis = Axis.Z) -> Motor:
    """
    按轴获取电机实例

    Args:
        axis: 轴类型，默认 Z 轴
            - Axis.X: X 轴 (从站 1, 200W, 1000mm/s)
            - Axis.Y: Y 轴 (从站 2, 100W, 500mm/s)
            - Axis.Z: Z 轴 (从站 3, 100W+抱闸, 500mm/s)

    Returns:
        Motor 实例

    Raises:
        ConnectionError: 未连接

    Example:
        >>> motor_z = service.get_motor_by_axis(Axis.Z)
        >>> motor_x = service.get_motor_by_axis(Axis.X)
    """
```

#### get_motor

```python
def get_motor(self, slave_id: int) -> Motor:
    """
    按从站地址获取电机实例

    Args:
        slave_id: 从站地址 (1-247)

    Returns:
        Motor 实例

    Raises:
        ConnectionError: 未连接
        ValueError: 从站地址无效

    Example:
        >>> motor = service.get_motor(slave_id=3)
    """
```

#### get_all_motors

```python
def get_all_motors(self) -> Dict[Axis, Motor]:
    """
    获取所有轴的电机实例

    Returns:
        轴到电机的映射字典

    Example:
        >>> motors = service.get_all_motors()
        >>> for axis, motor in motors.items():
        ...     print(f"{axis.value}: enabled={motor.is_enabled()}")
    """
```

### 2.4 轴配置

#### get_axis_config

```python
def get_axis_config(self, axis: Axis) -> AxisConfig:
    """
    获取轴配置参数

    Args:
        axis: 轴类型

    Returns:
        AxisConfig 配置对象

    Example:
        >>> config = service.get_axis_config(Axis.Z)
        >>> print(f"最大速度: {config.max_velocity} mm/s")
        >>> print(f"行程: {config.stroke_min}~{config.stroke_max} mm")
    """
```

---

## 3. Motor 电机控制类

### 3.1 类定义

```python
class Motor:
    """
    电机高级控制类

    提供用户友好的电机控制接口，封装底层 Modbus 通信和状态机管理。

    Attributes:
        axis (Axis): 所属轴
        slave_id (int): 从站地址
        is_connected (bool): 连接状态

    Example:
        >>> motor = service.get_motor_by_axis(Axis.Z)
        >>> motor.enable()
        >>> motor.set_velocity_mode()
        >>> motor.set_velocity(100)  # 100 mm/s
        >>> time.sleep(2)
        >>> motor.stop()
        >>> motor.disable()
    """
```

### 3.2 轴信息

#### get_axis

```python
def get_axis(self) -> Axis:
    """
    获取轴类型

    Returns:
        Axis 枚举值

    Example:
        >>> motor.get_axis()
        <Axis.Z: 'Z'>
    """
```

#### get_axis_config

```python
def get_axis_config(self) -> AxisConfig:
    """
    获取轴配置参数

    Returns:
        AxisConfig 配置对象

    Example:
        >>> config = motor.get_axis_config()
        >>> print(f"型号: {config.model}")
        >>> print(f"电机功率: {config.motor_power}W")
        >>> print(f"丝杠导程: {config.ball_screw_lead}mm")
    """
```

#### get_max_velocity

```python
def get_max_velocity(self) -> float:
    """
    获取最大速度

    Returns:
        最大速度 (mm/s)

    Example:
        >>> motor.get_max_velocity()
        500.0
    """
```

#### get_stroke_range

```python
def get_stroke_range(self) -> Tuple[float, float]:
    """
    获取行程范围

    Returns:
        元组 (最小位置, 最大位置)，单位 mm

    Example:
        >>> min_pos, max_pos = motor.get_stroke_range()
        >>> print(f"行程范围: {min_pos}~{max_pos} mm")
    """
```

### 3.3 抱闸控制 (Z 轴)

#### has_brake

```python
def has_brake(self) -> bool:
    """
    判断是否有抱闸

    Returns:
        有抱闸返回 True

    Note:
        仅 Z 轴配有抱闸

    Example:
        >>> if motor.has_brake():
        ...     print("此轴配有抱闸")
    """
```

#### release_brake

```python
def release_brake(self) -> bool:
    """
    释放抱闸

    仅 Z 轴有效。使能时会自动释放抱闸。

    Returns:
        成功返回 True

    Raises:
        MotorError: 轴无抱闸或释放失败

    Example:
        >>> motor.release_brake()
        True
    """
```

#### engage_brake

```python
def engage_brake(self) -> bool:
    """
    锁定抱闸

    仅 Z 轴有效。去使能时会自动锁定抱闸。

    Returns:
        成功返回 True

    Raises:
        MotorError: 轴无抱闸或锁定失败

    Warning:
        锁定抱闸前请确保电机已停止运动

    Example:
        >>> motor.stop()
        >>> motor.engage_brake()
        True
    """
```

### 3.4 使能控制

#### enable

```python
def enable(self) -> bool:
    """
    使能电机

    自动执行 CiA402 状态机转换:
    1. 如有故障，先尝试故障复位
    2. 如有抱闸（Z轴），先释放抱闸
    3. 执行状态转换到 Operation Enabled

    Returns:
        成功返回 True

    Raises:
        MotorFaultError: 故障复位失败
        CommunicationError: 通信错误

    Example:
        >>> if motor.enable():
        ...     print("使能成功")
        ... else:
        ...     print("使能失败")

    Warning:
        使能前请确保电机和负载处于安全状态
    """
```

#### disable

```python
def disable(self) -> bool:
    """
    去使能电机

    执行状态机转换到 Switch On Disabled 状态。
    如有抱闸（Z轴），会自动锁定抱闸。

    Returns:
        成功返回 True

    Example:
        >>> motor.disable()
        True
    """
```

#### is_enabled

```python
def is_enabled(self) -> bool:
    """
    查询使能状态

    Returns:
        已使能返回 True

    Example:
        >>> if motor.is_enabled():
        ...     motor.move_absolute(100)
    """
```

#### reset_fault

```python
def reset_fault(self) -> bool:
    """
    故障复位

    发送故障复位命令（控制字 Bit7 上升沿）。

    Returns:
        复位成功返回 True

    Note:
        部分故障（如硬件故障）无法通过软件复位

    Example:
        >>> if motor.is_fault():
        ...     motor.reset_fault()
    """
```

#### emergency_stop

```python
def emergency_stop(self) -> bool:
    """
    紧急停止

    立即停止电机运动，进入 Quick Stop 状态。

    Returns:
        成功返回 True

    Warning:
        紧急停止后需要重新使能才能继续运动

    Example:
        >>> motor.emergency_stop()
        True
    """
```

### 3.5 运动方向控制

#### jog_forward

```python
def jog_forward(self, velocity: float) -> bool:
    """
    正向点动

    电机以指定速度正向连续运动，直到调用 stop()。

    Args:
        velocity: 速度 (mm/s)，正值
            自动限制在最大速度范围内

    Returns:
        成功返回 True

    Raises:
        MotorNotEnabledError: 电机未使能

    Example:
        >>> motor.jog_forward(100)  # 100 mm/s 正转
        >>> time.sleep(2)
        >>> motor.stop()
    """
```

#### jog_reverse

```python
def jog_reverse(self, velocity: float) -> bool:
    """
    反向点动

    电机以指定速度反向连续运动，直到调用 stop()。

    Args:
        velocity: 速度 (mm/s)，正值
            自动限制在最大速度范围内

    Returns:
        成功返回 True

    Raises:
        MotorNotEnabledError: 电机未使能

    Example:
        >>> motor.jog_reverse(100)  # 100 mm/s 反转
        >>> time.sleep(2)
        >>> motor.stop()
    """
```

#### stop

```python
def stop(self) -> bool:
    """
    停止运动

    减速停止当前运动，使用配置的减速度。

    Returns:
        成功返回 True

    Example:
        >>> motor.jog_forward(100)
        >>> time.sleep(1)
        >>> motor.stop()
    """
```

#### quick_stop

```python
def quick_stop(self) -> bool:
    """
    快速停止

    使用快速停止减速度立即停止。

    Returns:
        成功返回 True

    Note:
        快速停止后电机仍保持使能状态

    Example:
        >>> motor.quick_stop()
    """
```

### 3.6 运行模式

#### set_position_mode

```python
def set_position_mode(self) -> bool:
    """
    设置位置模式

    切换到 Profile Position (PP) 模式。

    Returns:
        成功返回 True

    Example:
        >>> motor.set_position_mode()
        >>> motor.move_absolute(100)
    """
```

#### set_velocity_mode

```python
def set_velocity_mode(self) -> bool:
    """
    设置速度模式

    切换到 Profile Velocity (PV) 模式。

    Returns:
        成功返回 True

    Example:
        >>> motor.set_velocity_mode()
        >>> motor.set_velocity(100)  # 100 mm/s
    """
```

#### set_torque_mode

```python
def set_torque_mode(self) -> bool:
    """
    设置力矩模式

    切换到 Profile Torque (PT) 模式。

    Returns:
        成功返回 True

    Example:
        >>> motor.set_torque_mode()
        >>> motor.set_torque(100)  # 10% 额定力矩
    """
```

#### set_homing_mode

```python
def set_homing_mode(self) -> bool:
    """
    设置回零模式

    切换到 Homing (HM) 模式。

    Returns:
        成功返回 True

    Example:
        >>> motor.set_homing_mode()
        >>> motor.start_homing(method=HomingMethod.NEGATIVE_LIMIT)
    """
```

#### get_current_mode

```python
def get_current_mode(self) -> OperationMode:
    """
    获取当前运行模式

    Returns:
        OperationMode 枚举值

    Example:
        >>> mode = motor.get_current_mode()
        >>> if mode == OperationMode.PROFILE_POSITION:
        ...     print("当前为位置模式")
    """
```

### 3.7 位置控制

#### move_absolute

```python
def move_absolute(
    self,
    position: float,
    velocity: float = None,
    acceleration: float = None,
    deceleration: float = None,
    wait: bool = False,
    timeout: float = 30.0
) -> bool:
    """
    绝对位置移动

    移动到指定的绝对位置。

    Args:
        position: 目标位置 (mm)
            自动限制在行程范围内
        velocity: 速度 (mm/s)，None 使用默认值
            自动限制在最大速度范围内
        acceleration: 加速度 (mm/s²)，None 使用默认值
        deceleration: 减速度 (mm/s²)，None 使用默认值
        wait: 是否等待运动完成
        timeout: 等待超时时间（秒）

    Returns:
        命令发送成功返回 True
        如果 wait=True，运动完成返回 True

    Raises:
        MotorNotEnabledError: 电机未使能
        PositionOutOfRangeError: 位置超出行程范围
        TimeoutError: 等待超时

    Example:
        >>> # 非阻塞移动
        >>> motor.move_absolute(100)
        >>> motor.wait_for_position_reached()

        >>> # 阻塞移动
        >>> motor.move_absolute(100, wait=True, timeout=10)
    """
```

#### move_relative

```python
def move_relative(
    self,
    distance: float,
    velocity: float = None,
    acceleration: float = None,
    deceleration: float = None,
    wait: bool = False,
    timeout: float = 30.0
) -> bool:
    """
    相对位置移动

    从当前位置移动指定距离。

    Args:
        distance: 移动距离 (mm)
            正值正向移动，负值反向移动
        velocity: 速度 (mm/s)
        acceleration: 加速度 (mm/s²)
        deceleration: 减速度 (mm/s²)
        wait: 是否等待运动完成
        timeout: 等待超时时间（秒）

    Returns:
        成功返回 True

    Raises:
        MotorNotEnabledError: 电机未使能
        PositionOutOfRangeError: 目标位置超出行程范围

    Example:
        >>> motor.move_relative(10)   # 正向移动 10mm
        >>> motor.move_relative(-10)  # 反向移动 10mm
    """
```

#### get_current_position

```python
def get_current_position(self) -> float:
    """
    获取当前位置

    Returns:
        当前位置 (mm)

    Example:
        >>> pos = motor.get_current_position()
        >>> print(f"当前位置: {pos:.2f} mm")
    """
```

#### set_position_zero

```python
def set_position_zero(self) -> bool:
    """
    设置当前位置为零点

    将当前位置设为坐标原点 (0)。

    Returns:
        成功返回 True

    Warning:
        此操作会改变位置参考，请谨慎使用

    Example:
        >>> motor.set_position_zero()
    """
```

#### is_in_position

```python
def is_in_position(self) -> bool:
    """
    判断是否到达目标位置

    检查状态字的目标到达位 (Bit10)。

    Returns:
        已到达返回 True

    Example:
        >>> motor.move_absolute(100)
        >>> while not motor.is_in_position():
        ...     time.sleep(0.1)
        >>> print("已到达目标位置")
    """
```

#### wait_for_position_reached

```python
def wait_for_position_reached(self, timeout: float = 30.0) -> bool:
    """
    等待位置到达

    阻塞等待电机到达目标位置。

    Args:
        timeout: 超时时间（秒）

    Returns:
        到达返回 True，超时返回 False

    Raises:
        MotorFaultError: 运动过程中发生故障

    Example:
        >>> motor.move_absolute(100)
        >>> if motor.wait_for_position_reached(timeout=10):
        ...     print("到达")
        ... else:
        ...     print("超时")
    """
```

### 3.8 速度控制

#### set_velocity

```python
def set_velocity(self, velocity: float) -> bool:
    """
    设置目标速度

    在速度模式下设置目标速度。

    Args:
        velocity: 目标速度 (mm/s)
            正值正转，负值反转
            自动限制在最大速度范围内

    Returns:
        成功返回 True

    Raises:
        MotorNotEnabledError: 电机未使能

    Example:
        >>> motor.set_velocity_mode()
        >>> motor.set_velocity(100)   # 正转 100 mm/s
        >>> motor.set_velocity(-100)  # 反转 100 mm/s
        >>> motor.set_velocity(0)     # 停止
    """
```

#### set_acceleration

```python
def set_acceleration(self, acceleration: float) -> bool:
    """
    设置加速度

    Args:
        acceleration: 加速度 (mm/s²)

    Returns:
        成功返回 True

    Example:
        >>> motor.set_acceleration(500)
    """
```

#### set_deceleration

```python
def set_deceleration(self, deceleration: float) -> bool:
    """
    设置减速度

    Args:
        deceleration: 减速度 (mm/s²)

    Returns:
        成功返回 True

    Example:
        >>> motor.set_deceleration(500)
    """
```

#### get_current_velocity

```python
def get_current_velocity(self) -> float:
    """
    获取当前速度

    Returns:
        当前速度 (mm/s)，正值正转，负值反转

    Example:
        >>> vel = motor.get_current_velocity()
        >>> print(f"当前速度: {vel:.1f} mm/s")
    """
```

### 3.9 力矩控制

#### set_torque

```python
def set_torque(self, torque: int) -> bool:
    """
    设置目标力矩

    在力矩模式下设置目标力矩。

    Args:
        torque: 目标力矩 (0.1% 额定力矩)
            范围 -1000 ~ 1000 (即 -100% ~ 100%)

    Returns:
        成功返回 True

    Raises:
        MotorNotEnabledError: 电机未使能

    Example:
        >>> motor.set_torque_mode()
        >>> motor.set_torque(100)  # 10% 额定力矩
    """
```

#### set_torque_limit

```python
def set_torque_limit(self, positive: int, negative: int) -> bool:
    """
    设置力矩限制

    Args:
        positive: 正向力矩限制 (0.1%)
        negative: 反向力矩限制 (0.1%)

    Returns:
        成功返回 True

    Example:
        >>> motor.set_torque_limit(500, 500)  # 限制为 ±50%
    """
```

#### get_current_torque

```python
def get_current_torque(self) -> int:
    """
    获取当前力矩

    Returns:
        当前力矩 (0.1% 额定力矩)

    Example:
        >>> torque = motor.get_current_torque()
        >>> print(f"当前力矩: {torque/10:.1f}%")
    """
```

### 3.10 回零控制

#### start_homing

```python
def start_homing(self, method: HomingMethod = HomingMethod.NEGATIVE_LIMIT) -> bool:
    """
    开始回零

    启动回零操作。

    Args:
        method: 回零方式
            - HomingMethod.NEGATIVE_LIMIT (17): 负限位开关
            - HomingMethod.POSITIVE_LIMIT (18): 正限位开关
            - HomingMethod.NEGATIVE_LIMIT_INDEX (19): 负限位+Index
            - HomingMethod.POSITIVE_LIMIT_INDEX (20): 正限位+Index
            - HomingMethod.CURRENT_POSITION (35): 当前位置
            - HomingMethod.STALL (37): 堵转回零

    Returns:
        成功启动返回 True

    Raises:
        MotorNotEnabledError: 电机未使能

    Example:
        >>> motor.set_homing_mode()
        >>> motor.start_homing(HomingMethod.NEGATIVE_LIMIT)
        >>> motor.wait_for_homing_done(timeout=60)
    """
```

#### set_homing_velocity

```python
def set_homing_velocity(self, high_speed: float, low_speed: float) -> bool:
    """
    设置回零速度

    Args:
        high_speed: 高速寻找开关 (mm/s)
        low_speed: 低速寻找零点 (mm/s)

    Returns:
        成功返回 True

    Example:
        >>> motor.set_homing_velocity(high_speed=50, low_speed=10)
    """
```

#### set_homing_acceleration

```python
def set_homing_acceleration(self, acceleration: float) -> bool:
    """
    设置回零加速度

    Args:
        acceleration: 加速度 (mm/s²)

    Returns:
        成功返回 True
    """
```

#### set_home_offset

```python
def set_home_offset(self, offset: float) -> bool:
    """
    设置原点偏移

    回零完成后的位置偏移量。

    Args:
        offset: 偏移量 (mm)

    Returns:
        成功返回 True
    """
```

#### is_homing_completed

```python
def is_homing_completed(self) -> bool:
    """
    判断回零是否完成

    Returns:
        完成返回 True

    Example:
        >>> if motor.is_homing_completed():
        ...     print("回零完成")
    """
```

#### wait_for_homing_done

```python
def wait_for_homing_done(self, timeout: float = 60.0) -> bool:
    """
    等待回零完成

    Args:
        timeout: 超时时间（秒）

    Returns:
        完成返回 True，超时返回 False

    Raises:
        HomingError: 回零过程中发生错误

    Example:
        >>> motor.start_homing()
        >>> if motor.wait_for_homing_done(timeout=60):
        ...     print("回零成功")
    """
```

### 3.11 限位开关配置

#### set_positive_limit_switch

```python
def set_positive_limit_switch(
    self,
    di_number: int,
    logic: int = 0
) -> bool:
    """
    设置正向限位开关

    Args:
        di_number: DI 端口号 (1-3)
        logic: 逻辑
            - 0: 常闭 (低电平有效)
            - 1: 常开 (高电平有效)

    Returns:
        成功返回 True

    Example:
        >>> motor.set_positive_limit_switch(di_number=1, logic=0)
    """
```

#### set_negative_limit_switch

```python
def set_negative_limit_switch(
    self,
    di_number: int,
    logic: int = 0
) -> bool:
    """
    设置负向限位开关

    Args:
        di_number: DI 端口号 (1-3)
        logic: 逻辑 (0=常闭, 1=常开)

    Returns:
        成功返回 True
    """
```

#### set_home_switch

```python
def set_home_switch(
    self,
    di_number: int,
    logic: int = 0
) -> bool:
    """
    设置原点开关

    Args:
        di_number: DI 端口号 (1-3)
        logic: 逻辑 (0=常闭, 1=常开)

    Returns:
        成功返回 True
    """
```

#### enable_software_limit

```python
def enable_software_limit(self, min_pos: float, max_pos: float) -> bool:
    """
    启用软件限位

    Args:
        min_pos: 最小位置限制 (mm)
        max_pos: 最大位置限制 (mm)

    Returns:
        成功返回 True

    Example:
        >>> motor.enable_software_limit(min_pos=0, max_pos=100)
    """
```

#### disable_software_limit

```python
def disable_software_limit(self) -> bool:
    """
    禁用软件限位

    Returns:
        成功返回 True
    """
```

#### get_limit_switch_status

```python
def get_limit_switch_status(self) -> Dict[str, bool]:
    """
    获取限位开关状态

    Returns:
        状态字典，包含:
        - 'positive': 正限位状态
        - 'negative': 负限位状态
        - 'home': 原点开关状态

    Example:
        >>> status = motor.get_limit_switch_status()
        >>> if status['positive']:
        ...     print("正限位触发")
    """
```

### 3.12 状态查询

#### get_status

```python
def get_status(self) -> MotorStatus:
    """
    获取电机综合状态

    Returns:
        MotorStatus 状态对象

    Example:
        >>> status = motor.get_status()
        >>> print(f"位置: {status.position:.2f} mm")
        >>> print(f"速度: {status.velocity:.1f} mm/s")
        >>> print(f"使能: {status.enabled}")
        >>> print(f"故障: {status.fault}")
    """
```

#### get_fault_code

```python
def get_fault_code(self) -> int:
    """
    获取故障代码

    Returns:
        故障代码，0 表示无故障

    Example:
        >>> code = motor.get_fault_code()
        >>> if code != 0:
        ...     print(f"故障码: 0x{code:04X}")
    """
```

#### get_fault_info

```python
def get_fault_info(self) -> Optional[FaultInfo]:
    """
    获取故障详细信息

    Returns:
        FaultInfo 对象，无故障返回 None

    Example:
        >>> info = motor.get_fault_info()
        >>> if info:
        ...     print(f"故障: {info.name}")
        ...     print(f"说明: {info.description}")
        ...     print(f"建议: {info.suggestion}")
    """
```

#### get_temperature

```python
def get_temperature(self) -> int:
    """
    获取驱动器温度

    Returns:
        温度 (°C)

    Example:
        >>> temp = motor.get_temperature()
        >>> print(f"温度: {temp}°C")
    """
```

#### get_bus_voltage

```python
def get_bus_voltage(self) -> float:
    """
    获取母线电压

    Returns:
        电压 (V)

    Example:
        >>> voltage = motor.get_bus_voltage()
        >>> print(f"电压: {voltage:.1f}V")
    """
```

#### is_fault

```python
def is_fault(self) -> bool:
    """
    判断是否处于故障状态

    Returns:
        有故障返回 True
    """
```

#### is_running

```python
def is_running(self) -> bool:
    """
    判断电机是否正在运动

    Returns:
        运动中返回 True
    """
```

### 3.13 参数管理

#### save_parameters

```python
def save_parameters(self) -> bool:
    """
    保存参数到 EEPROM

    将当前参数保存到非易失性存储器。

    Returns:
        成功返回 True

    Warning:
        EEPROM 写入次数有限，避免频繁保存

    Example:
        >>> motor.set_acceleration(500)
        >>> motor.save_parameters()
    """
```

#### restore_factory_defaults

```python
def restore_factory_defaults(self) -> bool:
    """
    恢复出厂设置

    Returns:
        成功返回 True

    Warning:
        此操作会清除所有用户配置

    Example:
        >>> motor.restore_factory_defaults()
        >>> motor.save_parameters()
    """
```

### 3.14 事件回调

#### on_position_reached

```python
def on_position_reached(self, callback: Callable[[], None]) -> None:
    """
    注册位置到达回调

    Args:
        callback: 回调函数，无参数

    Example:
        >>> def on_reached():
        ...     print("位置到达!")
        >>> motor.on_position_reached(on_reached)
    """
```

#### on_fault_occurred

```python
def on_fault_occurred(self, callback: Callable[[int], None]) -> None:
    """
    注册故障发生回调

    Args:
        callback: 回调函数，参数为故障码

    Example:
        >>> def on_fault(code):
        ...     print(f"故障: 0x{code:04X}")
        >>> motor.on_fault_occurred(on_fault)
    """
```

#### on_homing_completed

```python
def on_homing_completed(self, callback: Callable[[], None]) -> None:
    """
    注册回零完成回调

    Args:
        callback: 回调函数
    """
```

#### on_limit_triggered

```python
def on_limit_triggered(self, callback: Callable[[str], None]) -> None:
    """
    注册限位触发回调

    Args:
        callback: 回调函数，参数为限位类型 ('positive'/'negative')
    """
```

---

## 4. 轴配置

### 4.1 Axis 枚举

```python
class Axis(Enum):
    """轴类型枚举"""
    X = "X"  # X 轴
    Y = "Y"  # Y 轴
    Z = "Z"  # Z 轴
```

### 4.2 AxisConfig 数据类

```python
@dataclass
class AxisConfig:
    """轴配置参数"""

    axis: Axis                     # 轴类型
    model: str                     # 型号 (CFG4/CFG5/CFG8)
    motor_power: int               # 电机功率 (W)
    has_brake: bool                # 是否有抱闸
    ball_screw_lead: float         # 丝杠导程 (mm)
    max_velocity: float            # 最大速度 (mm/s)
    stroke_min: float              # 最小行程 (mm)
    stroke_max: float              # 最大行程 (mm)
    positioning_accuracy: float    # 定位精度 (mm)
    repeat_accuracy: float         # 重复定位精度 (mm)
    max_payload_horizontal: float  # 水平最大负载 (kg)
    max_payload_vertical: float    # 垂直最大负载 (kg)
    slave_id: int                  # 默认从站地址
```

### 4.3 预定义配置

```python
AXIS_CONFIGS: Dict[Axis, AxisConfig] = {
    Axis.X: AxisConfig(
        axis=Axis.X,
        model="CFG8",
        motor_power=200,
        has_brake=False,
        ball_screw_lead=20.0,
        max_velocity=1000.0,
        stroke_min=50.0,
        stroke_max=1100.0,
        positioning_accuracy=0.02,
        repeat_accuracy=0.005,
        max_payload_horizontal=75.0,
        max_payload_vertical=30.0,
        slave_id=1
    ),
    Axis.Y: AxisConfig(
        axis=Axis.Y,
        model="CFG5",
        motor_power=100,
        has_brake=False,
        ball_screw_lead=10.0,
        max_velocity=500.0,
        stroke_min=100.0,
        stroke_max=500.0,
        positioning_accuracy=0.015,
        repeat_accuracy=0.005,
        max_payload_horizontal=30.0,
        max_payload_vertical=15.0,
        slave_id=2
    ),
    Axis.Z: AxisConfig(
        axis=Axis.Z,
        model="CFG4",
        motor_power=100,
        has_brake=True,
        ball_screw_lead=10.0,
        max_velocity=500.0,
        stroke_min=50.0,
        stroke_max=100.0,
        positioning_accuracy=0.01,
        repeat_accuracy=0.005,
        max_payload_horizontal=20.0,
        max_payload_vertical=10.0,
        slave_id=3
    ),
}
```

### 4.4 轴参数对照表

| 参数 | X 轴 | Y 轴 | Z 轴 |
|------|------|------|------|
| 型号 | CFG8 | CFG5 | CFG4 |
| 电机功率 | 200W | 100W | 100W+抱闸 |
| 丝杠导程 | 20 mm | 10 mm | 10 mm |
| 最大速度 | 1000 mm/s | 500 mm/s | 500 mm/s |
| 行程范围 | 50~1100 mm | 100~500 mm | 50~100 mm |
| 定位精度 | ±0.02 mm | ±0.015 mm | ±0.01 mm |
| 重复精度 | ±0.005 mm | ±0.005 mm | ±0.005 mm |
| 水平负载 | 75 kg | 30 kg | 20 kg |
| 垂直负载 | 30 kg | 15 kg | 10 kg |
| 从站地址 | 1 | 2 | 3 |

---

## 5. 数据类型

### 5.1 OperationMode 枚举

```python
class OperationMode(IntEnum):
    """运行模式"""
    NO_MODE = 0x00
    PROFILE_POSITION = 0x01   # PP - 轮廓位置模式
    VELOCITY_MODE = 0x02      # VM - 速度模式
    PROFILE_VELOCITY = 0x03   # PV - 轮廓速度模式
    PROFILE_TORQUE = 0x04     # PT - 轮廓力矩模式
    HOMING = 0x06             # HM - 回零模式
    INTERPOLATION = 0x07      # IP - 插补模式
    CSP = 0x08                # 周期同步位置模式
    CSV = 0x09                # 周期同步速度模式
    CST = 0x0A                # 周期同步力矩模式
```

### 5.2 HomingMethod 枚举

```python
class HomingMethod(IntEnum):
    """回零方式"""
    NEGATIVE_LIMIT = 17       # 负限位开关
    POSITIVE_LIMIT = 18       # 正限位开关
    NEGATIVE_LIMIT_INDEX = 19 # 负限位 + Index
    POSITIVE_LIMIT_INDEX = 20 # 正限位 + Index
    NEGATIVE_INDEX = 33       # 负向 Index
    POSITIVE_INDEX = 34       # 正向 Index
    CURRENT_POSITION = 35     # 当前位置
    STALL = 37                # 堵转回零
```

### 5.3 MotorStatus 数据类

```python
@dataclass
class MotorStatus:
    """电机状态"""

    enabled: bool           # 使能状态
    fault: bool             # 故障状态
    running: bool           # 运行状态
    in_position: bool       # 到位状态
    homing_done: bool       # 回零完成
    position: float         # 当前位置 (mm)
    velocity: float         # 当前速度 (mm/s)
    torque: int             # 当前力矩 (0.1%)
    state_machine: int      # 状态机状态值
    fault_code: int         # 故障代码
    temperature: int        # 温度 (°C)
    bus_voltage: float      # 母线电压 (V)
    axis: Axis              # 所属轴
```

### 5.4 FaultInfo 数据类

```python
@dataclass
class FaultInfo:
    """故障信息"""

    code: int               # 故障码
    name: str               # 故障名称 (英文)
    description: str        # 故障描述 (中文)
    severity: str           # 严重程度: 'warning', 'error', 'critical'
    auto_recover: bool      # 是否可自动恢复
    suggestion: str         # 处理建议
```

### 5.5 常见故障码

| 故障码 | 名称 | 说明 | 严重程度 |
|--------|------|------|----------|
| 0x0000 | No error | 无故障 | - |
| 0x2300 | Overcurrent | 电机过流 | critical |
| 0x3110 | Overvoltage | 母线过压 | critical |
| 0x3120 | Undervoltage | 母线欠压 | critical |
| 0x4210 | Over temperature | 驱动器过温 | critical |
| 0x7310 | Overspeed | 电机超速 | critical |
| 0x8611 | Following error | 跟随误差 | critical |
| 0x8612 | Homing error | 回零错误 | error |

---

## 6. 异常类型

### 6.1 异常层次

```
ServoMotorError (基类)
├── CommunicationError (通信错误)
│   ├── SerialPortError (串口错误)
│   ├── ModbusTimeoutError (通信超时)
│   ├── ModbusCRCError (CRC 校验失败)
│   └── ModbusExceptionError (从站异常响应)
├── MotorError (电机错误)
│   ├── MotorFaultError (电机故障)
│   ├── MotorNotEnabledError (电机未使能)
│   └── StateMachineError (状态机错误)
├── MotionError (运动错误)
│   ├── PositionOutOfRangeError (位置超限)
│   ├── VelocityExceededError (速度超限)
│   └── HomingError (回零错误)
└── ConfigurationError (配置错误)
    ├── InvalidParameterError (参数无效)
    └── AxisNotFoundError (轴不存在)
```

### 6.2 异常详情

#### ServoMotorError

```python
class ServoMotorError(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: int = 0, details: dict = None):
        """
        Args:
            message: 错误消息
            code: 错误代码
            details: 详细信息字典
        """
        self.code = code
        self.details = details or {}
        self.timestamp = time.time()
```

#### ModbusTimeoutError

```python
class ModbusTimeoutError(CommunicationError):
    """通信超时"""

    def __init__(self, slave_id: int, function_code: int, timeout: float):
        """
        Args:
            slave_id: 从站地址
            function_code: 功能码
            timeout: 超时时间
        """
```

#### MotorFaultError

```python
class MotorFaultError(MotorError):
    """电机故障"""

    def __init__(self, fault_code: int, axis: Axis = None):
        """
        Args:
            fault_code: 故障代码
            axis: 所属轴
        """
        self.fault_info = get_fault_info(fault_code)
```

### 6.3 异常处理示例

```python
from servo_service import (
    ServoService, Axis,
    ModbusTimeoutError, MotorFaultError, PositionOutOfRangeError
)

service = ServoService()

try:
    service.connect('/dev/ttyUSB0')
    motor = service.get_motor_by_axis(Axis.Z)
    motor.enable()
    motor.move_absolute(200)  # 可能超出行程

except ModbusTimeoutError as e:
    print(f"通信超时: 从站 {e.details['slave_id']}")

except MotorFaultError as e:
    print(f"电机故障: {e.fault_info.description}")
    print(f"处理建议: {e.fault_info.suggestion}")

except PositionOutOfRangeError as e:
    print(f"位置超限: {e.details['position']}mm")
    print(f"有效范围: {e.details['min']}~{e.details['max']}mm")

finally:
    service.disconnect()
```

---

## 7. Modbus 底层接口

### 7.1 ModbusClient 类

```python
class ModbusClient:
    """Modbus RTU 客户端"""

    def read_holding_registers(
        self,
        slave_id: int,
        address: int,
        count: int
    ) -> List[int]:
        """
        读取保持寄存器 (功能码 0x03)

        Args:
            slave_id: 从站地址 (1-247)
            address: 起始地址
            count: 寄存器数量 (1-125)

        Returns:
            寄存器值列表

        Raises:
            ModbusTimeoutError: 超时
            ModbusCRCError: CRC 错误
            ModbusExceptionError: 从站异常
        """

    def read_input_registers(
        self,
        slave_id: int,
        address: int,
        count: int
    ) -> List[int]:
        """读取输入寄存器 (功能码 0x04)"""

    def write_single_register(
        self,
        slave_id: int,
        address: int,
        value: int
    ) -> bool:
        """写单个寄存器 (功能码 0x06)"""

    def write_multiple_registers(
        self,
        slave_id: int,
        address: int,
        values: List[int]
    ) -> bool:
        """写多个寄存器 (功能码 0x10)"""
```

### 7.2 寄存器地址

```python
class Registers:
    """寄存器地址常量"""

    # 控制相关
    CONTROL_WORD = 0x0380          # 控制字
    STATUS_WORD = 0x0381           # 状态字
    OPERATION_MODE = 0x03C3        # 运行模式

    # 位置相关
    TARGET_POSITION = 0x03C5       # 目标位置 (32位)
    POSITION_ACTUAL = 0x03C8       # 实际位置 (32位)

    # 速度相关
    TARGET_VELOCITY = 0x03D2       # 目标速度 (32位)
    VELOCITY_ACTUAL = 0x03D5       # 实际速度 (32位)
    PROFILE_VELOCITY = 0x03CD      # 轮廓速度

    # 加减速
    PROFILE_ACCELERATION = 0x03D0  # 加速度
    PROFILE_DECELERATION = 0x03D1  # 减速度

    # 力矩相关
    TARGET_TORQUE = 0x03DB         # 目标力矩
    TORQUE_ACTUAL = 0x03DC         # 实际力矩

    # 回零相关
    HOMING_METHOD = 0x03E3         # 回零方式
    HOMING_SPEED_HIGH = 0x03E4     # 回零高速
    HOMING_SPEED_LOW = 0x03E5      # 回零低速

    # 故障相关
    FAULT_CODE = 0x0398            # 故障代码
```

---

## 8. 使用示例

### 8.1 基本位置控制

```python
from servo_service import ServoService, Axis

# 创建服务并连接
service = ServoService()
service.connect('/dev/ttyUSB0', baudrate=115200)

try:
    # 获取 Z 轴电机
    motor = service.get_motor_by_axis(Axis.Z)

    # 使能
    motor.enable()

    # 设置位置模式
    motor.set_position_mode()

    # 设置运动参数
    motor.set_acceleration(500)
    motor.set_deceleration(500)

    # 绝对位置移动
    motor.move_absolute(position=50, velocity=100)
    motor.wait_for_position_reached(timeout=10)
    print(f"当前位置: {motor.get_current_position():.2f} mm")

    # 相对位置移动
    motor.move_relative(distance=10)
    motor.wait_for_position_reached()
    print(f"当前位置: {motor.get_current_position():.2f} mm")

finally:
    motor.disable()
    service.disconnect()
```

### 8.2 速度控制

```python
from servo_service import ServoService, Axis
import time

service = ServoService()
service.connect('/dev/ttyUSB0')

motor = service.get_motor_by_axis(Axis.Z)
motor.enable()

try:
    # 设置速度模式
    motor.set_velocity_mode()

    # 正转
    print("正转 100 mm/s")
    motor.set_velocity(100)
    time.sleep(2)

    # 反转
    print("反转 100 mm/s")
    motor.set_velocity(-100)
    time.sleep(2)

    # 停止
    motor.set_velocity(0)

finally:
    motor.disable()
    service.disconnect()
```

### 8.3 点动控制

```python
from servo_service import ServoService, Axis
import time

service = ServoService()
service.connect('/dev/ttyUSB0')

motor = service.get_motor_by_axis(Axis.Z)
motor.enable()

try:
    # 正向点动
    print("正向点动...")
    motor.jog_forward(velocity=50)
    time.sleep(1)
    motor.stop()

    time.sleep(0.5)

    # 反向点动
    print("反向点动...")
    motor.jog_reverse(velocity=50)
    time.sleep(1)
    motor.stop()

finally:
    motor.disable()
    service.disconnect()
```

### 8.4 回零操作

```python
from servo_service import ServoService, Axis, HomingMethod

service = ServoService()
service.connect('/dev/ttyUSB0')

motor = service.get_motor_by_axis(Axis.Z)

try:
    # 配置限位开关
    motor.set_negative_limit_switch(di_number=1, logic=0)
    motor.set_positive_limit_switch(di_number=2, logic=0)

    # 使能并设置回零模式
    motor.enable()
    motor.set_homing_mode()

    # 配置回零参数
    motor.set_homing_velocity(high_speed=50, low_speed=10)
    motor.set_homing_acceleration(100)
    motor.set_home_offset(0)

    # 开始回零
    print("开始回零...")
    motor.start_homing(method=HomingMethod.NEGATIVE_LIMIT)

    # 等待完成
    if motor.wait_for_homing_done(timeout=60):
        print("回零完成!")
        print(f"当前位置: {motor.get_current_position():.2f} mm")
    else:
        print("回零超时!")

finally:
    motor.disable()
    service.disconnect()
```

### 8.5 多轴控制

```python
from servo_service import ServoService, Axis
import threading

service = ServoService()
service.connect('/dev/ttyUSB0')

# 获取所有轴
motors = service.get_all_motors()

def move_axis(motor, position):
    """移动单轴"""
    motor.enable()
    motor.set_position_mode()
    motor.move_absolute(position)
    motor.wait_for_position_reached()

try:
    # 并行移动所有轴
    threads = []
    positions = {Axis.X: 500, Axis.Y: 200, Axis.Z: 50}

    for axis, motor in motors.items():
        t = threading.Thread(
            target=move_axis,
            args=(motor, positions[axis])
        )
        threads.append(t)
        t.start()

    # 等待所有轴完成
    for t in threads:
        t.join()

    print("所有轴移动完成")

    # 打印各轴位置
    for axis, motor in motors.items():
        pos = motor.get_current_position()
        print(f"{axis.value}轴位置: {pos:.2f} mm")

finally:
    for motor in motors.values():
        motor.disable()
    service.disconnect()
```

### 8.6 状态监控

```python
from servo_service import ServoService, Axis
import time

service = ServoService()
service.connect('/dev/ttyUSB0')

motor = service.get_motor_by_axis(Axis.Z)

# 注册回调
def on_fault(code):
    info = motor.get_fault_info()
    print(f"故障! 代码: 0x{code:04X}")
    print(f"说明: {info.description}")
    print(f"建议: {info.suggestion}")

motor.on_fault_occurred(on_fault)

try:
    motor.enable()
    motor.set_velocity_mode()
    motor.set_velocity(100)

    # 监控状态
    for _ in range(20):
        status = motor.get_status()
        print(f"位置: {status.position:8.2f} mm | "
              f"速度: {status.velocity:6.1f} mm/s | "
              f"力矩: {status.torque/10:5.1f}% | "
              f"温度: {status.temperature}°C")
        time.sleep(0.5)

    motor.stop()

finally:
    motor.disable()
    service.disconnect()
```

### 8.7 异常处理

```python
from servo_service import (
    ServoService, Axis,
    ServoMotorError, ModbusTimeoutError, MotorFaultError,
    PositionOutOfRangeError
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

service = ServoService()

try:
    # 连接
    service.connect('/dev/ttyUSB0')
    motor = service.get_motor_by_axis(Axis.Z)

    # 使能（可能有故障）
    if motor.is_fault():
        logger.warning("检测到故障，尝试复位...")
        motor.reset_fault()

    motor.enable()

    # 获取行程范围
    min_pos, max_pos = motor.get_stroke_range()
    logger.info(f"行程范围: {min_pos}~{max_pos} mm")

    # 尝试移动到超出范围的位置
    try:
        motor.move_absolute(position=200)  # 可能超限
    except PositionOutOfRangeError as e:
        logger.error(f"位置超限: {e}")
        # 移动到安全位置
        motor.move_absolute(position=max_pos)

except ModbusTimeoutError as e:
    logger.error(f"通信超时: {e}")

except MotorFaultError as e:
    logger.error(f"电机故障: {e.fault_info.description}")
    logger.info(f"处理建议: {e.fault_info.suggestion}")

except ServoMotorError as e:
    logger.error(f"伺服错误: {e}")

finally:
    try:
        if service.is_connected:
            motor.disable()
            service.disconnect()
    except Exception:
        pass
```

---

## 附录

### A. 单位说明

| 物理量 | 单位 | 说明 |
|--------|------|------|
| 位置 | mm | 毫米 |
| 速度 | mm/s | 毫米/秒 |
| 加速度 | mm/s² | 毫米/秒² |
| 力矩 | 0.1% | 额定力矩的千分之一 |
| 温度 | °C | 摄氏度 |
| 电压 | V | 伏特 |
| 时间 | s | 秒 |

### B. 状态字位定义

| 位 | 名称 | 说明 |
|----|------|------|
| 0 | Ready to switch on | 准备就绪 |
| 1 | Switched on | 已上电 |
| 2 | Operation enabled | 运行使能 |
| 3 | Fault | 故障 |
| 4 | Voltage enabled | 电压使能 |
| 5 | Quick stop | 快速停止 (低有效) |
| 6 | Switch on disabled | 禁止上电 |
| 7 | Warning | 警告 |
| 10 | Target reached | 目标到达 |
| 12 | Set-point ack | 设定点确认 |
| 13 | Following error | 跟随误差 |

### C. 控制字命令

| 命令 | 值 | 目标状态 |
|------|-----|----------|
| Shutdown | 0x0006 | Ready to Switch On |
| Switch On | 0x0007 | Switched On |
| Enable Operation | 0x000F | Operation Enabled |
| Disable Voltage | 0x0000 | Switch On Disabled |
| Quick Stop | 0x0002 | Quick Stop Active |
| Fault Reset | 0x0080 | (上升沿触发) |

---

*文档结束*
