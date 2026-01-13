"""
运动控制面板组件

提供点动、位置移动、回零等运动控制功能。
"""

import logging
from typing import Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from servo_service import HomingMethod, ServoService
from ..i18n import tr

logger = logging.getLogger(__name__)


class MotionWorker(QThread):
    """运动控制工作线程"""

    finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, task: callable, parent: Optional[QThread] = None) -> None:
        super().__init__(parent)
        self._task = task

    def run(self) -> None:
        try:
            self._task()
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class MotionPanel(QGroupBox):
    """
    运动控制面板

    提供点动、位置移动、回零等控制功能。
    """

    # 运动开始/结束信号 (用于暂停/恢复状态定时器)
    motion_started = pyqtSignal()
    motion_finished = pyqtSignal()

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化运动控制面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__(tr("motion.title"), parent)
        self._service = service
        self._worker: Optional[MotionWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 使能/停止按钮组
        control_layout = QHBoxLayout()

        self._enable_btn = QPushButton(tr("motion.enable"))
        self._enable_btn.setProperty("class", "success")
        self._enable_btn.clicked.connect(self.enable_clicked)
        control_layout.addWidget(self._enable_btn)

        self._disable_btn = QPushButton(tr("motion.disable"))
        self._disable_btn.clicked.connect(self.disable_clicked)
        control_layout.addWidget(self._disable_btn)

        self._stop_btn = QPushButton(tr("motion.stop"))
        self._stop_btn.setProperty("class", "warning")
        self._stop_btn.clicked.connect(self.stop_clicked)
        control_layout.addWidget(self._stop_btn)

        self._quick_stop_btn = QPushButton(tr("motion.quick_stop"))
        self._quick_stop_btn.setProperty("class", "danger")
        self._quick_stop_btn.clicked.connect(self.quick_stop_clicked)
        control_layout.addWidget(self._quick_stop_btn)

        layout.addLayout(control_layout)

        # 选项卡
        self._tab_widget = QTabWidget()

        # 点动控制页
        jog_tab = self._create_jog_tab()
        self._tab_widget.addTab(jog_tab, tr("motion.jog"))

        # 位置控制页
        position_tab = self._create_position_tab()
        self._tab_widget.addTab(position_tab, tr("motion.position"))

        # 回零控制页
        home_tab = self._create_home_tab()
        self._tab_widget.addTab(home_tab, tr("motion.home"))

        layout.addWidget(self._tab_widget)

    def _create_jog_tab(self) -> QWidget:
        """创建点动控制页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 速度设置
        speed_layout = QFormLayout()
        self._jog_speed_spin = QDoubleSpinBox()
        self._jog_speed_spin.setRange(0.1, 1000)
        self._jog_speed_spin.setValue(100)
        self._jog_speed_spin.setSuffix(" mm/s")
        self._jog_speed_spin.setDecimals(1)
        self._jog_speed_label = QLabel(tr("motion.jog_speed"))
        speed_layout.addRow(self._jog_speed_label, self._jog_speed_spin)
        layout.addLayout(speed_layout)

        # 方向按钮
        dir_layout = QHBoxLayout()

        self._jog_neg_btn = QPushButton(tr("motion.negative"))
        self._jog_neg_btn.pressed.connect(lambda: self._start_jog(-1))
        self._jog_neg_btn.released.connect(self._stop_jog)
        dir_layout.addWidget(self._jog_neg_btn)

        self._jog_pos_btn = QPushButton(tr("motion.positive"))
        self._jog_pos_btn.pressed.connect(lambda: self._start_jog(1))
        self._jog_pos_btn.released.connect(self._stop_jog)
        dir_layout.addWidget(self._jog_pos_btn)

        layout.addLayout(dir_layout)

        # 步进移动
        step_layout = QHBoxLayout()

        self._step_spin = QDoubleSpinBox()
        self._step_spin.setRange(0.001, 100)
        self._step_spin.setValue(1.0)
        self._step_spin.setSuffix(" mm")
        self._step_spin.setDecimals(3)
        self._step_label = QLabel(tr("motion.step"))
        step_layout.addWidget(self._step_label)
        step_layout.addWidget(self._step_spin)

        self._step_neg_btn = QPushButton("-")
        self._step_neg_btn.setMaximumWidth(40)
        self._step_neg_btn.clicked.connect(lambda: self._step_move(-1))
        step_layout.addWidget(self._step_neg_btn)

        self._step_pos_btn = QPushButton("+")
        self._step_pos_btn.setMaximumWidth(40)
        self._step_pos_btn.clicked.connect(lambda: self._step_move(1))
        step_layout.addWidget(self._step_pos_btn)

        layout.addLayout(step_layout)

        layout.addStretch()
        return widget

    def _create_position_tab(self) -> QWidget:
        """创建位置控制页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 位置设置
        form_layout = QFormLayout()

        self._target_pos_spin = QDoubleSpinBox()
        self._target_pos_spin.setRange(-10000, 10000)
        self._target_pos_spin.setValue(0)
        self._target_pos_spin.setSuffix(" mm")
        self._target_pos_spin.setDecimals(3)
        self._target_pos_label = QLabel(tr("motion.target_pos"))
        form_layout.addRow(self._target_pos_label, self._target_pos_spin)

        self._pos_speed_spin = QDoubleSpinBox()
        self._pos_speed_spin.setRange(0.1, 1000)
        self._pos_speed_spin.setValue(100)
        self._pos_speed_spin.setSuffix(" mm/s")
        self._pos_speed_spin.setDecimals(1)
        self._move_speed_label = QLabel(tr("motion.move_speed"))
        form_layout.addRow(self._move_speed_label, self._pos_speed_spin)

        layout.addLayout(form_layout)

        # 移动按钮
        btn_layout = QHBoxLayout()

        self._move_abs_btn = QPushButton(tr("motion.move_abs"))
        self._move_abs_btn.setProperty("class", "success")
        self._move_abs_btn.clicked.connect(self._move_absolute)
        btn_layout.addWidget(self._move_abs_btn)

        self._move_rel_btn = QPushButton(tr("motion.move_rel"))
        self._move_rel_btn.clicked.connect(self._move_relative)
        btn_layout.addWidget(self._move_rel_btn)

        layout.addLayout(btn_layout)

        # 快速定位按钮
        preset_layout = QGridLayout()
        self._quick_pos_label = QLabel(tr("motion.quick_pos"))
        preset_layout.addWidget(self._quick_pos_label, 0, 0, 1, 4)

        self._preset_btns = {}
        presets = [
            ("min", tr("motion.min")),
            ("mid", tr("motion.mid")),
            ("max", tr("motion.max")),
        ]
        for i, (pos, label) in enumerate(presets):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, p=pos: self._move_preset(p))
            preset_layout.addWidget(btn, 1, i)
            self._preset_btns[pos] = btn

        layout.addLayout(preset_layout)

        layout.addStretch()
        return widget

    def _create_home_tab(self) -> QWidget:
        """创建回零控制页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 回零按钮
        self._home_btn = QPushButton(tr("motion.start_home"))
        self._home_btn.setProperty("class", "success")
        self._home_btn.clicked.connect(self.home_clicked)
        layout.addWidget(self._home_btn)

        # 设置当前位置为原点
        self._set_home_btn = QPushButton(tr("motion.set_home"))
        self._set_home_btn.clicked.connect(self._set_current_as_home)
        layout.addWidget(self._set_home_btn)

        # 故障复位
        self._fault_reset_btn = QPushButton(tr("motion.fault_reset"))
        self._fault_reset_btn.setProperty("class", "warning")
        self._fault_reset_btn.clicked.connect(self._fault_reset)
        layout.addWidget(self._fault_reset_btn)

        layout.addStretch()
        return widget

    # ==================== 点动控制 ====================

    def _start_jog(self, direction: int) -> None:
        """开始点动"""
        if not self._service.is_connected:
            return

        try:
            speed = self._jog_speed_spin.value() * direction
            self._service.jog(speed)
        except Exception as e:
            logger.error(f"点动失败: {e}")

    def _stop_jog(self) -> None:
        """停止点动"""
        if not self._service.is_connected:
            return

        try:
            self._service.stop(wait=False)
        except Exception as e:
            logger.error(f"停止点动失败: {e}")

    def _step_move(self, direction: int) -> None:
        """步进移动"""
        if not self._service.is_connected:
            return

        try:
            distance = self._step_spin.value() * direction
            speed = self._jog_speed_spin.value()
            self._run_motion(lambda: self._service.move_by(distance, speed))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('motion.step_failed')}: {e}")

    # ==================== 位置控制 ====================

    def _move_absolute(self) -> None:
        """绝对位置移动"""
        if not self._service.is_connected:
            return

        position = self._target_pos_spin.value()
        speed = self._pos_speed_spin.value()

        self._run_motion(lambda: self._service.move_to(position, speed))

    def _move_relative(self) -> None:
        """相对位置移动"""
        if not self._service.is_connected:
            return

        distance = self._target_pos_spin.value()
        speed = self._pos_speed_spin.value()

        self._run_motion(lambda: self._service.move_by(distance, speed))

    def _move_preset(self, preset: str) -> None:
        """移动到预设位置"""
        if not self._service.is_connected:
            return

        config = self._service.get_axis_config()
        speed = self._pos_speed_spin.value()

        if preset == "min":
            position = config.stroke_min
        elif preset == "max":
            position = config.stroke_max
        elif preset == "mid":
            position = (config.stroke_min + config.stroke_max) / 2
        else:
            return

        self._run_motion(lambda: self._service.move_to(position, speed))

    # ==================== 回零控制 ====================

    def home_clicked(self) -> None:
        """回零按钮点击"""
        if not self._service.is_connected:
            return

        reply = QMessageBox.question(
            self,
            tr("common.confirm"),
            tr("motion.home_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._run_motion(lambda: self._service.home())

    def _set_current_as_home(self) -> None:
        """将当前位置设为原点"""
        if not self._service.is_connected:
            return

        try:
            self._service.set_home_position()
            QMessageBox.information(self, tr("common.success"), tr("motion.set_home_success"))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('motion.set_home_failed')}: {e}")

    def _fault_reset(self) -> None:
        """故障复位"""
        if not self._service.is_connected:
            return

        try:
            self._service.fault_reset()
            QMessageBox.information(self, tr("common.success"), tr("motion.fault_reset_success"))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('motion.fault_reset_failed')}: {e}")

    # ==================== 使能控制 ====================

    def enable_clicked(self) -> None:
        """使能按钮点击"""
        if not self._service.is_connected:
            return

        try:
            self._service.enable()
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('motion.enable_failed')}: {e}")

    def disable_clicked(self) -> None:
        """禁用按钮点击"""
        if not self._service.is_connected:
            return

        try:
            self._service.disable()
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('motion.disable_failed')}: {e}")

    def stop_clicked(self) -> None:
        """停止按钮点击"""
        if not self._service.is_connected:
            return

        try:
            self._service.stop(wait=False)
        except Exception as e:
            logger.error(f"停止失败: {e}")

    def quick_stop_clicked(self) -> None:
        """快速停止按钮点击"""
        if not self._service.is_connected:
            return

        try:
            self._service.quick_stop()
        except Exception as e:
            logger.error(f"快速停止失败: {e}")

    # ==================== 辅助方法 ====================

    def _run_motion(self, task: callable) -> None:
        """在后台线程运行运动任务"""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, tr("common.warning"), tr("motion.operation_in_progress"))
            return

        self._set_buttons_enabled(False)

        # 通知暂停状态定时器 (避免通信冲突)
        self.motion_started.emit()

        self._worker = MotionWorker(task)
        self._worker.finished.connect(self._on_motion_finished)
        self._worker.start()

    def _on_motion_finished(self, success: bool, message: str) -> None:
        """运动完成回调"""
        self._set_buttons_enabled(True)

        # 通知恢复状态定时器
        self.motion_finished.emit()

        if not success:
            QMessageBox.warning(self, tr("motion.motion_failed"), message)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """设置按钮启用状态"""
        self._move_abs_btn.setEnabled(enabled)
        self._move_rel_btn.setEnabled(enabled)
        self._home_btn.setEnabled(enabled)
        self._step_neg_btn.setEnabled(enabled)
        self._step_pos_btn.setEnabled(enabled)

    def update_velocity(self, velocity: float) -> None:
        """
        更新速度控件的值

        Args:
            velocity: 速度值 (mm/s)
        """
        self._jog_speed_spin.setValue(velocity)
        self._pos_speed_spin.setValue(velocity)
        logger.info(f"运动面板速度已更新: {velocity} mm/s")

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        # 标题
        self.setTitle(tr("motion.title"))

        # 使能/停止按钮
        self._enable_btn.setText(tr("motion.enable"))
        self._disable_btn.setText(tr("motion.disable"))
        self._stop_btn.setText(tr("motion.stop"))
        self._quick_stop_btn.setText(tr("motion.quick_stop"))

        # 选项卡
        self._tab_widget.setTabText(0, tr("motion.jog"))
        self._tab_widget.setTabText(1, tr("motion.position"))
        self._tab_widget.setTabText(2, tr("motion.home"))

        # 点动控制页
        self._jog_speed_label.setText(tr("motion.jog_speed"))
        self._jog_neg_btn.setText(tr("motion.negative"))
        self._jog_pos_btn.setText(tr("motion.positive"))
        self._step_label.setText(tr("motion.step"))

        # 位置控制页
        self._target_pos_label.setText(tr("motion.target_pos"))
        self._move_speed_label.setText(tr("motion.move_speed"))
        self._move_abs_btn.setText(tr("motion.move_abs"))
        self._move_rel_btn.setText(tr("motion.move_rel"))
        self._quick_pos_label.setText(tr("motion.quick_pos"))
        self._preset_btns["min"].setText(tr("motion.min"))
        self._preset_btns["mid"].setText(tr("motion.mid"))
        self._preset_btns["max"].setText(tr("motion.max"))

        # 回零控制页
        self._home_btn.setText(tr("motion.start_home"))
        self._set_home_btn.setText(tr("motion.set_home"))
        self._fault_reset_btn.setText(tr("motion.fault_reset"))
