"""
NiMotion 伺服电机控制服务

提供完整的伺服电机控制功能，包括:
- 串口通信
- Modbus RTU 协议
- CiA402 状态机
- 多轴控制

使用示例:
    from servo_service import ServoService, AxisName

    # 创建服务并连接
    service = ServoService(port="/dev/ttyUSB0")
    service.connect()

    # 选择轴
    service.current_axis = AxisName.Z1

    # 使能电机
    service.enable()

    # 移动到指定位置
    service.move_to(50.0)  # 移动到 50mm

    # 断开连接
    service.disconnect()
"""

from .high_level_api import (
    AxisConfig,
    AxisName,
    AxisStatus,
    ServoService,
    get_axis_config,
)
from .modbus_rtu import ModbusClient, ModbusError
from .motor_control import (
    DriveState,
    HomingMethod,
    Motor,
    MotorError,
    MotorStatus,
    OperationMode,
)
from .serial_comm import PortInfo, PortScanner, SerialCommError, SerialPort

__version__ = "0.1.0"

__all__ = [
    # 版本
    "__version__",
    # 高级 API
    "ServoService",
    "AxisStatus",
    "AxisConfig",
    "AxisName",
    "get_axis_config",
    # 电机控制
    "Motor",
    "MotorStatus",
    "MotorError",
    "DriveState",
    "OperationMode",
    "HomingMethod",
    # Modbus
    "ModbusClient",
    "ModbusError",
    # 串口通信
    "SerialPort",
    "PortScanner",
    "PortInfo",
    "SerialCommError",
]
