"""
主窗口模块

NiMotion 伺服电机控制系统的主窗口。
"""

import logging
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QFont
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from servo_service import AxisName, ServoService

from .widgets.connection_panel import ConnectionPanel
from .widgets.axis_panel import AxisPanel
from .widgets.status_panel import StatusPanel
from .widgets.motion_panel import MotionPanel
from .widgets.parameter_panel import ParameterPanel
from .widgets.modbus_debug_panel import ModbusDebugPanel

logger = logging.getLogger(__name__)


# 视图索引常量
VIEW_MOTOR_CONTROL = 0
VIEW_MODBUS_DEBUG = 1


class MainWindow(QMainWindow):
    """
    主窗口类

    包含所有控制面板和状态显示，支持视图切换。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化主窗口"""
        super().__init__(parent)

        # 创建服务实例
        self._service = ServoService()

        # 状态更新定时器
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)

        # 当前视图
        self._current_view = VIEW_MOTOR_CONTROL

        # 初始化 UI
        self._init_ui()
        self._init_menu()
        self._init_statusbar()
        self._connect_signals()

        # 加载样式
        self._load_styles()

    def _init_ui(self) -> None:
        """初始化用户界面"""
        self.setWindowTitle("NiMotion 伺服电机控制系统")
        self.setMinimumSize(1024, 700)
        self.resize(1280, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧面板 (连接 + 轴选择 + 状态) - 在所有视图中共享
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 连接面板
        self._connection_panel = ConnectionPanel(self._service)
        left_layout.addWidget(self._connection_panel)

        # 轴选择面板
        self._axis_panel = AxisPanel(self._service)
        left_layout.addWidget(self._axis_panel)

        # 状态监控面板 (在所有视图中共享)
        self._status_panel = StatusPanel(self._service)
        left_layout.addWidget(self._status_panel)

        left_layout.addStretch()

        # 右侧使用 StackedWidget 实现视图切换
        self._view_stack = QStackedWidget()

        # 视图 1: 电机控制视图
        self._motor_control_view = self._create_motor_control_view()
        self._view_stack.addWidget(self._motor_control_view)

        # 视图 2: Modbus 调试视图
        self._modbus_debug_view = self._create_modbus_debug_view()
        self._view_stack.addWidget(self._modbus_debug_view)

        # 使用 Splitter 分隔左右面板
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self._view_stack)
        splitter.setSizes([350, 650])

        main_layout.addWidget(splitter)

    def _create_motor_control_view(self) -> QWidget:
        """创建电机控制视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 运动控制面板
        self._motion_panel = MotionPanel(self._service)
        layout.addWidget(self._motion_panel)

        # 参数设置面板
        self._parameter_panel = ParameterPanel(self._service)
        layout.addWidget(self._parameter_panel)

        layout.addStretch()

        return view

    def _create_modbus_debug_view(self) -> QWidget:
        """创建 Modbus 调试视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Modbus 调试面板
        self._modbus_debug_panel = ModbusDebugPanel(self._service)
        layout.addWidget(self._modbus_debug_panel)

        layout.addStretch()

        return view

    def _init_menu(self) -> None:
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        # 创建视图切换动作组（单选）
        view_group = QActionGroup(self)
        view_group.setExclusive(True)

        self._motor_control_action = QAction("电机控制(&M)", self)
        self._motor_control_action.setCheckable(True)
        self._motor_control_action.setChecked(True)
        self._motor_control_action.setShortcut("Ctrl+1")
        self._motor_control_action.triggered.connect(
            lambda: self._switch_view(VIEW_MOTOR_CONTROL)
        )
        view_group.addAction(self._motor_control_action)
        view_menu.addAction(self._motor_control_action)

        self._modbus_debug_action = QAction("Modbus 调试(&D)", self)
        self._modbus_debug_action.setCheckable(True)
        self._modbus_debug_action.setShortcut("Ctrl+2")
        self._modbus_debug_action.triggered.connect(
            lambda: self._switch_view(VIEW_MODBUS_DEBUG)
        )
        view_group.addAction(self._modbus_debug_action)
        view_menu.addAction(self._modbus_debug_action)

        # 连接菜单
        connect_menu = menubar.addMenu("连接(&C)")

        self._connect_action = QAction("连接(&C)", self)
        self._connect_action.setShortcut("Ctrl+O")
        self._connect_action.triggered.connect(self._on_connect)
        connect_menu.addAction(self._connect_action)

        self._disconnect_action = QAction("断开(&D)", self)
        self._disconnect_action.setShortcut("Ctrl+D")
        self._disconnect_action.triggered.connect(self._on_disconnect)
        self._disconnect_action.setEnabled(False)
        connect_menu.addAction(self._disconnect_action)

        # 控制菜单
        control_menu = menubar.addMenu("控制(&O)")

        enable_action = QAction("使能电机(&E)", self)
        enable_action.setShortcut("Ctrl+E")
        enable_action.triggered.connect(self._on_enable)
        control_menu.addAction(enable_action)

        disable_action = QAction("禁用电机(&D)", self)
        disable_action.triggered.connect(self._on_disable)
        control_menu.addAction(disable_action)

        control_menu.addSeparator()

        stop_action = QAction("停止(&S)", self)
        stop_action.setShortcut("Space")
        stop_action.triggered.connect(self._on_stop)
        control_menu.addAction(stop_action)

        quick_stop_action = QAction("快速停止(&Q)", self)
        quick_stop_action.setShortcut("Escape")
        quick_stop_action.triggered.connect(self._on_quick_stop)
        control_menu.addAction(quick_stop_action)

        control_menu.addSeparator()

        home_action = QAction("回零(&H)", self)
        home_action.setShortcut("Ctrl+H")
        home_action.triggered.connect(self._on_home)
        control_menu.addAction(home_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _init_statusbar(self) -> None:
        """初始化状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪 - 电机控制视图")

    def _connect_signals(self) -> None:
        """连接信号"""
        # 连接面板信号
        self._connection_panel.connected.connect(self._on_connected)
        self._connection_panel.disconnected.connect(self._on_disconnected)

        # 轴选择信号
        self._axis_panel.axis_changed.connect(self._on_axis_changed)

        # 运动面板信号 (用于暂停/恢复状态定时器，避免通信冲突)
        self._motion_panel.motion_started.connect(self.pause_status_timer)
        self._motion_panel.motion_finished.connect(self.resume_status_timer)

        # 参数面板信号 (同步运动面板的速度设置)
        self._parameter_panel.parameters_applied.connect(self._on_parameters_applied)

        # Modbus 调试面板信号
        self._modbus_debug_panel.request_pause_timer.connect(self.pause_status_timer)
        self._modbus_debug_panel.request_resume_timer.connect(self.resume_status_timer)

    def _load_styles(self) -> None:
        """加载样式表 - 工业风格黑黄配色"""
        style = """
        /* ==================== 工业风格黑黄配色 ==================== */

        QMainWindow {
            background-color: #1a1a1a;
        }

        QWidget {
            background-color: #1a1a1a;
            color: #e0e0e0;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #ffc107;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #2d2d2d;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: #ffc107;
            background-color: #1a1a1a;
            border: 1px solid #ffc107;
            border-radius: 3px;
        }

        /* ==================== 按钮样式 ==================== */

        QPushButton {
            background-color: #ffc107;
            color: #1a1a1a;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #ffcd39;
            border: 2px solid #ffffff;
        }

        QPushButton:pressed {
            background-color: #d9a406;
        }

        QPushButton:disabled {
            background-color: #4a4a4a;
            color: #808080;
        }

        QPushButton[class="danger"] {
            background-color: #dc3545;
            color: #ffffff;
        }

        QPushButton[class="danger"]:hover {
            background-color: #ff4444;
            border: 2px solid #ffffff;
        }

        QPushButton[class="success"] {
            background-color: #28a745;
            color: #ffffff;
        }

        QPushButton[class="success"]:hover {
            background-color: #34ce57;
            border: 2px solid #ffffff;
        }

        QPushButton[class="warning"] {
            background-color: #ff8c00;
            color: #1a1a1a;
        }

        QPushButton[class="warning"]:hover {
            background-color: #ffa500;
            border: 2px solid #ffffff;
        }

        /* ==================== 输入控件 ==================== */

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            border: 2px solid #555555;
            border-radius: 4px;
            padding: 6px;
            background-color: #2d2d2d;
            color: #e0e0e0;
            selection-background-color: #ffc107;
            selection-color: #1a1a1a;
        }

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #ffc107;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #ffc107;
            width: 24px;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 8px solid #1a1a1a;
        }

        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            color: #e0e0e0;
            selection-background-color: #ffc107;
            selection-color: #1a1a1a;
            border: 2px solid #ffc107;
        }

        QSpinBox::up-button, QDoubleSpinBox::up-button {
            background-color: #ffc107;
            border-top-right-radius: 3px;
        }

        QSpinBox::down-button, QDoubleSpinBox::down-button {
            background-color: #ffc107;
            border-bottom-right-radius: 3px;
        }

        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 6px solid #1a1a1a;
        }

        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #1a1a1a;
        }

        /* ==================== 标签样式 ==================== */

        QLabel {
            color: #e0e0e0;
            background-color: transparent;
        }

        QLabel[class="value"] {
            font-family: "Consolas", "Monaco", monospace;
            font-size: 14px;
            font-weight: bold;
            color: #ffc107;
        }

        QLabel[class="status-ok"] {
            color: #28a745;
            font-weight: bold;
        }

        QLabel[class="status-error"] {
            color: #dc3545;
            font-weight: bold;
        }

        QLabel[class="status-warning"] {
            color: #ff8c00;
            font-weight: bold;
        }

        /* ==================== 单选按钮 ==================== */

        QRadioButton {
            spacing: 8px;
            color: #e0e0e0;
        }

        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #ffc107;
            border-radius: 10px;
            background-color: #2d2d2d;
        }

        QRadioButton::indicator:checked {
            background-color: #ffc107;
            border: 2px solid #ffc107;
        }

        QRadioButton::indicator:checked::after {
            background-color: #1a1a1a;
        }

        /* ==================== 选项卡 ==================== */

        QTabWidget::pane {
            border: 2px solid #ffc107;
            border-radius: 4px;
            background-color: #2d2d2d;
        }

        QTabBar::tab {
            background-color: #3d3d3d;
            color: #e0e0e0;
            padding: 8px 16px;
            border: 1px solid #555555;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #ffc107;
            color: #1a1a1a;
            font-weight: bold;
        }

        QTabBar::tab:hover:!selected {
            background-color: #4a4a4a;
        }

        /* ==================== 状态栏 ==================== */

        QStatusBar {
            background-color: #2d2d2d;
            border-top: 2px solid #ffc107;
            color: #e0e0e0;
        }

        /* ==================== 菜单栏 ==================== */

        QMenuBar {
            background-color: #2d2d2d;
            border-bottom: 2px solid #ffc107;
            color: #e0e0e0;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
        }

        QMenuBar::item:selected {
            background-color: #ffc107;
            color: #1a1a1a;
        }

        QMenu {
            background-color: #2d2d2d;
            border: 2px solid #ffc107;
            color: #e0e0e0;
        }

        QMenu::item {
            padding: 6px 24px;
        }

        QMenu::item:selected {
            background-color: #ffc107;
            color: #1a1a1a;
        }

        QMenu::separator {
            height: 2px;
            background-color: #555555;
            margin: 4px 8px;
        }

        /* ==================== 进度条 ==================== */

        QProgressBar {
            border: 2px solid #555555;
            border-radius: 4px;
            background-color: #2d2d2d;
            text-align: center;
            color: #e0e0e0;
        }

        QProgressBar::chunk {
            background-color: #ffc107;
            border-radius: 2px;
        }

        /* ==================== 分隔线 ==================== */

        QFrame[frameShape="4"],
        QFrame[frameShape="5"] {
            background-color: #555555;
        }

        /* ==================== 滚动条 ==================== */

        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            border: none;
        }

        QScrollBar::handle:vertical {
            background-color: #ffc107;
            min-height: 20px;
            border-radius: 4px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar:horizontal {
            background-color: #2d2d2d;
            height: 12px;
            border: none;
        }

        QScrollBar::handle:horizontal {
            background-color: #ffc107;
            min-width: 20px;
            border-radius: 4px;
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        /* ==================== 分割器 ==================== */

        QSplitter::handle {
            background-color: #ffc107;
            width: 3px;
        }

        QSplitter::handle:hover {
            background-color: #ffcd39;
        }

        /* ==================== 消息框 ==================== */

        QMessageBox {
            background-color: #2d2d2d;
        }

        QMessageBox QLabel {
            color: #e0e0e0;
        }

        /* ==================== 工具提示 ==================== */

        QToolTip {
            background-color: #ffc107;
            color: #1a1a1a;
            border: 2px solid #1a1a1a;
            padding: 4px;
            font-weight: bold;
        }
        """
        self.setStyleSheet(style)

    # ==================== 视图切换 ====================

    def _switch_view(self, view_index: int) -> None:
        """切换视图"""
        self._current_view = view_index
        self._view_stack.setCurrentIndex(view_index)

        # 更新状态栏
        if view_index == VIEW_MOTOR_CONTROL:
            view_name = "电机控制视图"
        else:
            view_name = "Modbus 调试视图"

        if self._service.is_connected:
            self._statusbar.showMessage(f"已连接 - {view_name}")
        else:
            self._statusbar.showMessage(f"就绪 - {view_name}")

        logger.info(f"切换到{view_name}")

    # ==================== 事件处理 ====================

    def _on_connected(self) -> None:
        """连接成功"""
        self._connect_action.setEnabled(False)
        self._disconnect_action.setEnabled(True)

        # 更新状态栏
        view_name = "电机控制视图" if self._current_view == VIEW_MOTOR_CONTROL else "Modbus 调试视图"
        self._statusbar.showMessage(f"已连接 - {view_name}")

        # 启动状态更新
        self._status_timer.start(100)  # 100ms 刷新

        # 更新各面板状态
        self._update_panels_enabled(True)

    def _on_disconnected(self) -> None:
        """断开连接"""
        self._connect_action.setEnabled(True)
        self._disconnect_action.setEnabled(False)

        # 更新状态栏
        view_name = "电机控制视图" if self._current_view == VIEW_MOTOR_CONTROL else "Modbus 调试视图"
        self._statusbar.showMessage(f"已断开 - {view_name}")

        # 停止状态更新
        self._status_timer.stop()

        # 更新各面板状态
        self._update_panels_enabled(False)

    def _on_axis_changed(self, axis: AxisName) -> None:
        """轴切换"""
        self._statusbar.showMessage(f"切换到 {axis.value} 轴")
        self._update_status()

    def _on_parameters_applied(
        self, velocity: float, acceleration: float, deceleration: float
    ) -> None:
        """参数应用后同步到运动面板"""
        self._motion_panel.update_velocity(velocity)
        logger.info(f"参数已同步到运动面板: 速度={velocity}")

    def _on_connect(self) -> None:
        """连接菜单"""
        self._connection_panel.connect_clicked()

    def _on_disconnect(self) -> None:
        """断开菜单"""
        self._connection_panel.disconnect_clicked()

    def _on_enable(self) -> None:
        """使能电机"""
        self._motion_panel.enable_clicked()

    def _on_disable(self) -> None:
        """禁用电机"""
        self._motion_panel.disable_clicked()

    def _on_stop(self) -> None:
        """停止"""
        self._motion_panel.stop_clicked()

    def _on_quick_stop(self) -> None:
        """快速停止"""
        self._motion_panel.quick_stop_clicked()

    def _on_home(self) -> None:
        """回零"""
        self._motion_panel.home_clicked()

    def _on_about(self) -> None:
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h3>NiMotion 伺服电机控制系统</h3>"
            "<p>版本: 0.1.0</p>"
            "<p>基于 PyQt5 和 Modbus RTU 协议</p>"
            "<p>支持 XYG321-A 三轴平台</p>",
        )

    def _update_status(self) -> None:
        """更新状态显示"""
        if self._service.is_connected:
            self._status_panel.update_status()

    def pause_status_timer(self) -> None:
        """暂停状态定时器 (用于执行阻塞操作时避免通信冲突)"""
        if self._status_timer.isActive():
            self._status_timer.stop()
            logger.debug("状态定时器已暂停")

    def resume_status_timer(self) -> None:
        """恢复状态定时器"""
        if self._service.is_connected and not self._status_timer.isActive():
            self._status_timer.start(100)
            logger.debug("状态定时器已恢复")

    def _update_panels_enabled(self, enabled: bool) -> None:
        """更新面板启用状态"""
        self._axis_panel.setEnabled(enabled)
        self._status_panel.setEnabled(enabled)
        self._motion_panel.setEnabled(enabled)
        self._parameter_panel.setEnabled(enabled)
        self._modbus_debug_panel.setEnabled(enabled)

    def closeEvent(self, event: QCloseEvent) -> None:
        """窗口关闭事件"""
        # 停止定时器
        self._status_timer.stop()

        # 断开连接
        if self._service.is_connected:
            try:
                self._service.disable_all()
                self._service.disconnect()
            except Exception as e:
                logger.error(f"关闭时断开连接失败: {e}")

        event.accept()
