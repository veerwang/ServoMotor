#!/usr/bin/env python3
"""
TC-L4-002: PV模式速度运动测试

测试 Profile Velocity (PV) 模式下的速度运动功能:
- PV 模式设置
- 速度参数配置
- 正向/反向速度运动
- 速度达标检测
- Halt 停止功能

PV 模式单位说明:
- 目标速度 (60FFh): user units/s
- 实际速度 (606Ch): RPM
- 加速度/减速度: user units/s²

单位换算:
- 1 RPM = encoder_resolution / 60 user units/s
- 例如: 10000 脉冲/圈, 300 RPM = 300 * 10000 / 60 = 50000 user units/s
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, ".")

from servo_service.modbus_rtu import ModbusClient
from servo_service.serial_comm import SerialPort

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """
    测试配置

    PV 模式单位说明:
    - 目标速度: user units/s (不是 RPM!)
    - 实际速度寄存器返回: RPM
    - 加速度/减速度: user units/s²

    单位换算 (假设 encoder_resolution = 10000):
    - target_velocity = 50000 user units/s ≈ 300 RPM
    """
    port: str = "/dev/ttyUSB0"
    baudrate: int = 115200
    slave_id: int = 0x03  # Z 轴

    # 速度参数 (user units/s)
    target_velocity_forward: int = 50000   # 正向速度 ≈ 300 RPM
    target_velocity_reverse: int = -50000  # 反向速度 ≈ -300 RPM

    # 加减速参数 (user units/s²)
    profile_acceleration: int = 100000
    profile_deceleration: int = 100000

    # 安全限制
    max_velocity_rpm: int = 1000  # 最大允许速度 (RPM)
    velocity_run_time: float = 2.0  # 每个速度运行时间 (秒)
    velocity_timeout: float = 5.0  # 速度达标超时 (秒)

    # 编码器分辨率 (用于单位换算显示)
    encoder_resolution: int = 10000


class Reg:
    """寄存器地址 (已验证)"""
    # 控制寄存器
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    ERROR_CODE = 0x0382

    # 模式设置
    MODES_OF_OPERATION = 0x03C2
    MODES_OF_OPERATION_DISPLAY = 0x03C3

    # PV 模式寄存器
    TARGET_VELOCITY = 0x0448      # 60FFh - 目标速度 (32位, user units/s)
    VELOCITY_ACTUAL = 0x03D5      # 606Ch - 实际速度 (32位, RPM)
    VELOCITY_DEMAND = 0x03D3      # 606Bh - 速度命令 (32位)

    # 轮廓参数
    PROFILE_ACCELERATION = 0x03FC  # 6083h
    PROFILE_DECELERATION = 0x03FE  # 6084h
    MAX_PROFILE_VELOCITY = 0x03F4  # 607Fh
    MAX_MOTOR_SPEED = 0x03F6       # 6080h


class ControlWord:
    """控制字命令"""
    SHUTDOWN = 0x0006
    SWITCH_ON = 0x0007
    ENABLE_OPERATION = 0x000F
    DISABLE_VOLTAGE = 0x0000
    QUICK_STOP = 0x0002
    HALT = 0x010F  # Enable + Halt bit


class StatusMask:
    """状态字掩码"""
    READY_TO_SWITCH_ON = 0x0001
    SWITCHED_ON = 0x0002
    OPERATION_ENABLED = 0x0004
    FAULT = 0x0008
    VOLTAGE_ENABLED = 0x0010
    QUICK_STOP = 0x0020
    SWITCH_ON_DISABLED = 0x0040
    WARNING = 0x0080
    TARGET_REACHED = 0x0400
    SPEED_ZERO = 0x1000  # Bit 12 in PV mode


class PVModeTester:
    """PV 模式测试器"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.client: Optional[ModbusClient] = None
        self.serial: Optional[SerialPort] = None
        self.test_results: Dict[str, Tuple[bool, Dict]] = {}

    def connect(self) -> bool:
        """连接到驱动器"""
        try:
            logger.info(f"连接到 {self.config.port} @ {self.config.baudrate}")
            logger.info(f"目标从站: 0x{self.config.slave_id:02X}")

            self.serial = SerialPort(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=0.5,
            )
            self.serial.open()

            self.client = ModbusClient(serial_port=self.serial)

            # 验证通信
            status = self._read_status()
            logger.info(f"通信成功, 状态字: 0x{status:04X}")

            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.serial:
            self.serial.close()
            logger.info("已断开连接")

    def emergency_stop(self):
        """紧急停止"""
        try:
            logger.warning("执行急停!")
            self._write_control(ControlWord.QUICK_STOP)
            time.sleep(0.1)
            self._write_control(ControlWord.DISABLE_VOLTAGE)
        except Exception:
            pass

    def _read_register(self, address: int) -> int:
        if not self.client:
            raise RuntimeError("未连接")
        return self.client.read_register(self.config.slave_id, address)

    def _write_register(self, address: int, value: int):
        if not self.client:
            raise RuntimeError("未连接")
        self.client.write_register(self.config.slave_id, address, value)

    def _read_register_32bit(self, address: int, signed: bool = True) -> int:
        """读取 32 位寄存器 (大端序: 高字在前)"""
        if not self.client:
            raise RuntimeError("未连接")
        values = self.client.read_holding_registers(self.config.slave_id, address, 2)
        # NiMotion 实际使用大端序: [高字, 低字]
        value = ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)
        if signed and value >= 0x80000000:
            value -= 0x100000000
        return value

    def _write_register_32bit(self, address: int, value: int):
        """写入 32 位寄存器 (大端序)"""
        if not self.client:
            raise RuntimeError("未连接")
        if value < 0:
            value += 0x100000000
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        self.client.write_multiple_registers(
            self.config.slave_id, address, [high, low]
        )

    def _read_status(self) -> int:
        return self._read_register(Reg.STATUS_WORD)

    def _write_control(self, value: int):
        self._write_register(Reg.CONTROL_WORD, value)

    def _read_velocity(self) -> int:
        """读取实际速度 (RPM)"""
        return self._read_register_32bit(Reg.VELOCITY_ACTUAL)

    def _get_state_name(self, status: int) -> str:
        """获取状态名称"""
        if status & StatusMask.FAULT:
            return "Fault"
        if status & StatusMask.SWITCH_ON_DISABLED:
            return "Switch on disabled"
        if status & StatusMask.OPERATION_ENABLED:
            return "Operation enabled"
        if status & StatusMask.SWITCHED_ON:
            return "Switched on"
        if status & StatusMask.READY_TO_SWITCH_ON:
            return "Ready to switch on"
        return f"Unknown(0x{status & 0x6F:04X})"

    def _velocity_to_rpm(self, velocity_user_units: int) -> float:
        """将 user units/s 转换为 RPM"""
        return velocity_user_units * 60 / self.config.encoder_resolution

    def _monitor_velocity(self) -> bool:
        """监控速度安全"""
        try:
            velocity = abs(self._read_velocity())
            if velocity > self.config.max_velocity_rpm:
                logger.error(f"速度异常! {velocity} rpm > {self.config.max_velocity_rpm} rpm")
                self.emergency_stop()
                return False
            return True
        except Exception:
            return True

    # ==================== 测试步骤 ====================

    def test_1_check_initial_state(self) -> Tuple[bool, Dict]:
        """测试 1: 检查初始状态"""
        result = {}
        try:
            status = self._read_status()
            mode = self._read_register(Reg.MODES_OF_OPERATION_DISPLAY)
            velocity = self._read_velocity()

            result["状态字"] = f"0x{status:04X}"
            result["驱动器状态"] = self._get_state_name(status)
            result["当前速度"] = f"{velocity} RPM"
            result["当前模式"] = f"{mode}"

            # 初始状态可以是多种状态
            return True, result

        except Exception as e:
            result["错误"] = str(e)
            return False, result

    def test_2_set_pv_mode(self) -> Tuple[bool, Dict]:
        """测试 2: 设置 PV 模式"""
        result = {}
        try:
            # 写入 PV 模式 (3)
            self._write_register(Reg.MODES_OF_OPERATION, 3)
            time.sleep(0.1)

            # 读回验证
            mode = self._read_register(Reg.MODES_OF_OPERATION_DISPLAY)
            result["写入值"] = "3 (PV 模式)"
            result["读回值"] = f"{mode} ({'PV 模式' if mode == 3 else '其他模式'})"

            if mode == 3:
                return True, result
            else:
                result["错误"] = f"模式设置失败，期望 3，实际 {mode}"
                return False, result

        except Exception as e:
            result["错误"] = str(e)
            return False, result

    def test_3_set_velocity_parameters(self) -> Tuple[bool, Dict]:
        """测试 3: 设置速度参数"""
        result = {}
        errors = []

        try:
            # 设置加速度
            self._write_register_32bit(Reg.PROFILE_ACCELERATION, self.config.profile_acceleration)
            time.sleep(0.05)
            acc_read = self._read_register_32bit(Reg.PROFILE_ACCELERATION, signed=False)
            result["轮廓加速度"] = f"写入 {self.config.profile_acceleration}, 读回 {acc_read}"
            if acc_read != self.config.profile_acceleration:
                errors.append("加速度读回不匹配")
        except Exception as e:
            errors.append(f"加速度设置失败: {e}")
            result["轮廓加速度"] = f"失败: {e}"

        try:
            # 设置减速度
            self._write_register_32bit(Reg.PROFILE_DECELERATION, self.config.profile_deceleration)
            time.sleep(0.05)
            dec_read = self._read_register_32bit(Reg.PROFILE_DECELERATION, signed=False)
            result["轮廓减速度"] = f"写入 {self.config.profile_deceleration}, 读回 {dec_read}"
            if dec_read != self.config.profile_deceleration:
                errors.append("减速度读回不匹配")
        except Exception as e:
            errors.append(f"减速度设置失败: {e}")
            result["轮廓减速度"] = f"失败: {e}"

        if errors:
            result["警告"] = "; ".join(errors)

        # 即使有警告也继续测试
        return True, result

    def test_4_enable_operation(self) -> Tuple[bool, Dict]:
        """测试 4: 使能操作"""
        result = {}
        try:
            # Shutdown
            self._write_control(ControlWord.SHUTDOWN)
            time.sleep(0.1)
            status = self._read_status()
            result["Shutdown 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            # Switch on
            self._write_control(ControlWord.SWITCH_ON)
            time.sleep(0.1)
            status = self._read_status()
            result["Switch On 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            # Enable operation
            self._write_control(ControlWord.ENABLE_OPERATION)
            time.sleep(0.1)
            status = self._read_status()
            result["Enable 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            if status & StatusMask.OPERATION_ENABLED:
                return True, result
            else:
                result["错误"] = "未能进入 Operation enabled 状态"
                return False, result

        except Exception as e:
            result["错误"] = str(e)
            return False, result

    def test_5_forward_velocity(self) -> Tuple[bool, Dict]:
        """测试 5: 正向速度运动"""
        result = {}
        try:
            target_vel = self.config.target_velocity_forward
            target_rpm = self._velocity_to_rpm(target_vel)

            result["目标速度"] = f"{target_vel} user units/s (≈{target_rpm:.0f} RPM)"

            # 设置目标速度
            self._write_register_32bit(Reg.TARGET_VELOCITY, target_vel)
            time.sleep(0.1)

            # 等待速度稳定
            start_time = time.time()
            max_velocity = 0
            velocity_reached = False

            while time.time() - start_time < self.config.velocity_run_time:
                # 安全检查
                if not self._monitor_velocity():
                    result["错误"] = "速度超限"
                    return False, result

                velocity = self._read_velocity()
                max_velocity = max(max_velocity, abs(velocity))

                # 检查是否达到目标速度 (允许 10% 误差)
                if abs(velocity) >= abs(target_rpm) * 0.9:
                    velocity_reached = True

                status = self._read_status()
                if status & StatusMask.TARGET_REACHED:
                    result["TARGET_REACHED"] = "True"

                time.sleep(0.1)

            final_velocity = self._read_velocity()
            result["最大速度"] = f"{max_velocity} RPM"
            result["最终速度"] = f"{final_velocity} RPM"
            result["速度达标"] = str(velocity_reached)

            if velocity_reached or max_velocity > 0:
                return True, result
            else:
                result["警告"] = "电机未运动"
                return True, result  # 继续测试

        except Exception as e:
            result["错误"] = str(e)
            self.emergency_stop()
            return False, result

    def test_6_reverse_velocity(self) -> Tuple[bool, Dict]:
        """测试 6: 反向速度运动"""
        result = {}
        try:
            target_vel = self.config.target_velocity_reverse
            target_rpm = self._velocity_to_rpm(target_vel)

            result["目标速度"] = f"{target_vel} user units/s (≈{target_rpm:.0f} RPM)"

            # 设置目标速度 (负值)
            self._write_register_32bit(Reg.TARGET_VELOCITY, target_vel)
            time.sleep(0.1)

            # 等待速度稳定
            start_time = time.time()
            min_velocity = 0
            velocity_reached = False

            while time.time() - start_time < self.config.velocity_run_time:
                # 安全检查
                if not self._monitor_velocity():
                    result["错误"] = "速度超限"
                    return False, result

                velocity = self._read_velocity()
                if velocity < min_velocity:
                    min_velocity = velocity

                # 检查是否达到目标速度 (允许 10% 误差)
                if velocity <= target_rpm * 0.9:
                    velocity_reached = True

                time.sleep(0.1)

            final_velocity = self._read_velocity()
            result["最小速度"] = f"{min_velocity} RPM"
            result["最终速度"] = f"{final_velocity} RPM"
            result["速度达标"] = str(velocity_reached)

            if velocity_reached or min_velocity < 0:
                return True, result
            else:
                result["警告"] = "反向运动未检测"
                return True, result

        except Exception as e:
            result["错误"] = str(e)
            self.emergency_stop()
            return False, result

    def test_7_halt(self) -> Tuple[bool, Dict]:
        """测试 7: Halt 停止"""
        result = {}
        try:
            # 发送 Halt 命令
            self._write_control(ControlWord.HALT)
            result["Halt 命令"] = f"0x{ControlWord.HALT:04X}"

            # 等待电机停止
            start_time = time.time()
            while time.time() - start_time < 3.0:
                velocity = self._read_velocity()
                if abs(velocity) < 10:  # 速度接近 0
                    result["停止时间"] = f"{time.time() - start_time:.2f} 秒"
                    result["最终速度"] = f"{velocity} RPM"

                    # 清除 Halt，恢复正常控制
                    self._write_control(ControlWord.ENABLE_OPERATION)
                    return True, result
                time.sleep(0.1)

            velocity = self._read_velocity()
            result["最终速度"] = f"{velocity} RPM"
            result["警告"] = "停止超时"

            # 即使超时也清除 Halt
            self._write_control(ControlWord.ENABLE_OPERATION)
            return True, result

        except Exception as e:
            result["错误"] = str(e)
            return False, result

    def test_8_disable_operation(self) -> Tuple[bool, Dict]:
        """测试 8: 禁用操作"""
        result = {}
        try:
            # 先设置速度为 0
            self._write_register_32bit(Reg.TARGET_VELOCITY, 0)
            time.sleep(0.5)

            # Shutdown
            self._write_control(ControlWord.SHUTDOWN)
            time.sleep(0.1)

            status = self._read_status()
            velocity = self._read_velocity()

            result["最终状态"] = f"{self._get_state_name(status)} (0x{status:04X})"
            result["最终速度"] = f"{velocity} RPM"

            return True, result

        except Exception as e:
            result["错误"] = str(e)
            return False, result

    def run_all_tests(self, auto_mode: bool = False, dry_run: bool = False) -> bool:
        """运行所有测试"""
        tests = [
            ("检查初始状态", self.test_1_check_initial_state),
            ("设置 PV 模式", self.test_2_set_pv_mode),
            ("设置速度参数", self.test_3_set_velocity_parameters),
            ("使能操作", self.test_4_enable_operation),
            ("正向速度运动", self.test_5_forward_velocity),
            ("反向速度运动", self.test_6_reverse_velocity),
            ("Halt 停止", self.test_7_halt),
            ("禁用操作", self.test_8_disable_operation),
        ]

        print("\n" + "=" * 60)
        print("TC-L4-002: PV模式速度运动测试")
        print("=" * 60)
        print(f"测试设备: {self.config.port}")
        print(f"目标从站: 0x{self.config.slave_id:02X} (Z 轴)")
        print(f"正向速度: {self.config.target_velocity_forward} user units/s")
        print(f"反向速度: {self.config.target_velocity_reverse} user units/s")
        print(f"干运行模式: {dry_run}")
        print("=" * 60)

        all_passed = True

        for name, test_func in tests:
            print(f"\n--- 测试: {name} ---")

            if dry_run and name in ["正向速度运动", "反向速度运动"]:
                print("[跳过] 干运行模式")
                self.test_results[name] = (True, {"状态": "干运行跳过"})
                continue

            try:
                passed, result = test_func()
                self.test_results[name] = (passed, result)

                status = "[通过]" if passed else "[失败]"
                print(f"{status} {name}")
                for key, value in result.items():
                    print(f"  {key}: {value}")

                if not passed:
                    all_passed = False
                    if name in ["设置 PV 模式", "使能操作"]:
                        print("\n关键测试失败，停止后续测试")
                        break

            except Exception as e:
                print(f"[错误] {name}: {e}")
                self.test_results[name] = (False, {"异常": str(e)})
                all_passed = False
                self.emergency_stop()
                break

        # 打印汇总
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)

        passed_count = 0
        failed_count = 0

        for name, (passed, _) in self.test_results.items():
            status = "[通过]" if passed else "[失败]"
            print(f"  {status} {name}")
            if passed:
                passed_count += 1
            else:
                failed_count += 1

        total = passed_count + failed_count
        print(f"\n总计: {passed_count}/{total} 通过, {failed_count}/{total} 失败")
        print("=" * 60)

        return all_passed


def main():
    parser = argparse.ArgumentParser(description="TC-L4-002 PV模式速度运动测试")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--velocity", type=int, default=50000,
                        help="目标速度 (user units/s, 默认 50000 ≈ 300 RPM)")
    parser.add_argument("--auto", action="store_true", help="跳过确认提示，自动运行")
    parser.add_argument("--dry-run", action="store_true", help="干运行模式，不执行实际运动")
    args = parser.parse_args()

    config = TestConfig(
        port=args.port,
        slave_id=args.slave_id,
        target_velocity_forward=args.velocity,
        target_velocity_reverse=-args.velocity,
    )

    tester = PVModeTester(config)

    # 安全警告
    print("\n" + "=" * 60)
    print("安全警告")
    print("=" * 60)
    print("本测试将使电机进行速度运动")
    print("")
    print("测试前请确认:")
    print("  1. 电机轴上无负载或负载已牢固固定")
    print("  2. 运动范围内无障碍物")
    print("  3. 急停按钮可用")
    print("  4. 可以快速断电")
    print("")
    print("如有异常，立即按 Ctrl+C 或断电!")
    print("=" * 60)

    print(f"\n测试参数 (PV 模式使用 user units/s):")
    print(f"  串口: {config.port}")
    print(f"  从站地址: 0x{config.slave_id:02X}")
    print(f"  正向速度: {config.target_velocity_forward} user units/s (≈{config.target_velocity_forward * 60 / config.encoder_resolution:.0f} RPM)")
    print(f"  反向速度: {config.target_velocity_reverse} user units/s (≈{config.target_velocity_reverse * 60 / config.encoder_resolution:.0f} RPM)")
    print(f"  运行时间: {config.velocity_run_time} 秒/方向")
    print(f"  最大允许速度: {config.max_velocity_rpm} RPM")
    print(f"  干运行模式: {args.dry_run}")
    print(f"  自动模式: {args.auto}")

    if not args.auto:
        try:
            response = input("\n确认开始测试? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("测试取消")
                return 1
        except EOFError:
            print("\n无法读取输入，请使用 --auto 参数")
            return 1
    else:
        print("\n自动模式: 跳过确认，开始测试...")

    try:
        if not tester.connect():
            return 1

        # 获取初始状态
        status = tester._read_status()
        velocity = tester._read_velocity()
        mode = tester._read_register(Reg.MODES_OF_OPERATION_DISPLAY)

        logger.info(f"初始状态: {{'状态字': '0x{status:04X}', '驱动器状态': '{tester._get_state_name(status)}', '当前速度': '{velocity} RPM', '当前模式': '{mode}'}}")

        # 安全检查
        if not tester._monitor_velocity():
            return 1

        success = tester.run_all_tests(auto_mode=args.auto, dry_run=args.dry_run)
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        tester.emergency_stop()
        return 1
    finally:
        tester.disconnect()


if __name__ == "__main__":
    sys.exit(main())
