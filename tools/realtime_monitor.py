#!/usr/bin/env python3
"""
实时电机状态监控脚本

用于综合测试时后台监控电机状态，发现异常时报警。
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servo_service.modbus_rtu.client import ModbusClient
from servo_service.serial_comm.serial_port import SerialPort

# 寄存器地址
REG_CONTROL_WORD = 0x0380
REG_STATUS_WORD = 0x0381
REG_ERROR_CODE = 0x0382
REG_OPERATION_MODE = 0x03C3
REG_POSITION = 0x03C8
REG_VELOCITY = 0x03D5

# Z轴从站地址
SLAVE_ID = 0x03

# 状态字位定义
STATUS_READY_TO_SWITCH_ON = 0x0001
STATUS_SWITCHED_ON = 0x0002
STATUS_OPERATION_ENABLED = 0x0004
STATUS_FAULT = 0x0008
STATUS_VOLTAGE_ENABLED = 0x0010
STATUS_QUICK_STOP = 0x0020
STATUS_SWITCH_ON_DISABLED = 0x0040
STATUS_WARNING = 0x0080
STATUS_TARGET_REACHED = 0x0400
STATUS_INTERNAL_LIMIT = 0x0800

# 控制字位定义
CTRL_HALT = 0x0100

def decode_status_word(sw):
    """解析状态字"""
    states = []
    if sw & STATUS_FAULT:
        states.append("FAULT!")
    if sw & STATUS_WARNING:
        states.append("WARNING")
    if sw & STATUS_OPERATION_ENABLED:
        states.append("Enabled")
    elif sw & STATUS_SWITCHED_ON:
        states.append("SwitchedOn")
    elif sw & STATUS_READY_TO_SWITCH_ON:
        states.append("Ready")
    elif sw & STATUS_SWITCH_ON_DISABLED:
        states.append("Disabled")
    if sw & STATUS_TARGET_REACHED:
        states.append("TargetReached")
    if sw & STATUS_INTERNAL_LIMIT:
        states.append("LIMIT!")
    if sw & STATUS_QUICK_STOP:
        states.append("QuickStop")
    return ", ".join(states) if states else "Unknown"

def decode_control_word(cw):
    """解析控制字"""
    flags = []
    if cw & CTRL_HALT:
        flags.append("HALT")
    if cw & 0x0010:
        flags.append("NewSetpoint")
    if cw & 0x0040:
        flags.append("Relative")
    if cw & 0x000F == 0x000F:
        flags.append("EnableOp")
    elif cw & 0x0007 == 0x0007:
        flags.append("SwitchOn")
    elif cw & 0x0006 == 0x0006:
        flags.append("Shutdown")
    return ", ".join(flags) if flags else f"0x{cw:04X}"

def decode_operation_mode(mode):
    """解析操作模式"""
    modes = {
        0: "No mode",
        1: "PP (位置)",
        2: "VM (速度)",
        3: "PV (轮廓速度)",
        4: "PT (转矩)",
        6: "HM (回零)",
        7: "IP (插补)",
        8: "CSP",
        9: "CSV",
        10: "CST",
    }
    return modes.get(mode, f"Unknown({mode})")

def read_32bit(client, slave, addr):
    """读取32位寄存器（大端序）"""
    values = client.read_holding_registers(slave, addr, 2)
    return (values[0] << 16) | values[1]

def read_32bit_signed(client, slave, addr):
    """读取32位有符号寄存器"""
    value = read_32bit(client, slave, addr)
    if value >= 0x80000000:
        value -= 0x100000000
    return value

def main():
    port = "/dev/ttyUSB0"
    baudrate = 115200

    print("=" * 70)
    print("电机实时状态监控")
    print("=" * 70)
    print(f"端口: {port}, 波特率: {baudrate}, 从站: {SLAVE_ID}")
    print("按 Ctrl+C 停止监控")
    print("=" * 70)

    serial_port = SerialPort(port=port, baudrate=baudrate)
    serial_port.open()
    client = ModbusClient(serial_port)

    last_status = None
    last_control = None
    last_error = None
    last_mode = None
    error_count = 0

    try:
        while True:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                # 读取状态
                status_word = client.read_register(SLAVE_ID, REG_STATUS_WORD)
                control_word = client.read_register(SLAVE_ID, REG_CONTROL_WORD)
                error_code = client.read_register(SLAVE_ID, REG_ERROR_CODE)
                op_mode = client.read_register(SLAVE_ID, REG_OPERATION_MODE)
                position = read_32bit_signed(client, SLAVE_ID, REG_POSITION)
                velocity = read_32bit_signed(client, SLAVE_ID, REG_VELOCITY)

                # 转换位置和速度到 mm
                position_mm = position / 1000.0
                velocity_mm_s = velocity / 1000.0 * 60  # 转换为 mm/s

                # 检测变化和异常
                alerts = []

                # 检测故障
                if status_word & STATUS_FAULT:
                    alerts.append(f"⚠️  FAULT 检测到! 错误码: 0x{error_code:04X}")

                # 检测警告
                if status_word & STATUS_WARNING:
                    alerts.append(f"⚠️  WARNING 警告!")

                # 检测限位
                if status_word & STATUS_INTERNAL_LIMIT:
                    alerts.append(f"⚠️  LIMIT 内部限位触发!")

                # 检测 Halt 状态
                if control_word & CTRL_HALT:
                    if last_control is not None and not (last_control & CTRL_HALT):
                        alerts.append(f"ℹ️  HALT 位已设置 (电机停止)")

                # 检测状态变化
                status_changed = (last_status != status_word)
                control_changed = (last_control != control_word)
                mode_changed = (last_mode != op_mode)

                # 输出状态
                if status_changed or control_changed or mode_changed or alerts or abs(velocity) > 100:
                    status_str = decode_status_word(status_word)
                    control_str = decode_control_word(control_word)
                    mode_str = decode_operation_mode(op_mode)

                    print(f"\n[{timestamp}]")
                    print(f"  状态: 0x{status_word:04X} ({status_str})")
                    print(f"  控制: 0x{control_word:04X} ({control_str})")
                    print(f"  模式: {mode_str}")
                    print(f"  位置: {position_mm:.3f} mm ({position} pulses)")
                    print(f"  速度: {velocity_mm_s:.1f} mm/s ({velocity} pulses/s)")

                    if error_code != 0:
                        print(f"  错误: 0x{error_code:04X}")

                    for alert in alerts:
                        print(f"  {alert}")

                # 更新上一次状态
                last_status = status_word
                last_control = control_word
                last_error = error_code
                last_mode = op_mode
                error_count = 0

            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    print(f"\n[{timestamp}] ❌ 通信错误: {e}")
                elif error_count == 4:
                    print(f"\n[{timestamp}] ❌ 连续通信错误，暂停报警...")

            time.sleep(0.2)  # 200ms 轮询间隔

    except KeyboardInterrupt:
        print("\n\n监控已停止")
    finally:
        serial_port.close()

if __name__ == "__main__":
    main()
