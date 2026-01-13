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
from ..i18n import tr, get_language, Language

logger = logging.getLogger(__name__)

# 故障码定义 (中文, 英文)
ERROR_CODES = {
    # 电流/过载
    0x2300: ("电机过流", "Motor overcurrent"),
    0x2311: ("电机过载", "Motor overload"),
    0x2312: ("电机堵转", "Motor stalling"),
    # 电压
    0x3210: ("电源过压", "Power overvoltage"),
    0x3220: ("电源欠压", "Power undervoltage"),
    # 温度
    0x4210: ("过温保护", "Over temperature"),
    0x4220: ("低温保护", "Low temperature"),
    # 参数
    0x6320: ("参数设置错误", "Parameter setting error"),
    # 编码器
    0x7301: ("编码器电池电压过低", "Encoder battery low voltage"),
    0x7302: ("编码器电池警告", "Encoder battery warning"),
    0x7303: ("编码器通信失败", "Encoder communication failure"),
    0x7304: ("编码器多圈未校准", "Encoder multi-turn not calibrated"),
    0x7309: ("编码器内部故障", "Encoder internal fault"),
    0x7310: ("超速", "Overspeed"),
    # 通信
    0x7501: ("通信看门狗超时", "Communication watchdog timeout"),
    # 运动
    0x8610: ("回零超时", "Homing timeout"),
    0x8611: ("跟随误差", "Following error"),
    0x8613: ("软件限位", "Software position limit"),
    0x8614: ("限位开关触发", "Limit switch triggered"),
    # STO
    0xFF05: ("STO_1 关断失败", "STO_1 failed to close"),
    0xFF06: ("STO_1 使能失败", "STO_1 failed to enable"),
    0xFF07: ("STO_2 关断失败", "STO_2 failed to close"),
    0xFF08: ("STO_2 使能失败", "STO_2 failed to enable"),
    0xFF09: ("STO 输入异常", "STO input abnormal"),
    0xFF0A: ("STO 使能状态", "STO enabled state"),
}


def get_error_description(error_code: int) -> str:
    """获取故障码描述"""
    if error_code == 0:
        return ""

    # 尝试精确匹配
    if error_code in ERROR_CODES:
        zh, en = ERROR_CODES[error_code]
        return zh if get_language() == Language.CHINESE else en

    # 尝试匹配低16位 (有些错误码高位有额外信息)
    low_code = error_code & 0xFFFF
    if low_code in ERROR_CODES:
        zh, en = ERROR_CODES[low_code]
        return zh if get_language() == Language.CHINESE else en

    # 未知故障码
    return "未知故障" if get_language() == Language.CHINESE else "Unknown fault"


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
        super().__init__(tr("status_panel.title"), parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 位置和速度显示
        pos_vel_layout = QGridLayout()

        # 位置
        self._pos_title = QLabel(tr("status_panel.position"))
        pos_vel_layout.addWidget(self._pos_title, 0, 0)
        self._position_label = QLabel("0.000")
        self._position_label.setProperty("class", "value")
        self._position_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pos_vel_layout.addWidget(self._position_label, 0, 1)
        pos_vel_layout.addWidget(QLabel("mm"), 0, 2)

        # 速度
        self._vel_title = QLabel(tr("status_panel.velocity"))
        pos_vel_layout.addWidget(self._vel_title, 1, 0)
        self._velocity_label = QLabel("0.00")
        self._velocity_label.setProperty("class", "value")
        self._velocity_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pos_vel_layout.addWidget(self._velocity_label, 1, 1)
        pos_vel_layout.addWidget(QLabel("mm/s"), 1, 2)

        # 转矩 (可选显示)
        self._torque_title = QLabel(tr("status_panel.torque"))
        pos_vel_layout.addWidget(self._torque_title, 2, 0)
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
        self._status_form = QFormLayout()

        # 驱动器状态
        self._state_label = QLabel(tr("status_panel.unknown"))
        self._state_title = QLabel(tr("status_panel.drive_state"))
        self._status_form.addRow(self._state_title, self._state_label)

        # 操作模式
        self._mode_label = QLabel("--")
        self._mode_title = QLabel(tr("status_panel.op_mode"))
        self._status_form.addRow(self._mode_title, self._mode_label)

        # 错误码
        self._error_label = QLabel(tr("status_panel.none"))
        self._error_title = QLabel(tr("status_panel.error_code"))
        self._status_form.addRow(self._error_title, self._error_label)

        layout.addLayout(self._status_form)

        # 状态指示灯
        indicator_layout = QHBoxLayout()

        self._enabled_indicator = StatusIndicator(tr("status_panel.enabled"))
        indicator_layout.addWidget(self._enabled_indicator)

        self._fault_indicator = StatusIndicator(tr("status_panel.fault"))
        indicator_layout.addWidget(self._fault_indicator)

        self._homed_indicator = StatusIndicator(tr("status_panel.homed"))
        indicator_layout.addWidget(self._homed_indicator)

        self._target_indicator = StatusIndicator(tr("status_panel.target"))
        indicator_layout.addWidget(self._target_indicator)

        layout.addLayout(indicator_layout)

        # 行程进度条
        stroke_layout = QVBoxLayout()
        self._stroke_title = QLabel(tr("status_panel.stroke_pos"))
        stroke_layout.addWidget(self._stroke_title)
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
                desc = get_error_description(status.error_code)
                self._error_label.setText(f"0x{status.error_code:04X} - {desc}")
                self._error_label.setProperty("class", "status-error")
                self._error_label.setToolTip(f"故障码: 0x{status.error_code:04X}\n{desc}")
            else:
                self._error_label.setText(tr("status_panel.none"))
                self._error_label.setProperty("class", "")
                self._error_label.setToolTip("")

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

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("status_panel.title"))
        self._pos_title.setText(tr("status_panel.position"))
        self._vel_title.setText(tr("status_panel.velocity"))
        self._torque_title.setText(tr("status_panel.torque"))
        self._state_title.setText(tr("status_panel.drive_state"))
        self._mode_title.setText(tr("status_panel.op_mode"))
        self._error_title.setText(tr("status_panel.error_code"))
        self._stroke_title.setText(tr("status_panel.stroke_pos"))

        # 更新指示灯标签
        self._enabled_indicator.set_label(tr("status_panel.enabled"))
        self._fault_indicator.set_label(tr("status_panel.fault"))
        self._homed_indicator.set_label(tr("status_panel.homed"))
        self._target_indicator.set_label(tr("status_panel.target"))


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
        self._label_widget = QLabel(label)
        self._label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label_widget)

    def set_label(self, text: str) -> None:
        """设置标签文本"""
        self._label_widget.setText(text)

    def set_active(self, active: bool, is_error: bool = False) -> None:
        """设置激活状态"""
        self._is_active = active
        self._is_error = is_error
        self._update_light_style()

    def _update_light_style(self) -> None:
        """更新指示灯样式 - 工业风格"""
        if self._is_active:
            if self._is_error:
                color = "#dc3545"  # 红色 (危险)
                glow = "0 0 8px #dc3545"
            else:
                color = "#28a745"  # 绿色 (正常)
                glow = "0 0 8px #28a745"
        else:
            color = "#4a4a4a"  # 深灰色 (未激活)
            glow = "none"

        self._light.setStyleSheet(
            f"""
            background-color: {color};
            border-radius: 10px;
            border: 2px solid #ffc107;
            """
        )
