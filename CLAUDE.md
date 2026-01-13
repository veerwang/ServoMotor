# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains documentation and resources for developing servo motor control systems using NiMotion integrated low-voltage servo motors with Modbus RTU communication protocol.

### Hardware Documentation

- **LMS-C12-24050**: NiMotion integrated low-voltage servo motor (motor + drive in one unit)
- **XYG321-A**: 3-axis ball screw drive motion system (X/Y/Z axes)

---

## XYG321-A 3-Axis Ball Screw Drive System

### Basic Specifications

| Item | X Axis | Y Axis | Z Axis |
|------|--------|--------|--------|
| Model Type | CFG8 | CFG5 | CFG4 |
| Repeatability | ±0.01mm | ±0.01mm | ±0.01mm |
| Ball Screw Lead | 20mm | 10mm | 10mm |
| Maximum Speed | 1000mm/s | 500mm/s | 500mm/s |
| Stroke Range (50mm pitch) | 50~1100mm | 100~500mm | 50~100mm |
| AC Servo Motor Output | 200W | 100W | 100W+Brake |
| Environment | 0~40°C, 85%RH Below | | |

**Note:** Maximum speed is based on AC servo motor's 3000RPM.

### Verified Z-Axis Calibration (2026-01-10)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Encoder Resolution (608Fh) | 10000/1 | 10000 pulses per motor revolution |
| Gear Ratio (6091h) | 1:1 | No software gear compensation needed |
| Ball Screw Lead | 10mm | 1 revolution = 10mm linear movement |
| **Conversion** | **1000 units = 1mm** | Verified by physical measurement |
| Slave Address | 0x03 | Z-axis motor address |

**DI Configuration (Limit Switches) - Updated 2026-01-12:**
| DI | Function | Logic | Notes |
|----|----------|-------|-------|
| DI2 | 15 (Negative Limit) | 0 (Active Low) | Wiring swapped from original |
| DI3 | 14 (Positive Limit) | 0 (Active Low) | Wiring swapped from original |

**Homing Configuration (Verified 2026-01-10):**
| Parameter | Register | Value | Notes |
|-----------|----------|-------|-------|
| Homing Timeout | 0x012E (2005h:1Ch) | 60000ms | **IMPORTANT: Default was 0ms causing instant timeout!** |
| Homing Method | 0x0416 (6098h) | 38 | Negative direction blocking homing |
| Homing High Speed | 0x0417 (6099h:01) | 5000-10000 | user units/s |
| Homing Low Speed | 0x0419 (6099h:02) | 2000 | user units/s |
| Homing Acceleration | 0x041B (609Ah) | 50000 | user units/s² |
| Blocking Torque | 0x0170 (2007h:13h) | 200-300 | 0.1% units (20-30%) |
| Blocking Time | 0x0172 (2007h:15h) | 500 | ms |

### Maximum Stroke

| Axis | Stroke |
|------|--------|
| X | 1100mm |
| Y | 500mm |
| Z | 100mm |

### Maximum Payload (kg)

| Z Position (mm) | Y Position 100mm | 150mm | 200mm | 250mm | 300mm | 350mm | 400mm | 450mm | 500mm |
|-----------------|------------------|-------|-------|-------|-------|-------|-------|-------|-------|
| 50 | 3.3 | 2.6 | 2.4 | 1.7 | 1.5 | 0.8 | 0.6 | 0.5 | 0.5 |
| 100 | 3.1 | 2.4 | 2.2 | 1.5 | 1.3 | 0.6 | 0.5 | 0.5 | 0.5 |

### Ordering Method

Model number format: **XYG321 - A1 - 300 - 300 - 100 - T - C - 0001**

| Position | Description | Options |
|----------|-------------|---------|
| Model | Base model | XYG321 |
| Combination | Arm Type | A |
| Direction | Combination direction | 1, 2, 3, 4 |
| X Stroke | X axis stroke | 50~1100mm (50mm pitch) |
| Y Stroke | Y axis stroke | 100~500mm (50mm pitch) |
| Z Stroke | Z axis stroke | 50~100mm (50mm pitch) |
| Motor | Motor installation standard | T=Standard (Mitsubishi/Delta/Yaskawa/Inovance/etc.), P=Panasonic |
| Delivery | Delivery method | C=By Set, K=By Kit |
| Special | Special order number | 0001, etc. |

### X Axis Dimension Table

| X Stroke (mm) | 50 | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 | 550 | 600 | 650 | 700 | 750 | 800 | 850 | 900 | 950 | 1000 | 1050 | 1100 |
|---------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|------|------|
| L (mm) | 314.5 | 364.5 | 414.5 | 464.5 | 514.5 | 564.5 | 614.5 | 664.5 | 714.5 | 764.5 | 814.5 | 864.5 | 914.5 | 964.5 | 1014.5 | 1064.5 | 1114.5 | 1164.5 | 1214.5 | 1264.5 | 1314.5 | 1364.5 |
| A (mm) | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 | 50 | 100 |
| M | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 5 | 5 | 6 | 6 | 7 | 7 | 8 | 8 | 9 | 9 | 10 | 10 | 11 | 11 |
| N | 6 | 6 | 8 | 8 | 10 | 10 | 12 | 12 | 14 | 14 | 16 | 16 | 18 | 18 | 20 | 20 | 22 | 22 | 24 | 24 | 26 | 26 |
| P (mm) | 50 | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 | 550 | 600 | 650 | 700 | 750 | 800 | 850 | 900 | 950 | 1000 | 1050 | 1100 |
| Max Speed (mm/s) | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 | 900 | 800 | 700 | 600 | 500 | 400 | 300 | - |

**Note:** L = X Stroke + 264.5mm

### Y Axis Dimension Table

| Y Stroke (mm) | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 |
|---------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| H (mm) | 394.5 | 444.5 | 494.5 | 544.5 | 594.5 | 644.5 | 694.5 | 744.5 | 794.5 |
| Max Speed (mm/s) | 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 | 500 |

**Note:** H = Y Stroke + 294.5mm

### Combination Directions

Four mounting configurations available: A1, A2, A3, A4 (rotated orientations)

### Key Dimensions

- XY Cable Chain: 61mm × 50mm
- Z Stroke Height: Z Stroke + 140.5mm (total 120 + Z Stroke + 140.5)
- Mounting holes: 2-Ø3▽4.5H7, 4-M4▽9.5

### Speed Calculation

Motor-to-linear speed conversion:
```
Linear Speed (mm/s) = Motor Speed (rpm) × Ball Screw Lead (mm) / 60

Example for X axis (Lead = 20mm):
At 3000rpm: Speed = 3000 × 20 / 60 = 1000 mm/s

Example for Y/Z axis (Lead = 10mm):
At 3000rpm: Speed = 3000 × 10 / 60 = 500 mm/s
```

### Position Calculation

Encoder to linear position conversion:
```
Position (mm) = Encoder Count × Ball Screw Lead (mm) / Encoder Resolution

Example (assuming 10000 counts/rev encoder):
Position = Count × Lead / 10000
```

---

## Communication Protocol

### Modbus RTU Configuration

- Default baud rate: 115.2Kbps
- Default slave address: 0x01
- Data format: 8 data bits, no parity, 1 stop bit
- Physical interface: RS-485
- Frame idle interval: minimum 3.5 character times (t3.5)

### Baud Rate Settings

| Value | Baud Rate |
|-------|-----------|
| 0, 1  | 9.6Kbps   |
| 2     | 19.2Kbps  |
| 3     | 38.4Kbps  |
| 4     | 57.6Kbps  |
| 5     | 115.2Kbps |
| 6     | 256Kbps   |
| 7     | 500Kbps   |
| 8     | 1Mbps     |
| 9     | 1.5Mbps   |

### Network Data Format Options

| Value | Description |
|-------|-------------|
| 0     | 8 data bits, even parity, 1 stop bit |
| 1     | 8 data bits, odd parity, 1 stop bit |
| 2     | 8 data bits, no parity, 1 stop bit |
| 3     | 8 data bits, no parity, 2 stop bits |

### Supported Function Codes

| Code | Function | Broadcast Support |
|------|----------|-------------------|
| 0x03 | Read Holding Register | No |
| 0x04 | Read Input Register | No |
| 0x06 | Write Single Register | Yes |
| 0x10 | Write Multiple Registers | Yes |

### Modbus Frame Structure

| Field | Size |
|-------|------|
| Slave Address | 1 byte |
| Function Code | 1 byte |
| Data | 0-252 bytes |
| CRC (Low + High) | 2 bytes |

### Exception Codes

| Code | Name | Description |
|------|------|-------------|
| 01 | Illegal function code | Function code not within 0x00~0x0F |
| 02 | Illegal data address | Data address exceeds definition |
| 03 | Illegal data value | Value outside register storage |
| 04 | Slave equipment failure | Non-recoverable error |
| 05 | Recognize | Slave needs more time, master should poll |
| 06 | Slave equipment busy | Wait for slave to be idle |
| 12 | Slave equipment alarm | Motor has active alarm |

### Broadcast Preemption (Reset Communication)

When communication parameters are unknown, send broadcast message within 1 second before power-on:
- Address: 0x00, Function: 0xD2, Motor Serial Number: 4 bytes, CRC: 2 bytes
- Resets to: Address=1, Baud=115200, No parity, 8 data bits, 1 stop bit

---

## Key Register Addresses (Object Dictionary)

### Communication Parameters

| Parameter | Index:SubIndex | Modbus Address | Description |
|-----------|----------------|----------------|-------------|
| Slave Address | 200Ch:02h | 0230h | Range: 1-247 |
| Baud Rate | 200Ch:03h | 0231h | See baud rate table |
| Data Format | 200Ch:04h | 0232h | See data format table |

### Control Registers

| Parameter | Index | Modbus Address | Type | Description |
|-----------|-------|----------------|------|-------------|
| Control Word | 6040h | 0380h | R/W | Motor control commands |
| Status Word | 6041h | 0381h | R | Motor status feedback |
| Operation Mode | 6060h | 03C2h | R/W | Set operating mode |
| Operation Mode Display | 6061h | 03C3h | R | Current operating mode |

### Stop Mode Options

| Parameter | Index | Modbus Address | Description |
|-----------|-------|----------------|-------------|
| Quick Stop Option | 605Ah | 03BFh | Quick stop behavior |
| Shutdown Option | 605Bh | 03BDh | Shutdown behavior |
| Disable Operation Option | 605Ch | 03BEh | Disable operation behavior |
| Halt Option | 605Dh | 03C0h | Halt behavior |
| Fault Response Option | 605Eh | 03C1h | Fault reaction behavior |

### Unit Conversion Parameters

| Parameter | Index:SubIndex | Modbus Address | Description |
|-----------|----------------|----------------|-------------|
| Encoder Increment | 608Fh:01h | 0406h | Encoder pulses per motor turn |
| Motor Revolutions | 608Fh:02h | 0408h | Motor turns (denominator) |
| Gear Motor Revolutions | 6091h:01h | 040Eh | Motor shaft revolutions |
| Gear Shaft Revolutions | 6091h:02h | 0410h | Drive shaft revolutions |
| Polarity | 607Eh | 03F3h | Position/velocity direction |

### Input Voltage Register

| Parameter | Index:SubIndex | Modbus Address | Description |
|-----------|----------------|----------------|-------------|
| Input Voltage | 200Bh:15h | 01F7h | Current input voltage (0.1V units) |

---

## Motor Control Architecture

### CiA402 State Machine

```
                    +------------------+
                    | Not ready to     |
                    | switch on        |
                    +--------+---------+
                             | (1)
                    +--------v---------+
                    | Switch on        |
                    | disabled         |
                    +--------+---------+
                             | (2)
                    +--------v---------+
                    | Ready to         |<-----(7)-----+
                    | switch on        |              |
                    +--------+---------+              |
                             | (3)                    |
                    +--------v---------+              |
                    | Switched on      |<----(6)--+   |
                    +--------+---------+          |   |
                             | (4)                |   |
                    +--------v---------+          |   |
        +---------->| Operation        |---(5)----+   |
        |           | enabled          |              |
        |           +--------+---------+              |
        |  (16)              | (11)                   |
        |           +--------v---------+              |
        +-----------| Quick stop       |--(12)--------+
                    | active           |
                    +------------------+

    Fault path: Any state --(13)--> Fault reaction active --(14)--> Fault --(15)--> Switch on disabled
```

### State Transition Commands (Control Word 6040h)

| Command | Bit7 | Bit3 | Bit2 | Bit1 | Bit0 | Hex Value | Transitions |
|---------|------|------|------|------|------|-----------|-------------|
| Shutdown | 0 | X | 1 | 1 | 0 | 0x06 | 2,6,8 |
| Switch on | 0 | 0 | 1 | 1 | 1 | 0x07 | 3 |
| Switch on + Enable | 0 | 1 | 1 | 1 | 1 | 0x0F | 3+4 |
| Disable voltage | 0 | X | X | 0 | X | 0x00 | 7,9,10,12 |
| Quick stop | 0 | X | 0 | 1 | X | 0x02 | 7,10,11 |
| Disable operation | 0 | 0 | 1 | 1 | 1 | 0x07 | 5 |
| Enable operation | 0 | 1 | 1 | 1 | 1 | 0x0F | 4,16 |
| Fault reset | Rising edge Bit7 | X | X | X | X | 0x80 | 15 |

### Status Word (6041h) Bit Definition

| Bit | Name | Description |
|-----|------|-------------|
| 0 | Ready to switch on | State indicator |
| 1 | Switched on | State indicator |
| 2 | Operation enabled | State indicator |
| 3 | Fault | Fault present |
| 4 | Voltage enabled | Power stage on |
| 5 | Quick stop | Quick stop active |
| 6 | Switch on disabled | State indicator |
| 7 | Warning | Warning present |
| 8 | Manufacturer specific | - |
| 9 | Remote | Remote control enabled |
| 10 | Target reached | Motion complete |
| 11 | Internal limit active | Limit triggered |
| 12-13 | Operation mode specific | - |
| 14-15 | Manufacturer specific | - |

### Status Word State Masks

| Status Word Pattern | State |
|--------------------|-------|
| xxxx xxxx x0xx 0000 | Not ready to switch on |
| xxxx xxxx x1xx 0000 | Switch on disabled |
| xxxx xxxx x01x 0001 | Ready to switch on |
| xxxx xxxx x01x 0011 | Switched on |
| xxxx xxxx x01x 0111 | Operation enabled |
| xxxx xxxx x00x 0111 | Quick stop active |
| xxxx xxxx x0xx 1111 | Fault reaction active |
| xxxx xxxx x0xx 1000 | Fault |

---

## Unit Conversion

### Position Encoder Resolution (608Fh)

```
Resolution = Encoder_Increment (608Fh:01h) / Motor_Revolutions (608Fh:02h)
```
Default: 10000 increments / 1 revolution = 10000

### Gear Ratio (6091h)

```
Gear_Ratio = Motor_Revolutions (6091h:01h) / Shaft_Revolutions (6091h:02h)
```

### Conversion Formulas

**Position (User Units to Encoder):**
```
Motor_Position = User_Position × Gear_Ratio
```

**Velocity (User Units/s to RPM):**
```
Motor_Speed(rpm) = (Shaft_Speed × Gear_Ratio × 60) / Encoder_Resolution
```

**Acceleration:**
```
Motor_Accel(rpm/ms) = (Shaft_Accel × Gear_Ratio × 1000) / (Encoder_Resolution × 60)
```

### Polarity (607Eh)

| Bit | Function | 0 = Multiply by +1, 1 = Multiply by -1 |
|-----|----------|---------------------------------------|
| 7 | Position polarity | Affects PP, CSP modes |
| 6 | Velocity polarity | Affects VM, CSV modes |
| 5-0 | Reserved | Always 0 |

---

## Stop Mode Settings

### Quick Stop Option (605Ah)

| Value | Behavior |
|-------|----------|
| 0x00 | Coast to stop (free running) |
| 0x01 | Decelerate using 6084h ramp, then coast |
| 0x02 | Decelerate using 6085h (quick stop) ramp, then coast |

### Fault Response Option (605Eh)

| Value | Behavior |
|-------|----------|
| -1 | Use fault-specific reaction code |
| 0x00 | Coast to stop |
| 0x01 | Decelerate using 6084h ramp |
| 0x02 | Decelerate using 6085h ramp |

### Halt Option (605Dh)

| Value | Behavior |
|-------|----------|
| 0x00 | Reserved |
| 0x01 | Decelerate using 6084h, hold position |
| 0x02 | Decelerate using 6085h, hold position |

---

## Operating Modes

| Mode Code | Name | Description |
|-----------|------|-------------|
| 1 | PP | Profile Position Mode |
| 2 | VM | Velocity Mode |
| 3 | PV | Profile Velocity Mode |
| 4 | PT | Profile Torque Mode |
| 6 | HM | Homing Mode |
| 7 | IP | Interpolation Mode |
| 8 | CSP | Cyclic Synchronous Position Mode |
| 9 | CSV | Cyclic Synchronous Velocity Mode |
| 10 | CST | Cyclic Synchronous Torque Mode |
| -1 | NiMotion Position | Manufacturer position mode |
| -2 | NiMotion Speed | Manufacturer velocity mode |
| -3 | NiMotion Torque | Manufacturer torque mode |
| -4 | Multi-Segment Position | Multi-point position mode |
| -5 | Multi-Speed | Multi-speed mode |

---

## Development Notes

- All numerical values in documentation are decimal unless suffixed with 'h' (hexadecimal)
- Object notation: `<index>:<sub-index>` (e.g., 1003h:02h)
- CRC uses Modbus RTU standard (CRC-16)
- Save parameters to EEPROM: Write "save" (0x65766173) to register 0026h
- Parameters take effect after power cycle or reboot

---

## 重要: CiA402 对象索引到 Modbus 地址映射

### 地址映射说明

NiMotion 驱动器的 CiA402 对象索引到 Modbus 地址的映射 **没有简单的计算公式**。每个寄存器的地址需要查阅 NiMotion 手册确认。

**常见错误**: 假设地址映射遵循线性规则 (如 `Modbus地址 = (对象索引 - 0x6000) * 0x10`)，这是错误的。

### 验证过的寄存器地址映射表

以下地址已通过实际硬件测试验证:

#### 控制与状态寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 控制字 | 6040h | 0380h | UINT16 | RW |
| 状态字 | 6041h | 0381h | UINT16 | RO |
| 错误码 | 603Fh | 0382h | UINT16 | RO |
| 操作模式设置 | 6060h | **03C2h** | INT8 | RW |
| 操作模式显示 | 6061h | **03C3h** | INT8 | RO |

#### 位置控制寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 实际位置 | 6064h | **03C8h** | INT32 | RO |
| 目标位置 | 607Ah | **03E7h** | INT32 | RW |
| 跟随误差 | 60F4h | **0440h** | INT32 | RO |

#### 速度控制寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 实际速度 | 606Ch | **03D5h** | INT32 | RO |
| 目标速度 | 60FFh | **0448h** | INT32 | RW |
| 轮廓速度 | 6081h | **03F8h** | UINT32 | RW |

#### 加减速寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 轮廓加速度 | 6083h | **03FCh** | UINT32 | RW |
| 轮廓减速度 | 6084h | **03FEh** | UINT32 | RW |
| 快速停止减速度 | 6085h | **0400h** | UINT32 | RW |

#### 转矩控制寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 目标转矩 | 6071h | **03DBh** | INT16 | RW |
| 实际转矩 | 6077h | **03E3h** | INT16 | RO |

#### 回零控制寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 回零方式 | 6098h | **0416h** | INT8 | RW |
| 回零高速 | 6099h:01 | **0417h** | UINT32 | RW |
| 回零低速 | 6099h:02 | **0419h** | UINT32 | RW |
| 回零加速度 | 609Ah | **041Bh** | UINT32 | RW |

#### 数字 IO 寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 数字输入 | 60FDh | **0447h** | UINT32 | RO |
| 数字输出 | 60FEh | **0449h** | UINT32 | RW |

#### 编码器/减速比寄存器

| 寄存器 | CiA402 索引 | Modbus 地址 | 类型 | 访问 |
|--------|-------------|-------------|------|------|
| 编码器分辨率-分子 | 608Fh:01 | **0408h** | UINT32 | RW |
| 编码器分辨率-分母 | 608Fh:02 | **040Ah** | UINT32 | RW |
| 减速比-分子 | 6091h:01 | **040Ch** | UINT32 | RW |
| 减速比-分母 | 6091h:02 | **040Eh** | UINT32 | RW |

### 32 位寄存器读写注意事项

**重要**: 经实际硬件验证 (2026-01-10)，NiMotion 驱动器使用**大端序** (Big Endian):
- 高字 (High Word): 基础地址 (低地址)
- 低字 (Low Word): 基础地址 + 1 (高地址)

读取示例 (读取实际位置 6064h):
```python
high = read_register(slave, 0x03C8)  # 高字在低地址
low = read_register(slave, 0x03C9)   # 低字在高地址
value = (high << 16) | low
```

写入示例 (写入目标位置 607Ah):
```python
write_register(slave, 0x03E7, (target >> 16) & 0xFFFF)  # 高字在低地址
write_register(slave, 0x03E8, target & 0xFFFF)          # 低字在高地址
```

使用 write_multiple_registers 写入:
```python
high = (value >> 16) & 0xFFFF
low = value & 0xFFFF
write_multiple_registers(slave, address, [high, low])  # 大端序: 高字在前
```

---

## Modbus Communication Examples

### Read Holding Register (0x03)
Read baud rate (200Ch:03h = 0231h):
```
Request:  01 03 02 31 00 01 [CRC]
Response: 01 03 02 00 05 [CRC]  (Value 5 = 115.2Kbps)
```

### Write Single Register (0x06)
Set baud rate to 115.2Kbps:
```
Request:  01 06 02 31 00 05 [CRC]
Response: 01 06 02 31 00 05 [CRC]
```

### Write Multiple Registers (0x10)
Set slave address to 2 and baud rate to 9.6Kbps:
```
Request:  01 10 02 30 00 02 04 00 02 00 01 [CRC]
Response: 01 10 02 30 00 02 [CRC]
```

### Save Parameters
```
Request:  01 10 00 26 00 02 04 65 76 61 73 [CRC]  ("save" = 0x65766173)
Response: 01 10 00 26 00 02 [CRC]
```

### RS-485 Connection
```
Master Station
     |
    GND ----+----+----+
    485- ---+----+----+--- 120Ω termination
    485+ ---+----+----+--- 120Ω termination
            |    |    |
         Motor1 Motor2 Motor3
```

---

## Operating Mode Details

### Control Mode Selection

**2002h:01h (00B1h)** - Control Mode Option:
| Value | Mode |
|-------|------|
| 0x00 | CiA402 mode |
| 0x01 | NiMotion position mode |
| 0x02 | NiMotion speed mode |
| 0x03 | NiMotion torque mode |
| 0x04 | NiMotion open loop mode |

**6060h (03C2h)** - CiA402 Mode Selection (when 2002h:01h = 0):
| Value | Mode |
|-------|------|
| 0x01 | Profile Position Mode (PP) |
| 0x02 | Velocity Mode (VM) |
| 0x03 | Profile Velocity Mode (PV) |
| 0x04 | Profile Torque Mode (PT) |
| 0x06 | Home Return Mode (HM) |
| 0x07 | Interpolation Mode (IP) |
| 0x08 | Cyclic Synchronized Position Mode (CSP) |
| 0x09 | Cyclic Synchronized Velocity Mode (CSV) |
| 0x0A | Cyclic Synchronous Torque Mode (CST) |

---

### Profile Position Mode (PP) - Mode 0x01

Point-to-point positioning with trajectory generation.

#### Key Registers for PP Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Position | 607Ah | 03E7h | Target position (user units) |
| Profile Velocity | 6081h | 03F8h | Running velocity (user units/s) |
| End Velocity | 6082h | 03FAh | Velocity at target (usually 0) |
| Profile Acceleration | 6083h | 03FCh | Acceleration (user units/s²) |
| Profile Deceleration | 6084h | 03FEh | Deceleration (user units/s²) |
| Quick Stop Decel | 6085h | 0400h | Quick stop decel (user units/s²) |
| Motion Profile Type | 6086h | 0402h | 0=Trapezoidal, 3=S-curve |
| Max Profile Velocity | 607Fh | 03F4h | Speed limit (user units/s) |
| Max Motor Speed | 6080h | 03F6h | Motor speed limit (rpm) |
| Position Demand | 6062h | 03C4h | Current target position (user units) |
| Position Actual | 6064h | 03C8h | Actual position (user units) |
| Position Actual (enc) | 6063h | 03C6h | Actual position (encoder units) |
| Trajectory Output | 60FCh | 0446h | Planned position (encoder units) |
| Positioning Options | 60F2h | 043Fh | Positioning behavior options |
| Position Window | 6067h | 03CDh | Target reached window |
| Position Window Time | 6068h | 03CFh | Time in window for target reached (ms) |
| Following Error Window | 6065h | 03CAh | Max allowed following error |
| Following Error Timeout | 6066h | 03CCh | Following error timeout |
| Software Position Limit | 607Dh | 03EFh/03F1h | Min/max position limits |

#### PP Mode Control Word (6040h) Special Bits

| Bit | Function |
|-----|----------|
| 4 | New set-point (0→1 triggers motion) |
| 5 | Change set immediately (1=immediate, 0=after current) |
| 6 | Absolute/Relative (0=absolute, 1=relative) |
| 8 | Halt (1=stop motion) |
| 9 | Change on set-point |

#### PP Mode Status Word (6041h) Special Bits

| Bit | Function |
|-----|----------|
| 10 | Target reached (1=position reached) |
| 12 | Set-point acknowledge (1=new setpoint accepted) |
| 13 | Following error (1=error detected) |

#### PP Mode Motion Commands

| Command | 6040h Change | Description |
|---------|--------------|-------------|
| Absolute, queue | 0x0F → 0x1F | Absolute position, wait for previous |
| Absolute, immediate | 0x2F → 0x3F | Absolute position, interrupt current |
| Relative, queue | 0x4F → 0x5F | Relative position, wait for previous |
| Relative, immediate | 0x6F → 0x7F | Relative position, interrupt current |

#### PP Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x01
2. Set target position: 607Ah = 10000
3. Set velocity: 6081h = 10000
4. Set acceleration: 6083h = 40000
5. Set deceleration: 6084h = 40000
6. Enable: 6040h = 0x06 → 0x07 → 0x0F
7. Start motion: 6040h = 0x0F → 0x1F (absolute)
8. Monitor: Read 6041h bit10 for target reached
```

---

### Velocity Mode (VM) - Mode 0x02

Simple velocity control similar to VFD operation.

#### Key Registers for VM Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Velocity | 6042h | 0382h | Target speed (rpm × factor) |
| Velocity Demand | 6043h | 0383h | Current velocity command |
| Velocity Actual | 6044h | 0384h | Actual velocity (rpm) |
| Velocity Factor Num | 604Ch:01h | 0394h | Speed unit numerator |
| Velocity Factor Den | 604Ch:02h | 0396h | Speed unit denominator |
| Accel Delta Speed | 6048h:01h | 0389h | Speed change (rpm) |
| Accel Delta Time | 6048h:02h | 038Bh | Time for change (s×10) |
| Decel Delta Speed | 6049h:01h | 038Ch | Speed change (rpm) |
| Decel Delta Time | 6049h:02h | 038Eh | Time for change (s×10) |
| Quick Stop Delta Speed | 604Ah:01h | 038Fh | Quick stop speed (rpm) |
| Quick Stop Delta Time | 604Ah:02h | 0391h | Quick stop time (s×10) |
| Min Velocity | 6046h:01h | 0385h | Minimum speed limit |
| Max Velocity | 6046h:02h | 0387h | Maximum speed limit |

**Velocity Unit Calculation:**
```
Speed Unit = rpm × (604Ch:01h / 604Ch:02h)
```

**Acceleration Calculation:**
```
Acceleration = 6048h:01h / (6048h:02h / 10)  [rpm/s]
Example: 3000rpm in 3.5s → 6048h:01h=3000, 6048h:02h=35
```

#### VM Mode Control Word (6040h) Special Bits

| Bit | Value | Function |
|-----|-------|----------|
| 4 | 0 | No ramp, immediate speed change |
| 4 | 1 | Use acceleration/deceleration ramps |
| 5 | 0 | Lock current speed |
| 5 | 1 | Follow planner output |
| 6 | 0 | Planner input = 0 |
| 6 | 1 | Planner input = target speed |
| 8 | 1 | Halt motor |

#### VM Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x02
2. Set target speed: 6042h = 1000 (rpm)
3. Set acceleration: 6048h:01h=500, 6048h:02h=1 (500rpm/s)
4. Set deceleration: 6049h:01h=500, 6049h:02h=1
5. Enable: 6040h = 0x06 → 0x07 → 0x7F
6. Monitor: Read 606Ch for actual speed
```

---

### Profile Velocity Mode (PV) - Mode 0x03

Velocity control with trajectory planning and S-curve support.

#### Key Registers for PV Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Velocity | 60FFh | 0448h | Target speed (user units/s) |
| Velocity Demand | 606Bh | 03D3h | Current velocity command |
| Velocity Actual | 606Ch | 03D5h | Actual velocity (rpm) |
| Profile Acceleration | 6083h | 03FCh | Acceleration (user units/s²) |
| Profile Deceleration | 6084h | 03FEh | Deceleration (user units/s²) |
| Quick Stop Decel | 6085h | 0400h | Quick stop decel |
| Max Profile Velocity | 607Fh | 03F4h | Speed limit |
| Max Motor Speed | 6080h | 03F6h | Motor speed limit (rpm) |
| Motion Profile Type | 6086h | 0402h | 0=Trapezoidal, 3=S-curve |
| Max Acceleration | 60C5h | 043Bh | Accel limit (user units/s²) |
| Max Deceleration | 60C6h | 043Dh | Decel limit (user units/s²) |

#### PV vs VM Mode Differences

- PV mode uses user units for velocity (units/s)
- PV mode supports S-curve motion profiles
- VM mode uses rpm directly
- VM mode only supports trapezoidal profiles

---

### Position Control Functions

#### Following Error Detection

Following Error = Position Demand (6062h) - Position Actual (6064h)

If |Following Error| > Following Error Window (6065h) for time > Following Error Timeout (6066h):
- Status Word bit 13 = 1 (following error flag)

#### Target Reached Detection

Position Error = Target Position (607Ah) - Position Actual (6064h)

If |Position Error| < Position Window (6067h) for time > Position Window Time (6068h):
- Status Word bit 10 = 1 (target reached)

---

### Motion Profile Types (6086h)

| Value | Type | Description |
|-------|------|-------------|
| 0 | Trapezoidal | Linear acceleration/deceleration |
| 3 | S-curve | Jerk-limited smooth acceleration |

**S-curve Jerk Parameters (60A4h):**
| Sub-index | Modbus | Description |
|-----------|--------|-------------|
| 01h | 041Eh | Acceleration start/end jerk |
| 02h | 0420h | Deceleration start/end jerk |

---

### Profile Torque Mode (PT) - Mode 0x04

Torque control with speed limiting.

#### Key Registers for PT Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Torque | 6071h | 03DBh | Target torque (0.1% units) |
| Max Torque | 6072h | 03DCh | Maximum torque limit (0.1%) |
| Torque Actual | 6077h | 03E3h | Actual torque (0.1%) |
| Torque Slope | 6087h | 0403h | Torque change per second (0.1%/s) |
| Torque Profile Type | 6088h | 0405h | 0=ramp, 2=none |
| Forward Speed Limit | 2007h:10h | 016Dh | Forward speed limit (rpm) |
| Reverse Speed Limit | 2007h:11h | 016Eh | Reverse speed limit (rpm) |

**Torque Unit:** 0.1% of rated torque (e.g., 500 = 50%)

#### PT Mode Speed Limiting

When motor speed exceeds the speed limits, the drive automatically switches to speed control to maintain speed within limits. Returns to torque control when target torque < average torque at current speed.

#### PT Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x04
2. Set target torque: 6071h = 500 (50%)
3. Set ramp type: 6088h = 2 (no ramp)
4. Enable: 6040h = 0x06 → 0x07 → 0x0F
5. Monitor: Read 6077h for actual torque
```

---

### Homing Mode (HM) - Mode 0x06

Find mechanical home position using switches or blocking detection.

#### Key Registers for HM Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Homing Method | 6098h | 0416h | Homing method (17-38) |
| Homing Speed Fast | 6099h:01h | 0417h | Speed to find switch (user units/s) |
| Homing Speed Slow | 6099h:02h | 0419h | Speed to find home (user units/s) |
| Homing Acceleration | 609Ah | 041Bh | Homing acceleration (user units/s²) |
| Home Offset | 607Ch | 03EDh | Offset from home position |
| Blocking Torque | 2007h:13h | 0170h | Torque threshold for blocking (0.1%) |
| Blocking Time | 2007h:15h | 0172h | Blocking detection time (ms) |

#### HM Mode Control Word (6040h) Special Bits

| Bit | Value | Function |
|-----|-------|----------|
| 4 | 0 | Homing not activated |
| 4 | 1 | Start/continue homing |
| 8 | 1 | Halt homing |

#### HM Mode Status Word (6041h) Special Bits

| Bit | Value | Function |
|-----|-------|----------|
| 10 | 1 | Target position reached |
| 12 | 1 | Homing attained (complete) |
| 13 | 1 | Homing error |

#### Digital Input Functions for Homing

| Function Number | Description |
|-----------------|-------------|
| 14 | Positive limit switch |
| 15 | Negative limit switch |
| 31 | Home switch |

#### Homing Methods Summary

| Method | Switch Used | Initial Direction |
|--------|-------------|-------------------|
| 17 | Negative limit | Reverse |
| 18 | Positive limit | Forward |
| 19-20 | Home switch | Forward |
| 21-22 | Home switch | Reverse |
| 23-26 | Home + Positive limit | Forward |
| 27-30 | Home + Negative limit | Reverse |
| 37 | Blocking detection | Forward |
| 38 | Blocking detection | Reverse |

#### Blocking Homing (Methods 37, 38)

Uses torque detection instead of switches:
1. Motor runs at homing speed (6099h:02h)
2. When torque exceeds threshold (2007h:13h) for time (2007h:15h)
3. Position is set as home

#### HM Mode Example Sequence (Limit Switch)
```
1. Configure DI: 2003h:03h=15 (negative limit), 2003h:04h=0 (active low)
2. Set mode: 2002h:01h=0, 6060h=0x06
3. Set homing method: 6098h = 17
4. Set speeds: 6099h:01h=10000, 6099h:02h=1000
5. Set acceleration: 609Ah = 200000
6. Enable and start: 6040h = 0x06 → 0x07 → 0x0F → 0x1F
7. Monitor: Read 6041h bit12 for homing complete
```

---

### Interpolation Mode (IP) - Mode 0x07

Synchronized multi-axis motion with position interpolation.

#### Key Registers for IP Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Interpolation Position | 60C1h:01h | 042Dh | Target position (user units) |
| Interpolation Time Unit | 60C2h:01h | 042Fh | Time constant (t) |
| Interpolation Time Index | 60C2h:02h | 0430h | Time exponent (n) |
| Interpolation Type | 60C0h | 042Ch | 0=linear (only supported) |
| Position Demand | 6062h | 03C4h | Current position command |

**Interpolation Period Calculation:**
```
Period = t × 10^n seconds
Example: t=20, n=-3 → 20 × 10^-3 = 20ms
```
Recommended: 1-20ms

#### IP Mode Control Word (6040h) Special Bits

| Bit | Value | Function |
|-----|-------|----------|
| 4 | 0 | Disable interpolation |
| 4 | 1 | Enable interpolation |
| 8 | 1 | Halt |

#### IP Mode Status Word (6041h) Special Bits

| Bit | Value | Function |
|-----|-------|----------|
| 10 | 1 | Target reached |
| 12 | 1 | IP mode active |
| 13 | 1 | Following error |

#### IP Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x07
2. Set interpolation time: 60C2h:01h=20, 60C2h:02h=-3 (20ms)
3. Enable: 6040h = 0x06 → 0x07 → 0x0F → 0x1F
4. Send positions to 60C1h:01h at interpolation rate
```

---

### Cyclic Synchronized Position Mode (CSP) - Mode 0x08

Real-time position control where host sends position commands cyclically.

#### Key Registers for CSP Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Position | 607Ah | 03E7h | Absolute target position (user units) |
| Position Limit Min | 607Dh:01h | 03EFh | Minimum position limit |
| Position Limit Max | 607Dh:02h | 03F1h | Maximum position limit |
| Polarity | 607Eh | 03F3h | Direction of rotation |
| Following Error Window | 6065h | 03CAh | Error threshold (user units) |
| Following Error Timeout | 6066h | 03CCh | Error timeout (ms) |
| Max Motor Speed | 6080h | 03F6h | Speed limit (rpm) |
| Quick Stop Decel | 6085h | 0400h | Quick stop deceleration |
| Motion Profile Type | 6086h | 0402h | 0=trapezoidal, 3=S-curve |
| Position Offset | 60B0h | 0426h | Position offset (user units) |
| Velocity Offset | 60B1h | 0428h | Speed bias (user units) |
| Position Actual | 6064h | 03C8h | Current position (user units) |
| Velocity Actual | 606Ch | 03D5h | Current speed (rpm) |
| Following Error Actual | 60F4h | 0440h | Real-time following error |

**Note:** CSP mode only supports absolute position commands. Bit 4 in control word does not need to be set.

#### CSP Mode Status Word (6041h) Special Bits

| Bit | Value | Description |
|-----|-------|-------------|
| 12 | 0 | Controller ignores target preset (607Ah ignored) |
| 12 | 1 | Controller follows target preset |
| 13 | 0 | No following error |
| 13 | 1 | Following error detected |

#### CSP Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x08
   Send: 01 10 00 B1 00 01 02 00 00 (CiA402 mode)
   Send: 01 10 03 C2 00 01 02 00 08 (CSP mode)
2. Enable: 6040h = 0x06 → 0x07 → 0x0F
3. Send target positions to 607Ah cyclically
```

---

### Cyclic Synchronized Velocity Mode (CSV) - Mode 0x09

Real-time velocity control where host sends velocity commands cyclically.

#### Key Registers for CSV Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Velocity | 60FFh | 0448h | Target speed (user units/s) |
| Velocity Actual | 606Ch | 03D5h | Current speed (rpm) |
| Polarity | 607Eh | 03F3h | Direction of rotation |
| Max Motor Speed | 6080h | 03F6h | Speed limit (rpm) |
| Quick Stop Decel | 6085h | 0400h | Quick stop deceleration |
| Motion Profile Type | 6086h | 0402h | 0=trapezoidal, 3=S-curve |
| Velocity Offset | 60B1h | 0428h | Position offset (user units) |
| Torque Offset | 60B2h | 042Ah | Torque bias (0.1%) |
| Max Torque | 6072h | 03DCh | Maximum torque limit (0.1%) |

#### CSV Mode Status Word (6041h) Special Bits

| Bit | Value | Description |
|-----|-------|-------------|
| 12 | 0 | Target speed will be rounded |
| 12 | 1 | Target speed as planner input |

#### CSV Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x09
   Send: 01 10 00 B1 00 01 02 00 00 (CiA402 mode)
   Send: 01 10 03 C2 00 01 02 00 09 (CSV mode)
2. Enable: 6040h = 0x06 → 0x07 → 0x0F
3. Send target velocity to 60FFh cyclically
```

---

### Cyclic Synchronous Torque Mode (CST) - Mode 0x0A

Real-time torque control where host sends torque commands cyclically.

#### Key Registers for CST Mode

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Target Torque | 6071h | 03DBh | Target torque (0.1%) |
| Max Torque | 6072h | 03DCh | Maximum torque limit (0.1%) |
| Max Current | 6073h | 03DDh | Maximum current (0.01A) |
| Max Motor Speed | 6080h | 03F6h | Speed limit (rpm) |
| Torque Offset | 60B2h | 042Ah | Torque bias (0.1%) |
| Torque Ramp Type | 6088h | 0405h | 0=slope, 2=none |
| Torque Actual | 6077h | 03E3h | Actual torque (0.1%) |

**Note:** When speed reaches limit value, drive enters speed regulation phase.

#### CST Mode Status Word (6041h) Special Bits

| Bit | Value | Description |
|-----|-------|-------------|
| 12 | 0 | Target torque will be discarded |
| 12 | 1 | Target torque as planner input |

#### CST Mode Example Sequence
```
1. Set mode: 2002h:01h=0, 6060h=0x0A
   Send: 01 10 00 B1 00 01 02 00 00 (CiA402 mode)
   Send: 01 10 03 C2 00 01 02 00 0A (CST mode)
2. Enable: 6040h = 0x06 → 0x07 → 0x0F
3. Send target torque to 6071h cyclically
```

---

## NiMotion Proprietary Modes

NiMotion modes differ from CiA402 in that there is **no state machine management**. Motor is enabled via terminal inputs.

### NiMotion Position Mode (2002h:01h = 1)

#### Key Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Mode Selection | 2002h:01h | 00B1h | Set to 1 for position mode |
| Position Source | 2005h:01h | 010Dh | 0=pulse, 1=step, 2=multi-segment |
| Step Amount | 2005h:05h | 0112h | Step amount (encoder units) |
| DI Config | 2003h | 00D5h~00E6h | Physical input terminal config |
| VDI Config | 2017h | 0326h~0346h | Virtual input terminal config |

#### Position Command Sources

| Value | Source | Description |
|-------|--------|-------------|
| 0 | Pulse | External pulse input via DI1/DI2 |
| 1 | Step | Digital step amount via 2005h:05h |
| 2 | Multi-segment | Multi-position mode |

#### Step Position Control Example
```
1. Set NiMotion position mode: 2002h:01h = 1
   Send: 01 10 00 B1 00 01 02 00 01
2. Set position source to step: 2005h:01h = 1
   Send: 01 10 01 0D 00 01 02 00 01
3. Set step amount: 2005h:05h = 50
   Send: 01 10 01 12 00 01 02 00 32
4. Configure DI1 as motor enable (function 1): 2003h:03h = 1
   Send: 01 10 00 D5 00 01 02 00 01
5. Configure DI2 as step enable (function 20), falling edge trigger
   Send: 01 10 00 D7 00 01 02 00 14
   Send: 01 10 00 D8 00 01 02 00 03
6. Apply DI1 low level to enable, DI2 falling edge to step
```

---

### NiMotion Speed Mode (2002h:01h = 2)

#### Key Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Mode Selection | 2002h:01h | 00B1h | Set to 2 for speed mode |
| Max Speed | 2000h:0Fh | 006Bh | Maximum speed (rpm) |
| Main Speed Source | 2006h:01h | 0148h | 0=digital, 3=duty cycle |
| Aux Speed Source | 2006h:02h | 0149h | 0=digital, 3=multi-speed |
| Speed Selection | 2006h:03h | 014Ah | 0=main, 1=aux, 2=both |
| Speed Value | 2006h:04h | 014Bh | Speed command (rpm) |
| Accel Ramp | 2006h:07h | 014Eh | Accel time (ms for 0→1000rpm) |
| Decel Ramp | 2006h:08h | 014Fh | Decel time (ms) |

#### Speed Sources

| Value | Source | Description |
|-------|--------|-------------|
| 0 | Digital | Speed value from 2006h:04h |
| 3 | Duty Cycle | PWM input (20Hz-20kHz, 1kHz recommended) |

#### Digital Speed Control Example
```
1. Set NiMotion speed mode: 2002h:01h = 2
   Send: 01 10 00 B1 00 01 02 00 02
2. Set speed source to digital: 2006h:01h = 0
   Send: 01 10 01 48 00 01 02 00 00
3. Set accel ramp: 2006h:07h = 100 (100ms)
   Send: 01 10 01 4E 00 01 02 00 64
4. Set decel ramp: 2006h:08h = 100
   Send: 01 10 01 4F 00 01 02 00 64
5. Set target speed: 2006h:04h = 60 (60rpm)
   Send: 01 10 01 4B 00 01 02 00 3C
6. Configure DI1 as enable, apply low level to run
```

---

### NiMotion Torque Mode (2002h:01h = 3)

#### Key Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Mode Selection | 2002h:01h | 00B1h | Set to 3 for torque mode |
| Main Torque Source | 2007h:01h | 015Eh | 0=digital |
| Aux Torque Source | 2007h:02h | 015Fh | 0=digital |
| Torque Selection | 2007h:03h | 0160h | 0=main, 1=aux, 2=both |
| Torque Value | 2007h:04h | 0161h | Torque command (0.1%) |
| Positive Torque Limit | 2007h:0Ah | 0167h | Forward limit (0.1%) |
| Negative Torque Limit | 2007h:0Bh | 0168h | Reverse limit (0.1%) |
| Forward Speed Limit | 2007h:10h | 016Dh | Forward speed limit (rpm) |
| Reverse Speed Limit | 2007h:11h | 016Eh | Reverse speed limit (rpm) |

**Speed Limiting:** When motor speed exceeds limits, automatically switches to speed control. Returns to torque control when target torque < average torque at current speed.

#### Torque Control Example
```
1. Set NiMotion torque mode: 2002h:01h = 3
   Send: 01 10 00 B1 00 01 02 00 03
2. Set torque source to digital: 2007h:01h = 0
   Send: 01 10 01 5E 00 01 02 00 00
3. Set torque limits: 2007h:0Ah = 1000, 2007h:0Bh = 1000 (100%)
   Send: 01 10 01 67 00 01 02 03 E8
   Send: 01 10 01 68 00 01 02 03 E8
4. Set speed limits: 2007h:10h = 3000, 2007h:11h = 3000
   Send: 01 10 01 6D 00 01 02 0B B8
   Send: 01 10 01 6E 00 01 02 0B B8
5. Set target torque: 2007h:04h = 1000 (100%)
   Send: 01 10 01 61 00 01 02 03 E8
6. Configure DI1 as enable, apply low level to run
```

---

### Multi-Segment Position Mode

Position control with up to 16 programmable segments.

#### Key Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Position Source | 2005h:01h | 010Dh | Set to 2 for multi-segment |
| Operation Mode | 2011h:01h | 0291h | 0=single, 1=loop, 2=DI switch |
| End Segment | 2011h:02h | 0292h | Last segment number |
| Loop Count | 2011h:04h | 0294h | Number of loops |
| Start Segment | 2011h:06h | 0296h | First segment number |
| Position Type | 2011h:05h | 0295h | 0=relative, 1=absolute |
| Segment 1 Position | 2011h:07h | 0297h | Position (user units, 32-bit) |
| Segment 1 Speed | 2011h:08h | 0299h | Max speed (rpm) |
| Segment 1 Accel/Decel | 2011h:09h | 029Ah | Accel/decel time (ms) |
| Segment 1 Wait Time | 2011h:0Ah | 029Bh | Wait after completion (ms) |
| Motion Profile Type | 6086h | 0402h | 0=trapezoidal, 3=S-curve |
| Position Limits | 607Dh | 03EFh~03F1h | Software position limits |

#### Operation Modes

| Value | Mode | Description |
|-------|------|-------------|
| 0 | Single Run | Segments 1-16 run once |
| 1 | Loop | Loop from start to end segment |
| 2 | DI Switching | Segment selected by 4 DI terminals |

#### DI Switching Segment Selection

Uses DI terminals configured as functions 6,7,8,9 to form 4-bit binary number:

| Fun9 | Fun8 | Fun7 | Fun6 | Segment |
|------|------|------|------|---------|
| 0 | 0 | 0 | 0 | 1 |
| 0 | 0 | 0 | 1 | 2 |
| ... | ... | ... | ... | ... |
| 1 | 1 | 1 | 1 | 16 |

#### Multi-Segment Example (Single Run)
```
1. Set NiMotion position mode: 2002h:01h = 1
   Send: 01 10 00 B1 00 01 02 00 01
2. Set position source to multi-segment: 2005h:01h = 2
   Send: 01 10 01 0D 00 01 02 00 02
3. Set operation mode to single run: 2011h:01h = 0
   Send: 01 10 02 91 00 01 02 00 00
4. Set position type to relative: 2011h:05h = 0
   Send: 01 10 02 95 00 01 02 00 00
5. Set segment 1 position: 2011h:07h = 10000
   Send: 01 10 02 97 00 02 04 00 00 27 10
6. Set segment 1 speed: 2011h:08h = 500 (rpm)
   Send: 01 10 02 99 00 01 02 01 F4
7. Set segment 1 accel/decel: 2011h:09h = 500 (ms)
   Send: 01 10 02 9A 00 01 02 01 F4
8. Set segment 1 wait time: 2011h:0Ah = 1000 (ms)
   Send: 01 10 02 9B 00 01 02 03 E8
9. Configure DI1 as enable (func 1), DI2 as multi-segment enable (func 28)
10. Apply enables to run
```

---

### Multi-Speed Mode

Speed control with up to 16 programmable speed segments.

#### Key Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Aux Speed Source | 2006h:02h | 0149h | Set to 3 for multi-speed |
| Speed Selection | 2006h:03h | 014Ah | 1=auxiliary (multi-speed) |
| Operation Mode | 2012h:01h | 02E9h | 0=single, 1=loop, 2=DI switch |
| End Segment | 2012h:02h | 02EAh | Last segment number |
| Loop Count | 2012h:03h | 02EBh | Number of loops |
| Segment 1 Speed | 2012h:0Ch | 02F4h | Speed (rpm) |
| Segment 1 Run Time | 2012h:0Dh | 02F5h | Run time (ms) |
| Segment 1 Accel/Decel | 2012h:0Eh | 02F6h | Accel/decel time (ms) |

#### Multi-Speed Example (Single Run)
```
1. Set NiMotion speed mode: 2002h:01h = 2
   Send: 01 10 00 B1 00 01 02 00 02
2. Set aux speed source to multi-speed: 2006h:02h = 3
   Send: 01 10 01 49 00 01 02 00 03
3. Set speed selection to aux: 2006h:03h = 1
   Send: 01 10 01 4A 00 01 02 00 01
4. Set operation mode to single run: 2012h:01h = 0
   Send: 01 10 02 E9 00 01 02 00 00
5. Set segment 1 speed: 2012h:0Ch = 500 (rpm)
   Send: 01 10 02 F4 00 01 02 01 F4
6. Set segment 1 run time: 2012h:0Dh = 2000 (ms)
   Send: 01 10 02 F5 00 01 02 07 D0
7. Set segment 1 accel/decel: 2012h:0Eh = 500 (ms)
   Send: 01 10 02 F6 00 01 02 01 F4
8. Configure DI1 as enable (func 1), DI2 as multi-segment enable (func 28)
9. Apply enables to run
```

---

## Digital Inputs and Outputs

### Physical Digital Inputs (DI1-DI3)

Configuration via 2003h (00D5h~00E6h) parameter group.

#### DI Function Numbers

| Number | Function |
|--------|----------|
| 0 | Undefined |
| 1 | Motor enable (NiMotion mode only) |
| 2 | Alarm reset |
| 6 | Multi-segment command switching 1 |
| 7 | Multi-segment command switching 2 |
| 8 | Multi-segment command switching 3 |
| 9 | Multi-segment command switching 4 |
| 12 | Pause |
| 14 | Positive limit switch |
| 15 | Negative limit switch |
| 20 | Step amount enable |
| 21 | NiMotion speed mode direction |
| 28 | Multi-segment position/speed enable |
| 31 | Home switch |
| 33 | Set origin |
| 36 | Analog input direction control |
| 38 | Clear fault history |
| 39 | Clear power-up time |
| 40 | Quadrature pulse input A (DI1 only) |
| 41 | Quadrature pulse input B (DI2 only) |
| 42 | Pulse input (DI1 only) |
| 43 | Pulse direction (DI2 only) |
| 44 | Duty cycle input (DI1 only) |
| 45 | Duty cycle direction (DI2 only) |

#### DI Logic Selection

| Value | Logic |
|-------|-------|
| 0 | Active Low |
| 1 | Active High |
| 2 | Rising edge |
| 3 | Falling edge |
| 4 | Both edges |

**Notes:**
- Different terminals cannot have the same function number
- Digital inputs are sampled every 1ms - cannot handle signals < 1ms
- For HM mode, functions 14, 15, 31 must be configured

#### DI Configuration Example
```
Configure DI1 as positive limit switch, active low:
Send: 01 10 00 D5 00 01 02 00 0E (function = 14)
Send: 01 10 00 D6 00 01 02 00 00 (logic = active low)
```

### Virtual Digital Inputs (VDI1-VDI16)

Configuration via 2017h (0326h~0346h) parameter group.

#### VDI Control Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| VDI Enable | 200Ch:07h | 0235h | 0=disable, 1=enable VDI |
| VDI Level State | 2031h:01h | 0373h | Bit0=VDI1...Bit15=VDI16 |

#### VDI Logic Selection

| Value | Logic |
|-------|-------|
| 0 | Active High |
| 1 | Rising edge |

### Digital Outputs

Configuration via 2004h (00F8h~0101h) parameter group.

#### DO Function Numbers

| Number | Function |
|--------|----------|
| 0 | Configure as input |
| 1 | Configure as output |
| 2 | Motor running/stopped |
| 3 | Target reached |
| 4 | Alarm output |
| 5 | Brake output |
| 6 | External braking resistor |
| 30 | Brake power saving output |

#### DO Logic Selection

| Value | Logic |
|-------|-------|
| 0 | Active Low |
| 1 | Active High |

#### DO Control Register

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| DO State | 2031h:02h | 0374h | Communication DO output (bit0=DO1) |

#### DO Configuration Example
```
Configure DO1 as general output, active high, turn on:
Send: 01 10 00 F8 00 01 02 00 01 (function = output)
Send: 01 10 00 F9 00 01 02 00 01 (logic = active high)
Send: 01 10 03 74 00 01 02 00 01 (output = on)
```

---

## Analog Input Control

Analog input range: 0-10V

### Analog Input Parameters

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| AI1 Bias | 2003h:17h | 00E9h | Bias (1mV units) |
| AI1 Filter | 2003h:18h | 00EAh | Filter time constant (0.01ms) |
| AI1 Dead-band | 2003h:19h | 00EBh | Dead-band (1mV units) |
| AI1 Multiplier | 2003h:1Ah | 00ECh | Gain (0.001 units) |
| AI Position Value | 2005h:2Ch | 0142h | Position for 10V (encoder units) |
| AI Speed Value | 2003h:1Fh | 00F1h | Speed for 10V (rpm) |
| AI Torque Value | 2003h:20h | 00F2h | Torque for 10V (0.1%) |

### Analog Position Control

Position source: 2005h:01h = 3 (Mode 1) or 4 (Mode 2)

**Mode 1:** Position = Direction × AI_Position_10V × (Voltage × Multiplier + Bias) / 10000
- Direction controlled by DI function 36

**Mode 2:**
- 5-10V: Positive position
- 0-5V: Negative position

### Analog Speed Control

Speed source: 2006h:01h = 1 (analog), 2006h:03h = 0 (main)

**Mode 1:** Speed = Direction × AI_Speed_10V × (Voltage × Multiplier + Bias) / 10000

**Mode 2:**
- 5-10V: Forward speed
- 0-5V: Reverse speed

### Analog Torque Control

Torque source: 2007h:01h = 1 (analog), 2007h:03h = 0 (main)

**Mode 1:** Torque = Direction × AI_Torque_10V × (Voltage × Multiplier + Bias) / 10000

**Mode 2:**
- 5-10V: Positive torque
- 0-5V: Negative torque

---

## Holding Brake Settings

Brake output automatically controlled by CiA402 state machine.

### Brake Control Registers

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Brake Delay | 2002h:0Ah | 00BAh | Brake off to motor off delay (ms) |
| Gravity Preset Enable | 200Ah:1Fh | 01D8h | 0=no preset, 1=enable |
| Gravity Preset Value | 200Ah:20h | 01D9h | Torque at brake release (0.1%) |
| Gravity Recognition | 200Dh:0Bh | 0254h | 0=disable, 1=enable online |
| Brake Duty Cycle | 2002h:04h | 00B4h | PWM duty cycle 1-100% |

### Brake Output Configuration

Configure DO for brake function:
```
Set DX1 function to brake output (5):
2004h:01h = 5
```

**Notes for vertical axis applications:**
- Enable gravity preset to prevent load drop during brake release
- Enable online gravity recognition (auto-updates when speed < 300rpm)
- Set appropriate brake delay time

---

## Motor Protection

### I²t Overload Protection

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Rated Current | 2000h:09h | 0065h | Rated current (0.01A) |
| Max Current | 2000h:0Ah | 0066h | Maximum current (0.01A) |
| Max Current Duration | 2000h:0Bh | 0067h | Max current time (0.1s) |

### Braking Resistor Settings

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Brake Type | 2002h:13h | 00C3h | 0=internal, 1=external (power-on effective) |
| Brake Voltage | 2001h:0Fh | 0093h | Braking trigger voltage (default 55V) |

**Built-in Braking Resistor Specs:**

| Motor Model | Resistance | Power | Handling Power |
|-------------|------------|-------|----------------|
| PMM4010B (100W) | 50Ω | 10W | 3W |
| PMM6020B (200W) | 15Ω | 25W | 8W |
| PMM6040B (400W) | 15Ω | 25W | 8W |
| PMM8075B (750W) | 15Ω | 35W | 11W |

**External Braking Resistor Power Calculation:**
```
P = 2 × (N+1) × E / T
Where: N = load/motor inertia ratio, E = braking energy (J), T = motion period (s)
Use at 30% rated power: P_actual = P / 0.3
```

---

## Parameter Management

### Save Parameters

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Save Parameters | 1010h:01h | 0026h | Write 0x65766173 ("save") to save to user area |
| Save NiMotion | 1010h:0Bh | 003Ah | Write 0x65766173 to save NiMotion params |

**Save Command:** 0x65766173 (ASCII "save")
```
Send: 01 10 00 26 00 02 04 65 76 61 73 [CRC]
```

### Restore Factory Parameters

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Restore Parameters | 1011h:01h | 003Ch | Write 0x64616F6C to restore factory params |

**Restore Command:** 0x64616F6C (ASCII "load")

---

## Position Recovery Function

Allows motor to regain absolute position after power cycle.

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Recovery Method | 2005h:18h | 012Ah | 0=multi-turn, 1=single-turn |
| Return Direction | 2005h:1Dh | 012Fh | Direction for return to zero |

---

## Absolute Encoder Battery

Battery voltage monitored at power-up and stored in 200Fh:0Bh.

| Voltage | Warning Code | Action |
|---------|--------------|--------|
| 2.4V < DC < 2.6V | 0x7302 | Battery replacement recommended |
| DC ≤ 2.4V | 0x7301 | Replace battery immediately |
| DC ≥ 2.6V | 0x7309 | Contact support for recalibration |

**Battery Replacement:** Power on motor (non-operational), replace battery, alarm auto-clears.

---

## STO (Safe Torque Off) Function

Hardware safety function via STO1/STO2 terminals.

| STO1 | STO2 | Motor Current |
|------|------|---------------|
| HIGH | HIGH | Normal operation |
| LOW | HIGH | Blocked |
| HIGH | LOW | Blocked |
| LOW | LOW | Blocked |

**Both STO1 and STO2 must be connected to +24VDC for normal operation.**

---

## Communication Watchdog

Prevents motor from running if communication is lost.

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Watchdog Time | H0249 | 0249h | Timeout in ms (0=disabled) |

**Fault Code:** 0x7501 on watchdog timeout

**Example - Enable 100ms watchdog:**
```
Send: 01 10 02 49 00 01 02 00 64 (set to 100ms)
```
**Feed watchdog:** Send same command periodically to reset timer.

---

## Gain Adjustment

### Control Loop Parameters

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Speed Loop Gain | 2008h:01h | 0178h | Velocity gain (0.1Hz units) |
| Speed Integral Time | 2008h:02h | 0179h | Integration time (0.01ms units) |
| Position Loop Gain | 2008h:03h | 017Ah | Position gain (Hz units) |
| Speed FF Filter | 2008h:0Fh | 0186h | Speed feedforward filter (0.01ms) |
| Speed FF Gain | 2008h:10h | 0187h | Speed feedforward gain |
| Torque FF Filter | 2008h:11h | 0188h | Torque feedforward filter (0.01ms) |
| Torque FF Gain | 2008h:12h | 0189h | Torque feedforward gain |
| Torque Cmd Filter | 2007h:06h | 0163h | Torque command filter (0.01ms) |

### Second Gain Set (for gain switching)

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Speed Gain 2 | 2008h:04h | 017Bh | Second speed loop gain |
| Speed Integral 2 | 2008h:05h | 017Ch | Second speed integral time |
| Position Gain 2 | 2008h:06h | 017Dh | Second position loop gain |
| Gain Switch Mode | 2008h:08h | 017Fh | Switching condition (0-9) |

### Rigidity Table (Quick Tuning)

| Rigidity | Position Gain (Hz) | Speed Gain (0.1Hz) | Speed Integral (0.01ms) |
|----------|-------------------|--------------------|------------------------|
| 1 | 2 | 15 | 37000 |
| 5 | 5 | 35 | 16000 |
| 10 | 14 | 110 | 5000 |
| 12 | 32 | 180 | 3100 |
| 13 | 39 | 220 | 2500 |
| 20 | 162 | 900 | 800 |
| 25 | 449 | 2500 | 400 |
| 32 | 900 | 5000 | 200 |

**Recommendation:** Start with rigidity 12-13 for no-load, increase gradually.

---

## Vibration Suppression

### Notch Filters (4 available)

| Parameter | Notch 1 | Notch 2 | Notch 3 | Notch 4 |
|-----------|---------|---------|---------|---------|
| Frequency (Hz) | 2009h:0Dh (019Eh) | 2009h:10h (01A1h) | 2009h:13h (01A4h) | 2009h:16h (01A7h) |
| Width (Hz) | 2009h:0Eh (019Fh) | 2009h:11h (01A2h) | 2009h:14h (01A5h) | 2009h:17h (01A8h) |
| Depth (%) | 2009h:0Fh (01A0h) | 2009h:12h (01A3h) | 2009h:15h (01A6h) | 2009h:18h (01A9h) |

**Note:** Depth=0 disables the notch filter. Depth=100 completely suppresses the center frequency.

### Low-Frequency Vibration Suppression

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| LF Mode | 2009h:05h | 0196h | 0=off, 1=on |
| LF Frequency | 2009h:1Dh | 01AEh | Center frequency (0.1Hz, range 10-1000) |
| LF Width | 2009h:1Eh | 01AFh | Width level (%, range 0-100) |
| Damping Ratio | 2009h:23h | 01B5h | Damping coefficient (default 5, range 0-50) |

---

## Fault Management

### Alarm History

| Register | Index | Modbus | Description |
|----------|-------|--------|-------------|
| Fault Count | 1003h:00h | 0001h | Number of faults in history |
| Fault 1 (newest) | 1003h:01h | 0002h | Most recent fault code |
| Fault 16 (oldest) | 1003h:10h | 0020h | Oldest fault code |
| Current Error | 603Fh | 037Fh | Current error code (lower 16 bits) |

### Common Alarm Codes

| Code | Description | Type | Self-Reset |
|------|-------------|------|------------|
| 0x2300 | Motor overcurrent | Fault | No |
| 0x2311 | Motor overload | Warning | Yes |
| 0x2312 | Motor stalling | Pause+lock | No |
| 0x3210 | Power overvoltage | Fault | Yes |
| 0x3220 | Power undervoltage | Fault | Yes |
| 0x4210 | Over temperature | Fault | Yes |
| 0x4220 | Low temperature | Fault | Yes |
| 0x6320 | Parameter setting error | Fault | Yes |
| 0x7301 | Encoder battery low voltage | Fault | No |
| 0x7302 | Encoder battery warning | Warning | Yes |
| 0x7310 | Overspeed | Fault | Yes |
| 0x7501 | Communication watchdog timeout | Warning | Yes |
| 0x8610 | Homing timeout | Fault | No |
| 0x8611 | Following error | Fault | No |
| 0x8613 | Software limit error | Pause+lock | No |
| 0x8614 | Limit switch error | Pause+lock | No |

### Fault Response Codes

| Code | Action |
|------|--------|
| 0 | Switch to fault state, follow 605Eh setting |
| 1 | Switch to fault state, slow curve stop |
| 2 | Switch to fault state, fast curve stop |
| 3 | Quick stop, pause and lock shaft (no fault state) |
| 4 | Warning only, no state change |
| 5 | Ignore and log in 1003h |
| 6 | Ignore, do not log |

### Fault Reset

Write rising edge to Control Word bit 7:
```
Send: 01 10 03 80 00 01 02 00 80 (fault reset)
```

Alternative methods:
1. Configure physical DI for alarm reset (function 2)
2. Configure virtual DI for alarm reset (function 2)

### Fault Detection Details

| Fault Type | Trigger Condition |
|------------|-------------------|
| I²t Overload | Current > rated, integral > max_current × max_duration |
| Blocking | Speed < 5rpm, current > rated, integral exceeded |
| High Temperature | Drive temp > 105°C (clears at 70°C) |
| Low Temperature | Drive temp < -25°C (clears at -20°C) |
| Overvoltage | Voltage > 2001h:0Eh threshold |
| Undervoltage | Voltage < 2001h:10h threshold |
| Overspeed | Speed > 200Ah:06h for > 10ms |
| Home Timeout | Homing not complete within 2005h:1Ch limit |
| Tracking Error | Position error > ±6065h for time > 6066h |
| Software Overrun | Actual position exceeds 607Dh limits |
| Target Overflow | After gear ratio, position exceeds int32 range |
| Encoder Low Voltage | Battery ≤ 2.4V → fault 0x1007301 |
| Encoder Warning | Battery 2.4-2.6V → alarm 0x4017302 |
| Encoder Communication | Communication failure → 0x7303 |
| Encoder Multi-turn Error | Not calibrated → 0x7304 |
| Encoder Internal Fault | Abnormal restart → 0x7309 |

### STO Fault Codes

| Code | Description |
|------|-------------|
| 0xFF05 | STO_1 failed to close (signal high, power disconnected) |
| 0xFF06 | STO_1 failed to enable (signal low, power connected) |
| 0xFF07 | STO_2 failed to close |
| 0xFF08 | STO_2 failed to enable |
| 0xFF09 | STO input abnormal (one high, one low > 6ms) |
| 0xFF0A | STO enabled state (power and drive cut off) |

---

## NiMotion Protocol

Extended Modbus protocol with process data and synchronization messages for multi-motor coordination.

### Protocol Features

- **R_PDO**: Receive process data (master → slave)
- **T_PDO**: Transmit process data (slave → master)
- Multi-command control in single frame
- Synchronized multi-motor operation

### Transmission Modes

**Asynchronous Mode:**
- Unicast: Slave processes and responds
- Broadcast: Slaves process but don't respond

**Synchronous Mode:**
- Broadcast process data: Slaves cache data
- Broadcast sync message: All slaves process simultaneously

### Synchronization Message Format

Fixed format broadcast message to trigger buffered data processing.

| Field | Bytes | Value | Description |
|-------|-------|-------|-------------|
| Address | 1 | 0x00 | Broadcast mode |
| Function Code | 1 | 0x10 | Write multiple registers |
| Register Address | 2 | 0x8000 | Sync message identifier |
| Number of Registers | 2 | 0x0001 | 1 register |
| Byte Count | 1 | 0x02 | 2 bytes data |
| Register Value | 2 | 0x6688 | Sync flag (fixed) |
| CRC | 2 | - | CRC-16 |

**Example Sync Message:**
```
00 10 80 00 00 01 02 66 88 [CRC]
```

### Process Data Write Message (R_PDO)

| Field | Bytes | Value | Description |
|-------|-------|-------|-------------|
| Address | 1 | 0x00/0x01-0xF7 | Broadcast/unicast |
| Function Code | 1 | 0x10 | Write multiple registers |
| Register Address | 2 | 0x8300 | Process data identifier |
| Number of Registers | 2 | 0x0001-0x0021 | 1-33 registers |
| Byte Count | 1 | 0x02-0x42 | 2-66 bytes |
| Motor Address | 2 | 0x0000-0x00F7 | Target motor (0=all) |
| Register Values | 2×N | - | Mapped register data |
| CRC | 2 | - | CRC-16 |

### Process Data Read Message (T_PDO)

Only available in asynchronous mode.

| Field | Bytes | Value | Description |
|-------|-------|-------|-------------|
| Address | 1 | 0x01-0xF7 | Node address |
| Function Code | 1 | 0x04 | Read input registers |
| Register Address | 2 | 0x8380 | Buffer address |
| Number of Registers | 2 | 0x0001-0x0020 | 1-32 registers |
| CRC | 2 | - | CRC-16 |

### PDO Mapping Configuration

| Address | Name | Description |
|---------|------|-------------|
| 0x5000 | R_PDO Entry Count | Number of R_PDO mapping entries (0-12) |
| 0x5002-0x5018 | R_PDO Map 1-12 | High word: start address, Low word: register count |
| 0x6000 | T_PDO Entry Count | Number of T_PDO mapping entries (0-12) |
| 0x6002-0x6018 | T_PDO Map 1-12 | High word: start address, Low word: register count |

**Mapping Value Format:** 0xAAAA00NN
- AAAA: Register start address
- NN: Number of registers

**Example:** R_PDO Map 1 = 0x02310001 → Map baud rate (0x0231), 1 register

### Synchronization Mode Setup

1. Set R_PDO mapping entry count (0x5000)
2. Configure R_PDO mappings (0x5002+)
3. Set T_PDO mapping entry count (0x6000)
4. Configure T_PDO mappings (0x6002+)
5. Enable sync mode: 200Ch:18h (0x0246) = 0x01
6. Save parameters and restart

### Sync Mode Example

**Setup Motor #1:**
```
1. Set RPDO entries = 2:
   01 10 50 00 00 02 04 00 00 00 02 [CRC]

2. Map control word (0380h) and target position (03E7h):
   01 10 50 02 00 04 08 03 80 00 01 03 E7 00 02 [CRC]

3. Enable sync mode:
   01 10 02 46 00 01 02 00 01 [CRC]

4. Save parameters:
   01 10 00 26 00 02 04 65 76 61 73 [CRC]
```

**Send Process Data (control=6, position=1000):**
```
00 10 83 00 00 04 08 00 01 00 06 00 00 03 E8 [CRC]
```

**Send Sync Message to Execute:**
```
00 10 80 00 00 01 02 66 88 [CRC]
```

---

## Object Dictionary Details

### Data Types

| Type | Range | Size |
|------|-------|------|
| Int8 | -128 to 127 | 1 byte |
| Int16 | -32768 to 32767 | 2 bytes |
| Int32 | -2147483648 to 2147483647 | 4 bytes |
| Uint8 | 0 to 255 | 1 byte |
| Uint16 | 0 to 65535 | 2 bytes |
| Uint32 | 0 to 4294967295 | 4 bytes |
| String | ASCII | Variable |

### Accessibility

| Code | Meaning |
|------|---------|
| RW | Read/Write |
| RO | Read Only |
| WO | Write Only |

### Mappability

| Code | Meaning |
|------|---------|
| NO | Not mappable in PDO |
| RPDO | Can be mapped as R_PDO |
| TPDO | Can be mapped as T_PDO |

### Activation Modes

| Mode | Description |
|------|-------------|
| Immediate | Takes effect immediately |
| Suspension | Takes effect when not in operation state |
| Re-energized | Takes effect after power cycle |

### Communication Parameters (1000h Group)

| Index:Sub | Modbus | Name | Type | Access |
|-----------|--------|------|------|--------|
| 1001h | 0000h | Error Register | Uint8 | RO |
| 1003h:00h | 0001h | Alarm Count | Uint8 | RO |
| 1003h:01h-10h | 0002h-0020h | Alarm History 1-16 | Uint32 | RO |
| 1010h:01h | 0026h | Save All Parameters | Uint32 | RW |
| 1011h:01h | 003Ch | Restore Parameters | Uint32 | RW |
| 1017h | 0052h | Heartbeat Time | Uint16 | RW |
| 1018h:03h | 0053h | Software Version | Uint32 | RO |
| 1018h:04h | 0055h | Serial Number | Uint32 | RO |

### Motor Parameters (2000h Group)

| Index:Sub | Modbus | Name | Unit | Default |
|-----------|--------|------|------|---------|
| 2000h:06h | 0062h | Encoder Type | - | 1 |
| 2000h:07h | 0063h | Rated Voltage | 1V | 48 |
| 2000h:08h | 0064h | Rated Power | 0.01kW | 40 |
| 2000h:09h | 0065h | Rated Current | 0.01A | 1250 |
| 2000h:0Ah | 0066h | Max Current | 0.01A | 2250 |
| 2000h:0Bh | 0067h | Max Current Duration | 0.1s | 3000 |
| 2000h:0Ch | 0068h | Rated Torque | 0.01Nm | 127 |
| 2000h:0Dh | 0069h | Max Torque | 0.01Nm | 2000 |
| 2000h:0Eh | 006Ah | Rated Speed | 1rpm | 3000 |
| 2000h:0Fh | 006Bh | Max Speed | 1rpm | 6000 |
| 2000h:10h | 006Ch | Inertia Jm | 0.01kg·cm² | 30 |
| 2000h:11h | 006Dh | Pole Pairs | 1 | 4 |
| 2000h:12h | 006Eh | Stator Resistance | 0.001Ω | 115 |
| 2000h:13h | 006Fh | Stator Lq | 0.01mH | 25 |
| 2000h:14h | 0070h | Stator Ld | 0.01mH | 25 |
| 2000h:16h | 0072h | Torque Coeff Kt | 0.01Nm/Arms | 11 |
| 2000h:19h | 0075h | Encoder Bits | 1bit | 14 |
| 2000h:1Ah | 0077h | Encoder Poles | 1 | 1 |

### Drive Parameters (2001h Group)

| Index:Sub | Modbus | Name | Unit | Default |
|-----------|--------|------|------|---------|
| 2001h:07h | 008Bh | Rated Output Current | 0.01A | 1200 |
| 2001h:08h | 008Ch | Max Output Current | 0.01A | 1500 |
| 2001h:0Dh | 0091h | Switching Dead Time | μs | 100 |
| 2001h:0Eh | 0092h | Overvoltage Threshold | 1V | 100 |
| 2001h:0Fh | 0093h | DC Bus Voltage Relief Point | 1V | 55 |
| 2001h:10h | 0094h | Undervoltage Threshold | 1V | 24 |
| 2001h:11h | 0095h | Overcurrent Protection | 1A | 10 |
| 2001h:18h | 009Ch | Current Sampling Filter | 0.01 | 100 |
| 2001h:1Ch | 00A0h | Current Loop Cutoff Freq | 1Hz | 800 |
| 2001h:1Dh | 00A1h | Open Loop Operating Current | 0.01A | 625 |

### Basic Control Parameters (2002h Group)

| Index:Sub | Modbus | Name | Unit | Default | Activate |
|-----------|--------|------|------|---------|----------|
| 2002h:01h | 00B1h | Control Mode Selection | - | 4 | Immediate |
| 2002h:04h | 00B4h | Output Pulse Duty Cycle | 1% | 50 | Suspension |
| 2002h:13h | 00C3h | Int/Ext Brake Resistor | 1 | 0 | Re-energized |
| 2002h:1Ch | 00CDh | Firmware Code | - | 0 | RO |
| 2002h:1Eh | 00CFh | IAP Software Version | - | 0 | RO |
| 2002h:1Fh | 00D1h | Hardware Version | - | 0 | RO |

**Control Mode Selection (2002h:01h):**
| Value | Mode |
|-------|------|
| 0 | CiA402 mode |
| 1 | NiMotion position mode |
| 2 | NiMotion speed mode |
| 3 | NiMotion torque mode |
| 4 | NiMotion open-loop mode |
| 5 | Offline motor parameter identification |

### Terminal Input Parameters (2003h Group)

| Index:Sub | Modbus | Name | Range | Default |
|-----------|--------|------|-------|---------|
| 2003h:03h | 00D5h | DI1 Function | 0-55 | 1 |
| 2003h:04h | 00D6h | DI1 Logic | 0-4 | 0 |
| 2003h:05h | 00D7h | DI2 Function | 0-48 | 2 |
| 2003h:06h | 00D8h | DI2 Logic | 0-4 | 2 |
| 2003h:07h | 00D9h | DI3 Function | 0-48 | 12 |
| 2003h:08h | 00DAh | DI3 Logic | 0-4 | 0 |
| 2003h:09h-14h | 00DBh-00E6h | DI4-DI9 Func/Logic | - | 0 |
| 2003h:15h | 00E7h | Power-Up Effective Func | 0-65535 | 0 |
| 2003h:17h | 00E9h | AI1 Bias | 1mV | 0 |
| 2003h:18h | 00EAh | AI1 Filter Time | - | 0 |
| 2003h:19h | 00EBh | AI1 Dead Zone | 1mV | 0 |
| 2003h:1Ah | 00ECh | AI1 Multiplier | 0.001 | 0 |
| 2003h:1Fh | 00F1h | AI 10V Speed Value | rpm | 0 |
| 2003h:20h | 00F2h | AI 10V Torque Value | 0.1% | 0 |

### Terminal Output Parameters (2004h Group)

| Index:Sub | Modbus | Name | Range | Default |
|-----------|--------|------|-------|---------|
| 2004h:01h | 00F8h | DO1 Function | 0-30 | 0 |
| 2004h:02h | 00F9h | DO1 Logic | 0-1 | 0 |
| 2004h:03h-0Ah | 00FAh-0101h | DO2-DO5 Func/Logic | - | 0 |

### Position Control Parameters (2005h Group)

| Index:Sub | Modbus | Name | Unit | Default |
|-----------|--------|------|------|---------|
| 2005h:01h | 010Dh | Position Command Source | - | 1 |
| 2005h:05h | 0112h | Step Size | inc | 100 |
| 2005h:1Ch | 012Eh | Home Return Time Limit | ms | 10000 |

### Speed Control Parameters (2006h Group)

| Index:Sub | Modbus | Name | Unit | Default | Activate |
|-----------|--------|------|------|---------|----------|
| 2006h:01h | 0148h | Main Speed Source A | - | 0 | Suspension |
| 2006h:02h | 0149h | Aux Speed Source B | - | 0 | Suspension |
| 2006h:03h | 014Ah | Speed Command Selection | - | 0 | Suspension |
| 2006h:04h | 014Bh | Speed Keypad Setpoint | 1rpm | 10 | Immediate |
| 2006h:06h | 014Dh | Effective Speed Value | 1rpm | 0 | Immediate |
| 2006h:07h | 014Eh | Accel Ramp Time | 1ms | 10 | Immediate |
| 2006h:08h | 014Fh | Decel Ramp Time | 1ms | 10 | Immediate |
| 2006h:09h | 0150h | Max RPM Threshold | 1rpm | 6000 | Immediate |
| 2006h:0Ah | 0151h | Forward Velocity Threshold | 1rpm | 4000 | Immediate |
| 2006h:0Bh | 0152h | Reverse Velocity Threshold | 1rpm | 4000 | Immediate |
| 2006h:12h | 0159h | Speed Feedback Unit Select | - | 0 | Suspension |

**Speed Command Selection (2006h:03h):**
- 0: A only (2006h:01h active)
- 1: B only (2006h:02h active)
- 2: A+B (both active)

### Torque Control Parameters (2007h Group)

| Index:Sub | Modbus | Name | Unit | Default | Activate |
|-----------|--------|------|------|---------|----------|
| 2007h:01h | 015Eh | Main Torque Source A | - | 0 | Suspension |
| 2007h:02h | 015Fh | Aux Torque Source B | - | 0 | Suspension |
| 2007h:03h | 0160h | Torque Command Selection | - | 0 | Suspension |
| 2007h:04h | 0161h | Torque Keypad Setpoint | 0.1% | 10 | Suspension |
| 2007h:05h | 0162h | Effective Torque Setting | 0.1% | 10 | Suspension |
| 2007h:06h | 0163h | Torque Command Filter | 0.01ms | 0 | Immediate |
| 2007h:0Ah | 0167h | Positive Torque Limit | 0.1% | 1000 | Immediate |
| 2007h:0Bh | 0168h | Reverse Torque Limit | 0.1% | 1000 | Immediate |
| 2007h:10h | 016Dh | Forward Speed Limit | 1rpm | 3000 | Immediate |
| 2007h:11h | 016Eh | Reverse Speed Limit | 1rpm | 3000 | Immediate |
| 2007h:13h | 0170h | Blocking Home Torque | 0.1% | 500 | - |
| 2007h:15h | 0172h | Blocking Home Time | ms | 500 | - |

### Gain Parameters (2008h Group)

| Index:Sub | Modbus | Name | Unit | Range | Default |
|-----------|--------|------|------|-------|---------|
| 2008h:01h | 0178h | Velocity Loop Gain | 0.1Hz | 1-20000 | 500 |
| 2008h:02h | 0179h | Velocity Loop Int Time | 0.01ms | 0-51200 | 800 |
| 2008h:03h | 017Ah | Position Loop Gain | 1 | 0-20000 | 1500 |
| 2008h:04h | 017Bh | Second Velocity Gain | 0.1Hz | 1-20000 | 1 |
| 2008h:05h | 017Ch | Second Velocity Int Time | 0.01ms | 0-51200 | 15 |
| 2008h:06h | 017Dh | Second Position Gain | 1 | 0-20000 | 0 |
| 2008h:08h | 017Fh | Second Gain Mode | - | 0-9 | 0 |
| 2008h:09h | 0180h | Gain Switch Condition | - | 0-10 | 0 |
| 2008h:0Ah | 0181h | Gain Switch Delay | 0.1ms | 0-10000 | 0 |
| 2008h:0Bh | 0182h | Gain Switch Level | 1 | 0-20000 | 0 |
| 2008h:0Ch | 0183h | Gain Switch Time Lag | 1 | 0-20000 | 0 |
| 2008h:0Fh | 0186h | Velocity FF Filter | 0.01ms | 0-65535 | 0 |
| 2008h:10h | 0187h | Velocity FF Gain | 0.1% | 0-65535 | 0 |
| 2008h:11h | 0188h | Torque FF Filter | 0.01ms | 0-65535 | 0 |
| 2008h:12h | 0189h | Torque FF Gain | 0.001 | 0-65535 | 0 |
| 2008h:14h | 018Bh | Velocity Feedback LPF | 1Hz | 0-4000 | 900 |

**Notes:**
- Velocity Loop Gain: Larger = faster response, but may cause vibration
- Velocity Int Time: Smaller = stronger integration, 51200 = no integration
- Position Loop Gain: Larger = shorter positioning time, may cause vibration

### Notch Filter Parameters (2009h Group)

| Index:Sub | Modbus | Name | Unit | Range | Default |
|-----------|--------|------|------|-------|---------|
| 2009h:0Dh | 019Eh | Notch 1 Frequency | 1Hz | 0-2000 | 0 |
| 2009h:0Eh | 019Fh | Notch 1 Width | 1Hz | 0-2000 | 0 |
| 2009h:0Fh | 01A0h | Notch 1 Depth | % | 0-100 | 0 |
| 2009h:10h | 01A1h | Notch 2 Frequency | 1Hz | 0-2000 | 0 |
| 2009h:11h | 01A2h | Notch 2 Width | 1Hz | 0-2000 | 0 |
| 2009h:12h | 01A3h | Notch 2 Depth | % | 0-100 | 0 |
| 2009h:13h-18h | 01A4h-01A9h | Notch 3-4 | - | - | 0 |

### Monitoring Parameters (200Bh Group)

| Index:Sub | Modbus | Name | Unit | Access |
|-----------|--------|------|------|--------|
| 200Bh:01h | 01DEh | Motor Driver Status | - | RO |
| 200Bh:02h | 01DFh | Actual Motor Speed | 1rpm | RO |
| 200Bh:04h | 01E1h | Internal Torque Command | - | RO |
| 200Bh:05h | 01E2h | DI Signal Monitor | - | RO |
| 200Bh:06h | 01E3h | DO Signal Monitor | - | RO |
| 200Bh:0Ah | 01E8h | Input PWM Frequency | 1Hz | RO |
| 200Bh:0Fh | 01F0h | Total Power-up Time | s | RO |
| 200Bh:10h | 01F2h | AI1 Voltage | mV | RO |
| 200Bh:11h | 01F3h | AI2 Voltage | mV | RO |
| 200Bh:12h | 01F4h | Phase A Current RMS | 0.01A | RO |
| 200Bh:13h | 01F5h | Phase B Current RMS | 0.01A | RO |
| 200Bh:14h | 01F6h | Phase C Current RMS | 0.01A | RO |
| 200Bh:15h | 01F7h | Bus Voltage | 0.1V | RO |
| 200Bh:16h | 01F8h | Module Temperature | 1°C | RO |
| 200Bh:2Dh | 0211h | Actual Speed (high res) | 0.1rpm | RO |

**Motor Driver Status (200Bh:01h):**
| Value | Status |
|-------|--------|
| 0 | Not ready |
| 1 | Ready |
| 6 | Position closed-loop |
| 8 | Speed closed-loop |
| 9 | Torque control |
| 10 | Open-loop control |
| 12 | Error |

### Communication Parameters (200Ch Group)

| Index:Sub | Modbus | Name | Range | Default | Activate |
|-----------|--------|------|-------|---------|----------|
| 200Ch:01h | 022Fh | Communication Method | 0-2 | 1 | Re-energized |
| 200Ch:02h | 0230h | Drive Axis Address | 1-247 | 1 | Re-energized |
| 200Ch:03h | 0231h | Serial Baud Rate | 0-9 | 5 | Re-energized |
| 200Ch:18h | 0246h | Sync Mode Enable | 0-1 | 0 | Re-energized |

**Communication Method (200Ch:01h):**
- 0: External pulse control (default CAN)
- 1: EtherCAT
- 2: CAN

### Encoder Parameters (200Fh Group)

| Index:Sub | Modbus | Name | Access |
|-----------|--------|------|--------|
| 200Fh:0Ah | 028Bh | Multi-turn Encoder Test | RO |
| 200Fh:0Bh | 028Ch | Encoder Battery Voltage (mV) | RO |
| 200Fh:0Ch | 028Dh | Encoder Calibration Cmd | RW |
| 200Fh:0Dh | 028Eh | Calibration Complete Detect | RO |
| 200Fh:0Eh | 028Fh | Encoder Zero Absolute A | RW |
| 200Fh:0Fh | 0290h | Encoder Zero Absolute B | RW |

### Multi-Segment Position Parameters (2011h Group)

| Index:Sub | Modbus | Name | Range | Unit |
|-----------|--------|------|-------|------|
| 2011h:01h | 0291h | Operation Mode | 0-2 | - |
| 2011h:02h | 0292h | End Segment Number | 1-16 | - |
| 2011h:04h | 0294h | Loop Count | 0-65535 | - |
| 2011h:05h | 0295h | Position Type | 0-1 | - |
| 2011h:06h | 0296h | Loop Start Segment | 0-16 | - |

**Per-Segment Parameters (Segment 1 shown, repeat for 2-16):**

| Index:Sub | Modbus | Name | Unit |
|-----------|--------|------|------|
| 2011h:07h | 0297h | Segment 1 Position | user unit |
| 2011h:08h | 0299h | Segment 1 Max Speed | rpm |
| 2011h:09h | 029Ah | Segment 1 Accel/Decel | ms |
| 2011h:0Ah | 029Bh | Segment 1 Wait Time | ms |

**Position Type (2011h:05h):**
- 0: Relative displacement
- 1: Absolute displacement

### Multi-Speed Parameters (2012h Group)

| Index:Sub | Modbus | Name | Range | Unit |
|-----------|--------|------|-------|------|
| 2012h:01h | 02E9h | Operation Mode | 0-2 | - |
| 2012h:02h | 02EAh | End Segment | 0-16 | - |
| 2012h:03h | 02EBh | Loop Count | 0-65535 | - |

**Per-Segment Speed Parameters (Segment 1 shown, repeat for 2-16):**

| Index:Sub | Modbus | Name | Unit |
|-----------|--------|------|------|
| 2012h:0Ch | 02F4h | Segment 1 Speed | rpm |
| 2012h:0Dh | 02F5h | Segment 1 Run Time | ms |
| 2012h:0Eh | 02F6h | Segment 1 Accel/Decel | ms |

### Virtual Input Terminal Parameters (2017h Group)

| Index:Sub | Modbus | Name | Range | Default |
|-----------|--------|------|-------|---------|
| 2017h:01h | 0326h | VDI1 Function | 0-44 | 0 |
| 2017h:02h | 0327h | VDI1 Logic | 0-1 | 0 |
| 2017h:03h-20h | 0328h-0345h | VDI2-VDI16 Func/Logic | - | 0 |

**VDI Logic Selection:**
- 0: Active High
- 1: Rising edge

### Communication Variables (2031h Group)

| Index:Sub | Modbus | Name | Description |
|-----------|--------|------|-------------|
| 2031h:01h | 0373h | VDI Virtual Levels | bit(n)=1 → VDI(n+1) high |
| 2031h:02h | 0374h | DO Output State | bit(n)=1 → DO(n+1) active |

---

## CiA402 Standard Object Dictionary (6000h Group)

### Error and Control Registers

| Index | Modbus | Name | Type | Access | PDO |
|-------|--------|------|------|--------|-----|
| 603Fh | 037Fh | Error Code | uint16 | RO | TPDO |
| 6040h | 0380h | Control Word | uint16 | RW | RPDO |
| 6041h | 0381h | Status Word | uint16 | RO | TPDO |

### VM Mode Registers

| Index:Sub | Modbus | Name | Type | Default | Unit |
|-----------|--------|------|------|---------|------|
| 6042h | 0382h | Target Velocity | int16 | 0 | rpm |
| 6043h | 0383h | Velocity Demand | int16 | 0 | rpm |
| 6044h | 0384h | Velocity Actual | int16 | 0 | rpm |
| 6046h:01h | 0385h | Min Velocity | uint32 | 10 | rpm |
| 6046h:02h | 0387h | Max Velocity | uint32 | 3000 | rpm |
| 6048h:01h | 0389h | Accel Delta Speed | uint32 | 500 | rpm |
| 6048h:02h | 038Bh | Accel Delta Time | uint16 | 1 | s |
| 6049h:01h | 038Ch | Decel Delta Speed | uint32 | 500 | rpm |
| 6049h:02h | 038Eh | Decel Delta Time | uint16 | 1 | s |
| 604Ah:01h | 038Fh | Quick Stop Speed | uint32 | 800 | rpm |
| 604Ah:02h | 0391h | Quick Stop Time | uint16 | 1 | s |
| 604Ch:01h | 0394h | Velocity Factor Num | int32 | 0 | - |
| 604Ch:02h | 0396h | Velocity Factor Den | int32 | 0 | - |

### Stop Mode Registers

| Index | Modbus | Name | Range | Default |
|-------|--------|------|-------|---------|
| 605Ah | 03BFh | Quick Stop Option | 0-2 | 2 |
| 605Bh | 03BDh | Shutdown Option | 0-1 | 0 |
| 605Ch | 03BEh | Disable Operation Option | 0-1 | 0 |
| 605Dh | 03C0h | Halt Option | 1-2 | 1 |
| 605Eh | 03C1h | Fault Response Option | 0-2 | 0 |

### Operating Mode Registers

| Index | Modbus | Name | Type | Access | PDO |
|-------|--------|------|------|--------|-----|
| 6060h | 03C2h | Operation Mode | int8 | RW | RPDO |
| 6061h | 03C3h | Operation Mode Display | int8 | RO | TPDO |

### Position Registers

| Index | Modbus | Name | Type | Unit |
|-------|--------|------|------|------|
| 6062h | 03C4h | Position Demand | int32 | user unit |
| 6063h | 03C6h | Position Actual (enc) | int32 | encoder unit |
| 6064h | 03C8h | Position Actual (user) | int32 | user unit |
| 607Ah | 03E7h | Target Position | int32 | user unit |
| 607Ch | 03EDh | Home Offset | int32 | user unit |
| 607Dh:01h | 03EFh | Software Limit Min | int32 | user unit |
| 607Dh:02h | 03F1h | Software Limit Max | int32 | user unit |

### Position Window Registers

| Index | Modbus | Name | Default | Unit |
|-------|--------|------|---------|------|
| 6065h | 03CAh | Following Error Window | 50 | user unit |
| 6066h | 03CCh | Following Error Timeout | 30000 | ms |
| 6067h | 03CDh | Position Window | 10 | user unit |
| 6068h | 03CFh | Position Window Time | 5 | ms |

### Velocity Registers

| Index | Modbus | Name | Type | Unit |
|-------|--------|------|------|------|
| 6069h | 03D0h | Velocity Sensor | int32 | user unit/s |
| 606Bh | 03D3h | Velocity Demand | int32 | user unit/s |
| 606Ch | 03D5h | Velocity Actual | int32 | rpm |
| 606Dh | 03D7h | Velocity Window | uint16 | rpm |
| 606Eh | 03D8h | Velocity Window Time | uint16 | ms |
| 606Fh | 03D9h | Zero Speed Window | uint16 | user unit/s |
| 6070h | 03DAh | Zero Speed Time | uint16 | ms |

### Torque Registers

| Index | Modbus | Name | Range | Default | Unit |
|-------|--------|------|-------|---------|------|
| 6071h | 03DBh | Target Torque | -1000~1000 | 0 | 0.1% |
| 6072h | 03DCh | Max Torque | 0-2000 | 1000 | 0.1% |
| 6073h | 03DDh | Max Current | 0-2000 | 1500 | 0.1% |
| 6074h | 03DEh | Torque Demand | RO | - | 0.1% |
| 6075h | 03DFh | Rated Current | 0-11700 | 11700 | 0.001A |
| 6076h | 03E1h | Rated Torque | 0-1270 | 1270 | 0.01Nm |
| 6077h | 03E3h | Torque Actual | RO | - | 0.1% |
| 6078h | 03E4h | Current Actual | RO | - | 0.1% |

### Profile Parameters

| Index | Modbus | Name | Default | Unit |
|-------|--------|------|---------|------|
| 607Eh | 03F3h | Polarity | 0 | - |
| 607Fh | 03F4h | Max Profile Velocity | 500000 | user unit/s |
| 6080h | 03F6h | Max Motor Speed | 4000 | rpm |
| 6081h | 03F8h | Profile Velocity | 500000 | user unit/s |
| 6082h | 03FAh | End Velocity | 0 | user unit/s |
| 6083h | 03FCh | Profile Acceleration | 409600 | user unit/s² |
| 6084h | 03FEh | Profile Deceleration | 409600 | user unit/s² |
| 6085h | 0400h | Quick Stop Deceleration | 500000 | user unit/s² |
| 6086h | 0402h | Motion Profile Type | 3 | - |
| 6087h | 0403h | Torque Slope | 10 | 0.1%/s |
| 6088h | 0405h | Torque Slope Type | 0 | - |

**Motion Profile Type (6086h):**
- 0: Linear (trapezoidal)
- 3: S-curve

**Torque Slope Type (6088h):**
- 0: Ramp
- 2: No ramp

### Unit Conversion Registers

| Index:Sub | Modbus | Name | Default |
|-----------|--------|------|---------|
| 608Fh:01h | 0406h | Encoder Increment | 10000 |
| 608Fh:02h | 0408h | Motor Revolutions | 1 |
| 6091h:01h | 040Eh | Gear Ratio Numerator | 1 |
| 6091h:02h | 0410h | Gear Ratio Denominator | 1 |

### Homing Mode Registers

| Index:Sub | Modbus | Name | Type | Default | Unit |
|-----------|--------|------|------|---------|------|
| 6098h | 0416h | Homing Method | int8 | 20 | - |
| 6099h:01h | 0417h | Homing High Speed | uint32 | 10000 | user unit/s |
| 6099h:02h | 0419h | Homing Low Speed | int32 | 2730 | user unit/s |
| 609Ah | 041Bh | Homing Acceleration | uint32 | 409600 | user unit/s² |

**Homing Method (6098h):** Range 17-45, see section 5.7.4 for details.

### Contour Acceleration Registers

| Index:Sub | Modbus | Name | Type | Default | Unit |
|-----------|--------|------|------|---------|------|
| 60A3h | 041Dh | Contour Accel Count | uint8 | 2 | - |
| 60A4h:01h | 041Eh | Contour Acceleration | uint32 | 50000 | user unit/s² |
| 60A4h:02h | 0420h | Contour Deceleration | uint32 | 50000 | user unit/s² |

### Cyclic Mode Bias Registers

| Index | Modbus | Name | Type | Default | Unit | PDO |
|-------|--------|------|------|---------|------|-----|
| 60B0h | 0426h | Position Bias | int32 | 0 | user unit | RPDO |
| 60B1h | 0428h | Speed Bias | int32 | 0 | user unit | RPDO |
| 60B2h | 042Ah | Torque Bias | int32 | 0 | user unit | RPDO |

**Bias Formulas:**
- CSP Mode: Target Position = 607Ah + 60B0h
- CSV Mode: Target Speed = 60FFh + 60B1h
- CST Mode: Target Torque = 6071h + 60B2h

### Interpolation Mode Registers

| Index:Sub | Modbus | Name | Type | Default | Unit |
|-----------|--------|------|------|---------|------|
| 60C1h:01h | 042Dh | IP Target Position | int32 | 0 | user unit |
| 60C2h:01h | 042Fh | IP Cycle Time Constant t | uint8 | 20 | s |
| 60C2h:02h | 0430h | IP Cycle Time Index n | int8 | -1 | - |

**Interpolation Period:** Period = t × 10^n seconds

### Maximum Profile Registers

| Index | Modbus | Name | Type | Default | Unit |
|-------|--------|------|------|---------|------|
| 60C5h | 043Bh | Max Profile Acceleration | uint32 | 500000 | user unit/s² |
| 60C6h | 043Dh | Max Contour Deceleration | uint32 | 500000 | user unit/s² |

### Positioning Options Register

| Index | Modbus | Name | Type | Default |
|-------|--------|------|------|---------|
| 60F2h | 043Fh | Positioning Options | uint16 | 0 |

**Positioning Options (60F2h):**

| Bit1 | Bit0 | Description |
|------|------|-------------|
| 0 | 0 | Relative shift, relative to target position (607Ah) |
| 0 | 1 | Relative shift, relative to position command (60FCh) |
| 1 | 0 | Relative shift, relative to actual position (6064h) |

### Read-Only Feedback Registers

| Index | Modbus | Name | Type | Unit | PDO |
|-------|--------|------|------|------|-----|
| 60F4h | 0440h | User Position Bias | int32 | user unit | TPDO |
| 60FAh | 0444h | Regulator Output | int32 | command unit | TPDO |
| 60FCh | 0446h | Motor Position Command | int32 | user unit | TPDO |

**Motor Position Command:** 60FCh = 6062h × Electronic Gear Ratio (6091h)

### Target Speed Register

| Index | Modbus | Name | Type | Default | Unit | PDO |
|-------|--------|------|------|---------|------|-----|
| 60FFh | 0448h | Target Speed | int32 | 0 | user unit/s | RPDO |

**Usage:** Set user speed command in Profile Velocity (PV) and Cyclic Synchronized Velocity (CSV) modes.

---

## 实际测试经验总结 (2026-01-10)

本章节记录通过实际硬件测试验证的重要发现，这些内容与官方手册可能存在差异。

### 1. 32位寄存器字节序

**关键发现**: NiMotion 驱动器使用**大端序** (Big Endian)，而非手册中描述的小端序。

| 地址 | 内容 |
|------|------|
| 基础地址 | 高字 (High Word) |
| 基础地址 + 1 | 低字 (Low Word) |

```python
# 正确的读取方式 (大端序)
values = read_holding_registers(slave, address, 2)
value = (values[0] << 16) | values[1]

# 正确的写入方式 (大端序)
high = (value >> 16) & 0xFFFF
low = value & 0xFFFF
write_multiple_registers(slave, address, [high, low])
```

**错误示例** (会导致读取值异常):
```python
# 错误的小端序读取
value = (values[1] << 16) | values[0]  # 会得到错误的值!
```

### 2. 运动模式单位说明

#### PP 模式 (Profile Position)

| 参数 | 寄存器 | 单位 | 说明 |
|------|--------|------|------|
| 目标位置 | 607Ah (0x03E7) | user units | 编码器脉冲 |
| 实际位置 | 6064h (0x03C8) | user units | 编码器脉冲 |
| 轮廓速度 | 6081h (0x03F8) | user units/s | **不是 RPM!** |
| 轮廓加速度 | 6083h (0x03FC) | user units/s² | |
| 轮廓减速度 | 6084h (0x03FE) | user units/s² | |

#### PV 模式 (Profile Velocity)

| 参数 | 寄存器 | 单位 | 说明 |
|------|--------|------|------|
| 目标速度 | 60FFh (0x0448) | user units/s | **不是 RPM!** |
| 实际速度 | 606Ch (0x03D5) | RPM | 实际速度用 RPM |
| 轮廓加速度 | 6083h (0x03FC) | user units/s² | |
| 轮廓减速度 | 6084h (0x03FE) | user units/s² | |

### 3. 单位换算公式

假设 encoder_resolution = 10000 (脉冲/圈):

```
# 速度换算
RPM = velocity_user_units × 60 / encoder_resolution
velocity_user_units = RPM × encoder_resolution / 60

# 示例
50000 user units/s = 50000 × 60 / 10000 = 300 RPM
300 RPM = 300 × 10000 / 60 = 50000 user units/s
```

### 4. CiA402 状态机验证结果

状态转换命令序列 (已验证):

```python
# 使能序列
SHUTDOWN = 0x0006       # → Ready to switch on
SWITCH_ON = 0x0007      # → Switched on
ENABLE_OPERATION = 0x000F  # → Operation enabled

# PP 模式触发运动
START_ABSOLUTE = 0x001F    # 绝对位置运动
START_RELATIVE = 0x005F    # 相对位置运动

# PV 模式 Halt 停止
HALT = 0x010F              # Enable + Halt bit
```

### 5. 测试通过的功能

| 测试 | 结果 | 备注 |
|------|------|------|
| PP 模式位置运动 | 7/7 通过 | 位置误差 ±4 脉冲 |
| PV 模式速度运动 | 8/8 通过 | 速度精度 < 1% |
| CiA402 状态机 | 通过 | 所有状态转换正确 |
| Halt 停止功能 | 通过 | 0.69 秒内停止 |
| 32位寄存器读写 | 通过 | 使用大端序 |

### 6. 常见错误及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 速度读取值异常大 (如 130000000) | 32位字节序错误 | 使用大端序读取 |
| 位置值为负数且很大 | 32位字节序错误 | 使用大端序读取 |
| 参数写入后读回不匹配 | 32位字节序错误 | 使用大端序写入 |
| 电机不运动但状态正确 | 硬件未上电或编码器未配置 | 检查主电源和编码器 |

### 7. 测试脚本位置

```
tests/integration/
├── test_l4_001_pp_mode.py   # PP 模式位置运动测试
└── test_l4_002_pv_mode.py   # PV 模式速度运动测试
```

运行测试:
```bash
python3 tests/integration/test_l4_001_pp_mode.py --auto
python3 tests/integration/test_l4_002_pv_mode.py --auto
```

### 8. DI (数字输入) 配置经验

#### 重要寄存器地址

| 功能 | 寄存器 | Modbus 地址 | 说明 |
|------|--------|-------------|------|
| DI 物理状态监控 | 200Bh:05h | **0x01E2** | 位0=DI1, 位1=DI2, 位2=DI3 |
| DO 物理状态监控 | 200Bh:06h | 0x01E3 | 位0=DO1 |
| DI1 功能 | 2003h:03h | 0x00D5 | |
| DI1 逻辑 | 2003h:04h | 0x00D6 | |
| DI2 功能 | 2003h:05h | 0x00D7 | |
| DI2 逻辑 | 2003h:06h | 0x00D8 | |
| DI3 功能 | 2003h:07h | 0x00D9 | |
| DI3 逻辑 | 2003h:08h | 0x00DA | |

**注意**: DI 监控寄存器是 0x01E2，不是 0x01E3！

#### DI 功能编号

| 功能编号 | 说明 |
|----------|------|
| 0 | 未定义 |
| 1 | 电机使能 (NiMotion 模式) |
| 2 | 报警复位 |
| 14 | **正限位开关** |
| 15 | **负限位开关** |
| 31 | **原点开关** |

#### DI 逻辑选项

| 值 | 说明 |
|----|------|
| 0 | 低电平有效 (常用于 NO 型限位开关) |
| 1 | 高电平有效 |
| 2 | 上升沿触发 |
| 3 | 下降沿触发 |

#### Z 轴限位开关配置 (2026-01-12 验证)

**注意**: 实际硬件接线与预期不同，已通过软件配置修正。

```python
# DI2 配置为负限位 (下限位) - 实际硬件接线
write_register(0x03, 0x00D7, 15)  # 功能 = 15 (负限位)
write_register(0x03, 0x00D8, 0)   # 逻辑 = 0 (低电平有效)

# DI3 配置为正限位 (上限位) - 实际硬件接线
write_register(0x03, 0x00D9, 14)  # 功能 = 14 (正限位)
write_register(0x03, 0x00DA, 0)   # 逻辑 = 0 (低电平有效)
```

#### 限位开关状态判断

限位开关为常开 (NO) 型:
- **触发时**: 开关闭合 → DI 低电平 → 对应位 = 0
- **未触发时**: 开关断开 → DI 高电平 → 对应位 = 1

```python
# 读取 DI 状态
di_state = read_register(0x03, 0x01E2)
di1 = bool(di_state & 0x0001)  # DI1 状态
di2 = bool(di_state & 0x0002)  # DI2 状态 (负限位)
di3 = bool(di_state & 0x0004)  # DI3 状态 (正限位)

# 判断限位状态 (低电平有效)
at_negative_limit = not di2  # DI2=0 表示在负限位
at_positive_limit = not di3  # DI3=0 表示在正限位
```

### 9. 测试脚本位置 (更新)

```
tests/integration/
├── test_l4_001_pp_mode.py          # PP 模式位置运动测试
├── test_l4_002_pv_mode.py          # PV 模式速度运动测试
├── test_l4_003_homing.py           # 回零操作测试
├── test_max_average_speed.py       # 最大平均速度测试
├── test_gui_comprehensive.py       # GUI 界面综合测试
├── diagnose_limit_switches.py      # 限位开关诊断
└── detect_limit_switch_wiring.py   # 限位开关接线检测
```

### 10. 回零 (Homing) 注意事项

#### CiA402 数字输入寄存器 (60FDh)

| 位 | 说明 |
|----|------|
| Bit 0 | 负限位开关 (1=触发) |
| Bit 1 | 正限位开关 (1=触发) |
| Bit 2 | 原点开关 (1=触发) |

**重要**: 60FDh 显示驱动器识别的逻辑状态，需要与物理 DI 状态 (0x01E2) 对照验证。

#### 回零方式

| 方式 | 说明 | 需要的开关 |
|------|------|-----------|
| 17 | 负限位回零 | 负限位开关 (DI 功能 15) |
| 18 | 正限位回零 | 正限位开关 (DI 功能 14) |
| 37 | 正方向堵转 | 无 |
| 38 | 负方向堵转 | 无 |

#### 回零失败排查

1. **检查 60FDh 状态**: 如果显示限位已触发，回零操作会立即失败
2. **验证 DI 逻辑**: 物理状态和逻辑配置需要匹配
3. **告警码 0x8610**: 回零超时，检查限位开关是否正确连接

### 11. Z 轴最大平均速度测试 (2026-01-12)

#### 测试条件

| 参数 | 值 |
|------|------|
| 测试行程 | 50mm (5mm ↔ 55mm) |
| 设定最大速度 | 500 mm/s |
| 实际有效行程 | 61mm (0mm ~ 61mm) |

#### 测试结果

| 加速度 | 正向平均速度 | 反向平均速度 | 状态 |
|--------|-------------|-------------|------|
| 500 mm/s² | ~62 mm/s | ~67 mm/s | 稳定 |
| 2000 mm/s² | 81.1 mm/s | 103.0 mm/s | 稳定 |
| **3000 mm/s²** | **110.6 mm/s** | **113.1 mm/s** | **最佳** |
| 4000 mm/s² | - | - | 故障 |

#### 结论

- Z轴在 50mm 行程下的**最大稳定平均速度约为 110-113 mm/s**
- 推荐使用**加速度 3000 mm/s²** 获得最佳性能
- 4000 mm/s² 超出电机稳定工作范围，会导致故障
- 正反向速度差异约 2.2%，非常均衡

#### 理论分析

- 50mm 行程不足以让电机加速到 500 mm/s 的最大速度
- 要达到 500 mm/s 需要至少 83.3mm 的行程:
  - 加速距离 = v²/(2a) = 500²/(2×3000) = 41.67mm
  - 减速距离 = 41.67mm
  - 总计 = 83.3mm
- 当前运动为三角速度曲线 (无匀速段)

#### 测试脚本

```bash
python3 tests/integration/test_max_average_speed.py
```

---

## Version Information

| Manual Version | Date | Revision History |
|----------------|------|------------------|
| A | 2025/8/13 | Initial release |

## Manufacturer Contact

**Beijing NiMotion Control Technology Co., Ltd.**
- Address: Building 3, Yard 12, Jinxing Road, Daxing District, Beijing
- Zip Code: 102628
- Tel: (010) 60213882
- Fax: (010) 60213882
- E-mail: nimotion@nimotion.com
- Website: http://www.nimotion.com

