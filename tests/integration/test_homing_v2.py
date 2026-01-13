#!/usr/bin/env python3
"""
TC-L4-003: 回零操作测试 (V2)

在确认限位开关配置正确后，重新测试回零功能
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

    # 位置
    ACTUAL_POSITION = 0x03C8
    TARGET_POSITION = 0x03E7

    # 速度
    TARGET_VELOCITY = 0x0448
    ACTUAL_VELOCITY = 0x03D5

    # DI 监控
    DI_MONITOR = 0x01E2
    DIGITAL_INPUTS = 0x0447

    # 回零参数
    HOMING_METHOD = 0x0416
    HOMING_SPEED_HIGH = 0x0417
    HOMING_SPEED_LOW = 0x0419
    HOMING_ACCEL = 0x041B
    HOME_OFFSET = 0x03ED

    # 堵转参数
    BLOCKING_TORQUE = 0x0170
    BLOCKING_TIME = 0x0172

    # 轮廓参数
    PROFILE_VELOCITY = 0x03F8
    PROFILE_ACCEL = 0x03FC
    PROFILE_DECEL = 0x03FE

    # 告警
    ERROR_CODE = 0x0382
    ERROR_REGISTER = 0x0000


# 回零方式
HM_NEG_LIMIT = 17      # 负限位回零
HM_POS_LIMIT = 18      # 正限位回零
HM_CURRENT_POS = 35    # 当前位置设为原点
HM_BLOCK_POS = 37      # 正向堵转回零
HM_BLOCK_NEG = 38      # 负向堵转回零


def main():
    parser = argparse.ArgumentParser(description="TC-L4-003 回零操作测试 V2")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=3, help="从站地址")
    parser.add_argument("--method", type=int, default=38, help="回零方式 (17/18/35/37/38)")
    args = parser.parse_args()

    print("=" * 60)
    print("TC-L4-003: 回零操作测试 (V2)")
    print("=" * 60)
    print(f"回零方式: {args.method}")

    # 连接
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

    def get_state_name(status):
        """解析状态字"""
        if status & 0x08:  # Fault
            return "FAULT"
        if not (status & 0x40):  # Switch on disabled
            if status & 0x01:
                return "READY_TO_SWITCH_ON"
            return "SWITCH_ON_DISABLED"
        if (status & 0x27) == 0x27:
            return "OPERATION_ENABLED"
        if (status & 0x23) == 0x23:
            return "SWITCHED_ON"
        if (status & 0x21) == 0x21:
            return "READY_TO_SWITCH_ON"
        return f"UNKNOWN (0x{status:04X})"

    def clear_fault():
        """清除故障"""
        status = read_reg(Reg.STATUS_WORD)
        if status & 0x08:
            print("  检测到故障，尝试清除...")
            write_reg(Reg.CONTROL_WORD, 0x80)
            time.sleep(0.1)
            write_reg(Reg.CONTROL_WORD, 0x00)
            time.sleep(0.1)
            status = read_reg(Reg.STATUS_WORD)
            if status & 0x08:
                print(f"  故障未能清除! 状态: 0x{status:04X}")
                return False
            print("  故障已清除")
        return True

    def enable_motor():
        """使能电机"""
        # Shutdown -> Ready to switch on
        write_reg(Reg.CONTROL_WORD, 0x06)
        time.sleep(0.05)

        # Switch on
        write_reg(Reg.CONTROL_WORD, 0x07)
        time.sleep(0.05)

        # Enable operation
        write_reg(Reg.CONTROL_WORD, 0x0F)
        time.sleep(0.1)

        status = read_reg(Reg.STATUS_WORD)
        if status & 0x04:
            print(f"  使能成功, 状态: 0x{status:04X}")
            return True
        else:
            print(f"  使能失败, 状态: 0x{status:04X} ({get_state_name(status)})")
            return False

    def disable_motor():
        """禁用电机"""
        write_reg(Reg.CONTROL_WORD, 0x00)
        time.sleep(0.1)

    try:
        # 1. 检查初始状态
        print("\n" + "-" * 50)
        print("1. 检查初始状态")
        print("-" * 50)

        status = read_reg(Reg.STATUS_WORD)
        mode = read_reg(Reg.OP_MODE_DISPLAY)
        pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"  状态: 0x{status:04X} ({get_state_name(status)})")
        print(f"  当前模式: {mode}")
        print(f"  当前位置: {pos} ({pos/1000:.2f}mm)")
        print(f"  60FDh: 0x{di_logic:08X}")
        print(f"    负限位: {'触发' if di_logic & 0x01 else '未触发'}")
        print(f"    正限位: {'触发' if di_logic & 0x02 else '未触发'}")

        # 清除可能的故障
        if not clear_fault():
            return

        # 2. 设置 HM 模式
        print("\n" + "-" * 50)
        print("2. 设置 HM 模式")
        print("-" * 50)

        write_reg(Reg.OP_MODE, 6)  # HM mode
        time.sleep(0.1)

        mode = read_reg(Reg.OP_MODE_DISPLAY)
        print(f"  操作模式: {mode} (应为 6)")

        if mode != 6:
            print("  警告: 模式设置可能未生效")

        # 3. 配置回零参数
        print("\n" + "-" * 50)
        print("3. 配置回零参数")
        print("-" * 50)

        method = args.method
        write_reg(Reg.HOMING_METHOD, method)

        # 回零速度 (单位: user units/s, 1000 = 1mm/s)
        write_reg32(Reg.HOMING_SPEED_HIGH, 10000)  # 快速: 10mm/s
        write_reg32(Reg.HOMING_SPEED_LOW, 2000)    # 慢速: 2mm/s
        write_reg32(Reg.HOMING_ACCEL, 50000)       # 加速度: 50mm/s²

        # 堵转参数 (用于方式 37/38)
        if method in [37, 38]:
            write_reg(Reg.BLOCKING_TORQUE, 300)    # 30% 堵转扭矩
            write_reg(Reg.BLOCKING_TIME, 500)     # 500ms 堵转时间

        print(f"  回零方式: {method}")
        print(f"  快速速度: 10000 (10mm/s)")
        print(f"  慢速速度: 2000 (2mm/s)")
        print(f"  回零加速度: 50000 (50mm/s²)")
        if method in [37, 38]:
            print(f"  堵转扭矩: 30%")
            print(f"  堵转时间: 500ms")

        # 4. 使能并启动回零
        print("\n" + "-" * 50)
        print("4. 使能并启动回零")
        print("-" * 50)

        if not enable_motor():
            return

        start_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        print(f"  起始位置: {start_pos} ({start_pos/1000:.2f}mm)")

        # 启动回零: 设置控制字 bit4
        print("  启动回零...")
        write_reg(Reg.CONTROL_WORD, 0x1F)  # Enable + Start homing
        time.sleep(0.1)

        # 5. 监控回零过程
        print("\n" + "-" * 50)
        print("5. 监控回零过程")
        print("-" * 50)

        start_time = time.time()
        last_print = 0
        homing_started = False

        while True:
            elapsed = time.time() - start_time

            status = read_reg(Reg.STATUS_WORD)
            pos = read_reg32_signed(Reg.ACTUAL_POSITION)
            di_logic = read_reg32(Reg.DIGITAL_INPUTS)
            error = read_reg(Reg.ERROR_CODE)

            moved_mm = (pos - start_pos) / 1000
            neg_limit = (di_logic >> 0) & 1
            pos_limit = (di_logic >> 1) & 1

            # 状态位
            target_reached = bool(status & 0x400)
            homing_attained = bool(status & 0x1000)
            homing_error = bool(status & 0x2000)
            fault = bool(status & 0x08)

            # 打印状态
            if elapsed - last_print >= 0.5:
                print(f"  t={elapsed:5.1f}s | 位置:{pos:10d} | 移动:{moved_mm:+8.2f}mm | "
                      f"负限:{neg_limit} 正限:{pos_limit} | 状态:0x{status:04X}")
                last_print = elapsed

            # 检查完成
            if homing_attained:
                print(f"\n  >>> 回零完成! 已移动 {moved_mm:.2f}mm")
                break

            # 检查错误
            if homing_error or fault:
                print(f"\n  >>> 回零失败!")
                print(f"      状态: 0x{status:04X}")
                print(f"      错误码: 0x{error:04X}")

                if error == 0x8610:
                    print("      原因: 回零超时")
                elif error == 0x8611:
                    print("      原因: 跟踪误差")
                elif error == 0x8613:
                    print("      原因: 软件限位")
                elif error == 0x8614:
                    print("      原因: 限位开关错误")

                break

            # 超时
            if elapsed > 60:
                print("\n  >>> 测试超时 (60秒)")
                break

            time.sleep(0.1)

        # 6. 最终状态
        print("\n" + "-" * 50)
        print("6. 最终状态")
        print("-" * 50)

        final_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        status = read_reg(Reg.STATUS_WORD)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"  最终位置: {final_pos} ({final_pos/1000:.2f}mm)")
        print(f"  状态: 0x{status:04X}")
        print(f"  60FDh: 0x{di_logic:08X}")

        # 禁用
        disable_motor()

        # 7. 结论
        print("\n" + "=" * 60)
        if status & 0x1000:
            print("结果: 回零成功!")
        else:
            print("结果: 回零失败")
            print("""
建议:
  1. 如果使用限位回零 (方式17/18)，确保限位开关接线正确
  2. 如果使用堵转回零 (方式37/38)，尝试调整堵转扭矩和时间
  3. 可尝试方式 35 (当前位置设为原点) 作为临时方案
""")
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
