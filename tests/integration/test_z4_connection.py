#!/usr/bin/env python3
"""
Z4 轴电机连接和初始化测试

测试内容:
1. 串口连接
2. Modbus 通信
3. 电机状态读取
4. 参数初始化
"""

import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, "/home/hds/github.com/ServoMotor")

from servo_service import ServoService, AxisName
from servo_service.motor_control.registers import Registers
from servo_service.serial_comm.port_scanner import PortScanner


# 测试配置
BAUDRATE = 115200
Z4_SLAVE_ID = 4


def find_serial_port():
    """查找可用串口"""
    print("正在扫描串口...")
    scanner = PortScanner()
    ports = scanner.scan_ports()

    if not ports:
        print("未找到可用串口!")
        return None

    print(f"找到 {len(ports)} 个串口:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")

    # 优先选择 USB 串口
    for port in ports:
        if "USB" in port.device or "ttyUSB" in port.device:
            return port.device

    return ports[0].device


def test_connection(port: str) -> bool:
    """测试 Z4 电机连接"""
    print("\n" + "=" * 60)
    print(" Z4 轴电机连接测试")
    print("=" * 60)
    print(f"\n串口: {port}")
    print(f"波特率: {BAUDRATE}")
    print(f"从站地址: {Z4_SLAVE_ID}")

    try:
        # 直接使用 Modbus 客户端测试
        from servo_service.modbus_rtu import ModbusClient
        from servo_service.serial_comm import SerialPort

        serial_port = SerialPort(port, BAUDRATE)
        serial_port.open()
        print("\n[PASS] 串口连接成功")

        modbus = ModbusClient(serial_port)

        # 测试 1: 读取状态字
        print("\n--- 测试 1: 读取状态字 (6041h) ---")
        try:
            status_word = modbus.read_register(Z4_SLAVE_ID, Registers.STATUS_WORD.address)
            print(f"[PASS] 状态字: 0x{status_word:04X}")

            # 解析状态
            states = []
            if status_word & 0x0001:
                states.append("Ready to switch on")
            if status_word & 0x0002:
                states.append("Switched on")
            if status_word & 0x0004:
                states.append("Operation enabled")
            if status_word & 0x0008:
                states.append("Fault")
            if status_word & 0x0010:
                states.append("Voltage enabled")
            if status_word & 0x0040:
                states.append("Switch on disabled")
            if status_word & 0x0400:
                states.append("Target reached")
            print(f"       状态: {', '.join(states) if states else 'Unknown'}")
        except Exception as e:
            print(f"[FAIL] 读取状态字失败: {e}")
            return False

        # 测试 2: 读取实际位置
        print("\n--- 测试 2: 读取实际位置 (6064h) ---")
        try:
            pos_high = modbus.read_register(Z4_SLAVE_ID, Registers.POSITION_ACTUAL_VALUE.address)
            pos_low = modbus.read_register(Z4_SLAVE_ID, Registers.POSITION_ACTUAL_VALUE.address + 1)
            position = (pos_high << 16) | pos_low
            # 处理负数
            if position > 0x7FFFFFFF:
                position -= 0x100000000
            print(f"[PASS] 实际位置: {position} pulses ({position / 1000:.3f} mm)")
        except Exception as e:
            print(f"[FAIL] 读取位置失败: {e}")
            return False

        # 测试 3: 读取编码器分辨率
        print("\n--- 测试 3: 读取编码器分辨率 (608Fh) ---")
        try:
            enc_num_h = modbus.read_register(Z4_SLAVE_ID, Registers.ENCODER_RESOLUTION_NUM.address)
            enc_num_l = modbus.read_register(Z4_SLAVE_ID, Registers.ENCODER_RESOLUTION_NUM.address + 1)
            enc_num = (enc_num_h << 16) | enc_num_l

            enc_den_h = modbus.read_register(Z4_SLAVE_ID, Registers.ENCODER_RESOLUTION_DEN.address)
            enc_den_l = modbus.read_register(Z4_SLAVE_ID, Registers.ENCODER_RESOLUTION_DEN.address + 1)
            enc_den = (enc_den_h << 16) | enc_den_l

            print(f"[PASS] 编码器分辨率: {enc_num}/{enc_den} (pulses/rev)")
        except Exception as e:
            print(f"[FAIL] 读取编码器分辨率失败: {e}")
            return False

        # 测试 4: 读取输入电压
        print("\n--- 测试 4: 读取输入电压 (200Bh:15h) ---")
        try:
            voltage = modbus.read_register(Z4_SLAVE_ID, 0x01F7)  # 输入电压
            print(f"[PASS] 输入电压: {voltage / 10:.1f} V")
        except Exception as e:
            print(f"[WARN] 读取电压失败: {e}")

        # 测试 5: 读取 DI 状态
        print("\n--- 测试 5: 读取 DI 状态 (200Bh:05h) ---")
        try:
            di_state = modbus.read_register(Z4_SLAVE_ID, Registers.DI_PHYSICAL_STATE.address)
            print(f"[PASS] DI 状态: 0x{di_state:04X}")
            print(f"       DI1: {'高' if di_state & 0x01 else '低'}")
            print(f"       DI2: {'高' if di_state & 0x02 else '低'}")
            print(f"       DI3: {'高' if di_state & 0x04 else '低'}")
        except Exception as e:
            print(f"[WARN] 读取 DI 状态失败: {e}")

        # 测试 6: 读取电机驱动状态
        print("\n--- 测试 6: 读取驱动状态 (200Bh:01h) ---")
        try:
            driver_status = modbus.read_register(Z4_SLAVE_ID, 0x01DE)
            status_names = {
                0: "Not ready",
                1: "Ready",
                6: "Position closed-loop",
                8: "Speed closed-loop",
                9: "Torque control",
                10: "Open-loop control",
                12: "Error"
            }
            status_name = status_names.get(driver_status, f"Unknown ({driver_status})")
            print(f"[PASS] 驱动状态: {status_name}")
        except Exception as e:
            print(f"[WARN] 读取驱动状态失败: {e}")

        serial_port.close()
        return True

    except Exception as e:
        print(f"\n[FAIL] 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_initialization(port: str) -> bool:
    """测试 Z4 电机初始化"""
    print("\n" + "=" * 60)
    print(" Z4 轴参数初始化测试")
    print("=" * 60)

    try:
        from servo_service.modbus_rtu import ModbusClient
        from servo_service.serial_comm import SerialPort
        from servo_service.high_level_api.axis_config import DEFAULT_AXIS_CONFIGS

        serial_port = SerialPort(port, BAUDRATE)
        serial_port.open()

        modbus = ModbusClient(serial_port)

        # 获取 Z4 配置
        config = DEFAULT_AXIS_CONFIGS[AxisName.Z4]

        print(f"\nZ4 轴配置:")
        print(f"  从站地址: {config.slave_id}")
        print(f"  电机型号: {config.model}")
        print(f"  电机功率: {config.motor_power}W")
        print(f"  抱闸: {'有' if config.has_brake else '无'}")
        print(f"  丝杠导程: {config.ball_screw_lead}mm")
        print(f"  最大速度: {config.max_velocity}mm/s")
        print(f"  编码器分辨率: {config.encoder_resolution}")

        # 初始化电机参数
        print("\n正在初始化电机参数...")

        # 写入回零超时
        modbus.write_register(Z4_SLAVE_ID, Registers.HOMING_TIMEOUT.address, config.homing_timeout)
        print(f"  写入回零超时: {config.homing_timeout}ms")

        # 写入堵转参数
        modbus.write_register(Z4_SLAVE_ID, Registers.BLOCKING_TORQUE.address, config.blocking_torque)
        print(f"  写入堵转扭矩: {config.blocking_torque}")

        modbus.write_register(Z4_SLAVE_ID, Registers.BLOCKING_TIME.address, config.blocking_time)
        print(f"  写入堵转时间: {config.blocking_time}ms")

        # 写入 DI 配置
        if config.di2_function is not None:
            modbus.write_register(Z4_SLAVE_ID, Registers.DI2_FUNCTION.address, config.di2_function)
            modbus.write_register(Z4_SLAVE_ID, Registers.DI2_LOGIC.address, config.di2_logic)
            print(f"  写入 DI2: 功能={config.di2_function}, 逻辑={config.di2_logic}")

        if config.di3_function is not None:
            modbus.write_register(Z4_SLAVE_ID, Registers.DI3_FUNCTION.address, config.di3_function)
            modbus.write_register(Z4_SLAVE_ID, Registers.DI3_LOGIC.address, config.di3_logic)
            print(f"  写入 DI3: 功能={config.di3_function}, 逻辑={config.di3_logic}")

        time.sleep(0.2)
        print("[PASS] 参数写入完成")

        # 验证关键参数
        print("\n验证已写入参数:")

        # 回零超时
        homing_timeout = modbus.read_register(Z4_SLAVE_ID, Registers.HOMING_TIMEOUT.address)
        expected = config.homing_timeout
        status = "[PASS]" if homing_timeout == expected else "[FAIL]"
        print(f"  {status} 回零超时: {homing_timeout}ms (期望: {expected}ms)")

        # 堵转扭矩
        blocking_torque = modbus.read_register(Z4_SLAVE_ID, Registers.BLOCKING_TORQUE.address)
        expected = config.blocking_torque
        status = "[PASS]" if blocking_torque == expected else "[FAIL]"
        print(f"  {status} 堵转扭矩: {blocking_torque} (期望: {expected})")

        # DI2 功能
        di2_func = modbus.read_register(Z4_SLAVE_ID, Registers.DI2_FUNCTION.address)
        expected = config.di2_function
        status = "[PASS]" if di2_func == expected else "[FAIL]"
        print(f"  {status} DI2 功能: {di2_func} (期望: {expected})")

        # DI3 功能
        di3_func = modbus.read_register(Z4_SLAVE_ID, Registers.DI3_FUNCTION.address)
        expected = config.di3_function
        status = "[PASS]" if di3_func == expected else "[FAIL]"
        print(f"  {status} DI3 功能: {di3_func} (期望: {expected})")

        serial_port.close()
        return True

    except Exception as e:
        print(f"\n[FAIL] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print(" Z4 轴电机连接和初始化测试")
    print("=" * 60)

    # 查找串口
    port = find_serial_port()
    if not port:
        sys.exit(1)

    # 测试连接
    if not test_connection(port):
        print("\n连接测试失败，终止后续测试")
        sys.exit(1)

    # 测试初始化
    if not test_initialization(port):
        print("\n初始化测试失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
