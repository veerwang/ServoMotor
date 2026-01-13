#!/usr/bin/env python3
"""
诊断限位开关问题

调查为什么负限位在命令速度时立即触发
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

    # DI 配置
    DI1_FUNCTION = 0x00D5
    DI1_LOGIC = 0x00D6
    DI2_FUNCTION = 0x00D7
    DI2_LOGIC = 0x00D8
    DI3_FUNCTION = 0x00D9
    DI3_LOGIC = 0x00DA

    # 监控
    DI_MONITOR = 0x01E2      # 物理 DI 状态
    DIGITAL_INPUTS = 0x0447  # 60FDh CiA402 逻辑状态

    # 软件限位
    SW_LIMIT_MIN = 0x03EF
    SW_LIMIT_MAX = 0x03F1

    # 轮廓参数
    PROFILE_VELOCITY = 0x03F8
    PROFILE_ACCEL = 0x03FC
    PROFILE_DECEL = 0x03FE

    # 告警
    ERROR_CODE = 0x0382


def main():
    parser = argparse.ArgumentParser(description="诊断限位开关问题")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    args = parser.parse_args()

    print("=" * 60)
    print("限位开关问题诊断")
    print("=" * 60)

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
        # 大端序: 高字在前
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
        # 1. 读取 DI 配置
        print("\n" + "-" * 50)
        print("1. DI 配置")
        print("-" * 50)

        func_names = {
            0: "无功能",
            14: "正限位",
            15: "负限位",
            31: "原点开关",
        }
        logic_names = {
            0: "低电平有效 (Active Low)",
            1: "高电平有效 (Active High)",
        }

        di_configs = [
            ("DI1", Reg.DI1_FUNCTION, Reg.DI1_LOGIC),
            ("DI2", Reg.DI2_FUNCTION, Reg.DI2_LOGIC),
            ("DI3", Reg.DI3_FUNCTION, Reg.DI3_LOGIC),
        ]

        for name, func_addr, logic_addr in di_configs:
            func = read_reg(func_addr)
            logic = read_reg(logic_addr)
            func_name = func_names.get(func, f"功能 {func}")
            logic_name = logic_names.get(logic, f"逻辑 {logic}")
            print(f"  {name}: 功能={func_name}, 逻辑={logic_name}")

        # 2. 读取物理和逻辑状态
        print("\n" + "-" * 50)
        print("2. DI 状态")
        print("-" * 50)

        di_phys = read_reg(Reg.DI_MONITOR)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"  物理 DI (0x01E2): 0x{di_phys:04X}")
        print(f"    DI1: {'HIGH' if di_phys & 0x01 else 'LOW'}")
        print(f"    DI2: {'HIGH' if di_phys & 0x02 else 'LOW'}")
        print(f"    DI3: {'HIGH' if di_phys & 0x04 else 'LOW'}")
        print()
        print(f"  逻辑状态 (60FDh): 0x{di_logic:08X}")
        print(f"    Bit 0 (负限位): {'触发' if di_logic & 0x01 else '未触发'}")
        print(f"    Bit 1 (正限位): {'触发' if di_logic & 0x02 else '未触发'}")
        print(f"    Bit 2 (原点):   {'触发' if di_logic & 0x04 else '未触发'}")

        # 3. 读取软件限位
        print("\n" + "-" * 50)
        print("3. 软件限位 (607Dh)")
        print("-" * 50)

        sw_min = read_reg32_signed(Reg.SW_LIMIT_MIN)
        sw_max = read_reg32_signed(Reg.SW_LIMIT_MAX)
        actual_pos = read_reg32_signed(Reg.ACTUAL_POSITION)

        print(f"  最小限位: {sw_min} ({sw_min/1000:.2f}mm)")
        print(f"  最大限位: {sw_max} ({sw_max/1000:.2f}mm)")
        print(f"  当前位置: {actual_pos} ({actual_pos/1000:.2f}mm)")

        if sw_min != 0 or sw_max != 0:
            if actual_pos <= sw_min:
                print("  >>> 警告: 当前位置 <= 最小软件限位!")
            if actual_pos >= sw_max:
                print("  >>> 警告: 当前位置 >= 最大软件限位!")

        # 4. 读取当前状态
        print("\n" + "-" * 50)
        print("4. 驱动器状态")
        print("-" * 50)

        status = read_reg(Reg.STATUS_WORD)
        mode = read_reg(Reg.OP_MODE_DISPLAY)
        error = read_reg(Reg.ERROR_CODE)

        print(f"  状态字: 0x{status:04X}")
        print(f"    Ready to switch on: {bool(status & 0x01)}")
        print(f"    Switched on:        {bool(status & 0x02)}")
        print(f"    Operation enabled:  {bool(status & 0x04)}")
        print(f"    Fault:              {bool(status & 0x08)}")
        print(f"    Quick stop:         {bool(status & 0x20)}")
        print(f"    Internal limit:     {bool(status & 0x800)}")
        print(f"  操作模式: {mode}")
        print(f"  错误码: 0x{error:04X}")

        # 5. 测试: 在禁用状态下监控 60FDh
        print("\n" + "-" * 50)
        print("5. 测试: 禁用状态下监控 60FDh")
        print("-" * 50)

        # 确保禁用
        write_reg(Reg.CONTROL_WORD, 0x00)
        time.sleep(0.1)

        print("  已禁用电机，连续读取 60FDh 3秒...")
        for i in range(6):
            di_logic = read_reg32(Reg.DIGITAL_INPUTS)
            di_phys = read_reg(Reg.DI_MONITOR)
            neg = (di_logic >> 0) & 1
            pos = (di_logic >> 1) & 1
            print(f"    t={i*0.5:.1f}s: 物理=0x{di_phys:04X}, 60FDh=0x{di_logic:08X}, 负限位={neg}, 正限位={pos}")
            time.sleep(0.5)

        # 6. 测试: PP 模式下向正方向移动 1mm
        print("\n" + "-" * 50)
        print("6. 测试: PP 模式向正方向移动 1mm")
        print("-" * 50)

        # 设置 PP 模式
        write_reg(Reg.OP_MODE, 1)
        time.sleep(0.1)

        # 设置速度和加速度
        write_reg32(Reg.PROFILE_VELOCITY, 5000)  # 5mm/s
        write_reg32(Reg.PROFILE_ACCEL, 50000)
        write_reg32(Reg.PROFILE_DECEL, 50000)

        # 使能
        write_reg(Reg.CONTROL_WORD, 0x06)
        time.sleep(0.05)
        write_reg(Reg.CONTROL_WORD, 0x07)
        time.sleep(0.05)
        write_reg(Reg.CONTROL_WORD, 0x0F)
        time.sleep(0.1)

        status = read_reg(Reg.STATUS_WORD)
        if not (status & 0x04):
            print(f"  使能失败! 状态: 0x{status:04X}")
        else:
            print("  使能成功")

            # 读取起始位置
            start_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
            target = start_pos + 1000  # +1mm

            print(f"  起始位置: {start_pos}")
            print(f"  目标位置: {target} (+1mm)")

            # 写入目标位置并启动
            write_reg32(Reg.TARGET_POSITION, target)
            time.sleep(0.05)
            write_reg(Reg.CONTROL_WORD, 0x1F)  # New setpoint

            # 监控移动过程
            print("  移动中，监控 60FDh...")
            for i in range(20):
                di_logic = read_reg32(Reg.DIGITAL_INPUTS)
                pos = read_reg32_signed(Reg.ACTUAL_POSITION)
                status = read_reg(Reg.STATUS_WORD)
                neg = (di_logic >> 0) & 1
                pos_lim = (di_logic >> 1) & 1
                moved = (pos - start_pos) / 1000
                print(f"    t={i*0.1:.1f}s: 位置={pos}, 移动={moved:+.2f}mm, 负限位={neg}, 正限位={pos_lim}, 状态=0x{status:04X}")

                # 检查是否完成
                if status & 0x400:  # Target reached
                    print("  >>> 目标到达!")
                    break

                if neg or pos_lim:
                    print(f"  >>> 限位触发! 负={neg}, 正={pos_lim}")

                time.sleep(0.1)

            # 清除 new setpoint
            write_reg(Reg.CONTROL_WORD, 0x0F)

        # 7. 测试: PP 模式向负方向移动 1mm
        print("\n" + "-" * 50)
        print("7. 测试: PP 模式向负方向移动 1mm")
        print("-" * 50)

        # 读取起始位置
        start_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        target = start_pos - 1000  # -1mm

        print(f"  起始位置: {start_pos}")
        print(f"  目标位置: {target} (-1mm)")

        # 写入目标位置并启动
        write_reg32(Reg.TARGET_POSITION, target)
        time.sleep(0.05)
        write_reg(Reg.CONTROL_WORD, 0x1F)  # New setpoint

        # 监控移动过程
        print("  移动中，监控 60FDh...")
        for i in range(20):
            di_logic = read_reg32(Reg.DIGITAL_INPUTS)
            pos = read_reg32_signed(Reg.ACTUAL_POSITION)
            status = read_reg(Reg.STATUS_WORD)
            neg = (di_logic >> 0) & 1
            pos_lim = (di_logic >> 1) & 1
            moved = (pos - start_pos) / 1000
            print(f"    t={i*0.1:.1f}s: 位置={pos}, 移动={moved:+.2f}mm, 负限位={neg}, 正限位={pos_lim}, 状态=0x{status:04X}")

            # 检查是否完成
            if status & 0x400:  # Target reached
                print("  >>> 目标到达!")
                break

            if neg or pos_lim:
                print(f"  >>> 限位触发! 负={neg}, 正={pos_lim}")

            time.sleep(0.1)

        # 清除 new setpoint
        write_reg(Reg.CONTROL_WORD, 0x0F)

        # 8. 禁用
        print("\n" + "-" * 50)
        print("8. 禁用电机")
        print("-" * 50)

        write_reg(Reg.CONTROL_WORD, 0x00)
        time.sleep(0.1)

        final_pos = read_reg32_signed(Reg.ACTUAL_POSITION)
        status = read_reg(Reg.STATUS_WORD)
        print(f"  最终位置: {final_pos} ({final_pos/1000:.2f}mm)")
        print(f"  状态: 0x{status:04X}")

        # 9. 结论
        print("\n" + "=" * 60)
        print("诊断总结")
        print("=" * 60)
        print("""
如果 PP 模式移动正常但限位不触发:
  - 限位开关可能未接线或接线错误
  - 需要物理检查限位开关

如果限位在某个方向立即触发:
  - 检查该方向的物理限位是否被压住
  - 检查 DI 配置是否正确

如果 60FDh 始终显示限位触发 (即使物理 DI 为 HIGH):
  - DI 逻辑配置可能需要重新设置
  - 驱动器可能需要断电重启使配置生效
""")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        serial.close()


if __name__ == "__main__":
    main()
