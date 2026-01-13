#!/usr/bin/env python3
"""
限位开关与回零配置诊断脚本

在进行 TC-L4-003 回零测试之前，使用此脚本检查：
1. 数字输入 (DI) 配置状态
2. 限位开关当前状态
3. 回零参数配置
4. 实时监控限位开关变化

用法:
    python3 diagnose_limit_switches.py [--port PORT] [--slave-id ID] [--monitor]
"""

import argparse
import logging
import sys
import time
from typing import Dict, List, Optional

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
    # 状态寄存器
    STATUS_WORD = 0x0381
    ERROR_CODE = 0x0382

    # DI 配置 (2003h 组)
    DI1_FUNCTION = 0x00D5
    DI1_LOGIC = 0x00D6
    DI2_FUNCTION = 0x00D7
    DI2_LOGIC = 0x00D8
    DI3_FUNCTION = 0x00D9
    DI3_LOGIC = 0x00DA

    # 数字输入状态
    DIGITAL_INPUTS = 0x0447   # 60FDh

    # 回零参数
    HOMING_METHOD = 0x0416    # 6098h
    HOMING_SPEED_FAST = 0x0417  # 6099h:01
    HOMING_SPEED_SLOW = 0x0419  # 6099h:02
    HOMING_ACCELERATION = 0x041B  # 609Ah
    HOME_OFFSET = 0x03ED      # 607Ch

    # 堵转回零参数
    BLOCKING_TORQUE = 0x0170  # 2007h:13h
    BLOCKING_TIME = 0x0172    # 2007h:15h

    # 位置
    POSITION_ACTUAL = 0x03C8  # 6064h


# DI 功能号定义
DI_FUNCTIONS = {
    0: "未定义",
    1: "电机使能 (NiMotion)",
    2: "报警复位",
    6: "多段命令切换1",
    7: "多段命令切换2",
    8: "多段命令切换3",
    9: "多段命令切换4",
    12: "暂停",
    14: "正限位开关",
    15: "负限位开关",
    20: "步进使能",
    21: "速度方向",
    28: "多段位置/速度使能",
    31: "原点开关",
    33: "设置原点",
    36: "模拟输入方向",
    38: "清除故障历史",
    40: "正交脉冲A (DI1)",
    41: "正交脉冲B (DI2)",
    42: "脉冲输入 (DI1)",
    43: "脉冲方向 (DI2)",
    44: "占空比输入 (DI1)",
    45: "占空比方向 (DI2)",
}

DI_LOGIC = {
    0: "低电平有效",
    1: "高电平有效",
    2: "上升沿",
    3: "下降沿",
    4: "双边沿",
}

HOMING_METHODS = {
    17: "负限位 (反向)",
    18: "正限位 (正向)",
    19: "原点开关 (正向, 正侧)",
    20: "原点开关 (正向, 负侧)",
    21: "原点开关 (反向, 负侧)",
    22: "原点开关 (反向, 正侧)",
    23: "原点+正限位 (正向)",
    24: "原点+正限位 (正向)",
    25: "原点+正限位 (正向)",
    26: "原点+正限位 (正向)",
    27: "原点+负限位 (反向)",
    28: "原点+负限位 (反向)",
    29: "原点+负限位 (反向)",
    30: "原点+负限位 (反向)",
    37: "堵转检测 (正向)",
    38: "堵转检测 (反向)",
}


class LimitSwitchDiagnostics:
    """限位开关诊断工具"""

    def __init__(self, port: str, slave_id: int):
        self.port = port
        self.slave_id = slave_id
        self.client: Optional[ModbusClient] = None
        self.serial: Optional[SerialPort] = None

    def connect(self) -> bool:
        """连接到驱动器"""
        try:
            self.serial = SerialPort(port=self.port, baudrate=115200, timeout=0.5)
            self.serial.open()
            self.client = ModbusClient(serial_port=self.serial)

            # 验证通信
            status = self.client.read_register(self.slave_id, Reg.STATUS_WORD)
            logger.info(f"连接成功, 状态字: 0x{status:04X}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.serial:
            self.serial.close()

    def _read_register(self, address: int) -> int:
        return self.client.read_register(self.slave_id, address)

    def _read_register_32bit(self, address: int, signed: bool = False) -> int:
        """读取 32 位寄存器 (大端序)"""
        values = self.client.read_holding_registers(self.slave_id, address, 2)
        value = (values[0] << 16) | values[1]
        if signed and value >= 0x80000000:
            value -= 0x100000000
        return value

    def diagnose_di_config(self) -> Dict:
        """诊断 DI 配置"""
        print("\n" + "=" * 60)
        print("数字输入 (DI) 配置")
        print("=" * 60)

        di_configs = []
        limit_switches = {"positive": None, "negative": None, "home": None}

        for i, (func_reg, logic_reg) in enumerate([
            (Reg.DI1_FUNCTION, Reg.DI1_LOGIC),
            (Reg.DI2_FUNCTION, Reg.DI2_LOGIC),
            (Reg.DI3_FUNCTION, Reg.DI3_LOGIC),
        ], start=1):
            try:
                func = self._read_register(func_reg)
                logic = self._read_register(logic_reg)

                func_name = DI_FUNCTIONS.get(func, f"未知({func})")
                logic_name = DI_LOGIC.get(logic, f"未知({logic})")

                di_configs.append({
                    "di": f"DI{i}",
                    "function": func,
                    "function_name": func_name,
                    "logic": logic,
                    "logic_name": logic_name,
                })

                print(f"  DI{i}: 功能={func} ({func_name}), 逻辑={logic} ({logic_name})")

                # 检查限位开关配置
                if func == 14:
                    limit_switches["positive"] = f"DI{i}"
                elif func == 15:
                    limit_switches["negative"] = f"DI{i}"
                elif func == 31:
                    limit_switches["home"] = f"DI{i}"

            except Exception as e:
                print(f"  DI{i}: 读取失败 - {e}")

        print()
        print("限位开关配置状态:")
        print(f"  正限位 (功能14): {limit_switches['positive'] or '未配置'}")
        print(f"  负限位 (功能15): {limit_switches['negative'] or '未配置'}")
        print(f"  原点开关 (功能31): {limit_switches['home'] or '未配置'}")

        return {"di_configs": di_configs, "limit_switches": limit_switches}

    def diagnose_di_state(self) -> Dict:
        """诊断 DI 当前状态"""
        print("\n" + "=" * 60)
        print("数字输入当前状态")
        print("=" * 60)

        try:
            di_state = self._read_register_32bit(Reg.DIGITAL_INPUTS)
            print(f"  数字输入寄存器 (60FDh): 0x{di_state:08X}")
            print()

            # 解析各位
            # 根据 CiA402 标准，60FDh 的位定义:
            # Bit 0: 负限位
            # Bit 1: 正限位
            # Bit 2: 原点开关
            signals = {
                "负限位 (Bit 0)": bool(di_state & 0x0001),
                "正限位 (Bit 1)": bool(di_state & 0x0002),
                "原点开关 (Bit 2)": bool(di_state & 0x0004),
            }

            print("  信号状态 (根据 CiA402 60FDh 定义):")
            for name, active in signals.items():
                status = "触发" if active else "未触发"
                print(f"    {name}: {status}")

            return {"raw": di_state, "signals": signals}

        except Exception as e:
            print(f"  读取失败: {e}")
            return {"error": str(e)}

    def diagnose_homing_config(self) -> Dict:
        """诊断回零配置"""
        print("\n" + "=" * 60)
        print("回零配置参数")
        print("=" * 60)

        config = {}

        try:
            # 回零方式
            method = self._read_register(Reg.HOMING_METHOD)
            method_name = HOMING_METHODS.get(method, f"未知方式({method})")
            config["method"] = method
            config["method_name"] = method_name
            print(f"  回零方式 (6098h): {method} - {method_name}")

            # 回零速度
            speed_fast = self._read_register_32bit(Reg.HOMING_SPEED_FAST)
            speed_slow = self._read_register_32bit(Reg.HOMING_SPEED_SLOW)
            config["speed_fast"] = speed_fast
            config["speed_slow"] = speed_slow
            print(f"  回零高速 (6099h:01): {speed_fast} user units/s")
            print(f"  回零低速 (6099h:02): {speed_slow} user units/s")

            # 回零加速度
            accel = self._read_register_32bit(Reg.HOMING_ACCELERATION)
            config["acceleration"] = accel
            print(f"  回零加速度 (609Ah): {accel} user units/s²")

            # 原点偏移
            offset = self._read_register_32bit(Reg.HOME_OFFSET, signed=True)
            config["offset"] = offset
            print(f"  原点偏移 (607Ch): {offset} user units")

            # 堵转回零参数
            if method in [37, 38]:
                print()
                print("  堵转回零参数:")
                try:
                    torque = self._read_register(Reg.BLOCKING_TORQUE)
                    blocking_time = self._read_register(Reg.BLOCKING_TIME)
                    config["blocking_torque"] = torque
                    config["blocking_time"] = blocking_time
                    print(f"    堵转转矩 (2007h:13h): {torque} (0.1%)")
                    print(f"    堵转时间 (2007h:15h): {blocking_time} ms")
                except Exception as e:
                    print(f"    读取失败: {e}")

        except Exception as e:
            print(f"  读取失败: {e}")
            config["error"] = str(e)

        return config

    def diagnose_position(self) -> Dict:
        """诊断当前位置"""
        print("\n" + "=" * 60)
        print("当前位置")
        print("=" * 60)

        try:
            position = self._read_register_32bit(Reg.POSITION_ACTUAL, signed=True)
            print(f"  实际位置 (6064h): {position} user units")
            print(f"  约等于: {position / 10000:.2f} 圈 (假设 10000 脉冲/圈)")
            return {"position": position}
        except Exception as e:
            print(f"  读取失败: {e}")
            return {"error": str(e)}

    def check_safety(self, di_config: Dict, homing_config: Dict) -> List[str]:
        """检查安全隐患"""
        print("\n" + "=" * 60)
        print("安全检查")
        print("=" * 60)

        warnings = []

        limit_switches = di_config.get("limit_switches", {})
        method = homing_config.get("method", 0)

        # 检查限位开关配置
        if method in [17, 27, 28, 29, 30]:  # 需要负限位
            if not limit_switches.get("negative"):
                warnings.append("回零方式需要负限位开关，但未配置!")

        if method in [18, 23, 24, 25, 26]:  # 需要正限位
            if not limit_switches.get("positive"):
                warnings.append("回零方式需要正限位开关，但未配置!")

        if method in [19, 20, 21, 22]:  # 需要原点开关
            if not limit_switches.get("home"):
                warnings.append("回零方式需要原点开关，但未配置!")

        if method in [23, 24, 25, 26, 27, 28, 29, 30]:  # 需要原点+限位
            if not limit_switches.get("home"):
                warnings.append("回零方式需要原点开关，但未配置!")

        # 检查速度
        speed_fast = homing_config.get("speed_fast", 0)
        if speed_fast > 100000:  # > 600 RPM
            warnings.append(f"回零高速过快 ({speed_fast} user units/s)，建议降低")

        # 堵转回零检查
        if method in [37, 38]:
            if not homing_config.get("blocking_torque"):
                warnings.append("使用堵转回零，但堵转转矩参数未读取")
            warnings.append("注意: 堵转回零可能导致电机过热或机械损伤")

        # 打印结果
        if warnings:
            print("  发现以下安全隐患:")
            for i, w in enumerate(warnings, 1):
                print(f"    {i}. {w}")
        else:
            print("  未发现明显安全隐患")

        return warnings

    def monitor_di_state(self, duration: float = 30.0):
        """实时监控 DI 状态变化"""
        print("\n" + "=" * 60)
        print(f"实时监控数字输入状态 (持续 {duration} 秒)")
        print("请手动触发限位开关进行测试...")
        print("按 Ctrl+C 停止监控")
        print("=" * 60)

        last_state = None
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    di_state = self._read_register_32bit(Reg.DIGITAL_INPUTS)

                    if di_state != last_state:
                        elapsed = time.time() - start_time
                        neg_limit = "触发" if di_state & 0x0001 else "---"
                        pos_limit = "触发" if di_state & 0x0002 else "---"
                        home_sw = "触发" if di_state & 0x0004 else "---"

                        print(f"  [{elapsed:6.2f}s] 0x{di_state:08X} | 负限位:{neg_limit} | 正限位:{pos_limit} | 原点:{home_sw}")
                        last_state = di_state

                    time.sleep(0.05)

                except Exception as e:
                    print(f"  读取错误: {e}")
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n  监控已停止")

    def run_full_diagnosis(self, monitor: bool = False):
        """运行完整诊断"""
        print("\n" + "=" * 60)
        print("限位开关与回零配置诊断")
        print("=" * 60)
        print(f"串口: {self.port}")
        print(f"从站地址: 0x{self.slave_id:02X}")

        if not self.connect():
            return

        try:
            di_config = self.diagnose_di_config()
            di_state = self.diagnose_di_state()
            homing_config = self.diagnose_homing_config()
            position = self.diagnose_position()

            warnings = self.check_safety(di_config, homing_config)

            # 建议
            print("\n" + "=" * 60)
            print("建议")
            print("=" * 60)

            limit_switches = di_config.get("limit_switches", {})
            if not any(limit_switches.values()):
                print("  1. 当前没有配置任何限位开关")
                print("     如果使用限位回零，需要先配置 DI 功能:")
                print("     - 正限位: 写入 14 到 DI 功能寄存器")
                print("     - 负限位: 写入 15 到 DI 功能寄存器")
                print("     - 原点: 写入 31 到 DI 功能寄存器")

            if warnings:
                print(f"  2. 发现 {len(warnings)} 个安全隐患，请先解决后再进行回零测试")
            else:
                print("  2. 可以进行回零测试，但请确保:")
                print("     - 手动验证限位开关能正确触发")
                print("     - 准备好急停按钮")
                print("     - 首次使用低速测试")

            if monitor:
                self.monitor_di_state()

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description="限位开关与回零配置诊断")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="串口设备")
    parser.add_argument("--slave-id", type=int, default=0x03, help="从站地址")
    parser.add_argument("--monitor", action="store_true", help="启用实时监控模式")
    args = parser.parse_args()

    diag = LimitSwitchDiagnostics(args.port, args.slave_id)
    diag.run_full_diagnosis(monitor=args.monitor)


if __name__ == "__main__":
    main()
