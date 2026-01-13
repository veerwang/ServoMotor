"""
连接面板组件

提供串口选择和连接控制功能。
"""

import logging
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from servo_service import ServoService

logger = logging.getLogger(__name__)


class ConnectionPanel(QGroupBox):
    """
    连接面板

    用于选择串口和控制连接状态。
    """

    # 信号
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    # 波特率选项
    BAUDRATE_OPTIONS = [9600, 19200, 38400, 57600, 115200, 230400]

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化连接面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__("连接设置", parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 串口选择
        form_layout = QFormLayout()

        # 串口下拉框
        port_layout = QHBoxLayout()
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(150)
        port_layout.addWidget(self._port_combo)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setMinimumWidth(60)
        self._refresh_btn.clicked.connect(self._refresh_ports)
        port_layout.addWidget(self._refresh_btn)

        form_layout.addRow("串口:", port_layout)

        # 波特率下拉框
        self._baudrate_combo = QComboBox()
        for baud in self.BAUDRATE_OPTIONS:
            self._baudrate_combo.addItem(str(baud), baud)
        self._baudrate_combo.setCurrentText("115200")
        form_layout.addRow("波特率:", self._baudrate_combo)

        layout.addLayout(form_layout)

        # 连接状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self._status_label = QLabel("未连接")
        self._status_label.setProperty("class", "status-warning")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 连接按钮
        btn_layout = QHBoxLayout()

        self._connect_btn = QPushButton("连接")
        self._connect_btn.setProperty("class", "success")
        self._connect_btn.clicked.connect(self.connect_clicked)
        btn_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setProperty("class", "danger")
        self._disconnect_btn.clicked.connect(self.disconnect_clicked)
        self._disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self._disconnect_btn)

        layout.addLayout(btn_layout)

        # 初始刷新串口列表
        self._refresh_ports()

    def _refresh_ports(self) -> None:
        """刷新串口列表"""
        self._port_combo.clear()
        ports = self._service.get_available_ports()

        for port in ports:
            self._port_combo.addItem(port.display_name, port.device)

        if not ports:
            self._port_combo.addItem("未检测到串口", "")

        # 默认选择 /dev/ttyUSB0
        default_port = "/dev/ttyUSB0"
        for i in range(self._port_combo.count()):
            if self._port_combo.itemData(i) == default_port:
                self._port_combo.setCurrentIndex(i)
                break

        logger.debug(f"刷新串口列表: {len(ports)} 个")

    def connect_clicked(self) -> None:
        """连接按钮点击"""
        port = self._port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "警告", "请选择有效的串口")
            return

        baudrate = self._baudrate_combo.currentData()

        try:
            self._service.connect(port, baudrate)
            self._update_connected_state(True)
            self.connected.emit()
            logger.info(f"已连接到 {port} @ {baudrate}")

        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"无法连接到串口:\n{e}")
            logger.error(f"连接失败: {e}")

    def disconnect_clicked(self) -> None:
        """断开按钮点击"""
        try:
            self._service.disconnect()
            self._update_connected_state(False)
            self.disconnected.emit()
            logger.info("已断开连接")

        except Exception as e:
            QMessageBox.warning(self, "断开失败", f"断开连接时出错:\n{e}")
            logger.error(f"断开失败: {e}")

    def _update_connected_state(self, connected: bool) -> None:
        """更新连接状态显示"""
        self._connect_btn.setEnabled(not connected)
        self._disconnect_btn.setEnabled(connected)
        self._port_combo.setEnabled(not connected)
        self._baudrate_combo.setEnabled(not connected)
        self._refresh_btn.setEnabled(not connected)

        if connected:
            self._status_label.setText("已连接")
            self._status_label.setProperty("class", "status-ok")
        else:
            self._status_label.setText("未连接")
            self._status_label.setProperty("class", "status-warning")

        # 刷新样式
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
