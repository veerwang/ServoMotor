"""
轴选择面板组件

提供 X/Y/Z 轴选择功能。
"""

import logging
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from servo_service import AxisName, ServoService, get_axis_config

logger = logging.getLogger(__name__)


class AxisPanel(QGroupBox):
    """
    轴选择面板

    用于选择当前控制的轴 (X/Y/Z)。
    """

    # 信号
    axis_changed = pyqtSignal(AxisName)

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化轴选择面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__("轴选择", parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 轴选择按钮组
        axis_layout = QHBoxLayout()
        self._axis_group = QButtonGroup(self)

        for axis in AxisName:
            config = get_axis_config(axis)
            radio = QRadioButton(f"{axis.value} 轴")
            radio.setToolTip(
                f"型号: {config.model}\n"
                f"功率: {config.motor_power}W\n"
                f"行程: {config.stroke_min}-{config.stroke_max}mm"
            )
            self._axis_group.addButton(radio, axis.value.encode()[0])  # X=88, Y=89, Z=90
            axis_layout.addWidget(radio)

            # 默认选中 Z 轴
            if axis == AxisName.Z:
                radio.setChecked(True)

        layout.addLayout(axis_layout)

        # 当前轴信息
        self._info_label = QLabel()
        self._update_info(AxisName.Z)
        layout.addWidget(self._info_label)

        # 连接信号
        self._axis_group.buttonClicked.connect(self._on_axis_clicked)

    def _on_axis_clicked(self, button: QRadioButton) -> None:
        """轴选择按钮点击"""
        axis_name = button.text()[0]  # 获取第一个字符 X/Y/Z
        axis = AxisName(axis_name)

        self._service.current_axis = axis
        self._update_info(axis)
        self.axis_changed.emit(axis)

        logger.debug(f"选择轴: {axis.value}")

    def _update_info(self, axis: AxisName) -> None:
        """更新轴信息显示"""
        config = get_axis_config(axis)
        info_text = (
            f"<b>{axis.value} 轴</b> | "
            f"从站: {config.slave_id} | "
            f"型号: {config.model} | "
            f"行程: {config.stroke_min:.0f}-{config.stroke_max:.0f}mm | "
            f"最大速度: {config.max_velocity:.0f}mm/s"
        )
        if config.has_brake:
            info_text += " | <span style='color:#f0ad4e'>带抱闸</span>"

        self._info_label.setText(info_text)

    def get_current_axis(self) -> AxisName:
        """获取当前选中的轴"""
        return self._service.current_axis

    def set_current_axis(self, axis: AxisName) -> None:
        """设置当前轴"""
        for button in self._axis_group.buttons():
            if button.text()[0] == axis.value:
                button.setChecked(True)
                self._on_axis_clicked(button)
                break
