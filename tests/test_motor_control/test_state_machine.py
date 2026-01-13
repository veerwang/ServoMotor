"""
CiA402 状态机测试
"""

import pytest

from servo_service.motor_control.registers import ControlWordBits, StatusWordBits
from servo_service.motor_control.state_machine import (
    DriveCommand,
    DriveState,
    StateMachine,
    decode_status_word,
    decode_status_word_flags,
    get_transition_path,
    is_fault,
    is_operation_enabled,
    is_target_reached,
    is_warning,
)


class TestDecodeStatusWord:
    """测试状态字解码"""

    def test_switch_on_disabled(self) -> None:
        """测试 Switch on disabled 状态"""
        status_word = 0x0040  # Bit 6 set
        state = decode_status_word(status_word)
        assert state == DriveState.SWITCH_ON_DISABLED

    def test_ready_to_switch_on(self) -> None:
        """测试 Ready to switch on 状态"""
        status_word = 0x0021  # Bits 0, 5 set
        state = decode_status_word(status_word)
        assert state == DriveState.READY_TO_SWITCH_ON

    def test_switched_on(self) -> None:
        """测试 Switched on 状态"""
        status_word = 0x0023  # Bits 0, 1, 5 set
        state = decode_status_word(status_word)
        assert state == DriveState.SWITCHED_ON

    def test_operation_enabled(self) -> None:
        """测试 Operation enabled 状态"""
        status_word = 0x0027  # Bits 0, 1, 2, 5 set
        state = decode_status_word(status_word)
        assert state == DriveState.OPERATION_ENABLED

    def test_fault(self) -> None:
        """测试 Fault 状态"""
        status_word = 0x0008  # Bit 3 (fault) set
        state = decode_status_word(status_word)
        assert state == DriveState.FAULT

    def test_quick_stop_active(self) -> None:
        """测试 Quick stop active 状态"""
        status_word = 0x0007  # Bits 0, 1, 2 set (no quick stop bit)
        state = decode_status_word(status_word)
        assert state == DriveState.QUICK_STOP_ACTIVE


class TestDecodeStatusWordFlags:
    """测试状态字标志位解码"""

    def test_all_flags(self) -> None:
        """测试所有标志位"""
        # 设置多个标志位
        status_word = (
            StatusWordBits.READY_TO_SWITCH_ON
            | StatusWordBits.SWITCHED_ON
            | StatusWordBits.OPERATION_ENABLED
            | StatusWordBits.TARGET_REACHED
        )

        flags = decode_status_word_flags(status_word)

        assert flags["ready_to_switch_on"] is True
        assert flags["switched_on"] is True
        assert flags["operation_enabled"] is True
        assert flags["target_reached"] is True
        assert flags["fault"] is False
        assert flags["warning"] is False

    def test_fault_flag(self) -> None:
        """测试故障标志"""
        status_word = StatusWordBits.FAULT
        flags = decode_status_word_flags(status_word)
        assert flags["fault"] is True


class TestStatusHelpers:
    """测试状态辅助函数"""

    def test_is_target_reached(self) -> None:
        """测试目标到达检测"""
        assert is_target_reached(StatusWordBits.TARGET_REACHED) is True
        assert is_target_reached(0x0000) is False

    def test_is_fault(self) -> None:
        """测试故障检测"""
        assert is_fault(StatusWordBits.FAULT) is True
        assert is_fault(0x0000) is False

    def test_is_warning(self) -> None:
        """测试警告检测"""
        assert is_warning(StatusWordBits.WARNING) is True
        assert is_warning(0x0000) is False

    def test_is_operation_enabled(self) -> None:
        """测试操作使能检测"""
        assert is_operation_enabled(StatusWordBits.OPERATION_ENABLED) is True
        assert is_operation_enabled(0x0000) is False


class TestGetTransitionPath:
    """测试状态转换路径"""

    def test_same_state(self) -> None:
        """测试相同状态"""
        path = get_transition_path(DriveState.OPERATION_ENABLED, DriveState.OPERATION_ENABLED)
        assert path == []

    def test_disabled_to_enabled(self) -> None:
        """测试从禁用到使能"""
        path = get_transition_path(DriveState.SWITCH_ON_DISABLED, DriveState.OPERATION_ENABLED)

        assert len(path) == 3
        commands = [cmd for cmd, cw in path]
        assert DriveCommand.SHUTDOWN in commands
        assert DriveCommand.SWITCH_ON in commands
        assert DriveCommand.ENABLE_OPERATION in commands

    def test_enabled_to_switched_on(self) -> None:
        """测试从使能到开机"""
        path = get_transition_path(DriveState.OPERATION_ENABLED, DriveState.SWITCHED_ON)

        assert len(path) == 1
        assert path[0][0] == DriveCommand.DISABLE_OPERATION

    def test_fault_to_enabled(self) -> None:
        """测试从故障到使能"""
        path = get_transition_path(DriveState.FAULT, DriveState.OPERATION_ENABLED)

        # 应该先故障复位，然后正常使能流程
        assert len(path) >= 4
        assert path[0][0] == DriveCommand.FAULT_RESET


class TestStateMachine:
    """测试状态机类"""

    def test_initial_state(self) -> None:
        """测试初始状态"""
        sm = StateMachine()
        assert sm.current_state == DriveState.UNKNOWN
        assert sm.status_word == 0

    def test_update(self) -> None:
        """测试状态更新"""
        sm = StateMachine()

        # 更新到 Operation Enabled
        state = sm.update(0x0027)

        assert state == DriveState.OPERATION_ENABLED
        assert sm.current_state == DriveState.OPERATION_ENABLED
        assert sm.status_word == 0x0027

    def test_properties(self) -> None:
        """测试属性"""
        sm = StateMachine()
        sm.update(0x0027 | StatusWordBits.TARGET_REACHED)

        assert sm.is_operation_enabled is True
        assert sm.is_target_reached is True
        assert sm.is_fault is False

    def test_get_path_to(self) -> None:
        """测试获取转换路径"""
        sm = StateMachine()
        sm.update(0x0040)  # Switch on disabled

        path = sm.get_path_to(DriveState.OPERATION_ENABLED)
        assert len(path) == 3

    def test_flags(self) -> None:
        """测试标志位"""
        sm = StateMachine()
        sm.update(StatusWordBits.OPERATION_ENABLED | StatusWordBits.TARGET_REACHED)

        flags = sm.flags
        assert flags["operation_enabled"] is True
        assert flags["target_reached"] is True
