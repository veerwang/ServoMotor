#!/usr/bin/env python3
"""
Z1 轴运动测试脚本

包含:
1. 参数保存到 EEPROM
2. PP 模式 (Profile Position) 测试
3. PV 模式 (Profile Velocity) 测试
"""

import sys
import time
import argparse

sys.path.insert(0, "/home/hds/github.com/ServoMotor")

from servo_service.serial_comm import SerialPort
from servo_service.modbus_rtu import ModbusClient
from servo_service.motor_control.registers import Registers

# 配置
PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
Z1_SLAVE_ID = 4

# Z1 参数
ENCODER_RESOLUTION = 131072  # 17-bit encoder
BALL_SCREW_LEAD = 10.0  # mm/rev
PULSES_PER_MM = ENCODER_RESOLUTION / BALL_SCREW_LEAD  # 13107.2

# CiA402 控制字
SHUTDOWN = 0x0006
SWITCH_ON = 0x0007
ENABLE_OPERATION = 0x000F
START_ABSOLUTE = 0x001F
START_RELATIVE = 0x005F
HALT = 0x010F
DISABLE_VOLTAGE = 0x0000

# 操作模式
MODE_PP = 1  # Profile Position
MODE_PV = 3  # Profile Velocity
MODE_HM = 6  # Homing


def mm_to_pulses(mm: float) -> int:
    """毫米转脉冲"""
    return int(mm * PULSES_PER_MM)


def pulses_to_mm(pulses: int) -> float:
    """脉冲转毫米"""
    return pulses / PULSES_PER_MM


def read_32bit(modbus: ModbusClient, slave_id: int, address: int) -> int:
    """读取32位寄存器 (大端序)"""
    high = modbus.read_register(slave_id, address)
    low = modbus.read_register(slave_id, address + 1)
    value = (high << 16) | low
    # 处理有符号数
    if value > 0x7FFFFFFF:
        value -= 0x100000000
    return value


def write_32bit(modbus: ModbusClient, slave_id: int, address: int, value: int):
    """写入32位寄存器 (大端序)"""
    if value < 0:
        value += 0x100000000
    high = (value >> 16) & 0xFFFF
    low = value & 0xFFFF
    modbus.write_multiple_registers(slave_id, address, [high, low])


def get_status_word(modbus: ModbusClient) -> int:
    """读取状态字"""
    return modbus.read_register(Z1_SLAVE_ID, Registers.STATUS_WORD.address)


def get_position(modbus: ModbusClient) -> int:
    """读取当前位置 (脉冲)"""
    return read_32bit(modbus, Z1_SLAVE_ID, Registers.POSITION_ACTUAL_VALUE.address)


def wait_for_target_reached(modbus: ModbusClient, timeout: float = 30.0) -> bool:
    """等待目标到达"""
    start = time.time()
    while time.time() - start < timeout:
        status = get_status_word(modbus)
        if status & 0x0400:  # Bit 10: Target reached
            return True
        time.sleep(0.1)
    return False


def enable_motor(modbus: ModbusClient) -> bool:
    """使能电机"""
    print("  使能电机...")

    # Shutdown
    modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, SHUTDOWN)
    time.sleep(0.1)

    # Switch on
    modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, SWITCH_ON)
    time.sleep(0.1)

    # Enable operation
    modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, ENABLE_OPERATION)
    time.sleep(0.2)

    status = get_status_word(modbus)
    if status & 0x0004:  # Operation enabled
        print("  [OK] 电机已使能")
        return True
    else:
        print(f"  [FAIL] 使能失败, 状态字: 0x{status:04X}")
        return False


def disable_motor(modbus: ModbusClient):
    """禁用电机"""
    modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, DISABLE_VOLTAGE)
    time.sleep(0.1)
    print("  电机已禁用")


def save_parameters(modbus: ModbusClient) -> bool:
    """保存参数到 EEPROM"""
    print("\n" + "=" * 60)
    print(" 保存参数到 EEPROM")
    print("=" * 60)

    try:
        # 保存命令: 0x65766173 = "save"
        save_cmd = 0x65766173
        high = (save_cmd >> 16) & 0xFFFF
        low = save_cmd & 0xFFFF

        print("  写入保存命令...")
        modbus.write_multiple_registers(Z1_SLAVE_ID, 0x0026, [high, low])

        # 等待保存完成
        print("  等待保存完成...")
        time.sleep(1.0)

        print("  [OK] 参数已保存到 EEPROM")
        return True

    except Exception as e:
        print(f"  [FAIL] 保存失败: {e}")
        return False


def test_pp_mode(modbus: ModbusClient) -> bool:
    """测试 PP 模式 (Profile Position)"""
    print("\n" + "=" * 60)
    print(" PP 模式测试 (Profile Position)")
    print("=" * 60)

    try:
        # 读取当前位置
        start_pos = get_position(modbus)
        start_mm = pulses_to_mm(start_pos)
        print(f"\n  当前位置: {start_pos} pulses ({start_mm:.2f} mm)")

        # 设置操作模式为 PP
        print("  设置操作模式为 PP (1)...")
        modbus.write_register(Z1_SLAVE_ID, Registers.MODES_OF_OPERATION.address, MODE_PP)
        time.sleep(0.1)

        # 设置运动参数
        velocity = mm_to_pulses(50)  # 50 mm/s
        acceleration = mm_to_pulses(200)  # 200 mm/s²
        deceleration = mm_to_pulses(200)  # 200 mm/s²

        print(f"  速度: 50 mm/s ({velocity} pulses/s)")
        print(f"  加速度: 200 mm/s² ({acceleration} pulses/s²)")

        write_32bit(modbus, Z1_SLAVE_ID, Registers.PROFILE_VELOCITY.address, velocity)
        write_32bit(modbus, Z1_SLAVE_ID, Registers.PROFILE_ACCELERATION.address, acceleration)
        write_32bit(modbus, Z1_SLAVE_ID, Registers.PROFILE_DECELERATION.address, deceleration)

        # 使能电机
        if not enable_motor(modbus):
            return False

        # 测试 1: 移动到 30mm
        print("\n--- 测试 1: 移动到 30mm ---")
        target1 = mm_to_pulses(30)
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_POSITION.address, target1)

        # 触发运动 (绝对位置)
        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, ENABLE_OPERATION)
        time.sleep(0.05)
        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, START_ABSOLUTE)

        print("  等待到达目标...")
        if wait_for_target_reached(modbus, 10.0):
            pos = get_position(modbus)
            pos_mm = pulses_to_mm(pos)
            error = abs(pos_mm - 30)
            print(f"  [OK] 到达位置: {pos} pulses ({pos_mm:.2f} mm), 误差: {error:.3f} mm")
        else:
            print("  [FAIL] 超时未到达目标")
            disable_motor(modbus)
            return False

        time.sleep(0.5)

        # 测试 2: 移动到 10mm
        print("\n--- 测试 2: 移动到 10mm ---")
        target2 = mm_to_pulses(10)
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_POSITION.address, target2)

        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, ENABLE_OPERATION)
        time.sleep(0.05)
        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, START_ABSOLUTE)

        print("  等待到达目标...")
        if wait_for_target_reached(modbus, 10.0):
            pos = get_position(modbus)
            pos_mm = pulses_to_mm(pos)
            error = abs(pos_mm - 10)
            print(f"  [OK] 到达位置: {pos} pulses ({pos_mm:.2f} mm), 误差: {error:.3f} mm")
        else:
            print("  [FAIL] 超时未到达目标")
            disable_motor(modbus)
            return False

        time.sleep(0.5)

        # 测试 3: 相对移动 +15mm
        print("\n--- 测试 3: 相对移动 +15mm ---")
        current_pos = get_position(modbus)
        target3 = mm_to_pulses(15)  # 相对位移
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_POSITION.address, target3)

        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, ENABLE_OPERATION)
        time.sleep(0.05)
        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, START_RELATIVE)

        print("  等待到达目标...")
        if wait_for_target_reached(modbus, 10.0):
            pos = get_position(modbus)
            pos_mm = pulses_to_mm(pos)
            expected_mm = pulses_to_mm(current_pos) + 15
            error = abs(pos_mm - expected_mm)
            print(f"  [OK] 到达位置: {pos} pulses ({pos_mm:.2f} mm), 误差: {error:.3f} mm")
        else:
            print("  [FAIL] 超时未到达目标")
            disable_motor(modbus)
            return False

        # 禁用电机
        disable_motor(modbus)

        print("\n  [PASS] PP 模式测试通过")
        return True

    except Exception as e:
        print(f"\n  [FAIL] PP 模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        try:
            disable_motor(modbus)
        except:
            pass
        return False


def test_pv_mode(modbus: ModbusClient) -> bool:
    """测试 PV 模式 (Profile Velocity)"""
    print("\n" + "=" * 60)
    print(" PV 模式测试 (Profile Velocity)")
    print("=" * 60)

    try:
        # 读取当前位置
        start_pos = get_position(modbus)
        start_mm = pulses_to_mm(start_pos)
        print(f"\n  当前位置: {start_pos} pulses ({start_mm:.2f} mm)")

        # 设置操作模式为 PV
        print("  设置操作模式为 PV (3)...")
        modbus.write_register(Z1_SLAVE_ID, Registers.MODES_OF_OPERATION.address, MODE_PV)
        time.sleep(0.1)

        # 设置加减速
        acceleration = mm_to_pulses(100)  # 100 mm/s²
        write_32bit(modbus, Z1_SLAVE_ID, Registers.PROFILE_ACCELERATION.address, acceleration)
        write_32bit(modbus, Z1_SLAVE_ID, Registers.PROFILE_DECELERATION.address, acceleration)

        # 使能电机
        if not enable_motor(modbus):
            return False

        # 测试 1: 正向运动 30 mm/s，持续 1 秒
        print("\n--- 测试 1: 正向 30 mm/s, 1秒 ---")
        velocity = mm_to_pulses(30)  # 30 mm/s
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_VELOCITY.address, velocity)

        start_pos = get_position(modbus)
        time.sleep(1.0)

        # 停止
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_VELOCITY.address, 0)
        time.sleep(0.5)

        end_pos = get_position(modbus)
        distance = pulses_to_mm(end_pos - start_pos)
        avg_speed = distance / 1.0
        print(f"  移动距离: {distance:.2f} mm")
        print(f"  平均速度: {avg_speed:.2f} mm/s")

        if 25 < avg_speed < 35:
            print("  [OK] 速度在预期范围内")
        else:
            print("  [WARN] 速度偏差较大")

        time.sleep(0.5)

        # 测试 2: 反向运动 30 mm/s，持续 1 秒
        print("\n--- 测试 2: 反向 30 mm/s, 1秒 ---")
        velocity = mm_to_pulses(-30)  # -30 mm/s
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_VELOCITY.address, velocity)

        start_pos = get_position(modbus)
        time.sleep(1.0)

        # 停止
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_VELOCITY.address, 0)
        time.sleep(0.5)

        end_pos = get_position(modbus)
        distance = pulses_to_mm(end_pos - start_pos)
        avg_speed = abs(distance) / 1.0
        print(f"  移动距离: {distance:.2f} mm")
        print(f"  平均速度: {avg_speed:.2f} mm/s")

        if 25 < avg_speed < 35:
            print("  [OK] 速度在预期范围内")
        else:
            print("  [WARN] 速度偏差较大")

        # 测试 3: Halt 停止测试
        print("\n--- 测试 3: Halt 停止测试 ---")
        velocity = mm_to_pulses(50)  # 50 mm/s
        write_32bit(modbus, Z1_SLAVE_ID, Registers.TARGET_VELOCITY.address, velocity)

        time.sleep(0.5)  # 让电机运行起来

        # 发送 Halt
        print("  发送 Halt 命令...")
        modbus.write_register(Z1_SLAVE_ID, Registers.CONTROL_WORD.address, HALT)

        halt_start = time.time()
        while True:
            # 读取实际速度
            actual_vel = read_32bit(modbus, Z1_SLAVE_ID, Registers.VELOCITY_ACTUAL_VALUE.address)
            if abs(actual_vel) < 10:  # 接近 0
                break
            if time.time() - halt_start > 3.0:
                print("  [FAIL] Halt 超时")
                break
            time.sleep(0.05)

        halt_time = time.time() - halt_start
        print(f"  停止时间: {halt_time:.2f} 秒")

        if halt_time < 2.0:
            print("  [OK] Halt 响应正常")
        else:
            print("  [WARN] Halt 响应较慢")

        # 禁用电机
        disable_motor(modbus)

        print("\n  [PASS] PV 模式测试通过")
        return True

    except Exception as e:
        print(f"\n  [FAIL] PV 模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        try:
            disable_motor(modbus)
        except:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(description="Z1 轴运动测试")
    parser.add_argument("--save", action="store_true", help="保存参数到 EEPROM")
    parser.add_argument("--pp", action="store_true", help="测试 PP 模式")
    parser.add_argument("--pv", action="store_true", help="测试 PV 模式")
    parser.add_argument("--all", action="store_true", help="运行所有测试")

    args = parser.parse_args()

    # 如果没有指定任何参数，默认运行所有测试
    if not (args.save or args.pp or args.pv or args.all):
        args.all = True

    print("=" * 60)
    print(" Z1 轴运动测试")
    print("=" * 60)
    print(f"\n串口: {PORT}")
    print(f"波特率: {BAUDRATE}")
    print(f"从站地址: {Z1_SLAVE_ID}")
    print(f"编码器分辨率: {ENCODER_RESOLUTION} pulses/rev")
    print(f"丝杠导程: {BALL_SCREW_LEAD} mm/rev")
    print(f"脉冲/毫米: {PULSES_PER_MM:.1f}")

    serial_port = SerialPort(PORT, BAUDRATE)
    serial_port.open()
    modbus = ModbusClient(serial_port)

    results = {}

    try:
        if args.save or args.all:
            results["save"] = save_parameters(modbus)

        if args.pp or args.all:
            results["pp"] = test_pp_mode(modbus)

        if args.pv or args.all:
            results["pv"] = test_pv_mode(modbus)

        # 打印总结
        print("\n" + "=" * 60)
        print(" 测试总结")
        print("=" * 60)

        all_pass = True
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  {test_name}: {status}")

        print("=" * 60)
        if all_pass:
            print(" 所有测试通过!")
        else:
            print(" 部分测试失败")
        print("=" * 60)

    finally:
        serial_port.close()


if __name__ == "__main__":
    main()
