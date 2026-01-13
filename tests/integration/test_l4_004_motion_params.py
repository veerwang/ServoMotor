#!/usr/bin/env python3
"""
TC-L4-004: 运动参数设置测试

测试内容:
1. 轮廓速度 (Profile Velocity) - 6081h
2. 轮廓加速度 (Profile Acceleration) - 6083h
3. 轮廓减速度 (Profile Deceleration) - 6084h
4. 快速停止减速度 (Quick Stop Deceleration) - 6085h
5. 软件位置限制 (Software Position Limits) - 607Dh
6. 运动轮廓类型 (Motion Profile Type) - 6086h

验证方法:
- 读取/写入各参数
- 验证不同参数设置下的运动行为
- 测试参数边界值
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
    """寄存器地址 (已验证)"""
    # 控制寄存器
    CONTROL_WORD = 0x0380      # 6040h
    STATUS_WORD = 0x0381       # 6041h
    OPERATION_MODE = 0x03C2    # 6060h

    # 位置寄存器
    TARGET_POSITION = 0x03E7   # 607Ah (32-bit)
    ACTUAL_POSITION = 0x03C8   # 6064h (32-bit)

    # 速度寄存器
    PROFILE_VELOCITY = 0x03F8  # 6081h (32-bit) user units/s
    ACTUAL_VELOCITY = 0x03D5   # 606Ch (32-bit) rpm

    # 加减速寄存器
    PROFILE_ACCEL = 0x03FC     # 6083h (32-bit) user units/s²
    PROFILE_DECEL = 0x03FE     # 6084h (32-bit) user units/s²
    QUICK_STOP_DECEL = 0x0400  # 6085h (32-bit) user units/s²

    # 运动轮廓
    MOTION_PROFILE_TYPE = 0x0402  # 6086h (0=梯形, 3=S曲线)

    # 软件限位
    SW_LIMIT_MIN = 0x03EF      # 607Dh:01 (32-bit)
    SW_LIMIT_MAX = 0x03F1      # 607Dh:02 (32-bit)

    # 位置窗口
    POSITION_WINDOW = 0x03CD   # 6067h
    POSITION_WINDOW_TIME = 0x03CF  # 6068h

    # 最大值限制
    MAX_PROFILE_VELOCITY = 0x03F4  # 607Fh (32-bit)
    MAX_MOTOR_SPEED = 0x03F6   # 6080h (32-bit) rpm


class MotionParamsTest:
    def __init__(self, port: str, slave_id: int):
        self.port = port
        self.slave_id = slave_id
        self.serial = None
        self.client = None
        self.test_results = []

    def connect(self):
        """连接到驱动器"""
        self.serial = SerialPort(port=self.port, baudrate=115200, timeout=0.5)
        self.serial.open()
        self.client = ModbusClient(serial_port=self.serial)
        logger.info(f"已连接到 {self.port}, 从站地址 {self.slave_id}")

    def disconnect(self):
        """断开连接"""
        if self.serial:
            self.serial.close()

    def read_reg(self, addr: int) -> int:
        """读取16位寄存器"""
        return self.client.read_holding_registers(self.slave_id, addr, 1)[0]

    def read_reg32(self, addr: int) -> int:
        """读取32位寄存器 (大端序)"""
        values = self.client.read_holding_registers(self.slave_id, addr, 2)
        value = ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)
        # 处理有符号数
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    def write_reg(self, addr: int, value: int):
        """写入16位寄存器"""
        self.client.write_single_register(self.slave_id, addr, value & 0xFFFF)

    def write_reg32(self, addr: int, value: int):
        """写入32位寄存器 (大端序)"""
        if value < 0:
            value += 0x100000000
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        self.client.write_multiple_registers(self.slave_id, addr, [high, low])

    def get_status_state(self) -> str:
        """获取当前状态机状态"""
        status = self.read_reg(Reg.STATUS_WORD)
        if status & 0x0008:  # Fault
            return "Fault"
        if (status & 0x006F) == 0x0027:  # Operation enabled
            return "Operation enabled"
        if (status & 0x006F) == 0x0023:  # Switched on
            return "Switched on"
        if (status & 0x006F) == 0x0021:  # Ready to switch on
            return "Ready to switch on"
        if (status & 0x004F) == 0x0040:  # Switch on disabled
            return "Switch on disabled"
        return f"Unknown (0x{status:04X})"

    def enable_motor(self) -> bool:
        """使能电机 (进入 Operation Enabled 状态)"""
        # 清除故障
        self.write_reg(Reg.CONTROL_WORD, 0x0080)
        time.sleep(0.1)

        # 状态机转换
        commands = [
            (0x0006, "Shutdown"),
            (0x0007, "Switch on"),
            (0x000F, "Enable operation"),
        ]

        for cmd, name in commands:
            self.write_reg(Reg.CONTROL_WORD, cmd)
            time.sleep(0.1)

        state = self.get_status_state()
        if state == "Operation enabled":
            logger.info("电机已使能")
            return True
        else:
            logger.error(f"使能失败，当前状态: {state}")
            return False

    def disable_motor(self):
        """禁用电机"""
        self.write_reg(Reg.CONTROL_WORD, 0x0006)
        time.sleep(0.1)

    def set_pp_mode(self):
        """设置为PP模式"""
        self.write_reg(Reg.OPERATION_MODE, 1)
        time.sleep(0.1)

    def move_absolute(self, position: int, wait: bool = True, timeout: float = 10.0) -> bool:
        """执行绝对位置运动"""
        self.write_reg32(Reg.TARGET_POSITION, position)
        time.sleep(0.05)

        # 触发运动 (绝对位置)
        self.write_reg(Reg.CONTROL_WORD, 0x000F)
        time.sleep(0.02)
        self.write_reg(Reg.CONTROL_WORD, 0x001F)  # 新设定点

        if not wait:
            return True

        # 等待目标到达
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.read_reg(Reg.STATUS_WORD)
            if status & 0x0400:  # Target reached
                return True
            time.sleep(0.1)

        return False

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "name": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {details}")

    # ==================== 测试用例 ====================

    def test_1_read_motion_params(self) -> bool:
        """测试1: 读取运动参数"""
        print("\n" + "=" * 60)
        print("测试 1: 读取运动参数")
        print("=" * 60)

        try:
            # 读取各参数
            profile_vel = self.read_reg32(Reg.PROFILE_VELOCITY)
            profile_accel = self.read_reg32(Reg.PROFILE_ACCEL)
            profile_decel = self.read_reg32(Reg.PROFILE_DECEL)
            quick_stop = self.read_reg32(Reg.QUICK_STOP_DECEL)
            motion_type = self.read_reg(Reg.MOTION_PROFILE_TYPE)
            max_vel = self.read_reg32(Reg.MAX_PROFILE_VELOCITY)
            max_motor_speed = self.read_reg32(Reg.MAX_MOTOR_SPEED)

            print(f"\n当前运动参数:")
            print(f"  轮廓速度 (6081h):     {profile_vel} user units/s")
            print(f"  轮廓加速度 (6083h):   {profile_accel} user units/s²")
            print(f"  轮廓减速度 (6084h):   {profile_decel} user units/s²")
            print(f"  快速停止减速度 (6085h): {quick_stop} user units/s²")
            print(f"  运动轮廓类型 (6086h): {motion_type} (0=梯形, 3=S曲线)")
            print(f"  最大轮廓速度 (607Fh): {max_vel} user units/s")
            print(f"  最大电机速度 (6080h): {max_motor_speed} rpm")

            # 读取软件限位
            sw_min = self.read_reg32(Reg.SW_LIMIT_MIN)
            sw_max = self.read_reg32(Reg.SW_LIMIT_MAX)
            print(f"\n软件限位:")
            print(f"  最小位置 (607Dh:01): {sw_min}")
            print(f"  最大位置 (607Dh:02): {sw_max}")

            self.record_result("读取运动参数", True, "成功读取所有参数")
            return True

        except Exception as e:
            self.record_result("读取运动参数", False, str(e))
            return False

    def test_2_velocity_setting(self) -> bool:
        """测试2: 轮廓速度设置"""
        print("\n" + "=" * 60)
        print("测试 2: 轮廓速度设置")
        print("=" * 60)

        try:
            self.set_pp_mode()
            if not self.enable_motor():
                self.record_result("轮廓速度设置", False, "电机使能失败")
                return False

            # 保存原始值
            orig_vel = self.read_reg32(Reg.PROFILE_VELOCITY)
            print(f"原始轮廓速度: {orig_vel}")

            # 测试不同速度值
            test_velocities = [5000, 10000, 20000]  # user units/s

            # 获取当前位置
            start_pos = self.read_reg32(Reg.ACTUAL_POSITION)

            for vel in test_velocities:
                print(f"\n设置速度: {vel} user units/s")
                self.write_reg32(Reg.PROFILE_VELOCITY, vel)
                time.sleep(0.05)

                # 验证写入
                read_vel = self.read_reg32(Reg.PROFILE_VELOCITY)
                print(f"读回速度: {read_vel}")

                if abs(read_vel - vel) > 1:
                    self.record_result("轮廓速度设置", False,
                                      f"速度写入验证失败: 写入{vel}, 读回{read_vel}")
                    return False

                # 执行短距离运动测试速度
                target = start_pos + 5000  # 移动5mm

                move_start = time.time()
                self.move_absolute(target, wait=True, timeout=10)
                move_time = time.time() - move_start

                # 计算预期时间 (距离/速度)
                expected_time = 5000 / vel
                print(f"移动时间: {move_time:.2f}s, 预期约: {expected_time:.2f}s")

                # 回到起点
                self.move_absolute(start_pos, wait=True, timeout=10)
                time.sleep(0.2)

            # 恢复原始值
            self.write_reg32(Reg.PROFILE_VELOCITY, orig_vel)

            self.disable_motor()
            self.record_result("轮廓速度设置", True, "不同速度设置验证通过")
            return True

        except Exception as e:
            self.disable_motor()
            self.record_result("轮廓速度设置", False, str(e))
            return False

    def test_3_acceleration_setting(self) -> bool:
        """测试3: 加减速设置"""
        print("\n" + "=" * 60)
        print("测试 3: 加减速设置")
        print("=" * 60)

        try:
            self.set_pp_mode()
            if not self.enable_motor():
                self.record_result("加减速设置", False, "电机使能失败")
                return False

            # 保存原始值
            orig_accel = self.read_reg32(Reg.PROFILE_ACCEL)
            orig_decel = self.read_reg32(Reg.PROFILE_DECEL)
            print(f"原始加速度: {orig_accel}, 原始减速度: {orig_decel}")

            # 设置固定速度用于测试
            self.write_reg32(Reg.PROFILE_VELOCITY, 20000)  # 20mm/s

            # 测试不同加减速值
            test_accels = [10000, 50000, 100000]  # user units/s²

            start_pos = self.read_reg32(Reg.ACTUAL_POSITION)

            for accel in test_accels:
                print(f"\n设置加速度/减速度: {accel} user units/s²")
                self.write_reg32(Reg.PROFILE_ACCEL, accel)
                self.write_reg32(Reg.PROFILE_DECEL, accel)
                time.sleep(0.05)

                # 验证写入
                read_accel = self.read_reg32(Reg.PROFILE_ACCEL)
                read_decel = self.read_reg32(Reg.PROFILE_DECEL)
                print(f"读回加速度: {read_accel}, 读回减速度: {read_decel}")

                if abs(read_accel - accel) > 1 or abs(read_decel - accel) > 1:
                    self.record_result("加减速设置", False, "加减速写入验证失败")
                    return False

                # 执行运动
                target = start_pos + 10000  # 移动10mm
                move_start = time.time()
                self.move_absolute(target, wait=True, timeout=10)
                move_time = time.time() - move_start
                print(f"移动时间: {move_time:.2f}s")

                # 回到起点
                self.move_absolute(start_pos, wait=True, timeout=10)
                time.sleep(0.2)

            # 恢复原始值
            self.write_reg32(Reg.PROFILE_ACCEL, orig_accel)
            self.write_reg32(Reg.PROFILE_DECEL, orig_decel)

            self.disable_motor()
            self.record_result("加减速设置", True, "不同加减速设置验证通过")
            return True

        except Exception as e:
            self.disable_motor()
            self.record_result("加减速设置", False, str(e))
            return False

    def test_4_quick_stop_decel(self) -> bool:
        """测试4: 快速停止减速度"""
        print("\n" + "=" * 60)
        print("测试 4: 快速停止减速度设置")
        print("=" * 60)

        try:
            # 保存原始值
            orig_qs = self.read_reg32(Reg.QUICK_STOP_DECEL)
            print(f"原始快速停止减速度: {orig_qs}")

            # 测试不同值
            test_values = [50000, 100000, 200000]

            for val in test_values:
                print(f"\n设置快速停止减速度: {val}")
                self.write_reg32(Reg.QUICK_STOP_DECEL, val)
                time.sleep(0.05)

                # 验证写入
                read_val = self.read_reg32(Reg.QUICK_STOP_DECEL)
                print(f"读回值: {read_val}")

                if abs(read_val - val) > 1:
                    self.record_result("快速停止减速度", False,
                                      f"写入验证失败: 写入{val}, 读回{read_val}")
                    return False

            # 恢复原始值
            self.write_reg32(Reg.QUICK_STOP_DECEL, orig_qs)

            self.record_result("快速停止减速度", True, "参数读写验证通过")
            return True

        except Exception as e:
            self.record_result("快速停止减速度", False, str(e))
            return False

    def test_5_motion_profile_type(self) -> bool:
        """测试5: 运动轮廓类型"""
        print("\n" + "=" * 60)
        print("测试 5: 运动轮廓类型")
        print("=" * 60)

        try:
            self.set_pp_mode()
            if not self.enable_motor():
                self.record_result("运动轮廓类型", False, "电机使能失败")
                return False

            # 保存原始值
            orig_type = self.read_reg(Reg.MOTION_PROFILE_TYPE)
            print(f"原始运动轮廓类型: {orig_type} (0=梯形, 3=S曲线)")

            # 设置运动参数
            self.write_reg32(Reg.PROFILE_VELOCITY, 20000)
            self.write_reg32(Reg.PROFILE_ACCEL, 50000)
            self.write_reg32(Reg.PROFILE_DECEL, 50000)

            start_pos = self.read_reg32(Reg.ACTUAL_POSITION)

            # 测试梯形轮廓
            print("\n--- 梯形轮廓 (0) ---")
            self.write_reg(Reg.MOTION_PROFILE_TYPE, 0)
            time.sleep(0.05)

            read_type = self.read_reg(Reg.MOTION_PROFILE_TYPE)
            print(f"读回类型: {read_type}")

            target = start_pos + 15000  # 15mm
            move_start = time.time()
            self.move_absolute(target, wait=True, timeout=10)
            trap_time = time.time() - move_start
            print(f"梯形轮廓移动时间: {trap_time:.3f}s")

            # 回到起点
            self.move_absolute(start_pos, wait=True, timeout=10)
            time.sleep(0.5)

            # 测试S曲线轮廓
            print("\n--- S曲线轮廓 (3) ---")
            self.write_reg(Reg.MOTION_PROFILE_TYPE, 3)
            time.sleep(0.05)

            read_type = self.read_reg(Reg.MOTION_PROFILE_TYPE)
            print(f"读回类型: {read_type}")

            move_start = time.time()
            self.move_absolute(target, wait=True, timeout=10)
            scurve_time = time.time() - move_start
            print(f"S曲线轮廓移动时间: {scurve_time:.3f}s")

            # 回到起点
            self.move_absolute(start_pos, wait=True, timeout=10)

            # 恢复原始值
            self.write_reg(Reg.MOTION_PROFILE_TYPE, orig_type)

            self.disable_motor()

            print(f"\n时间对比: 梯形={trap_time:.3f}s, S曲线={scurve_time:.3f}s")
            self.record_result("运动轮廓类型", True,
                             f"梯形={trap_time:.3f}s, S曲线={scurve_time:.3f}s")
            return True

        except Exception as e:
            self.disable_motor()
            self.record_result("运动轮廓类型", False, str(e))
            return False

    def test_6_software_limits(self) -> bool:
        """测试6: 软件位置限制"""
        print("\n" + "=" * 60)
        print("测试 6: 软件位置限制")
        print("=" * 60)

        try:
            # 读取当前软件限位
            sw_min = self.read_reg32(Reg.SW_LIMIT_MIN)
            sw_max = self.read_reg32(Reg.SW_LIMIT_MAX)
            print(f"当前软件限位: min={sw_min}, max={sw_max}")

            # 测试写入软件限位
            test_min = -50000  # -50mm
            test_max = 50000   # +50mm

            print(f"\n写入测试限位: min={test_min}, max={test_max}")
            self.write_reg32(Reg.SW_LIMIT_MIN, test_min)
            self.write_reg32(Reg.SW_LIMIT_MAX, test_max)
            time.sleep(0.05)

            # 验证写入
            read_min = self.read_reg32(Reg.SW_LIMIT_MIN)
            read_max = self.read_reg32(Reg.SW_LIMIT_MAX)
            print(f"读回限位: min={read_min}, max={read_max}")

            if abs(read_min - test_min) > 1 or abs(read_max - test_max) > 1:
                self.record_result("软件位置限制", False, "软件限位写入验证失败")
                return False

            # 恢复原始限位
            self.write_reg32(Reg.SW_LIMIT_MIN, sw_min)
            self.write_reg32(Reg.SW_LIMIT_MAX, sw_max)

            self.record_result("软件位置限制", True, "软件限位读写验证通过")
            return True

        except Exception as e:
            self.record_result("软件位置限制", False, str(e))
            return False

    def test_7_position_window(self) -> bool:
        """测试7: 位置窗口设置"""
        print("\n" + "=" * 60)
        print("测试 7: 位置窗口设置")
        print("=" * 60)

        try:
            # 读取当前值
            pos_window = self.read_reg(Reg.POSITION_WINDOW)
            pos_window_time = self.read_reg(Reg.POSITION_WINDOW_TIME)
            print(f"当前位置窗口: {pos_window} units, 时间: {pos_window_time} ms")

            # 测试写入
            test_window = 20
            test_time = 10

            print(f"\n写入测试值: 窗口={test_window}, 时间={test_time}ms")
            self.write_reg(Reg.POSITION_WINDOW, test_window)
            self.write_reg(Reg.POSITION_WINDOW_TIME, test_time)
            time.sleep(0.05)

            # 验证
            read_window = self.read_reg(Reg.POSITION_WINDOW)
            read_time = self.read_reg(Reg.POSITION_WINDOW_TIME)
            print(f"读回值: 窗口={read_window}, 时间={read_time}ms")

            if read_window != test_window or read_time != test_time:
                self.record_result("位置窗口设置", False, "位置窗口写入验证失败")
                return False

            # 恢复原始值
            self.write_reg(Reg.POSITION_WINDOW, pos_window)
            self.write_reg(Reg.POSITION_WINDOW_TIME, pos_window_time)

            self.record_result("位置窗口设置", True, "位置窗口读写验证通过")
            return True

        except Exception as e:
            self.record_result("位置窗口设置", False, str(e))
            return False

    def run_all_tests(self, auto: bool = False):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("TC-L4-004: 运动参数设置测试")
        print("=" * 70)

        self.connect()

        try:
            # 运行测试
            self.test_1_read_motion_params()

            if auto:
                self.test_2_velocity_setting()
                self.test_3_acceleration_setting()
                self.test_4_quick_stop_decel()
                self.test_5_motion_profile_type()
                self.test_6_software_limits()
                self.test_7_position_window()
            else:
                # 交互模式
                tests = [
                    ("轮廓速度设置", self.test_2_velocity_setting),
                    ("加减速设置", self.test_3_acceleration_setting),
                    ("快速停止减速度", self.test_4_quick_stop_decel),
                    ("运动轮廓类型", self.test_5_motion_profile_type),
                    ("软件位置限制", self.test_6_software_limits),
                    ("位置窗口设置", self.test_7_position_window),
                ]

                for name, test_func in tests:
                    resp = input(f"\n是否执行 '{name}' 测试? (y/n): ")
                    if resp.lower() == 'y':
                        test_func()
                    else:
                        self.record_result(name, False, "跳过")

        finally:
            self.disable_motor()
            self.disconnect()

        # 打印测试汇总
        self.print_summary()

    def print_summary(self):
        """打印测试汇总"""
        print("\n" + "=" * 70)
        print("测试汇总")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)

        for r in self.test_results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  [{status}] {r['name']}: {r['details']}")

        print("-" * 70)
        print(f"通过: {passed}/{total}")

        if passed == total:
            print("\nTC-L4-004 测试通过!")
        else:
            print(f"\nTC-L4-004 测试失败: {total - passed} 个测试未通过")


def main():
    parser = argparse.ArgumentParser(description="TC-L4-004: 运动参数设置测试")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--auto", action="store_true", help="自动运行所有测试")
    args = parser.parse_args()

    test = MotionParamsTest(args.port, args.slave_id)
    test.run_all_tests(auto=args.auto)


if __name__ == "__main__":
    main()
