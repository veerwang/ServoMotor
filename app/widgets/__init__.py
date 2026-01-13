"""
UI 组件模块

提供各种控制面板组件。
"""

from .axis_panel import AxisPanel
from .connection_panel import ConnectionPanel
from .modbus_debug_panel import ModbusDebugPanel
from .motion_panel import MotionPanel
from .parameter_panel import ParameterPanel
from .register_config_panel import RegisterConfigPanel
from .status_panel import StatusIndicator, StatusPanel

__all__ = [
    "ConnectionPanel",
    "AxisPanel",
    "StatusPanel",
    "StatusIndicator",
    "MotionPanel",
    "ParameterPanel",
    "ModbusDebugPanel",
    "RegisterConfigPanel",
]
