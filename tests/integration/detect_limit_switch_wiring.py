#!/usr/bin/env python3
"""
限位开关接线检测脚本

通过监控 DI 信号变化来检测限位开关接在哪个端口。

使用方法:
1. 运行脚本
2. 按提示手动触发每个限位开关
3. 脚本会检测并报告接线情况
"""

import argparse
import logging
import sys
import time
from typing import Dict, List, Optional, Tuple

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
    # DI 监控寄存器 (200Bh:05h) - 注意: 是 0x01E2 不是 0x01E3!
    DI_MONITOR = 0x01E2

    # DI 配置
    DI1_FUNCTION = 0x00D5
    DI1_LOGIC = 0x00D6
    DI2_FUNCTION = 0x00D7
    DI2_LOGIC = 0x00D8
    DI3_FUNCTION = 0x00D9
    DI3_LOGIC = 0x00DA


class LimitSwitchDetector:
    """限位开关检测器"""

    def __init__(self, port: str, slave_id: int):
        self.port = port
        self.slave_id = slave_id
        self.client: Optional[ModbusClient] = None
        self.serial: Optional[SerialPort] = None
        self.detected_wiring: Dict[str, Optional[int]] = {
            "negative_limit": None,
            "positive_limit": None,
            "home_switch": None,
        }

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

    def _read_di_state(self) -> int:
        """读取 DI 原始状态"""
        return self.client.read_register(self.slave_id, Reg.DI_MONITOR)

    def _parse_di_bits(self, state: int) -> Dict[str, bool]:
        """解析 DI 各位状态"""
        return {
            "DI1": bool(state & 0x0001),
            "DI2": bool(state & 0x0002),
            "DI3": bool(state & 0x0004),
        }

    def monitor_for_change(self, timeout: float = 10.0) -> Optional[Tuple[str, bool]]:
        """监控 DI 变化，返回变化的 DI 和新状态"""
        initial_state = self._read_di_state()
        initial_bits = self._parse_di_bits(initial_state)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_state = self._read_di_state()
                current_bits = self._parse_di_bits(current_state)

                # 检测变化
                for di_name in ["DI1", "DI2", "DI3"]:
                    if current_bits[di_name] != initial_bits[di_name]:
                        return (di_name, current_bits[di_name])

                time.sleep(0.05)
            except Exception:
                time.sleep(0.1)

        return None

    def detect_switch(self, switch_name: str, description: str) -> Optional[int]:
        """检测单个开关的接线"""
        print(f"\n{'='*50}")
        print(f"检测: {switch_name}")
        print(f"{'='*50}")
        print(f"请{description}")
        print("等待检测中... (10秒超时)")
        print()

        # 显示当前状态
        initial_state = self._read_di_state()
        initial_bits = self._parse_di_bits(initial_state)
        print(f"当前 DI 状态: DI1={'高' if initial_bits['DI1'] else '低'}, "
              f"DI2={'高' if initial_bits['DI2'] else '低'}, "
              f"DI3={'高' if initial_bits['DI3'] else '低'}")
        print()

        result = self.monitor_for_change(timeout=10.0)

        if result:
            di_name, new_state = result
            di_num = int(di_name[2])  # 提取数字
            state_str = "高电平" if new_state else "低电平"
            print(f"检测到 {di_name} 变化为 {state_str}")
            print(f">>> {switch_name} 接在 {di_name}")
            return di_num
        else:
            print("未检测到 DI 变化")
            return None

    def run_detection(self):
        """运行完整检测流程"""
        print("\n" + "=" * 60)
        print("限位开关接线检测")
        print("=" * 60)
        print(f"串口: {self.port}")
        print(f"从站地址: 0x{self.slave_id:02X}")
        print()
        print("本脚本将引导您检测限位开关的接线位置。")
        print("请按照提示操作，手动触发对应的限位开关。")
        print()

        if not self.connect():
            return

        try:
            # 显示当前 DI 状态
            state = self._read_di_state()
            bits = self._parse_di_bits(state)
            print(f"当前 DI 原始状态: 0x{state:04X}")
            print(f"  DI1: {'高' if bits['DI1'] else '低'}")
            print(f"  DI2: {'高' if bits['DI2'] else '低'}")
            print(f"  DI3: {'高' if bits['DI3'] else '低'}")

            input("\n按 Enter 开始检测负限位开关...")

            # 检测负限位
            neg_di = self.detect_switch(
                "负限位开关",
                "手动触发 负限位 开关 (Z轴向下的限位)"
            )
            self.detected_wiring["negative_limit"] = neg_di

            if neg_di:
                input("\n松开开关后，按 Enter 继续检测正限位...")
            else:
                input("\n按 Enter 继续检测正限位 (如果没有负限位可跳过)...")

            # 检测正限位
            pos_di = self.detect_switch(
                "正限位开关",
                "手动触发 正限位 开关 (Z轴向上的限位)"
            )
            self.detected_wiring["positive_limit"] = pos_di

            if pos_di:
                input("\n松开开关后，按 Enter 继续检测原点开关...")
            else:
                input("\n按 Enter 继续检测原点开关 (如果没有正限位可跳过)...")

            # 检测原点开关
            home_di = self.detect_switch(
                "原点开关",
                "手动触发 原点 开关 (如果有的话)"
            )
            self.detected_wiring["home_switch"] = home_di

            # 显示结果
            self.show_results()

        except KeyboardInterrupt:
            print("\n\n检测已取消")
        finally:
            self.disconnect()

    def show_results(self):
        """显示检测结果"""
        print("\n" + "=" * 60)
        print("检测结果汇总")
        print("=" * 60)

        detected_any = False

        if self.detected_wiring["negative_limit"]:
            print(f"  负限位开关: DI{self.detected_wiring['negative_limit']}")
            detected_any = True
        else:
            print("  负限位开关: 未检测到")

        if self.detected_wiring["positive_limit"]:
            print(f"  正限位开关: DI{self.detected_wiring['positive_limit']}")
            detected_any = True
        else:
            print("  正限位开关: 未检测到")

        if self.detected_wiring["home_switch"]:
            print(f"  原点开关: DI{self.detected_wiring['home_switch']}")
            detected_any = True
        else:
            print("  原点开关: 未检测到")

        if detected_any:
            print("\n" + "-" * 60)
            print("建议的 DI 配置命令:")
            print("-" * 60)

            if self.detected_wiring["negative_limit"]:
                di = self.detected_wiring["negative_limit"]
                func_reg = [0x00D5, 0x00D7, 0x00D9][di - 1]
                print(f"  # 配置 DI{di} 为负限位 (功能15)")
                print(f"  write_register(0x03, 0x{func_reg:04X}, 15)")

            if self.detected_wiring["positive_limit"]:
                di = self.detected_wiring["positive_limit"]
                func_reg = [0x00D5, 0x00D7, 0x00D9][di - 1]
                print(f"  # 配置 DI{di} 为正限位 (功能14)")
                print(f"  write_register(0x03, 0x{func_reg:04X}, 14)")

            if self.detected_wiring["home_switch"]:
                di = self.detected_wiring["home_switch"]
                func_reg = [0x00D5, 0x00D7, 0x00D9][di - 1]
                print(f"  # 配置 DI{di} 为原点开关 (功能31)")
                print(f"  write_register(0x03, 0x{func_reg:04X}, 31)")

            # 生成自动配置脚本
            print("\n" + "-" * 60)
            print("是否要自动应用这些配置? (将创建配置脚本)")
            print("-" * 60)
        else:
            print("\n未检测到任何限位开关。")
            print("可能的原因:")
            print("  1. 限位开关未接线")
            print("  2. 限位开关接线不正确")
            print("  3. 限位开关损坏")
            print("\n建议:")
            print("  - 检查限位开关接线")
            print("  - 使用万用表测试限位开关")
            print("  - 考虑使用堵转回零方式 (方式 37/38)")


def main():
    parser = argparse.ArgumentParser(description="限位开关接线检测")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    args = parser.parse_args()

    detector = LimitSwitchDetector(args.port, args.slave_id)
    detector.run_detection()


if __name__ == "__main__":
    main()
