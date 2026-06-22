#!/usr/bin/env python3
"""
限位开关状态只读诊断工具

只读取状态，不发送任何运动/使能指令。用于验证硬件限位开关接线是否正常。

读取内容:
  - DI 物理状态 (0x01E2): 位0=DI1, 位1=DI2, 位2=DI3
  - CiA402 数字输入逻辑 (60FDh / 0x0447): 位0=负限位, 位1=正限位, 位2=原点
  - 实际位置 (6064h / 0x03C8)
  - DI 功能/逻辑配置回读 (确认驱动器里配置是否正确)

用法:
  python3 tools/read_limit_status.py --axis Z4
  python3 tools/read_limit_status.py --slave 4 --port /dev/ttyUSB0
"""
import argparse
import sys

from servo_service.modbus_rtu.client import ModbusClient
from servo_service.motor_control.registers import Registers as R
from servo_service.high_level_api.axis_config import AxisName, get_axis_config

AXIS_SLAVE = {"Z4": 4, "Y2": 2, "Z3": 3, "X": 1}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--axis", default="Z4", choices=list(AXIS_SLAVE.keys()))
    ap.add_argument("--slave", type=int, default=None, help="覆盖从站地址")
    ap.add_argument("--port", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    slave = args.slave if args.slave is not None else AXIS_SLAVE[args.axis]
    cfg = get_axis_config(AxisName(args.axis))

    client = ModbusClient(timeout=0.2, retries=3)
    client.connect(port=args.port, baudrate=args.baud)
    try:
        di_phys = client.read_register(slave, R.DI_PHYSICAL_STATE.address)
        di_logic = client.read_register_32bit(slave, R.DIGITAL_INPUTS.address)
        pos = client.read_register_32bit(slave, R.POSITION_ACTUAL_VALUE.address, signed=True)
        status = client.read_register(slave, R.STATUS_WORD.address)
        di2_f = client.read_register(slave, R.DI2_FUNCTION.address)
        di2_l = client.read_register(slave, R.DI2_LOGIC.address)
        di3_f = client.read_register(slave, R.DI3_FUNCTION.address)
        di3_l = client.read_register(slave, R.DI3_LOGIC.address)
    finally:
        client.disconnect()

    # 物理 DI 位
    di1 = bool(di_phys & 0x01)
    di2 = bool(di_phys & 0x02)  # 负限位 (功能15)
    di3 = bool(di_phys & 0x04)  # 正限位 (功能14)

    # 低电平有效: DI=0(低电平) 表示触发
    neg_triggered = not di2  # 负限位/下限位
    pos_triggered = not di3  # 正限位/上限位

    # CiA402 逻辑限位状态 (60FDh)
    cia_neg = bool(di_logic & 0x01)  # 位0=负限位
    cia_pos = bool(di_logic & 0x02)  # 位1=正限位
    cia_home = bool(di_logic & 0x04)  # 位2=原点

    pos_mm = pos * cfg.mm_per_pulse

    print(f"\n========== {args.axis} 轴 (slave={slave}) 限位状态 ==========")
    print(f"实际位置        : {pos} pulses = {pos_mm:.3f} mm")
    print(f"状态字 6041h    : 0x{status:04X}")
    print(f"DI 物理状态 0x01E2: 0b{di_phys:03b}  (DI1={int(di1)} DI2={int(di2)} DI3={int(di3)})")
    print(f"CiA402 60FDh    : 0b{di_logic & 0x7:03b}  (负限位={int(cia_neg)} 正限位={int(cia_pos)} 原点={int(cia_home)})")
    print("-" * 50)
    print(f"DI2 配置回读    : 功能={di2_f} (期望15=负限位)  逻辑={di2_l} (期望0=低有效)")
    print(f"DI3 配置回读    : 功能={di3_f} (期望14=正限位)  逻辑={di3_l} (期望0=低有效)")
    print("-" * 50)
    print(f">> 负限位(下限位 DI2): {'★ 已触发 ★' if neg_triggered else '未触发'}")
    print(f">> 正限位(上限位 DI3): {'★ 已触发 ★' if pos_triggered else '未触发'}")
    print("=" * 50)

    # 一致性检查: 物理(低有效) 与 CiA402 逻辑应一致
    if neg_triggered != cia_neg or pos_triggered != cia_pos:
        print("⚠️  物理 DI 状态与 CiA402 逻辑状态不一致，可能极性/接线配置有误！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
