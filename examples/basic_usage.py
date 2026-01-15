#!/usr/bin/env python3
"""
基础使用示例

演示 servo_service 模块的基本用法。
"""

import logging
import sys
import time

# 添加项目路径
sys.path.insert(0, "..")

from servo_service import (
    AxisName,
    DriveState,
    HomingMethod,
    ServoService,
    get_axis_config,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def example_basic_connection():
    """基础连接示例"""
    print("\n=== 基础连接示例 ===\n")

    # 创建服务
    service = ServoService()

    # 列出可用串口
    ports = service.get_available_ports()
    print("可用串口:")
    for port in ports[:5]:  # 只显示前 5 个
        print(f"  - {port.display_name}")

    if not ports:
        print("未找到可用串口")
        return

    # 使用第一个串口连接 (实际使用时需要选择正确的串口)
    # service.connect(ports[0].device)
    # service.disconnect()

    print("\n连接示例完成")


def example_axis_config():
    """轴配置示例"""
    print("\n=== 轴配置示例 ===\n")

    for axis in AxisName:
        config = get_axis_config(axis)
        print(f"{axis.value} 轴配置:")
        print(f"  从站地址: {config.slave_id}")
        print(f"  电机型号: {config.model}")
        print(f"  电机功率: {config.motor_power}W")
        print(f"  丝杠导程: {config.ball_screw_lead}mm")
        print(f"  最大速度: {config.max_velocity}mm/s")
        print(f"  有效行程: {config.stroke_min} - {config.stroke_max}mm")
        print(f"  抱闸: {'有' if config.has_brake else '无'}")
        print()


def example_unit_conversion():
    """单位转换示例"""
    print("\n=== 单位转换示例 ===\n")

    config = get_axis_config(AxisName.Z3)

    # 位置转换
    position_mm = 25.0
    position_pulses = config.mm_to_pulses(position_mm)
    back_to_mm = config.pulses_to_mm(position_pulses)

    print(f"位置转换: {position_mm}mm -> {position_pulses} pulses -> {back_to_mm}mm")

    # 速度转换
    velocity_mm_s = 100.0
    velocity_pulses_s = config.velocity_mm_to_pulses(velocity_mm_s)
    back_to_mm_s = config.velocity_pulses_to_mm(velocity_pulses_s)

    print(f"速度转换: {velocity_mm_s}mm/s -> {velocity_pulses_s} pulses/s -> {back_to_mm_s}mm/s")

    # 每脉冲位移
    print(f"每脉冲位移: {config.mm_per_pulse * 1000:.4f}um")
    print(f"每毫米脉冲: {config.pulses_per_mm:.1f} pulses")


def example_simulated_motion():
    """模拟运动控制示例 (无需实际硬件)"""
    print("\n=== 模拟运动控制示例 ===\n")

    print("注意: 以下代码展示 API 用法，实际运行需要连接硬件")
    print()

    code_example = '''
    # 创建服务并连接
    service = ServoService(port="/dev/ttyUSB0")
    service.connect()

    # 选择 Z 轴
    service.current_axis = AxisName.Z3

    # 使能电机
    service.enable()

    # 获取状态
    status = service.get_axis_status()
    print(f"当前位置: {status.position_mm}mm")
    print(f"当前状态: {status.state.value}")

    # 回零
    service.home()

    # 移动到 50mm 位置
    service.move_to(50.0, velocity_mm_s=100.0)

    # 相对移动 10mm
    service.move_by(10.0)

    # 点动 (速度模式)
    service.jog(50.0)  # 50mm/s 正向
    time.sleep(1)
    service.stop()

    # 禁用电机
    service.disable()

    # 断开连接
    service.disconnect()
    '''

    print(code_example)


def example_context_manager():
    """上下文管理器示例"""
    print("\n=== 上下文管理器示例 ===\n")

    code_example = '''
    # 使用 with 语句自动管理连接
    with ServoService(port="/dev/ttyUSB0") as service:
        service.enable()
        service.move_to(50.0)
        # 退出时自动断开连接
    '''

    print("使用 with 语句可以自动管理连接:")
    print(code_example)


def example_multi_axis():
    """多轴控制示例"""
    print("\n=== 多轴控制示例 ===\n")

    code_example = '''
    service = ServoService(port="/dev/ttyUSB0")
    service.connect()

    # 使能所有轴
    service.enable_all()

    # 所有轴回零
    service.home_all()

    # 分别控制各轴
    service.move_to(100.0, axis=AxisName.X)
    service.move_to(50.0, axis=AxisName.Y2)
    service.move_to(25.0, axis=AxisName.Z3)

    # 获取所有轴状态
    all_status = service.get_all_axis_status()
    for axis, status in all_status.items():
        print(f"{axis.value}: {status.position_mm}mm")

    # 快速停止所有轴
    service.quick_stop_all()

    # 禁用所有轴
    service.disable_all()

    service.disconnect()
    '''

    print("多轴控制示例:")
    print(code_example)


def main():
    """主函数"""
    print("=" * 60)
    print("NiMotion 伺服电机控制系统 - 基础使用示例")
    print("=" * 60)

    example_basic_connection()
    example_axis_config()
    example_unit_conversion()
    example_simulated_motion()
    example_context_manager()
    example_multi_axis()

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
