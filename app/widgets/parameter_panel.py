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
        super().__init__("运动参数", parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 参数表单
        form_layout = QFormLayout()

        # 速度
        self._velocity_spin = QDoubleSpinBox()
        self._velocity_spin.setRange(0.1, 1000)
        self._velocity_spin.setValue(100)
        self._velocity_spin.setSuffix(" mm/s")
        self._velocity_spin.setDecimals(1)
        form_layout.addRow("默认速度:", self._velocity_spin)

        # 加速度
        self._accel_spin = QDoubleSpinBox()
        self._accel_spin.setRange(1, 5000)
        self._accel_spin.setValue(500)
        self._accel_spin.setSuffix(" mm/s²")
        self._accel_spin.setDecimals(1)
        form_layout.addRow("加速度:", self._accel_spin)

        # 减速度
        self._decel_spin = QDoubleSpinBox()
        self._decel_spin.setRange(1, 5000)
        self._decel_spin.setValue(500)
        self._decel_spin.setSuffix(" mm/s²")
        self._decel_spin.setDecimals(1)
        form_layout.addRow("减速度:", self._decel_spin)

        layout.addLayout(form_layout)

        # 应用按钮
        btn_layout = QHBoxLayout()

        self._apply_btn = QPushButton("应用参数")
        self._apply_btn.clicked.connect(self._apply_parameters)
        btn_layout.addWidget(self._apply_btn)

        self._read_btn = QPushButton("读取当前")
        self._read_btn.clicked.connect(self._read_parameters)
        btn_layout.addWidget(self._read_btn)

        layout.addLayout(btn_layout)

        # 加载默认值按钮
        self._load_default_btn = QPushButton("加载默认值")
        self._load_default_btn.clicked.connect(self._load_defaults)
        layout.addWidget(self._load_default_btn)

    def _apply_parameters(self) -> None:
        """应用参数到电机"""
        if not self._service.is_connected:
            QMessageBox.warning(self, "警告", "请先连接到伺服系统")
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

            QMessageBox.information(self, "成功", "参数已应用")
            logger.info(f"参数已应用: 速度={velocity}, 加速度={accel}, 减速度={decel}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"应用参数失败: {e}")
            logger.error(f"应用参数失败: {e}")

    def _read_parameters(self) -> None:
        """从电机读取当前参数"""
        if not self._service.is_connected:
            QMessageBox.warning(self, "警告", "请先连接到伺服系统")
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
                self, "成功",
                f"已读取当前参数:\n"
                f"速度: {velocity:.1f} mm/s\n"
                f"加速度: {accel:.1f} mm/s²\n"
                f"减速度: {decel:.1f} mm/s²"
            )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取参数失败: {e}")
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
