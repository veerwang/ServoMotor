"""
伺服电机服务模块

提供统一的高级 API 用于控制伺服电机系统。
"""

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union

from ..modbus_rtu import ModbusClient
from ..motor_control import (
    DriveState,
    HomingMethod,
    Motor,
    MotorError,
    MotorStatus,
    OperationMode,
)
from ..serial_comm import PortInfo, PortScanner, SerialPort
from .axis_config import AxisConfig, AxisName, DEFAULT_AXIS_CONFIGS, get_axis_config

logger = logging.getLogger(__name__)


@dataclass
class AxisStatus:
    """轴状态数据"""

    axis: AxisName
    """轴名称"""

    connected: bool
    """是否连接"""

    state: DriveState
    """驱动器状态"""

    position_mm: float
    """当前位置 (mm)"""

    velocity_mm_s: float
    """当前速度 (mm/s)"""

    is_enabled: bool
    """是否使能"""

    is_fault: bool
    """是否有故障"""

    is_homed: bool
    """是否已回零"""

    is_target_reached: bool
    """目标是否到达"""

    error_code: int
    """错误码"""

    status_word: int = 0
    """状态字原始值 (调试用)"""


class ServoService:
    """
    伺服电机服务类

    提供多轴控制的统一接口。
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        axis_configs: Optional[Dict[AxisName, AxisConfig]] = None,
        timeout: float = 0.5,
        retries: int = 3,
    ) -> None:
        """
        初始化伺服服务

        Args:
            port: 串口名称 (可选，后续通过 connect 指定)
            baudrate: 波特率
            axis_configs: 轴配置字典 (默认使用 XYG321-A 配置)
            timeout: 通信超时 (秒)
            retries: 重试次数
        """
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._retries = retries

        # 轴配置
        self._axis_configs = axis_configs or DEFAULT_AXIS_CONFIGS.copy()

        # 通信对象
        self._serial_port: Optional[SerialPort] = None
        self._modbus_client: Optional[ModbusClient] = None

        # 电机实例
        self._motors: Dict[AxisName, Motor] = {}

        # 当前选中的轴
        self._current_axis: AxisName = AxisName.Z

        # 回零状态
        self._homed_axes: Dict[AxisName, bool] = {axis: False for axis in AxisName}

        # 端口扫描器
        self._port_scanner = PortScanner()

    # ==================== 连接管理 ====================

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._modbus_client is not None and self._modbus_client.is_connected

    def get_modbus_client(self) -> Optional[ModbusClient]:
        """
        获取底层 Modbus 客户端（供调试使用）

        Returns:
            ModbusClient 实例，未连接时返回 None
        """
        return self._modbus_client

    @property
    def current_axis(self) -> AxisName:
        """获取当前选中的轴"""
        return self._current_axis

    @current_axis.setter
    def current_axis(self, axis: AxisName) -> None:
        """设置当前选中的轴"""
        if axis not in self._axis_configs:
            raise ValueError(f"轴 {axis.value} 未配置")

        old_axis = self._current_axis
        self._current_axis = axis
        logger.info(f"切换到轴 {axis.value}")

        # 如果已连接且切换了轴，自动初始化新轴参数
        if self.is_connected and axis != old_axis:
            try:
                self.initialize_motor_parameters(axis=axis, verbose=True)
            except Exception as e:
                logger.warning(f"初始化轴 {axis.value} 参数失败: {e}")

    def get_available_ports(self) -> List[PortInfo]:
        """
        获取可用串口列表

        Returns:
            PortInfo 列表
        """
        return self._port_scanner.scan_ports()

    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> None:
        """
        连接到伺服系统

        Args:
            port: 串口名称
            baudrate: 波特率
        """
        if port is not None:
            self._port = port
        if baudrate is not None:
            self._baudrate = baudrate

        if not self._port:
            raise ValueError("未指定串口")

        logger.info(f"连接到伺服系统: {self._port} @ {self._baudrate}")

        # 创建串口
        self._serial_port = SerialPort(
            port=self._port,
            baudrate=self._baudrate,
            timeout=self._timeout,
        )
        self._serial_port.open()

        # 创建 Modbus 客户端
        self._modbus_client = ModbusClient(
            serial_port=self._serial_port,
            timeout=self._timeout,
            retries=self._retries,
        )

        # 创建电机实例
        self._motors = {}
        for axis_name, config in self._axis_configs.items():
            self._motors[axis_name] = Motor(
                modbus_client=self._modbus_client,
                slave_id=config.slave_id,
            )

        # 验证与当前轴电机的通信
        self._verify_motor_communication()

        # 自动初始化当前轴参数
        self.initialize_motor_parameters(verbose=True)

        logger.info("伺服系统连接成功")

    def _verify_motor_communication(self) -> None:
        """
        验证与电机的通信

        尝试读取状态字来确认电机响应正常。

        Raises:
            RuntimeError: 如果通信失败
        """
        motor = self._motors.get(self._current_axis)
        if motor is None:
            raise RuntimeError(f"未找到轴 {self._current_axis.value} 的电机实例")

        config = self._axis_configs[self._current_axis]

        try:
            # 尝试读取状态字 (6041h) 来验证通信
            status_word = motor.read_status_word()
            logger.info(
                f"电机通信验证成功: 轴={self._current_axis.value}, "
                f"从站地址={config.slave_id}, 状态字=0x{status_word:04X}"
            )
        except Exception as e:
            # 关闭已打开的资源
            self._motors.clear()
            if self._modbus_client:
                self._modbus_client.disconnect()
                self._modbus_client = None
            if self._serial_port:
                self._serial_port.close()
                self._serial_port = None

            raise RuntimeError(
                f"无法与电机通信: 轴={self._current_axis.value}, "
                f"从站地址={config.slave_id}。请检查从站地址是否正确。\n"
                f"原始错误: {e}"
            )

    def disconnect(self) -> None:
        """断开连接"""
        logger.info("断开伺服系统连接")

        self._motors.clear()

        if self._modbus_client is not None:
            self._modbus_client.disconnect()
            self._modbus_client = None

        if self._serial_port is not None:
            self._serial_port.close()
            self._serial_port = None

        # 重置回零状态
        self._homed_axes = {axis: False for axis in AxisName}

    # ==================== 电机参数初始化 ====================

    def initialize_motor_parameters(
        self,
        axis: Optional[AxisName] = None,
        verbose: bool = True,
    ) -> None:
        """
        初始化电机参数

        根据 AxisConfig 中的配置，将以下参数写入驱动器:
        - 编码器分辨率 (608Fh) - 分子/分母
        - 减速比 (6091h) - 分子/分母
        - 回零超时时间
        - 堵转回零参数
        - DI (数字输入) 功能配置

        Args:
            axis: 轴名称 (None 则使用当前轴)
            verbose: 是否显示详细信息

        Note:
            建议在连接后、执行运动前调用此函数，确保驱动器参数正确。
            特别是回零超时参数，默认值 0ms 会导致回零立即超时!
        """
        if not self.is_connected:
            raise MotorError("未连接到伺服系统")

        if axis is None:
            axis = self._current_axis

        motor = self.get_motor(axis)
        config = self.get_axis_config(axis)

        if verbose:
            logger.info(f"初始化 {axis.value} 轴电机参数...")

        # 1. 设置编码器分辨率 (608Fh)
        motor.set_encoder_resolution(
            config.encoder_resolution,
            config.encoder_resolution_denominator
        )
        if verbose:
            logger.info(
                f"  编码器分辨率: {config.encoder_resolution}/"
                f"{config.encoder_resolution_denominator}"
            )

        # 2. 设置减速比 (6091h)
        motor.set_gear_ratio(
            config.gear_ratio_numerator,
            config.gear_ratio_denominator
        )
        if verbose:
            logger.info(
                f"  减速比: {config.gear_ratio_numerator}/"
                f"{config.gear_ratio_denominator}"
            )

        # 3. 设置回零超时
        motor.set_homing_timeout(config.homing_timeout)
        if verbose:
            logger.info(f"  回零超时: {config.homing_timeout}ms")

        # 4. 设置堵转回零参数
        motor.set_blocking_parameters(config.blocking_torque, config.blocking_time)
        if verbose:
            logger.info(
                f"  堵转参数: 扭矩阈值={config.blocking_torque/10}%, "
                f"检测时间={config.blocking_time}ms"
            )

        # 5. 配置 DI 功能
        di_configs = [
            (1, config.di1_function, config.di1_logic),
            (2, config.di2_function, config.di2_logic),
            (3, config.di3_function, config.di3_logic),
        ]

        for di_num, func, logic in di_configs:
            if func is not None:
                motor.set_di_config(di_num, func, logic)
                func_name = self._get_di_function_name(func)
                if verbose:
                    logger.info(f"  DI{di_num}: {func_name} (逻辑={logic})")

        if verbose:
            logger.info(f"{axis.value} 轴电机参数初始化完成")

    def initialize_all_motors(self, verbose: bool = True) -> None:
        """
        初始化所有电机参数

        Args:
            verbose: 是否显示详细信息
        """
        for axis in self._axis_configs.keys():
            try:
                self.initialize_motor_parameters(axis, verbose=verbose)
            except Exception as e:
                logger.warning(f"初始化 {axis.value} 轴失败: {e}")

    @staticmethod
    def _get_di_function_name(function: int) -> str:
        """获取 DI 功能名称"""
        di_functions = {
            0: "未定义",
            1: "电机使能",
            2: "报警复位",
            14: "正限位开关",
            15: "负限位开关",
            31: "原点开关",
        }
        return di_functions.get(function, f"功能{function}")

    # ==================== 轴访问 ====================

    def get_motor(self, axis: Optional[AxisName] = None) -> Motor:
        """
        获取电机实例

        Args:
            axis: 轴名称 (None 则使用当前轴)

        Returns:
            Motor 实例
        """
        if not self.is_connected:
            raise MotorError("未连接到伺服系统")

        if axis is None:
            axis = self._current_axis

        if axis not in self._motors:
            raise ValueError(f"轴 {axis.value} 未配置")

        return self._motors[axis]

    def get_axis_config(self, axis: Optional[AxisName] = None) -> AxisConfig:
        """
        获取轴配置

        Args:
            axis: 轴名称 (None 则使用当前轴)

        Returns:
            AxisConfig
        """
        if axis is None:
            axis = self._current_axis
        return self._axis_configs[axis]

    # ==================== 状态读取 ====================

    def get_axis_status(self, axis: Optional[AxisName] = None) -> AxisStatus:
        """
        获取轴状态

        Args:
            axis: 轴名称 (None 则使用当前轴)

        Returns:
            AxisStatus
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)

        if not self.is_connected:
            return AxisStatus(
                axis=axis,
                connected=False,
                state=DriveState.UNKNOWN,
                position_mm=0.0,
                velocity_mm_s=0.0,
                is_enabled=False,
                is_fault=False,
                is_homed=False,
                is_target_reached=False,
                error_code=0,
                status_word=0,
            )

        motor = self.get_motor(axis)
        status = motor.get_status()

        return AxisStatus(
            axis=axis,
            connected=True,
            state=status.state,
            position_mm=config.pulses_to_mm(status.position),
            velocity_mm_s=config.velocity_pulses_to_mm(status.velocity),
            is_enabled=status.state == DriveState.OPERATION_ENABLED,
            is_fault=status.is_fault,
            is_homed=self._homed_axes.get(axis, False),
            is_target_reached=status.is_target_reached,
            error_code=status.error_code,
            status_word=status.status_word,
        )

    def get_all_axis_status(self) -> Dict[AxisName, AxisStatus]:
        """
        获取所有轴状态

        Returns:
            轴状态字典
        """
        return {axis: self.get_axis_status(axis) for axis in self._axis_configs.keys()}

    def get_position(self, axis: Optional[AxisName] = None) -> float:
        """
        获取当前位置 (mm)

        Args:
            axis: 轴名称

        Returns:
            位置 (mm)
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        motor = self.get_motor(axis)
        position_pulses = motor.read_position()

        return config.pulses_to_mm(position_pulses)

    def get_velocity(self, axis: Optional[AxisName] = None) -> float:
        """
        获取当前速度 (mm/s)

        Args:
            axis: 轴名称

        Returns:
            速度 (mm/s)
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        motor = self.get_motor(axis)
        velocity_pulses = motor.read_velocity()

        return config.velocity_pulses_to_mm(velocity_pulses)

    # ==================== 使能控制 ====================

    def enable(self, axis: Optional[AxisName] = None) -> None:
        """
        使能轴

        Args:
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        logger.info(f"使能轴 {axis.value}")
        motor = self.get_motor(axis)
        motor.enable()

    def disable(self, axis: Optional[AxisName] = None) -> None:
        """
        禁用轴

        Args:
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        logger.info(f"禁用轴 {axis.value}")
        motor = self.get_motor(axis)
        motor.disable()

    def enable_all(self) -> None:
        """使能所有轴"""
        for axis in self._axis_configs.keys():
            self.enable(axis)

    def disable_all(self) -> None:
        """禁用所有轴"""
        for axis in self._axis_configs.keys():
            self.disable(axis)

    def quick_stop(self, axis: Optional[AxisName] = None) -> None:
        """
        快速停止

        Args:
            axis: 轴名称 (None 则停止当前轴)
        """
        if axis is None:
            axis = self._current_axis

        logger.warning(f"快速停止轴 {axis.value}")
        motor = self.get_motor(axis)
        motor.quick_stop()

    def quick_stop_all(self) -> None:
        """快速停止所有轴"""
        for axis in self._axis_configs.keys():
            self.quick_stop(axis)

    def fault_reset(self, axis: Optional[AxisName] = None) -> None:
        """
        故障复位

        Args:
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        logger.info(f"故障复位轴 {axis.value}")
        motor = self.get_motor(axis)
        motor.fault_reset()

    # ==================== 运动控制 ====================

    def move_to(
        self,
        position_mm: float,
        velocity_mm_s: Optional[float] = None,
        axis: Optional[AxisName] = None,
        wait: bool = True,
    ) -> None:
        """
        移动到指定位置 (绝对位置)

        Args:
            position_mm: 目标位置 (mm)
            velocity_mm_s: 移动速度 (mm/s)
            axis: 轴名称
            wait: 是否等待完成
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)

        # 检查位置有效性
        if not config.is_position_valid(position_mm):
            raise ValueError(
                f"位置 {position_mm}mm 超出行程范围 "
                f"[{config.stroke_min}, {config.stroke_max}]"
            )

        # 转换单位
        position_pulses = config.mm_to_pulses(position_mm)

        velocity_pulses = None
        if velocity_mm_s is not None:
            velocity_pulses = config.velocity_mm_to_pulses(velocity_mm_s)

        logger.info(f"轴 {axis.value} 移动到 {position_mm}mm")

        motor = self.get_motor(axis)
        motor.move_absolute(position_pulses, velocity_pulses, wait=wait)

    def move_by(
        self,
        distance_mm: float,
        velocity_mm_s: Optional[float] = None,
        axis: Optional[AxisName] = None,
        wait: bool = True,
    ) -> None:
        """
        相对移动

        Args:
            distance_mm: 移动距离 (mm)
            velocity_mm_s: 移动速度 (mm/s)
            axis: 轴名称
            wait: 是否等待完成
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)

        # 检查目标位置有效性
        current_pos = self.get_position(axis)
        target_pos = current_pos + distance_mm

        if not config.is_position_valid(target_pos):
            raise ValueError(
                f"目标位置 {target_pos}mm 超出行程范围 "
                f"[{config.stroke_min}, {config.stroke_max}]"
            )

        # 转换单位
        distance_pulses = config.mm_to_pulses(distance_mm)

        velocity_pulses = None
        if velocity_mm_s is not None:
            velocity_pulses = config.velocity_mm_to_pulses(velocity_mm_s)

        logger.info(f"轴 {axis.value} 相对移动 {distance_mm}mm")

        motor = self.get_motor(axis)
        motor.move_relative(distance_pulses, velocity_pulses, wait=wait)

    def jog(
        self,
        velocity_mm_s: float,
        axis: Optional[AxisName] = None,
    ) -> None:
        """
        点动运行 (速度模式)

        Args:
            velocity_mm_s: 速度 (mm/s，正为正向，负为反向)
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)

        # 限制速度
        if abs(velocity_mm_s) > config.max_velocity:
            velocity_mm_s = config.max_velocity * (1 if velocity_mm_s > 0 else -1)

        # 应用速度极性修正
        velocity_mm_s_corrected = velocity_mm_s * config.velocity_polarity
        velocity_pulses = config.velocity_mm_to_pulses(velocity_mm_s_corrected)

        logger.info(f"轴 {axis.value} 点动: {velocity_mm_s}mm/s")

        motor = self.get_motor(axis)
        motor.run_velocity(velocity_pulses)

    def stop(self, axis: Optional[AxisName] = None, wait: bool = True) -> None:
        """
        停止运动

        Args:
            axis: 轴名称
            wait: 是否等待停止完成
        """
        if axis is None:
            axis = self._current_axis

        logger.info(f"停止轴 {axis.value}")
        motor = self.get_motor(axis)
        motor.stop(wait=wait)

    # ==================== 回零控制 ====================

    def home(
        self,
        axis: Optional[AxisName] = None,
        method: Optional[HomingMethod] = None,
        wait: bool = True,
    ) -> None:
        """
        执行回零

        Args:
            axis: 轴名称
            method: 回零方式 (不指定则使用轴配置中的默认方式)
            wait: 是否等待完成
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)

        # 如果没有指定回零方式，使用配置中的默认方式
        if method is None and config.homing_method is not None:
            method = HomingMethod(config.homing_method)

        # 设置回零速度
        motor = self.get_motor(axis)
        motor.set_homing_speeds(
            high_speed=config.velocity_mm_to_pulses(config.homing_velocity_high),
            low_speed=config.velocity_mm_to_pulses(config.homing_velocity_low),
            acceleration=config.velocity_mm_to_pulses(config.homing_acceleration),
        )

        logger.info(f"轴 {axis.value} 执行回零 (方式: {method})")
        motor.home(method=method, wait=wait)

        if wait:
            self._homed_axes[axis] = True

    def home_all(self, wait: bool = True) -> None:
        """
        所有轴回零

        Args:
            wait: 是否等待完成
        """
        for axis in self._axis_configs.keys():
            self.home(axis, wait=wait)

    def set_home_position(self, axis: Optional[AxisName] = None) -> None:
        """
        将当前位置设为原点

        Args:
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        motor = self.get_motor(axis)
        motor.set_homing_method(HomingMethod.CURRENT_POSITION_AS_HOME)
        motor.home(wait=True)

        self._homed_axes[axis] = True
        logger.info(f"轴 {axis.value} 当前位置设为原点")

    # ==================== 参数设置 ====================

    def set_velocity(
        self,
        velocity_mm_s: float,
        axis: Optional[AxisName] = None,
    ) -> None:
        """
        设置默认速度

        Args:
            velocity_mm_s: 速度 (mm/s)
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        velocity_pulses = config.velocity_mm_to_pulses(velocity_mm_s)

        motor = self.get_motor(axis)
        motor.set_profile_velocity(velocity_pulses)

    def set_acceleration(
        self,
        acceleration_mm_s2: float,
        axis: Optional[AxisName] = None,
    ) -> None:
        """
        设置加速度

        Args:
            acceleration_mm_s2: 加速度 (mm/s²)
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        acceleration_pulses = config.velocity_mm_to_pulses(acceleration_mm_s2)

        motor = self.get_motor(axis)
        motor.set_profile_acceleration(acceleration_pulses)

    def set_deceleration(
        self,
        deceleration_mm_s2: float,
        axis: Optional[AxisName] = None,
    ) -> None:
        """
        设置减速度

        Args:
            deceleration_mm_s2: 减速度 (mm/s²)
            axis: 轴名称
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        deceleration_pulses = config.velocity_mm_to_pulses(deceleration_mm_s2)

        motor = self.get_motor(axis)
        motor.set_profile_deceleration(deceleration_pulses)

    def get_profile_velocity(
        self,
        axis: Optional[AxisName] = None,
    ) -> float:
        """
        读取轮廓速度

        Args:
            axis: 轴名称

        Returns:
            速度 (mm/s)
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        motor = self.get_motor(axis)
        velocity_pulses = motor.get_profile_velocity()

        return config.velocity_pulses_to_mm(velocity_pulses)

    def get_profile_acceleration(
        self,
        axis: Optional[AxisName] = None,
    ) -> float:
        """
        读取轮廓加速度

        Args:
            axis: 轴名称

        Returns:
            加速度 (mm/s²)
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        motor = self.get_motor(axis)
        acceleration_pulses = motor.get_profile_acceleration()

        return config.velocity_pulses_to_mm(acceleration_pulses)

    def get_profile_deceleration(
        self,
        axis: Optional[AxisName] = None,
    ) -> float:
        """
        读取轮廓减速度

        Args:
            axis: 轴名称

        Returns:
            减速度 (mm/s²)
        """
        if axis is None:
            axis = self._current_axis

        config = self.get_axis_config(axis)
        motor = self.get_motor(axis)
        deceleration_pulses = motor.get_profile_deceleration()

        return config.velocity_pulses_to_mm(deceleration_pulses)

    # ==================== 上下文管理 ====================

    def __enter__(self) -> "ServoService":
        """上下文管理器入口"""
        if self._port:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """上下文管理器出口"""
        self.disconnect()

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"ServoService({self._port}, {status})"
