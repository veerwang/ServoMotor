#!/usr/bin/env python3
"""
测试堵转回零 (方式 37/38)

在确认回零超时参数正确后，测试堵转回零
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
    ACTUAL_VELOCITY = 0x03D5

    # 回零参数
    HOMING_METHOD = 0x0416
    HOMING_SPEED_HIGH = 0x0417
    HOMING_SPEED_LOW = 0x0419
    HOMING_ACCEL = 0x041B
    HOME_OFFSET = 0x03ED
    HOMING_TIMEOUT = 0x012E  # 2005h:1Ch

    # 堵转参数
    BLOCKING_TORQUE = 0x0170  # 2007h:13h
    BLOCKING_TIME = 0x0172    # 2007h:15h

    # DI
    DIGITAL_INPUTS = 0x0447

    # 告警
    ERROR_CODE = 0x037F

    # 保存参数
    SAVE_PARAMS = 0x0026


def main():
    parser = argparse.ArgumentParser(description="测试堵转回零")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=3, help="从站地址")
    parser.add_argument("--method", type=int, default=38, help="回零方式 (37=正向, 38=负向)")
    parser.add_argument("--save", action="store_true", help="保存参数到 EEPROM")
    args = parser.parse_args()

    print("=" * 60)
    print(f"测试堵转回零 (方式 {args.method})")
    print("=" * 60)

    if args.method == 37:
        print("方式 37: 正方向堵转回零")
    elif args.method == 38:
        print("方式 38: 负方向堵转回零")

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
        else:
            print("  无故障")

        # 1. 设置回零参数
        print("\n" + "-" * 50)
        print("1. 设置回零参数")
        print("-" * 50)

        # 回零超时
        timeout = read_reg(Reg.HOMING_TIMEOUT)
        print(f"  当前回零超时: {timeout}ms")

        if timeout < 30000:
            write_reg(Reg.HOMING_TIMEOUT, 60000)  # 60秒
            timeout = read_reg(Reg.HOMING_TIMEOUT)
            print(f"  设置回零超时: {timeout}ms")

        # 回零方式
        write_reg(Reg.HOMING_METHOD, args.method)
        method = read_reg(Reg.HOMING_METHOD)
        print(f"  回零方式: {method}")

        # 回零速度 (慢速用于堵转检测)
        write_reg32(Reg.HOMING_SPEED_HIGH, 5000)   # 5mm/s
        write_reg32(Reg.HOMING_SPEED_LOW, 2000)    # 2mm/s
        write_reg32(Reg.HOMING_ACCEL, 20000)       # 20mm/s²
        write_reg32(Reg.HOME_OFFSET, 0)

        hs_high = read_reg32(Reg.HOMING_SPEED_HIGH)
        hs_low = read_reg32(Reg.HOMING_SPEED_LOW)
        accel = read_reg32(Reg.HOMING_ACCEL)

        print(f"  快速回零速度: {hs_high} (user units/s)")
        print(f"  慢速回零速度: {hs_low} (user units/s)")
        print(f"  回零加速度: {accel} (user units/s²)")

        # 堵转参数
        write_reg(Reg.BLOCKING_TORQUE, 200)  # 20% 扭矩
        write_reg(Reg.BLOCKING_TIME, 500)    # 500ms

        bt = read_reg(Reg.BLOCKING_TORQUE)
        btime = read_reg(Reg.BLOCKING_TIME)
        print(f"  堵转扭矩: {bt/10:.1f}%")
        print(f"  堵转时间: {btime}ms")

        # 2. 保存参数 (可选)
        if args.save:
            print("\n" + "-" * 50)
            print("2. 保存参数到 EEPROM")
            print("-" * 50)

            save_value = 0x65766173  # "save"
            high = (save_value >> 16) & 0xFFFF
            low = save_value & 0xFFFF
            client.write_multiple_registers(slave, Reg.SAVE_PARAMS, [high, low])
            print("  参数已保存")
            time.sleep(0.5)

        # 3. 切换到 HM 模式
        print("\n" + "-" * 50)
        print("3. 切换到 HM 模式并使能")
        print("-" * 50)

        # 禁用
        write_reg(Reg.CONTROL_WORD, 0x00)
        time.sleep(0.1)

        # 设置 HM 模式
        write_reg(Reg.OP_MODE, 6)
        time.sleep(0.1)

        mode = read_reg(Reg.OP_MODE_DISPLAY)
        print(f"  操作模式: {mode}")

        # 状态机使能
        write_reg(Reg.CONTROL_WORD, 0x06)
        time.sleep(0.05)
        write_reg(Reg.CONTROL_WORD, 0x07)
        time.sleep(0.05)
        write_reg(Reg.CONTROL_WORD, 0x0F)
        time.sleep(0.1)

        status = read_reg(Reg.STATUS_WORD)
        if not (status & 0x04):
            print(f"  使能失败! 状态: 0x{status:04X}")
            return

        print(f"  使能成功, 状态: 0x{status:04X}")

        # 4. 记录起始位置
        start_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        print(f"  起始位置: {start_pos} ({start_pos/1000:.2f}mm)")

        # 5. 启动回零
        print("\n" + "-" * 50)
        print("4. 启动堵转回零")
        print("-" * 50)
        print("  电机将向负方向移动直到堵转...")
        print("  可以用手阻挡电机来模拟堵转")
        print()

        write_reg(Reg.CONTROL_WORD, 0x1F)

        # 监控
        start_time = time.time()
        last_print = 0
        max_duration = 60  # 最长60秒

        while True:
            elapsed = time.time() - start_time

            status = read_reg(Reg.STATUS_WORD)
            pos = read_reg32_signed(Reg.ACTUAL_POSITION)
            vel = read_reg32_signed(Reg.ACTUAL_VELOCITY)
            di_logic = read_reg32(Reg.DIGITAL_INPUTS)

            moved_mm = (pos - start_pos) / 1000
            homing_attained = bool(status & 0x1000)
            homing_error = bool(status & 0x2000)
            fault = bool(status & 0x08)

            # 打印 (每0.5秒)
            if elapsed - last_print >= 0.5:
                print(f"  t={elapsed:5.1f}s | 移动:{moved_mm:+8.2f}mm | 速度:{vel:5d}rpm | "
                      f"状态:0x{status:04X}")
                last_print = elapsed

            # 检查完成
            if homing_attained:
                print(f"\n  >>> 堵转回零完成!")
                print(f"      总移动: {moved_mm:.2f}mm")
                break

            if homing_error or fault:
                error = read_reg32(Reg.ERROR_CODE)
                print(f"\n  >>> 回零失败! 错误码: 0x{error:08X}")
                break

            # 超时
            if elapsed > max_duration:
                print(f"\n  >>> 超时 ({max_duration}秒)")
                break

            time.sleep(0.1)

        # 6. 结果
        print("\n" + "-" * 50)
        print("5. 结果")
        print("-" * 50)

        final_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        status = read_reg(Reg.STATUS_WORD)

        print(f"  最终位置: {final_pos} ({final_pos/1000:.2f}mm)")
        print(f"  最终状态: 0x{status:04X}")

        # 禁用
        write_reg(Reg.CONTROL_WORD, 0x00)

        if status & 0x1000:
            print("\n" + "=" * 60)
            print("堵转回零成功!")
            print(f"原点位置: {final_pos}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("堵转回零失败")
            print("=" * 60)

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
