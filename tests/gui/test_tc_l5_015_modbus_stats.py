#!/usr/bin/env python3
"""
TC-L5-015: Modbus 统计信息测试

测试 ModbusDebugPanel 的统计功能:
- 计数器追踪 (_tx_count, _rx_count, _err_count)
- 统计更新 (_update_stats)
- 统计重置 (_reset_stats)
- 成功率计算
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QApplication
from servo_service import ServoService
from app.widgets.modbus_debug_panel import ModbusDebugPanel


def test_initial_stats():
    """测试初始统计状态"""
    print("\n--- 测试初始统计状态 ---")

    service = ServoService()
    panel = ModbusDebugPanel(service)

    # 验证初始计数器
    assert panel._tx_count == 0, f"初始 tx_count 应为 0, 实际: {panel._tx_count}"
    assert panel._rx_count == 0, f"初始 rx_count 应为 0, 实际: {panel._rx_count}"
    assert panel._err_count == 0, f"初始 err_count 应为 0, 实际: {panel._err_count}"

    # 验证初始统计标签
    stats_text = panel._stats_label.text()
    assert "发送: 0" in stats_text, f"应包含 '发送: 0': {stats_text}"
    assert "接收: 0" in stats_text, f"应包含 '接收: 0': {stats_text}"
    assert "错误: 0" in stats_text, f"应包含 '错误: 0': {stats_text}"
    assert "成功率: --" in stats_text, f"应包含 '成功率: --': {stats_text}"

    print("  ✓ 初始计数器全为 0")
    print("  ✓ 初始统计标签显示正确")
    return True


def test_update_stats():
    """测试统计更新功能"""
    print("\n--- 测试统计更新功能 ---")

    service = ServoService()
    panel = ModbusDebugPanel(service)

    # 测试 1: 设置计数器并更新
    panel._tx_count = 10
    panel._rx_count = 8
    panel._err_count = 2
    panel._update_stats()

    stats_text = panel._stats_label.text()
    assert "发送: 10" in stats_text, f"应包含 '发送: 10': {stats_text}"
    assert "接收: 8" in stats_text, f"应包含 '接收: 8': {stats_text}"
    assert "错误: 2" in stats_text, f"应包含 '错误: 2': {stats_text}"
    # 成功率 = 8/10 * 100 = 80.0%
    assert "成功率: 80.0%" in stats_text, f"应包含 '成功率: 80.0%': {stats_text}"

    print("  ✓ 计数器值正确更新到标签")
    print("  ✓ 成功率计算正确 (80.0%)")

    # 测试 2: 不同的成功率
    panel._tx_count = 3
    panel._rx_count = 2
    panel._err_count = 1
    panel._update_stats()

    stats_text = panel._stats_label.text()
    # 成功率 = 2/3 * 100 = 66.666...%
    assert "66.7%" in stats_text, f"应包含约 66.7%: {stats_text}"

    print("  ✓ 成功率计算正确 (66.7%)")

    # 测试 3: 100% 成功率
    panel._tx_count = 5
    panel._rx_count = 5
    panel._err_count = 0
    panel._update_stats()

    stats_text = panel._stats_label.text()
    assert "成功率: 100.0%" in stats_text, f"应包含 '成功率: 100.0%': {stats_text}"

    print("  ✓ 100% 成功率计算正确")

    return True


def test_reset_stats():
    """测试统计重置功能"""
    print("\n--- 测试统计重置功能 ---")

    service = ServoService()
    panel = ModbusDebugPanel(service)

    # 设置一些计数
    panel._tx_count = 100
    panel._rx_count = 95
    panel._err_count = 5
    panel._update_stats()

    # 验证设置后的状态
    assert panel._tx_count == 100
    assert panel._rx_count == 95
    assert panel._err_count == 5

    # 执行重置
    panel._reset_stats()

    # 验证重置后的状态
    assert panel._tx_count == 0, f"重置后 tx_count 应为 0, 实际: {panel._tx_count}"
    assert panel._rx_count == 0, f"重置后 rx_count 应为 0, 实际: {panel._rx_count}"
    assert panel._err_count == 0, f"重置后 err_count 应为 0, 实际: {panel._err_count}"

    # 验证标签也更新了
    stats_text = panel._stats_label.text()
    assert "发送: 0" in stats_text, f"重置后应包含 '发送: 0': {stats_text}"
    assert "接收: 0" in stats_text, f"重置后应包含 '接收: 0': {stats_text}"
    assert "错误: 0" in stats_text, f"重置后应包含 '错误: 0': {stats_text}"
    assert "成功率: --" in stats_text, f"重置后应包含 '成功率: --': {stats_text}"

    print("  ✓ 计数器全部重置为 0")
    print("  ✓ 统计标签更新正确")
    return True


def test_stats_label_format():
    """测试统计标签格式"""
    print("\n--- 测试统计标签格式 ---")

    service = ServoService()
    panel = ModbusDebugPanel(service)

    # 期望格式: "发送: X  接收: Y  错误: Z  成功率: N%"
    expected_format_parts = ["发送:", "接收:", "错误:", "成功率:"]

    stats_text = panel._stats_label.text()
    for part in expected_format_parts:
        assert part in stats_text, f"统计标签应包含 '{part}': {stats_text}"

    print("  ✓ 标签格式包含所有必要部分")

    # 验证标签样式
    style = panel._stats_label.styleSheet()
    assert "color" in style.lower(), f"标签应有颜色样式: {style}"

    print("  ✓ 标签有颜色样式")
    return True


def test_zero_division():
    """测试零除处理"""
    print("\n--- 测试零除处理 ---")

    service = ServoService()
    panel = ModbusDebugPanel(service)

    # tx_count = 0 时不应发生除零错误
    panel._tx_count = 0
    panel._rx_count = 0
    panel._err_count = 0

    # 这不应该抛出异常
    try:
        panel._update_stats()
    except ZeroDivisionError:
        assert False, "不应发生零除错误"

    stats_text = panel._stats_label.text()
    assert "成功率: --" in stats_text, f"tx=0 时成功率应显示 '--': {stats_text}"

    print("  ✓ 零除保护正常")
    print("  ✓ tx=0 时显示 '--'")
    return True


def main():
    """运行所有测试"""
    # 创建应用实例 (必须在创建 Qt widgets 之前)
    app = QApplication(sys.argv)

    print("=" * 60)
    print("TC-L5-015: Modbus 统计信息测试")
    print("=" * 60)

    tests = [
        ("初始统计状态", test_initial_stats),
        ("统计更新功能", test_update_stats),
        ("统计重置功能", test_reset_stats),
        ("统计标签格式", test_stats_label_format),
        ("零除处理", test_zero_division),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} 测试通过")
            else:
                failed += 1
                print(f"\n✗ {name} 测试失败")
        except AssertionError as e:
            failed += 1
            print(f"\n✗ {name} 测试失败: {e}")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    if failed == 0:
        print("TC-L5-015: PASSED")
    else:
        print(f"TC-L5-015: FAILED ({failed} 项失败)")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
