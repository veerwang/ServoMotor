#!/usr/bin/env python3
"""
读取告警历史和详细状态
"""

import argparse
import sys

sys.path.insert(0, ".")

from servo_service.modbus_rtu import ModbusClient
from servo_service.serial_comm import SerialPort


class Reg:
    """寄存器地址"""
    # 告警相关
    ERROR_REGISTER = 0x0000    # 1001h
    ALARM_COUNT = 0x0001       # 1003h:00
    ALARM_1 = 0x0002           # 1003h:01 (最新)
    ALARM_2 = 0x0004           # 1003h:02
    ALARM_3 = 0x0006           # 1003h:03
    ALARM_4 = 0x0008           # 1003h:04

    # 控制状态
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    ERROR_CODE = 0x037F        # 603Fh

    # DI
    DI_MONITOR = 0x01E2
    DIGITAL_INPUTS = 0x0447

    # 回零
    HOMING_METHOD = 0x0416
    HOMING_SPEED_HIGH = 0x0417
    HOMING_SPEED_LOW = 0x0419
    HOMING_ACCEL = 0x041B

    # 位置
    ACTUAL_POSITION = 0x03C8

    # 操作模式
    OP_MODE = 0x03C2
    OP_MODE_DISPLAY = 0x03C3


# 常见告警码
ALARM_CODES = {
    0x2300: "电机过流",
    0x2311: "电机过载 (警告)",
    0x2312: "电机堵转",
    0x3210: "电源过压",
    0x3220: "电源欠压",
    0x4210: "过温",
    0x4220: "低温",
    0x6320: "参数设置错误",
    0x7301: "编码器电池低电压",
    0x7302: "编码器电池警告",
    0x7310: "超速",
    0x7501: "通信看门狗超时",
    0x8610: "回零超时",
    0x8611: "跟随误差",
    0x8613: "软件限位错误",
    0x8614: "限位开关错误",
}


def main():
    parser = argparse.ArgumentParser(description="读取告警历史")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=3, help="从站地址")
    args = parser.parse_args()

    print("=" * 60)
    print("告警历史和状态诊断")
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

    try:
        # 1. 错误寄存器
        print("\n" + "-" * 50)
        print("1. 错误寄存器")
        print("-" * 50)

        error_reg = read_reg(Reg.ERROR_REGISTER)
        error_code = read_reg32(Reg.ERROR_CODE)

        print(f"  错误寄存器 (1001h): 0x{error_reg:04X}")
        print(f"  错误码 (603Fh): 0x{error_code:08X}")

        if error_code in ALARM_CODES:
            print(f"    含义: {ALARM_CODES[error_code]}")

        # 2. 告警历史
        print("\n" + "-" * 50)
        print("2. 告警历史 (1003h)")
        print("-" * 50)

        alarm_count = read_reg(Reg.ALARM_COUNT)
        print(f"  告警数量: {alarm_count}")

        if alarm_count > 0:
            for i in range(min(alarm_count, 4)):
                alarm_addr = Reg.ALARM_1 + i * 2
                alarm = read_reg32(alarm_addr)
                alarm_name = ALARM_CODES.get(alarm & 0xFFFF, f"未知 (0x{alarm & 0xFFFF:04X})")
                print(f"  告警 {i+1}: 0x{alarm:08X} - {alarm_name}")
        else:
            print("  (无告警记录)")

        # 3. 当前状态
        print("\n" + "-" * 50)
        print("3. 当前状态")
        print("-" * 50)

        status = read_reg(Reg.STATUS_WORD)
        ctrl = read_reg(Reg.CONTROL_WORD)
        mode = read_reg(Reg.OP_MODE_DISPLAY)
        pos = read_reg32_signed(Reg.ACTUAL_POSITION)

        print(f"  控制字: 0x{ctrl:04X}")
        print(f"  状态字: 0x{status:04X}")
        print(f"    Bit 0 (Ready to switch on): {bool(status & 0x01)}")
        print(f"    Bit 1 (Switched on):        {bool(status & 0x02)}")
        print(f"    Bit 2 (Operation enabled):  {bool(status & 0x04)}")
        print(f"    Bit 3 (Fault):              {bool(status & 0x08)}")
        print(f"    Bit 4 (Voltage enabled):    {bool(status & 0x10)}")
        print(f"    Bit 5 (Quick stop):         {bool(status & 0x20)}")
        print(f"    Bit 6 (Switch on disabled): {bool(status & 0x40)}")
        print(f"    Bit 7 (Warning):            {bool(status & 0x80)}")
        print(f"    Bit 9 (Remote):             {bool(status & 0x200)}")
        print(f"    Bit 10 (Target reached):    {bool(status & 0x400)}")
        print(f"    Bit 11 (Internal limit):    {bool(status & 0x800)}")
        print(f"    Bit 12 (HM: op mode spec):  {bool(status & 0x1000)}")
        print(f"    Bit 13 (HM: homing error):  {bool(status & 0x2000)}")
        print(f"  操作模式: {mode}")
        print(f"  当前位置: {pos} ({pos/1000:.2f}mm)")

        # 4. DI 状态
        print("\n" + "-" * 50)
        print("4. DI 状态")
        print("-" * 50)

        di_phys = read_reg(Reg.DI_MONITOR)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"  物理 DI (0x01E2): 0x{di_phys:04X}")
        print(f"  逻辑 60FDh: 0x{di_logic:08X}")
        print(f"    Bit 0 (负限位): {(di_logic >> 0) & 1}")
        print(f"    Bit 1 (正限位): {(di_logic >> 1) & 1}")
        print(f"    Bit 2 (原点):   {(di_logic >> 2) & 1}")

        # 5. 回零参数
        print("\n" + "-" * 50)
        print("5. 回零参数")
        print("-" * 50)

        hm_method = read_reg(Reg.HOMING_METHOD)
        hm_speed_high = read_reg32(Reg.HOMING_SPEED_HIGH)
        hm_speed_low = read_reg32(Reg.HOMING_SPEED_LOW)
        hm_accel = read_reg32(Reg.HOMING_ACCEL)

        print(f"  回零方式 (6098h): {hm_method}")
        print(f"  快速速度 (6099h:01): {hm_speed_high}")
        print(f"  慢速速度 (6099h:02): {hm_speed_low}")
        print(f"  回零加速度 (609Ah): {hm_accel}")

        # 6. 尝试清除故障
        print("\n" + "-" * 50)
        print("6. 尝试清除故障")
        print("-" * 50)

        if status & 0x08:
            print("  检测到故障，尝试清除...")
            import time
            client.write_single_register(slave, Reg.CONTROL_WORD, 0x80)
            time.sleep(0.1)
            client.write_single_register(slave, Reg.CONTROL_WORD, 0x00)
            time.sleep(0.1)

            status = read_reg(Reg.STATUS_WORD)
            error_code = read_reg32(Reg.ERROR_CODE)

            print(f"  清除后状态: 0x{status:04X}")
            print(f"  清除后错误码: 0x{error_code:08X}")

            if status & 0x08:
                print("  >>> 故障未能清除!")
            else:
                print("  >>> 故障已清除")
        else:
            print("  当前无故障")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        serial.close()


if __name__ == "__main__":
    main()
