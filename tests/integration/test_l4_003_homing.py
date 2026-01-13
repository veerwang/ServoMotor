#!/usr/bin/env python3
"""
TC-L4-003: 回零操作测试

测试 Homing Mode (HM) 下的回零功能:
- HM 模式设置
- 回零参数配置
- 限位开关回零 (方式 17)
- 回零状态监控
- 回零完成检测

前置条件:
- DI2 已配置为正限位 (功能 14)
- DI3 已配置为负限位 (功能 15)
"""

import argparse
import logging
import sys
import time
from typing import Optional

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
    # 控制与状态
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    OPERATION_MODE = 0x03C2
    OPERATION_MODE_DISPLAY = 0x03C3

    # 位置
    POSITION_ACTUAL = 0x03C8  # 32位

    # 回零参数
    HOMING_METHOD = 0x0416
    HOMING_SPEED_FAST = 0x0417  # 32位
    HOMING_SPEED_SLOW = 0x0419  # 32位
    HOMING_ACCELERATION = 0x041B  # 32位
    HOME_OFFSET = 0x03ED  # 32位

    # DI 监控
    DI_MONITOR = 0x01E2

    # DI 配置
    DI2_FUNCTION = 0x00D7
    DI2_LOGIC = 0x00D8
    DI3_FUNCTION = 0x00D9
    DI3_LOGIC = 0x00DA


class StatusWord:
    """状态字位定义"""
    READY_TO_SWITCH_ON = 0x0001
    SWITCHED_ON = 0x0002
    OPERATION_ENABLED = 0x0004
    FAULT = 0x0008
    VOLTAGE_ENABLED = 0x0010
    QUICK_STOP = 0x0020
    SWITCH_ON_DISABLED = 0x0040
    WARNING = 0x0080
    TARGET_REACHED = 0x0400
    HOMING_ATTAINED = 0x1000  # Bit 12
    HOMING_ERROR = 0x2000     # Bit 13


class HomingTest:
    """回零测试类"""

    def __init__(self, port: str, slave_id: int, auto_mode: bool = False):
        self.port = port
        self.slave_id = slave_id
        self.auto_mode = auto_mode
        self.client: Optional[ModbusClient] = None
        self.serial: Optional[SerialPort] = None
        self.passed = 0
        self.failed = 0
        self.test_results = []

    def connect(self) -> bool:
        """连接到驱动器"""
        try:
            self.serial = SerialPort(port=self.port, baudrate=115200, timeout=0.5)
            self.serial.open()
            self.client = ModbusClient(serial_port=self.serial)
            logger.info("连接成功")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.serial:
            self.serial.close()

    def read_register(self, address: int) -> int:
        """读取单个寄存器"""
        return self.client.read_register(self.slave_id, address)

    def write_register(self, address: int, value: int):
        """写入单个寄存器"""
        self.client.write_register(self.slave_id, address, value)

    def read_register_32(self, address: int) -> int:
        """读取 32 位寄存器 (大端序)"""
        values = self.client.read_holding_registers(self.slave_id, address, 2)
        value = ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)
        # 处理有符号数
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    def write_register_32(self, address: int, value: int):
        """写入 32 位寄存器 (大端序)"""
        if value < 0:
            value += 0x100000000
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        self.client.write_multiple_registers(self.slave_id, address, [high, low])

    def get_status_string(self, status: int) -> str:
        """解析状态字"""
        if status & StatusWord.FAULT:
            return "Fault"
        if status & StatusWord.SWITCH_ON_DISABLED:
            return "Switch on disabled"
        if status & StatusWord.OPERATION_ENABLED:
            return "Operation enabled"
        if status & StatusWord.SWITCHED_ON:
            return "Switched on"
        if status & StatusWord.READY_TO_SWITCH_ON:
            return "Ready to switch on"
        return f"Unknown (0x{status:04X})"

    def check_di_config(self) -> dict:
        """检查 DI 配置状态"""
        di2_func = self.read_register(Reg.DI2_FUNCTION)
        di2_logic = self.read_register(Reg.DI2_LOGIC)
        di3_func = self.read_register(Reg.DI3_FUNCTION)
        di3_logic = self.read_register(Reg.DI3_LOGIC)
        di_state = self.read_register(Reg.DI_MONITOR)

        return {
            "di2_function": di2_func,
            "di2_logic": di2_logic,
            "di3_function": di3_func,
            "di3_logic": di3_logic,
            "di_physical_state": di_state,
            "di2_state": bool(di_state & 0x0002),
            "di3_state": bool(di_state & 0x0004),
            "positive_limit_configured": di2_func == 14,
            "negative_limit_configured": di3_func == 15,
        }

    def wait_for_state(self, expected_state: int, timeout: float = 5.0) -> bool:
        """等待状态转换"""
        start = time.time()
        while time.time() - start < timeout:
            status = self.read_register(Reg.STATUS_WORD)
            if (status & 0x006F) == expected_state:
                return True
            time.sleep(0.05)
        return False

    def enable_drive(self) -> bool:
        """使能驱动器"""
        # Shutdown
        self.write_register(Reg.CONTROL_WORD, 0x0006)
        if not self.wait_for_state(0x0021, 3.0):
            logger.warning("Shutdown 超时")

        # Switch on
        self.write_register(Reg.CONTROL_WORD, 0x0007)
        if not self.wait_for_state(0x0023, 3.0):
            logger.warning("Switch on 超时")

        # Enable operation
        self.write_register(Reg.CONTROL_WORD, 0x000F)
        if not self.wait_for_state(0x0027, 3.0):
            logger.warning("Enable operation 超时")
            return False

        return True

    def disable_drive(self):
        """禁用驱动器"""
        self.write_register(Reg.CONTROL_WORD, 0x0006)
        time.sleep(0.2)

    def log_test(self, name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "通过" if passed else "失败"
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        logger.info(f"测试 '{name}': {status} {details}")

    def run_tests(self):
        """运行测试"""
        print("\n" + "=" * 60)
        print("TC-L4-003: 回零操作测试")
        print("=" * 60)
        print(f"串口: {self.port}")
        print(f"从站地址: 0x{self.slave_id:02X}")
        print(f"自动模式: {self.auto_mode}")
        print()

        if not self.connect():
            return

        try:
            # 测试 1: 检查 DI 配置
            self._test_di_config()

            # 测试 2: 检查当前位置和状态
            self._test_initial_state()

            # 测试 3: 设置 HM 模式
            self._test_set_hm_mode()

            # 测试 4: 配置回零参数
            self._test_set_homing_params()

            # 测试 5: 使能操作
            self._test_enable_operation()

            # 测试 6: 执行回零
            self._test_homing_execution()

            # 测试 7: 验证回零结果
            self._test_verify_homing()

            # 测试 8: 禁用操作
            self._test_disable_operation()

            # 显示结果汇总
            self._show_summary()

        except KeyboardInterrupt:
            print("\n\n测试被用户中断")
        except Exception as e:
            logger.error(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 确保禁用驱动器
            try:
                self.disable_drive()
            except:
                pass
            self.disconnect()

    def _test_di_config(self):
        """测试 1: 检查 DI 配置"""
        print("\n--- 测试 1: 检查 DI 配置 ---")

        di_config = self.check_di_config()

        print(f"DI2 功能: {di_config['di2_function']} (期望 14=正限位)")
        print(f"DI2 逻辑: {di_config['di2_logic']} (期望 0=低电平有效)")
        print(f"DI3 功能: {di_config['di3_function']} (期望 15=负限位)")
        print(f"DI3 逻辑: {di_config['di3_logic']} (期望 0=低电平有效)")
        print(f"DI 物理状态: 0x{di_config['di_physical_state']:04X}")
        print(f"  DI2 (正限位): {'高' if di_config['di2_state'] else '低 (触发)'}")
        print(f"  DI3 (负限位): {'高' if di_config['di3_state'] else '低 (触发)'}")

        passed = di_config['positive_limit_configured'] and di_config['negative_limit_configured']

        if not passed:
            print("\n警告: 限位开关未正确配置!")
            print("请先运行 diagnose_limit_switches.py 配置限位开关")

        self.log_test("检查 DI 配置", passed,
                     f"正限位={di_config['positive_limit_configured']}, 负限位={di_config['negative_limit_configured']}")

    def _test_initial_state(self):
        """测试 2: 检查初始状态"""
        print("\n--- 测试 2: 检查初始状态 ---")

        status = self.read_register(Reg.STATUS_WORD)
        mode = self.read_register(Reg.OPERATION_MODE_DISPLAY)
        position = self.read_register_32(Reg.POSITION_ACTUAL)

        print(f"状态字: 0x{status:04X} ({self.get_status_string(status)})")
        print(f"当前模式: {mode}")
        print(f"当前位置: {position} 脉冲")

        # 检查是否在限位
        di_state = self.read_register(Reg.DI_MONITOR)
        at_pos_limit = not bool(di_state & 0x0002)
        at_neg_limit = not bool(di_state & 0x0004)

        if at_pos_limit:
            print("注意: 当前在正限位位置")
        if at_neg_limit:
            print("注意: 当前在负限位位置")

        passed = not (status & StatusWord.FAULT)
        self.log_test("检查初始状态", passed, f"状态=0x{status:04X}, 位置={position}")

    def _test_set_hm_mode(self):
        """测试 3: 设置 HM 模式"""
        print("\n--- 测试 3: 设置 HM 模式 ---")

        # 写入 HM 模式 (6)
        self.write_register(Reg.OPERATION_MODE, 6)
        time.sleep(0.1)

        # 读回验证
        mode = self.read_register(Reg.OPERATION_MODE_DISPLAY)
        print(f"操作模式: {mode} (期望 6=HM)")

        passed = mode == 6
        self.log_test("设置 HM 模式", passed, f"mode={mode}")

    def _test_set_homing_params(self):
        """测试 4: 配置回零参数"""
        print("\n--- 测试 4: 配置回零参数 ---")

        # 回零方式 17: 负限位开关回零
        homing_method = 17
        homing_speed_fast = 10000  # user units/s (约 60 RPM)
        homing_speed_slow = 2000   # user units/s (约 12 RPM)
        homing_accel = 50000       # user units/s²
        home_offset = 0            # 偏移量

        print(f"回零方式: {homing_method} (负限位回零)")
        print(f"快速回零速度: {homing_speed_fast} user units/s")
        print(f"慢速回零速度: {homing_speed_slow} user units/s")
        print(f"回零加速度: {homing_accel} user units/s²")
        print(f"原点偏移: {home_offset}")

        # 写入参数
        self.write_register(Reg.HOMING_METHOD, homing_method)
        self.write_register_32(Reg.HOMING_SPEED_FAST, homing_speed_fast)
        self.write_register_32(Reg.HOMING_SPEED_SLOW, homing_speed_slow)
        self.write_register_32(Reg.HOMING_ACCELERATION, homing_accel)
        self.write_register_32(Reg.HOME_OFFSET, home_offset)

        time.sleep(0.1)

        # 读回验证
        method_readback = self.read_register(Reg.HOMING_METHOD)
        speed_fast_readback = self.read_register_32(Reg.HOMING_SPEED_FAST)
        speed_slow_readback = self.read_register_32(Reg.HOMING_SPEED_SLOW)
        accel_readback = self.read_register_32(Reg.HOMING_ACCELERATION)

        print(f"\n读回验证:")
        print(f"  回零方式: {method_readback}")
        print(f"  快速速度: {speed_fast_readback}")
        print(f"  慢速速度: {speed_slow_readback}")
        print(f"  加速度: {accel_readback}")

        passed = (method_readback == homing_method and
                 speed_fast_readback == homing_speed_fast)
        self.log_test("配置回零参数", passed, f"method={method_readback}")

    def _test_enable_operation(self):
        """测试 5: 使能操作"""
        print("\n--- 测试 5: 使能操作 ---")

        result = self.enable_drive()

        status = self.read_register(Reg.STATUS_WORD)
        print(f"状态字: 0x{status:04X} ({self.get_status_string(status)})")

        passed = result and (status & StatusWord.OPERATION_ENABLED)
        self.log_test("使能操作", passed, f"status=0x{status:04X}")

    def _test_homing_execution(self):
        """测试 6: 执行回零"""
        print("\n--- 测试 6: 执行回零 ---")

        if not self.auto_mode:
            print("\n警告: 回零操作将使电机运动!")
            print("请确保:")
            print("  1. 运动路径畅通无阻碍")
            print("  2. 限位开关正常工作")
            print("  3. 准备好紧急停止")
            input("\n按 Enter 开始回零...")

        # 记录初始位置
        initial_pos = self.read_register_32(Reg.POSITION_ACTUAL)
        print(f"初始位置: {initial_pos}")

        # 启动回零: 设置 bit4 (新设定点)
        print("启动回零...")
        self.write_register(Reg.CONTROL_WORD, 0x001F)
        time.sleep(0.1)

        # 监控回零过程
        timeout = 30.0  # 最长 30 秒
        start_time = time.time()
        homing_complete = False
        homing_error = False
        last_pos = initial_pos

        print("\n回零过程监控:")
        while time.time() - start_time < timeout:
            status = self.read_register(Reg.STATUS_WORD)
            position = self.read_register_32(Reg.POSITION_ACTUAL)
            di_state = self.read_register(Reg.DI_MONITOR)

            # 检查状态
            homing_attained = bool(status & StatusWord.HOMING_ATTAINED)
            homing_error = bool(status & StatusWord.HOMING_ERROR)
            target_reached = bool(status & StatusWord.TARGET_REACHED)

            # 检查限位状态
            at_neg_limit = not bool(di_state & 0x0004)

            # 显示进度
            if position != last_pos or homing_attained or homing_error:
                pos_diff = position - initial_pos
                print(f"  位置: {position:10d} (Δ{pos_diff:+8d}) | "
                      f"负限位: {'触发' if at_neg_limit else '未触发'} | "
                      f"状态: 0x{status:04X}")
                last_pos = position

            if homing_attained:
                print(f"\n回零完成! (用时 {time.time() - start_time:.2f} 秒)")
                homing_complete = True
                break

            if homing_error:
                print(f"\n回零错误! 状态字: 0x{status:04X}")
                break

            # 检查是否有故障
            if status & StatusWord.FAULT:
                print(f"\n驱动器故障! 状态字: 0x{status:04X}")
                break

            time.sleep(0.2)

        if not homing_complete and not homing_error:
            print(f"\n回零超时 ({timeout}秒)")

        # 最终位置
        final_pos = self.read_register_32(Reg.POSITION_ACTUAL)
        print(f"\n最终位置: {final_pos}")
        print(f"位移: {final_pos - initial_pos}")

        self.log_test("执行回零", homing_complete,
                     f"complete={homing_complete}, error={homing_error}")

    def _test_verify_homing(self):
        """测试 7: 验证回零结果"""
        print("\n--- 测试 7: 验证回零结果 ---")

        status = self.read_register(Reg.STATUS_WORD)
        position = self.read_register_32(Reg.POSITION_ACTUAL)

        homing_attained = bool(status & StatusWord.HOMING_ATTAINED)

        print(f"状态字: 0x{status:04X}")
        print(f"  HOMING_ATTAINED: {homing_attained}")
        print(f"  TARGET_REACHED: {bool(status & StatusWord.TARGET_REACHED)}")
        print(f"当前位置: {position}")

        # 检查位置是否接近零点
        position_near_home = abs(position) < 1000  # 允许 1000 脉冲误差

        passed = homing_attained
        details = f"homing_attained={homing_attained}, position={position}"

        if homing_attained and not position_near_home:
            print(f"\n注意: 位置 {position} 不是零点")
            print("这可能是因为设置了原点偏移或编码器绝对位置")

        self.log_test("验证回零结果", passed, details)

    def _test_disable_operation(self):
        """测试 8: 禁用操作"""
        print("\n--- 测试 8: 禁用操作 ---")

        self.disable_drive()
        time.sleep(0.2)

        status = self.read_register(Reg.STATUS_WORD)
        print(f"最终状态: 0x{status:04X} ({self.get_status_string(status)})")

        passed = not (status & StatusWord.OPERATION_ENABLED)
        self.log_test("禁用操作", passed, f"status=0x{status:04X}")

    def _show_summary(self):
        """显示测试结果汇总"""
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)

        for i, result in enumerate(self.test_results, 1):
            status = "通过" if result['passed'] else "失败"
            print(f"{i}. {result['name']}: {status}")

        print("-" * 60)
        total = self.passed + self.failed
        print(f"总计: {self.passed}/{total} 通过, {self.failed}/{total} 失败")

        if self.failed == 0:
            print("\n所有测试通过!")
        else:
            print(f"\n有 {self.failed} 个测试失败")


def main():
    parser = argparse.ArgumentParser(description="TC-L4-003 回零操作测试")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--auto", action="store_true", help="自动模式 (无需确认)")
    args = parser.parse_args()

    test = HomingTest(args.port, args.slave_id, args.auto)
    test.run_tests()


if __name__ == "__main__":
    main()
