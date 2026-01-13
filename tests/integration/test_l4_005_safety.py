#!/usr/bin/env python3
"""
TC-L4-005: 急停与安全功能测试

测试内容:
1. 快速停止 (Quick Stop) - 控制字 bit2
2. 暂停功能 (Halt) - 控制字 bit8
3. 禁用操作 (Disable Operation)
4. 故障响应与复位
5. 限位开关响应
6. 不同停止模式选项 (605Ah, 605Dh)

安全测试说明:
- 所有测试使用小距离和低速度以确保安全
- 测试过程中请保持注意，准备手动断电
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
    ERROR_CODE = 0x037F        # 603Fh
    OPERATION_MODE = 0x03C2    # 6060h

    # 位置寄存器
    TARGET_POSITION = 0x03E7   # 607Ah (32-bit)
    ACTUAL_POSITION = 0x03C8   # 6064h (32-bit)

    # 速度寄存器
    TARGET_VELOCITY = 0x0448   # 60FFh (32-bit) PV模式
    PROFILE_VELOCITY = 0x03F8  # 6081h (32-bit)
    ACTUAL_VELOCITY = 0x03D5   # 606Ch (32-bit)

    # 加减速
    PROFILE_ACCEL = 0x03FC     # 6083h
    PROFILE_DECEL = 0x03FE     # 6084h
    QUICK_STOP_DECEL = 0x0400  # 6085h

    # 停止模式选项
    QUICK_STOP_OPTION = 0x03BF   # 605Ah
    SHUTDOWN_OPTION = 0x03BD    # 605Bh
    DISABLE_OP_OPTION = 0x03BE  # 605Ch
    HALT_OPTION = 0x03C0        # 605Dh
    FAULT_OPTION = 0x03C1       # 605Eh

    # 限位状态
    DIGITAL_INPUTS = 0x0447    # 60FDh (32-bit)
    DI_MONITOR = 0x01E2        # 物理DI状态

    # 告警历史
    ALARM_COUNT = 0x0001       # 1003h:00
    ALARM_1 = 0x0002           # 1003h:01 最新告警


# 控制字位定义
CW_SWITCH_ON = 0x0001         # bit 0
CW_ENABLE_VOLTAGE = 0x0002    # bit 1
CW_QUICK_STOP = 0x0004        # bit 2 (0=quick stop, 1=normal)
CW_ENABLE_OPERATION = 0x0008  # bit 3
CW_NEW_SETPOINT = 0x0010      # bit 4 (PP mode)
CW_HALT = 0x0100              # bit 8
CW_FAULT_RESET = 0x0080       # bit 7


class SafetyTest:
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

    def get_status_word(self) -> int:
        """获取状态字"""
        return self.read_reg(Reg.STATUS_WORD)

    def get_status_state(self) -> str:
        """获取当前状态机状态"""
        status = self.get_status_word()
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
        if (status & 0x006F) == 0x0007:  # Quick stop active
            return "Quick stop active"
        return f"Unknown (0x{status:04X})"

    def clear_fault(self):
        """清除故障"""
        self.write_reg(Reg.CONTROL_WORD, 0x0080)  # Fault reset
        time.sleep(0.1)
        self.write_reg(Reg.CONTROL_WORD, 0x0000)
        time.sleep(0.1)

    def enable_motor(self) -> bool:
        """使能电机"""
        self.clear_fault()

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

    def set_pv_mode(self):
        """设置为PV模式"""
        self.write_reg(Reg.OPERATION_MODE, 3)
        time.sleep(0.1)

    def start_motion(self, target_position: int):
        """开始PP模式运动"""
        self.write_reg32(Reg.TARGET_POSITION, target_position)
        time.sleep(0.02)
        self.write_reg(Reg.CONTROL_WORD, 0x000F)
        time.sleep(0.02)
        self.write_reg(Reg.CONTROL_WORD, 0x001F)

    def start_velocity(self, velocity: int):
        """开始PV模式运动"""
        self.write_reg32(Reg.TARGET_VELOCITY, velocity)
        time.sleep(0.02)
        # PV模式使能
        self.write_reg(Reg.CONTROL_WORD, 0x000F)

    def is_moving(self) -> bool:
        """检查电机是否在运动"""
        vel = self.read_reg32(Reg.ACTUAL_VELOCITY)
        return abs(vel) > 5  # > 5 rpm

    def get_actual_velocity(self) -> int:
        """获取实际速度 (rpm)"""
        return self.read_reg32(Reg.ACTUAL_VELOCITY)

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {"name": test_name, "passed": passed, "details": details}
        self.test_results.append(result)
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {details}")

    # ==================== 测试用例 ====================

    def test_1_read_stop_options(self) -> bool:
        """测试1: 读取停止模式选项"""
        print("\n" + "=" * 60)
        print("测试 1: 读取停止模式选项")
        print("=" * 60)

        try:
            qs_opt = self.read_reg(Reg.QUICK_STOP_OPTION)
            shutdown_opt = self.read_reg(Reg.SHUTDOWN_OPTION)
            disable_opt = self.read_reg(Reg.DISABLE_OP_OPTION)
            halt_opt = self.read_reg(Reg.HALT_OPTION)
            fault_opt = self.read_reg(Reg.FAULT_OPTION)

            print(f"\n停止模式选项:")
            print(f"  快速停止选项 (605Ah): {qs_opt}")
            print(f"    0=滑行停止, 1=使用6084h减速, 2=使用6085h减速")
            print(f"  关闭选项 (605Bh): {shutdown_opt}")
            print(f"  禁用操作选项 (605Ch): {disable_opt}")
            print(f"  暂停选项 (605Dh): {halt_opt}")
            print(f"    1=使用6084h减速, 2=使用6085h减速")
            print(f"  故障响应选项 (605Eh): {fault_opt}")

            # 读取减速度参数
            profile_decel = self.read_reg32(Reg.PROFILE_DECEL)
            quick_stop_decel = self.read_reg32(Reg.QUICK_STOP_DECEL)

            print(f"\n减速度参数:")
            print(f"  轮廓减速度 (6084h): {profile_decel} user units/s²")
            print(f"  快速停止减速度 (6085h): {quick_stop_decel} user units/s²")

            self.record_result("读取停止模式选项", True, "成功读取所有选项")
            return True

        except Exception as e:
            self.record_result("读取停止模式选项", False, str(e))
            return False

    def test_2_halt_function(self) -> bool:
        """测试2: 暂停功能 (Halt)"""
        print("\n" + "=" * 60)
        print("测试 2: 暂停功能 (Halt)")
        print("=" * 60)

        try:
            self.set_pv_mode()
            if not self.enable_motor():
                self.record_result("暂停功能", False, "电机使能失败")
                return False

            # 设置运动参数
            self.write_reg32(Reg.PROFILE_ACCEL, 50000)
            self.write_reg32(Reg.PROFILE_DECEL, 50000)

            # 开始速度运动
            test_velocity = 10000  # user units/s ≈ 60 rpm
            print(f"\n启动速度运动: {test_velocity} user units/s")
            self.start_velocity(test_velocity)

            # 等待加速
            time.sleep(1.0)

            actual_vel = self.get_actual_velocity()
            print(f"运动中实际速度: {actual_vel} rpm")

            if not self.is_moving():
                self.record_result("暂停功能", False, "电机未能启动运动")
                return False

            # 触发 Halt
            print("\n发送 Halt 命令 (控制字 bit8=1)...")
            halt_start = time.time()
            self.write_reg(Reg.CONTROL_WORD, 0x010F)  # Enable + Halt

            # 监控减速过程
            max_wait = 3.0
            while time.time() - halt_start < max_wait:
                vel = self.get_actual_velocity()
                print(f"  速度: {vel} rpm")
                if abs(vel) < 5:
                    break
                time.sleep(0.1)

            halt_time = time.time() - halt_start
            final_vel = self.get_actual_velocity()
            print(f"\nHalt 完成，耗时: {halt_time:.2f}s, 最终速度: {final_vel} rpm")

            # 检查状态
            status = self.get_status_word()
            target_reached = bool(status & 0x0400)
            print(f"状态字: 0x{status:04X}, 目标到达: {target_reached}")

            # 释放 Halt
            print("\n释放 Halt...")
            self.write_reg(Reg.CONTROL_WORD, 0x000F)
            time.sleep(0.5)

            # 停止运动
            self.write_reg32(Reg.TARGET_VELOCITY, 0)
            time.sleep(0.5)

            self.disable_motor()

            passed = halt_time < 2.0 and abs(final_vel) < 10
            self.record_result("暂停功能", passed,
                             f"Halt耗时={halt_time:.2f}s, 最终速度={final_vel}rpm")
            return passed

        except Exception as e:
            self.disable_motor()
            self.record_result("暂停功能", False, str(e))
            return False

    def test_3_quick_stop(self) -> bool:
        """测试3: 快速停止 (Quick Stop)"""
        print("\n" + "=" * 60)
        print("测试 3: 快速停止 (Quick Stop)")
        print("=" * 60)

        try:
            self.set_pv_mode()
            if not self.enable_motor():
                self.record_result("快速停止", False, "电机使能失败")
                return False

            # 设置较大的快速停止减速度
            self.write_reg32(Reg.QUICK_STOP_DECEL, 200000)
            self.write_reg32(Reg.PROFILE_ACCEL, 50000)

            # 开始速度运动
            test_velocity = 15000  # user units/s
            print(f"\n启动速度运动: {test_velocity} user units/s")
            self.start_velocity(test_velocity)

            # 等待加速
            time.sleep(1.0)

            actual_vel = self.get_actual_velocity()
            print(f"运动中实际速度: {actual_vel} rpm")

            if not self.is_moving():
                self.record_result("快速停止", False, "电机未能启动运动")
                return False

            # 触发 Quick Stop (bit2 = 0)
            print("\n发送 Quick Stop 命令 (控制字 bit2=0)...")
            qs_start = time.time()
            # Quick stop: 保持 bit0,1,3 但清除 bit2
            self.write_reg(Reg.CONTROL_WORD, 0x000B)  # 0x0F & ~0x04 = 0x0B

            # 监控减速
            max_wait = 3.0
            while time.time() - qs_start < max_wait:
                vel = self.get_actual_velocity()
                state = self.get_status_state()
                print(f"  速度: {vel} rpm, 状态: {state}")
                if abs(vel) < 5:
                    break
                time.sleep(0.1)

            qs_time = time.time() - qs_start
            final_vel = self.get_actual_velocity()
            final_state = self.get_status_state()
            print(f"\nQuick Stop 完成，耗时: {qs_time:.2f}s")
            print(f"最终速度: {final_vel} rpm, 状态: {final_state}")

            # 恢复正常
            print("\n恢复到正常操作...")
            self.enable_motor()
            time.sleep(0.2)
            self.disable_motor()

            passed = qs_time < 1.5 and abs(final_vel) < 10
            self.record_result("快速停止", passed,
                             f"Quick Stop耗时={qs_time:.2f}s, 状态={final_state}")
            return passed

        except Exception as e:
            self.disable_motor()
            self.record_result("快速停止", False, str(e))
            return False

    def test_4_disable_operation(self) -> bool:
        """测试4: 禁用操作"""
        print("\n" + "=" * 60)
        print("测试 4: 禁用操作 (Disable Operation)")
        print("=" * 60)

        try:
            self.set_pv_mode()
            if not self.enable_motor():
                self.record_result("禁用操作", False, "电机使能失败")
                return False

            # 开始运动
            test_velocity = 10000
            print(f"\n启动速度运动: {test_velocity} user units/s")
            self.start_velocity(test_velocity)
            time.sleep(1.0)

            if not self.is_moving():
                self.record_result("禁用操作", False, "电机未能启动运动")
                return False

            actual_vel = self.get_actual_velocity()
            print(f"运动中实际速度: {actual_vel} rpm")

            # 禁用操作 (0x07 = Switch on, not operation enabled)
            print("\n发送 Disable Operation 命令...")
            disable_start = time.time()
            self.write_reg(Reg.CONTROL_WORD, 0x0007)

            # 监控
            max_wait = 3.0
            while time.time() - disable_start < max_wait:
                vel = self.get_actual_velocity()
                state = self.get_status_state()
                print(f"  速度: {vel} rpm, 状态: {state}")
                if state == "Switched on" and abs(vel) < 5:
                    break
                time.sleep(0.1)

            disable_time = time.time() - disable_start
            final_state = self.get_status_state()
            final_vel = self.get_actual_velocity()

            print(f"\nDisable Operation 完成，耗时: {disable_time:.2f}s")
            print(f"最终状态: {final_state}, 速度: {final_vel} rpm")

            self.disable_motor()

            passed = final_state == "Switched on" and abs(final_vel) < 10
            self.record_result("禁用操作", passed,
                             f"耗时={disable_time:.2f}s, 状态={final_state}")
            return passed

        except Exception as e:
            self.disable_motor()
            self.record_result("禁用操作", False, str(e))
            return False

    def test_5_fault_reset(self) -> bool:
        """测试5: 故障复位"""
        print("\n" + "=" * 60)
        print("测试 5: 故障复位")
        print("=" * 60)

        try:
            # 读取当前告警状态
            alarm_count = self.read_reg(Reg.ALARM_COUNT)
            print(f"告警历史数量: {alarm_count}")

            if alarm_count > 0:
                alarm1 = self.read_reg32(Reg.ALARM_1)
                print(f"最新告警码: 0x{alarm1:08X}")

            # 检查当前状态
            state = self.get_status_state()
            print(f"当前状态: {state}")

            # 发送故障复位
            print("\n发送 Fault Reset 命令 (控制字 bit7 上升沿)...")
            self.write_reg(Reg.CONTROL_WORD, 0x0000)
            time.sleep(0.05)
            self.write_reg(Reg.CONTROL_WORD, 0x0080)  # Rising edge
            time.sleep(0.2)
            self.write_reg(Reg.CONTROL_WORD, 0x0000)
            time.sleep(0.1)

            new_state = self.get_status_state()
            print(f"复位后状态: {new_state}")

            # 尝试使能
            print("\n尝试使能电机...")
            enabled = self.enable_motor()
            final_state = self.get_status_state()

            self.disable_motor()

            passed = enabled and final_state == "Operation enabled"
            self.record_result("故障复位", passed, f"复位后可使能={enabled}")
            return passed

        except Exception as e:
            self.record_result("故障复位", False, str(e))
            return False

    def test_6_limit_switch_status(self) -> bool:
        """测试6: 限位开关状态检查"""
        print("\n" + "=" * 60)
        print("测试 6: 限位开关状态")
        print("=" * 60)

        try:
            # 读取物理DI状态
            di_phys = self.read_reg(Reg.DI_MONITOR)
            # 读取逻辑限位状态 (60FDh)
            di_logic = self.read_reg32(Reg.DIGITAL_INPUTS)

            print(f"\nDI 物理状态 (0x01E2): 0x{di_phys:04X}")
            print(f"  DI1: {'HIGH' if di_phys & 0x01 else 'LOW'}")
            print(f"  DI2: {'HIGH' if di_phys & 0x02 else 'LOW'} (负限位)")
            print(f"  DI3: {'HIGH' if di_phys & 0x04 else 'LOW'} (正限位)")

            print(f"\n逻辑状态 (60FDh): 0x{di_logic:08X}")
            neg_limit = bool(di_logic & 0x01)
            pos_limit = bool(di_logic & 0x02)
            home_sw = bool(di_logic & 0x04)

            print(f"  负限位 (Bit0): {'触发' if neg_limit else '未触发'}")
            print(f"  正限位 (Bit1): {'触发' if pos_limit else '未触发'}")
            print(f"  原点开关 (Bit2): {'触发' if home_sw else '未触发'}")

            # 检查状态字的 Internal limit active (bit11)
            status = self.get_status_word()
            internal_limit = bool(status & 0x0800)
            print(f"\n状态字 bit11 (内部限位激活): {internal_limit}")

            # 判断是否正常
            if neg_limit or pos_limit:
                print("\n警告: 限位开关当前被触发!")

            self.record_result("限位开关状态", True,
                             f"负限位={neg_limit}, 正限位={pos_limit}")
            return True

        except Exception as e:
            self.record_result("限位开关状态", False, str(e))
            return False

    def test_7_stop_mode_options(self) -> bool:
        """测试7: 停止模式选项配置"""
        print("\n" + "=" * 60)
        print("测试 7: 停止模式选项配置")
        print("=" * 60)

        try:
            # 保存原始值
            orig_qs = self.read_reg(Reg.QUICK_STOP_OPTION)
            orig_halt = self.read_reg(Reg.HALT_OPTION)

            print(f"原始快速停止选项: {orig_qs}")
            print(f"原始暂停选项: {orig_halt}")

            # 测试不同快速停止选项
            qs_options = [0, 1, 2]  # 0=滑行, 1=6084h减速, 2=6085h减速
            for opt in qs_options:
                print(f"\n写入快速停止选项: {opt}")
                self.write_reg(Reg.QUICK_STOP_OPTION, opt)
                time.sleep(0.05)
                read_opt = self.read_reg(Reg.QUICK_STOP_OPTION)
                print(f"读回值: {read_opt}")
                if read_opt != opt:
                    self.record_result("停止模式选项", False,
                                      f"快速停止选项写入失败: 写入{opt}, 读回{read_opt}")
                    return False

            # 测试暂停选项
            halt_options = [1, 2]  # 1=6084h, 2=6085h
            for opt in halt_options:
                print(f"\n写入暂停选项: {opt}")
                self.write_reg(Reg.HALT_OPTION, opt)
                time.sleep(0.05)
                read_opt = self.read_reg(Reg.HALT_OPTION)
                print(f"读回值: {read_opt}")
                if read_opt != opt:
                    self.record_result("停止模式选项", False,
                                      f"暂停选项写入失败: 写入{opt}, 读回{read_opt}")
                    return False

            # 恢复原始值
            self.write_reg(Reg.QUICK_STOP_OPTION, orig_qs)
            self.write_reg(Reg.HALT_OPTION, orig_halt)

            self.record_result("停止模式选项", True, "所有选项读写验证通过")
            return True

        except Exception as e:
            self.record_result("停止模式选项", False, str(e))
            return False

    def run_all_tests(self, auto: bool = False):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("TC-L4-005: 急停与安全功能测试")
        print("=" * 70)
        print("\n警告: 此测试涉及紧急停止和安全功能")
        print("       请确保设备安全，随时准备手动断电")

        self.connect()

        try:
            # 运行测试
            self.test_1_read_stop_options()
            self.test_6_limit_switch_status()

            if auto:
                self.test_2_halt_function()
                self.test_3_quick_stop()
                self.test_4_disable_operation()
                self.test_5_fault_reset()
                self.test_7_stop_mode_options()
            else:
                tests = [
                    ("暂停功能 (Halt)", self.test_2_halt_function),
                    ("快速停止 (Quick Stop)", self.test_3_quick_stop),
                    ("禁用操作", self.test_4_disable_operation),
                    ("故障复位", self.test_5_fault_reset),
                    ("停止模式选项配置", self.test_7_stop_mode_options),
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
            print("\nTC-L4-005 测试通过!")
        else:
            print(f"\nTC-L4-005 测试失败: {total - passed} 个测试未通过")


def main():
    parser = argparse.ArgumentParser(description="TC-L4-005: 急停与安全功能测试")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--auto", action="store_true", help="自动运行所有测试")
    args = parser.parse_args()

    test = SafetyTest(args.port, args.slave_id)
    test.run_all_tests(auto=args.auto)


if __name__ == "__main__":
    main()
