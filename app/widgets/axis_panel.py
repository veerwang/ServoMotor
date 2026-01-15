"""
轴选择面板组件

提供 Z4/Y/Z 轴选择功能。
"""

import logging
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from servo_service import AxisName, ServoService, get_axis_config
from ..i18n import tr

logger = logging.getLogger(__name__)


class AxisPanel(QGroupBox):
    """
    轴选择面板

    用于选择当前控制的轴 (Z4/Y/Z)。
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
        super().__init__(tr("axis.title"), parent)
        self._service = service
        self._axis_buttons = {}
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 轴选择按钮组
        axis_layout = QHBoxLayout()
        axis_layout.setSpacing(8)
        self._axis_group = QButtonGroup(self)
        self._axis_group.setExclusive(True)

        # 按钮样式
        self._button_style_normal = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                min-width: 60px;
                min-height: 40px;
                border: 2px solid #555;
                border-radius: 6px;
                background-color: #3a3a3a;
                color: #aaa;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666;
            }
        """
        self._button_style_selected = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                min-width: 60px;
                min-height: 40px;
                border: 2px solid #4fc3f7;
                border-radius: 6px;
                background-color: #1565c0;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """

        for idx, axis in enumerate(AxisName):
            config = get_axis_config(axis)
            btn = QPushButton(axis.value)
            btn.setCheckable(True)
            btn.setToolTip(
                f"{tr('axis.model')}: {config.model}\n"
                f"{tr('axis.power')}: {config.motor_power}W\n"
                f"{tr('axis.stroke')}: {config.stroke_min}-{config.stroke_max}mm"
            )
            btn.setStyleSheet(self._button_style_normal)
            self._axis_group.addButton(btn, idx)
            axis_layout.addWidget(btn)
            self._axis_buttons[axis] = btn

            # 默认选中 Z4 轴
            if axis == AxisName.Z4:
                btn.setChecked(True)
                btn.setStyleSheet(self._button_style_selected)

        layout.addLayout(axis_layout)

        # 当前轴信息
        self._info_label = QLabel()
        self._update_info(AxisName.Z4)
        layout.addWidget(self._info_label)

        # 连接信号
        self._axis_group.buttonClicked.connect(self._on_axis_clicked)

    def _on_axis_clicked(self, button: QPushButton) -> None:
        """轴选择按钮点击"""
        axis_name = button.text()  # 获取完整轴名 (Z4/Y2/Z3)
        axis = AxisName(axis_name)

        # 如果点击的是当前轴，无需处理
        if axis == self._service.current_axis:
            return

        # 记录之前的轴，用于切换失败时恢复
        previous_axis = self._service.current_axis

        # 使用安全的轴切换方法
        if self._service.is_connected:
            success = self._service.switch_axis(axis)
            if not success:
                # 切换失败，恢复按钮状态
                self._restore_button_state(previous_axis)
                # 显示警告消息
                config = get_axis_config(axis)
                QMessageBox.warning(
                    self,
                    tr("axis.switch_failed_title"),
                    tr("axis.switch_failed_message").format(
                        axis=axis.value,
                        slave_id=config.slave_id
                    )
                )
                logger.warning(f"轴切换失败: {axis.value} 无响应")
                return
        else:
            # 未连接时直接切换
            self._service.current_axis = axis

        # 切换成功，更新所有按钮样式
        for ax, btn in self._axis_buttons.items():
            if ax == axis:
                btn.setStyleSheet(self._button_style_selected)
            else:
                btn.setStyleSheet(self._button_style_normal)

        self._update_info(axis)
        self.axis_changed.emit(axis)
        logger.debug(f"选择轴: {axis.value}")

    def _restore_button_state(self, axis: AxisName) -> None:
        """恢复按钮状态到指定轴"""
        for ax, btn in self._axis_buttons.items():
            if ax == axis:
                btn.setChecked(True)
                btn.setStyleSheet(self._button_style_selected)
            else:
                btn.setChecked(False)
                btn.setStyleSheet(self._button_style_normal)

    def _update_info(self, axis: AxisName) -> None:
        """更新轴信息显示"""
        config = get_axis_config(axis)
        info_text = (
            f"<b>{tr(f'axis.{axis.value.lower()}')}</b> | "
            f"{tr('axis.slave')}: {config.slave_id} | "
            f"{tr('axis.model')}: {config.model} | "
            f"{tr('axis.stroke')}: {config.stroke_min:.0f}-{config.stroke_max:.0f}mm | "
            f"{tr('axis.max_speed')}: {config.max_velocity:.0f}mm/s"
        )
        if config.has_brake:
            info_text += f" | <span style='color:#ffc107'>{tr('axis.with_brake')}</span>"

        self._info_label.setText(info_text)

    def get_current_axis(self) -> AxisName:
        """获取当前选中的轴"""
        return self._service.current_axis

    def set_current_axis(self, axis: AxisName) -> None:
        """设置当前轴"""
        for button in self._axis_group.buttons():
            if button.text() == axis.value:
                button.setChecked(True)
                self._on_axis_clicked(button)
                break

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("axis.title"))

        for axis, btn in self._axis_buttons.items():
            config = get_axis_config(axis)
            # 按钮文字只显示轴名 (Z4/Y/Z)，不需要翻译
            btn.setToolTip(
                f"{tr('axis.model')}: {config.model}\n"
                f"{tr('axis.power')}: {config.motor_power}W\n"
                f"{tr('axis.stroke')}: {config.stroke_min}-{config.stroke_max}mm"
            )

        self._update_info(self._service.current_axis)
