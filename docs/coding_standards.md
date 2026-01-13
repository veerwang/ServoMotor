# 编码规则文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | NiMotion 伺服电机控制系统 |
| 文档版本 | 1.0 |
| 创建日期 | 2026-01-09 |

---

## 目录

1. [通用规范](#1-通用规范)
2. [命名规范](#2-命名规范)
3. [代码格式](#3-代码格式)
4. [注释规范](#4-注释规范)
5. [文档字符串](#5-文档字符串)
6. [类型注解](#6-类型注解)
7. [异常处理](#7-异常处理)
8. [日志规范](#8-日志规范)
9. [测试规范](#9-测试规范)
10. [Git 提交规范](#10-git-提交规范)
11. [PyQt5 规范](#11-pyqt5-规范)
12. [代码审查清单](#12-代码审查清单)

---

## 1. 通用规范

### 1.1 Python 版本

- 项目使用 **Python 3.9+**
- 充分利用新版本特性（类型注解、dataclass、walrus operator 等）

### 1.2 代码风格

- 遵循 **PEP 8** 代码风格指南
- 使用 **Black** 进行代码格式化
- 使用 **isort** 进行 import 排序
- 使用 **flake8** 进行代码检查
- 使用 **mypy** 进行类型检查

### 1.3 工具配置

```toml
# pyproject.toml

[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.git
    | \.venv
    | build
    | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["servo_service", "app"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.flake8]
max-line-length = 100
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist", ".venv"]
```

### 1.4 行长度

- 最大行长度: **100 字符**
- 文档字符串和注释: **80 字符**（建议）

---

## 2. 命名规范

### 2.1 总体原则

- 名称应清晰、准确、有意义
- 避免使用缩写，除非是广泛认可的缩写
- 使用英文命名，不使用拼音

### 2.2 命名风格

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块 | snake_case | `serial_port.py`, `motor_control.py` |
| 包 | snake_case | `servo_service`, `high_level_api` |
| 类 | PascalCase | `SerialPort`, `MotorController` |
| 异常类 | PascalCase + Error | `SerialPortError`, `ModbusTimeoutError` |
| 函数/方法 | snake_case | `read_register()`, `get_status()` |
| 变量 | snake_case | `slave_id`, `target_position` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有成员 | _前缀 | `_port`, `_is_connected` |
| 受保护成员 | _前缀 | `_parse_frame()` |
| 名称混淆 | __前缀 | `__internal_state` (极少使用) |
| 类型变量 | PascalCase | `T`, `ResponseType` |
| 枚举成员 | UPPER_SNAKE_CASE | `Axis.X`, `OperationMode.HOMING` |

### 2.3 具体命名规则

#### 2.3.1 类命名

```python
# Good
class SerialPort:
    pass

class ModbusClient:
    pass

class MotorController:
    pass

class AxisConfig:
    pass

# Bad
class serialport:  # 应使用 PascalCase
    pass

class Modbus_Client:  # 不应使用下划线
    pass
```

#### 2.3.2 函数/方法命名

```python
# Good - 使用动词开头
def read_register(address: int) -> int:
    pass

def write_control_word(value: int) -> bool:
    pass

def is_connected() -> bool:  # 布尔返回值使用 is_/has_/can_
    pass

def has_brake() -> bool:
    pass

def get_current_position() -> int:  # 获取属性使用 get_
    pass

def set_target_velocity(velocity: int) -> None:  # 设置属性使用 set_
    pass

# Bad
def register_read():  # 动词应在前面
    pass

def position():  # 不清楚是获取还是设置
    pass
```

#### 2.3.3 变量命名

```python
# Good
slave_id = 1
target_position = 10000
max_velocity = 1000
is_enabled = True
fault_code = 0x2300
axis_config = AxisConfig(...)

# Bad
id = 1           # 避免使用内置名称
pos = 10000      # 避免过度缩写
maxV = 1000      # 不使用驼峰式
flag = True      # 意义不明确
```

#### 2.3.4 常量命名

```python
# Good
MAX_RETRIES = 3
DEFAULT_BAUDRATE = 115200
CONTROL_WORD_ADDRESS = 0x0380
STATUS_WORD_ADDRESS = 0x0381

# 寄存器地址常量
class Registers:
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    TARGET_POSITION = 0x03C5

# 协议相关常量
class ModbusFunctionCode:
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_REGISTERS = 0x10
```

#### 2.3.5 私有成员命名

```python
class Motor:
    def __init__(self):
        # 私有属性
        self._controller = None
        self._axis_config = None
        self._is_enabled = False

        # 缓存/内部状态
        self._status_cache = {}
        self._last_update_time = 0.0

    # 私有方法
    def _validate_position(self, position: int) -> bool:
        pass

    def _send_command(self, command: int) -> bool:
        pass
```

### 2.4 特殊命名

```python
# 迭代变量
for i, item in enumerate(items):
    pass

for axis in [Axis.X, Axis.Y, Axis.Z]:
    pass

# 临时变量
_, result = some_function()  # 忽略不需要的返回值

# 上下文管理器
with open(file_path) as f:
    pass

# 异常变量
try:
    pass
except SomeError as e:
    logger.error(f"Error: {e}")
```

---

## 3. 代码格式

### 3.1 导入顺序

```python
# 1. 标准库导入
import os
import sys
import time
import logging
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple, Callable

# 2. 第三方库导入
import serial
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

# 3. 本地应用导入
from servo_service.serial_comm import SerialPort
from servo_service.modbus_rtu import ModbusClient
from servo_service.high_level_api import Motor, Axis

# 4. 相对导入 (同一包内)
from .exceptions import MotorError
from .constants import Registers
```

### 3.2 空行规则

```python
# 模块级别: 顶层定义之间使用两个空行
import os


CONSTANT_VALUE = 100


class FirstClass:
    pass


class SecondClass:
    pass


def top_level_function():
    pass


# 类内部: 方法之间使用一个空行
class Motor:
    """电机控制类"""

    def __init__(self):
        self._enabled = False

    def enable(self) -> bool:
        """使能电机"""
        pass

    def disable(self) -> bool:
        """去使能电机"""
        pass


# 函数内部: 逻辑块之间使用空行分隔
def complex_function():
    # 初始化
    result = []
    counter = 0

    # 处理逻辑
    for item in items:
        processed = process(item)
        result.append(processed)
        counter += 1

    # 返回结果
    return result
```

### 3.3 缩进

- 使用 **4 个空格** 进行缩进
- 不使用 Tab 字符

```python
# Good
def function():
    if condition:
        do_something()
        if another_condition:
            do_another_thing()

# 多行参数
result = some_function(
    first_argument,
    second_argument,
    third_argument,
)

# 多行条件
if (condition_one
        and condition_two
        and condition_three):
    do_something()

# 多行列表/字典
config = {
    'baudrate': 115200,
    'timeout': 0.1,
    'retries': 3,
}
```

### 3.4 空格使用

```python
# Good
x = 1
result = function(arg1, arg2)
my_list = [1, 2, 3]
my_dict = {'key': 'value'}

if x == 1:
    pass

def function(arg1: int, arg2: str = 'default') -> bool:
    pass

# Bad
x=1                              # 赋值符号两边需要空格
result = function( arg1, arg2 )  # 括号内不需要空格
my_list = [ 1, 2, 3 ]            # 括号内不需要空格
my_dict = { 'key' : 'value' }    # 冒号前不需要空格

def function(arg1 : int):        # 类型注解冒号前不需要空格
    pass
```

### 3.5 字符串格式化

```python
# 推荐: f-string (Python 3.6+)
name = "Motor"
position = 12345
message = f"当前 {name} 位置: {position}"

# 调试信息
logger.debug(f"Reading register 0x{address:04X}, count={count}")

# 多行 f-string
error_message = (
    f"通信错误: 从站 {slave_id}, "
    f"功能码 0x{function_code:02X}, "
    f"超时 {timeout}s"
)

# 复杂表达式使用变量
velocity_mm = velocity * lead / encoder_resolution
message = f"速度: {velocity_mm:.2f} mm/s"

# 不推荐: % 格式化 (旧式)
message = "位置: %d" % position

# 不推荐: str.format() (除非必要)
message = "位置: {}".format(position)
```

---

## 4. 注释规范

### 4.1 注释原则

- 注释应解释 **为什么 (Why)**，而非 **是什么 (What)**
- 代码应该自解释，避免冗余注释
- 保持注释与代码同步更新
- 使用中文注释（本项目约定）

### 4.2 行内注释

```python
# Good
x = x + 1  # 补偿边界条件
timeout = 0.1  # 单位: 秒

# 计算 CRC-16 校验值 (Modbus RTU 标准)
crc = calculate_crc(data)

# Bad
x = x + 1  # x 加 1 (冗余注释)
i += 1  # 增加计数器 (显而易见)
```

### 4.3 块注释

```python
# Good: 解释复杂逻辑
# 状态机转换需要按特定顺序执行:
# 1. 先发送 Shutdown 命令进入 Ready to Switch On 状态
# 2. 再发送 Switch On 命令进入 Switched On 状态
# 3. 最后发送 Enable Operation 命令进入 Operation Enabled 状态
# 每次转换后需要等待状态确认
self._execute_state_transition()

# 解释业务规则
# Z 轴配有抱闸，使能前需要先释放抱闸
# 去使能后需要自动锁定抱闸以防止滑落
if self._axis_config.has_brake:
    self._release_brake()
```

### 4.4 TODO 注释

```python
# TODO: 实现自动重连机制
# TODO(author): 添加超时参数配置
# FIXME: 高并发时可能存在竞态条件
# HACK: 临时解决方案，等待上游库修复
# NOTE: 此处性能关键，避免频繁分配内存
# XXX: 需要重构此部分代码
```

### 4.5 禁用检查注释

```python
# 类型检查禁用 (谨慎使用)
value = some_dynamic_value  # type: ignore

# flake8 禁用
from module import *  # noqa: F401

# 格式化禁用
# fmt: off
matrix = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
]
# fmt: on
```

---

## 5. 文档字符串

### 5.1 风格

采用 **Google 风格** 文档字符串。

### 5.2 模块文档

```python
"""
串口通信模块

本模块提供串口通信的基础功能，包括:
- 串口设备枚举和扫描
- 串口打开/关闭
- 数据收发
- 超时和错误处理

Example:
    基本使用示例::

        from servo_service.serial_comm import SerialPort

        port = SerialPort('/dev/ttyUSB0', 115200)
        port.open()
        port.write(b'\\x01\\x03\\x00\\x00\\x00\\x01')
        response = port.read(7)
        port.close()

Note:
    所有串口操作都是线程安全的。

Attributes:
    DEFAULT_BAUDRATE (int): 默认波特率 115200
    DEFAULT_TIMEOUT (float): 默认超时时间 0.1 秒
"""

import serial
from typing import List, Optional

DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 0.1
```

### 5.3 类文档

```python
class SerialPort:
    """
    串口通信类

    封装 pyserial 库，提供线程安全的串口操作。

    Attributes:
        port_name (str): 串口名称
        baudrate (int): 波特率
        timeout (float): 读取超时时间（秒）
        is_open (bool): 串口是否打开

    Example:
        创建并使用串口::

            port = SerialPort('/dev/ttyUSB0', 115200)
            try:
                port.open()
                port.write(data)
                response = port.read(10)
            finally:
                port.close()

        使用上下文管理器::

            with SerialPort('/dev/ttyUSB0') as port:
                port.write(data)
                response = port.read(10)

    Note:
        多线程环境下，所有读写操作都会自动加锁。
    """

    def __init__(self, port_name: str, baudrate: int = 115200,
                 timeout: float = 0.1):
        """
        初始化串口实例

        Args:
            port_name: 串口名称，如 '/dev/ttyUSB0' 或 'COM3'
            baudrate: 波特率，默认 115200
            timeout: 读取超时时间（秒），默认 0.1

        Raises:
            ValueError: 如果波特率不在支持范围内
        """
        pass
```

### 5.4 函数/方法文档

```python
def read_holding_registers(
    self,
    slave_id: int,
    address: int,
    count: int,
    timeout: float = None
) -> List[int]:
    """
    读取保持寄存器

    使用 Modbus 功能码 0x03 读取指定从站的保持寄存器。

    Args:
        slave_id: 从站地址，范围 1-247
        address: 起始寄存器地址
        count: 读取的寄存器数量，范围 1-125
        timeout: 超时时间（秒），None 表示使用默认值

    Returns:
        读取到的寄存器值列表，每个元素为 16 位无符号整数

    Raises:
        ModbusTimeoutError: 通信超时
        ModbusCRCError: CRC 校验失败
        ModbusExceptionError: 从站返回异常响应
        ValueError: 参数超出有效范围

    Example:
        读取控制字和状态字::

            values = client.read_holding_registers(1, 0x0380, 2)
            control_word = values[0]
            status_word = values[1]

    Note:
        单次最多读取 125 个寄存器。如需读取更多，请分多次读取。

    See Also:
        write_single_register: 写单个寄存器
        write_multiple_registers: 写多个寄存器
    """
    pass


def enable(self) -> bool:
    """
    使能电机

    自动执行 CiA402 状态机转换，将电机从任意状态转换到
    Operation Enabled 状态。如果电机有故障，会先尝试故障复位。
    如果是 Z 轴（配有抱闸），会先释放抱闸。

    Returns:
        使能成功返回 True，失败返回 False

    Raises:
        MotorFaultError: 故障复位失败
        CommunicationError: 通信错误

    Example:
        基本使能::

            motor = service.get_motor_by_axis(Axis.Z)
            if motor.enable():
                print("电机使能成功")
            else:
                print("电机使能失败")

    Warning:
        使能前请确保电机和负载处于安全状态。
    """
    pass
```

### 5.5 属性文档

```python
class AxisConfig:
    """轴配置类"""

    @property
    def max_velocity(self) -> float:
        """
        最大速度 (mm/s)

        返回该轴允许的最大运行速度。设置目标速度时不应超过此值。

        Returns:
            最大速度值，单位 mm/s

        Example:
            >>> config = AXIS_CONFIGS[Axis.Z]
            >>> print(f"Z轴最大速度: {config.max_velocity} mm/s")
            Z轴最大速度: 500.0 mm/s
        """
        return self._max_velocity

    @property
    def stroke_range(self) -> Tuple[float, float]:
        """
        行程范围 (mm)

        Returns:
            元组 (最小位置, 最大位置)，单位 mm
        """
        return (self._stroke_min, self._stroke_max)
```

---

## 6. 类型注解

### 6.1 基本类型注解

```python
from typing import (
    Dict, List, Tuple, Set,
    Optional, Union,
    Callable, Awaitable,
    TypeVar, Generic,
    Any, Final
)


# 基本类型
name: str = "Motor"
count: int = 10
value: float = 3.14
is_enabled: bool = True

# 可选类型 (可能为 None)
result: Optional[int] = None
config: Optional[AxisConfig] = None

# 联合类型
value: Union[int, float] = 10
identifier: Union[str, int] = "motor_1"

# 容器类型
values: List[int] = [1, 2, 3]
mapping: Dict[str, int] = {'a': 1, 'b': 2}
coordinates: Tuple[float, float, float] = (1.0, 2.0, 3.0)
unique_ids: Set[int] = {1, 2, 3}

# 可调用类型
callback: Callable[[int], None] = lambda x: print(x)
handler: Callable[[str, int], bool] = some_function

# Final (常量)
MAX_RETRIES: Final[int] = 3
DEFAULT_TIMEOUT: Final[float] = 0.1
```

### 6.2 函数类型注解

```python
def simple_function(x: int, y: int) -> int:
    return x + y


def function_with_default(
    name: str,
    count: int = 10,
    timeout: Optional[float] = None
) -> bool:
    pass


def function_returning_none(message: str) -> None:
    print(message)


def function_with_callback(
    data: bytes,
    on_success: Callable[[bytes], None],
    on_error: Callable[[Exception], None]
) -> None:
    pass


# 生成器函数
def generate_values(start: int, end: int) -> Iterator[int]:
    for i in range(start, end):
        yield i


# 异步函数
async def async_read(address: int) -> int:
    pass
```

### 6.3 类类型注解

```python
from __future__ import annotations  # 支持前向引用
from dataclasses import dataclass
from typing import ClassVar, Self


class Motor:
    # 类变量
    instances: ClassVar[Dict[int, Motor]] = {}

    def __init__(self, slave_id: int) -> None:
        self._slave_id: int = slave_id
        self._controller: Optional[MotorController] = None

    def clone(self) -> Self:
        """返回自身类型的实例"""
        return type(self)(self._slave_id)

    @classmethod
    def create(cls, slave_id: int) -> Motor:
        """工厂方法"""
        return cls(slave_id)


@dataclass
class MotorStatus:
    """电机状态数据类"""
    enabled: bool
    position: float
    velocity: float
    fault_code: int = 0
```

### 6.4 泛型类型

```python
from typing import TypeVar, Generic

T = TypeVar('T')
ResponseT = TypeVar('ResponseT', bound='Response')


class Cache(Generic[T]):
    """泛型缓存类"""

    def __init__(self) -> None:
        self._data: Dict[str, T] = {}

    def get(self, key: str) -> Optional[T]:
        return self._data.get(key)

    def set(self, key: str, value: T) -> None:
        self._data[key] = value


# 使用
status_cache: Cache[MotorStatus] = Cache()
config_cache: Cache[AxisConfig] = Cache()
```

### 6.5 类型别名

```python
from typing import TypeAlias

# 简单别名
SlaveId: TypeAlias = int
RegisterAddress: TypeAlias = int
RegisterValue: TypeAlias = int

# 复杂别名
RegisterMap: TypeAlias = Dict[RegisterAddress, RegisterValue]
Callback: TypeAlias = Callable[[MotorStatus], None]
AxisMotorMap: TypeAlias = Dict[Axis, Motor]

# 使用
def read_registers(
    slave_id: SlaveId,
    addresses: List[RegisterAddress]
) -> RegisterMap:
    pass
```

---

## 7. 异常处理

### 7.1 异常处理原则

- 只捕获你能处理的异常
- 避免裸 `except:` 语句
- 使用具体的异常类型
- 记录异常信息
- 适当重新抛出异常

### 7.2 异常处理模式

```python
# Good: 捕获具体异常
try:
    result = client.read_holding_registers(1, 0x0380, 1)
except ModbusTimeoutError:
    logger.warning("通信超时，重试中...")
    result = client.read_holding_registers(1, 0x0380, 1)
except ModbusCRCError as e:
    logger.error(f"CRC 校验失败: {e}")
    raise


# Good: 多个异常类型
try:
    port.open()
    port.write(data)
except FileNotFoundError:
    logger.error(f"串口 {port_name} 不存在")
    raise SerialPortError(f"Port not found: {port_name}")
except PermissionError:
    logger.error(f"无权限访问串口 {port_name}")
    raise SerialPortError(f"Permission denied: {port_name}")
except serial.SerialException as e:
    logger.error(f"串口错误: {e}")
    raise SerialPortError(str(e))


# Good: finally 确保资源释放
port = None
try:
    port = SerialPort(port_name)
    port.open()
    return port.read(size)
finally:
    if port is not None:
        port.close()


# Good: 上下文管理器
with SerialPort(port_name) as port:
    return port.read(size)


# Bad: 裸 except
try:
    do_something()
except:  # 捕获所有异常，包括 KeyboardInterrupt
    pass


# Bad: 过于宽泛的异常
try:
    do_something()
except Exception:  # 应该更具体
    pass
```

### 7.3 自定义异常

```python
class ServoMotorError(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = time.time()

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.args[0]}"
        return self.args[0]


class MotorFaultError(ServoMotorError):
    """电机故障异常"""

    def __init__(self, fault_code: int, axis: Optional[Axis] = None):
        fault_info = get_fault_info(fault_code)
        super().__init__(
            message=f"{fault_info.name}: {fault_info.description}",
            code=fault_code,
            details={'axis': axis, 'fault_info': fault_info}
        )
        self.fault_info = fault_info
```

### 7.4 异常链

```python
# 保留原始异常信息
try:
    result = low_level_operation()
except LowLevelError as e:
    raise HighLevelError("操作失败") from e


# 明确抑制原始异常
try:
    cleanup()
except CleanupError:
    raise OperationError("清理失败") from None
```

---

## 8. 日志规范

### 8.1 日志配置

```python
import logging
import logging.handlers
from pathlib import Path


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """配置日志系统"""

    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # 文件处理器 (轮转)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/servo_motor.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

### 8.2 日志使用

```python
import logging

# 获取模块日志器
logger = logging.getLogger(__name__)


class MotorController:
    def __init__(self, slave_id: int):
        self._slave_id = slave_id
        self._logger = logging.getLogger(f"{__name__}.Motor{slave_id}")

    def enable(self) -> bool:
        self._logger.info("开始使能电机")

        try:
            # 操作...
            self._logger.debug(f"写入控制字: 0x{control_word:04X}")

            if success:
                self._logger.info("电机使能成功")
                return True
            else:
                self._logger.warning("电机使能失败，状态异常")
                return False

        except CommunicationError as e:
            self._logger.error(f"通信错误: {e}")
            raise
        except Exception as e:
            self._logger.exception("未预期的错误")  # 自动记录堆栈
            raise
```

### 8.3 日志级别使用

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| DEBUG | 详细调试信息 | 寄存器读写值、帧内容 |
| INFO | 正常操作记录 | 连接成功、使能完成 |
| WARNING | 异常但可恢复 | 通信超时重试、参数越界修正 |
| ERROR | 错误但程序继续 | 命令执行失败、故障发生 |
| CRITICAL | 严重错误 | 系统无法继续运行 |

```python
# DEBUG - 调试详情
logger.debug(f"发送帧: {frame.hex(' ')}")
logger.debug(f"接收帧: {response.hex(' ')}")
logger.debug(f"读取寄存器 0x{address:04X} = 0x{value:04X}")

# INFO - 操作记录
logger.info(f"连接到 {port_name}, 波特率 {baudrate}")
logger.info(f"电机 {slave_id} 使能成功")
logger.info(f"开始回零，方式: {homing_method}")

# WARNING - 警告
logger.warning(f"通信超时，第 {retry}/{max_retries} 次重试")
logger.warning(f"速度 {velocity} 超过最大值，已限制为 {max_velocity}")

# ERROR - 错误
logger.error(f"故障发生: 0x{fault_code:04X} - {fault_name}")
logger.error(f"使能失败，当前状态: {state}")

# CRITICAL - 严重
logger.critical("紧急停止触发")
logger.critical("硬件限位触发，停止所有运动")
```

---

## 9. 测试规范

### 9.1 测试结构

```
tests/
├── __init__.py
├── conftest.py                 # pytest 配置和 fixtures
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_serial_port.py
│   ├── test_modbus_client.py
│   ├── test_motor_controller.py
│   └── test_state_machine.py
├── integration/                # 集成测试
│   ├── __init__.py
│   ├── test_servo_service.py
│   └── test_motor_operations.py
└── fixtures/                   # 测试数据
    ├── modbus_frames.py
    └── motor_responses.py
```

### 9.2 测试命名

```python
# 测试文件: test_<模块名>.py
# test_serial_port.py
# test_motor_controller.py

# 测试类: Test<被测试类名>
class TestSerialPort:
    pass

class TestMotorController:
    pass

# 测试方法: test_<方法名>_<场景>_<期望结果>
class TestMotorController:
    def test_enable_when_not_connected_raises_error(self):
        pass

    def test_enable_when_fault_resets_and_enables(self):
        pass

    def test_read_position_returns_correct_value(self):
        pass
```

### 9.3 测试编写

```python
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestModbusClient:
    """Modbus 客户端测试"""

    @pytest.fixture
    def mock_serial(self):
        """模拟串口"""
        serial = Mock()
        serial.is_open = True
        return serial

    @pytest.fixture
    def client(self, mock_serial):
        """创建测试客户端"""
        return ModbusClient(mock_serial)

    def test_read_holding_registers_success(self, client, mock_serial):
        """测试成功读取保持寄存器"""
        # Arrange
        mock_serial.read.return_value = bytes([
            0x01, 0x03, 0x02, 0x00, 0x27, 0xF9, 0xB4
        ])

        # Act
        result = client.read_holding_registers(1, 0x0380, 1)

        # Assert
        assert result == [0x0027]
        mock_serial.write.assert_called_once()

    def test_read_holding_registers_timeout(self, client, mock_serial):
        """测试读取超时"""
        # Arrange
        mock_serial.read.return_value = b''

        # Act & Assert
        with pytest.raises(ModbusTimeoutError):
            client.read_holding_registers(1, 0x0380, 1)

    def test_read_holding_registers_crc_error(self, client, mock_serial):
        """测试 CRC 错误"""
        # Arrange - 错误的 CRC
        mock_serial.read.return_value = bytes([
            0x01, 0x03, 0x02, 0x00, 0x27, 0xFF, 0xFF
        ])

        # Act & Assert
        with pytest.raises(ModbusCRCError):
            client.read_holding_registers(1, 0x0380, 1)

    @pytest.mark.parametrize("slave_id,address,count", [
        (0, 0x0380, 1),     # 无效从站地址
        (248, 0x0380, 1),   # 无效从站地址
        (1, 0x0380, 0),     # 无效数量
        (1, 0x0380, 126),   # 数量超限
    ])
    def test_read_holding_registers_invalid_params(
        self, client, slave_id, address, count
    ):
        """测试无效参数"""
        with pytest.raises(ValueError):
            client.read_holding_registers(slave_id, address, count)
```

### 9.4 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=servo_service --cov-report=html tests/

# 要求最小覆盖率
pytest --cov=servo_service --cov-fail-under=80 tests/
```

---

## 10. Git 提交规范

### 10.1 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 10.2 类型 (type)

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(motor): 添加多轴控制支持 |
| fix | 修复 bug | fix(modbus): 修复 CRC 计算错误 |
| docs | 文档更新 | docs: 更新 API 文档 |
| style | 代码格式 | style: 格式化代码 |
| refactor | 重构 | refactor(serial): 重构串口类 |
| test | 测试 | test: 添加状态机测试 |
| chore | 构建/工具 | chore: 更新依赖版本 |
| perf | 性能优化 | perf: 优化通信响应时间 |

### 10.3 范围 (scope)

- `serial` - 串口通信层
- `modbus` - Modbus 协议层
- `motor` - 电机控制层
- `api` - 高级 API 层
- `ui` - 界面层
- `config` - 配置相关
- `docs` - 文档相关

### 10.4 示例

```
feat(motor): 添加 Z 轴抱闸控制功能

- 新增 release_brake() 和 engage_brake() 方法
- 使能时自动释放抱闸
- 去使能时自动锁定抱闸
- 添加抱闸状态检测

Closes #123
```

```
fix(modbus): 修复多寄存器写入时的字节序问题

写入多个寄存器时，数据字节序不正确导致值错误。
现在正确使用大端序（MSB first）。

Fixes #456
```

### 10.5 分支命名

```
main                    # 主分支
develop                 # 开发分支
feature/multi-axis      # 功能分支
bugfix/crc-calculation  # 修复分支
release/v1.0.0          # 发布分支
hotfix/critical-bug     # 热修复分支
```

---

## 11. PyQt5 规范

### 11.1 信号和槽命名

```python
class MotorControlView(QWidget):
    """电机控制视图"""

    # 信号命名: <动作>_<对象> 或 <对象>_<状态>
    enable_requested = pyqtSignal()
    axis_changed = pyqtSignal(Axis)
    position_updated = pyqtSignal(float)
    fault_occurred = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        """连接信号和槽"""
        # 槽命名: _on_<信号来源>_<信号名> 或 _handle_<事件>
        self._enable_btn.clicked.connect(self._on_enable_btn_clicked)
        self._axis_selector.axis_changed.connect(self._on_axis_changed)
        self._status_monitor.fault_detected.connect(self._handle_fault)

    def _on_enable_btn_clicked(self):
        """处理使能按钮点击"""
        self.enable_requested.emit()

    def _on_axis_changed(self, axis: Axis):
        """处理轴切换"""
        self._update_axis_info(axis)
        self.axis_changed.emit(axis)

    def _handle_fault(self, fault_code: int):
        """处理故障"""
        self._show_fault_dialog(fault_code)
```

### 11.2 UI 组件组织

```python
class MotorControlView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_style()
        self._connect_signals()

    def _setup_ui(self):
        """设置 UI 组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 创建子组件
        self._create_connection_panel()
        self._create_axis_panel()
        self._create_status_panel()
        self._create_control_panel()

        # 添加到布局
        main_layout.addWidget(self._connection_panel)
        main_layout.addWidget(self._axis_panel)
        main_layout.addWidget(self._status_panel)
        main_layout.addWidget(self._control_panel)
        main_layout.addStretch()

    def _create_connection_panel(self):
        """创建连接配置面板"""
        self._connection_panel = QGroupBox("连接配置")
        layout = QHBoxLayout(self._connection_panel)

        # 串口选择
        layout.addWidget(QLabel("串口:"))
        self._port_combo = QComboBox()
        layout.addWidget(self._port_combo)

        # 波特率
        layout.addWidget(QLabel("波特率:"))
        self._baudrate_combo = QComboBox()
        self._baudrate_combo.addItems(['9600', '115200', '256000'])
        layout.addWidget(self._baudrate_combo)

        # 连接按钮
        self._connect_btn = QPushButton("连接")
        layout.addWidget(self._connect_btn)

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
```

### 11.3 线程安全

```python
class StatusMonitor(QThread):
    """状态监控线程"""

    status_updated = pyqtSignal(MotorStatus)

    def __init__(self, motor: Motor):
        super().__init__()
        self._motor = motor
        self._running = False

    def run(self):
        """线程主函数"""
        self._running = True
        while self._running:
            try:
                status = self._motor.get_status()
                # 通过信号发送数据到主线程
                self.status_updated.emit(status)
            except Exception as e:
                logging.error(f"状态读取错误: {e}")
            time.sleep(0.1)

    def stop(self):
        """停止线程"""
        self._running = False
        self.wait()  # 等待线程结束


class MotorControlView(QWidget):
    def __init__(self, motor: Motor):
        super().__init__()
        self._motor = motor

        # 创建监控线程
        self._monitor = StatusMonitor(motor)
        self._monitor.status_updated.connect(self._update_status)
        self._monitor.start()

    def _update_status(self, status: MotorStatus):
        """在主线程中更新 UI"""
        self._position_label.setText(f"{status.position:.2f}")
        self._velocity_label.setText(f"{status.velocity:.1f}")

    def closeEvent(self, event):
        """窗口关闭时停止线程"""
        self._monitor.stop()
        super().closeEvent(event)
```

---

## 12. 代码审查清单

### 12.1 通用检查

- [ ] 代码符合 PEP 8 规范
- [ ] 所有公共接口都有文档字符串
- [ ] 函数参数和返回值都有类型注解
- [ ] 没有硬编码的魔法数字
- [ ] 错误处理完善
- [ ] 日志记录充分
- [ ] 没有调试代码残留

### 12.2 安全检查

- [ ] 没有敏感信息泄露
- [ ] 输入验证完善
- [ ] 没有 SQL 注入风险
- [ ] 没有命令注入风险

### 12.3 性能检查

- [ ] 没有不必要的循环
- [ ] 避免频繁的小内存分配
- [ ] 使用适当的数据结构
- [ ] 没有阻塞 UI 线程的操作

### 12.4 可维护性检查

- [ ] 函数职责单一
- [ ] 类设计合理
- [ ] 代码重复最小化
- [ ] 命名清晰准确

---

## 附录

### A. 常用缩写

| 缩写 | 全称 | 说明 |
|------|------|------|
| ID | Identifier | 标识符 |
| CRC | Cyclic Redundancy Check | 循环冗余校验 |
| RTU | Remote Terminal Unit | 远程终端单元 |
| DI | Digital Input | 数字输入 |
| DO | Digital Output | 数字输出 |
| PP | Profile Position | 轮廓位置模式 |
| PV | Profile Velocity | 轮廓速度模式 |
| HM | Homing Mode | 回零模式 |
| CSP | Cyclic Sync Position | 周期同步位置 |
| CSV | Cyclic Sync Velocity | 周期同步速度 |

### B. 参考资料

- [PEP 8 - Python 代码风格指南](https://pep8.org/)
- [PEP 257 - 文档字符串约定](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 - 类型提示](https://www.python.org/dev/peps/pep-0484/)
- [Google Python 风格指南](https://google.github.io/styleguide/pyguide.html)
- [Black 代码格式化工具](https://black.readthedocs.io/)

---

*文档结束*
