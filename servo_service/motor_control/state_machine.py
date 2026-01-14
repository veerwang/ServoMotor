"""
CiA402 状态机模块

实现 CiA402 标准定义的伺服驱动器状态机。
"""

from enum import Enum
from typing import List, Optional, Tuple

from .registers import ControlWordBits, StatusWordBits


class DriveState(Enum):
    """驱动器状态"""

    NOT_READY_TO_SWITCH_ON = "Not ready to switch on"
    SWITCH_ON_DISABLED = "Switch on disabled"
    READY_TO_SWITCH_ON = "Ready to switch on"
    SWITCHED_ON = "Switched on"
    OPERATION_ENABLED = "Operation enabled"
    QUICK_STOP_ACTIVE = "Quick stop active"
    FAULT_REACTION_ACTIVE = "Fault reaction active"
    FAULT = "Fault"
    UNKNOWN = "Unknown"


class DriveCommand(Enum):
    """驱动器命令"""

    SHUTDOWN = "Shutdown"
    SWITCH_ON = "Switch on"
    ENABLE_OPERATION = "Enable operation"
    DISABLE_OPERATION = "Disable operation"
    DISABLE_VOLTAGE = "Disable voltage"
    QUICK_STOP = "Quick stop"
    FAULT_RESET = "Fault reset"


# 状态转换表: (当前状态, 命令) -> (目标状态, 控制字)
# 基于 CiA402 状态机图
STATE_TRANSITIONS = {
    # 从 Switch on disabled
    (DriveState.SWITCH_ON_DISABLED, DriveCommand.SHUTDOWN): (
        DriveState.READY_TO_SWITCH_ON,
        ControlWordBits.CMD_SHUTDOWN,
    ),
    # 从 Ready to switch on
    (DriveState.READY_TO_SWITCH_ON, DriveCommand.SWITCH_ON): (
        DriveState.SWITCHED_ON,
        ControlWordBits.CMD_SWITCH_ON,
    ),
    (DriveState.READY_TO_SWITCH_ON, DriveCommand.DISABLE_VOLTAGE): (
        DriveState.SWITCH_ON_DISABLED,
        ControlWordBits.CMD_DISABLE_VOLTAGE,
    ),
    # 从 Switched on
    (DriveState.SWITCHED_ON, DriveCommand.ENABLE_OPERATION): (
        DriveState.OPERATION_ENABLED,
        ControlWordBits.CMD_ENABLE_OPERATION,
    ),
    (DriveState.SWITCHED_ON, DriveCommand.SHUTDOWN): (
        DriveState.READY_TO_SWITCH_ON,
        ControlWordBits.CMD_SHUTDOWN,
    ),
    (DriveState.SWITCHED_ON, DriveCommand.DISABLE_VOLTAGE): (
        DriveState.SWITCH_ON_DISABLED,
        ControlWordBits.CMD_DISABLE_VOLTAGE,
    ),
    # 从 Operation enabled
    (DriveState.OPERATION_ENABLED, DriveCommand.DISABLE_OPERATION): (
        DriveState.SWITCHED_ON,
        ControlWordBits.CMD_DISABLE_OPERATION,
    ),
    (DriveState.OPERATION_ENABLED, DriveCommand.SHUTDOWN): (
        DriveState.READY_TO_SWITCH_ON,
        ControlWordBits.CMD_SHUTDOWN,
    ),
    (DriveState.OPERATION_ENABLED, DriveCommand.DISABLE_VOLTAGE): (
        DriveState.SWITCH_ON_DISABLED,
        ControlWordBits.CMD_DISABLE_VOLTAGE,
    ),
    (DriveState.OPERATION_ENABLED, DriveCommand.QUICK_STOP): (
        DriveState.QUICK_STOP_ACTIVE,
        ControlWordBits.CMD_QUICK_STOP,
    ),
    # 从 Quick stop active
    (DriveState.QUICK_STOP_ACTIVE, DriveCommand.DISABLE_VOLTAGE): (
        DriveState.SWITCH_ON_DISABLED,
        ControlWordBits.CMD_DISABLE_VOLTAGE,
    ),
    (DriveState.QUICK_STOP_ACTIVE, DriveCommand.ENABLE_OPERATION): (
        DriveState.OPERATION_ENABLED,
        ControlWordBits.CMD_ENABLE_OPERATION,
    ),
    # 从 Fault
    (DriveState.FAULT, DriveCommand.FAULT_RESET): (
        DriveState.SWITCH_ON_DISABLED,
        ControlWordBits.FAULT_RESET,
    ),
}


def decode_status_word(status_word: int) -> DriveState:
    """
    从状态字解码驱动器状态

    根据 CiA402 标准，状态由以下位决定:
    - Bit 0: Ready to switch on
    - Bit 1: Switched on
    - Bit 2: Operation enabled
    - Bit 3: Fault
    - Bit 5: Quick stop (0=激活)
    - Bit 6: Switch on disabled

    状态模式 (x=无关):
    | 状态字模式           | 状态                    |
    |---------------------|------------------------|
    | xxxx xxxx x0xx 0000 | Not ready to switch on |
    | xxxx xxxx x1xx 0000 | Switch on disabled     |
    | xxxx xxxx x01x 0001 | Ready to switch on     |
    | xxxx xxxx x01x 0011 | Switched on            |
    | xxxx xxxx x01x 0111 | Operation enabled      |
    | xxxx xxxx x00x 0111 | Quick stop active      |
    | xxxx xxxx x0xx 1111 | Fault reaction active  |
    | xxxx xxxx x0xx 1000 | Fault                  |

    Args:
        status_word: 状态字值

    Returns:
        当前驱动器状态
    """
    # 提取状态相关位 (bits 0-3, 5, 6)
    state_bits = status_word & StatusWordBits.STATE_MASK

    # 检查故障状态 (Bit 3 = 1)
    if status_word & StatusWordBits.FAULT:
        # Fault reaction active: xxxx xxxx x0xx 1111
        if (state_bits & 0x004F) == 0x000F:
            return DriveState.FAULT_REACTION_ACTIVE
        # Fault: xxxx xxxx x0xx 1000
        return DriveState.FAULT

    # 按照优先级检查其他状态 (使用位掩码而非精确匹配)

    # Operation enabled: xxxx xxxx x01x 0111
    # 需要 bits 0-2 = 111, bit 5 = 1, bit 6 = 0
    if (state_bits & 0x006F) == 0x0027:
        return DriveState.OPERATION_ENABLED

    # Quick stop active: xxxx xxxx x00x 0111
    # 需要 bits 0-2 = 111, bit 5 = 0, bit 6 = 0
    if (state_bits & 0x006F) == 0x0007:
        return DriveState.QUICK_STOP_ACTIVE

    # Switched on: xxxx xxxx x01x 0011
    # 需要 bits 0-1 = 11, bit 2 = 0, bit 5 = 1, bit 6 = 0
    if (state_bits & 0x006F) == 0x0023:
        return DriveState.SWITCHED_ON

    # Ready to switch on: xxxx xxxx x01x 0001
    # 需要 bit 0 = 1, bits 1-2 = 0, bit 5 = 1, bit 6 = 0
    if (state_bits & 0x006F) == 0x0021:
        return DriveState.READY_TO_SWITCH_ON

    # Switch on disabled: xxxx xxxx x1xx 0000
    # 需要 bits 0-3 = 0, bit 6 = 1, bit 5 可以是任意值
    if (state_bits & 0x004F) == 0x0040:
        return DriveState.SWITCH_ON_DISABLED

    # Not ready to switch on: xxxx xxxx x0xx 0000
    # 需要 bits 0-3 = 0, bit 6 = 0 (bit 5 可以是任意值)
    if (state_bits & 0x004F) == 0x0000:
        return DriveState.NOT_READY_TO_SWITCH_ON

    return DriveState.UNKNOWN


def get_command_control_word(command: DriveCommand) -> int:
    """
    获取命令对应的控制字

    Args:
        command: 驱动器命令

    Returns:
        控制字值
    """
    command_map = {
        DriveCommand.SHUTDOWN: ControlWordBits.CMD_SHUTDOWN,
        DriveCommand.SWITCH_ON: ControlWordBits.CMD_SWITCH_ON,
        DriveCommand.ENABLE_OPERATION: ControlWordBits.CMD_ENABLE_OPERATION,
        DriveCommand.DISABLE_OPERATION: ControlWordBits.CMD_DISABLE_OPERATION,
        DriveCommand.DISABLE_VOLTAGE: ControlWordBits.CMD_DISABLE_VOLTAGE,
        DriveCommand.QUICK_STOP: ControlWordBits.CMD_QUICK_STOP,
        DriveCommand.FAULT_RESET: ControlWordBits.FAULT_RESET,
    }
    return command_map.get(command, 0)


def get_transition_path(
    current_state: DriveState,
    target_state: DriveState,
) -> List[Tuple[DriveCommand, int]]:
    """
    获取从当前状态到目标状态的转换路径

    Args:
        current_state: 当前状态
        target_state: 目标状态

    Returns:
        命令和控制字的列表 [(command, control_word), ...]
    """
    if current_state == target_state:
        return []

    # 故障状态必须先复位
    if current_state == DriveState.FAULT:
        path = [(DriveCommand.FAULT_RESET, ControlWordBits.FAULT_RESET)]
        # 复位后进入 SWITCH_ON_DISABLED
        remaining = get_transition_path(DriveState.SWITCH_ON_DISABLED, target_state)
        return path + remaining

    # 定义状态层级 (用于判断转换方向)
    state_levels = {
        DriveState.NOT_READY_TO_SWITCH_ON: 0,
        DriveState.SWITCH_ON_DISABLED: 1,
        DriveState.READY_TO_SWITCH_ON: 2,
        DriveState.SWITCHED_ON: 3,
        DriveState.OPERATION_ENABLED: 4,
        DriveState.QUICK_STOP_ACTIVE: 4,
        DriveState.FAULT: 0,
        DriveState.FAULT_REACTION_ACTIVE: 0,
    }

    current_level = state_levels.get(current_state, 0)
    target_level = state_levels.get(target_state, 0)

    path: List[Tuple[DriveCommand, int]] = []

    if target_level > current_level:
        # 向上转换 (使能方向)
        if current_state == DriveState.SWITCH_ON_DISABLED:
            path.append((DriveCommand.SHUTDOWN, ControlWordBits.CMD_SHUTDOWN))
            current_state = DriveState.READY_TO_SWITCH_ON

        if current_state == DriveState.READY_TO_SWITCH_ON and target_level >= 3:
            path.append((DriveCommand.SWITCH_ON, ControlWordBits.CMD_SWITCH_ON))
            current_state = DriveState.SWITCHED_ON

        if current_state == DriveState.SWITCHED_ON and target_level >= 4:
            path.append((DriveCommand.ENABLE_OPERATION, ControlWordBits.CMD_ENABLE_OPERATION))

    else:
        # 向下转换 (禁用方向)
        if current_state == DriveState.OPERATION_ENABLED:
            if target_level <= 3:
                path.append((DriveCommand.DISABLE_OPERATION, ControlWordBits.CMD_DISABLE_OPERATION))
                current_state = DriveState.SWITCHED_ON

        if current_state == DriveState.SWITCHED_ON:
            if target_level <= 2:
                path.append((DriveCommand.SHUTDOWN, ControlWordBits.CMD_SHUTDOWN))
                current_state = DriveState.READY_TO_SWITCH_ON

        if current_state == DriveState.READY_TO_SWITCH_ON:
            if target_level <= 1:
                path.append((DriveCommand.DISABLE_VOLTAGE, ControlWordBits.CMD_DISABLE_VOLTAGE))

        if current_state == DriveState.QUICK_STOP_ACTIVE:
            path.append((DriveCommand.DISABLE_VOLTAGE, ControlWordBits.CMD_DISABLE_VOLTAGE))
            if target_level > 1:
                remaining = get_transition_path(DriveState.SWITCH_ON_DISABLED, target_state)
                return path + remaining

    return path


def is_target_reached(status_word: int) -> bool:
    """
    检查目标是否到达

    Args:
        status_word: 状态字值

    Returns:
        是否到达目标
    """
    return bool(status_word & StatusWordBits.TARGET_REACHED)


def is_fault(status_word: int) -> bool:
    """
    检查是否有故障

    Args:
        status_word: 状态字值

    Returns:
        是否有故障
    """
    return bool(status_word & StatusWordBits.FAULT)


def is_warning(status_word: int) -> bool:
    """
    检查是否有警告

    Args:
        status_word: 状态字值

    Returns:
        是否有警告
    """
    return bool(status_word & StatusWordBits.WARNING)


def is_operation_enabled(status_word: int) -> bool:
    """
    检查操作是否使能

    Args:
        status_word: 状态字值

    Returns:
        操作是否使能
    """
    return bool(status_word & StatusWordBits.OPERATION_ENABLED)


def decode_status_word_flags(status_word: int) -> dict:
    """
    解码状态字的所有标志位

    Args:
        status_word: 状态字值

    Returns:
        标志位字典
    """
    return {
        "ready_to_switch_on": bool(status_word & StatusWordBits.READY_TO_SWITCH_ON),
        "switched_on": bool(status_word & StatusWordBits.SWITCHED_ON),
        "operation_enabled": bool(status_word & StatusWordBits.OPERATION_ENABLED),
        "fault": bool(status_word & StatusWordBits.FAULT),
        "voltage_enabled": bool(status_word & StatusWordBits.VOLTAGE_ENABLED),
        "quick_stop": bool(status_word & StatusWordBits.QUICK_STOP),
        "switch_on_disabled": bool(status_word & StatusWordBits.SWITCH_ON_DISABLED),
        "warning": bool(status_word & StatusWordBits.WARNING),
        "remote": bool(status_word & StatusWordBits.REMOTE),
        "target_reached": bool(status_word & StatusWordBits.TARGET_REACHED),
        "internal_limit_active": bool(status_word & StatusWordBits.INTERNAL_LIMIT_ACTIVE),
        "set_point_ack": bool(status_word & StatusWordBits.SET_POINT_ACK),
        "following_error": bool(status_word & StatusWordBits.FOLLOWING_ERROR),
    }


class StateMachine:
    """
    CiA402 状态机

    封装状态机逻辑，提供状态查询和转换功能。
    """

    def __init__(self) -> None:
        """初始化状态机"""
        self._current_state = DriveState.UNKNOWN
        self._status_word = 0

    @property
    def current_state(self) -> DriveState:
        """获取当前状态"""
        return self._current_state

    @property
    def status_word(self) -> int:
        """获取状态字"""
        return self._status_word

    def update(self, status_word: int) -> DriveState:
        """
        更新状态

        Args:
            status_word: 新的状态字值

        Returns:
            更新后的状态
        """
        self._status_word = status_word
        self._current_state = decode_status_word(status_word)
        return self._current_state

    def get_path_to(self, target_state: DriveState) -> List[Tuple[DriveCommand, int]]:
        """
        获取到目标状态的转换路径

        Args:
            target_state: 目标状态

        Returns:
            转换路径
        """
        return get_transition_path(self._current_state, target_state)

    @property
    def is_target_reached(self) -> bool:
        """目标是否到达"""
        return is_target_reached(self._status_word)

    @property
    def is_fault(self) -> bool:
        """是否有故障"""
        return is_fault(self._status_word)

    @property
    def is_warning(self) -> bool:
        """是否有警告"""
        return is_warning(self._status_word)

    @property
    def is_operation_enabled(self) -> bool:
        """操作是否使能"""
        return is_operation_enabled(self._status_word)

    @property
    def flags(self) -> dict:
        """获取所有标志位"""
        return decode_status_word_flags(self._status_word)

    def __repr__(self) -> str:
        return f"StateMachine(state={self._current_state.value}, status=0x{self._status_word:04X})"
