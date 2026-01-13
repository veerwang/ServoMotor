#!/usr/bin/env python3
"""
GUI 界面综合性自动化测试

测试 UI 界面上所有按键功能和参数是否符合预期。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

from servo_service import ServoService, AxisName
from app.main_window import MainWindow

# 测试结果
test_results = []

def auto_close_message_boxes():
    """自动关闭所有弹出的消息框"""
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMessageBox):
            widget.accept()  # 点击确定/关闭

# 全局定时器，每 200ms 检查并关闭弹窗
_auto_close_timer = None

def start_auto_close_timer():
    """启动自动关闭弹窗的定时器"""
    global _auto_close_timer
    _auto_close_timer = QTimer()
    _auto_close_timer.timeout.connect(auto_close_message_boxes)
    _auto_close_timer.start(2000)  # 每 2000ms 检查一次 (让弹窗显示 2 秒)

def stop_auto_close_timer():
    """停止自动关闭弹窗的定时器"""
    global _auto_close_timer
    if _auto_close_timer:
        _auto_close_timer.stop()
        _auto_close_timer = None

def log_test(name, passed, details=""):
    """记录测试结果"""
    status = "✓ PASS" if passed else "✗ FAIL"
    test_results.append({"name": name, "passed": passed, "details": details})
    print(f"  {status}: {name}")
    if details:
        print(f"         {details}")

def log_section(title):
    """打印测试章节"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

class GUITester:
    """GUI 测试器"""

    def __init__(self, window: MainWindow):
        self.window = window
        self.service = window._service

    def wait_ms(self, ms):
        """等待指定毫秒，并自动关闭弹窗"""
        # 分段等待，每 100ms 检查一次弹窗
        elapsed = 0
        while elapsed < ms:
            QTest.qWait(100)
            auto_close_message_boxes()
            elapsed += 100

    def get_position(self):
        """获取当前位置"""
        return self.service.get_position()

    def get_velocity(self):
        """获取当前速度"""
        return self.service.get_velocity()

    def clear_serial_buffer(self):
        """清空串口缓冲区"""
        try:
            serial = self.service._modbus_client._serial
            if hasattr(serial, '_serial') and serial._serial:
                serial._serial.reset_input_buffer()
                serial._serial.reset_output_buffer()
        except:
            pass
        self.wait_ms(100)

    # ==================== 连接面板测试 ====================

    def test_connection_panel(self):
        """测试连接面板"""
        log_section("1. 连接面板测试")

        panel = self.window._connection_panel

        # 测试连接按钮
        try:
            panel._connect_btn.click()
            self.wait_ms(1000)
            connected = self.service.is_connected
            log_test("点击连接按钮", connected,
                    f"连接状态: {'已连接' if connected else '未连接'}")
        except Exception as e:
            log_test("点击连接按钮", False, str(e))

        # 验证连接后状态
        if self.service.is_connected:
            try:
                status_text = self.window._status_panel._state_label.text()
                has_status = len(status_text) > 0
                log_test("状态面板更新", has_status, f"状态: {status_text}")
            except Exception as e:
                log_test("状态面板更新", False, str(e))

    # ==================== 轴选择面板测试 ====================

    def test_axis_panel(self):
        """测试轴选择面板"""
        log_section("2. 轴选择面板测试")

        panel = self.window._axis_panel

        # 测试 Z 轴选择 (通过 set_current_axis 方法)
        try:
            panel.set_current_axis(AxisName.Z)
            self.wait_ms(200)
            current_axis = self.service.current_axis
            passed = current_axis == AxisName.Z
            log_test("选择 Z 轴", passed, f"当前轴: {current_axis.value}")
        except Exception as e:
            log_test("选择 Z 轴", False, str(e))

    # ==================== 运动参数面板测试 ====================

    def test_parameter_panel(self):
        """测试运动参数面板"""
        log_section("3. 运动参数面板测试")

        panel = self.window._parameter_panel
        motion_panel = self.window._motion_panel

        # 测试设置速度
        try:
            test_velocity = 80.0
            panel._velocity_spin.setValue(test_velocity)
            self.wait_ms(100)
            ui_value = panel._velocity_spin.value()
            log_test("设置速度控件值", abs(ui_value - test_velocity) < 0.1,
                    f"设置: {test_velocity}, UI显示: {ui_value}")
        except Exception as e:
            log_test("设置速度控件值", False, str(e))

        # 测试设置加速度
        try:
            test_accel = 300.0
            panel._accel_spin.setValue(test_accel)
            self.wait_ms(100)
            ui_value = panel._accel_spin.value()
            log_test("设置加速度控件值", abs(ui_value - test_accel) < 0.1,
                    f"设置: {test_accel}, UI显示: {ui_value}")
        except Exception as e:
            log_test("设置加速度控件值", False, str(e))

        # 测试设置减速度
        try:
            test_decel = 300.0
            panel._decel_spin.setValue(test_decel)
            self.wait_ms(100)
            ui_value = panel._decel_spin.value()
            log_test("设置减速度控件值", abs(ui_value - test_decel) < 0.1,
                    f"设置: {test_decel}, UI显示: {ui_value}")
        except Exception as e:
            log_test("设置减速度控件值", False, str(e))

        # 测试应用参数按钮
        try:
            panel._apply_btn.click()
            self.wait_ms(500)

            # 验证参数是否写入驱动器
            read_velocity = self.service.get_profile_velocity()
            passed = abs(read_velocity - test_velocity) < 5.0
            log_test("应用参数按钮", passed,
                    f"设置速度: {test_velocity}, 驱动器读取: {read_velocity:.1f}")
        except Exception as e:
            log_test("应用参数按钮", False, str(e))

        # 测试参数同步到运动面板
        try:
            jog_speed = motion_panel._jog_speed_spin.value()
            pos_speed = motion_panel._pos_speed_spin.value()
            synced = abs(jog_speed - test_velocity) < 0.1 and abs(pos_speed - test_velocity) < 0.1
            log_test("参数同步到运动面板", synced,
                    f"点动速度: {jog_speed}, 位置速度: {pos_speed}")
        except Exception as e:
            log_test("参数同步到运动面板", False, str(e))

        # 测试读取当前参数按钮
        try:
            panel._read_btn.click()
            self.wait_ms(500)
            # 验证 UI 显示的值是从驱动器读取的
            ui_velocity = panel._velocity_spin.value()
            driver_velocity = self.service.get_profile_velocity()
            passed = abs(ui_velocity - driver_velocity) < 5.0
            log_test("读取当前参数按钮", passed,
                    f"UI显示: {ui_velocity:.1f}, 驱动器: {driver_velocity:.1f}")
        except Exception as e:
            log_test("读取当前参数按钮", False, str(e))

        # 测试加载默认值按钮
        try:
            panel._load_default_btn.click()
            self.wait_ms(200)
            config = self.service.get_axis_config()
            ui_velocity = panel._velocity_spin.value()
            passed = abs(ui_velocity - config.default_velocity) < 0.1
            log_test("加载默认值按钮", passed,
                    f"UI速度: {ui_velocity}, 默认速度: {config.default_velocity}")
        except Exception as e:
            log_test("加载默认值按钮", False, str(e))

    # ==================== 运动控制面板测试 ====================

    def test_motion_panel_enable(self):
        """测试使能/禁用按钮"""
        log_section("4. 使能/禁用按钮测试")

        panel = self.window._motion_panel

        # 测试使能按钮
        try:
            panel._enable_btn.click()
            self.wait_ms(500)
            status = self.service.get_axis_status()
            state_str = str(status.state).lower()
            enabled = "enabled" in state_str or "operation" in state_str
            log_test("使能按钮", enabled, f"状态: {status.state}")
        except Exception as e:
            log_test("使能按钮", False, str(e))

        # 测试禁用按钮
        try:
            panel._disable_btn.click()
            self.wait_ms(500)
            status = self.service.get_axis_status()
            state_str = str(status.state).lower()
            disabled = "disabled" in state_str or "switched" in state_str or "ready" in state_str
            log_test("禁用按钮", disabled, f"状态: {status.state}")
        except Exception as e:
            log_test("禁用按钮", False, str(e))

        # 重新使能
        panel._enable_btn.click()
        self.wait_ms(800)

    def test_motion_panel_jog(self):
        """测试点动功能"""
        log_section("5. 点动功能测试")

        panel = self.window._motion_panel

        # 清空缓冲区并确保使能
        self.clear_serial_buffer()
        panel._enable_btn.click()
        self.wait_ms(500)

        # 设置点动速度
        panel._jog_speed_spin.setValue(30.0)
        self.wait_ms(200)

        # 测试正向点动按钮
        try:
            start_pos = self.get_position()

            # 模拟按下正向按钮
            QTest.mousePress(panel._jog_pos_btn, Qt.LeftButton)
            self.wait_ms(500)
            QTest.mouseRelease(panel._jog_pos_btn, Qt.LeftButton)
            self.wait_ms(300)

            end_pos = self.get_position()
            moved = abs(end_pos - start_pos) > 1.0
            log_test("正向点动按钮 (按下/松开)", moved,
                    f"起始: {start_pos:.2f}mm, 结束: {end_pos:.2f}mm, 移动: {end_pos-start_pos:.2f}mm")
        except Exception as e:
            log_test("正向点动按钮", False, str(e))

        # 测试负向点动按钮
        try:
            start_pos = self.get_position()

            QTest.mousePress(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(500)
            QTest.mouseRelease(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(300)

            end_pos = self.get_position()
            moved = abs(end_pos - start_pos) > 1.0
            log_test("负向点动按钮 (按下/松开)", moved,
                    f"起始: {start_pos:.2f}mm, 结束: {end_pos:.2f}mm, 移动: {end_pos-start_pos:.2f}mm")
        except Exception as e:
            log_test("负向点动按钮", False, str(e))

        # 测试点动停止 - 松开后电机应停止
        try:
            QTest.mousePress(panel._jog_pos_btn, Qt.LeftButton)
            self.wait_ms(300)
            QTest.mouseRelease(panel._jog_pos_btn, Qt.LeftButton)

            pos_at_release = self.get_position()
            self.wait_ms(500)
            pos_after_wait = self.get_position()

            stopped = abs(pos_after_wait - pos_at_release) < 2.0  # 考虑减速惯性
            log_test("点动松开后停止", stopped,
                    f"松开时: {pos_at_release:.2f}mm, 0.5秒后: {pos_after_wait:.2f}mm")
        except Exception as e:
            log_test("点动松开后停止", False, str(e))

    def test_motion_panel_step(self):
        """测试步进移动功能"""
        log_section("6. 步进移动功能测试")

        panel = self.window._motion_panel

        # 清空缓冲区确保通信稳定
        self.clear_serial_buffer()

        # 设置步进距离
        step_distance = 2.0
        panel._step_spin.setValue(step_distance)
        self.wait_ms(200)

        # 测试 + 步进按钮
        try:
            start_pos = self.get_position()

            panel._step_pos_btn.click()
            self.wait_ms(3000)  # 等待运动完成

            end_pos = self.get_position()
            actual_move = end_pos - start_pos
            error = abs(actual_move - step_distance)
            passed = error < 0.2
            log_test("+ 步进按钮", passed,
                    f"目标: +{step_distance}mm, 实际: {actual_move:.3f}mm, 误差: {error:.3f}mm")
        except Exception as e:
            log_test("+ 步进按钮", False, str(e))

        # 测试 - 步进按钮
        try:
            start_pos = self.get_position()

            panel._step_neg_btn.click()
            self.wait_ms(3000)

            end_pos = self.get_position()
            actual_move = end_pos - start_pos
            error = abs(actual_move - (-step_distance))
            passed = error < 0.2
            log_test("- 步进按钮", passed,
                    f"目标: -{step_distance}mm, 实际: {actual_move:.3f}mm, 误差: {error:.3f}mm")
        except Exception as e:
            log_test("- 步进按钮", False, str(e))

    def test_motion_panel_position(self):
        """测试位置移动功能"""
        log_section("7. 位置移动功能测试")

        panel = self.window._motion_panel

        # 清空缓冲区确保通信稳定
        self.clear_serial_buffer()

        # 设置目标位置和速度
        panel._target_pos_spin.setValue(15.0)
        panel._pos_speed_spin.setValue(50.0)
        self.wait_ms(200)

        # 测试绝对移动按钮
        try:
            target_pos = 15.0
            panel._target_pos_spin.setValue(target_pos)

            panel._move_abs_btn.click()
            self.wait_ms(5000)  # 等待运动完成

            actual_pos = self.get_position()
            error = abs(actual_pos - target_pos)
            passed = error < 0.2
            log_test("绝对移动按钮", passed,
                    f"目标: {target_pos}mm, 实际: {actual_pos:.3f}mm, 误差: {error:.3f}mm")
        except Exception as e:
            log_test("绝对移动按钮", False, str(e))

        # 测试相对移动按钮
        try:
            start_pos = self.get_position()
            rel_distance = 5.0
            panel._target_pos_spin.setValue(rel_distance)

            panel._move_rel_btn.click()
            self.wait_ms(5000)

            end_pos = self.get_position()
            actual_move = end_pos - start_pos
            error = abs(actual_move - rel_distance)
            passed = error < 0.2
            log_test("相对移动按钮", passed,
                    f"目标: +{rel_distance}mm, 实际移动: {actual_move:.3f}mm, 误差: {error:.3f}mm")
        except Exception as e:
            log_test("相对移动按钮", False, str(e))

    def test_motion_panel_stop(self):
        """测试停止按钮"""
        log_section("8. 停止按钮测试")

        panel = self.window._motion_panel

        # 清空缓冲区确保通信稳定
        self.clear_serial_buffer()

        # 设置较慢的速度以便测试停止
        panel._pos_speed_spin.setValue(10.0)  # 10 mm/s (更慢)
        self.wait_ms(200)

        # 测试停止按钮 (向负方向移动，避免超出行程)
        try:
            # 先移动到 55mm 位置
            self.service.move_to(55.0, velocity_mm_s=80.0)
            self.wait_ms(500)

            start_pos = self.get_position()
            target_pos = 5.0  # 目标位置 5mm，向负方向移动约 50mm

            # 开始长距离移动
            panel._target_pos_spin.setValue(target_pos)
            panel._move_abs_btn.click()
            self.wait_ms(1500)  # 以 10mm/s 计，1500ms 移动约 15mm

            # 点击停止
            panel._stop_btn.click()
            self.wait_ms(500)

            final_pos = self.get_position()
            moved = abs(final_pos - start_pos) > 5.0  # 移动了超过 5mm
            not_reached = abs(final_pos - target_pos) > 5.0  # 离目标还有超过 5mm
            passed = moved and not_reached
            log_test("停止按钮", passed,
                    f"起始: {start_pos:.2f}mm, 停止: {final_pos:.2f}mm, 目标: {target_pos:.2f}mm")
        except Exception as e:
            log_test("停止按钮", False, str(e))

        # 测试急停按钮
        try:
            start_pos = self.get_position()

            panel._target_pos_spin.setValue(start_pos + 30.0)
            panel._move_abs_btn.click()
            self.wait_ms(300)

            panel._quick_stop_btn.click()
            self.wait_ms(500)

            final_pos = self.get_position()
            log_test("急停按钮", True, f"停止位置: {final_pos:.2f}mm")
        except Exception as e:
            log_test("急停按钮", False, str(e))

    def test_sequence_operations(self):
        """测试操作序列"""
        log_section("9. 操作序列测试 (点动后其他操作)")

        panel = self.window._motion_panel

        # 清空串口缓冲区，确保干净的通信环境
        try:
            serial = self.service._modbus_client._serial
            if hasattr(serial, '_serial') and serial._serial:
                serial._serial.reset_input_buffer()
                serial._serial.reset_output_buffer()
        except:
            pass
        self.wait_ms(300)

        # 重新使能
        panel._enable_btn.click()
        self.wait_ms(800)

        # 点动后步进
        try:
            # 先移动到安全位置 (30mm)
            self.service.move_to(30.0, velocity_mm_s=80.0)
            self.wait_ms(500)

            # 使用 stop(wait=True) 确保电机稳定
            try:
                self.service.stop(wait=True)
            except:
                pass
            self.wait_ms(300)

            # 记录点动前位置
            pos_before_jog = self.get_position()

            # 负向点动 (短时间)
            QTest.mousePress(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(200)
            QTest.mouseRelease(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(1000)

            # 使用 stop(wait=True) 确保完全停止并清除 Halt
            try:
                self.service.stop(wait=True)
            except:
                pass
            self.wait_ms(300)

            # 重新使能，确保可以执行下一个运动
            try:
                self.service.enable()
            except:
                pass
            self.wait_ms(300)

            # 清理通信缓冲区
            self.clear_serial_buffer()
            self.wait_ms(100)

            # 读取起始位置
            start_pos = self.get_position()
            print(f"    [调试] 起始位置: {start_pos:.3f}mm")

            # 执行步进移动 (正向 2mm)
            step_distance = 2.0
            move_success = False
            try:
                self.service.move_by(step_distance, velocity_mm_s=50.0)
                move_success = True
                print(f"    [调试] move_by 执行成功")
            except Exception as e:
                print(f"    [调试] move_by 异常: {e}")

            # 读取结束位置
            end_pos = self.get_position()
            print(f"    [调试] 结束位置: {end_pos:.3f}mm")

            actual_move = end_pos - start_pos
            passed = abs(actual_move - step_distance) < 0.3 and move_success
            log_test("点动后步进移动", passed,
                    f"目标: {step_distance}mm, 实际: {actual_move:.3f}mm")
        except Exception as e:
            log_test("点动后步进移动", False, str(e))

        # 点动后绝对移动
        try:
            # 先点动
            QTest.mousePress(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(400)
            QTest.mouseRelease(panel._jog_neg_btn, Qt.LeftButton)
            self.wait_ms(1000)  # 等待电机完全停止

            # 然后绝对移动
            target = 10.0
            panel._target_pos_spin.setValue(target)
            panel._move_abs_btn.click()
            self.wait_ms(5000)

            actual_pos = self.get_position()
            passed = abs(actual_pos - target) < 0.2
            log_test("点动后绝对移动", passed,
                    f"目标: {target}mm, 实际: {actual_pos:.3f}mm")
        except Exception as e:
            log_test("点动后绝对移动", False, str(e))

    def test_view_switching(self):
        """测试视图切换"""
        log_section("10. 视图切换测试")

        try:
            # 切换到 Modbus 调试视图 (索引 1)
            self.window._view_stack.setCurrentIndex(1)
            self.wait_ms(300)
            current_index = self.window._view_stack.currentIndex()
            log_test("切换到 Modbus 调试视图", current_index == 1,
                    f"当前视图索引: {current_index}")
        except Exception as e:
            log_test("切换到 Modbus 调试视图", False, str(e))

        try:
            # 切换回电机控制视图 (索引 0)
            self.window._view_stack.setCurrentIndex(0)
            self.wait_ms(300)
            current_index = self.window._view_stack.currentIndex()
            log_test("切换到电机控制视图", current_index == 0,
                    f"当前视图索引: {current_index}")
        except Exception as e:
            log_test("切换到电机控制视图", False, str(e))

    def test_fault_reset(self):
        """测试故障复位按钮"""
        log_section("11. 故障复位按钮测试")

        panel = self.window._motion_panel

        try:
            panel._fault_reset_btn.click()
            self.wait_ms(500)
            status = self.service.get_axis_status()
            state_str = str(status.state).lower()
            no_fault = "fault" not in state_str
            log_test("故障复位按钮", no_fault, f"状态: {status.state}")
        except Exception as e:
            log_test("故障复位按钮", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        self.test_connection_panel()

        if not self.service.is_connected:
            print("\n无法连接，测试终止")
            return False

        # 暂停状态定时器，避免通信冲突
        print("\n[暂停状态定时器以避免通信冲突]")
        self.window.pause_status_timer()
        self.wait_ms(500)  # 等待定时器完全停止

        # 清空串口缓冲区
        try:
            serial = self.service._modbus_client._serial
            if hasattr(serial, '_serial') and serial._serial:
                serial._serial.reset_input_buffer()
                serial._serial.reset_output_buffer()
                print("[串口缓冲区已清空]")
        except Exception as e:
            print(f"[清空缓冲区失败: {e}]")
        self.wait_ms(200)

        try:
            self.test_axis_panel()
            self.test_parameter_panel()
            self.test_motion_panel_enable()
            self.test_motion_panel_jog()
            self.test_motion_panel_step()
            self.test_motion_panel_position()
            self.test_motion_panel_stop()
            self.test_sequence_operations()
            self.test_view_switching()
            self.test_fault_reset()
        finally:
            # 恢复状态定时器
            print("\n[恢复状态定时器]")
            self.window.resume_status_timer()

        return True


def print_summary():
    """打印测试总结"""
    print(f"\n{'='*70}")
    print(" 测试总结")
    print(f"{'='*70}")

    passed = sum(1 for t in test_results if t["passed"])
    failed = sum(1 for t in test_results if not t["passed"])
    total = len(test_results)

    print(f"\n总计: {total} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")

    if failed > 0:
        print(f"\n失败的测试:")
        for t in test_results:
            if not t["passed"]:
                print(f"  - {t['name']}")
                if t["details"]:
                    print(f"    {t['details']}")

    print(f"\n{'='*70}")
    return failed == 0


def main():
    print("=" * 70)
    print(" GUI 界面综合性自动化测试")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建 Qt 应用
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 创建测试器
    tester = GUITester(window)

    # 启动自动关闭弹窗的定时器
    start_auto_close_timer()

    # 延迟运行测试
    def run_tests():
        try:
            tester.run_all_tests()
        except Exception as e:
            print(f"\n测试过程中发生异常: {e}")
        finally:
            print_summary()

            # 停止自动关闭定时器
            stop_auto_close_timer()

            # 清理
            try:
                tester.service.disable()
            except:
                pass
            try:
                tester.service.disconnect()
            except:
                pass

            print("\n测试完成，3秒后关闭窗口...")
            QTimer.singleShot(3000, app.quit)

    # 1秒后开始测试
    QTimer.singleShot(1000, run_tests)

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
