#!/usr/bin/env python3
"""
TC-L5-010: 菜单功能测试

测试主窗口的菜单功能:
- 文件菜单 (退出)
- 连接菜单 (连接/断开)
- 控制菜单 (使能/禁用/停止/快速停止/回零)
- 帮助菜单 (关于)
"""

import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QMenuBar

# 添加项目路径
sys.path.insert(0, "/home/hds/codes/ServoMotorCreate/CreateServoMotor")

from app.main_window import MainWindow


def run_test():
    """执行测试"""
    app = QApplication(sys.argv)

    print("=" * 60)
    print("TC-L5-010: 菜单功能测试")
    print("=" * 60)

    test_results = []

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 处理事件
    QApplication.processEvents()
    time.sleep(0.5)

    # ==================== 测试1: 检查菜单栏 ====================
    print("\n[测试1] 检查菜单栏...")

    menubar = window.menuBar()
    if menubar:
        print(f"  ✓ 菜单栏存在")

        # 获取所有菜单
        menus = []
        for action in menubar.actions():
            if action.menu():
                menus.append(action.text())

        print(f"  菜单项: {menus}")
        test_results.append(("检查菜单栏", len(menus) >= 4))
    else:
        print(f"  ✗ 菜单栏不存在")
        test_results.append(("检查菜单栏", False))

    # ==================== 测试2: 文件菜单 ====================
    print("\n[测试2] 文件菜单...")

    file_menu = None
    for action in menubar.actions():
        if "文件" in action.text():
            file_menu = action.menu()
            break

    if file_menu:
        print(f"  ✓ 文件菜单存在")

        # 查找退出动作
        exit_action = None
        for action in file_menu.actions():
            if "退出" in action.text():
                exit_action = action
                break

        if exit_action:
            print(f"  ✓ 退出动作存在")
            print(f"    文本: {exit_action.text()}")
            print(f"    快捷键: {exit_action.shortcut().toString()}")
            test_results.append(("文件菜单", True))
        else:
            print(f"  ✗ 退出动作不存在")
            test_results.append(("文件菜单", False))
    else:
        print(f"  ✗ 文件菜单不存在")
        test_results.append(("文件菜单", False))

    # ==================== 测试3: 连接菜单 ====================
    print("\n[测试3] 连接菜单...")

    connect_menu = None
    for action in menubar.actions():
        if "连接" in action.text():
            connect_menu = action.menu()
            break

    if connect_menu:
        print(f"  ✓ 连接菜单存在")

        # 检查连接和断开动作
        connect_action = None
        disconnect_action = None

        for action in connect_menu.actions():
            text = action.text()
            if "连接" in text and "断" not in text:
                connect_action = action
            elif "断开" in text:
                disconnect_action = action

        actions_found = []
        if connect_action:
            actions_found.append(f"连接 ({connect_action.shortcut().toString()})")
        if disconnect_action:
            actions_found.append(f"断开 ({disconnect_action.shortcut().toString()})")

        print(f"  动作: {actions_found}")
        test_results.append(("连接菜单", connect_action is not None and disconnect_action is not None))
    else:
        print(f"  ✗ 连接菜单不存在")
        test_results.append(("连接菜单", False))

    # ==================== 测试4: 控制菜单 ====================
    print("\n[测试4] 控制菜单...")

    control_menu = None
    for action in menubar.actions():
        if "控制" in action.text():
            control_menu = action.menu()
            break

    if control_menu:
        print(f"  ✓ 控制菜单存在")

        # 检查控制动作
        control_actions = []
        for action in control_menu.actions():
            if not action.isSeparator():
                shortcut = action.shortcut().toString()
                if shortcut:
                    control_actions.append(f"{action.text()} ({shortcut})")
                else:
                    control_actions.append(action.text())

        print(f"  动作数量: {len(control_actions)}")
        for a in control_actions:
            print(f"    - {a}")

        # 应该至少有: 使能、禁用、停止、快速停止、回零
        test_results.append(("控制菜单", len(control_actions) >= 5))
    else:
        print(f"  ✗ 控制菜单不存在")
        test_results.append(("控制菜单", False))

    # ==================== 测试5: 帮助菜单 ====================
    print("\n[测试5] 帮助菜单...")

    help_menu = None
    for action in menubar.actions():
        if "帮助" in action.text():
            help_menu = action.menu()
            break

    if help_menu:
        print(f"  ✓ 帮助菜单存在")

        # 查找关于动作
        about_action = None
        for action in help_menu.actions():
            if "关于" in action.text():
                about_action = action
                break

        if about_action:
            print(f"  ✓ 关于动作存在")
            print(f"    文本: {about_action.text()}")
            test_results.append(("帮助菜单", True))
        else:
            print(f"  ✗ 关于动作不存在")
            test_results.append(("帮助菜单", False))
    else:
        print(f"  ✗ 帮助菜单不存在")
        test_results.append(("帮助菜单", False))

    # ==================== 测试6: 快捷键检查 ====================
    print("\n[测试6] 快捷键检查...")

    expected_shortcuts = {
        "退出": "Ctrl+Q",
        "连接": "Ctrl+O",
        "断开": "Ctrl+D",
        "使能": "Ctrl+E",
        "停止": "Space",
        "快速停止": "Escape",
        "回零": "Ctrl+H",
    }

    shortcuts_found = {}
    all_menus = [file_menu, connect_menu, control_menu, help_menu]

    for menu in all_menus:
        if menu:
            for action in menu.actions():
                text = action.text().replace("&", "")
                shortcut = action.shortcut().toString()
                if shortcut:
                    # 简化文本匹配
                    for key in expected_shortcuts:
                        if key in text:
                            shortcuts_found[key] = shortcut
                            break

    print(f"  找到的快捷键:")
    for name, shortcut in shortcuts_found.items():
        expected = expected_shortcuts.get(name, "")
        match = "✓" if shortcut == expected else "✗"
        print(f"    {match} {name}: {shortcut} (预期: {expected})")

    # 检查是否所有关键快捷键都存在
    key_shortcuts = ["退出", "连接", "使能", "停止", "回零"]
    all_found = all(k in shortcuts_found for k in key_shortcuts)
    test_results.append(("快捷键检查", all_found))

    # ==================== 测试7: 状态栏检查 ====================
    print("\n[测试7] 状态栏检查...")

    statusbar = window.statusBar()
    if statusbar:
        message = statusbar.currentMessage()
        print(f"  ✓ 状态栏存在")
        print(f"  当前消息: {message}")
        test_results.append(("状态栏检查", True))
    else:
        print(f"  ✗ 状态栏不存在")
        test_results.append(("状态栏检查", False))

    # ==================== 测试8: 窗口标题和大小 ====================
    print("\n[测试8] 窗口标题和大小...")

    title = window.windowTitle()
    size = window.size()
    min_size = window.minimumSize()

    print(f"  窗口标题: {title}")
    print(f"  窗口大小: {size.width()} x {size.height()}")
    print(f"  最小大小: {min_size.width()} x {min_size.height()}")

    if "NiMotion" in title and size.width() >= 1024 and size.height() >= 700:
        print(f"  ✓ 窗口配置正确")
        test_results.append(("窗口标题和大小", True))
    else:
        print(f"  ✗ 窗口配置异常")
        test_results.append(("窗口标题和大小", False))

    # ==================== 测试9: 面板存在性检查 ====================
    print("\n[测试9] 面板存在性检查...")

    panels = {
        "连接面板": hasattr(window, '_connection_panel') and window._connection_panel is not None,
        "轴选择面板": hasattr(window, '_axis_panel') and window._axis_panel is not None,
        "状态面板": hasattr(window, '_status_panel') and window._status_panel is not None,
        "运动控制面板": hasattr(window, '_motion_panel') and window._motion_panel is not None,
        "参数面板": hasattr(window, '_parameter_panel') and window._parameter_panel is not None,
    }

    all_panels_exist = True
    for name, exists in panels.items():
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {name}: {'存在' if exists else '不存在'}")
        if not exists:
            all_panels_exist = False

    test_results.append(("面板存在性检查", all_panels_exist))

    # ==================== 清理 ====================
    print("\n[清理] 关闭窗口...")

    window.close()
    QApplication.processEvents()
    print("  窗口已关闭")

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

    report = f"""# 测试报告: TC-L5-010 菜单功能测试

## 测试信息

| 项目 | 内容 |
|------|------|
| 测试用例编号 | TC-L5-010 |
| 测试名称 | 菜单功能测试 |
| 测试层级 | Layer 5 - 应用层 (GUI) |
| 测试日期 | 2026-01-12 |
| 测试环境 | PyQt5 GUI 应用程序 |

---

## 测试目的

验证主窗口的菜单功能：
- 文件菜单 (退出)
- 连接菜单 (连接/断开)
- 控制菜单 (使能/禁用/停止/快速停止/回零)
- 帮助菜单 (关于)
- 快捷键
- 状态栏
- 窗口配置

---

## 测试结果汇总

| 序号 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
"""

    for i, (name, result) in enumerate(results, 1):
        status = "**通过**" if result else "**失败**"
        report += f"| {i} | {name} | {status} | |\n"

    report += f"""
**总计: {passed}/{total} 通过，通过率 {passed*100//total if total > 0 else 0}%**

---

## 结论

**测试结果: {"通过" if passed == total else "部分通过"}**

TC-L5-010 菜单功能测试{"全部通过" if passed == total else f"通过 {passed}/{total}"}。

---

*测试报告生成于 2026-01-12*
"""

    # 保存报告
    report_path = "/home/hds/codes/ServoMotorCreate/CreateServoMotor/docs/test_results/TC-L5-010_菜单功能测试.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n测试报告已保存到: {report_path}")
