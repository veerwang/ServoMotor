# 电机控制系统软件设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | NiMotion 伺服电机控制系统 |
| 文档版本 | 1.0 |
| 创建日期 | 2026-01-09 |
| 基于需求 | requirements.md v1.1 |

---

## 目录

1. [系统架构设计](#1-系统架构设计)
2. [Layer 1: 串口通信层设计](#2-layer-1-串口通信层设计)
3. [Layer 2: Modbus 协议层设计](#3-layer-2-modbus-协议层设计)
4. [Layer 3: 电机控制层设计](#4-layer-3-电机控制层设计)
5. [Layer 4: 高级 API 层设计](#5-layer-4-高级-api-层设计)
6. [Layer 5: 应用层设计](#6-layer-5-应用层设计)
7. [数据结构设计](#7-数据结构设计)
8. [状态机设计](#8-状态机设计)
9. [错误处理设计](#9-错误处理设计)
10. [线程模型设计](#10-线程模型设计)
11. [配置管理设计](#11-配置管理设计)

---

## 1. 系统架构设计

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Layer 5: 应用层                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              MainWindow                                      ││
│  │  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐    ││
│  │  │  MotorControlView   │ │   ModbusDebugView   │ │  RegisterConfigView │    ││
│  │  │ ┌───────┐ ┌───────┐ │ │ ┌───────┐ ┌───────┐ │ │ ┌─────────────────┐ │    ││
│  │  │ │AxisSel│ │Status │ │ │ │Send   │ │Log    │ │ │ │ RegisterTables  │ │    ││
│  │  │ ├───────┤ ├───────┤ │ │ ├───────┤ ├───────┤ │ │ │ (6 categories)  │ │    ││
│  │  │ │JogPnl │ │Param  │ │ │ │Quick  │ │Stats  │ │ │ ├─────────────────┤ │    ││
│  │  │ ├───────┤ ├───────┤ │ │ └───────┘ └───────┘ │ │ │ Read/Write/Save │ │    ││
│  │  │ │Plot   │ │Homing │ │ │                     │ │ └─────────────────┘ │    ││
│  │  │ └───────┘ └───────┘ │ │                     │ │                     │    ││
│  │  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌─────────────────────────────────────────────────────────────────────────┐  │
│    │                         ServoService (服务模块)                          │  │
│    │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│    │  │                    Layer 4: 高级 API 层                            │  │  │
│    │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │  │  │
│    │  │  │  Motor  │ │ Motion  │ │ Homing  │ │  Limits │ │ AxisConfig  │  │  │  │
│    │  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──────┬──────┘  │  │  │
│    │  └───────┼───────────┼───────────┼───────────┼─────────────┼─────────┘  │  │
│    │  ┌───────┴───────────┴───────────┴───────────┴─────────────┴─────────┐  │  │
│    │  │                    Layer 3: 电机控制层                             │  │  │
│    │  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────────┐│  │  │
│    │  │  │MotorController│ │ StateMachine  │ │      Registers            ││  │  │
│    │  │  └───────┬───────┘ └───────┬───────┘ └─────────────┬─────────────┘│  │  │
│    │  └──────────┼─────────────────┼───────────────────────┼──────────────┘  │  │
│    │  ┌──────────┴─────────────────┴───────────────────────┴──────────────┐  │  │
│    │  │                    Layer 2: Modbus 协议层                          │  │  │
│    │  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────────┐│  │  │
│    │  │  │ ModbusClient  │ │ FrameBuilder  │ │      FrameParser          ││  │  │
│    │  │  └───────┬───────┘ └───────────────┘ └───────────────────────────┘│  │  │
│    │  └──────────┼────────────────────────────────────────────────────────┘  │  │
│    │  ┌──────────┴────────────────────────────────────────────────────────┐  │  │
│    │  │                    Layer 1: 串口通信层                             │  │  │
│    │  │  ┌───────────────┐ ┌───────────────┐                              │  │  │
│    │  │  │  SerialPort   │ │  PortScanner  │                              │  │  │
│    │  │  └───────────────┘ └───────────────┘                              │  │  │
│    │  └───────────────────────────────────────────────────────────────────┘  │  │
│    └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │   USB-to-Serial   │
                              │     RS-485        │
                              └─────────┬─────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              ┌───────────┐       ┌───────────┐       ┌───────────┐
              │  X 轴     │       │  Y 轴     │       │  Z 轴     │
              │ Slave: 1  │       │ Slave: 2  │       │ Slave: 3  │
              │ CFG8/200W │       │ CFG5/100W │       │ CFG4/100W │
              └───────────┘       └───────────┘       └───────────┘
```

### 1.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                          app (Layer 5)                          │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ServoService                          │   │
│  │  ┌─────────────────────────────────────────────────────┐│   │
│  │  │              high_level_api (Layer 4)               ││   │
│  │  │                        │                            ││   │
│  │  │                        ▼                            ││   │
│  │  │  ┌─────────────────────────────────────────────┐   ││   │
│  │  │  │           motor_control (Layer 3)           │   ││   │
│  │  │  │                     │                       │   ││   │
│  │  │  │                     ▼                       │   ││   │
│  │  │  │  ┌─────────────────────────────────────┐   │   ││   │
│  │  │  │  │         modbus_rtu (Layer 2)        │   │   ││   │
│  │  │  │  │                  │                  │   │   ││   │
│  │  │  │  │                  ▼                  │   │   ││   │
│  │  │  │  │  ┌─────────────────────────────┐   │   │   ││   │
│  │  │  │  │  │    serial_comm (Layer 1)    │   │   │   ││   │
│  │  │  │  │  └─────────────────────────────┘   │   │   ││   │
│  │  │  │  └─────────────────────────────────────┘   │   ││   │
│  │  │  └─────────────────────────────────────────────┘   ││   │
│  │  └─────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 数据流图

```
┌─────────────┐     用户操作      ┌─────────────┐
│   用户界面   │ ───────────────▶ │   应用层    │
│  (Layer 5)  │ ◀─────────────── │  (Layer 5)  │
└─────────────┘     状态更新      └──────┬──────┘
                                         │
                                   API 调用
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  高级 API    │
                                  │  (Layer 4)   │
                                  └──────┬───────┘
                                         │
                                   寄存器操作
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  电机控制    │
                                  │  (Layer 3)   │
                                  └──────┬───────┘
                                         │
                                  Modbus 请求
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  Modbus 协议 │
                                  │  (Layer 2)   │
                                  └──────┬───────┘
                                         │
                                   串口数据
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  串口通信    │
                                  │  (Layer 1)   │
                                  └──────┬───────┘
                                         │
                                    RS-485
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  伺服驱动器  │
                                  │  (X/Y/Z轴)  │
                                  └──────────────┘
```

---

## 2. Layer 1: 串口通信层设计

### 2.1 模块结构

```
serial_comm/
├── __init__.py
├── serial_port.py      # 串口操作类
├── port_scanner.py     # 端口扫描类
└── exceptions.py       # 异常定义
```

### 2.2 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                         SerialPort                               │
├─────────────────────────────────────────────────────────────────┤
│ - _port: serial.Serial                                          │
│ - _port_name: str                                                │
│ - _baudrate: int                                                 │
│ - _timeout: float                                                │
│ - _is_open: bool                                                 │
│ - _lock: threading.Lock                                          │
│ - _read_buffer: bytes                                            │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(port_name: str, baudrate: int, timeout: float)       │
│ + open() -> bool                                                 │
│ + close() -> None                                                │
│ + is_open() -> bool                                              │
│ + write(data: bytes) -> int                                      │
│ + read(size: int) -> bytes                                       │
│ + read_until(terminator: bytes, timeout: float) -> bytes        │
│ + flush() -> None                                                │
│ + set_baudrate(baudrate: int) -> None                           │
│ + set_timeout(timeout: float) -> None                           │
│ + get_port_info() -> PortInfo                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PortScanner                              │
├─────────────────────────────────────────────────────────────────┤
│ + scan_ports() -> List[PortInfo]                                │
│ + get_available_ports() -> List[str]                            │
│ + is_port_available(port_name: str) -> bool                     │
│ + get_port_description(port_name: str) -> str                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          PortInfo                                │
├─────────────────────────────────────────────────────────────────┤
│ + device: str                                                    │
│ + description: str                                               │
│ + hwid: str                                                      │
│ + vid: int                                                       │
│ + pid: int                                                       │
│ + serial_number: str                                             │
│ + manufacturer: str                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 SerialPort 详细设计

```python
class SerialPort:
    """
    串口通信类

    特性:
    - 线程安全的读写操作
    - 自动重连机制
    - 超时处理
    - 缓冲区管理
    """

    # 默认配置
    DEFAULT_BAUDRATE = 115200
    DEFAULT_TIMEOUT = 0.1  # 100ms
    DEFAULT_BYTESIZE = serial.EIGHTBITS
    DEFAULT_PARITY = serial.PARITY_NONE
    DEFAULT_STOPBITS = serial.STOPBITS_ONE

    def __init__(self, port_name: str = None,
                 baudrate: int = DEFAULT_BAUDRATE,
                 timeout: float = DEFAULT_TIMEOUT):
        """
        初始化串口

        Args:
            port_name: 串口名称 (如 '/dev/ttyUSB0', 'COM3')
            baudrate: 波特率
            timeout: 读取超时时间 (秒)
        """
        self._port_name = port_name
        self._baudrate = baudrate
        self._timeout = timeout
        self._port: Optional[serial.Serial] = None
        self._is_open = False
        self._lock = threading.RLock()

    def open(self) -> bool:
        """
        打开串口

        Returns:
            成功返回 True

        Raises:
            SerialPortError: 打开失败
        """
        with self._lock:
            if self._is_open:
                return True

            try:
                self._port = serial.Serial(
                    port=self._port_name,
                    baudrate=self._baudrate,
                    bytesize=self.DEFAULT_BYTESIZE,
                    parity=self.DEFAULT_PARITY,
                    stopbits=self.DEFAULT_STOPBITS,
                    timeout=self._timeout
                )
                self._is_open = True
                return True
            except serial.SerialException as e:
                raise SerialPortError(f"Failed to open port {self._port_name}: {e}")

    def write(self, data: bytes) -> int:
        """
        写入数据

        Args:
            data: 要发送的字节数据

        Returns:
            实际写入的字节数

        Raises:
            SerialPortError: 写入失败
        """
        with self._lock:
            if not self._is_open:
                raise SerialPortError("Port is not open")
            try:
                return self._port.write(data)
            except serial.SerialException as e:
                raise SerialPortError(f"Write failed: {e}")

    def read(self, size: int, timeout: float = None) -> bytes:
        """
        读取指定长度数据

        Args:
            size: 要读取的字节数
            timeout: 超时时间 (None 使用默认值)

        Returns:
            读取到的数据
        """
        with self._lock:
            if not self._is_open:
                raise SerialPortError("Port is not open")

            if timeout is not None:
                old_timeout = self._port.timeout
                self._port.timeout = timeout

            try:
                data = self._port.read(size)
                return data
            finally:
                if timeout is not None:
                    self._port.timeout = old_timeout
```

### 2.4 通信时序

```
发送请求:
┌─────────┐                              ┌─────────┐
│ 主站    │                              │ 从站    │
│(Master) │                              │(Slave)  │
└────┬────┘                              └────┬────┘
     │                                        │
     │  ──────── 请求帧 (Request) ─────────▶  │
     │  [Addr][Func][Data...][CRC16]         │
     │                                        │
     │         t_response (响应等待)          │
     │                                        │
     │  ◀─────── 响应帧 (Response) ────────   │
     │  [Addr][Func][Data...][CRC16]         │
     │                                        │
     │         t3.5 (帧间隔)                  │
     │                                        │
     │  ──────── 下一请求帧 ──────────────▶   │
     │                                        │

时序要求:
- t3.5: 帧间最小间隔 = 3.5 × 字符时间
- 115200bps 时: t3.5 ≈ 0.3ms
- 响应超时: 默认 100ms
```

---

## 3. Layer 2: Modbus 协议层设计

### 3.1 模块结构

```
modbus_rtu/
├── __init__.py
├── modbus_client.py    # Modbus 客户端
├── frame_builder.py    # 帧构建器
├── frame_parser.py     # 帧解析器
├── crc.py              # CRC 校验
├── exceptions.py       # 异常定义
└── constants.py        # 常量定义
```

### 3.2 类图

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              ModbusClient                                  │
├───────────────────────────────────────────────────────────────────────────┤
│ - _serial: SerialPort                                                      │
│ - _frame_builder: FrameBuilder                                             │
│ - _frame_parser: FrameParser                                               │
│ - _timeout: float                                                          │
│ - _retries: int                                                            │
│ - _transaction_lock: threading.Lock                                        │
│ - _statistics: CommunicationStatistics                                     │
├───────────────────────────────────────────────────────────────────────────┤
│ + __init__(serial_port: SerialPort)                                        │
│ + read_holding_registers(slave_id, address, count) -> List[int]           │
│ + read_input_registers(slave_id, address, count) -> List[int]             │
│ + write_single_register(slave_id, address, value) -> bool                 │
│ + write_multiple_registers(slave_id, address, values) -> bool             │
│ + send_raw_frame(frame: bytes) -> bytes                                   │
│ + get_statistics() -> CommunicationStatistics                             │
│ + reset_statistics() -> None                                               │
│ - _execute_transaction(request: bytes) -> bytes                           │
│ - _wait_for_response(expected_length: int) -> bytes                       │
└───────────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  FrameBuilder   │ │  FrameParser    │ │      CRC        │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ + build_read_   │ │ + parse_response│ │ + calculate()   │
│   holding_regs()│ │ + validate_crc()│ │ + verify()      │
│ + build_write_  │ │ + extract_data()│ │ + crc16_table   │
│   single_reg()  │ │ + get_exception │ └─────────────────┘
│ + build_write_  │ │   _code()       │
│   multi_regs()  │ └─────────────────┘
└─────────────────┘
```

### 3.3 Modbus RTU 帧格式

```
请求帧格式:
┌──────────┬──────────┬──────────────────────┬──────────┐
│ 从站地址 │  功能码  │        数据域         │  CRC16   │
│  1 byte  │  1 byte  │      N bytes         │  2 bytes │
└──────────┴──────────┴──────────────────────┴──────────┘

功能码 0x03 (读保持寄存器):
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│  Addr    │   0x03   │ 起始地址 │ 寄存器数 │   CRC16  │
│  1 byte  │  1 byte  │ 2 bytes  │ 2 bytes  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┴──────────┘

响应帧:
┌──────────┬──────────┬──────────┬──────────────────┬──────────┐
│  Addr    │   0x03   │ 字节数   │     寄存器数据    │   CRC16  │
│  1 byte  │  1 byte  │  1 byte  │     N bytes      │  2 bytes │
└──────────┴──────────┴──────────┴──────────────────┴──────────┘

功能码 0x06 (写单个寄存器):
请求:
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│  Addr    │   0x06   │ 寄存器   │  写入值  │   CRC16  │
│  1 byte  │  1 byte  │ 2 bytes  │ 2 bytes  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┴──────────┘

响应 (原样返回):
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│  Addr    │   0x06   │ 寄存器   │  写入值  │   CRC16  │
│  1 byte  │  1 byte  │ 2 bytes  │ 2 bytes  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┴──────────┘

功能码 0x10 (写多个寄存器):
请求:
┌──────────┬──────────┬──────────┬──────────┬──────────┬───────────┬──────────┐
│  Addr    │   0x10   │ 起始地址 │ 寄存器数 │ 字节数   │ 寄存器数据│   CRC16  │
│  1 byte  │  1 byte  │ 2 bytes  │ 2 bytes  │  1 byte  │  N bytes  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┴──────────┴───────────┴──────────┘

响应:
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│  Addr    │   0x10   │ 起始地址 │ 寄存器数 │   CRC16  │
│  1 byte  │  1 byte  │ 2 bytes  │ 2 bytes  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┴──────────┘

异常响应:
┌──────────┬──────────┬──────────┬──────────┐
│  Addr    │ Func|0x80│ 异常码   │   CRC16  │
│  1 byte  │  1 byte  │  1 byte  │  2 bytes │
└──────────┴──────────┴──────────┴──────────┘
```

### 3.4 CRC-16 计算

```python
class CRC:
    """Modbus RTU CRC-16 计算"""

    # CRC-16 查找表 (预计算)
    CRC_TABLE = [
        0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
        0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
        # ... 完整 256 项表
    ]

    @classmethod
    def calculate(cls, data: bytes) -> int:
        """
        计算 CRC-16

        Args:
            data: 要计算的数据

        Returns:
            CRC-16 值 (低字节在前)
        """
        crc = 0xFFFF
        for byte in data:
            crc = (crc >> 8) ^ cls.CRC_TABLE[(crc ^ byte) & 0xFF]
        return crc

    @classmethod
    def verify(cls, frame: bytes) -> bool:
        """
        验证帧 CRC

        Args:
            frame: 包含 CRC 的完整帧

        Returns:
            CRC 正确返回 True
        """
        if len(frame) < 3:
            return False
        data = frame[:-2]
        received_crc = frame[-2] | (frame[-1] << 8)
        calculated_crc = cls.calculate(data)
        return received_crc == calculated_crc

    @classmethod
    def append(cls, data: bytes) -> bytes:
        """
        追加 CRC 到数据

        Args:
            data: 原始数据

        Returns:
            追加 CRC 后的数据
        """
        crc = cls.calculate(data)
        return data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
```

### 3.5 异常码定义

```python
class ModbusException(IntEnum):
    """Modbus 异常码"""
    ILLEGAL_FUNCTION = 0x01      # 非法功能码
    ILLEGAL_DATA_ADDRESS = 0x02  # 非法数据地址
    ILLEGAL_DATA_VALUE = 0x03    # 非法数据值
    SLAVE_DEVICE_FAILURE = 0x04  # 从站设备故障
    ACKNOWLEDGE = 0x05           # 确认
    SLAVE_DEVICE_BUSY = 0x06     # 从站设备忙
    MEMORY_PARITY_ERROR = 0x08   # 存储器奇偶校验错误
    GATEWAY_PATH_UNAVAILABLE = 0x0A  # 网关路径不可用
    GATEWAY_TARGET_NO_RESP = 0x0B    # 网关目标设备无响应
```

---

## 4. Layer 3: 电机控制层设计

### 4.1 模块结构

```
motor_control/
├── __init__.py
├── motor_controller.py  # 底层电机控制器
├── state_machine.py     # CiA402 状态机
├── registers.py         # 寄存器地址定义
├── constants.py         # 常量定义
└── exceptions.py        # 异常定义
```

### 4.2 类图

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           MotorController                                  │
├───────────────────────────────────────────────────────────────────────────┤
│ - _modbus: ModbusClient                                                    │
│ - _slave_id: int                                                           │
│ - _state_machine: StateMachine                                             │
│ - _current_mode: OperationMode                                             │
│ - _status_cache: MotorStatusCache                                          │
├───────────────────────────────────────────────────────────────────────────┤
│ + __init__(modbus: ModbusClient, slave_id: int)                           │
│ + read_control_word() -> int                                               │
│ + write_control_word(value: int) -> bool                                   │
│ + read_status_word() -> int                                                │
│ + read_operation_mode() -> OperationMode                                   │
│ + set_operation_mode(mode: OperationMode) -> bool                         │
│ + read_position() -> int                                                   │
│ + write_target_position(position: int) -> bool                            │
│ + read_velocity() -> int                                                   │
│ + write_target_velocity(velocity: int) -> bool                            │
│ + read_torque() -> int                                                     │
│ + write_target_torque(torque: int) -> bool                                │
│ + read_fault_code() -> int                                                 │
│ + get_state_machine() -> StateMachine                                      │
└───────────────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                            StateMachine                                    │
├───────────────────────────────────────────────────────────────────────────┤
│ - _controller: MotorController                                             │
│ - _current_state: CiA402State                                              │
│ - _state_handlers: Dict[CiA402State, Callable]                            │
├───────────────────────────────────────────────────────────────────────────┤
│ + get_current_state() -> CiA402State                                       │
│ + update_state() -> CiA402State                                            │
│ + transition_to(target: CiA402State) -> bool                              │
│ + shutdown() -> bool                                                       │
│ + switch_on() -> bool                                                      │
│ + enable_operation() -> bool                                               │
│ + disable_operation() -> bool                                              │
│ + quick_stop() -> bool                                                     │
│ + fault_reset() -> bool                                                    │
│ - _parse_status_word(status: int) -> CiA402State                          │
│ - _get_control_word_for_transition(target: CiA402State) -> int            │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4.3 寄存器地址定义

```python
class Registers:
    """NiMotion 寄存器地址定义"""

    # ==================== 控制相关 ====================
    CONTROL_WORD = 0x0380          # 6040h - 控制字
    STATUS_WORD = 0x0381           # 6041h - 状态字
    OPERATION_MODE = 0x03C3        # 6060h - 运行模式设置
    OPERATION_MODE_DISPLAY = 0x03C2  # 6061h - 运行模式显示

    # ==================== 位置相关 ====================
    TARGET_POSITION = 0x03C5       # 607Ah - 目标位置 (32位)
    POSITION_ACTUAL = 0x03C8       # 6064h - 实际位置 (32位)
    POSITION_WINDOW = 0x03CB       # 6067h - 位置到达窗口
    POSITION_WINDOW_TIME = 0x03CC  # 6068h - 位置到达时间

    # ==================== 速度相关 ====================
    TARGET_VELOCITY = 0x03D2       # 60FFh - 目标速度 (32位)
    VELOCITY_ACTUAL = 0x03D5       # 606Ch - 实际速度 (32位)
    PROFILE_VELOCITY = 0x03CD      # 6081h - 轮廓速度
    MAX_PROFILE_VELOCITY = 0x03CF  # 607Fh - 最大轮廓速度

    # ==================== 加减速相关 ====================
    PROFILE_ACCELERATION = 0x03D0  # 6083h - 轮廓加速度
    PROFILE_DECELERATION = 0x03D1  # 6084h - 轮廓减速度
    QUICK_STOP_DECELERATION = 0x038B  # 6085h - 快速停止减速度

    # ==================== 力矩相关 ====================
    TARGET_TORQUE = 0x03DB         # 6071h - 目标力矩
    TORQUE_ACTUAL = 0x03DC         # 6077h - 实际力矩
    MAX_TORQUE = 0x03E0            # 6072h - 最大力矩

    # ==================== 回零相关 ====================
    HOMING_METHOD = 0x03E3         # 6098h - 回零方式
    HOMING_SPEED_HIGH = 0x03E4     # 6099h:01 - 回零高速
    HOMING_SPEED_LOW = 0x03E5      # 6099h:02 - 回零低速
    HOMING_ACCELERATION = 0x03E6   # 609Ah - 回零加速度
    HOME_OFFSET = 0x03C7           # 607Ch - 原点偏移

    # ==================== 故障相关 ====================
    FAULT_CODE = 0x0398            # 603Fh - 故障代码

    # ==================== DI/DO 相关 ====================
    DI_FUNCTION_BASE = 0x0400      # 2010h - DI 功能配置基地址
    DI_LOGIC_BASE = 0x0410         # 2011h - DI 逻辑配置基地址
    DI_STATUS = 0x0420             # 60FDh - DI 状态
    DO_FUNCTION_BASE = 0x0430      # 2020h - DO 功能配置基地址
    DO_CONTROL = 0x0440            # 60FEh - DO 控制

    # ==================== 软件限位 ====================
    SW_POSITION_LIMIT_MIN = 0x03C9  # 607Dh:01 - 软件限位最小值
    SW_POSITION_LIMIT_MAX = 0x03CA  # 607Dh:02 - 软件限位最大值

    # ==================== 通信配置 ====================
    SLAVE_ADDRESS = 0x0230         # 200Ch:02 - 从站地址
    BAUDRATE = 0x0231              # 200Ch:03 - 波特率

    # ==================== 抱闸控制 ====================
    BRAKE_CONTROL = 0x0450         # 抱闸控制寄存器
    BRAKE_STATUS = 0x0451          # 抱闸状态寄存器
```

### 4.4 运行模式定义

```python
class OperationMode(IntEnum):
    """运行模式"""
    NO_MODE = 0x00
    PROFILE_POSITION = 0x01       # PP - 轮廓位置模式
    VELOCITY_MODE = 0x02          # VM - 速度模式
    PROFILE_VELOCITY = 0x03       # PV - 轮廓速度模式
    PROFILE_TORQUE = 0x04         # PT - 轮廓力矩模式
    HOMING = 0x06                 # HM - 回零模式
    INTERPOLATION = 0x07          # IP - 插补模式
    CSP = 0x08                    # CSP - 周期同步位置模式
    CSV = 0x09                    # CSV - 周期同步速度模式
    CST = 0x0A                    # CST - 周期同步力矩模式
```

---

## 5. Layer 4: 高级 API 层设计

### 5.1 模块结构

```
high_level_api/
├── __init__.py
├── motor.py            # 电机高级接口
├── axis_config.py      # 轴配置定义
├── motion.py           # 运动控制
├── homing.py           # 回零控制
├── io_control.py       # IO 控制
├── limits.py           # 限位配置
├── brake.py            # 抱闸控制
├── parameters.py       # 参数管理
├── events.py           # 事件回调
└── exceptions.py       # 异常定义
```

### 5.2 Motor 类设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                   Motor                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ - _controller: MotorController                                                 │
│ - _axis: Axis                                                                  │
│ - _axis_config: AxisConfig                                                     │
│ - _motion: MotionControl                                                       │
│ - _homing: HomingControl                                                       │
│ - _limits: LimitsControl                                                       │
│ - _brake: BrakeControl                                                         │
│ - _io: IOControl                                                               │
│ - _events: EventManager                                                        │
│ - _status_monitor: StatusMonitor                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│ «轴配置»                                                                       │
│ + get_axis() -> Axis                                                           │
│ + get_axis_config() -> AxisConfig                                              │
│ + get_max_velocity() -> float                                                  │
│ + get_stroke_range() -> Tuple[float, float]                                    │
│ + has_brake() -> bool                                                          │
│ + release_brake() -> bool                                                      │
│ + engage_brake() -> bool                                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│ «使能控制»                                                                     │
│ + enable() -> bool                                                             │
│ + disable() -> bool                                                            │
│ + is_enabled() -> bool                                                         │
│ + reset_fault() -> bool                                                        │
│ + emergency_stop() -> bool                                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│ «运动控制»                                                                     │
│ + jog_forward(velocity: int) -> bool                                           │
│ + jog_reverse(velocity: int) -> bool                                           │
│ + stop() -> bool                                                               │
│ + quick_stop() -> bool                                                         │
│ + set_position_mode() -> bool                                                  │
│ + set_velocity_mode() -> bool                                                  │
│ + set_torque_mode() -> bool                                                    │
│ + move_absolute(position, velocity, acceleration) -> bool                      │
│ + move_relative(distance, velocity, acceleration) -> bool                      │
│ + set_velocity(velocity: int) -> bool                                          │
│ + set_torque(torque: int) -> bool                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│ «回零控制»                                                                     │
│ + set_homing_mode() -> bool                                                    │
│ + start_homing(method: int) -> bool                                            │
│ + set_homing_velocity(high: int, low: int) -> bool                            │
│ + is_homing_completed() -> bool                                                │
│ + wait_for_homing_done(timeout: float) -> bool                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│ «限位配置»                                                                     │
│ + set_positive_limit_switch(di: int, logic: int) -> bool                      │
│ + set_negative_limit_switch(di: int, logic: int) -> bool                      │
│ + enable_software_limit(min: int, max: int) -> bool                           │
│ + disable_software_limit() -> bool                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│ «状态查询»                                                                     │
│ + get_current_position() -> int                                                │
│ + get_current_velocity() -> int                                                │
│ + get_current_torque() -> int                                                  │
│ + get_status() -> MotorStatus                                                  │
│ + get_fault_code() -> int                                                      │
│ + is_in_position() -> bool                                                     │
│ + is_fault() -> bool                                                           │
│ + is_running() -> bool                                                         │
├───────────────────────────────────────────────────────────────────────────────┤
│ «事件回调»                                                                     │
│ + on_position_reached(callback: Callable) -> None                              │
│ + on_fault_occurred(callback: Callable) -> None                                │
│ + on_homing_completed(callback: Callable) -> None                              │
│ + on_limit_triggered(callback: Callable) -> None                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 AxisConfig 设计

```python
@dataclass
class AxisConfig:
    """轴配置参数"""
    axis: Axis                    # 轴类型 (X/Y/Z)
    model: str                    # 型号 (CFG4/CFG5/CFG8)
    motor_power: int              # 电机功率 (W)
    has_brake: bool               # 是否有抱闸
    ball_screw_lead: float        # 丝杠导程 (mm)
    max_velocity: float           # 最大速度 (mm/s)
    stroke_min: float             # 最小行程 (mm)
    stroke_max: float             # 最大行程 (mm)
    positioning_accuracy: float   # 定位精度 (mm)
    repeat_accuracy: float        # 重复定位精度 (mm)
    max_payload_horizontal: float # 水平最大负载 (kg)
    max_payload_vertical: float   # 垂直最大负载 (kg)
    slave_id: int                 # 默认从站地址

    def validate_velocity(self, velocity: float) -> float:
        """验证并限制速度在有效范围内"""
        return min(abs(velocity), self.max_velocity)

    def validate_position(self, position: float) -> float:
        """验证并限制位置在行程范围内"""
        return max(self.stroke_min, min(position, self.stroke_max))

    def mm_to_pulse(self, mm: float) -> int:
        """毫米转换为脉冲数"""
        # 假设编码器分辨率为 10000 脉冲/圈
        pulses_per_rev = 10000
        pulse = int(mm / self.ball_screw_lead * pulses_per_rev)
        return pulse

    def pulse_to_mm(self, pulse: int) -> float:
        """脉冲数转换为毫米"""
        pulses_per_rev = 10000
        mm = pulse * self.ball_screw_lead / pulses_per_rev
        return mm


# 预定义轴配置
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

### 5.4 使能流程设计

```
Motor.enable() 调用流程:

┌─────────────────┐
│  enable() 调用  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     否     ┌─────────────────┐
│  检查是否已使能  │ ─────────▶ │  返回 True      │
└────────┬────────┘           └─────────────────┘
         │ 否
         ▼
┌─────────────────┐     是     ┌─────────────────┐
│  检查是否有故障  │ ─────────▶ │  尝试故障复位   │
└────────┬────────┘           └────────┬────────┘
         │ 否                          │
         │ ◀───────────────────────────┘
         ▼
┌─────────────────┐     是     ┌─────────────────┐
│ 检查是否有抱闸   │ ─────────▶ │  释放抱闸       │
│  (Z 轴)         │           └────────┬────────┘
└────────┬────────┘                    │
         │ 否                          │
         │ ◀───────────────────────────┘
         ▼
┌─────────────────┐
│  读取当前状态   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 状态机转换流程  │
│ ┌─────────────┐ │
│ │ Switch On   │ │
│ │  Disabled   │ │
│ └──────┬──────┘ │
│        ▼        │
│ ┌─────────────┐ │
│ │ Ready to    │ │◀── 写入 0x0006 (Shutdown)
│ │ Switch On   │ │
│ └──────┬──────┘ │
│        ▼        │
│ ┌─────────────┐ │
│ │ Switched On │ │◀── 写入 0x0007 (Switch On)
│ └──────┬──────┘ │
│        ▼        │
│ ┌─────────────┐ │
│ │ Operation   │ │◀── 写入 0x000F (Enable Operation)
│ │  Enabled    │ │
│ └─────────────┘ │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  验证使能状态   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  返回结果       │
└─────────────────┘
```

### 5.5 位置运动流程设计

```
Motor.move_absolute() 调用流程:

┌─────────────────────┐
│ move_absolute() 调用│
│ position, velocity  │
│ acceleration        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     否     ┌─────────────────┐
│   检查是否已使能    │ ─────────▶ │  返回 False     │
└──────────┬──────────┘           │  (需先使能)     │
           │ 是                    └─────────────────┘
           ▼
┌─────────────────────┐
│ 验证参数有效性      │
│ - 位置在行程范围内  │
│ - 速度不超过最大值  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     否     ┌─────────────────┐
│ 当前模式是位置模式? │ ─────────▶ │ 切换到位置模式  │
└──────────┬──────────┘           └────────┬────────┘
           │ 是                            │
           │ ◀─────────────────────────────┘
           ▼
┌─────────────────────┐
│  写入运动参数       │
│  1. 轮廓速度        │
│  2. 轮廓加速度      │
│  3. 轮廓减速度      │
│  4. 目标位置        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 设置控制字          │
│ Bit4=1 (新设定点)   │
│ Bit5=0 (立即执行)   │
│ Bit6=0 (绝对位置)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 等待 Bit12=1        │
│ (设定点确认)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 清除 Bit4           │
│ (为下次运动准备)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  返回 True          │
└─────────────────────┘
```

---

## 6. Layer 5: 应用层设计

### 6.1 模块结构

```
app/
├── __init__.py
├── main.py                 # 主程序入口
├── main_window.py          # 主窗口 (支持视图切换)
└── widgets/
    ├── __init__.py
    ├── connection_panel.py     # 串口连接面板
    ├── axis_panel.py           # 轴选择面板
    ├── status_panel.py         # 状态监控面板
    ├── motion_panel.py         # 运动控制面板 (使能、点动、位置移动、回零)
    ├── parameter_panel.py      # 参数设置面板
    ├── modbus_debug_panel.py   # Modbus 调试面板
    └── register_config_panel.py  # 寄存器配置面板
```

**视图切换机制:**
- 使用 QStackedWidget 实现三个视图的切换
- 通过菜单 "视图" 或快捷键 (Ctrl+1/Ctrl+2/Ctrl+3) 切换
- 左侧面板 (连接、轴选择、状态) 在所有视图中共享

### 6.2 主窗口类图

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                 MainWindow                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│ - _service: ServoService                                                       │
│ - _view_stack: QStackedWidget          # 视图切换容器                           │
│ - _current_view: int                   # 当前视图索引                           │
│ - _status_timer: QTimer                # 状态更新定时器                          │
│ - _statusbar: QStatusBar                                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│ 左侧面板 (共享):                                                                │
│ - _connection_panel: ConnectionPanel   # 串口连接面板                           │
│ - _axis_panel: AxisPanel               # 轴选择面板                             │
│ - _status_panel: StatusPanel           # 状态监控面板                           │
├───────────────────────────────────────────────────────────────────────────────┤
│ 电机控制视图 (VIEW_MOTOR_CONTROL = 0):                                          │
│ - _motion_panel: MotionPanel           # 运动控制面板                           │
│ - _parameter_panel: ParameterPanel     # 参数设置面板                           │
├───────────────────────────────────────────────────────────────────────────────┤
│ Modbus 调试视图 (VIEW_MODBUS_DEBUG = 1):                                        │
│ - _modbus_debug_panel: ModbusDebugPanel  # Modbus 调试面板                      │
├───────────────────────────────────────────────────────────────────────────────┤
│ 寄存器配置视图 (VIEW_REGISTER_CONFIG = 2):                                       │
│ - _register_config_panel: RegisterConfigPanel  # 寄存器配置面板                  │
├───────────────────────────────────────────────────────────────────────────────┤
│ + _init_ui() -> None                                                           │
│ + _init_menu() -> None                                                         │
│ + _switch_view(view_index: int) -> None  # 视图切换                             │
│ + _on_connected() -> None                                                      │
│ + _on_disconnected() -> None                                                   │
│ + pause_status_timer() -> None           # 暂停状态更新 (避免通信冲突)            │
│ + resume_status_timer() -> None          # 恢复状态更新                          │
│ + closeEvent(event: QCloseEvent) -> None                                       │
└───────────────────────────────────────────────────────────────────────────────┘

界面布局:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 菜单栏: 文件 | 视图 | 连接 | 控制 | 帮助                                       │
├────────────────────┬────────────────────────────────────────────────────────┤
│ 左侧面板 (固定)     │ 右侧面板 (QStackedWidget)                               │
│                    │                                                        │
│ ┌────────────────┐ │ 视图1: 电机控制 (Ctrl+1)                                │
│ │ 连接面板       │ │ ┌────────────────────────────────────────────────────┐ │
│ │ [串口] [连接]  │ │ │ 运动控制面板                                       │ │
│ └────────────────┘ │ │ [使能] [禁用] [停止] [急停]                        │ │
│                    │ │ [正向点动] [反向点动]                               │ │
│ ┌────────────────┐ │ │ [目标位置] [移动到] [相对移动]                      │ │
│ │ 轴选择面板     │ │ │ [回零方式] [开始回零]                               │ │
│ │ (X) (Y) (Z)    │ │ └────────────────────────────────────────────────────┘ │
│ └────────────────┘ │ ┌────────────────────────────────────────────────────┐ │
│                    │ │ 参数设置面板                                       │ │
│ ┌────────────────┐ │ │ [速度] [加速度] [减速度] [应用] [读取]              │ │
│ │ 状态监控面板   │ │ └────────────────────────────────────────────────────┘ │
│ │ 位置: xxx mm   │ │                                                        │
│ │ 速度: xxx mm/s │ │ 视图2: Modbus 调试 (Ctrl+2)                            │
│ │ 状态: xxx      │ │ ┌────────────────────────────────────────────────────┐ │
│ │ [■使能][■故障] │ │ │ [快捷操作] [状态字] [位置] [速度] [错误码]          │ │
│ └────────────────┘ │ │ [手动发送] 功能码/地址/数量 [发送]                  │ │
│                    │ │ [通信日志] TX/RX 帧显示                             │ │
│                    │ │ [统计] 发送:xx 接收:xx 错误:xx 成功率:xx%           │ │
│                    │ └────────────────────────────────────────────────────┘ │
│                    │                                                        │
│                    │ 视图3: 寄存器配置 (Ctrl+3)                              │
│                    │ ┌────────────────────────────────────────────────────┐ │
│                    │ │ [分类标签] 核心|位置|速度|回零|DI配置|编码器         │ │
│                    │ │ [寄存器列表] 地址|名称|当前值|说明                   │ │
│                    │ │ [操作] 读取当前|读取全部|写入|保存到EEPROM           │ │
│                    │ └────────────────────────────────────────────────────┘ │
├────────────────────┴────────────────────────────────────────────────────────┤
│ 状态栏: 已连接 - 电机控制视图                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 轴选择控件设计

```python
class AxisSelector(QWidget):
    """
    轴选择控件

    提供 X/Y/Z 轴选择，显示当前轴参数信息
    """

    # 信号定义
    axis_changed = pyqtSignal(Axis)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_axis = Axis.Z  # 默认 Z 轴
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 轴选择按钮组
        axis_group = QButtonGroup(self)
        axis_layout = QHBoxLayout()

        for axis in Axis:
            radio = QRadioButton(f"{axis.value} 轴")
            radio.setChecked(axis == Axis.Z)  # 默认选中 Z 轴
            radio.toggled.connect(lambda checked, a=axis:
                                  self._on_axis_toggled(a) if checked else None)
            axis_group.addButton(radio)
            axis_layout.addWidget(radio)

        layout.addLayout(axis_layout)

        # 轴参数信息面板
        self._info_panel = AxisInfoPanel(self)
        layout.addWidget(self._info_panel)

        # 更新显示
        self._update_info()

    def _on_axis_toggled(self, axis: Axis):
        self._current_axis = axis
        self._update_info()
        self.axis_changed.emit(axis)

    def _update_info(self):
        config = AXIS_CONFIGS[self._current_axis]
        self._info_panel.update_config(config)

    def get_current_axis(self) -> Axis:
        return self._current_axis

    def set_current_axis(self, axis: Axis):
        self._current_axis = axis
        # 更新 UI 状态...
```

### 6.4 状态面板设计

```python
class StatusPanel(QWidget):
    """
    状态显示面板

    显示电机状态机状态、使能状态、故障状态、位置、速度、力矩等
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout(self)

        # 状态机状态
        layout.addWidget(QLabel("状态机:"), 0, 0)
        self._state_label = QLabel("--")
        self._state_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._state_label, 0, 1)

        # 使能状态 LED
        layout.addWidget(QLabel("使能:"), 0, 2)
        self._enable_led = LEDIndicator()
        layout.addWidget(self._enable_led, 0, 3)

        # 故障状态 LED
        layout.addWidget(QLabel("故障:"), 0, 4)
        self._fault_led = LEDIndicator()
        layout.addWidget(self._fault_led, 0, 5)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line, 1, 0, 1, 6)

        # 位置显示
        layout.addWidget(QLabel("当前位置:"), 2, 0)
        self._position_value = QLabel("0")
        self._position_value.setProperty("class", "value-large")
        layout.addWidget(self._position_value, 2, 1)
        layout.addWidget(QLabel("mm"), 2, 2)

        # 速度显示
        layout.addWidget(QLabel("当前速度:"), 3, 0)
        self._velocity_value = QLabel("0")
        self._velocity_value.setProperty("class", "value")
        layout.addWidget(self._velocity_value, 3, 1)
        layout.addWidget(QLabel("mm/s"), 3, 2)

        # 力矩显示
        layout.addWidget(QLabel("当前力矩:"), 4, 0)
        self._torque_value = QLabel("0")
        self._torque_value.setProperty("class", "value")
        layout.addWidget(self._torque_value, 4, 1)
        layout.addWidget(QLabel("%"), 4, 2)

        # 温度和电压
        layout.addWidget(QLabel("温度:"), 2, 3)
        self._temp_value = QLabel("--")
        layout.addWidget(self._temp_value, 2, 4)
        layout.addWidget(QLabel("°C"), 2, 5)

        layout.addWidget(QLabel("电压:"), 3, 3)
        self._voltage_value = QLabel("--")
        layout.addWidget(self._voltage_value, 3, 4)
        layout.addWidget(QLabel("V"), 3, 5)

    def update_status(self, status: MotorStatus):
        """更新状态显示"""
        # 状态机状态
        state_text = self._get_state_text(status.state_machine)
        self._state_label.setText(state_text)

        # LED 指示
        self._enable_led.set_state(status.enabled)
        self._fault_led.set_state(status.fault, color='red' if status.fault else 'gray')

        # 数值显示
        self._position_value.setText(f"{status.position:.2f}")
        self._velocity_value.setText(f"{status.velocity:.1f}")
        self._torque_value.setText(f"{status.torque / 10:.1f}")

    def _get_state_text(self, state: int) -> str:
        """获取状态机状态文本"""
        state_texts = {
            0x00: "初始化中",
            0x40: "等待上电",
            0x21: "准备就绪",
            0x23: "已上电",
            0x27: "运行中",
            0x07: "快速停止",
            0x08: "故障",
        }
        return state_texts.get(state & 0x6F, f"未知 (0x{state:04X})")
```

### 6.5 UI 信号流程

```
用户界面交互信号流程:

┌─────────────────┐
│   用户点击      │
│  [使能] 按钮    │
└────────┬────────┘
         │
         ▼ clicked signal
┌─────────────────┐
│  JogPanel.      │
│  _on_enable_    │
│  clicked()      │
└────────┬────────┘
         │
         ▼ emit enable_requested signal
┌─────────────────┐
│ MotorControl    │
│ ViewController  │
│ .on_enable_     │
│ requested()     │
└────────┬────────┘
         │
         ▼ 调用
┌─────────────────┐
│   Motor.        │
│   enable()      │
└────────┬────────┘
         │
         ▼ 状态变化
┌─────────────────┐
│  StatusMonitor  │
│  检测到状态变化  │
└────────┬────────┘
         │
         ▼ emit status_changed signal
┌─────────────────┐
│ StatusPanel.    │
│ update_status() │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UI 更新        │
│  LED 变绿       │
│  状态文字更新   │
└─────────────────┘
```

---

## 7. 数据结构设计

### 7.1 核心数据类

```python
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional, List, Callable


class Axis(Enum):
    """轴类型"""
    X = "X"
    Y = "Y"
    Z = "Z"


class CiA402State(IntEnum):
    """CiA402 状态机状态"""
    NOT_READY_TO_SWITCH_ON = 0x00
    SWITCH_ON_DISABLED = 0x40
    READY_TO_SWITCH_ON = 0x21
    SWITCHED_ON = 0x23
    OPERATION_ENABLED = 0x27
    QUICK_STOP_ACTIVE = 0x07
    FAULT_REACTION_ACTIVE = 0x0F
    FAULT = 0x08


class OperationMode(IntEnum):
    """运行模式"""
    NO_MODE = 0x00
    PROFILE_POSITION = 0x01
    VELOCITY_MODE = 0x02
    PROFILE_VELOCITY = 0x03
    PROFILE_TORQUE = 0x04
    HOMING = 0x06
    INTERPOLATION = 0x07
    CSP = 0x08
    CSV = 0x09
    CST = 0x0A


class DIFunction(IntEnum):
    """数字输入功能"""
    UNDEFINED = 0
    MOTOR_ENABLE = 1
    ALARM_RESET = 2
    POSITIVE_LIMIT = 14
    NEGATIVE_LIMIT = 15
    HOME_SWITCH = 31


class HomingMethod(IntEnum):
    """回零方式"""
    NEGATIVE_LIMIT = 17
    POSITIVE_LIMIT = 18
    NEGATIVE_LIMIT_INDEX = 19
    POSITIVE_LIMIT_INDEX = 20
    NEGATIVE_INDEX = 33
    POSITIVE_INDEX = 34
    CURRENT_POSITION = 35
    STALL = 37


@dataclass
class MotorStatus:
    """电机状态"""
    enabled: bool              # 使能状态
    fault: bool                # 故障状态
    running: bool              # 运行状态
    in_position: bool          # 到位状态
    homing_done: bool          # 回零完成
    position: float            # 当前位置 (mm)
    velocity: float            # 当前速度 (mm/s)
    torque: int                # 当前力矩 (0.1%)
    state_machine: int         # 状态机状态值
    fault_code: int            # 故障代码
    temperature: int           # 温度 (°C)
    bus_voltage: float         # 母线电压 (V)
    axis: Axis                 # 所属轴


@dataclass
class CommunicationStatistics:
    """通信统计"""
    tx_count: int = 0          # 发送帧数
    rx_count: int = 0          # 接收帧数
    error_count: int = 0       # 错误数
    timeout_count: int = 0     # 超时数
    crc_error_count: int = 0   # CRC 错误数

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.tx_count
        if total == 0:
            return 0.0
        success = self.rx_count - self.error_count
        return success / total * 100


@dataclass
class FaultInfo:
    """故障信息"""
    code: int                  # 故障码
    name: str                  # 故障名称
    description: str           # 故障描述
    severity: str              # 严重程度 (warning/error/critical)
    auto_recover: bool         # 是否可自动恢复
    suggestion: str            # 处理建议


@dataclass
class ModbusLogEntry:
    """Modbus 日志条目"""
    timestamp: float           # 时间戳
    direction: str             # 方向 (TX/RX/ERR/TIMEOUT)
    slave_id: int              # 从站地址
    function_code: int         # 功能码
    raw_data: bytes            # 原始数据
    parsed_info: str           # 解析信息
```

### 7.2 故障码定义

```python
FAULT_DEFINITIONS: Dict[int, FaultInfo] = {
    0x0000: FaultInfo(
        code=0x0000,
        name="No error",
        description="无故障",
        severity="info",
        auto_recover=True,
        suggestion=""
    ),
    0x2300: FaultInfo(
        code=0x2300,
        name="Overcurrent",
        description="电机过流",
        severity="critical",
        auto_recover=False,
        suggestion="检查负载是否过重，检查机械是否卡死"
    ),
    0x3110: FaultInfo(
        code=0x3110,
        name="DC link overvoltage",
        description="母线过压",
        severity="critical",
        auto_recover=True,
        suggestion="检查电源电压，降低减速度，增加制动电阻"
    ),
    0x3120: FaultInfo(
        code=0x3120,
        name="DC link undervoltage",
        description="母线欠压",
        severity="critical",
        auto_recover=True,
        suggestion="检查电源电压，检查电源容量，检查接线"
    ),
    0x4210: FaultInfo(
        code=0x4210,
        name="Over temperature drive",
        description="驱动器过温",
        severity="critical",
        auto_recover=True,
        suggestion="改善散热条件，降低运行负荷"
    ),
    0x7310: FaultInfo(
        code=0x7310,
        name="Overspeed",
        description="电机超速",
        severity="critical",
        auto_recover=True,
        suggestion="检查负载和速度设置，降低运行速度"
    ),
    0x8611: FaultInfo(
        code=0x8611,
        name="Following error",
        description="位置跟随误差过大",
        severity="critical",
        auto_recover=False,
        suggestion="降低运行速度，调整增益参数，检查机械负载"
    ),
    0x8612: FaultInfo(
        code=0x8612,
        name="Homing error",
        description="回零错误",
        severity="error",
        auto_recover=False,
        suggestion="检查限位开关配置，检查回零参数"
    ),
    # ... 其他故障码
}

def get_fault_info(fault_code: int) -> FaultInfo:
    """获取故障信息"""
    return FAULT_DEFINITIONS.get(fault_code, FaultInfo(
        code=fault_code,
        name="Unknown",
        description=f"未知故障 (0x{fault_code:04X})",
        severity="error",
        auto_recover=False,
        suggestion="请查阅手册或联系厂家"
    ))
```

---

## 8. 状态机设计

### 8.1 CiA402 状态机

```
                              ┌─────────────────────────────────────┐
                              │                                     │
                              ▼                                     │
┌─────────────────┐    ┌─────────────────┐                         │
│  Start          │───▶│ Not Ready to    │                         │
│                 │    │ Switch On       │                         │
└─────────────────┘    │ (初始化中)       │                         │
                       └────────┬────────┘                         │
                                │ 自动                              │
                                ▼                                   │
                       ┌─────────────────┐                         │
                       │ Switch On       │◀────────────────────────┤
                       │ Disabled        │                         │
                       │ (等待上电命令)   │                         │
                       └────────┬────────┘                         │
                                │ Shutdown (0x0006)                │
                                ▼                                   │
                       ┌─────────────────┐                         │
            ┌─────────▶│ Ready to        │                         │
            │          │ Switch On       │                         │
            │          │ (准备就绪)       │                         │
            │          └────────┬────────┘                         │
            │                   │ Switch On (0x0007)               │
            │                   ▼                                   │
            │          ┌─────────────────┐                         │
            │ Disable  │ Switched On     │                         │
            │ Voltage  │ (已上电)         │                         │
            │ (0x0000) └────────┬────────┘                         │
            │                   │ Enable Operation (0x000F)        │
            │                   ▼                                   │
            │          ┌─────────────────┐     Quick Stop          │
            └──────────│ Operation       │────────────────────┐    │
                       │ Enabled         │                    │    │
                       │ (运行中)         │                    │    │
                       └────────┬────────┘                    │    │
                                │                             ▼    │
                                │                    ┌──────────────┤
                                │                    │ Quick Stop   │
                                │                    │ Active       │
                                │                    │ (快速停止中) │
                                │                    └──────────────┘
                                │ Fault
                                ▼
                       ┌─────────────────┐
                       │ Fault           │─────────────────────────┘
                       │ (故障)          │    Fault Reset (Bit7 上升沿)
                       └─────────────────┘
```

### 8.2 状态转换控制字

```python
class ControlWordBits:
    """控制字位定义"""
    SWITCH_ON = 0x0001           # Bit 0
    ENABLE_VOLTAGE = 0x0002      # Bit 1
    QUICK_STOP = 0x0004          # Bit 2 (低有效)
    ENABLE_OPERATION = 0x0008    # Bit 3
    NEW_SET_POINT = 0x0010       # Bit 4 (位置模式)
    CHANGE_IMMEDIATELY = 0x0020  # Bit 5 (位置模式)
    ABS_REL = 0x0040             # Bit 6 (0=绝对, 1=相对)
    FAULT_RESET = 0x0080         # Bit 7
    HALT = 0x0100                # Bit 8


class ControlWordCommands:
    """控制字命令"""
    SHUTDOWN = 0x0006            # 进入 Ready to Switch On
    SWITCH_ON = 0x0007           # 进入 Switched On
    ENABLE_OPERATION = 0x000F    # 进入 Operation Enabled
    DISABLE_VOLTAGE = 0x0000     # 进入 Switch On Disabled
    QUICK_STOP = 0x0002          # 进入 Quick Stop Active
    DISABLE_OPERATION = 0x0007   # 回到 Switched On
    FAULT_RESET = 0x0080         # 故障复位 (上升沿)


class StatusWordBits:
    """状态字位定义"""
    READY_TO_SWITCH_ON = 0x0001  # Bit 0
    SWITCHED_ON = 0x0002         # Bit 1
    OPERATION_ENABLED = 0x0004   # Bit 2
    FAULT = 0x0008               # Bit 3
    VOLTAGE_ENABLED = 0x0010     # Bit 4
    QUICK_STOP = 0x0020          # Bit 5 (低有效)
    SWITCH_ON_DISABLED = 0x0040  # Bit 6
    WARNING = 0x0080             # Bit 7
    REMOTE = 0x0200              # Bit 9
    TARGET_REACHED = 0x0400      # Bit 10
    INTERNAL_LIMIT = 0x0800      # Bit 11
    SET_POINT_ACK = 0x1000       # Bit 12 (位置模式)
    FOLLOWING_ERROR = 0x2000     # Bit 13 (位置模式)
```

### 8.3 状态机实现

```python
class StateMachine:
    """CiA402 状态机管理"""

    def __init__(self, controller: 'MotorController'):
        self._controller = controller
        self._current_state = CiA402State.SWITCH_ON_DISABLED

    def get_current_state(self) -> CiA402State:
        """获取当前状态"""
        status = self._controller.read_status_word()
        return self._parse_status_word(status)

    def _parse_status_word(self, status: int) -> CiA402State:
        """解析状态字获取状态机状态"""
        # 提取状态相关位
        state_bits = status & 0x006F

        if state_bits == 0x0000:
            return CiA402State.NOT_READY_TO_SWITCH_ON
        elif state_bits == 0x0040:
            return CiA402State.SWITCH_ON_DISABLED
        elif state_bits == 0x0021:
            return CiA402State.READY_TO_SWITCH_ON
        elif state_bits == 0x0023:
            return CiA402State.SWITCHED_ON
        elif state_bits == 0x0027:
            return CiA402State.OPERATION_ENABLED
        elif state_bits == 0x0007:
            return CiA402State.QUICK_STOP_ACTIVE
        elif status & 0x0008:  # Fault bit
            return CiA402State.FAULT
        else:
            return CiA402State.SWITCH_ON_DISABLED

    def transition_to_enabled(self) -> bool:
        """
        转换到使能状态

        Returns:
            成功返回 True
        """
        current = self.get_current_state()

        # 如果已经使能，直接返回
        if current == CiA402State.OPERATION_ENABLED:
            return True

        # 如果有故障，先复位
        if current == CiA402State.FAULT:
            if not self.fault_reset():
                return False
            current = self.get_current_state()

        # 状态转换序列
        transitions = [
            (CiA402State.SWITCH_ON_DISABLED, ControlWordCommands.SHUTDOWN),
            (CiA402State.READY_TO_SWITCH_ON, ControlWordCommands.SWITCH_ON),
            (CiA402State.SWITCHED_ON, ControlWordCommands.ENABLE_OPERATION),
        ]

        for expected_state, command in transitions:
            current = self.get_current_state()
            if current == CiA402State.OPERATION_ENABLED:
                return True

            self._controller.write_control_word(command)
            time.sleep(0.01)  # 等待状态转换

            # 验证转换
            new_state = self.get_current_state()
            if new_state == CiA402State.FAULT:
                return False

        return self.get_current_state() == CiA402State.OPERATION_ENABLED

    def fault_reset(self) -> bool:
        """故障复位"""
        # 写入 Bit7 低
        self._controller.write_control_word(0x0000)
        time.sleep(0.01)

        # 写入 Bit7 高 (上升沿触发)
        self._controller.write_control_word(ControlWordCommands.FAULT_RESET)
        time.sleep(0.05)

        # 写入 Bit7 低
        self._controller.write_control_word(0x0000)
        time.sleep(0.01)

        return self.get_current_state() != CiA402State.FAULT
```

---

## 9. 错误处理设计

### 9.1 异常层次结构

```
Exception
└── ServoMotorError (基类)
    ├── CommunicationError (通信层错误)
    │   ├── SerialPortError (串口错误)
    │   │   ├── PortNotFoundError
    │   │   ├── PortOpenError
    │   │   └── PortAccessError
    │   └── ModbusError (Modbus 错误)
    │       ├── ModbusTimeoutError
    │       ├── ModbusCRCError
    │       └── ModbusExceptionError
    │           ├── IllegalFunctionError
    │           ├── IllegalAddressError
    │           └── IllegalDataError
    ├── MotorError (电机控制层错误)
    │   ├── MotorFaultError
    │   ├── MotorNotEnabledError
    │   ├── MotorBusyError
    │   └── StateMachineError
    ├── MotionError (运动控制错误)
    │   ├── PositionOutOfRangeError
    │   ├── VelocityExceededError
    │   ├── HomingError
    │   └── LimitSwitchError
    └── ConfigurationError (配置错误)
        ├── InvalidParameterError
        └── AxisNotFoundError
```

### 9.2 异常定义

```python
class ServoMotorError(Exception):
    """伺服电机控制系统基础异常"""

    def __init__(self, message: str, code: int = 0, details: dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = time.time()


class CommunicationError(ServoMotorError):
    """通信层错误"""
    pass


class SerialPortError(CommunicationError):
    """串口错误"""
    pass


class ModbusTimeoutError(CommunicationError):
    """Modbus 通信超时"""

    def __init__(self, slave_id: int, function_code: int, timeout: float):
        super().__init__(
            f"Modbus timeout: slave={slave_id}, func=0x{function_code:02X}, "
            f"timeout={timeout}s",
            code=0x1001,
            details={
                'slave_id': slave_id,
                'function_code': function_code,
                'timeout': timeout
            }
        )


class MotorFaultError(ServoMotorError):
    """电机故障"""

    def __init__(self, fault_code: int, axis: Axis = None):
        fault_info = get_fault_info(fault_code)
        super().__init__(
            f"Motor fault: {fault_info.name} - {fault_info.description}",
            code=fault_code,
            details={
                'axis': axis.value if axis else None,
                'fault_info': fault_info
            }
        )
        self.fault_info = fault_info


class PositionOutOfRangeError(ServoMotorError):
    """位置超出范围"""

    def __init__(self, position: float, axis_config: AxisConfig):
        super().__init__(
            f"Position {position}mm out of range "
            f"[{axis_config.stroke_min}, {axis_config.stroke_max}]mm",
            code=0x3001,
            details={
                'position': position,
                'min': axis_config.stroke_min,
                'max': axis_config.stroke_max,
                'axis': axis_config.axis.value
            }
        )
```

### 9.3 错误处理策略

```python
class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self._error_callbacks: List[Callable[[ServoMotorError], None]] = []
        self._error_history: List[ServoMotorError] = []
        self._max_history = 100

    def register_callback(self, callback: Callable[[ServoMotorError], None]):
        """注册错误回调"""
        self._error_callbacks.append(callback)

    def handle_error(self, error: ServoMotorError):
        """处理错误"""
        # 记录错误
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

        # 记录日志
        logging.error(f"Error: {error}", exc_info=True)

        # 通知回调
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logging.error(f"Error callback failed: {e}")

        # 根据错误类型决定是否重新抛出
        if isinstance(error, (MotorFaultError, PositionOutOfRangeError)):
            raise error


def with_error_handling(func):
    """错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ServoMotorError:
            raise
        except serial.SerialException as e:
            raise SerialPortError(str(e))
        except Exception as e:
            raise ServoMotorError(f"Unexpected error: {e}")
    return wrapper
```

### 9.4 重试机制

```python
class RetryPolicy:
    """重试策略"""

    def __init__(self,
                 max_retries: int = 3,
                 retry_delay: float = 0.1,
                 backoff_factor: float = 2.0,
                 retry_exceptions: tuple = (ModbusTimeoutError,)):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.retry_exceptions = retry_exceptions


def with_retry(policy: RetryPolicy = None):
    """重试装饰器"""
    if policy is None:
        policy = RetryPolicy()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            delay = policy.retry_delay

            for attempt in range(policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except policy.retry_exceptions as e:
                    last_error = e
                    if attempt < policy.max_retries:
                        logging.warning(
                            f"Retry {attempt + 1}/{policy.max_retries}: {e}"
                        )
                        time.sleep(delay)
                        delay *= policy.backoff_factor
                    else:
                        raise

            raise last_error
        return wrapper
    return decorator
```

---

## 10. 线程模型设计

### 10.1 线程架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            主线程 (UI Thread)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         PyQt5 Event Loop                            ││
│  │  - 界面渲染                                                          ││
│  │  - 用户事件处理                                                      ││
│  │  - 信号槽调用                                                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ signals            │ signals            │ signals
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  状态监控线程    │  │   通信工作线程   │  │   曲线更新线程   │
│ StatusMonitor   │  │ CommunicationW  │  │   PlotUpdater   │
│                 │  │     orker       │  │                 │
│ - 周期读取状态   │  │ - 执行 Modbus   │  │ - 更新曲线数据  │
│ - 发射状态信号   │  │   请求          │  │ - 50ms 刷新     │
│ - 100ms 周期    │  │ - 队列处理      │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │
         └────────────────────┘
                   │
                   ▼ 共享
         ┌─────────────────┐
         │   SerialPort    │
         │   (线程锁保护)   │
         └─────────────────┘
```

### 10.2 状态监控线程

```python
class StatusMonitor(QThread):
    """
    状态监控线程

    周期性读取电机状态并发射信号
    """

    # 信号定义
    status_updated = pyqtSignal(MotorStatus)
    fault_detected = pyqtSignal(int)  # 故障码
    connection_lost = pyqtSignal()

    def __init__(self, motor: Motor, interval_ms: int = 100):
        super().__init__()
        self._motor = motor
        self._interval = interval_ms / 1000.0
        self._running = False
        self._last_fault_code = 0

    def run(self):
        self._running = True
        error_count = 0

        while self._running:
            try:
                # 读取状态
                status = self._motor.get_status()

                # 发射状态更新信号
                self.status_updated.emit(status)

                # 检查故障
                if status.fault and status.fault_code != self._last_fault_code:
                    self.fault_detected.emit(status.fault_code)
                    self._last_fault_code = status.fault_code
                elif not status.fault:
                    self._last_fault_code = 0

                error_count = 0

            except CommunicationError as e:
                error_count += 1
                if error_count >= 3:
                    self.connection_lost.emit()
                    self._running = False

            time.sleep(self._interval)

    def stop(self):
        self._running = False
        self.wait()
```

### 10.3 通信工作线程

```python
class CommunicationWorker(QThread):
    """
    通信工作线程

    处理异步 Modbus 请求
    """

    # 信号定义
    request_completed = pyqtSignal(int, object)  # request_id, result
    request_failed = pyqtSignal(int, str)        # request_id, error

    def __init__(self, modbus: ModbusClient):
        super().__init__()
        self._modbus = modbus
        self._request_queue: Queue = Queue()
        self._running = False
        self._request_id = 0

    def submit_request(self, request_type: str, **kwargs) -> int:
        """提交请求"""
        self._request_id += 1
        self._request_queue.put({
            'id': self._request_id,
            'type': request_type,
            'kwargs': kwargs
        })
        return self._request_id

    def run(self):
        self._running = True

        while self._running:
            try:
                request = self._request_queue.get(timeout=0.1)
            except Empty:
                continue

            try:
                result = self._execute_request(request)
                self.request_completed.emit(request['id'], result)
            except Exception as e:
                self.request_failed.emit(request['id'], str(e))

    def _execute_request(self, request: dict) -> object:
        """执行请求"""
        request_type = request['type']
        kwargs = request['kwargs']

        if request_type == 'read_holding':
            return self._modbus.read_holding_registers(**kwargs)
        elif request_type == 'write_single':
            return self._modbus.write_single_register(**kwargs)
        elif request_type == 'write_multiple':
            return self._modbus.write_multiple_registers(**kwargs)
        else:
            raise ValueError(f"Unknown request type: {request_type}")

    def stop(self):
        self._running = False
        self.wait()
```

### 10.4 线程安全设计

```python
class ThreadSafeModbusClient:
    """线程安全的 Modbus 客户端包装器"""

    def __init__(self, modbus: ModbusClient):
        self._modbus = modbus
        self._lock = threading.RLock()

    def read_holding_registers(self, slave_id: int, address: int,
                                count: int) -> List[int]:
        with self._lock:
            return self._modbus.read_holding_registers(slave_id, address, count)

    def write_single_register(self, slave_id: int, address: int,
                               value: int) -> bool:
        with self._lock:
            return self._modbus.write_single_register(slave_id, address, value)

    def write_multiple_registers(self, slave_id: int, address: int,
                                   values: List[int]) -> bool:
        with self._lock:
            return self._modbus.write_multiple_registers(slave_id, address, values)
```

---

## 11. 配置管理设计

### 11.1 配置文件结构

```yaml
# config.yaml

# 应用配置
app:
  language: "zh_CN"
  theme: "default"
  window:
    width: 1280
    height: 800
    remember_position: true

# 通信配置
communication:
  default_port: ""  # 自动检测
  baudrate: 115200
  timeout: 0.1
  retries: 3

# 轴配置
axes:
  default_axis: "Z"
  x:
    slave_id: 1
    max_velocity: 1000  # mm/s
    stroke_min: 50      # mm
    stroke_max: 1100    # mm
  y:
    slave_id: 2
    max_velocity: 500
    stroke_min: 100
    stroke_max: 500
  z:
    slave_id: 3
    max_velocity: 500
    stroke_min: 50
    stroke_max: 100

# 控制参数
control:
  jog_velocity: 100       # mm/s
  position_velocity: 200  # mm/s
  acceleration: 500       # mm/s²
  deceleration: 500       # mm/s²
  homing_velocity_high: 50
  homing_velocity_low: 10

# 监控配置
monitor:
  status_interval: 100    # ms
  plot_interval: 50       # ms
  plot_history: 10        # seconds

# 日志配置
logging:
  level: "INFO"
  file: "logs/servo_motor.log"
  max_size: 10485760      # 10MB
  backup_count: 5
```

### 11.2 配置管理类

```python
class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_PATH = "config.yaml"

    def __init__(self, config_path: str = None):
        self._config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict = {}
        self._load_defaults()

    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            'app': {
                'language': 'zh_CN',
                'theme': 'default',
            },
            'communication': {
                'baudrate': 115200,
                'timeout': 0.1,
                'retries': 3,
            },
            'axes': {
                'default_axis': 'Z',
            },
            'control': {
                'jog_velocity': 100,
                'position_velocity': 200,
                'acceleration': 500,
            },
            'monitor': {
                'status_interval': 100,
                'plot_interval': 50,
            },
        }

    def load(self) -> bool:
        """加载配置文件"""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                    self._merge_config(loaded)
            return True
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return False

    def save(self) -> bool:
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False

    def get(self, key: str, default=None):
        """获取配置值 (支持点号路径)"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def _merge_config(self, loaded: Dict):
        """合并加载的配置"""
        def merge(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge(base[key], value)
                else:
                    base[key] = value
        merge(self._config, loaded)


# 全局配置实例
config = ConfigManager()
```

---

## 12. 附录

### 12.1 文件清单

```
servo_motor_control/
├── servo_service/                    # 服务模块
│   ├── __init__.py
│   ├── service.py                    # 统一服务接口
│   ├── serial_comm/                  # Layer 1
│   │   ├── __init__.py
│   │   ├── serial_port.py
│   │   ├── port_scanner.py
│   │   └── exceptions.py
│   ├── modbus_rtu/                   # Layer 2
│   │   ├── __init__.py
│   │   ├── modbus_client.py
│   │   ├── frame_builder.py
│   │   ├── frame_parser.py
│   │   ├── crc.py
│   │   ├── exceptions.py
│   │   └── constants.py
│   ├── motor_control/                # Layer 3
│   │   ├── __init__.py
│   │   ├── motor_controller.py
│   │   ├── state_machine.py
│   │   ├── registers.py
│   │   ├── constants.py
│   │   └── exceptions.py
│   └── high_level_api/               # Layer 4
│       ├── __init__.py
│       ├── motor.py
│       ├── axis_config.py
│       ├── motion.py
│       ├── homing.py
│       ├── io_control.py
│       ├── limits.py
│       ├── brake.py
│       ├── parameters.py
│       ├── events.py
│       └── exceptions.py
├── app/                              # Layer 5
│   ├── __init__.py
│   ├── main.py
│   ├── main_window.py
│   ├── views/
│   ├── widgets/
│   ├── controllers/
│   ├── models/
│   ├── resources/
│   └── utils/
├── tests/
├── docs/
├── examples/
├── config.yaml
├── requirements.txt
├── setup.py
└── README.md
```

### 12.2 实现状态 (2026-01-12)

#### 已实现功能

| 功能模块 | 状态 | 说明 |
|----------|------|------|
| 串口通信 (Layer 1) | ✅ 完成 | SerialPort, PortScanner |
| Modbus RTU (Layer 2) | ✅ 完成 | ModbusClient, CRC, Frame |
| 电机控制 (Layer 3) | ✅ 完成 | Motor, StateMachine, Registers |
| 高级 API (Layer 4) | ✅ 完成 | ServoService, AxisConfig |
| GUI 界面 (Layer 5) | ✅ 完成 | 基础控制界面 |

#### Z 轴特殊配置

Z 轴由于物理安装方向，需要特殊配置：

| 参数 | 值 | 说明 |
|------|-----|------|
| `homing_method` | 17 | 负限位开关回零 |
| `velocity_polarity` | -1 | 速度方向反转 |
| DI2 功能 | 15 (负限位) | 实际接线为负限位 |
| DI3 功能 | 14 (正限位) | 实际接线为正限位 |

#### 运动控制实现细节

**点动 (Jog) 实现**:
- 使用 PP 模式 (Profile Position) 模拟连续运动
- 设置一个很远的目标位置实现持续运动
- 速度通过 Profile Velocity 寄存器控制
- 方向通过目标位置的正负控制

**停止 (Stop) 实现**:
1. 读取当前位置
2. 设置目标位置为当前位置
3. 设置 Halt 位 (控制字 bit 8)
4. 等待速度降为 0
5. 更新目标位置为最终位置
6. 清除 Halt 位

**回零 (Homing) 实现**:
1. 设置操作模式为 HOMING (0x06)
2. 设置回零方式 (Z 轴使用 method 17)
3. 重新执行使能序列 (Shutdown → Switch On → Enable)
4. 触发回零 (设置 New Setpoint 位)
5. 等待回零完成

#### 已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 点动方向有时不正确 | 🔄 待修复 | 需要进一步调试 velocity_polarity |
| 点动停止时有延迟 | 🔄 待优化 | Halt 减速时间可调整 |
| Modbus 调试界面 | ❌ 未实现 | 需求中有，尚未开发 |

### 12.3 修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2026-01-09 | 初始版本 | - |
| 1.1 | 2026-01-12 | 添加实现状态章节，记录 Z 轴特殊配置和运动控制细节 | Claude |

---

*文档结束*
