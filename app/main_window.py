"""
主窗口模块

NiMotion 伺服电机控制系统的主窗口。
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QFont, QIcon
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

from .i18n import Language, get_language, load_language, register_language_callback, set_language, tr
from .widgets.connection_panel import ConnectionPanel
from .widgets.axis_panel import AxisPanel
from .widgets.status_panel import StatusPanel
from .widgets.motion_panel import MotionPanel
from .widgets.parameter_panel import ParameterPanel
from .widgets.modbus_debug_panel import ModbusDebugPanel
from .widgets.register_config_panel import RegisterConfigPanel

logger = logging.getLogger(__name__)


# 视图索引常量
VIEW_MOTOR_CONTROL = 0
VIEW_MODBUS_DEBUG = 1
VIEW_REGISTER_CONFIG = 2


class MainWindow(QMainWindow):
    """
    主窗口类

    包含所有控制面板和状态显示，支持视图切换。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化主窗口"""
        super().__init__(parent)

        # 加载保存的语言设置
        load_language()

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
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(1024, 700)
        self.resize(1280, 800)

        # 设置窗口图标
        icon_path = Path(__file__).parent / "resources" / "motor_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

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

        # 视图 3: 寄存器配置视图
        self._register_config_view = self._create_register_config_view()
        self._view_stack.addWidget(self._register_config_view)

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

    def _create_register_config_view(self) -> QWidget:
        """创建寄存器配置视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 寄存器配置面板
        self._register_config_panel = RegisterConfigPanel(self._service)
        layout.addWidget(self._register_config_panel)

        return view

    def _init_menu(self) -> None:
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        self._file_menu = menubar.addMenu(tr("menu.file"))

        self._exit_action = QAction(tr("menu.exit"), self)
        self._exit_action.setShortcut("Ctrl+Q")
        self._exit_action.triggered.connect(self.close)
        self._file_menu.addAction(self._exit_action)

        # 视图菜单
        self._view_menu = menubar.addMenu(tr("menu.view"))

        # 创建视图切换动作组（单选）
        view_group = QActionGroup(self)
        view_group.setExclusive(True)

        self._motor_control_action = QAction(tr("menu.motor_control"), self)
        self._motor_control_action.setCheckable(True)
        self._motor_control_action.setChecked(True)
        self._motor_control_action.setShortcut("Ctrl+1")
        self._motor_control_action.triggered.connect(
            lambda: self._switch_view(VIEW_MOTOR_CONTROL)
        )
        view_group.addAction(self._motor_control_action)
        self._view_menu.addAction(self._motor_control_action)

        self._modbus_debug_action = QAction(tr("menu.modbus_debug"), self)
        self._modbus_debug_action.setCheckable(True)
        self._modbus_debug_action.setShortcut("Ctrl+2")
        self._modbus_debug_action.triggered.connect(
            lambda: self._switch_view(VIEW_MODBUS_DEBUG)
        )
        view_group.addAction(self._modbus_debug_action)
        self._view_menu.addAction(self._modbus_debug_action)

        self._register_config_action = QAction(tr("menu.register_config"), self)
        self._register_config_action.setCheckable(True)
        self._register_config_action.setShortcut("Ctrl+3")
        self._register_config_action.triggered.connect(
            lambda: self._switch_view(VIEW_REGISTER_CONFIG)
        )
        view_group.addAction(self._register_config_action)
        self._view_menu.addAction(self._register_config_action)

        # 连接菜单
        self._connect_menu = menubar.addMenu(tr("menu.connect"))

        self._connect_action = QAction(tr("menu.connect_action"), self)
        self._connect_action.setShortcut("Ctrl+O")
        self._connect_action.triggered.connect(self._on_connect)
        self._connect_menu.addAction(self._connect_action)

        self._disconnect_action = QAction(tr("menu.disconnect"), self)
        self._disconnect_action.setShortcut("Ctrl+D")
        self._disconnect_action.triggered.connect(self._on_disconnect)
        self._disconnect_action.setEnabled(False)
        self._connect_menu.addAction(self._disconnect_action)

        # 控制菜单
        self._control_menu = menubar.addMenu(tr("menu.control"))

        self._enable_action = QAction(tr("menu.enable"), self)
        self._enable_action.setShortcut("Ctrl+E")
        self._enable_action.triggered.connect(self._on_enable)
        self._control_menu.addAction(self._enable_action)

        self._disable_action = QAction(tr("menu.disable"), self)
        self._disable_action.triggered.connect(self._on_disable)
        self._control_menu.addAction(self._disable_action)

        self._control_menu.addSeparator()

        self._stop_action = QAction(tr("menu.stop"), self)
        self._stop_action.setShortcut("Space")
        self._stop_action.triggered.connect(self._on_stop)
        self._control_menu.addAction(self._stop_action)

        self._quick_stop_action = QAction(tr("menu.quick_stop"), self)
        self._quick_stop_action.setShortcut("Escape")
        self._quick_stop_action.triggered.connect(self._on_quick_stop)
        self._control_menu.addAction(self._quick_stop_action)

        self._control_menu.addSeparator()

        self._home_action = QAction(tr("menu.home"), self)
        self._home_action.setShortcut("Ctrl+H")
        self._home_action.triggered.connect(self._on_home)
        self._control_menu.addAction(self._home_action)

        # 语言菜单
        self._lang_menu = menubar.addMenu(tr("menu.language"))

        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)

        self._chinese_action = QAction(tr("menu.chinese"), self)
        self._chinese_action.setCheckable(True)
        self._chinese_action.setChecked(get_language() == Language.CHINESE)
        self._chinese_action.triggered.connect(lambda: self._change_language(Language.CHINESE))
        lang_group.addAction(self._chinese_action)
        self._lang_menu.addAction(self._chinese_action)

        self._english_action = QAction(tr("menu.english"), self)
        self._english_action.setCheckable(True)
        self._english_action.setChecked(get_language() == Language.ENGLISH)
        self._english_action.triggered.connect(lambda: self._change_language(Language.ENGLISH))
        lang_group.addAction(self._english_action)
        self._lang_menu.addAction(self._english_action)

        # 帮助菜单
        self._help_menu = menubar.addMenu(tr("menu.help"))

        self._about_action = QAction(tr("menu.about"), self)
        self._about_action.triggered.connect(self._on_about)
        self._help_menu.addAction(self._about_action)

    def _init_statusbar(self) -> None:
        """初始化状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._update_statusbar_message()

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

        # 寄存器配置面板信号
        self._register_config_panel.request_pause_timer.connect(self.pause_status_timer)
        self._register_config_panel.request_resume_timer.connect(self.resume_status_timer)

        # 注册语言变更回调
        register_language_callback(self._on_language_changed)

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
        self._update_statusbar_message()

        view_names = {
            VIEW_MOTOR_CONTROL: tr("status.view_motor"),
            VIEW_MODBUS_DEBUG: tr("status.view_modbus"),
            VIEW_REGISTER_CONFIG: tr("status.view_register"),
        }
        view_name = view_names.get(view_index, "")
        logger.info(f"{tr('common.switch_to')} {view_name}")

    # ==================== 事件处理 ====================

    def _on_connected(self) -> None:
        """连接成功"""
        self._connect_action.setEnabled(False)
        self._disconnect_action.setEnabled(True)

        # 更新状态栏
        self._update_statusbar_message()

        # 启动状态更新
        self._status_timer.start(100)  # 100ms 刷新

        # 更新各面板状态
        self._update_panels_enabled(True)

    def _on_disconnected(self) -> None:
        """断开连接"""
        self._connect_action.setEnabled(True)
        self._disconnect_action.setEnabled(False)

        # 更新状态栏
        self._update_statusbar_message()

        # 停止状态更新
        self._status_timer.stop()

        # 更新各面板状态
        self._update_panels_enabled(False)

    def _on_axis_changed(self, axis: AxisName) -> None:
        """轴切换"""
        axis_name = tr(f"axis.{axis.value.lower()}")
        self._statusbar.showMessage(f"{tr('common.switch_to')} {axis_name}")
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
            tr("about.title"),
            tr("about.content"),
        )

    def _change_language(self, lang: Language) -> None:
        """切换语言"""
        set_language(lang)

    def _on_language_changed(self) -> None:
        """语言变更回调"""
        self._refresh_ui_texts()

    def _refresh_ui_texts(self) -> None:
        """刷新所有 UI 文本"""
        # 窗口标题
        self.setWindowTitle(tr("app.title"))

        # 菜单
        self._file_menu.setTitle(tr("menu.file"))
        self._exit_action.setText(tr("menu.exit"))

        self._view_menu.setTitle(tr("menu.view"))
        self._motor_control_action.setText(tr("menu.motor_control"))
        self._modbus_debug_action.setText(tr("menu.modbus_debug"))
        self._register_config_action.setText(tr("menu.register_config"))

        self._connect_menu.setTitle(tr("menu.connect"))
        self._connect_action.setText(tr("menu.connect_action"))
        self._disconnect_action.setText(tr("menu.disconnect"))

        self._control_menu.setTitle(tr("menu.control"))
        self._enable_action.setText(tr("menu.enable"))
        self._disable_action.setText(tr("menu.disable"))
        self._stop_action.setText(tr("menu.stop"))
        self._quick_stop_action.setText(tr("menu.quick_stop"))
        self._home_action.setText(tr("menu.home"))

        self._lang_menu.setTitle(tr("menu.language"))
        self._chinese_action.setText(tr("menu.chinese"))
        self._english_action.setText(tr("menu.english"))

        self._help_menu.setTitle(tr("menu.help"))
        self._about_action.setText(tr("menu.about"))

        # 状态栏
        self._update_statusbar_message()

        # 刷新各面板
        self._connection_panel.refresh_texts()
        self._axis_panel.refresh_texts()
        self._status_panel.refresh_texts()
        self._motion_panel.refresh_texts()
        self._parameter_panel.refresh_texts()
        self._modbus_debug_panel.refresh_texts()
        self._register_config_panel.refresh_texts()

    def _update_statusbar_message(self) -> None:
        """更新状态栏消息"""
        view_names = {
            VIEW_MOTOR_CONTROL: tr("status.view_motor"),
            VIEW_MODBUS_DEBUG: tr("status.view_modbus"),
            VIEW_REGISTER_CONFIG: tr("status.view_register"),
        }
        view_name = view_names.get(self._current_view, "")
        if self._service.is_connected:
            self._statusbar.showMessage(f"{tr('status.connected')} - {view_name}")
        else:
            self._statusbar.showMessage(f"{tr('status.ready')} - {view_name}")

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
        # 轴选择面板始终可用，允许用户在连接前选择目标轴
        # self._axis_panel.setEnabled(enabled)
        self._status_panel.setEnabled(enabled)
        self._motion_panel.setEnabled(enabled)
        self._parameter_panel.setEnabled(enabled)
        self._modbus_debug_panel.setEnabled(enabled)
        self._register_config_panel.setEnabled(enabled)

    def closeEvent(self, event: QCloseEvent) -> None:
        """窗口关闭事件"""
        # 停止定时器
        self._status_timer.stop()

        # 断开连接
        if self._service.is_connected:
            # 尝试禁用电机（忽略错误，因为设备可能已断开）
            try:
                self._service.disable_all()
            except Exception as e:
                logger.debug(f"关闭时禁用电机失败（可忽略）: {e}")

            # 断开串口连接
            try:
                self._service.disconnect()
            except Exception as e:
                logger.debug(f"关闭时断开连接失败（可忽略）: {e}")

        event.accept()
