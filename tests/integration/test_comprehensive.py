#!/usr/bin/env python3
"""
综合性自动化测试脚本

测试所有主要功能，自动判断预期行为并记录异常。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from servo_service import ServoService, AxisName, HomingMethod

# 测试配置
PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
AXIS = AxisName.Z3

# 测试结果
test_results = []

def log_test(name, passed, details=""):
    """记录测试结果"""
    status = "✓ PASS" if passed else "✗ FAIL"
    test_results.append({
        "name": name,
        "passed": passed,
        "details": details
    })
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")

def log_section(title):
    """打印测试章节"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def wait_and_check_position(service, expected_pos, tolerance=0.5, timeout=10):
    """等待并检查位置"""
    start = time.time()
    while time.time() - start < timeout:
        pos = service.get_position()
        if abs(pos - expected_pos) <= tolerance:
            return True, pos
        time.sleep(0.1)
    return False, service.get_position()

def test_connection(service):
    """测试连接"""
    log_section("1. 连接测试")

    try:
        service.connect()
        connected = service.is_connected
        log_test("连接到伺服系统", connected)
        return connected
    except Exception as e:
        log_test("连接到伺服系统", False, str(e))
        return False

def test_status_read(service):
    """测试状态读取"""
    log_section("2. 状态读取测试")

    try:
        pos = service.get_position()
        log_test("读取位置", True, f"位置: {pos:.3f} mm")
    except Exception as e:
        log_test("读取位置", False, str(e))

    try:
        vel = service.get_velocity()
        log_test("读取速度", True, f"速度: {vel:.3f} mm/s")
    except Exception as e:
        log_test("读取速度", False, str(e))

    try:
        status = service.get_axis_status()
        log_test("读取轴状态", True, f"状态: {status}")
    except Exception as e:
        log_test("读取轴状态", False, str(e))

def test_parameter_read_write(service):
    """测试参数读写"""
    log_section("3. 参数读写测试")

    # 测试速度参数
    try:
        # 写入速度
        test_velocity = 50.0
        service.set_velocity(test_velocity)
        time.sleep(0.1)

        # 读取速度
        read_velocity = service.get_profile_velocity()
        tolerance = 1.0  # 允许1mm/s误差
        passed = abs(read_velocity - test_velocity) <= tolerance
        log_test("速度参数读写", passed,
                f"写入: {test_velocity}, 读取: {read_velocity:.1f}")
    except Exception as e:
        log_test("速度参数读写", False, str(e))

    # 测试加速度参数
    try:
        test_accel = 200.0
        service.set_acceleration(test_accel)
        time.sleep(0.1)

        read_accel = service.get_profile_acceleration()
        tolerance = 10.0
        passed = abs(read_accel - test_accel) <= tolerance
        log_test("加速度参数读写", passed,
                f"写入: {test_accel}, 读取: {read_accel:.1f}")
    except Exception as e:
        log_test("加速度参数读写", False, str(e))

    # 测试减速度参数
    try:
        test_decel = 200.0
        service.set_deceleration(test_decel)
        time.sleep(0.1)

        read_decel = service.get_profile_deceleration()
        tolerance = 10.0
        passed = abs(read_decel - test_decel) <= tolerance
        log_test("减速度参数读写", passed,
                f"写入: {test_decel}, 读取: {read_decel:.1f}")
    except Exception as e:
        log_test("减速度参数读写", False, str(e))

def test_enable_disable(service):
    """测试使能/禁用"""
    log_section("4. 使能/禁用测试")

    try:
        service.enable()
        time.sleep(0.5)
        status = service.get_axis_status()
        state_str = str(status.state).lower()
        enabled = "enabled" in state_str or "operation" in state_str
        log_test("使能电机", enabled, f"状态: {status.state}")
    except Exception as e:
        log_test("使能电机", False, str(e))

    try:
        service.disable()
        time.sleep(0.5)
        status = service.get_axis_status()
        state_str = str(status.state).lower()
        disabled = "disabled" in state_str or "switch" in state_str
        log_test("禁用电机", disabled, f"状态: {status.state}")
    except Exception as e:
        log_test("禁用电机", False, str(e))

    # 重新使能以便后续测试
    try:
        service.enable()
        time.sleep(0.5)
    except:
        pass

def test_jog(service):
    """测试点动"""
    log_section("5. 点动测试")

    try:
        # 记录初始位置
        start_pos = service.get_position()

        # 正向点动 0.5 秒
        service.jog(20.0)  # 20 mm/s
        time.sleep(0.5)
        service.stop(wait=False)
        time.sleep(0.3)

        pos_after_jog = service.get_position()
        moved = abs(pos_after_jog - start_pos) > 1.0  # 至少移动 1mm

        log_test("正向点动", moved,
                f"起始: {start_pos:.2f}, 结束: {pos_after_jog:.2f}, 移动: {pos_after_jog-start_pos:.2f} mm")
    except Exception as e:
        log_test("正向点动", False, str(e))

    try:
        # 记录当前位置
        start_pos = service.get_position()

        # 负向点动 0.5 秒
        service.jog(-20.0)  # -20 mm/s
        time.sleep(0.5)
        service.stop(wait=False)
        time.sleep(0.3)

        pos_after_jog = service.get_position()
        moved = abs(pos_after_jog - start_pos) > 1.0

        log_test("负向点动", moved,
                f"起始: {start_pos:.2f}, 结束: {pos_after_jog:.2f}, 移动: {pos_after_jog-start_pos:.2f} mm")
    except Exception as e:
        log_test("负向点动", False, str(e))

def test_jog_stop(service):
    """测试点动停止"""
    log_section("6. 点动停止测试")

    try:
        # 开始点动
        service.jog(30.0)
        time.sleep(0.3)

        # 停止
        service.stop(wait=False)
        time.sleep(0.1)

        # 记录停止后位置
        pos_at_stop = service.get_position()
        time.sleep(0.5)
        pos_after_wait = service.get_position()

        # 检查是否真的停止了（位置不再变化）
        stopped = abs(pos_after_wait - pos_at_stop) < 0.5
        log_test("点动停止", stopped,
                f"停止时: {pos_at_stop:.2f}, 0.5秒后: {pos_after_wait:.2f}")
    except Exception as e:
        log_test("点动停止", False, str(e))

def test_step_move(service):
    """测试步进移动"""
    log_section("7. 步进移动测试")

    try:
        start_pos = service.get_position()
        step_distance = 2.0  # 2mm

        # 正向步进
        service.move_by(step_distance, velocity_mm_s=30.0)

        end_pos = service.get_position()
        error = abs((end_pos - start_pos) - step_distance)
        passed = error < 0.1  # 允许 0.1mm 误差

        log_test("正向步进移动", passed,
                f"目标: {step_distance}mm, 实际: {end_pos-start_pos:.3f}mm, 误差: {error:.3f}mm")
    except Exception as e:
        log_test("正向步进移动", False, str(e))

    try:
        start_pos = service.get_position()
        step_distance = -2.0  # -2mm

        # 负向步进
        service.move_by(step_distance, velocity_mm_s=30.0)

        end_pos = service.get_position()
        error = abs((end_pos - start_pos) - step_distance)
        passed = error < 0.1

        log_test("负向步进移动", passed,
                f"目标: {step_distance}mm, 实际: {end_pos-start_pos:.3f}mm, 误差: {error:.3f}mm")
    except Exception as e:
        log_test("负向步进移动", False, str(e))

def test_absolute_move(service):
    """测试绝对位置移动"""
    log_section("8. 绝对位置移动测试")

    try:
        # 移动到 10mm
        target_pos = 10.0
        service.move_to(target_pos, velocity_mm_s=50.0)

        actual_pos = service.get_position()
        error = abs(actual_pos - target_pos)
        passed = error < 0.1

        log_test("绝对移动到 10mm", passed,
                f"目标: {target_pos}mm, 实际: {actual_pos:.3f}mm, 误差: {error:.3f}mm")
    except Exception as e:
        log_test("绝对移动到 10mm", False, str(e))

    try:
        # 移动到 20mm
        target_pos = 20.0
        service.move_to(target_pos, velocity_mm_s=50.0)

        actual_pos = service.get_position()
        error = abs(actual_pos - target_pos)
        passed = error < 0.1

        log_test("绝对移动到 20mm", passed,
                f"目标: {target_pos}mm, 实际: {actual_pos:.3f}mm, 误差: {error:.3f}mm")
    except Exception as e:
        log_test("绝对移动到 20mm", False, str(e))

def test_stop_during_motion(service):
    """测试运动中停止"""
    log_section("9. 运动中停止测试")

    try:
        start_pos = service.get_position()

        # 开始长距离移动（不等待）
        service.move_to(start_pos + 50.0, velocity_mm_s=30.0, wait=False)
        time.sleep(0.5)  # 移动一段时间

        # 停止
        service.stop(wait=True)

        # 检查是否停在中途
        final_pos = service.get_position()
        moved = abs(final_pos - start_pos) > 5.0
        not_reached_target = abs(final_pos - (start_pos + 50.0)) > 5.0

        passed = moved and not_reached_target
        log_test("运动中停止", passed,
                f"起始: {start_pos:.2f}, 停止位置: {final_pos:.2f}")
    except Exception as e:
        log_test("运动中停止", False, str(e))

def test_sequence_jog_then_step(service):
    """测试点动后步进"""
    log_section("10. 点动后步进测试 (验证 Halt 清除)")

    try:
        # 先点动
        service.jog(20.0)
        time.sleep(0.3)
        service.stop(wait=False)
        time.sleep(0.2)

        # 记录位置
        pos_before_step = service.get_position()

        # 然后步进
        step_distance = 3.0
        service.move_by(step_distance, velocity_mm_s=30.0)

        pos_after_step = service.get_position()
        actual_move = pos_after_step - pos_before_step
        error = abs(actual_move - step_distance)
        passed = error < 0.2

        log_test("点动后步进移动", passed,
                f"步进目标: {step_distance}mm, 实际移动: {actual_move:.3f}mm")
    except Exception as e:
        log_test("点动后步进移动", False, str(e))

def test_sequence_jog_then_absolute(service):
    """测试点动后绝对移动"""
    log_section("11. 点动后绝对移动测试")

    try:
        # 先点动
        service.jog(-20.0)
        time.sleep(0.3)
        service.stop(wait=False)
        time.sleep(0.2)

        # 然后绝对移动
        target_pos = 15.0
        service.move_to(target_pos, velocity_mm_s=50.0)

        actual_pos = service.get_position()
        error = abs(actual_pos - target_pos)
        passed = error < 0.1

        log_test("点动后绝对移动", passed,
                f"目标: {target_pos}mm, 实际: {actual_pos:.3f}mm")
    except Exception as e:
        log_test("点动后绝对移动", False, str(e))

def test_fault_reset(service):
    """测试故障复位"""
    log_section("12. 故障复位测试")

    try:
        service.fault_reset()
        time.sleep(0.3)
        status = service.get_axis_status()
        state_str = str(status.state).lower()
        no_fault = "fault" not in state_str
        log_test("故障复位", no_fault, f"状态: {status.state}")
    except Exception as e:
        log_test("故障复位", False, str(e))

def print_summary():
    """打印测试总结"""
    print(f"\n{'='*60}")
    print(" 测试总结")
    print(f"{'='*60}")

    passed = sum(1 for t in test_results if t["passed"])
    failed = sum(1 for t in test_results if not t["passed"])
    total = len(test_results)

    print(f"\n总计: {total} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print(f"通过率: {passed/total*100:.1f}%")

    if failed > 0:
        print(f"\n失败的测试:")
        for t in test_results:
            if not t["passed"]:
                print(f"  - {t['name']}: {t['details']}")

    print(f"\n{'='*60}")
    return failed == 0

def main():
    print("=" * 60)
    print(" 伺服电机综合性自动化测试")
    print("=" * 60)
    print(f"端口: {PORT}")
    print(f"轴: {AXIS.value}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    service = ServoService(port=PORT, baudrate=BAUDRATE)
    service.current_axis = AXIS

    try:
        # 1. 连接测试
        if not test_connection(service):
            print("\n无法连接，测试终止")
            return False

        # 2. 状态读取测试
        test_status_read(service)

        # 3. 参数读写测试
        test_parameter_read_write(service)

        # 4. 使能/禁用测试
        test_enable_disable(service)

        # 5. 点动测试
        test_jog(service)

        # 6. 点动停止测试
        test_jog_stop(service)

        # 7. 步进移动测试
        test_step_move(service)

        # 8. 绝对位置移动测试
        test_absolute_move(service)

        # 9. 运动中停止测试
        test_stop_during_motion(service)

        # 10. 点动后步进测试
        test_sequence_jog_then_step(service)

        # 11. 点动后绝对移动测试
        test_sequence_jog_then_absolute(service)

        # 12. 故障复位测试
        test_fault_reset(service)

        # 打印总结
        return print_summary()

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return False
    finally:
        try:
            service.disable()
        except:
            pass
        service.disconnect()
        print("\n已断开连接")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
