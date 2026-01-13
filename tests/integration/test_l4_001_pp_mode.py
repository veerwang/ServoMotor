#!/usr/bin/env python3
"""
TC-L4-001: PP模式位置运动测试

测试目标: 验证 Profile Position (PP) 模式下的位置运动功能

基于上次测试报告 (2026-01-09) 的结果:
- 上次测试使用了错误的寄存器地址 (已修正)
- 上次测试结果: 4/7 通过
- 问题: 位置反馈始终为 0，电机飞转

本次修正:
- 使用正确的 Modbus 地址 (根据 NiMotion 手册验证)
- 增加安全保护措施

用法:
=====
python3 test_l4_001_pp_mode.py [选项]

选项:
  --auto        跳过确认提示，自动运行
  --dry-run     干运行模式，不执行实际运动

安全警告:
=========
1. 确认电机轴上无负载或负载已固定
2. 确认运动范围内无障碍物
3. 确认急停按钮可用
4. 测试过程中全程观察电机状态
5. 如有异常立即 Ctrl+C 或断电
"""

import sys
import time
import logging
import argparse
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum

# 添加项目路径
sys.path.insert(0, "/home/hds/codes/ServoMotorCreate/CreateServoMotor")

from servo_service.modbus_rtu.client import ModbusClient
from servo_service.serial_comm import SerialPort

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# 测试配置 - 根据上次测试报告调整
# ============================================================
@dataclass
class TestConfig:
    """
    测试配置

    PP 模式单位说明:
    ================
    - 位置: user units (编码器脉冲)
    - 速度: user units/s (不是 RPM!)
    - 加速度: user units/s²

    单位换算 (假设编码器 10000 脉冲/圈):
    - 速度: user units/s = RPM × 10000 / 60
    - 例如: 100 RPM ≈ 16667 user units/s
    - 例如: 500 RPM ≈ 83333 user units/s
    """

    # 串口配置 (与上次测试报告一致)
    port: str = "/dev/ttyUSB0"
    baudrate: int = 115200
    slave_id: int = 0x03  # Z 轴地址 (上次测试报告使用的地址)

    # 运动参数 - PP 模式使用 user units
    target_position: int = 10000     # 目标位置 (user units, 10000 = 1圈)
    profile_velocity: int = 50000    # 轮廓速度 (user units/s, ≈300 RPM)
    profile_acceleration: int = 100000  # 轮廓加速度 (user units/s²)
    profile_deceleration: int = 100000  # 轮廓减速度 (user units/s²)

    # 安全限制
    max_velocity_rpm: int = 1000     # 最大允许速度 (rpm, 用于安全监控)
    max_position: int = 100000       # 最大允许位置 (user units)
    motion_timeout: float = 10.0     # 运动超时 (秒)

    # 测试选项
    require_confirmation: bool = True  # 需要用户确认
    dry_run: bool = False              # 干运行模式


# ============================================================
# 寄存器地址定义 - 已修正 (根据 NiMotion 手册)
# ============================================================
class Reg:
    """
    寄存器地址 - 已通过 NiMotion 手册验证

    对比上次测试报告中使用的错误地址:
    | 寄存器     | 错误地址 | 正确地址 |
    |------------|----------|----------|
    | 实际位置   | 0x03A7   | 0x03C8   |
    | 目标位置   | 0x03BD   | 0x03E7   |
    | 轮廓速度   | 0x03C4   | 0x03F8   |
    | 实际速度   | 0x03AF   | 0x03D5   |
    | 实际转矩   | 0x03BA   | 0x03E3   |
    """

    # 控制寄存器
    CONTROL_WORD = 0x0380           # 控制字
    STATUS_WORD = 0x0381            # 状态字
    ERROR_CODE = 0x0382             # 错误码
    MODES_OF_OPERATION = 0x03C2     # 操作模式设置
    MODES_OF_OPERATION_DISPLAY = 0x03C3  # 操作模式显示

    # 位置寄存器 (已修正)
    TARGET_POSITION = 0x03E7        # 目标位置 (32位) - 旧: 0x03BD
    POSITION_ACTUAL = 0x03C8        # 实际位置 (32位) - 旧: 0x03A7
    FOLLOWING_ERROR = 0x0440        # 跟随误差 (32位)

    # 速度寄存器 (已修正)
    PROFILE_VELOCITY = 0x03F8       # 轮廓速度 (32位) - 旧: 0x03C4
    VELOCITY_ACTUAL = 0x03D5        # 实际速度 (32位) - 旧: 0x03AF

    # 加减速寄存器 (已修正)
    PROFILE_ACCELERATION = 0x03FC   # 轮廓加速度 (32位)
    PROFILE_DECELERATION = 0x03FE   # 轮廓减速度 (32位)
    QUICK_STOP_DECEL = 0x0400       # 快速停止减速度 (32位)

    # 转矩寄存器 (已修正)
    TORQUE_ACTUAL = 0x03E3          # 实际转矩 - 旧: 0x03BA

    # 编码器参数
    ENCODER_INCREMENT = 0x0408      # 编码器增量 (608Fh:01)
    MOTOR_REVOLUTIONS = 0x040A      # 电机圈数 (608Fh:02)


class ControlWord:
    """控制字命令"""
    SHUTDOWN = 0x0006               # 关机
    SWITCH_ON = 0x0007              # 开机
    ENABLE_OPERATION = 0x000F       # 使能操作
    DISABLE_VOLTAGE = 0x0000        # 禁用电压
    QUICK_STOP = 0x0002             # 快速停止
    FAULT_RESET = 0x0080            # 故障复位

    # PP 模式启动运动
    START_ABSOLUTE = 0x001F         # 启动绝对位置运动
    START_RELATIVE = 0x005F         # 启动相对位置运动


class StatusMask:
    """状态字掩码"""
    STATE_MASK = 0x006F
    READY_TO_SWITCH_ON = 0x0021
    SWITCHED_ON = 0x0023
    OPERATION_ENABLED = 0x0027
    SWITCH_ON_DISABLED = 0x0040
    FAULT = 0x0008
    TARGET_REACHED = 0x0400
    SET_POINT_ACK = 0x1000
    FOLLOWING_ERROR = 0x2000


# ============================================================
# 测试类
# ============================================================
class PPModeTest:
    """PP 模式位置运动测试 (对应测试报告 TC-L4-001)"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.client: Optional[ModbusClient] = None
        self.initial_position: int = 0
        self.test_results = []

    def connect(self) -> bool:
        """连接到电机驱动器"""
        try:
            logger.info(f"连接到 {self.config.port} @ {self.config.baudrate}")
            logger.info(f"目标从站: 0x{self.config.slave_id:02X}")

            serial_port = SerialPort(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=0.5
            )
            serial_port.open()

            self.client = ModbusClient(
                serial_port=serial_port,
                timeout=0.5,
                retries=3
            )

            # 测试通信
            status = self._read_status()
            logger.info(f"通信成功, 状态字: 0x{status:04X}")
            return True

        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.client:
            try:
                self._write_control(ControlWord.DISABLE_VOLTAGE)
            except:
                pass
            self.client.disconnect()
            logger.info("已断开连接")

    # ============================================================
    # 寄存器读写方法
    # ============================================================

    def _read_register(self, address: int) -> int:
        """读取 16 位寄存器"""
        if not self.client:
            raise RuntimeError("未连接")
        return self.client.read_register(self.config.slave_id, address)

    def _write_register(self, address: int, value: int):
        """写入 16 位寄存器"""
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

    def _read_position(self) -> int:
        return self._read_register_32bit(Reg.POSITION_ACTUAL)

    def _read_velocity(self) -> int:
        return self._read_register_32bit(Reg.VELOCITY_ACTUAL)

    def _get_state_name(self, status: int) -> str:
        """获取状态名称"""
        if status & StatusMask.FAULT:
            return "Fault"
        state = status & StatusMask.STATE_MASK
        states = {
            0x0000: "Not ready to switch on",
            0x0040: "Switch on disabled",
            0x0021: "Ready to switch on",
            0x0023: "Switched on",
            0x0027: "Operation enabled",
            0x0007: "Quick stop active",
        }
        return states.get(state, f"Unknown(0x{state:04X})")

    def confirm(self, message: str) -> bool:
        """请求用户确认"""
        if not self.config.require_confirmation:
            return True
        print(f"\n[确认] {message}")
        response = input("继续? (y/n): ").strip().lower()
        return response == 'y'

    def emergency_stop(self):
        """急停"""
        logger.warning("执行急停!")
        try:
            self._write_control(ControlWord.QUICK_STOP)
            time.sleep(0.1)
            self._write_control(ControlWord.DISABLE_VOLTAGE)
        except Exception as e:
            logger.error(f"急停失败: {e}")

    # ============================================================
    # 安全监控
    # ============================================================

    def _check_velocity_safety(self) -> bool:
        """检查速度是否安全 (实际速度寄存器 606Ch 返回 rpm)"""
        try:
            velocity = abs(self._read_velocity())
            if velocity > self.config.max_velocity_rpm:
                logger.error(f"速度异常! {velocity} rpm > {self.config.max_velocity_rpm} rpm")
                self.emergency_stop()
                return False
            return True
        except:
            return True

    # ============================================================
    # 测试步骤 (对应测试报告中的 7 个测试)
    # ============================================================

    def test_01_check_initial_state(self) -> Tuple[bool, dict]:
        """测试 1: 检查初始状态"""
        result = {}
        try:
            status = self._read_status()
            position = self._read_position()
            mode = self._read_register(Reg.MODES_OF_OPERATION_DISPLAY)

            result = {
                "状态字": f"0x{status:04X}",
                "驱动器状态": self._get_state_name(status),
                "当前位置": f"{position} 脉冲",
                "当前模式": f"{mode} ({'PP' if mode == 1 else 'Other'})",
            }

            self.initial_position = position
            logger.info(f"初始状态: {result}")

            return True, result

        except Exception as e:
            return False, {"错误": str(e)}

    def test_02_set_pp_mode(self) -> Tuple[bool, dict]:
        """测试 2: 设置 PP 模式"""
        result = {}
        try:
            # 写入 PP 模式 (1)
            self._write_register(Reg.MODES_OF_OPERATION, 1)
            time.sleep(0.1)

            # 读回验证
            mode = self._read_register(Reg.MODES_OF_OPERATION_DISPLAY)

            result = {
                "写入值": "1 (PP 模式)",
                "读回值": f"{mode} ({'PP 模式' if mode == 1 else '其他'})",
            }

            success = (mode == 1)
            return success, result

        except Exception as e:
            return False, {"错误": str(e)}

    def test_03_set_motion_parameters(self) -> Tuple[bool, dict]:
        """测试 3: 设置运动参数"""
        result = {}
        errors = []

        try:
            # 设置轮廓速度
            try:
                self._write_register_32bit(Reg.PROFILE_VELOCITY, self.config.profile_velocity)
                vel_read = self._read_register_32bit(Reg.PROFILE_VELOCITY, signed=False)
                result["轮廓速度"] = f"写入 {self.config.profile_velocity}, 读回 {vel_read}"
            except Exception as e:
                errors.append(f"轮廓速度写入失败: {e}")
                result["轮廓速度"] = f"失败: {e}"

            # 设置加速度
            try:
                self._write_register_32bit(Reg.PROFILE_ACCELERATION, self.config.profile_acceleration)
                acc_read = self._read_register_32bit(Reg.PROFILE_ACCELERATION, signed=False)
                result["轮廓加速度"] = f"写入 {self.config.profile_acceleration}, 读回 {acc_read}"
            except Exception as e:
                errors.append(f"加速度写入失败: {e}")
                result["轮廓加速度"] = f"失败: {e}"

            # 设置减速度
            try:
                self._write_register_32bit(Reg.PROFILE_DECELERATION, self.config.profile_deceleration)
                dec_read = self._read_register_32bit(Reg.PROFILE_DECELERATION, signed=False)
                result["轮廓减速度"] = f"写入 {self.config.profile_deceleration}, 读回 {dec_read}"
            except Exception as e:
                errors.append(f"减速度写入失败: {e}")
                result["轮廓减速度"] = f"失败: {e}"

            success = len(errors) == 0
            return success, result

        except Exception as e:
            return False, {"错误": str(e)}

    def test_04_enable_operation(self) -> Tuple[bool, dict]:
        """测试 4: 使能操作"""
        result = {}
        try:
            # Step 1: Shutdown
            self._write_control(ControlWord.SHUTDOWN)
            time.sleep(0.1)
            status = self._read_status()
            result["Shutdown 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            # Step 2: Switch On
            self._write_control(ControlWord.SWITCH_ON)
            time.sleep(0.1)
            status = self._read_status()
            result["Switch On 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            # Step 3: Enable Operation
            self._write_control(ControlWord.ENABLE_OPERATION)
            time.sleep(0.1)
            status = self._read_status()
            result["Enable 后"] = f"{self._get_state_name(status)} (0x{status:04X})"

            # 检查是否使能成功
            state = status & StatusMask.STATE_MASK
            success = (state == StatusMask.OPERATION_ENABLED)

            return success, result

        except Exception as e:
            return False, {"错误": str(e)}

    def test_05_execute_position_motion(self) -> Tuple[bool, dict]:
        """测试 5: 执行位置运动"""
        result = {}

        if self.config.dry_run:
            return True, {"说明": "干运行模式 - 跳过实际运动"}

        try:
            # 记录起始位置
            start_pos = self._read_position()
            target_pos = start_pos + self.config.target_position

            result["起始位置"] = f"{start_pos} 脉冲"
            result["目标位置"] = f"{target_pos} 脉冲"

            # 设置目标位置
            self._write_register_32bit(Reg.TARGET_POSITION, target_pos)

            # 触发运动 (使用绝对位置)
            self._write_control(ControlWord.ENABLE_OPERATION)
            time.sleep(0.05)
            self._write_control(ControlWord.START_ABSOLUTE)

            result["触发控制字"] = f"0x{ControlWord.START_ABSOLUTE:04X}"

            # 检查 SET_POINT_ACK
            time.sleep(0.1)
            status = self._read_status()
            set_point_ack = bool(status & StatusMask.SET_POINT_ACK)
            result["SET_POINT_ACK"] = str(set_point_ack)

            # 等待运动完成
            start_time = time.time()
            motion_detected = False

            while time.time() - start_time < self.config.motion_timeout:
                status = self._read_status()
                position = self._read_position()
                velocity = self._read_velocity()

                # 安全检查: 速度是否异常 (实际速度寄存器返回 rpm)
                if abs(velocity) > self.config.max_velocity_rpm:
                    self.emergency_stop()
                    result["错误"] = f"速度异常: {velocity} rpm > {self.config.max_velocity_rpm} rpm"
                    return False, result

                # 检测到运动
                if abs(position - start_pos) > 10 or abs(velocity) > 10:
                    motion_detected = True

                # 检查目标到达
                if status & StatusMask.TARGET_REACHED:
                    final_pos = self._read_position()
                    result["TARGET_REACHED"] = "True"
                    result["最终位置"] = f"{final_pos} 脉冲"
                    result["位置误差"] = f"{final_pos - target_pos} 脉冲"
                    result["运动检测"] = str(motion_detected)
                    return True, result

                # 检查故障
                if status & StatusMask.FAULT:
                    error_code = self._read_register(Reg.ERROR_CODE)
                    result["错误"] = f"故障 0x{error_code:04X}"
                    self.emergency_stop()
                    return False, result

                time.sleep(0.1)

            # 超时
            final_pos = self._read_position()
            result["TARGET_REACHED"] = "False (超时)"
            result["最终位置"] = f"{final_pos} 脉冲"
            result["运动检测"] = str(motion_detected)

            self.emergency_stop()
            return False, result

        except Exception as e:
            self.emergency_stop()
            return False, {"错误": str(e)}

    def test_06_return_to_origin(self) -> Tuple[bool, dict]:
        """测试 6: 返回原位"""
        result = {}

        if self.config.dry_run:
            return True, {"说明": "干运行模式 - 跳过"}

        try:
            # 设置目标为初始位置
            self._write_register_32bit(Reg.TARGET_POSITION, self.initial_position)

            # 重新触发运动
            self._write_control(ControlWord.ENABLE_OPERATION)
            time.sleep(0.05)
            self._write_control(ControlWord.START_ABSOLUTE)

            # 等待完成
            start_time = time.time()
            while time.time() - start_time < self.config.motion_timeout:
                status = self._read_status()
                position = self._read_position()

                if status & StatusMask.TARGET_REACHED:
                    result["最终位置"] = f"{position} 脉冲"
                    result["初始位置"] = f"{self.initial_position} 脉冲"
                    return True, result

                if status & StatusMask.FAULT:
                    break

                time.sleep(0.1)

            position = self._read_position()
            result["最终位置"] = f"{position} 脉冲"
            result["状态"] = "超时或故障"
            return False, result

        except Exception as e:
            return False, {"错误": str(e)}

    def test_07_disable_operation(self) -> Tuple[bool, dict]:
        """测试 7: 禁用操作"""
        result = {}
        try:
            self._write_control(ControlWord.DISABLE_VOLTAGE)
            time.sleep(0.1)

            status = self._read_status()
            result["最终状态"] = f"{self._get_state_name(status)} (0x{status:04X})"

            return True, result

        except Exception as e:
            return False, {"错误": str(e)}

    # ============================================================
    # 运行所有测试
    # ============================================================

    def run_all_tests(self):
        """运行所有测试"""
        tests = [
            ("检查初始状态", self.test_01_check_initial_state),
            ("设置 PP 模式", self.test_02_set_pp_mode),
            ("设置运动参数", self.test_03_set_motion_parameters),
            ("使能操作", self.test_04_enable_operation),
            ("执行位置运动", self.test_05_execute_position_motion),
            ("返回原位", self.test_06_return_to_origin),
            ("禁用操作", self.test_07_disable_operation),
        ]

        print("\n" + "=" * 60)
        print("TC-L4-001: PP模式位置运动测试")
        print("=" * 60)
        print(f"测试设备: {self.config.port}")
        print(f"目标从站: 0x{self.config.slave_id:02X} (Z 轴)")
        print(f"目标位置: +{self.config.target_position} user units")
        print(f"轮廓速度: {self.config.profile_velocity} user units/s")
        print(f"干运行模式: {self.config.dry_run}")
        print("=" * 60)

        if not self.confirm("开始测试?"):
            print("测试已取消")
            return

        self.test_results = []
        passed = 0
        failed = 0

        for i, (name, test_func) in enumerate(tests, 1):
            print(f"\n--- 测试 {i}: {name} ---")

            # 关键测试需要确认
            if name in ["使能操作", "执行位置运动"] and not self.config.dry_run:
                if not self.confirm(f"即将执行: {name}"):
                    self.test_results.append((name, False, {"说明": "用户跳过"}))
                    failed += 1
                    continue

            try:
                success, result = test_func()
                self.test_results.append((name, success, result))

                status = "通过" if success else "失败"
                print(f"[{status}] {name}")
                for key, value in result.items():
                    print(f"  {key}: {value}")

                if success:
                    passed += 1
                else:
                    failed += 1

                # 关键测试失败则停止
                if not success and name in ["使能操作", "执行位置运动"]:
                    print("\n关键测试失败，停止后续测试")
                    break

            except Exception as e:
                self.test_results.append((name, False, {"错误": str(e)}))
                print(f"[错误] {name}: {e}")
                failed += 1
                break

        # 汇总
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)

        for name, success, result in self.test_results:
            status = "通过" if success else "失败"
            print(f"  [{status}] {name}")

        total = passed + failed
        print(f"\n总计: {passed}/{total} 通过, {failed}/{total} 失败")
        print("=" * 60)


# ============================================================
# 主程序
# ============================================================
def main():
    """主程序"""

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="TC-L4-001: PP模式位置运动测试")
    parser.add_argument("--auto", action="store_true", help="跳过确认提示，自动运行")
    parser.add_argument("--dry-run", action="store_true", help="干运行模式，不执行实际运动")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址 (默认: 3)")
    args = parser.parse_args()

    # 编码器分辨率 (用于显示换算)
    encoder_resolution = 10000  # 脉冲/圈

    config = TestConfig(
        port=args.port,
        baudrate=115200,
        slave_id=args.slave_id,

        # 运动参数 - PP 模式使用 user units
        target_position=10000,       # 10000 user units = 1 圈
        profile_velocity=50000,      # 50000 user units/s ≈ 300 RPM
        profile_acceleration=100000, # user units/s²
        profile_deceleration=100000, # user units/s²

        # 安全限制
        max_velocity_rpm=1000,       # 最大速度 (rpm)
        max_position=100000,         # 最大位置 (user units)
        motion_timeout=10.0,

        # 选项 - 根据命令行参数设置
        require_confirmation=not args.auto,
        dry_run=args.dry_run,
    )

    # 计算换算值
    velocity_rpm = config.profile_velocity * 60 / encoder_resolution
    position_rev = config.target_position / encoder_resolution

    # 安全警告
    print("""
╔══════════════════════════════════════════════════════════════╗
║                      安 全 警 告                              ║
╠══════════════════════════════════════════════════════════════╣
║  本测试将使电机进行位置运动                                   ║
║                                                              ║
║  测试前请确认:                                                ║
║  1. 电机轴上无负载或负载已牢固固定                            ║
║  2. 运动范围内无障碍物                                        ║
║  3. 急停按钮可用                                              ║
║  4. 可以快速断电                                              ║
║                                                              ║
║  如有异常，立即按 Ctrl+C 或断电!                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    print("测试参数 (PP 模式使用 user units):")
    print(f"  串口: {config.port}")
    print(f"  从站地址: 0x{config.slave_id:02X}")
    print(f"  目标位置: {config.target_position} user units ({position_rev:.2f} 圈)")
    print(f"  轮廓速度: {config.profile_velocity} user units/s (≈{velocity_rpm:.0f} RPM)")
    print(f"  轮廓加速度: {config.profile_acceleration} user units/s²")
    print(f"  轮廓减速度: {config.profile_deceleration} user units/s²")
    print(f"  最大允许速度: {config.max_velocity_rpm} RPM")
    print(f"  干运行模式: {config.dry_run}")
    print(f"  自动模式: {args.auto}")
    print()

    if not args.auto:
        response = input("确认参数并开始测试? (y/n): ").strip().lower()
        if response != 'y':
            print("已取消")
            return
    else:
        print("自动模式: 跳过确认，开始测试...")

    test = PPModeTest(config)

    try:
        if not test.connect():
            print("连接失败")
            return

        test.run_all_tests()

    except KeyboardInterrupt:
        print("\n\n用户中断!")
        test.emergency_stop()

    finally:
        test.disconnect()


if __name__ == "__main__":
    main()
