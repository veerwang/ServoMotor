#!/usr/bin/env python3
"""
电机参数初始化测试脚本

测试 ServoService.initialize_motor_parameters() 功能
验证参数是否正确写入驱动器

用法:
    python3 test_motor_initialization.py [--axis X|Y|Z] [--verify-only]
"""

import argparse
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, "/home/hds/codes/ServoMotorCreate/CreateServoMotor")

from servo_service import ServoService, AxisName
from servo_service.motor_control.registers import Registers


# 测试配置
PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

# DI 功能名称映射
DI_FUNCTION_NAMES = {
    0: "未定义",
    1: "电机使能",
    2: "报警复位",
    14: "正限位开关",
    15: "负限位开关",
    31: "原点开关",
}


def get_di_function_name(func: int) -> str:
    """获取 DI 功能名称"""
    return DI_FUNCTION_NAMES.get(func, f"功能{func}")


def read_current_parameters(service: ServoService, axis: AxisName) -> dict:
    """读取当前电机参数"""
    config = service.get_axis_config(axis)
    modbus = service.get_modbus_client()
    slave_id = config.slave_id

    params = {}

    # 读取回零超时
    params["homing_timeout"] = modbus.read_register(
        slave_id, Registers.HOMING_TIMEOUT.address
    )

    # 读取堵转参数
    params["blocking_torque"] = modbus.read_register(
        slave_id, Registers.BLOCKING_TORQUE.address
    )
    params["blocking_time"] = modbus.read_register(
        slave_id, Registers.BLOCKING_TIME.address
    )

    # 读取 DI 配置
    params["di1_function"] = modbus.read_register(
        slave_id, Registers.DI1_FUNCTION.address
    )
    params["di1_logic"] = modbus.read_register(slave_id, Registers.DI1_LOGIC.address)
    params["di2_function"] = modbus.read_register(
        slave_id, Registers.DI2_FUNCTION.address
    )
    params["di2_logic"] = modbus.read_register(slave_id, Registers.DI2_LOGIC.address)
    params["di3_function"] = modbus.read_register(
        slave_id, Registers.DI3_FUNCTION.address
    )
    params["di3_logic"] = modbus.read_register(slave_id, Registers.DI3_LOGIC.address)

    # 读取 DI 物理状态
    params["di_state"] = modbus.read_register(
        slave_id, Registers.DI_PHYSICAL_STATE.address
    )

    return params


def print_parameters(params: dict, title: str = "当前参数"):
    """打印参数"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print("=" * 50)

    print(f"\n回零超时: {params['homing_timeout']}ms")

    print(f"\n堵转回零参数:")
    print(f"  扭矩阈值: {params['blocking_torque']} ({params['blocking_torque']/10}%)")
    print(f"  检测时间: {params['blocking_time']}ms")

    print(f"\nDI 配置:")
    print(
        f"  DI1: {get_di_function_name(params['di1_function'])} "
        f"(功能={params['di1_function']}, 逻辑={params['di1_logic']})"
    )
    print(
        f"  DI2: {get_di_function_name(params['di2_function'])} "
        f"(功能={params['di2_function']}, 逻辑={params['di2_logic']})"
    )
    print(
        f"  DI3: {get_di_function_name(params['di3_function'])} "
        f"(功能={params['di3_function']}, 逻辑={params['di3_logic']})"
    )

    di_state = params["di_state"]
    print(f"\nDI 物理状态: 0x{di_state:04X}")
    print(f"  DI1: {'高' if di_state & 0x01 else '低'}")
    print(f"  DI2: {'高' if di_state & 0x02 else '低'}")
    print(f"  DI3: {'高' if di_state & 0x04 else '低'}")


def verify_parameters(service: ServoService, axis: AxisName) -> bool:
    """验证参数是否与配置匹配"""
    config = service.get_axis_config(axis)
    params = read_current_parameters(service, axis)

    print(f"\n{'='*50}")
    print(f" 验证 {axis.value} 轴参数")
    print("=" * 50)

    all_pass = True

    # 验证回零超时
    expected = config.homing_timeout
    actual = params["homing_timeout"]
    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"\n回零超时: {status}")
    print(f"  期望: {expected}ms, 实际: {actual}ms")

    # 验证堵转参数
    expected = config.blocking_torque
    actual = params["blocking_torque"]
    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"\n堵转扭矩阈值: {status}")
    print(f"  期望: {expected} ({expected/10}%), 实际: {actual} ({actual/10}%)")

    expected = config.blocking_time
    actual = params["blocking_time"]
    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"\n堵转检测时间: {status}")
    print(f"  期望: {expected}ms, 实际: {actual}ms")

    # 验证 DI 配置
    di_configs = [
        ("DI1", config.di1_function, config.di1_logic, "di1_function", "di1_logic"),
        ("DI2", config.di2_function, config.di2_logic, "di2_function", "di2_logic"),
        ("DI3", config.di3_function, config.di3_logic, "di3_function", "di3_logic"),
    ]

    for di_name, exp_func, exp_logic, func_key, logic_key in di_configs:
        if exp_func is not None:
            actual_func = params[func_key]
            actual_logic = params[logic_key]
            func_pass = actual_func == exp_func
            logic_pass = actual_logic == exp_logic
            status = "PASS" if (func_pass and logic_pass) else "FAIL"
            if status == "FAIL":
                all_pass = False
            print(f"\n{di_name}: {status}")
            print(
                f"  功能: 期望={exp_func} ({get_di_function_name(exp_func)}), "
                f"实际={actual_func} ({get_di_function_name(actual_func)})"
            )
            print(f"  逻辑: 期望={exp_logic}, 实际={actual_logic}")

    return all_pass


def test_initialization(axis: AxisName, verify_only: bool = False):
    """测试电机参数初始化"""
    print("=" * 60)
    print(f" 电机参数初始化测试 - {axis.value} 轴")
    print("=" * 60)

    service = ServoService(port=PORT, baudrate=BAUDRATE)
    service.current_axis = axis

    try:
        service.connect()
        print(f"\n已连接到 {PORT}")

        # 读取初始化前的参数
        print("\n" + "-" * 40)
        print(" 初始化前")
        print("-" * 40)
        params_before = read_current_parameters(service, axis)
        print_parameters(params_before, "初始化前参数")

        if not verify_only:
            # 执行初始化
            print("\n" + "-" * 40)
            print(" 执行初始化")
            print("-" * 40)
            service.initialize_motor_parameters(axis)

            time.sleep(0.2)  # 等待写入完成

            # 读取初始化后的参数
            print("\n" + "-" * 40)
            print(" 初始化后")
            print("-" * 40)
            params_after = read_current_parameters(service, axis)
            print_parameters(params_after, "初始化后参数")

        # 验证参数
        print("\n" + "-" * 40)
        print(" 参数验证")
        print("-" * 40)
        all_pass = verify_parameters(service, axis)

        print("\n" + "=" * 60)
        if all_pass:
            print(" 测试结果: PASS")
        else:
            print(" 测试结果: FAIL - 部分参数不匹配")
        print("=" * 60)

        return all_pass

    except Exception as e:
        print(f"\n错误: {e}")
        return False

    finally:
        service.disconnect()
        print("\n已断开连接")


def main():
    parser = argparse.ArgumentParser(description="电机参数初始化测试")
    parser.add_argument(
        "--axis",
        type=str,
        choices=["X", "Y", "Z"],
        default="Z",
        help="要测试的轴 (默认: Z)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证参数，不执行初始化",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="测试所有轴",
    )

    args = parser.parse_args()

    if args.all:
        # 测试所有轴
        results = {}
        for axis in [AxisName.Z]:  # 目前只有 Z 轴配置了 DI
            results[axis.value] = test_initialization(axis, args.verify_only)
            print("\n")

        print("\n" + "=" * 60)
        print(" 测试总结")
        print("=" * 60)
        for axis_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {axis_name} 轴: {status}")
    else:
        # 测试指定轴
        axis = AxisName[args.axis]
        success = test_initialization(axis, args.verify_only)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
