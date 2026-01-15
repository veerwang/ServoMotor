#!/usr/bin/env python3
"""
最大平均速度测试

测试正反向的最大平均速度。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from servo_service import ServoService, AxisName

# 测试配置
PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
AXIS = AxisName.Z3

# 行程配置 (Z轴实际行程 0-61mm)
START_POS = 5.0      # 起始位置 (mm)
END_POS = 55.0       # 结束位置 (mm)
DISTANCE = END_POS - START_POS  # 50mm

# 速度配置
MAX_VELOCITY = 500.0  # Z轴最大速度 (mm/s)
ACCELERATION = 3000.0  # 加速度 (mm/s²) - 测试验证的最大稳定值
DECELERATION = 3000.0  # 减速度 (mm/s²)

def measure_move_time(service, start, end, velocity):
    """
    测量从 start 到 end 的移动时间

    Returns:
        (actual_distance, elapsed_time, average_speed)
    """
    # 先移动到起始位置
    service.move_to(start, velocity_mm_s=100.0)
    time.sleep(0.5)

    # 读取实际起始位置
    actual_start = service.get_position()

    # 记录开始时间
    t_start = time.time()

    # 执行移动
    service.move_to(end, velocity_mm_s=velocity)

    # 记录结束时间
    t_end = time.time()

    # 读取实际结束位置
    actual_end = service.get_position()

    # 计算结果
    actual_distance = abs(actual_end - actual_start)
    elapsed_time = t_end - t_start
    average_speed = actual_distance / elapsed_time if elapsed_time > 0 else 0

    return actual_distance, elapsed_time, average_speed

def main():
    print("=" * 60)
    print(" Z轴最大平均速度测试")
    print("=" * 60)
    print(f"端口: {PORT}")
    print(f"设定速度: {MAX_VELOCITY} mm/s")
    print(f"加速度: {ACCELERATION} mm/s²")
    print(f"测试行程: {DISTANCE} mm ({START_POS}mm <-> {END_POS}mm)")
    print("=" * 60)

    service = ServoService(port=PORT, baudrate=BAUDRATE)
    service.current_axis = AXIS

    try:
        # 连接
        service.connect()
        print(f"\n已连接到伺服系统")

        # 故障复位并等待状态恢复
        print(f"正在恢复电机状态...")
        for i in range(5):
            try:
                service.fault_reset()
                time.sleep(0.3)
            except:
                pass

            # 检查状态
            try:
                state = service.get_state()
                print(f"  当前状态: {state}")
                if "Unknown" not in str(state) and "FAULT" not in str(state):
                    break
            except:
                pass
            time.sleep(0.5)

        print(f"故障复位完成")

        # 设置运动参数
        service.set_velocity(MAX_VELOCITY)
        service.set_acceleration(ACCELERATION)
        service.set_deceleration(DECELERATION)
        print(f"已设置运动参数")

        # 使能
        service.enable()
        time.sleep(0.5)
        print(f"电机已使能")

        # 多次测试取平均
        NUM_TESTS = 3

        print(f"\n{'='*60}")
        print(f" 正向测试 ({START_POS}mm -> {END_POS}mm)")
        print(f"{'='*60}")

        forward_speeds = []
        for i in range(NUM_TESTS):
            dist, t, speed = measure_move_time(service, START_POS, END_POS, MAX_VELOCITY)
            forward_speeds.append(speed)
            print(f"  测试 {i+1}: 距离={dist:.2f}mm, 时间={t:.3f}s, 平均速度={speed:.1f}mm/s")
            time.sleep(0.3)

        avg_forward = sum(forward_speeds) / len(forward_speeds)
        print(f"  ----------------------------------------")
        print(f"  正向平均速度: {avg_forward:.1f} mm/s")

        print(f"\n{'='*60}")
        print(f" 反向测试 ({END_POS}mm -> {START_POS}mm)")
        print(f"{'='*60}")

        reverse_speeds = []
        for i in range(NUM_TESTS):
            dist, t, speed = measure_move_time(service, END_POS, START_POS, MAX_VELOCITY)
            reverse_speeds.append(speed)
            print(f"  测试 {i+1}: 距离={dist:.2f}mm, 时间={t:.3f}s, 平均速度={speed:.1f}mm/s")
            time.sleep(0.3)

        avg_reverse = sum(reverse_speeds) / len(reverse_speeds)
        print(f"  ----------------------------------------")
        print(f"  反向平均速度: {avg_reverse:.1f} mm/s")

        # 总结
        print(f"\n{'='*60}")
        print(f" 测试总结")
        print(f"{'='*60}")
        print(f"  设定速度:     {MAX_VELOCITY:.1f} mm/s")
        print(f"  正向平均速度: {avg_forward:.1f} mm/s ({avg_forward/MAX_VELOCITY*100:.1f}%)")
        print(f"  反向平均速度: {avg_reverse:.1f} mm/s ({avg_reverse/MAX_VELOCITY*100:.1f}%)")
        print(f"  正反向差异:   {abs(avg_forward - avg_reverse):.1f} mm/s ({abs(avg_forward - avg_reverse)/max(avg_forward, avg_reverse)*100:.1f}%)")
        print(f"{'='*60}")

        # 理论分析
        print(f"\n理论分析:")
        # 梯形速度曲线: 加速时间 = v/a, 加速距离 = v²/(2a)
        t_accel = MAX_VELOCITY / ACCELERATION
        d_accel = MAX_VELOCITY * MAX_VELOCITY / (2 * ACCELERATION)
        t_decel = MAX_VELOCITY / DECELERATION
        d_decel = MAX_VELOCITY * MAX_VELOCITY / (2 * DECELERATION)

        d_cruise = DISTANCE - d_accel - d_decel
        if d_cruise > 0:
            t_cruise = d_cruise / MAX_VELOCITY
            t_total = t_accel + t_cruise + t_decel
            theoretical_avg = DISTANCE / t_total
            print(f"  加速距离: {d_accel:.1f}mm, 加速时间: {t_accel:.3f}s")
            print(f"  匀速距离: {d_cruise:.1f}mm, 匀速时间: {t_cruise:.3f}s")
            print(f"  减速距离: {d_decel:.1f}mm, 减速时间: {t_decel:.3f}s")
            print(f"  理论总时间: {t_total:.3f}s")
            print(f"  理论平均速度: {theoretical_avg:.1f} mm/s")
        else:
            print(f"  行程不足以达到最大速度 (需要 {d_accel + d_decel:.1f}mm)")

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            service.disable()
        except:
            pass
        service.disconnect()
        print("\n已断开连接")

if __name__ == "__main__":
    main()
