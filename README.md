# NiMotion 伺服电机控制系统

基于 Python 的 NiMotion 伺服电机控制系统，支持 Modbus RTU 通信协议和 CiA402 标准状态机。

## 功能特性

- **多轴支持**: 支持多轴平台 (Z4/Y/Z)
- **Modbus RTU**: 完整的 Modbus RTU 协议实现
- **CiA402 状态机**: 标准的伺服驱动器状态管理
- **PyQt5 GUI**: 现代化的图形用户界面，支持视图切换
- **Modbus 调试**: 内置 Modbus 调试面板，支持手动读写寄存器
- **线程安全**: 支持多线程环境下的安全操作
- **单位转换**: 自动毫米/脉冲单位转换

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (PyQt5 GUI)                    │
├─────────────────────────────────────────────────────────┤
│                 高级 API 层 (ServoService)               │
├─────────────────────────────────────────────────────────┤
│                 电机控制层 (Motor, StateMachine)         │
├─────────────────────────────────────────────────────────┤
│                 Modbus RTU 层 (ModbusClient)            │
├─────────────────────────────────────────────────────────┤
│                 串口通信层 (SerialPort)                  │
└─────────────────────────────────────────────────────────┘
```

## 安装

### 依赖要求

- Python 3.9+
- PyQt5
- pyserial
- PyYAML

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd CreateServoMotor

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖 (可选)
pip install -r requirements-dev.txt
```

## 快速开始

### 命令行使用

```python
from servo_service import ServoService, AxisName

# 创建服务并连接
service = ServoService(port="/dev/ttyUSB0")
service.connect()

# 选择 Z4 轴 (默认)
service.current_axis = AxisName.Z4

# 使能电机
service.enable()

# 回零
service.home()

# 移动到指定位置
service.move_to(50.0)  # 移动到 50mm

# 相对移动
service.move_by(10.0)  # 向前移动 10mm

# 点动
service.jog(100.0)  # 100mm/s 正向点动

# 停止
service.stop()

# 断开连接
service.disconnect()
```

### 使用上下文管理器

```python
from servo_service import ServoService, AxisName

with ServoService(port="/dev/ttyUSB0") as service:
    service.enable()
    service.move_to(50.0)
    # 退出时自动断开连接
```

### 启动 GUI

```bash
python app/main.py
```

### GUI 界面说明

GUI 界面支持三种视图，通过菜单或快捷键切换:

| 视图 | 快捷键 | 说明 |
|-----|-------|-----|
| 电机控制视图 | Ctrl+1 | 运动控制、参数设置 |
| Modbus 调试视图 | Ctrl+2 | 寄存器读写、通信日志 |
| 寄存器配置视图 | Ctrl+3 | 驱动器寄存器查看与配置 |

**电机控制视图功能:**
- 使能/禁用电机
- 点动控制 (正向/反向)
- 绝对/相对位置移动
- 回零操作
- 运动参数设置

**Modbus 调试视图功能:**
- 快捷读取常用寄存器 (状态字、位置、速度、错误码)
- 手动发送 Modbus 请求 (支持 FC 0x03, 0x04, 0x06, 0x10)
- 实时通信日志 (TX/RX 帧显示)
- 通信统计 (发送/接收/错误计数、成功率)

**寄存器配置视图功能:**
- 分类浏览驱动器寄存器 (核心控制、位置、速度、回零、DI配置、编码器)
- 显示寄存器地址、名称、当前值和说明
- 单个/批量读取寄存器值
- 修改寄存器值 (带写入验证)
- 关键寄存器警告提示 (如回零超时等)
- 保存参数到 EEPROM

## 项目结构

```
CreateServoMotor/
├── servo_service/           # 核心服务模块
│   ├── serial_comm/         # 串口通信层
│   ├── modbus_rtu/          # Modbus RTU 协议层
│   ├── motor_control/       # 电机控制层
│   └── high_level_api/      # 高级 API 层
├── app/                     # GUI 应用
│   ├── widgets/             # UI 组件
│   └── main.py              # 应用入口
├── tests/                   # 单元测试
├── examples/                # 使用示例
├── docs/                    # 文档
├── config.yaml              # 配置文件
├── requirements.txt         # 运行依赖
└── requirements-dev.txt     # 开发依赖
```

## 轴配置

默认配置支持 XYG321-A 三轴平台:

| 轴 | 从站地址 | 型号 | 功率 | 行程 | 最大速度 | 特性 |
|---|---------|-----|-----|-----|---------|-----|
| X | 1 | CFG8 | 200W | 50-1100mm | 1000mm/s | - |
| Y | 2 | CFG5 | 100W | 100-500mm | 500mm/s | - |
| Z | 3 | CFG4 | 100W | 0-100mm | 500mm/s | 带抱闸 |

## API 文档

### ServoService 主要方法

| 方法 | 描述 |
|-----|-----|
| `connect(port, baudrate)` | 连接到伺服系统 |
| `disconnect()` | 断开连接 |
| `enable(axis)` | 使能指定轴 |
| `disable(axis)` | 禁用指定轴 |
| `home(axis)` | 执行回零 |
| `move_to(position, velocity, axis)` | 绝对位置移动 |
| `move_by(distance, velocity, axis)` | 相对位置移动 |
| `jog(velocity, axis)` | 点动运行 |
| `stop(axis)` | 停止运动 |
| `quick_stop(axis)` | 快速停止 |
| `get_position(axis)` | 获取当前位置 |
| `get_velocity(axis)` | 获取当前速度 |
| `get_axis_status(axis)` | 获取轴状态 |

### 驱动器状态

基于 CiA402 标准的状态机:

```
Not ready to switch on
        ↓
Switch on disabled
        ↓ Shutdown
Ready to switch on
        ↓ Switch on
   Switched on
        ↓ Enable operation
Operation enabled ←→ Quick stop active
        ↓
      Fault
```

## 通信协议

### Modbus RTU 配置

- 默认波特率: 115200
- 数据位: 8
- 校验: 无
- 停止位: 1

### 支持的功能码

| 功能码 | 描述 |
|-------|-----|
| 0x03 | 读取保持寄存器 |
| 0x04 | 读取输入寄存器 |
| 0x06 | 写入单个寄存器 |
| 0x10 | 写入多个寄存器 |

## 开发

### 运行测试

```bash
# 使用 pytest
pytest tests/ -v

# 或使用简单测试
python -m pytest tests/
```

### 代码格式化

```bash
# 格式化
black .
isort .

# 检查
flake8
mypy servo_service/
```

## 许可证

MIT License

## 相关文档

- [需求文档](docs/requirements.md)
- [设计文档](docs/design.md)
- [API 参考](docs/api_reference.md)
- [编码规范](docs/coding_standards.md)
