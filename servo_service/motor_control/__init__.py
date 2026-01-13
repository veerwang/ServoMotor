"""
电机控制模块

提供伺服电机控制功能，包括状态机、寄存器定义、运动控制等。
"""

from .motor import Motor, MotorError, MotorStateError, MotorStatus, MotorTimeoutError
from .registers import (
    ControlWordBits,
    ErrorCode,
    HomingMethod,
    OperationMode,
    RegisterAccess,
    RegisterDef,
    Registers,
    StatusWordBits,
)
from .state_machine import (
    DriveCommand,
    DriveState,
    StateMachine,
    decode_status_word,
    decode_status_word_flags,
    get_command_control_word,
    get_transition_path,
    is_fault,
    is_operation_enabled,
    is_target_reached,
    is_warning,
)

__all__ = [
    # Motor
    "Motor",
    "MotorStatus",
    "MotorError",
    "MotorStateError",
    "MotorTimeoutError",
    # Registers
    "Registers",
    "RegisterDef",
    "RegisterAccess",
    "ControlWordBits",
    "StatusWordBits",
    "OperationMode",
    "HomingMethod",
    "ErrorCode",
    # State Machine
    "DriveState",
    "DriveCommand",
    "StateMachine",
    "decode_status_word",
    "decode_status_word_flags",
    "get_command_control_word",
    "get_transition_path",
    "is_fault",
    "is_warning",
    "is_target_reached",
    "is_operation_enabled",
]
