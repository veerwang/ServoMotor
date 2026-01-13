"""
电机控制类

提供伺服电机的高级控制接口。
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from ..modbus_rtu import ModbusClient
from .registers import (
    ControlWordBits,
    ErrorCode,
    HomingMethod,
    OperationMode,
    Registers,
    StatusWordBits,
)
from .state_machine import (
    DriveCommand,
    DriveState,
    StateMachine,
    decode_status_word,
    get_transition_path,
)

logger = logging.getLogger(__name__)


class MotorError(Exception):
    """电机控制错误"""

    pass


class MotorStateError(MotorError):
    """电机状态错误"""

    pass


class MotorTimeoutError(MotorError):
    """电机操作超时"""

    pass


@dataclass
class MotorStatus:
    """电机状态数据"""

    state: DriveState
    """驱动器状态"""

    status_word: int
    """状态字"""

    position: int
    """当前位置 (用户单位)"""

    velocity: int
    """当前速度"""

    torque: int
    """当前转矩"""

    operation_mode: int
    """当前操作模式"""

    is_target_reached: bool
    """目标是否到达"""

    is_fault: bool
    """是否有故障"""

    is_warning: bool
    """是否有警告"""

    error_code: int
    """错误码"""


class Motor:
    """
    伺服电机控制类

    提供电机的状态控制、运动控制等功能。
    """

    # 默认超时设置
    DEFAULT_STATE_TIMEOUT = 2.0  # 状态转换超时 (秒)
    DEFAULT_MOTION_TIMEOUT = 30.0  # 运动超时 (秒)
    DEFAULT_POLL_INTERVAL = 0.01  # 轮询间隔 (秒)

    def __init__(
        self,
        modbus_client: ModbusClient,
        slave_id: int = 1,
        state_timeout: float = DEFAULT_STATE_TIMEOUT,
        motion_timeout: float = DEFAULT_MOTION_TIMEOUT,
    ) -> None:
        """
        初始化电机控制

        Args:
            modbus_client: Modbus 客户端
            slave_id: 从站地址
            state_timeout: 状态转换超时 (秒)
            motion_timeout: 运动超时 (秒)
        """
        self._client = modbus_client
        self._slave_id = slave_id
        self._state_timeout = state_timeout
        self._motion_timeout = motion_timeout
        self._state_machine = StateMachine()

    @property
    def slave_id(self) -> int:
        """获取从站地址"""
        return self._slave_id

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._client.is_connected

    # ==================== 状态读取 ====================

    def read_status_word(self) -> int:
        """
        读取状态字

        Returns:
            状态字值
        """
        return self._client.read_register(self._slave_id, Registers.STATUS_WORD.address)

    def read_control_word(self) -> int:
        """
        读取控制字

        Returns:
            控制字值
        """
        return self._client.read_register(self._slave_id, Registers.CONTROL_WORD.address)

    def write_control_word(self, value: int) -> None:
        """
        写入控制字

        Args:
            value: 控制字值
        """
        self._client.write_register(self._slave_id, Registers.CONTROL_WORD.address, value)

    def read_position(self) -> int:
        """
        读取当前位置

        Returns:
            位置值 (编码器单位)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.POSITION_ACTUAL_VALUE.address, signed=True
        )

    def read_velocity(self) -> int:
        """
        读取当前速度

        Returns:
            速度值
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.VELOCITY_ACTUAL_VALUE.address, signed=True
        )

    def read_torque(self) -> int:
        """
        读取当前转矩

        Returns:
            转矩值 (0.1% 额定转矩)
        """
        return self._client.read_register(self._slave_id, Registers.TORQUE_ACTUAL_VALUE.address)

    def read_operation_mode(self) -> int:
        """
        读取当前操作模式

        Returns:
            操作模式值
        """
        return self._client.read_register(
            self._slave_id, Registers.MODES_OF_OPERATION_DISPLAY.address
        )

    def read_error_code(self) -> int:
        """
        读取错误码

        Returns:
            错误码
        """
        return self._client.read_register(self._slave_id, Registers.ERROR_CODE.address)

    def get_state(self) -> DriveState:
        """
        获取当前驱动器状态

        Returns:
            驱动器状态
        """
        status_word = self.read_status_word()
        return self._state_machine.update(status_word)

    def get_status(self) -> MotorStatus:
        """
        获取完整电机状态

        Returns:
            MotorStatus 实例
        """
        status_word = self.read_status_word()
        state = self._state_machine.update(status_word)

        return MotorStatus(
            state=state,
            status_word=status_word,
            position=self.read_position(),
            velocity=self.read_velocity(),
            torque=self.read_torque(),
            operation_mode=self.read_operation_mode(),
            is_target_reached=bool(status_word & StatusWordBits.TARGET_REACHED),
            is_fault=bool(status_word & StatusWordBits.FAULT),
            is_warning=bool(status_word & StatusWordBits.WARNING),
            error_code=self.read_error_code() if status_word & StatusWordBits.FAULT else 0,
        )

    # ==================== 状态控制 ====================

    def enable(self, timeout: Optional[float] = None) -> None:
        """
        使能电机

        将电机从任意状态转换到 Operation Enabled 状态。

        Args:
            timeout: 超时时间 (秒)

        Raises:
            MotorStateError: 状态转换失败
            MotorTimeoutError: 超时
        """
        if timeout is None:
            timeout = self._state_timeout

        current_state = self.get_state()
        logger.info(f"使能电机 (当前状态: {current_state.value})")

        if current_state == DriveState.OPERATION_ENABLED:
            logger.info("电机已处于使能状态")
            return

        # 获取转换路径
        path = get_transition_path(current_state, DriveState.OPERATION_ENABLED)
        if not path:
            raise MotorStateError(f"无法从 {current_state.value} 转换到使能状态")

        # 执行状态转换
        for command, control_word in path:
            logger.debug(f"执行命令: {command.value}, 控制字: 0x{control_word:04X}")
            self.write_control_word(control_word)
            time.sleep(0.01)

        # 等待到达目标状态
        self._wait_for_state(DriveState.OPERATION_ENABLED, timeout)
        logger.info("电机使能成功")

    def disable(self, timeout: Optional[float] = None) -> None:
        """
        禁用电机

        将电机转换到 Switched On 状态。

        Args:
            timeout: 超时时间 (秒)
        """
        if timeout is None:
            timeout = self._state_timeout

        current_state = self.get_state()
        logger.info(f"禁用电机 (当前状态: {current_state.value})")

        if current_state in (DriveState.SWITCHED_ON, DriveState.READY_TO_SWITCH_ON):
            logger.info("电机已处于禁用状态")
            return

        if current_state == DriveState.OPERATION_ENABLED:
            self.write_control_word(ControlWordBits.CMD_DISABLE_OPERATION)
            self._wait_for_state(DriveState.SWITCHED_ON, timeout)
            logger.info("电机禁用成功")

    def quick_stop(self) -> None:
        """
        快速停止

        立即执行快速停止。
        """
        logger.warning("执行快速停止")
        self.write_control_word(ControlWordBits.CMD_QUICK_STOP)

    def fault_reset(self, timeout: Optional[float] = None) -> None:
        """
        故障复位

        Args:
            timeout: 超时时间 (秒)
        """
        if timeout is None:
            timeout = self._state_timeout

        current_state = self.get_state()
        if current_state != DriveState.FAULT:
            logger.info("电机无故障，无需复位")
            return

        logger.info("执行故障复位")

        # 发送故障复位 (上升沿)
        current_cw = self.read_control_word()
        self.write_control_word(current_cw & ~ControlWordBits.FAULT_RESET)
        time.sleep(0.01)
        self.write_control_word(current_cw | ControlWordBits.FAULT_RESET)
        time.sleep(0.05)
        self.write_control_word(current_cw & ~ControlWordBits.FAULT_RESET)

        # 等待离开故障状态
        self._wait_for_state(DriveState.SWITCH_ON_DISABLED, timeout)
        logger.info("故障复位成功")

    def _wait_for_state(
        self,
        target_state: DriveState,
        timeout: float,
    ) -> None:
        """
        等待到达目标状态

        Args:
            target_state: 目标状态
            timeout: 超时时间

        Raises:
            MotorTimeoutError: 超时
            MotorStateError: 进入故障状态
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_state = self.get_state()

            if current_state == target_state:
                return

            if current_state == DriveState.FAULT:
                error_code = self.read_error_code()
                raise MotorStateError(f"电机故障: 错误码 0x{error_code:04X}")

            time.sleep(self.DEFAULT_POLL_INTERVAL)

        raise MotorTimeoutError(
            f"等待状态 {target_state.value} 超时 ({timeout}s), "
            f"当前状态: {self.get_state().value}"
        )

    # ==================== 操作模式 ====================

    def set_operation_mode(self, mode: OperationMode) -> None:
        """
        设置操作模式

        Args:
            mode: 操作模式
        """
        logger.info(f"设置操作模式: {mode.name}")
        self._client.write_register(
            self._slave_id, Registers.MODES_OF_OPERATION.address, mode.value
        )

    # ==================== 位置控制 ====================

    def set_target_position(self, position: int) -> None:
        """
        设置目标位置

        Args:
            position: 目标位置 (编码器单位)
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.TARGET_POSITION.address, position, signed=True
        )

    def set_profile_velocity(self, velocity: int) -> None:
        """
        设置轮廓速度

        Args:
            velocity: 速度值
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.PROFILE_VELOCITY.address, velocity
        )

    def get_profile_velocity(self) -> int:
        """
        读取轮廓速度

        Returns:
            速度值 (user units/s)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.PROFILE_VELOCITY.address
        )

    def set_profile_acceleration(self, acceleration: int) -> None:
        """
        设置轮廓加速度

        Args:
            acceleration: 加速度值
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.PROFILE_ACCELERATION.address, acceleration
        )

    def get_profile_acceleration(self) -> int:
        """
        读取轮廓加速度

        Returns:
            加速度值 (user units/s²)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.PROFILE_ACCELERATION.address
        )

    def set_profile_deceleration(self, deceleration: int) -> None:
        """
        设置轮廓减速度

        Args:
            deceleration: 减速度值
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.PROFILE_DECELERATION.address, deceleration
        )

    def get_profile_deceleration(self) -> int:
        """
        读取轮廓减速度

        Returns:
            减速度值 (user units/s²)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.PROFILE_DECELERATION.address
        )

    def move_absolute(
        self,
        position: int,
        velocity: Optional[int] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """
        绝对位置移动

        Args:
            position: 目标位置
            velocity: 移动速度 (可选)
            wait: 是否等待完成
            timeout: 超时时间 (秒)
        """
        if timeout is None:
            timeout = self._motion_timeout

        logger.info(f"绝对位置移动: 目标={position}")

        # 确保在位置模式
        self.set_operation_mode(OperationMode.PROFILE_POSITION)

        # 设置速度 (如果指定)
        if velocity is not None:
            self.set_profile_velocity(velocity)

        # 设置目标位置
        self.set_target_position(position)

        # 触发运动 (绝对位置)
        cw = self.read_control_word()
        cw &= ~ControlWordBits.ABS_REL  # 清除相对位置位
        cw &= ~ControlWordBits.NEW_SET_POINT  # 清除新设定点位
        cw &= ~ControlWordBits.HALT  # 清除 Halt 位
        self.write_control_word(cw)
        time.sleep(0.001)
        cw |= ControlWordBits.NEW_SET_POINT  # 设置新设定点
        self.write_control_word(cw)

        if wait:
            self._wait_for_motion_complete(timeout)

    def move_relative(
        self,
        distance: int,
        velocity: Optional[int] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """
        相对位置移动

        Args:
            distance: 移动距离
            velocity: 移动速度 (可选)
            wait: 是否等待完成
            timeout: 超时时间 (秒)
        """
        if timeout is None:
            timeout = self._motion_timeout

        logger.info(f"相对位置移动: 距离={distance}")

        # 确保在位置模式
        self.set_operation_mode(OperationMode.PROFILE_POSITION)

        # 设置速度 (如果指定)
        if velocity is not None:
            self.set_profile_velocity(velocity)

        # 设置目标距离
        self.set_target_position(distance)

        # 触发运动 (相对位置)
        cw = self.read_control_word()
        cw |= ControlWordBits.ABS_REL  # 设置相对位置位
        cw &= ~ControlWordBits.NEW_SET_POINT  # 清除新设定点位
        cw &= ~ControlWordBits.HALT  # 清除 Halt 位
        self.write_control_word(cw)
        time.sleep(0.001)
        cw |= ControlWordBits.NEW_SET_POINT  # 设置新设定点
        self.write_control_word(cw)

        if wait:
            self._wait_for_motion_complete(timeout)

    def _wait_for_motion_complete(self, timeout: float) -> None:
        """
        等待运动完成

        Args:
            timeout: 超时时间

        Raises:
            MotorTimeoutError: 超时
            MotorStateError: 故障
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_word = self.read_status_word()

            # 检查故障
            if status_word & StatusWordBits.FAULT:
                error_code = self.read_error_code()
                raise MotorStateError(f"运动过程中发生故障: 错误码 0x{error_code:04X}")

            # 检查目标到达
            if status_word & StatusWordBits.TARGET_REACHED:
                logger.info("运动完成")
                return

            time.sleep(self.DEFAULT_POLL_INTERVAL)

        raise MotorTimeoutError(f"等待运动完成超时 ({timeout}s)")

    # ==================== 速度控制 ====================

    def set_target_velocity(self, velocity: int) -> None:
        """
        设置目标速度

        Args:
            velocity: 目标速度
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.TARGET_VELOCITY.address, velocity, signed=True
        )

    def run_velocity(self, velocity: int) -> None:
        """
        速度模式运行 (使用位置模式模拟，移动到很远的位置)

        Args:
            velocity: 目标速度 (正值正向，负值反向)
        """
        logger.info(f"速度模式运行: 速度={velocity}")

        # 使用位置模式模拟速度运行
        self.set_operation_mode(OperationMode.PROFILE_POSITION)

        # 设置轮廓速度
        self.set_profile_velocity(abs(velocity))

        # 根据方向设置目标位置
        far_position = -10000000 if velocity > 0 else 10000000

        self.set_target_position(far_position)

        # 触发绝对位置移动: Enable + New setpoint (同时清除 Halt 位)
        self.write_control_word(0x000F)  # 清除 New setpoint 和 Halt
        time.sleep(0.001)
        self.write_control_word(0x001F)  # Enable + New setpoint + Absolute

    def stop(self, wait: bool = True, timeout: float = 5.0) -> None:
        """
        停止运动

        Args:
            wait: 是否等待停止完成
            timeout: 超时时间
        """
        logger.info("停止运动")

        # 读取当前位置
        current_pos = self.read_position()

        # 设置目标位置为当前位置（防止清除Halt后继续运动）
        self.set_target_position(current_pos)

        # 设置 Halt 位停止运动
        self.write_control_word(0x010F)  # Enable + Halt

        if wait:
            # 等待速度降为 0
            start_time = time.time()
            while time.time() - start_time < timeout:
                velocity = self.read_velocity()
                if abs(velocity) < 10:  # 速度接近 0
                    break
                time.sleep(self.DEFAULT_POLL_INTERVAL)

            # 重新读取停止后的位置
            final_pos = self.read_position()
            self.set_target_position(final_pos)

            # 清除 Halt，恢复正常使能
            self.write_control_word(0x000F)  # Enable only
            logger.info(f"运动已停止，位置: {final_pos}")
        else:
            # 非阻塞模式：只设置 Halt，不清除
            # Halt 位会在下一个运动命令时自动清除
            logger.info(f"已发送停止命令 (Halt)，当前位置: {current_pos}")

    # ==================== 回零控制 ====================

    def set_homing_method(self, method: HomingMethod) -> None:
        """
        设置回零方式

        Args:
            method: 回零方式
        """
        self._client.write_register(
            self._slave_id, Registers.HOMING_METHOD.address, method.value
        )

    def set_homing_speeds(
        self,
        high_speed: int,
        low_speed: int,
        acceleration: int,
    ) -> None:
        """
        设置回零速度参数

        Args:
            high_speed: 高速 (搜索开关)
            low_speed: 低速 (搜索零点)
            acceleration: 加速度
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.HOMING_SPEED_HIGH.address, high_speed
        )
        self._client.write_register_32bit(
            self._slave_id, Registers.HOMING_SPEED_LOW.address, low_speed
        )
        self._client.write_register_32bit(
            self._slave_id, Registers.HOMING_ACCELERATION.address, acceleration
        )

    def home(
        self,
        method: Optional[HomingMethod] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """
        执行回零

        Args:
            method: 回零方式 (可选，不指定则使用当前设置)
            wait: 是否等待完成
            timeout: 超时时间
        """
        if timeout is None:
            timeout = self._motion_timeout

        logger.info("执行回零")

        # 设置回零模式
        self.set_operation_mode(OperationMode.HOMING)
        time.sleep(0.05)

        # 设置回零方式
        if method is not None:
            self.set_homing_method(method)

        # 确保电机使能 (重新执行使能序列)
        self.write_control_word(ControlWordBits.CMD_SHUTDOWN)
        time.sleep(0.01)
        self.write_control_word(ControlWordBits.CMD_SWITCH_ON)
        time.sleep(0.01)
        self.write_control_word(ControlWordBits.CMD_ENABLE_OPERATION)
        time.sleep(0.01)

        # 启动回零 (触发 New setpoint)
        self.write_control_word(0x001F)  # Enable + New setpoint

        if wait:
            self._wait_for_homing_complete(timeout)

    def _wait_for_homing_complete(self, timeout: float) -> None:
        """
        等待回零完成

        Args:
            timeout: 超时时间
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_word = self.read_status_word()

            # 检查故障
            if status_word & StatusWordBits.FAULT:
                error_code = self.read_error_code()
                raise MotorStateError(f"回零过程中发生故障: 错误码 0x{error_code:04X}")

            # 检查回零完成 (target_reached 且无回零错误)
            if status_word & StatusWordBits.TARGET_REACHED:
                # 检查是否真的完成 (操作模式显示)
                mode = self.read_operation_mode()
                if mode == OperationMode.HOMING:
                    logger.info("回零完成")
                    return

            time.sleep(self.DEFAULT_POLL_INTERVAL)

        raise MotorTimeoutError(f"等待回零完成超时 ({timeout}s)")

    # ==================== 数字 I/O ====================

    def read_digital_inputs(self) -> int:
        """
        读取数字输入状态

        Returns:
            数字输入状态 (32 位)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.DIGITAL_INPUTS.address
        )

    def read_digital_outputs(self) -> int:
        """
        读取数字输出状态

        Returns:
            数字输出状态 (32 位)
        """
        return self._client.read_register_32bit(
            self._slave_id, Registers.DIGITAL_OUTPUTS.address
        )

    def write_digital_outputs(self, value: int) -> None:
        """
        写入数字输出

        Args:
            value: 输出值 (32 位)
        """
        self._client.write_register_32bit(
            self._slave_id, Registers.DIGITAL_OUTPUTS.address, value
        )

    def __repr__(self) -> str:
        return f"Motor(slave_id={self._slave_id}, state={self.get_state().value})"
