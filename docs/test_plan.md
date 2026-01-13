# NiMotion 伺服电机控制系统 - 硬件集成测试计划

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | NiMotion 伺服电机控制系统 |
| 文档版本 | 1.0 |
| 创建日期 | 2026-01-09 |
| 适用硬件 | XYG321-A 三轴平台 + LMS-C12-24050 伺服电机 |

---

## 目录

1. [测试概述](#1-测试概述)
2. [测试环境](#2-测试环境)
3. [Layer 1: 串口通信测试](#3-layer-1-串口通信测试)
4. [Layer 2: Modbus RTU 协议测试](#4-layer-2-modbus-rtu-协议测试)
5. [Layer 3: 电机控制层测试](#5-layer-3-电机控制层测试)
6. [Layer 4: 高级 API 层测试](#6-layer-4-高级-api-层测试)
7. [Layer 5: 应用层 (GUI) 测试](#7-layer-5-应用层-gui-测试)
8. [集成测试](#8-集成测试)
9. [系统测试](#9-系统测试)
10. [性能测试](#10-性能测试)
11. [安全测试](#11-安全测试)
12. [测试检查清单](#12-测试检查清单)

---

## 1. 测试概述

### 1.1 测试目标

验证 NiMotion 伺服电机控制系统从底层串口通信到上层 GUI 应用的完整功能链路。

### 1.2 测试策略

采用自底向上 (Bottom-Up) 的测试策略：

```
Layer 5: 应用层 (GUI)          ← 最后测试
    ↑
Layer 4: 高级 API (ServoService)
    ↑
Layer 3: 电机控制 (Motor, StateMachine)
    ↑
Layer 2: Modbus RTU (ModbusClient)
    ↑
Layer 1: 串口通信 (SerialPort)  ← 首先测试
```

### 1.3 测试分类

| 类型 | 描述 | 是否需要硬件 |
|------|------|--------------|
| 单元测试 | 模块内部逻辑测试 | 否 |
| 集成测试 | 模块间接口测试 | 是 |
| 系统测试 | 完整功能验证 | 是 |
| 性能测试 | 响应时间、吞吐量 | 是 |

---

## 2. 测试环境

### 2.1 硬件要求

| 设备 | 规格 | 数量 |
|------|------|------|
| XYG321-A 三轴平台 | X/Y/Z 轴 | 1 套 |
| LMS-C12-24050 电机 | X轴: 200W, Y/Z轴: 100W | 3 台 |
| USB-RS485 转换器 | 支持 115200bps | 1 个 |
| 24V 直流电源 | ≥10A | 1 台 |
| 急停按钮 | 常闭触点 | 1 个 |

### 2.2 软件环境

```bash
# 操作系统
Linux Ubuntu 22.04+ / Windows 10+

# Python 版本
Python 3.9+

# 依赖包
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2.3 通信配置

| 参数 | 值 |
|------|-----|
| 波特率 | 115200 |
| 数据位 | 8 |
| 校验位 | 无 |
| 停止位 | 1 |
| 从站地址 | X=1, Y=2, Z=3 |

### 2.4 安全注意事项

> **警告**: 进行硬件测试前，请确保：
> - 急停按钮功能正常
> - 运动范围内无障碍物
> - 已了解各轴行程限制
> - 首次测试使用低速设置

---

## 3. Layer 1: 串口通信测试

### 3.1 测试目标

验证底层串口通信功能，确保能够正确打开/关闭串口、发送/接收数据。

### 3.2 前置条件

- USB-RS485 转换器已连接
- 伺服驱动器已上电
- 已知串口设备名称 (如 `/dev/ttyUSB0` 或 `COM3`)

### 3.3 测试用例

#### TC-L1-001: 串口扫描

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证系统能够扫描并列出可用串口 |
| **测试步骤** | 1. 连接 USB-RS485 转换器<br>2. 运行端口扫描<br>3. 检查返回结果 |
| **预期结果** | 返回包含目标串口的列表 |
| **测试代码** | 见下方 |

```python
from servo_service.serial_comm import PortScanner

def test_port_scanner():
    scanner = PortScanner()
    ports = scanner.scan_ports()

    print("发现的串口:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")

    assert len(ports) > 0, "未发现任何串口"
    # 检查目标串口是否存在
    devices = [p.device for p in ports]
    assert "/dev/ttyUSB0" in devices or "COM3" in devices
```

#### TC-L1-002: 串口打开/关闭

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证串口能够正常打开和关闭 |
| **测试步骤** | 1. 打开串口<br>2. 检查状态<br>3. 关闭串口<br>4. 检查状态 |
| **预期结果** | 串口状态正确切换 |

```python
from servo_service.serial_comm import SerialPort

def test_serial_open_close():
    port = SerialPort(port="/dev/ttyUSB0", baudrate=115200)

    # 测试打开
    assert not port.is_open
    port.open()
    assert port.is_open
    print(f"串口已打开: {port}")

    # 测试关闭
    port.close()
    assert not port.is_open
    print("串口已关闭")
```

#### TC-L1-003: 基本数据发送

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证数据能够通过串口发送 |
| **测试步骤** | 1. 打开串口<br>2. 发送测试数据<br>3. 检查返回字节数 |
| **预期结果** | 返回正确的发送字节数 |

```python
def test_serial_write():
    with SerialPort(port="/dev/ttyUSB0", baudrate=115200) as port:
        # 发送 Modbus 读取状态字请求
        # 从站地址=0x03, 功能码=0x03, 地址=0x0381, 数量=0x0001
        test_data = bytes([0x03, 0x03, 0x03, 0x81, 0x00, 0x01, 0x54, 0x58])

        bytes_written = port.write(test_data)
        assert bytes_written == len(test_data)
        print(f"发送 {bytes_written} 字节: {test_data.hex()}")
```

#### TC-L1-004: 数据接收

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证能够接收从站响应数据 |
| **测试步骤** | 1. 发送读取请求<br>2. 等待响应<br>3. 验证响应数据 |
| **预期结果** | 收到有效的 Modbus 响应帧 |

```python
def test_serial_read():
    with SerialPort(port="/dev/ttyUSB0", baudrate=115200, timeout=0.5) as port:
        # 发送读取状态字请求 (Z轴, 地址3)
        request = bytes([0x03, 0x03, 0x03, 0x81, 0x00, 0x01, 0x54, 0x58])
        port.write(request)

        # 读取响应 (预期: 从站地址 + 功能码 + 字节数 + 数据 + CRC = 7 字节)
        response = port.read_until(expected_length=7, timeout=0.5)

        print(f"收到响应: {response.hex()}")
        assert len(response) == 7, f"响应长度错误: {len(response)}"
        assert response[0] == 0x03, "从站地址不匹配"
        assert response[1] == 0x03, "功能码不匹配"
```

#### TC-L1-005: 超时处理

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证读取超时异常处理 |
| **测试步骤** | 1. 发送请求到不存在的从站<br>2. 等待超时 |
| **预期结果** | 抛出 ReadTimeoutError |

```python
from servo_service.serial_comm import ReadTimeoutError

def test_serial_timeout():
    with SerialPort(port="/dev/ttyUSB0", baudrate=115200, timeout=0.5) as port:
        # 发送请求到不存在的从站地址 (0xFF)
        request = bytes([0xFF, 0x03, 0x03, 0x81, 0x00, 0x01, 0x80, 0x14])
        port.write(request)

        try:
            response = port.read_until(expected_length=7, timeout=0.5)
            assert False, "应该抛出超时异常"
        except ReadTimeoutError as e:
            print(f"正确捕获超时异常: {e}")
```

#### TC-L1-006: 波特率配置

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证波特率设置功能 |
| **测试步骤** | 1. 使用不同波特率尝试通信<br>2. 验证只有正确波特率能通信 |
| **预期结果** | 只有 115200 能正常通信 |

```python
def test_baudrate_configuration():
    # 错误波特率 - 应该无法通信
    with SerialPort(port="/dev/ttyUSB0", baudrate=9600, timeout=0.3) as port:
        request = bytes([0x03, 0x03, 0x03, 0x81, 0x00, 0x01, 0x54, 0x58])
        port.write(request)
        response = port.read(7)
        assert len(response) == 0, "错误波特率不应收到响应"

    # 正确波特率 - 应该能通信
    with SerialPort(port="/dev/ttyUSB0", baudrate=115200, timeout=0.3) as port:
        port.write(request)
        response = port.read_until(7, timeout=0.3)
        assert len(response) == 7, "正确波特率应收到响应"
        print("波特率配置测试通过")
```

### 3.4 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-L1-001 | 串口扫描 | | □ 通过 □ 失败 | |
| TC-L1-002 | 串口打开/关闭 | | □ 通过 □ 失败 | |
| TC-L1-003 | 基本数据发送 | | □ 通过 □ 失败 | |
| TC-L1-004 | 数据接收 | | □ 通过 □ 失败 | |
| TC-L1-005 | 超时处理 | | □ 通过 □ 失败 | |
| TC-L1-006 | 波特率配置 | | □ 通过 □ 失败 | |

---

## 4. Layer 2: Modbus RTU 协议测试

### 4.1 测试目标

验证 Modbus RTU 协议层的帧构建、CRC 校验、请求/响应处理功能。

### 4.2 前置条件

- Layer 1 测试全部通过
- 串口通信正常

### 4.3 测试用例

#### TC-L2-001: CRC 校验计算

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 CRC-16 计算正确性 |
| **测试步骤** | 使用已知数据验证 CRC 计算 |
| **预期结果** | CRC 值与标准值匹配 |

```python
from servo_service.modbus_rtu import calculate_crc, verify_crc, append_crc

def test_crc_calculation():
    # 标准测试向量: 从站=0x01, FC=0x03, 地址=0x0000, 数量=0x0001
    data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01])

    crc = calculate_crc(data)
    print(f"CRC 值: 0x{crc:04X}")
    assert crc == 0x0A84, f"CRC 计算错误: 0x{crc:04X}"

    # 验证追加 CRC 后的帧
    frame = append_crc(data)
    assert verify_crc(frame), "CRC 验证失败"
    print("CRC 校验测试通过")
```

#### TC-L2-002: 读取保持寄存器 (FC=0x03)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证读取保持寄存器功能 |
| **测试步骤** | 1. 构建读取请求<br>2. 发送并接收响应<br>3. 解析响应数据 |
| **预期结果** | 正确读取状态字寄存器值 |

```python
from servo_service.modbus_rtu import ModbusClient

def test_read_holding_registers():
    client = ModbusClient(timeout=0.5, retries=3)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 读取 Z 轴 (从站3) 状态字 (地址 0x0381)
        values = client.read_holding_registers(
            slave_id=3,
            start_address=0x0381,
            quantity=1
        )

        status_word = values[0]
        print(f"状态字: 0x{status_word:04X}")

        # 状态字应该是有效值
        assert 0x0000 <= status_word <= 0xFFFF
        print("读取保持寄存器测试通过")

    finally:
        client.disconnect()
```

#### TC-L2-003: 读取输入寄存器 (FC=0x04)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证读取输入寄存器功能 |
| **测试步骤** | 读取实际位置值 |
| **预期结果** | 返回有效的位置数据 |

```python
def test_read_input_registers():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 读取实际位置 (32位, 2个寄存器)
        values = client.read_input_registers(
            slave_id=3,
            start_address=0x03A7,  # POSITION_ACTUAL_VALUE
            quantity=2
        )

        position = (values[0] << 16) | values[1]
        print(f"实际位置: {position} pulses")

    finally:
        client.disconnect()
```

#### TC-L2-004: 写入单个寄存器 (FC=0x06)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证写入单个寄存器功能 |
| **测试步骤** | 1. 写入操作模式寄存器<br>2. 读回验证 |
| **预期结果** | 写入值与读回值一致 |

```python
def test_write_single_register():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 写入操作模式 (6060h -> 0x03C3)
        # 模式 1 = 轮廓位置模式
        client.write_single_register(
            slave_id=3,
            address=0x03C3,
            value=1
        )
        print("写入操作模式: 1 (PP)")

        # 读回验证
        values = client.read_holding_registers(3, 0x03C4, 1)  # 模式显示
        print(f"读回操作模式: {values[0]}")
        # 注意: 模式显示可能需要一点时间更新

    finally:
        client.disconnect()
```

#### TC-L2-005: 写入多个寄存器 (FC=0x10)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证写入多个寄存器功能 |
| **测试步骤** | 写入 32 位目标位置 (2个寄存器) |
| **预期结果** | 写入成功，无异常 |

```python
def test_write_multiple_registers():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 写入目标位置 (32位 = 2个寄存器)
        target_position = 10000  # 10000 pulses
        high_word = (target_position >> 16) & 0xFFFF
        low_word = target_position & 0xFFFF

        client.write_multiple_registers(
            slave_id=3,
            start_address=0x03BD,  # TARGET_POSITION
            values=[high_word, low_word]
        )
        print(f"写入目标位置: {target_position} pulses")

    finally:
        client.disconnect()
```

#### TC-L2-006: Modbus 异常响应处理

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证异常响应处理 |
| **测试步骤** | 读取无效寄存器地址 |
| **预期结果** | 捕获 ModbusExceptionResponse |

```python
from servo_service.modbus_rtu import ModbusExceptionResponse

def test_modbus_exception():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 读取无效地址
        try:
            client.read_holding_registers(
                slave_id=3,
                start_address=0xFFFF,  # 无效地址
                quantity=1
            )
            assert False, "应该抛出异常"
        except ModbusExceptionResponse as e:
            print(f"正确捕获 Modbus 异常: {e}")

    finally:
        client.disconnect()
```

#### TC-L2-007: 通信重试机制

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证通信失败重试机制 |
| **测试步骤** | 1. 设置较短超时<br>2. 验证重试次数 |
| **预期结果** | 重试后能恢复通信 |

```python
def test_retry_mechanism():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    client = ModbusClient(timeout=0.05, retries=3)  # 很短的超时
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        # 这可能需要重试
        values = client.read_holding_registers(3, 0x0381, 1)
        print(f"经过重试后成功读取: 0x{values[0]:04X}")

    finally:
        client.disconnect()
```

### 4.4 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-L2-001 | CRC 校验计算 | | □ 通过 □ 失败 | |
| TC-L2-002 | 读取保持寄存器 | | □ 通过 □ 失败 | |
| TC-L2-003 | 读取输入寄存器 | | □ 通过 □ 失败 | |
| TC-L2-004 | 写入单个寄存器 | | □ 通过 □ 失败 | |
| TC-L2-005 | 写入多个寄存器 | | □ 通过 □ 失败 | |
| TC-L2-006 | 异常响应处理 | | □ 通过 □ 失败 | |
| TC-L2-007 | 通信重试机制 | | □ 通过 □ 失败 | |

---

## 5. Layer 3: 电机控制层测试

### 5.1 测试目标

验证 CiA402 状态机、电机使能/禁用、运动控制等核心功能。

### 5.2 前置条件

- Layer 1, 2 测试全部通过
- 电机已正确接线
- 急停按钮就绪

### 5.3 测试用例

#### TC-L3-001: 读取驱动器状态

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证状态字解析功能 |
| **测试步骤** | 读取并解析状态字 |
| **预期结果** | 正确识别驱动器状态 |

```python
from servo_service.modbus_rtu import ModbusClient
from servo_service.motor_control import Motor, DriveState

def test_read_drive_state():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        state = motor.get_state()
        print(f"驱动器状态: {state.value}")

        # 验证状态有效性
        assert state in DriveState, f"无效状态: {state}"

        # 上电后通常是 SWITCH_ON_DISABLED 状态
        print(f"状态名称: {state.name}")

    finally:
        client.disconnect()
```

#### TC-L3-002: 读取完整电机状态

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证完整状态读取 |
| **测试步骤** | 获取 MotorStatus 对象 |
| **预期结果** | 返回有效的状态数据 |

```python
def test_read_motor_status():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)
        status = motor.get_status()

        print("=== 电机状态 ===")
        print(f"  驱动器状态: {status.state.value}")
        print(f"  状态字: 0x{status.status_word:04X}")
        print(f"  当前位置: {status.position} pulses")
        print(f"  当前速度: {status.velocity}")
        print(f"  当前转矩: {status.torque}")
        print(f"  操作模式: {status.operation_mode}")
        print(f"  目标到达: {status.is_target_reached}")
        print(f"  故障: {status.is_fault}")
        print(f"  错误码: 0x{status.error_code:04X}")

    finally:
        client.disconnect()
```

#### TC-L3-003: 电机使能

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证电机使能流程 |
| **测试步骤** | 执行使能操作，观察状态转换 |
| **预期结果** | 成功进入 OPERATION_ENABLED 状态 |

> **警告**: 使能后电机可能会抱死，请确保轴可以自由移动或有足够力矩

```python
def test_motor_enable():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        print(f"使能前状态: {motor.get_state().value}")

        # 使能电机
        motor.enable(timeout=5.0)

        state = motor.get_state()
        print(f"使能后状态: {state.value}")
        assert state == DriveState.OPERATION_ENABLED

        print("电机使能测试通过")

    finally:
        # 确保禁用电机
        motor.disable()
        client.disconnect()
```

#### TC-L3-004: 电机禁用

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证电机禁用功能 |
| **测试步骤** | 使能后执行禁用 |
| **预期结果** | 成功进入 SWITCHED_ON 状态 |

```python
def test_motor_disable():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        # 先使能
        motor.enable()
        assert motor.get_state() == DriveState.OPERATION_ENABLED

        # 禁用
        motor.disable()
        state = motor.get_state()
        print(f"禁用后状态: {state.value}")
        assert state == DriveState.SWITCHED_ON

    finally:
        client.disconnect()
```

#### TC-L3-005: 快速停止

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证快速停止功能 |
| **测试步骤** | 使能后执行快速停止 |
| **预期结果** | 进入 QUICK_STOP_ACTIVE 状态 |

```python
def test_quick_stop():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        motor.enable()
        print("电机已使能")

        # 快速停止
        motor.quick_stop()

        import time
        time.sleep(0.1)

        state = motor.get_state()
        print(f"快速停止后状态: {state.value}")
        # 状态可能是 QUICK_STOP_ACTIVE 或 SWITCH_ON_DISABLED

    finally:
        client.disconnect()
```

#### TC-L3-006: 故障复位

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证故障复位功能 |
| **测试步骤** | 模拟故障后执行复位 |
| **预期结果** | 成功清除故障 |

```python
def test_fault_reset():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        state = motor.get_state()
        if state == DriveState.FAULT:
            print("检测到故障状态，执行复位")
            motor.fault_reset()

            state = motor.get_state()
            print(f"复位后状态: {state.value}")
            assert state != DriveState.FAULT
        else:
            print(f"当前状态: {state.value} (无故障，跳过测试)")

    finally:
        client.disconnect()
```

#### TC-L3-007: 绝对位置移动

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证绝对位置移动功能 |
| **测试步骤** | 移动到指定位置 |
| **预期结果** | 电机移动到目标位置 |

> **警告**: 确保目标位置在安全范围内

```python
def test_absolute_move():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)

        # 使能
        motor.enable()

        # 设置低速以确保安全
        motor.set_profile_velocity(10000)  # 较低速度

        # 读取当前位置
        start_pos = motor.read_position()
        print(f"起始位置: {start_pos}")

        # 移动到目标位置 (小距离测试)
        target_pos = start_pos + 1000
        motor.move_absolute(target_pos, wait=True, timeout=10.0)

        # 验证位置
        end_pos = motor.read_position()
        print(f"结束位置: {end_pos}")

        error = abs(end_pos - target_pos)
        assert error < 10, f"位置误差过大: {error}"

    finally:
        motor.disable()
        client.disconnect()
```

#### TC-L3-008: 相对位置移动

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证相对位置移动功能 |
| **测试步骤** | 执行相对移动 |
| **预期结果** | 移动指定距离 |

```python
def test_relative_move():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)
        motor.enable()
        motor.set_profile_velocity(10000)

        start_pos = motor.read_position()
        print(f"起始位置: {start_pos}")

        # 相对移动 500 pulses
        distance = 500
        motor.move_relative(distance, wait=True, timeout=10.0)

        end_pos = motor.read_position()
        print(f"结束位置: {end_pos}")

        actual_distance = end_pos - start_pos
        error = abs(actual_distance - distance)
        print(f"实际移动: {actual_distance}, 误差: {error}")
        assert error < 10

    finally:
        motor.disable()
        client.disconnect()
```

#### TC-L3-009: 速度模式运行

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证速度模式 (点动) |
| **测试步骤** | 以指定速度运行一段时间后停止 |
| **预期结果** | 电机按指定速度运行 |

```python
import time

def test_velocity_mode():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)
        motor.enable()

        # 以较低速度运行
        velocity = 5000  # pulses/s
        motor.run_velocity(velocity)

        print(f"速度模式运行: {velocity} pulses/s")

        # 运行 1 秒
        time.sleep(1.0)

        # 读取实际速度
        actual_vel = motor.read_velocity()
        print(f"实际速度: {actual_vel}")

        # 停止
        motor.stop()
        print("已停止")

    finally:
        motor.disable()
        client.disconnect()
```

#### TC-L3-010: 回零操作

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证回零功能 |
| **测试步骤** | 执行回零操作 |
| **预期结果** | 成功完成回零 |

> **警告**: 回零会移动电机到机械原点，确保行程内无障碍

```python
from servo_service.motor_control import HomingMethod

def test_homing():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    try:
        motor = Motor(modbus_client=client, slave_id=3)
        motor.enable()

        # 设置回零速度
        motor.set_homing_speeds(
            high_speed=10000,   # 搜索开关速度
            low_speed=2000,     # 搜索零点速度
            acceleration=5000
        )

        print("开始回零...")
        motor.home(method=HomingMethod.NEGATIVE_LIMIT_SWITCH, wait=True, timeout=60.0)

        print("回零完成")
        position = motor.read_position()
        print(f"回零后位置: {position}")

    finally:
        motor.disable()
        client.disconnect()
```

### 5.4 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-L3-001 | 读取驱动器状态 | | □ 通过 □ 失败 | |
| TC-L3-002 | 读取完整状态 | | □ 通过 □ 失败 | |
| TC-L3-003 | 电机使能 | | □ 通过 □ 失败 | |
| TC-L3-004 | 电机禁用 | | □ 通过 □ 失败 | |
| TC-L3-005 | 快速停止 | | □ 通过 □ 失败 | |
| TC-L3-006 | 故障复位 | | □ 通过 □ 失败 | |
| TC-L3-007 | 绝对位置移动 | | □ 通过 □ 失败 | |
| TC-L3-008 | 相对位置移动 | | □ 通过 □ 失败 | |
| TC-L3-009 | 速度模式运行 | | □ 通过 □ 失败 | |
| TC-L3-010 | 回零操作 | | □ 通过 □ 失败 | |

---

## 6. Layer 4: 高级 API 层测试

### 6.1 测试目标

验证 ServoService 高级 API，包括单位转换、多轴管理、安全检查等功能。

### 6.2 前置条件

- Layer 1-3 测试全部通过
- 了解各轴行程范围

### 6.3 测试用例

#### TC-L4-001: 连接管理

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 ServoService 连接功能 |
| **测试步骤** | 连接、断开伺服系统 |
| **预期结果** | 正确管理连接状态 |

```python
from servo_service import ServoService

def test_service_connection():
    service = ServoService()

    assert not service.is_connected

    service.connect(port="/dev/ttyUSB0", baudrate=115200)
    assert service.is_connected
    print("服务已连接")

    service.disconnect()
    assert not service.is_connected
    print("服务已断开")
```

#### TC-L4-002: 上下文管理器

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 with 语句使用 |
| **预期结果** | 退出时自动断开 |

```python
def test_context_manager():
    with ServoService(port="/dev/ttyUSB0") as service:
        assert service.is_connected
        print(f"连接状态: {service}")

    # 退出后应自动断开
    print("已自动断开")
```

#### TC-L4-003: 轴选择

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证多轴选择功能 |
| **测试步骤** | 切换不同轴并验证 |
| **预期结果** | 正确切换当前轴 |

```python
from servo_service import AxisName

def test_axis_selection():
    with ServoService(port="/dev/ttyUSB0") as service:
        # 默认是 Z 轴
        assert service.current_axis == AxisName.Z

        # 切换到 X 轴
        service.current_axis = AxisName.X
        assert service.current_axis == AxisName.X

        # 切换到 Y 轴
        service.current_axis = AxisName.Y
        assert service.current_axis == AxisName.Y

        print("轴选择测试通过")
```

#### TC-L4-004: 获取轴状态

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证轴状态获取 |
| **预期结果** | 返回正确的状态数据 |

```python
def test_axis_status():
    with ServoService(port="/dev/ttyUSB0") as service:
        # 获取所有轴状态
        all_status = service.get_all_axis_status()

        for axis, status in all_status.items():
            print(f"=== {axis.value} 轴 ===")
            print(f"  连接: {status.connected}")
            print(f"  状态: {status.state.value}")
            print(f"  位置: {status.position_mm:.3f} mm")
            print(f"  速度: {status.velocity_mm_s:.3f} mm/s")
            print(f"  使能: {status.is_enabled}")
            print(f"  故障: {status.is_fault}")
```

#### TC-L4-005: 单位转换 - 位置

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 mm 到 pulses 转换 |
| **预期结果** | 转换结果正确 |

```python
def test_position_unit_conversion():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z
        config = service.get_axis_config()

        # 测试转换
        test_mm = 10.0
        pulses = config.mm_to_pulses(test_mm)
        back_mm = config.pulses_to_mm(pulses)

        print(f"{test_mm} mm -> {pulses} pulses -> {back_mm} mm")

        assert abs(back_mm - test_mm) < 0.001, "转换误差过大"
```

#### TC-L4-006: 移动到位置 (mm)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证以 mm 为单位的移动 |
| **预期结果** | 移动到正确位置 |

```python
def test_move_to_mm():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z
        service.enable()

        # 获取当前位置
        start_pos = service.get_position()
        print(f"起始位置: {start_pos:.3f} mm")

        # 移动 5mm
        target_pos = start_pos + 5.0
        service.move_to(target_pos, velocity_mm_s=50.0)

        end_pos = service.get_position()
        print(f"结束位置: {end_pos:.3f} mm")

        error = abs(end_pos - target_pos)
        print(f"位置误差: {error:.3f} mm")
        assert error < 0.1, f"位置误差过大: {error}"

        service.disable()
```

#### TC-L4-007: 相对移动 (mm)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证以 mm 为单位的相对移动 |
| **预期结果** | 移动正确距离 |

```python
def test_move_by_mm():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z
        service.enable()

        start_pos = service.get_position()

        # 相对移动 3mm
        distance = 3.0
        service.move_by(distance, velocity_mm_s=50.0)

        end_pos = service.get_position()
        actual_distance = end_pos - start_pos

        print(f"目标距离: {distance} mm, 实际距离: {actual_distance:.3f} mm")
        assert abs(actual_distance - distance) < 0.1

        service.disable()
```

#### TC-L4-008: 点动控制

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证点动功能 |
| **预期结果** | 以指定速度运行 |

```python
import time

def test_jog():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z
        service.enable()

        # 正向点动
        service.jog(velocity_mm_s=20.0)
        print("正向点动 20 mm/s")
        time.sleep(0.5)

        # 停止
        service.stop()
        print("停止")
        time.sleep(0.2)

        # 反向点动
        service.jog(velocity_mm_s=-20.0)
        print("反向点动 -20 mm/s")
        time.sleep(0.5)

        service.stop()
        service.disable()
```

#### TC-L4-009: 行程限制检查

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证软件行程限制 |
| **预期结果** | 超出行程时报错 |

```python
def test_stroke_limit():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z
        config = service.get_axis_config()

        print(f"Z轴行程: {config.stroke_min} - {config.stroke_max} mm")

        # 尝试移动到超出范围的位置
        try:
            service.enable()
            service.move_to(config.stroke_max + 10.0)
            assert False, "应该抛出异常"
        except ValueError as e:
            print(f"正确捕获行程限制: {e}")
        finally:
            service.disable()
```

#### TC-L4-010: 多轴操作

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证多轴切换操作 |
| **预期结果** | 各轴独立控制正常 |

```python
def test_multi_axis():
    with ServoService(port="/dev/ttyUSB0") as service:
        # 获取所有轴状态
        for axis in [AxisName.X, AxisName.Y, AxisName.Z]:
            service.current_axis = axis
            status = service.get_axis_status()
            print(f"{axis.value}轴: 位置={status.position_mm:.2f}mm, 状态={status.state.value}")

        # 分别使能各轴
        for axis in [AxisName.X, AxisName.Y, AxisName.Z]:
            service.enable(axis)
            print(f"{axis.value}轴已使能")

        # 禁用所有轴
        service.disable_all()
        print("所有轴已禁用")
```

#### TC-L4-011: 电机参数初始化

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证电机参数初始化功能 |
| **测试步骤** | 1. 连接电机<br>2. 调用 initialize_motor_parameters()<br>3. 验证参数已写入驱动器 |
| **预期结果** | 回零超时、DI配置、堵转参数正确写入 |

> **重要**: 回零超时参数默认值为 0ms，会导致回零立即超时，必须初始化为合理值 (如 60000ms)

```python
def test_motor_initialization():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.current_axis = AxisName.Z

        # 执行初始化
        service.initialize_motor_parameters()

        # 验证参数
        motor = service.get_motor()
        modbus = service.get_modbus_client()
        slave_id = 3

        # 验证回零超时 (应为 60000ms)
        timeout = modbus.read_register(slave_id, 0x012E)
        print(f"回零超时: {timeout}ms")
        assert timeout == 60000, f"回零超时错误: {timeout}"

        # 验证 DI2 (负限位)
        di2_func = modbus.read_register(slave_id, 0x00D7)
        assert di2_func == 15, f"DI2功能错误: {di2_func}"

        # 验证 DI3 (正限位)
        di3_func = modbus.read_register(slave_id, 0x00D9)
        assert di3_func == 14, f"DI3功能错误: {di3_func}"

        print("电机参数初始化测试通过")
```

**测试脚本:**
```bash
python3 tests/integration/test_motor_initialization.py --axis Z
```

### 6.4 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-L4-001 | 连接管理 | | □ 通过 □ 失败 | |
| TC-L4-002 | 上下文管理器 | | □ 通过 □ 失败 | |
| TC-L4-003 | 轴选择 | | □ 通过 □ 失败 | |
| TC-L4-004 | 获取轴状态 | | □ 通过 □ 失败 | |
| TC-L4-005 | 单位转换 | | □ 通过 □ 失败 | |
| TC-L4-006 | 移动到位置 | | □ 通过 □ 失败 | |
| TC-L4-007 | 相对移动 | | □ 通过 □ 失败 | |
| TC-L4-008 | 点动控制 | | □ 通过 □ 失败 | |
| TC-L4-009 | 行程限制检查 | | □ 通过 □ 失败 | |
| TC-L4-010 | 多轴操作 | | □ 通过 □ 失败 | |

---

## 7. Layer 5: 应用层 (GUI) 测试

### 7.1 测试目标

验证 PyQt5 GUI 应用的功能完整性和用户交互。

### 7.2 前置条件

- Layer 1-4 测试全部通过
- 显示器正常
- PyQt5 已安装

### 7.3 测试用例

#### TC-L5-001: 应用启动

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 GUI 应用能正常启动 |
| **测试步骤** | 运行 `python app/main.py` |
| **预期结果** | 主窗口正常显示 |

```bash
# 启动命令
python app/main.py
```

**检查项:**
- [ ] 主窗口正常显示
- [ ] 窗口标题正确
- [ ] 所有面板正常加载
- [ ] 无错误消息

#### TC-L5-002: 串口连接面板

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 查看串口下拉列表 | 显示可用串口 |
| 2. 点击"刷新"按钮 | 更新串口列表 |
| 3. 选择目标串口 | 串口被选中 |
| 4. 选择波特率 | 默认 115200 |
| 5. 点击"连接"按钮 | 状态变为已连接 |
| 6. 点击"断开"按钮 | 状态变为已断开 |

#### TC-L5-003: 轴选择面板

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 查看轴选择区域 | 显示 X/Y/Z 三个选项 |
| 2. 默认选中 Z 轴 | Z 轴被选中 |
| 3. 点击 X 轴 | 切换到 X 轴，显示 X 轴信息 |
| 4. 点击 Y 轴 | 切换到 Y 轴，显示 Y 轴信息 |
| 5. 检查轴信息显示 | 显示从站地址、型号、行程等 |

#### TC-L5-004: 状态监控面板

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 连接后查看状态 | 状态定时刷新 |
| 2. 检查位置显示 | 显示当前位置 (mm) |
| 3. 检查速度显示 | 显示当前速度 (mm/s) |
| 4. 检查状态指示灯 | 正确显示使能/故障/回零/到位状态 |
| 5. 检查行程进度条 | 正确显示当前位置相对行程 |

#### TC-L5-005: 运动控制面板 - 使能/禁用

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 点击"使能"按钮 | 电机使能，指示灯变绿 |
| 2. 点击"禁用"按钮 | 电机禁用，指示灯变灰 |
| 3. 点击"急停"按钮 | 电机快速停止 |
| 4. 如有故障，点击"复位" | 故障清除 |

#### TC-L5-006: 运动控制面板 - 点动

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 使能电机 | 电机已使能 |
| 2. 设置点动速度 | 速度值更新 |
| 3. 按住"正向"按钮 | 电机正向移动 |
| 4. 释放按钮 | 电机停止 |
| 5. 按住"反向"按钮 | 电机反向移动 |
| 6. 释放按钮 | 电机停止 |

#### TC-L5-007: 运动控制面板 - 位置移动

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 输入目标位置 | 位置值被接受 |
| 2. 设置移动速度 | 速度值更新 |
| 3. 点击"移动到"按钮 | 电机移动到目标位置 |
| 4. 输入相对距离 | 距离值被接受 |
| 5. 点击"相对移动"按钮 | 电机移动指定距离 |

#### TC-L5-008: 运动控制面板 - 回零

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 选择回零方式 | 回零方式被选中 |
| 2. 点击"开始回零"按钮 | 电机开始回零 |
| 3. 等待回零完成 | 回零指示灯变绿 |
| 4. 点击"设为原点"按钮 | 当前位置设为 0 |

#### TC-L5-009: 参数设置面板

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 输入速度参数 | 参数值被接受 |
| 2. 输入加速度参数 | 参数值被接受 |
| 3. 输入减速度参数 | 参数值被接受 |
| 4. 点击"应用"按钮 | 参数写入电机 |
| 5. 点击"读取"按钮 | 显示当前参数值 |

#### TC-L5-010: 菜单功能

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 文件 → 退出 | 应用正常退出 |
| 2. 帮助 → 关于 | 显示关于对话框 |

#### TC-L5-011: 视图切换

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 默认视图 | 显示电机控制视图 |
| 2. 点击 视图 → Modbus 调试 | 切换到 Modbus 调试视图 |
| 3. 按 Ctrl+1 | 切换到电机控制视图 |
| 4. 按 Ctrl+2 | 切换到 Modbus 调试视图 |
| 5. 左侧面板在两个视图中 | 连接面板、轴选择面板、状态面板保持显示 |
| 6. 状态栏更新 | 显示当前视图名称 |

#### TC-L5-012: Modbus 调试面板 - 快捷操作

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 连接电机后切换到 Modbus 调试视图 | 调试面板可用 |
| 2. 点击"状态字"快捷按钮 | 读取并显示状态字值 |
| 3. 点击"位置"快捷按钮 | 读取并显示 32 位位置值 |
| 4. 点击"速度"快捷按钮 | 读取并显示 32 位速度值 |
| 5. 点击"错误码"快捷按钮 | 读取并显示错误码 |
| 6. 修改从站地址 | 读取目标从站的寄存器 |

#### TC-L5-013: Modbus 调试面板 - 手动发送

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 选择功能码 0x03 (读保持寄存器) | 功能码选中 |
| 2. 输入起始地址 0x0381 | 地址输入正确 |
| 3. 输入数量 1 | 数量输入正确 |
| 4. 查看帧预览 | 显示完整的 Modbus 帧 (含 CRC) |
| 5. 点击"发送"按钮 | 发送请求并显示响应 |
| 6. 选择功能码 0x06 (写单寄存器) | 功能码切换 |
| 7. 输入地址和数据 | 输入正确 |
| 8. 点击"发送"按钮 | 写入成功并显示响应 |

#### TC-L5-014: Modbus 调试面板 - 通信日志

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 执行读取操作 | 日志显示 TX 帧 (蓝色) |
| 2. 收到响应 | 日志显示 RX 帧 (绿色) |
| 3. 发送到无效地址 | 日志显示错误 (红色) |
| 4. 点击"清空"按钮 | 日志清空 |
| 5. 检查时间戳 | 每条日志带时间戳 |
| 6. 检查帧解析 | 显示寄存器名称和数值 |

#### TC-L5-015: Modbus 调试面板 - 统计信息

| 测试步骤 | 预期结果 |
|----------|----------|
| 1. 执行多次读取操作 | 发送计数增加 |
| 2. 收到响应 | 接收计数增加 |
| 3. 模拟通信错误 | 错误计数增加 |
| 4. 检查成功率 | 显示正确的成功率百分比 |

### 7.4 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-L5-001 | 应用启动 | | □ 通过 □ 失败 | |
| TC-L5-002 | 串口连接面板 | | □ 通过 □ 失败 | |
| TC-L5-003 | 轴选择面板 | | □ 通过 □ 失败 | |
| TC-L5-004 | 状态监控面板 | | □ 通过 □ 失败 | |
| TC-L5-005 | 使能/禁用 | | □ 通过 □ 失败 | |
| TC-L5-006 | 点动控制 | | □ 通过 □ 失败 | |
| TC-L5-007 | 位置移动 | | □ 通过 □ 失败 | |
| TC-L5-008 | 回零操作 | | □ 通过 □ 失败 | |
| TC-L5-009 | 参数设置 | | □ 通过 □ 失败 | |
| TC-L5-010 | 菜单功能 | | □ 通过 □ 失败 | |
| TC-L5-011 | 视图切换 | | □ 通过 □ 失败 | |
| TC-L5-012 | Modbus 快捷操作 | | □ 通过 □ 失败 | |
| TC-L5-013 | Modbus 手动发送 | | □ 通过 □ 失败 | |
| TC-L5-014 | Modbus 通信日志 | | □ 通过 □ 失败 | |
| TC-L5-015 | Modbus 统计信息 | | □ 通过 □ 失败 | |

---

## 8. 集成测试

### 8.1 测试目标

验证各层之间的接口和数据流是否正确。

### 8.2 测试用例

#### TC-INT-001: 完整通信链路

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 GUI → Service → Motor → Modbus → Serial 完整链路 |
| **测试步骤** | 通过 GUI 执行操作，验证底层通信 |
| **预期结果** | 数据正确传递到电机 |

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 通过 DEBUG 日志观察完整通信链路
```

#### TC-INT-002: 多轴协同

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证多轴依次操作 |
| **测试步骤** | 依次操作 X/Y/Z 轴 |
| **预期结果** | 各轴独立正常工作 |

```python
def test_multi_axis_coordination():
    with ServoService(port="/dev/ttyUSB0") as service:
        # 依次使能各轴
        for axis in [AxisName.X, AxisName.Y, AxisName.Z]:
            service.enable(axis)

        # 依次移动各轴
        for axis in [AxisName.X, AxisName.Y, AxisName.Z]:
            service.current_axis = axis
            pos = service.get_position()
            service.move_to(pos + 5.0, velocity_mm_s=50.0)

        # 禁用所有轴
        service.disable_all()
```

#### TC-INT-003: 异常恢复

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证故障后的恢复流程 |
| **测试步骤** | 触发故障 → 复位 → 恢复操作 |
| **预期结果** | 系统正常恢复 |

#### TC-INT-004: 连接中断恢复

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证通信中断后的处理 |
| **测试步骤** | 拔插 USB 线 → 重新连接 |
| **预期结果** | 正确处理断开，可重新连接 |

### 8.3 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-INT-001 | 完整通信链路 | | □ 通过 □ 失败 | |
| TC-INT-002 | 多轴协同 | | □ 通过 □ 失败 | |
| TC-INT-003 | 异常恢复 | | □ 通过 □ 失败 | |
| TC-INT-004 | 连接中断恢复 | | □ 通过 □ 失败 | |

---

## 9. 系统测试

### 9.1 测试目标

验证系统在实际工作条件下的完整功能。

### 9.2 测试用例

#### TC-SYS-001: 完整工作流程

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证典型工作流程 |
| **测试步骤** | 连接 → 使能 → 回零 → 移动 → 禁用 → 断开 |
| **预期结果** | 完整流程正常执行 |

```python
def test_complete_workflow():
    """完整工作流程测试"""
    with ServoService(port="/dev/ttyUSB0") as service:
        # 1. 使能 Z 轴
        service.current_axis = AxisName.Z
        service.enable()
        print("Z轴已使能")

        # 2. 执行回零
        service.home()
        print("回零完成")

        # 3. 移动到多个位置
        positions = [10.0, 30.0, 20.0, 0.0]
        for pos in positions:
            service.move_to(pos, velocity_mm_s=100.0)
            print(f"移动到 {pos}mm")

        # 4. 禁用
        service.disable()
        print("已禁用")
```

#### TC-SYS-002: 长时间运行

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证系统稳定性 |
| **测试步骤** | 连续运行 1 小时，重复执行移动 |
| **预期结果** | 无错误、无内存泄漏 |

```python
import time

def test_long_running():
    """长时间运行测试"""
    with ServoService(port="/dev/ttyUSB0") as service:
        service.enable()
        service.home()

        start_time = time.time()
        cycle_count = 0

        while time.time() - start_time < 3600:  # 1 小时
            # 往返移动
            service.move_to(10.0, velocity_mm_s=100.0)
            service.move_to(0.0, velocity_mm_s=100.0)

            cycle_count += 1
            if cycle_count % 100 == 0:
                print(f"已完成 {cycle_count} 个循环")

        print(f"测试完成，共 {cycle_count} 个循环")
        service.disable()
```

#### TC-SYS-003: 边界条件

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证行程边界行为 |
| **测试步骤** | 移动到行程边界位置 |
| **预期结果** | 边界位置可达，限位正常 |

#### TC-SYS-004: 急停功能

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证急停响应 |
| **测试步骤** | 运动中触发急停 |
| **预期结果** | 立即停止，可恢复 |

### 9.3 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-SYS-001 | 完整工作流程 | | □ 通过 □ 失败 | |
| TC-SYS-002 | 长时间运行 | | □ 通过 □ 失败 | |
| TC-SYS-003 | 边界条件 | | □ 通过 □ 失败 | |
| TC-SYS-004 | 急停功能 | | □ 通过 □ 失败 | |

---

## 10. 性能测试

### 10.1 测试目标

验证系统性能指标是否满足要求。

### 10.2 测试用例

#### TC-PERF-001: 通信响应时间

| 项目 | 内容 |
|------|------|
| **测试目的** | 测量 Modbus 请求响应时间 |
| **测试方法** | 发送 1000 次读取请求，统计响应时间 |
| **合格标准** | 平均响应时间 < 10ms |

```python
import time
import statistics

def test_response_time():
    client = ModbusClient(timeout=0.5)
    client.connect(port="/dev/ttyUSB0", baudrate=115200)

    times = []
    for i in range(1000):
        start = time.perf_counter()
        client.read_holding_registers(3, 0x0381, 1)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # 转换为毫秒

    print(f"平均响应时间: {statistics.mean(times):.2f} ms")
    print(f"最小响应时间: {min(times):.2f} ms")
    print(f"最大响应时间: {max(times):.2f} ms")
    print(f"标准差: {statistics.stdev(times):.2f} ms")

    client.disconnect()
```

#### TC-PERF-002: 状态更新频率

| 项目 | 内容 |
|------|------|
| **测试目的** | 测量状态读取频率 |
| **测试方法** | 连续读取状态，统计频率 |
| **合格标准** | 状态更新 > 50Hz |

```python
def test_status_update_rate():
    with ServoService(port="/dev/ttyUSB0") as service:
        start = time.perf_counter()
        count = 0

        while time.perf_counter() - start < 10:  # 测试 10 秒
            service.get_axis_status()
            count += 1

        rate = count / 10
        print(f"状态更新频率: {rate:.1f} Hz")
        assert rate > 50, f"更新频率过低: {rate}"
```

#### TC-PERF-003: 定位精度

| 项目 | 内容 |
|------|------|
| **测试目的** | 测量定位精度 |
| **测试方法** | 移动到多个位置，测量误差 |
| **合格标准** | 定位精度 < 0.02mm |

```python
def test_positioning_accuracy():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.enable()
        service.home()

        errors = []
        targets = [10.0, 20.0, 30.0, 40.0, 50.0]

        for target in targets:
            service.move_to(target, velocity_mm_s=50.0)
            time.sleep(0.5)  # 等待稳定
            actual = service.get_position()
            error = abs(actual - target)
            errors.append(error)
            print(f"目标: {target}mm, 实际: {actual:.4f}mm, 误差: {error:.4f}mm")

        max_error = max(errors)
        avg_error = sum(errors) / len(errors)
        print(f"最大误差: {max_error:.4f}mm, 平均误差: {avg_error:.4f}mm")

        service.disable()
```

#### TC-PERF-004: 重复定位精度

| 项目 | 内容 |
|------|------|
| **测试目的** | 测量重复定位精度 |
| **测试方法** | 反复移动到同一位置，测量偏差 |
| **合格标准** | 重复定位精度 < 0.01mm |

```python
def test_repeat_accuracy():
    with ServoService(port="/dev/ttyUSB0") as service:
        service.enable()
        service.home()

        target = 25.0
        positions = []

        for i in range(20):
            service.move_to(0.0, velocity_mm_s=100.0)
            service.move_to(target, velocity_mm_s=100.0)
            time.sleep(0.2)
            positions.append(service.get_position())

        mean_pos = statistics.mean(positions)
        std_dev = statistics.stdev(positions)

        print(f"平均位置: {mean_pos:.4f}mm")
        print(f"标准差: {std_dev:.4f}mm")
        print(f"重复精度 (3σ): {3*std_dev:.4f}mm")

        service.disable()
```

### 10.3 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 测量值 | 合格标准 | 结果 |
|----------|----------|----------|--------|----------|------|
| TC-PERF-001 | 通信响应时间 | | ms | < 10ms | □ 通过 □ 失败 |
| TC-PERF-002 | 状态更新频率 | | Hz | > 50Hz | □ 通过 □ 失败 |
| TC-PERF-003 | 定位精度 | | mm | < 0.02mm | □ 通过 □ 失败 |
| TC-PERF-004 | 重复定位精度 | | mm | < 0.01mm | □ 通过 □ 失败 |

---

## 11. 安全测试

### 11.1 测试目标

验证系统安全保护机制。

### 11.2 测试用例

#### TC-SAF-001: 软件行程限制

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证软件限位功能 |
| **测试步骤** | 尝试移动超出行程 |
| **预期结果** | 拒绝超限移动命令 |

#### TC-SAF-002: 急停功能

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证急停响应 |
| **测试步骤** | 高速运动中触发急停 |
| **预期结果** | 立即停止，最大减速度停止 |

#### TC-SAF-003: 故障保护

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证故障检测和保护 |
| **测试步骤** | 模拟过载、编码器断线等故障 |
| **预期结果** | 正确检测并进入保护状态 |

#### TC-SAF-004: 断电保护 (Z轴)

| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 Z 轴抱闸功能 |
| **测试步骤** | 断电后检查 Z 轴是否下落 |
| **预期结果** | 抱闸生效，Z 轴保持位置 |

### 11.3 测试结果记录表

| 用例编号 | 测试项目 | 测试日期 | 结果 | 备注 |
|----------|----------|----------|------|------|
| TC-SAF-001 | 软件行程限制 | | □ 通过 □ 失败 | |
| TC-SAF-002 | 急停功能 | | □ 通过 □ 失败 | |
| TC-SAF-003 | 故障保护 | | □ 通过 □ 失败 | |
| TC-SAF-004 | 断电保护 | | □ 通过 □ 失败 | |

---

## 12. 测试检查清单

### 12.1 测试前准备

- [ ] 硬件连接正确
- [ ] 电源供应正常 (24V DC)
- [ ] 急停按钮功能正常
- [ ] USB-RS485 转换器已连接
- [ ] 运动范围内无障碍物
- [ ] 已安装所有依赖包
- [ ] 已配置正确的串口权限

### 12.2 按层测试进度

| 层级 | 测试项目 | 总数 | 通过 | 失败 | 进度 |
|------|----------|------|------|------|------|
| Layer 1 | 串口通信 | 6 | | | % |
| Layer 2 | Modbus RTU | 7 | | | % |
| Layer 3 | 电机控制 | 10 | | | % |
| Layer 4 | 高级 API | 10 | | | % |
| Layer 5 | GUI 应用 | 15 | | | % |
| 集成测试 | | 4 | | | % |
| 系统测试 | | 4 | | | % |
| 性能测试 | | 4 | | | % |
| 安全测试 | | 4 | | | % |
| **总计** | | **64** | | | **%** |

### 12.3 测试完成标准

1. **Layer 1-4**: 所有用例 100% 通过
2. **Layer 5 (GUI)**: 所有用例 100% 通过
3. **集成测试**: 所有用例 100% 通过
4. **系统测试**: 所有用例 100% 通过
5. **性能测试**: 所有指标满足标准
6. **安全测试**: 所有保护机制正常

### 12.4 测试报告模板

```markdown
# 测试报告

## 概要信息
- 测试日期:
- 测试人员:
- 软件版本:
- 硬件配置:

## 测试结果汇总
- 总测试用例: 59
- 通过:
- 失败:
- 跳过:

## 问题记录
| 编号 | 描述 | 严重程度 | 状态 |
|------|------|----------|------|
| | | | |

## 结论与建议

```

---

## 附录

### A. 测试脚本运行命令

```bash
# 运行单个测试
python -c "from tests.integration.test_xxx import test_xxx; test_xxx()"

# 运行 pytest 测试
pytest tests/ -v

# 运行带日志的测试
python -c "import logging; logging.basicConfig(level=logging.DEBUG); from tests.integration.test_xxx import test_xxx; test_xxx()"
```

### B. 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无法打开串口 | 权限不足 | `sudo chmod 666 /dev/ttyUSB0` |
| 通信超时 | 波特率不匹配 | 确认使用 115200 |
| 无响应 | 从站地址错误 | 确认 X=1, Y=2, Z=3 |
| 使能失败 | 电机有故障 | 检查错误码并复位 |

### C. 参考文档

- [NiMotion 伺服电机手册](documents/LMS-C12-24050.md)
- [XYG321-A 三轴平台规格](documents/XYG321-A.md)
- [CiA402 标准参考](https://www.can-cia.org/can-knowledge/)
- [Modbus RTU 协议规范](https://modbus.org/)

---

*文档结束*
