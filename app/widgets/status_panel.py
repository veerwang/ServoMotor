"""
状态监控面板组件

显示电机的实时状态信息。
"""

import logging
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from servo_service import DriveState, ServoService

logger = logging.getLogger(__name__)


class StatusPanel(QGroupBox):
    """
    状态监控面板

    显示电机位置、速度、状态等信息。
    """

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化状态面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__("状态监控", parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 位置和速度显示
        pos_vel_layout = QGridLayout()

        # 位置
        pos_vel_layout.addWidget(QLabel("位置:"), 0, 0)
        self._position_label = QLabel("0.000")
        self._position_label.setProperty("class", "value")
        self._position_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pos_vel_layout.addWidget(self._position_label, 0, 1)
        pos_vel_layout.addWidget(QLabel("mm"), 0, 2)

        # 速度
        pos_vel_layout.addWidget(QLabel("速度:"), 1, 0)
        self._velocity_label = QLabel("0.00")
        self._velocity_label.setProperty("class", "value")
        self._velocity_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pos_vel_layout.addWidget(self._velocity_label, 1, 1)
        pos_vel_layout.addWidget(QLabel("mm/s"), 1, 2)

        # 转矩 (可选显示)
        pos_vel_layout.addWidget(QLabel("转矩:"), 2, 0)
        self._torque_label = QLabel("0.0")
        self._torque_label.setProperty("class", "value")
        self._torque_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pos_vel_layout.addWidget(self._torque_label, 2, 1)
        pos_vel_layout.addWidget(QLabel("%"), 2, 2)

        layout.addLayout(pos_vel_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 状态信息
        status_layout = QFormLayout()

        # 驱动器状态
        self._state_label = QLabel("未知")
        status_layout.addRow("驱动器状态:", self._state_label)

        # 操作模式
        self._mode_label = QLabel("--")
        status_layout.addRow("操作模式:", self._mode_label)

        # 错误码
        self._error_label = QLabel("无")
        status_layout.addRow("错误码:", self._error_label)

        layout.addLayout(status_layout)

        # 状态指示灯
        indicator_layout = QHBoxLayout()

        self._enabled_indicator = StatusIndicator("使能")
        indicator_layout.addWidget(self._enabled_indicator)

        self._fault_indicator = StatusIndicator("故障")
        indicator_layout.addWidget(self._fault_indicator)

        self._homed_indicator = StatusIndicator("回零")
        indicator_layout.addWidget(self._homed_indicator)

        self._target_indicator = StatusIndicator("到位")
        indicator_layout.addWidget(self._target_indicator)

        layout.addLayout(indicator_layout)

        # 行程进度条
        stroke_layout = QVBoxLayout()
        stroke_layout.addWidget(QLabel("行程位置:"))
        self._stroke_bar = QProgressBar()
        self._stroke_bar.setMinimum(0)
        self._stroke_bar.setMaximum(100)
        self._stroke_bar.setValue(0)
        self._stroke_bar.setTextVisible(True)
        self._stroke_bar.setFormat("%v%")
        stroke_layout.addWidget(self._stroke_bar)

        layout.addLayout(stroke_layout)

    def update_status(self) -> None:
        """更新状态显示"""
        try:
            status = self._service.get_axis_status()
            config = self._service.get_axis_config()

            # 更新位置
            self._position_label.setText(f"{status.position_mm:.3f}")

            # 更新速度
            self._velocity_label.setText(f"{status.velocity_mm_s:.2f}")

            # 更新转矩 (需要从 motor 获取)
            # self._torque_label.setText(f"{status.torque / 10:.1f}")

            # 更新状态
            self._state_label.setText(status.state.value)
            self._update_state_style(status.state)

            # 更新操作模式
            mode_names = {
                1: "轮廓位置",
                2: "速度",
                3: "轮廓速度",
                4: "轮廓转矩",
                6: "回零",
                7: "插补位置",
                8: "周期位置",
                9: "周期速度",
                10: "周期转矩",
            }
            # mode_name = mode_names.get(status.operation_mode, f"未知({status.operation_mode})")
            # self._mode_label.setText(mode_name)

            # 更新错误码
            if status.error_code:
                self._error_label.setText(f"0x{status.error_code:04X}")
                self._error_label.setProperty("class", "status-error")
            else:
                self._error_label.setText("无")
                self._error_label.setProperty("class", "")

            # 更新指示灯
            self._enabled_indicator.set_active(status.is_enabled)
            self._fault_indicator.set_active(status.is_fault, is_error=True)
            self._homed_indicator.set_active(status.is_homed)
            self._target_indicator.set_active(status.is_target_reached)

            # 更新行程进度条
            stroke_percent = (
                (status.position_mm - config.stroke_min)
                / (config.stroke_max - config.stroke_min)
                * 100
            )
            stroke_percent = max(0, min(100, stroke_percent))
            self._stroke_bar.setValue(int(stroke_percent))

        except Exception as e:
            logger.debug(f"更新状态失败: {e}")

    def _update_state_style(self, state: DriveState) -> None:
        """更新状态文字样式"""
        if state == DriveState.OPERATION_ENABLED:
            self._state_label.setProperty("class", "status-ok")
        elif state == DriveState.FAULT:
            self._state_label.setProperty("class", "status-error")
        elif state in (DriveState.READY_TO_SWITCH_ON, DriveState.SWITCHED_ON):
            self._state_label.setProperty("class", "status-warning")
        else:
            self._state_label.setProperty("class", "")

        self._state_label.style().unpolish(self._state_label)
        self._state_label.style().polish(self._state_label)


class StatusIndicator(QWidget):
    """状态指示灯组件"""

    def __init__(self, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_active = False
        self._is_error = False
        self._init_ui(label)

    def _init_ui(self, label: str) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # 指示灯
        self._light = QLabel()
        self._light.setFixedSize(20, 20)
        self._light.setAlignment(Qt.AlignCenter)
        self._update_light_style()
        layout.addWidget(self._light, alignment=Qt.AlignCenter)

        # 标签
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)

    def set_active(self, active: bool, is_error: bool = False) -> None:
        """设置激活状态"""
        self._is_active = active
        self._is_error = is_error
        self._update_light_style()

    def _update_light_style(self) -> None:
        """更新指示灯样式"""
        if self._is_active:
            if self._is_error:
                color = "#d9534f"  # 红色
            else:
                color = "#5cb85c"  # 绿色
        else:
            color = "#cccccc"  # 灰色

        self._light.setStyleSheet(
            f"""
            background-color: {color};
            border-radius: 10px;
            border: 1px solid #999999;
            """
        )
