#!/usr/bin/env python3
"""
编码器分辨率验证脚本

目的: 验证编码器分辨率设置是否正确
测试: 命令移动 10mm，实际测量移动距离

Z 轴参数:
- 丝杠导程: 10mm/rev
- 编码器分辨率: 10000 脉冲/rev
- 理论上: 10mm = 10000 脉冲 = 1 转
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
    CONTROL_WORD = 0x0380
    STATUS_WORD = 0x0381
    OP_MODE = 0x03C2
    OP_MODE_DISPLAY = 0x03C3

    # 位置
    POSITION_ACTUAL = 0x03C8
    TARGET_POSITION = 0x03E7

    # 速度
    PROFILE_VELOCITY = 0x03F8
    PROFILE_ACCEL = 0x03FC
    PROFILE_DECEL = 0x03FE

    # 编码器/齿轮比
    ENCODER_INCREMENT = 0x0408  # 608Fh:01h
    MOTOR_REVOLUTIONS = 0x040A  # 608Fh:02h
    GEAR_RATIO_NUM = 0x040C     # 6091h:01h (应该是 040Eh)
    GEAR_RATIO_DEN = 0x040E     # 6091h:02h (应该是 0410h)

    # DI/限位状态
    DI_MONITOR = 0x01E2
    DIGITAL_INPUTS = 0x0447     # 60FDh

    # DI 配置
    DI1_FUNCTION = 0x00D5
    DI2_FUNCTION = 0x00D7
    DI3_FUNCTION = 0x00D9

    # 告警
    ERROR_CODE = 0x037F


class EncoderVerifier:
    """编码器分辨率验证器"""

    def __init__(self, port: str, slave_id: int):
        self.port = port
        self.slave_id = slave_id
        self.client = None
        self.serial = None

    def connect(self) -> bool:
        """连接"""
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
        """断开"""
        if self.serial:
            self.serial.close()

    def read_reg(self, addr: int) -> int:
        """读取 16 位寄存器"""
        return self.client.read_holding_registers(self.slave_id, addr, 1)[0]

    def read_reg32(self, addr: int) -> int:
        """读取 32 位寄存器 (大端序: 高字在前)"""
        values = self.client.read_holding_registers(self.slave_id, addr, 2)
        # 大端序: values[0] = 高字, values[1] = 低字
        value = ((values[0] & 0xFFFF) << 16) | (values[1] & 0xFFFF)
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    def write_reg(self, addr: int, value: int):
        """写入 16 位寄存器"""
        self.client.write_single_register(self.slave_id, addr, value & 0xFFFF)

    def write_reg32(self, addr: int, value: int):
        """写入 32 位寄存器 (大端序)"""
        if value < 0:
            value += 0x100000000
        high = (value >> 16) & 0xFFFF
        low = value & 0xFFFF
        self.client.write_multiple_registers(self.slave_id, addr, [high, low])

    def check_status(self) -> dict:
        """检查状态"""
        status = self.read_reg(Reg.STATUS_WORD)
        di_phys = self.read_reg(Reg.DI_MONITOR)
        di_logic = self.read_reg32(Reg.DIGITAL_INPUTS)

        result = {
            "status_word": status,
            "di_physical": di_phys,
            "di_logical": di_logic,
            "ready": (status & 0x0001) != 0,
            "switched_on": (status & 0x0002) != 0,
            "op_enabled": (status & 0x0004) != 0,
            "fault": (status & 0x0008) != 0,
            "quick_stop": (status & 0x0020) == 0,  # 0 = quick stop active
            "warning": (status & 0x0080) != 0,
            "neg_limit": (di_logic & 0x0001) != 0,
            "pos_limit": (di_logic & 0x0002) != 0,
        }
        return result

    def print_status(self):
        """打印状态"""
        s = self.check_status()
        print(f"\n状态字: 0x{s['status_word']:04X}")
        print(f"  Ready: {s['ready']}, Switched On: {s['switched_on']}, Op Enabled: {s['op_enabled']}")
        print(f"  Fault: {s['fault']}, Warning: {s['warning']}, Quick Stop: {s['quick_stop']}")
        print(f"DI 物理状态: 0x{s['di_physical']:04X}")
        print(f"60FDh 逻辑状态: 0x{s['di_logical']:08X}")
        print(f"  负限位(Bit0): {s['neg_limit']}, 正限位(Bit1): {s['pos_limit']}")

        if s['neg_limit'] or s['pos_limit']:
            print("\n*** 警告: 60FDh 显示限位触发! ***")
            print("如果实际未在限位位置，请尝试:")
            print("  1. 断电重启驱动器")
            print("  2. 检查 DI 功能配置")
        return s

    def read_encoder_settings(self):
        """读取编码器设置"""
        print("\n" + "=" * 50)
        print("编码器/齿轮比设置")
        print("=" * 50)

        enc_inc = self.read_reg32(Reg.ENCODER_INCREMENT)
        motor_rev = self.read_reg32(Reg.MOTOR_REVOLUTIONS)

        # 注意: 根据 CLAUDE.md, 齿轮比寄存器地址可能不同
        # 6091h:01h = 040Eh, 6091h:02h = 0410h
        try:
            gear_num = self.read_reg32(0x040E)  # 尝试正确地址
            gear_den = self.read_reg32(0x0410)
        except:
            gear_num = 1
            gear_den = 1

        print(f"编码器分辨率 (608Fh):")
        print(f"  Increment (01h): {enc_inc}")
        print(f"  Motor Rev (02h): {motor_rev}")
        print(f"  分辨率 = {enc_inc}/{motor_rev} = {enc_inc/motor_rev if motor_rev else 'N/A'} 脉冲/转")

        print(f"\n齿轮比 (6091h):")
        print(f"  Numerator (01h): {gear_num}")
        print(f"  Denominator (02h): {gear_den}")
        print(f"  齿轮比 = {gear_num}/{gear_den} = {gear_num/gear_den if gear_den else 'N/A'}")

        print(f"\nZ 轴丝杠导程: 10mm/rev")
        print(f"理论计算:")
        print(f"  1mm = {enc_inc/motor_rev/10 if motor_rev else 'N/A':.1f} 脉冲")
        print(f"  10mm = {enc_inc/motor_rev if motor_rev else 'N/A':.1f} 脉冲")

        return enc_inc, motor_rev, gear_num, gear_den

    def disable_limit_functions(self):
        """禁用限位功能"""
        print("\n禁用 DI 限位功能...")
        # 设置 DI2, DI3 功能为 0 (无功能)
        self.write_reg(Reg.DI2_FUNCTION, 0)
        self.write_reg(Reg.DI3_FUNCTION, 0)
        time.sleep(0.1)

        # 验证
        di2_func = self.read_reg(Reg.DI2_FUNCTION)
        di3_func = self.read_reg(Reg.DI3_FUNCTION)
        print(f"  DI2 功能: {di2_func}")
        print(f"  DI3 功能: {di3_func}")

    def fault_reset(self):
        """故障复位"""
        print("\n执行故障复位...")
        self.write_reg(Reg.CONTROL_WORD, 0x0080)
        time.sleep(0.1)
        self.write_reg(Reg.CONTROL_WORD, 0x0000)
        time.sleep(0.1)

    def enable_motor(self) -> bool:
        """使能电机"""
        print("\n使能电机...")

        # 状态机转换
        steps = [
            (0x0006, "Shutdown"),
            (0x0007, "Switch On"),
            (0x000F, "Enable Operation"),
        ]

        for cmd, name in steps:
            self.write_reg(Reg.CONTROL_WORD, cmd)
            time.sleep(0.1)
            status = self.read_reg(Reg.STATUS_WORD)
            print(f"  {name}: 0x{status:04X}")

            # 检查是否进入警告状态
            if status & 0x0080:  # Warning bit
                print(f"  *** 警告位置位! ***")
                return False

        # 最终检查
        status = self.read_reg(Reg.STATUS_WORD)
        if (status & 0x0007) == 0x0007:  # Operation enabled
            print("  电机已使能")
            return True
        else:
            print(f"  使能失败, 状态: 0x{status:04X}")
            return False

    def disable_motor(self):
        """禁用电机"""
        self.write_reg(Reg.CONTROL_WORD, 0x0006)
        time.sleep(0.1)

    def move_relative(self, distance_mm: float, velocity_mm_s: float = 10.0) -> bool:
        """
        相对移动

        Args:
            distance_mm: 移动距离 (mm)
            velocity_mm_s: 速度 (mm/s)
        """
        # 计算脉冲数 (假设 1000 脉冲/mm)
        pulses_per_mm = 1000  # 10000 pulses/rev, 10mm/rev
        pulses = int(distance_mm * pulses_per_mm)
        velocity = int(velocity_mm_s * pulses_per_mm)

        print(f"\n移动 {distance_mm}mm ({pulses} 脉冲)")
        print(f"速度: {velocity_mm_s}mm/s ({velocity} 脉冲/s)")

        # 读取当前位置
        start_pos = self.read_reg32(Reg.POSITION_ACTUAL)
        target_pos = start_pos + pulses
        print(f"起始位置: {start_pos}")
        print(f"目标位置: {target_pos}")

        # 设置 PP 模式
        self.write_reg(Reg.OP_MODE, 1)  # PP mode
        time.sleep(0.1)

        mode = self.read_reg(Reg.OP_MODE_DISPLAY)
        print(f"当前模式: {mode}")

        # 设置运动参数
        self.write_reg32(Reg.PROFILE_VELOCITY, velocity)
        self.write_reg32(Reg.PROFILE_ACCEL, velocity * 2)  # 加速度
        self.write_reg32(Reg.PROFILE_DECEL, velocity * 2)  # 减速度

        # 设置目标位置
        self.write_reg32(Reg.TARGET_POSITION, target_pos)

        # 使能
        if not self.enable_motor():
            print("使能失败!")
            return False

        # 检查状态
        status = self.check_status()
        if status['warning'] or status['neg_limit'] or status['pos_limit']:
            print("状态异常，无法移动!")
            self.print_status()
            return False

        # 触发新位置命令 (Bit 4 rising edge)
        print("\n触发移动...")
        self.write_reg(Reg.CONTROL_WORD, 0x000F)  # Clear new setpoint
        time.sleep(0.05)
        self.write_reg(Reg.CONTROL_WORD, 0x001F)  # Set new setpoint (absolute)

        # 监控移动
        print("\n监控移动中...")
        start_time = time.time()
        last_pos = start_pos

        while time.time() - start_time < 10:  # 10秒超时
            try:
                pos = self.read_reg32(Reg.POSITION_ACTUAL)
                status = self.read_reg(Reg.STATUS_WORD)
                delta = pos - last_pos

                moved = pos - start_pos
                moved_mm = moved / pulses_per_mm

                print(f"  位置: {pos:10d} | 移动: {moved:+8d} ({moved_mm:+.3f}mm) | 状态: 0x{status:04X}")

                # 检查目标到达
                if status & 0x0400:  # Target reached
                    print("\n目标到达!")
                    break

                # 检查警告
                if status & 0x0080:
                    print("\n警告!")
                    break

                last_pos = pos
                time.sleep(0.2)

            except Exception as e:
                print(f"读取错误: {e}")
                time.sleep(0.1)

        # 最终结果
        end_pos = self.read_reg32(Reg.POSITION_ACTUAL)
        total_moved = end_pos - start_pos
        total_mm = total_moved / pulses_per_mm

        print("\n" + "=" * 50)
        print("移动结果")
        print("=" * 50)
        print(f"起始位置: {start_pos}")
        print(f"结束位置: {end_pos}")
        print(f"移动脉冲: {total_moved}")
        print(f"移动距离: {total_mm:.3f} mm")
        print(f"预期距离: {distance_mm:.3f} mm")

        error = abs(total_mm - distance_mm)
        error_pct = (error / abs(distance_mm)) * 100 if distance_mm else 0
        print(f"误差: {error:.3f} mm ({error_pct:.1f}%)")

        if error_pct > 10:
            print("\n*** 误差过大! 请检查编码器分辨率或齿轮比设置 ***")

        return True

    def run_test(self, distance_mm: float = 10.0):
        """运行测试"""
        print("\n" + "=" * 60)
        print("编码器分辨率验证测试")
        print("=" * 60)
        print(f"测试距离: {distance_mm} mm")
        print("=" * 60)

        if not self.connect():
            return

        try:
            # 1. 读取设置
            self.read_encoder_settings()

            # 2. 检查状态
            print("\n" + "-" * 50)
            print("检查初始状态")
            print("-" * 50)
            status = self.print_status()

            # 3. 如果有限位问题，尝试禁用
            if status['neg_limit'] or status['pos_limit']:
                print("\n检测到限位状态，尝试禁用限位功能...")
                self.disable_limit_functions()
                self.fault_reset()
                time.sleep(0.5)

                print("\n重新检查状态...")
                status = self.print_status()

                if status['neg_limit'] or status['pos_limit']:
                    print("\n" + "!" * 50)
                    print("限位状态仍然存在!")
                    print("请断电重启驱动器后再次运行此脚本。")
                    print("!" * 50)
                    return

            # 4. 执行移动测试
            print("\n" + "-" * 50)
            print(f"执行 {distance_mm}mm 移动测试")
            print("-" * 50)

            input(f"\n准备移动 {distance_mm}mm。请确认安全后按 Enter 继续...")

            self.move_relative(distance_mm)

            # 5. 禁用
            self.disable_motor()

            print("\n" + "-" * 50)
            print("请使用尺子测量实际移动距离，与预期 10mm 对比。")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\n测试中断")
            self.disable_motor()
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description="编码器分辨率验证")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--distance", type=float, default=10.0, help="测试距离 (mm)")
    args = parser.parse_args()

    verifier = EncoderVerifier(args.port, args.slave_id)
    verifier.run_test(args.distance)


if __name__ == "__main__":
    main()
