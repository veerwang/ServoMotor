"""
参数设置面板组件

提供运动参数设置功能。
"""

import logging
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from servo_service import ServoService
from ..i18n import tr

logger = logging.getLogger(__name__)


class ParameterPanel(QGroupBox):
    """
    参数设置面板

    用于设置速度、加减速等运动参数。
    """

    # 参数应用信号 (velocity, acceleration, deceleration)
    parameters_applied = pyqtSignal(float, float, float)

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化参数面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__(tr("param.title"), parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 参数表单
        self._form_layout = QFormLayout()

        # 速度
        self._velocity_spin = QDoubleSpinBox()
        self._velocity_spin.setRange(0.1, 1000)
        self._velocity_spin.setValue(100)
        self._velocity_spin.setSuffix(" mm/s")
        self._velocity_spin.setDecimals(1)
        self._velocity_label = tr("param.velocity")
        self._form_layout.addRow(self._velocity_label, self._velocity_spin)

        # 加速度
        self._accel_spin = QDoubleSpinBox()
        self._accel_spin.setRange(1, 5000)
        self._accel_spin.setValue(500)
        self._accel_spin.setSuffix(" mm/s²")
        self._accel_spin.setDecimals(1)
        self._accel_label = tr("param.acceleration")
        self._form_layout.addRow(self._accel_label, self._accel_spin)

        # 减速度
        self._decel_spin = QDoubleSpinBox()
        self._decel_spin.setRange(1, 5000)
        self._decel_spin.setValue(500)
        self._decel_spin.setSuffix(" mm/s²")
        self._decel_spin.setDecimals(1)
        self._decel_label = tr("param.deceleration")
        self._form_layout.addRow(self._decel_label, self._decel_spin)

        layout.addLayout(self._form_layout)

        # 应用按钮
        btn_layout = QHBoxLayout()

        self._apply_btn = QPushButton(tr("param.apply"))
        self._apply_btn.clicked.connect(self._apply_parameters)
        btn_layout.addWidget(self._apply_btn)

        self._read_btn = QPushButton(tr("param.read"))
        self._read_btn.clicked.connect(self._read_parameters)
        btn_layout.addWidget(self._read_btn)

        layout.addLayout(btn_layout)

        # 加载默认值按钮
        self._load_default_btn = QPushButton(tr("param.load_default"))
        self._load_default_btn.clicked.connect(self._load_defaults)
        layout.addWidget(self._load_default_btn)

    def _apply_parameters(self) -> None:
        """应用参数到电机"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("param.connect_first"))
            return

        try:
            velocity = self._velocity_spin.value()
            accel = self._accel_spin.value()
            decel = self._decel_spin.value()

            self._service.set_velocity(velocity)
            self._service.set_acceleration(accel)
            self._service.set_deceleration(decel)

            # 发出信号同步其他面板
            self.parameters_applied.emit(velocity, accel, decel)

            QMessageBox.information(self, tr("common.success"), tr("param.applied"))
            logger.info(f"参数已应用: 速度={velocity}, 加速度={accel}, 减速度={decel}")

        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('param.apply_failed')}: {e}")
            logger.error(f"应用参数失败: {e}")

    def _read_parameters(self) -> None:
        """从电机读取当前参数"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("param.connect_first"))
            return

        try:
            velocity = self._service.get_profile_velocity()
            accel = self._service.get_profile_acceleration()
            decel = self._service.get_profile_deceleration()

            self._velocity_spin.setValue(velocity)
            self._accel_spin.setValue(accel)
            self._decel_spin.setValue(decel)

            logger.info(f"已读取参数: 速度={velocity:.1f}, 加速度={accel:.1f}, 减速度={decel:.1f}")
            QMessageBox.information(
                self, tr("common.success"),
                tr("param.read_success_detail", vel=velocity, accel=accel, decel=decel)
            )
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('param.read_failed')}: {e}")
            logger.error(f"读取参数失败: {e}")

    def _load_defaults(self) -> None:
        """加载默认值"""
        config = self._service.get_axis_config()

        self._velocity_spin.setValue(config.default_velocity)
        self._accel_spin.setValue(config.default_acceleration)
        self._decel_spin.setValue(config.default_deceleration)

        logger.info("已加载默认参数")

    def update_from_config(self) -> None:
        """从配置更新显示"""
        self._load_defaults()

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("param.title"))

        # 更新表单行标签 (需要重新设置)
        # 由于 QFormLayout 不支持直接更新行标签，这里更新按钮文本
        self._apply_btn.setText(tr("param.apply"))
        self._read_btn.setText(tr("param.read"))
        self._load_default_btn.setText(tr("param.load_default"))
