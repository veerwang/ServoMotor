#!/usr/bin/env python3
"""
修复限位开关极性配置

根据用户反馈: "LED light is on when NOT triggered"
- 未触发时: LED 亮 → DI = HIGH
- 触发时: LED 灭 → DI = LOW

因此需要设置 DI 逻辑为 Active Low (logic=0):
- 当 DI = LOW 时，限位被触发
- 当 DI = HIGH 时，限位未触发
"""

import argparse
import logging
import sys
import time

sys.path.insert(0, ".")

from servo_service.modbus_rtu import ModbusClient
from servo_service.serial_comm import SerialPort

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class Reg:
    """寄存器地址"""
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

    # 控制
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381

    # 保存参数
    SAVE_PARAMS = 0x0026


# DI 功能定义
DI_FUNC_NONE = 0
DI_FUNC_POSITIVE_LIMIT = 14
DI_FUNC_NEGATIVE_LIMIT = 15
DI_FUNC_HOME_SWITCH = 31

# DI 逻辑定义
DI_LOGIC_ACTIVE_LOW = 0   # 低电平有效 (信号 LOW 时功能激活)
DI_LOGIC_ACTIVE_HIGH = 1  # 高电平有效 (信号 HIGH 时功能激活)


def main():
    parser = argparse.ArgumentParser(description="修复限位开关极性")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    args = parser.parse_args()

    print("=" * 60)
    print("限位开关极性修复脚本")
    print("=" * 60)
    print()
    print("问题分析:")
    print("  用户反馈: LED 在未触发时亮起")
    print("  → 未触发: LED ON → DI = HIGH")
    print("  → 触发:   LED OFF → DI = LOW")
    print()
    print("正确配置:")
    print("  DI Logic = 0 (Active Low)")
    print("  → 当 DI = LOW 时，限位被触发")
    print("  → 当 DI = HIGH 时，限位未触发")
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
        return ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)

    def write_reg(addr, value):
        client.write_single_register(slave, addr, value & 0xFFFF)

    try:
        # 1. 读取当前配置
        print("\n" + "-" * 50)
        print("当前 DI 配置")
        print("-" * 50)

        di_configs = [
            ("DI1", Reg.DI1_FUNCTION, Reg.DI1_LOGIC),
            ("DI2", Reg.DI2_FUNCTION, Reg.DI2_LOGIC),
            ("DI3", Reg.DI3_FUNCTION, Reg.DI3_LOGIC),
        ]

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

        for name, func_addr, logic_addr in di_configs:
            func = read_reg(func_addr)
            logic = read_reg(logic_addr)
            func_name = func_names.get(func, f"功能 {func}")
            logic_name = logic_names.get(logic, f"逻辑 {logic}")
            print(f"  {name}: 功能={func_name}, 逻辑={logic_name}")

        # 2. 读取物理和逻辑状态
        di_phys = read_reg(Reg.DI_MONITOR)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"\n当前状态:")
        print(f"  物理 DI (0x01E2): 0x{di_phys:04X}")
        print(f"    DI1: {'HIGH' if di_phys & 0x01 else 'LOW'}")
        print(f"    DI2: {'HIGH' if di_phys & 0x02 else 'LOW'}")
        print(f"    DI3: {'HIGH' if di_phys & 0x04 else 'LOW'}")
        print(f"  逻辑状态 (60FDh): 0x{di_logic:08X}")
        print(f"    负限位 (Bit0): {'触发' if di_logic & 0x01 else '未触发'}")
        print(f"    正限位 (Bit1): {'触发' if di_logic & 0x02 else '未触发'}")

        # 3. 分析问题
        print("\n" + "-" * 50)
        print("分析")
        print("-" * 50)

        # 如果物理 HIGH 但逻辑显示触发，说明极性配置错误
        needs_fix = False

        if (di_phys & 0x02) and (di_logic & 0x01):  # DI2 HIGH but neg limit triggered
            print("  DI2 物理 HIGH 但负限位显示触发 → 极性错误!")
            needs_fix = True
        if (di_phys & 0x04) and (di_logic & 0x02):  # DI3 HIGH but pos limit triggered
            print("  DI3 物理 HIGH 但正限位显示触发 → 极性错误!")
            needs_fix = True

        if not needs_fix and (di_logic & 0x03):
            print("  60FDh 显示限位触发，可能需要检查逻辑配置")
            needs_fix = True

        # 4. 修复配置
        print("\n" + "-" * 50)
        print("修复配置")
        print("-" * 50)

        # 设置正确的配置:
        # DI2 = 正限位 (14), Active Low
        # DI3 = 负限位 (15), Active Low
        print("设置 DI2 = 正限位 (功能 14), Active Low (逻辑 0)")
        write_reg(Reg.DI2_FUNCTION, DI_FUNC_POSITIVE_LIMIT)
        write_reg(Reg.DI2_LOGIC, DI_LOGIC_ACTIVE_LOW)

        print("设置 DI3 = 负限位 (功能 15), Active Low (逻辑 0)")
        write_reg(Reg.DI3_FUNCTION, DI_FUNC_NEGATIVE_LIMIT)
        write_reg(Reg.DI3_LOGIC, DI_LOGIC_ACTIVE_LOW)

        time.sleep(0.1)

        # 5. 验证写入
        print("\n验证写入...")
        for name, func_addr, logic_addr in di_configs:
            func = read_reg(func_addr)
            logic = read_reg(logic_addr)
            func_name = func_names.get(func, f"功能 {func}")
            logic_name = logic_names.get(logic, f"逻辑 {logic}")
            print(f"  {name}: 功能={func_name}, 逻辑={logic_name}")

        # 6. 重新检查状态
        print("\n重新检查状态...")
        time.sleep(0.2)
        di_phys = read_reg(Reg.DI_MONITOR)
        di_logic = read_reg32(Reg.DIGITAL_INPUTS)

        print(f"  物理 DI: 0x{di_phys:04X}")
        print(f"  逻辑 60FDh: 0x{di_logic:08X}")
        print(f"    负限位: {'触发' if di_logic & 0x01 else '未触发'}")
        print(f"    正限位: {'触发' if di_logic & 0x02 else '未触发'}")

        if di_logic & 0x03:
            print("\n" + "!" * 50)
            print("60FDh 仍显示限位触发!")
            print("可能的原因:")
            print("  1. 配置更改需要保存并重启才能生效")
            print("  2. 驱动器内部状态已锁存")
            print("!" * 50)

        # 7. 保存参数
        print("\n" + "-" * 50)
        print("保存参数到 EEPROM")
        print("-" * 50)

        # 写入 "save" (0x65766173) 到保存寄存器
        save_value = 0x65766173  # "save" in ASCII
        high = (save_value >> 16) & 0xFFFF
        low = save_value & 0xFFFF
        client.write_multiple_registers(slave, Reg.SAVE_PARAMS, [high, low])
        print("参数已保存")

        time.sleep(0.5)

        # 8. 最终建议
        print("\n" + "=" * 60)
        print("完成!")
        print("=" * 60)
        print()
        print("已执行的更改:")
        print("  - DI2: 正限位 (14), Active Low (0)")
        print("  - DI3: 负限位 (15), Active Low (0)")
        print("  - 参数已保存到 EEPROM")
        print()
        print("重要: 请断电重启驱动器使配置完全生效!")
        print()
        print("重启后，如果工作台不在限位位置:")
        print("  - 60FDh 应该显示 0x0000 (无限位触发)")
        print("  - 电机应该可以正常移动")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        serial.close()


if __name__ == "__main__":
    main()
