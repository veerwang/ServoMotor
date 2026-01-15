#!/usr/bin/env python3
"""
TC-L5-007: 位置移动测试

测试运动控制面板的位置移动功能:
- 目标位置输入
- 移动速度设置
- 绝对位置移动
- 相对位置移动
- 快速定位按钮
"""

import sys
import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDoubleSpinBox, QPushButton

# 添加项目路径
sys.path.insert(0, "/home/hds/codes/ServoMotorCreate/CreateServoMotor")

from app.widgets.motion_panel import MotionPanel
from servo_service import AxisName, ServoService


def find_widget_by_text(parent, widget_type, text):
    """查找包含指定文本的组件"""
    for widget in parent.findChildren(widget_type):
        if hasattr(widget, "text") and text in widget.text():
            return widget
    return None


def run_test():
    """执行测试"""
    app = QApplication(sys.argv)

    print("=" * 60)
    print("TC-L5-007: 位置移动测试")
    print("=" * 60)

    test_results = []

    # 创建服务和面板
    service = ServoService()
    panel = MotionPanel(service)
    panel.show()

    # 处理事件
    QApplication.processEvents()
    time.sleep(0.5)

    # ==================== 测试1: 检查位置控制组件 ====================
    print("\n[测试1] 检查位置控制组件...")

    # 查找目标位置输入框
    target_pos_spin = panel._target_pos_spin if hasattr(panel, '_target_pos_spin') else None
    # 查找移动速度输入框
    pos_speed_spin = panel._pos_speed_spin if hasattr(panel, '_pos_speed_spin') else None
    # 查找绝对移动按钮
    move_abs_btn = panel._move_abs_btn if hasattr(panel, '_move_abs_btn') else None
    # 查找相对移动按钮
    move_rel_btn = panel._move_rel_btn if hasattr(panel, '_move_rel_btn') else None

    components = {
        "目标位置输入框": target_pos_spin,
        "移动速度输入框": pos_speed_spin,
        "绝对移动按钮": move_abs_btn,
        "相对移动按钮": move_rel_btn,
    }

    all_found = True
    for name, widget in components.items():
        if widget:
            print(f"  ✓ {name}: 存在")
        else:
            print(f"  ✗ {name}: 不存在")
            all_found = False

    test_results.append(("检查位置控制组件", all_found))

    # ==================== 测试2: 连接设备并使能 ====================
    print("\n[测试2] 连接设备并使能...")

    try:
        service.connect(port="/dev/ttyUSB0", baudrate=115200)
        service.current_axis = AxisName.Z3
        time.sleep(0.3)

        # 使能电机
        service.enable()
        time.sleep(0.5)

        status = service.get_axis_status()
        if status.is_enabled:
            print(f"  ✓ 电机已使能")
            test_results.append(("连接并使能", True))
        else:
            print(f"  ✗ 电机未使能")
            test_results.append(("连接并使能", False))
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        test_results.append(("连接并使能", False))
        service = None

    # ==================== 测试3: 设置目标位置 ====================
    print("\n[测试3] 设置目标位置...")

    if target_pos_spin:
        initial_pos = target_pos_spin.value()
        print(f"  初始位置: {initial_pos} mm")

        # 设置新位置
        target_pos_spin.setValue(10.0)
        QApplication.processEvents()

        new_pos = target_pos_spin.value()
        print(f"  设置位置: 10.0 mm")
        print(f"  实际位置: {new_pos} mm")

        # 检查范围
        print(f"  位置范围: {target_pos_spin.minimum()} - {target_pos_spin.maximum()} mm")

        test_results.append(("设置目标位置", abs(new_pos - 10.0) < 0.001))
    else:
        test_results.append(("设置目标位置", False))

    # ==================== 测试4: 设置移动速度 ====================
    print("\n[测试4] 设置移动速度...")

    if pos_speed_spin:
        initial_speed = pos_speed_spin.value()
        print(f"  初始速度: {initial_speed} mm/s")

        # 设置新速度
        pos_speed_spin.setValue(50.0)
        QApplication.processEvents()

        new_speed = pos_speed_spin.value()
        print(f"  设置速度: 50.0 mm/s")
        print(f"  实际速度: {new_speed} mm/s")

        # 检查范围
        print(f"  速度范围: {pos_speed_spin.minimum()} - {pos_speed_spin.maximum()} mm/s")

        test_results.append(("设置移动速度", abs(new_speed - 50.0) < 0.001))
    else:
        test_results.append(("设置移动速度", False))

    # ==================== 测试5: 绝对位置移动 ====================
    print("\n[测试5] 绝对位置移动...")

    if service and service.is_connected and move_abs_btn:
        try:
            # 获取当前位置
            initial_position = service.get_position()
            print(f"  初始位置: {initial_position:.3f} mm")

            # 设置目标位置 (相对当前位置 +5mm)
            target = initial_position + 5.0
            if target > 95:  # 保持在安全范围内
                target = initial_position - 5.0

            target_pos_spin.setValue(target)
            pos_speed_spin.setValue(50.0)
            print(f"  目标位置: {target:.3f} mm")
            print(f"  移动速度: 50.0 mm/s")

            QApplication.processEvents()

            # 点击绝对移动按钮
            QTest.mouseClick(move_abs_btn, Qt.LeftButton)
            print(f"  点击绝对移动按钮")

            # 等待运动完成 (持续处理事件)
            for i in range(60):  # 最多等待 6 秒
                time.sleep(0.1)
                QApplication.processEvents()
                # 检查是否到达目标
                current = service.get_position()
                if abs(current - target) < 0.1:
                    print(f"  第 {i*0.1:.1f} 秒: 到达目标")
                    break

            # 获取新位置
            new_position = service.get_position()
            position_error = abs(new_position - target)
            print(f"  新位置: {new_position:.3f} mm")
            print(f"  位置误差: {position_error:.3f} mm")

            # 位置误差应小于 0.1mm
            if position_error < 0.1:
                print(f"  ✓ 绝对移动成功")
                test_results.append(("绝对位置移动", True))
            else:
                print(f"  ✗ 位置误差过大")
                test_results.append(("绝对位置移动", False))
        except Exception as e:
            print(f"  ✗ 绝对移动失败: {e}")
            test_results.append(("绝对位置移动", False))
    else:
        print("  跳过 (未连接或组件不存在)")
        test_results.append(("绝对位置移动", False))

    # ==================== 测试6: 相对位置移动 ====================
    print("\n[测试6] 相对位置移动...")

    if service and service.is_connected and move_rel_btn:
        try:
            # 获取当前位置
            initial_position = service.get_position()
            print(f"  初始位置: {initial_position:.3f} mm")

            # 设置相对移动距离
            rel_distance = -3.0  # 负向移动 3mm
            if initial_position < 5:  # 如果接近下限，改为正向移动
                rel_distance = 3.0

            target_pos_spin.setValue(rel_distance)
            pos_speed_spin.setValue(50.0)
            print(f"  相对距离: {rel_distance:.3f} mm")
            print(f"  移动速度: 50.0 mm/s")

            expected_position = initial_position + rel_distance
            print(f"  预期位置: {expected_position:.3f} mm")

            QApplication.processEvents()

            # 点击相对移动按钮
            QTest.mouseClick(move_rel_btn, Qt.LeftButton)
            print(f"  点击相对移动按钮")

            # 等待运动完成 (持续处理事件)
            for i in range(40):  # 最多等待 4 秒
                time.sleep(0.1)
                QApplication.processEvents()
                # 检查是否到达目标
                current = service.get_position()
                if abs(current - expected_position) < 0.1:
                    print(f"  第 {i*0.1:.1f} 秒: 到达目标")
                    break

            # 获取新位置
            new_position = service.get_position()
            position_error = abs(new_position - expected_position)
            print(f"  新位置: {new_position:.3f} mm")
            print(f"  位置误差: {position_error:.3f} mm")

            # 位置误差应小于 0.1mm
            if position_error < 0.1:
                print(f"  ✓ 相对移动成功")
                test_results.append(("相对位置移动", True))
            else:
                print(f"  ✗ 位置误差过大")
                test_results.append(("相对位置移动", False))
        except Exception as e:
            print(f"  ✗ 相对移动失败: {e}")
            test_results.append(("相对位置移动", False))
    else:
        print("  跳过 (未连接或组件不存在)")
        test_results.append(("相对位置移动", False))

    # ==================== 测试7: 快速定位按钮 ====================
    print("\n[测试7] 快速定位按钮...")

    # 查找快速定位按钮
    preset_btns = {}
    for btn in panel.findChildren(QPushButton):
        if btn.text() == "最小":
            preset_btns["最小"] = btn
        elif btn.text() == "中点":
            preset_btns["中点"] = btn
        elif btn.text() == "最大":
            preset_btns["最大"] = btn

    if len(preset_btns) == 3:
        print(f"  ✓ 快速定位按钮存在: {list(preset_btns.keys())}")
        test_results.append(("快速定位按钮", True))
    else:
        print(f"  ✗ 快速定位按钮不完整: {list(preset_btns.keys())}")
        test_results.append(("快速定位按钮", False))

    # ==================== 测试8: 中点定位测试 ====================
    print("\n[测试8] 中点定位测试...")

    if service and service.is_connected and "中点" in preset_btns:
        try:
            # 获取轴配置
            config = service.get_axis_config()
            mid_position = (config.stroke_min + config.stroke_max) / 2
            print(f"  行程范围: {config.stroke_min} - {config.stroke_max} mm")
            print(f"  中点位置: {mid_position:.3f} mm")

            # 获取当前位置
            initial_position = service.get_position()
            print(f"  当前位置: {initial_position:.3f} mm")

            # 点击中点按钮
            QTest.mouseClick(preset_btns["中点"], Qt.LeftButton)
            print(f"  点击中点按钮")

            # 等待运动完成 (持续处理事件)
            for i in range(100):  # 最多等待 10 秒 (中点距离较远)
                time.sleep(0.1)
                QApplication.processEvents()
                # 检查是否到达目标
                current = service.get_position()
                if abs(current - mid_position) < 0.5:
                    print(f"  第 {i*0.1:.1f} 秒: 到达目标")
                    break
                if i % 10 == 0 and i > 0:
                    print(f"  第 {i*0.1:.1f} 秒: 当前位置 {current:.3f} mm")

            # 获取新位置
            new_position = service.get_position()
            position_error = abs(new_position - mid_position)
            print(f"  新位置: {new_position:.3f} mm")
            print(f"  位置误差: {position_error:.3f} mm")

            # 位置误差应小于 0.5mm
            if position_error < 0.5:
                print(f"  ✓ 中点定位成功")
                test_results.append(("中点定位测试", True))
            else:
                print(f"  ✗ 位置误差过大")
                test_results.append(("中点定位测试", False))
        except Exception as e:
            print(f"  ✗ 中点定位失败: {e}")
            test_results.append(("中点定位测试", False))
    else:
        print("  跳过 (未连接或按钮不存在)")
        test_results.append(("中点定位测试", False))

    # ==================== 清理 ====================
    print("\n[清理] 禁用电机...")

    if service and service.is_connected:
        try:
            service.disable()
            time.sleep(0.3)
            service.disconnect()
            print("  已禁用并断开连接")
        except Exception as e:
            print(f"  清理失败: {e}")

    panel.close()

    # ==================== 测试汇总 ====================
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    for name, result in test_results:
        status = "通过" if result else "失败"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {name}: {status}")
        if result:
            passed += 1

    print("-" * 60)
    print(f"总计: {passed}/{len(test_results)} 通过")
    print("=" * 60)

    return test_results


if __name__ == "__main__":
    results = run_test()

    # 生成测试报告
    passed = sum(1 for _, r in results if r)
    total = len(results)

    report = f"""# 测试报告: TC-L5-007 位置移动测试

## 测试信息

| 项目 | 内容 |
|------|------|
| 测试用例编号 | TC-L5-007 |
| 测试名称 | 位置移动测试 |
| 测试层级 | Layer 5 - 应用层 (GUI) |
| 测试日期 | 2026-01-12 |
| 测试环境 | PyQt5 GUI 应用程序 |
| 测试设备 | /dev/ttyUSB0 (FT232R USB UART) |

---

## 测试目的

验证运动控制面板的位置移动功能：
- 目标位置输入
- 移动速度设置
- 绝对位置移动
- 相对位置移动
- 快速定位按钮

---

## 测试结果汇总

| 序号 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
"""

    for i, (name, result) in enumerate(results, 1):
        status = "**通过**" if result else "**失败**"
        report += f"| {i} | {name} | {status} | |\n"

    report += f"""
**总计: {passed}/{total} 通过，通过率 {passed*100//total}%**

---

## 结论

**测试结果: {"通过" if passed == total else "部分通过"}**

TC-L5-007 位置移动测试{"全部通过" if passed == total else f"通过 {passed}/{total}"}。

---

*测试报告生成于 2026-01-12*
"""

    # 保存报告
    report_path = "/home/hds/codes/ServoMotorCreate/CreateServoMotor/docs/test_results/TC-L5-007_位置移动测试.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n测试报告已保存到: {report_path}")
