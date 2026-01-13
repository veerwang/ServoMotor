#!/usr/bin/env python3
"""
专门测试回零方式 35 (当前位置设为原点)

方式 35 不需要任何运动，应该立即完成
"""

import argparse
import sys
import time

sys.path.insert(0, ".")

from servo_service.modbus_rtu import ModbusClient
from servo_service.serial_comm import SerialPort


class Reg:
    """寄存器地址"""
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    OP_MODE = 0x03C2
    OP_MODE_DISPLAY = 0x03C3
    ACTUAL_POSITION = 0x03C8

    # 回零参数
    HOMING_METHOD = 0x0416
    HOMING_SPEED_HIGH = 0x0417
    HOMING_SPEED_LOW = 0x0419
    HOMING_ACCEL = 0x041B
    HOME_OFFSET = 0x03ED
    HOMING_TIMEOUT = 0x012E  # 2005h:1Ch

    # 告警
    ERROR_CODE = 0x037F


def main():
    parser = argparse.ArgumentParser(description="测试回零方式 35")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=3, help="从站地址")
    args = parser.parse_args()

    print("=" * 60)
    print("测试回零方式 35 (当前位置设为原点)")
    print("=" * 60)

    try:
        serial = SerialPort(port=args.port, baudrate=115200, timeout=0.5)
        serial.open()
        client = ModbusClient(serial_port=serial)
        print("连接成功")
    except Exception as e:
        print(f"连接失败: {e}")
        return

    slave = args.slave_id

    def read_reg(addr):
        return client.read_holding_registers(slave, addr, 1)[0]

    def read_reg32(addr):
        values = client.read_holding_registers(slave, addr, 2)
        return ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)

    def read_reg32_signed(addr):
        val = read_reg32(addr)
        if val >= 0x80000000:
            val -= 0x100000000
        return val

    def write_reg(addr, value):
        client.write_single_register(slave, addr, value & 0xFFFF)

    def write_reg32(addr, value):
        if value < 0:
            value += 0x100000000
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        client.write_multiple_registers(slave, addr, [high, low])

    try:
        # 0. 清除故障
        print("\n" + "-" * 50)
        print("0. 清除故障")
        print("-" * 50)

        status = read_reg(Reg.STATUS_WORD)
        if status & 0x08:
            print("  清除故障...")
            write_reg(Reg.CONTROL_WORD, 0x80)
            time.sleep(0.1)
            write_reg(Reg.CONTROL_WORD, 0x00)
            time.sleep(0.1)
            status = read_reg(Reg.STATUS_WORD)
            print(f"  状态: 0x{status:04X}")

        # 1. 检查回零超时参数
        print("\n" + "-" * 50)
        print("1. 检查回零参数")
        print("-" * 50)

        timeout = read_reg(Reg.HOMING_TIMEOUT)
        print(f"  回零超时 (2005h:1Ch): {timeout}ms")

        # 设置较长的超时
        write_reg(Reg.HOMING_TIMEOUT, 30000)  # 30秒
        timeout = read_reg(Reg.HOMING_TIMEOUT)
        print(f"  设置超时为: {timeout}ms")

        # 2. 设置回零方式 35
        print("\n" + "-" * 50)
        print("2. 设置回零方式 35")
        print("-" * 50)

        write_reg(Reg.HOMING_METHOD, 35)
        method = read_reg(Reg.HOMING_METHOD)
        print(f"  回零方式: {method}")

        # 也设置其他参数 (虽然方式35不需要)
        write_reg32(Reg.HOMING_SPEED_HIGH, 10000)
        write_reg32(Reg.HOMING_SPEED_LOW, 2000)
        write_reg32(Reg.HOMING_ACCEL, 50000)
        write_reg32(Reg.HOME_OFFSET, 0)

        # 3. 切换到 HM 模式
        print("\n" + "-" * 50)
        print("3. 切换到 HM 模式")
        print("-" * 50)

        # 先禁用
        write_reg(Reg.CONTROL_WORD, 0x00)
        time.sleep(0.1)

        # 设置 HM 模式
        write_reg(Reg.OP_MODE, 6)
        time.sleep(0.1)

        mode = read_reg(Reg.OP_MODE_DISPLAY)
        print(f"  操作模式: {mode} (应为 6)")

        # 4. CiA402 状态机: 逐步使能
        print("\n" + "-" * 50)
        print("4. 状态机转换")
        print("-" * 50)

        pos_before = read_reg32_signed(Reg.ACTUAL_POSITION)
        print(f"  起始位置: {pos_before} ({pos_before/1000:.2f}mm)")

        # Step 1: Shutdown
        print("  Step 1: Shutdown (0x06)")
        write_reg(Reg.CONTROL_WORD, 0x06)
        time.sleep(0.05)
        status = read_reg(Reg.STATUS_WORD)
        print(f"    状态: 0x{status:04X}")

        # Step 2: Switch on
        print("  Step 2: Switch on (0x07)")
        write_reg(Reg.CONTROL_WORD, 0x07)
        time.sleep(0.05)
        status = read_reg(Reg.STATUS_WORD)
        print(f"    状态: 0x{status:04X}")

        # Step 3: Enable operation
        print("  Step 3: Enable operation (0x0F)")
        write_reg(Reg.CONTROL_WORD, 0x0F)
        time.sleep(0.1)
        status = read_reg(Reg.STATUS_WORD)
        print(f"    状态: 0x{status:04X}")

        if not (status & 0x04):
            print("  >>> 使能失败!")
            error = read_reg32(Reg.ERROR_CODE)
            print(f"  错误码: 0x{error:08X}")
            return

        # 5. 启动回零 (bit4 从 0 变为 1)
        print("\n" + "-" * 50)
        print("5. 启动回零")
        print("-" * 50)

        print("  发送 0x1F (bit4=1, 启动回零)")
        write_reg(Reg.CONTROL_WORD, 0x1F)
        time.sleep(0.1)

        # 监控状态
        for i in range(20):
            status = read_reg(Reg.STATUS_WORD)
            pos = read_reg32_signed(Reg.ACTUAL_POSITION)
            error = read_reg32(Reg.ERROR_CODE)

            homing_attained = bool(status & 0x1000)
            homing_error = bool(status & 0x2000)
            target_reached = bool(status & 0x400)
            fault = bool(status & 0x08)

            print(f"  t={i*0.1:.1f}s | 状态:0x{status:04X} | 位置:{pos} | "
                  f"完成:{homing_attained} 错误:{homing_error} 故障:{fault}")

            if homing_attained:
                print("\n  >>> 回零成功!")
                break

            if homing_error or fault:
                print(f"\n  >>> 回零失败! 错误码: 0x{error:08X}")
                break

            time.sleep(0.1)

        # 6. 结果
        print("\n" + "-" * 50)
        print("6. 结果")
        print("-" * 50)

        pos_after = read_reg32_signed(Reg.ACTUAL_POSITION)
        status = read_reg(Reg.STATUS_WORD)

        print(f"  最终位置: {pos_after} ({pos_after/1000:.2f}mm)")
        print(f"  最终状态: 0x{status:04X}")

        if status & 0x1000:
            print("\n>>> 回零方式 35 成功!")
            print(f"    原点已设置在位置 {pos_after}")
        else:
            print("\n>>> 回零方式 35 失败")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            write_reg(Reg.CONTROL_WORD, 0x00)
        except:
            pass
        serial.close()


if __name__ == "__main__":
    main()
