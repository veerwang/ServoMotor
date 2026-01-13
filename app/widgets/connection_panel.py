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
from ..i18n import tr

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
        super().__init__(tr("connection.title"), parent)
        self._service = service
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 串口选择
        self._form_layout = QFormLayout()

        # 串口下拉框
        port_layout = QHBoxLayout()
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(150)
        port_layout.addWidget(self._port_combo)

        self._refresh_btn = QPushButton(tr("connection.refresh"))
        self._refresh_btn.setMinimumWidth(60)
        self._refresh_btn.clicked.connect(self._refresh_ports)
        port_layout.addWidget(self._refresh_btn)

        self._port_label = QLabel(tr("connection.port"))
        self._form_layout.addRow(self._port_label, port_layout)

        # 波特率下拉框
        self._baudrate_combo = QComboBox()
        for baud in self.BAUDRATE_OPTIONS:
            self._baudrate_combo.addItem(str(baud), baud)
        self._baudrate_combo.setCurrentText("115200")
        self._baudrate_label = QLabel(tr("connection.baudrate"))
        self._form_layout.addRow(self._baudrate_label, self._baudrate_combo)

        layout.addLayout(self._form_layout)

        # 连接状态
        status_layout = QHBoxLayout()
        self._status_title_label = QLabel(tr("connection.status"))
        status_layout.addWidget(self._status_title_label)
        self._status_label = QLabel(tr("connection.not_connected"))
        self._status_label.setProperty("class", "status-warning")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 连接按钮
        btn_layout = QHBoxLayout()

        self._connect_btn = QPushButton(tr("connection.connect"))
        self._connect_btn.setProperty("class", "success")
        self._connect_btn.clicked.connect(self.connect_clicked)
        btn_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton(tr("connection.disconnect"))
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
            self._port_combo.addItem(tr("connection.no_port"), "")

        # 默认选择 /dev/ttyUSB0
        default_port = "/dev/ttyUSB0"
        for i in range(self._port_combo.count()):
            if self._port_combo.itemData(i) == default_port:
                self._port_combo.setCurrentIndex(i)
                break

        logger.debug(f"Refreshed port list: {len(ports)} ports")

    def connect_clicked(self) -> None:
        """连接按钮点击"""
        port = self._port_combo.currentData()
        if not port:
            QMessageBox.warning(self, tr("common.warning"), tr("connection.select_port"))
            return

        baudrate = self._baudrate_combo.currentData()

        try:
            self._service.connect(port, baudrate)
            self._update_connected_state(True)
            self.connected.emit()
            logger.info(f"Connected to {port} @ {baudrate}")

        except Exception as e:
            QMessageBox.critical(self, tr("connection.failed"), f"{tr('connection.failed_msg')}\n{e}")
            logger.error(f"Connection failed: {e}")

    def disconnect_clicked(self) -> None:
        """断开按钮点击"""
        try:
            self._service.disconnect()
            self._update_connected_state(False)
            self.disconnected.emit()
            logger.info("Disconnected")

        except Exception as e:
            QMessageBox.warning(self, tr("connection.disconnect_failed"), f"{tr('connection.disconnect_error')}\n{e}")
            logger.error(f"Disconnect failed: {e}")

    def _update_connected_state(self, connected: bool) -> None:
        """更新连接状态显示"""
        self._connect_btn.setEnabled(not connected)
        self._disconnect_btn.setEnabled(connected)
        self._port_combo.setEnabled(not connected)
        self._baudrate_combo.setEnabled(not connected)
        self._refresh_btn.setEnabled(not connected)

        if connected:
            self._status_label.setText(tr("connection.connected"))
            self._status_label.setProperty("class", "status-ok")
        else:
            self._status_label.setText(tr("connection.not_connected"))
            self._status_label.setProperty("class", "status-warning")

        # 刷新样式
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("connection.title"))
        self._port_label.setText(tr("connection.port"))
        self._baudrate_label.setText(tr("connection.baudrate"))
        self._status_title_label.setText(tr("connection.status"))
        self._refresh_btn.setText(tr("connection.refresh"))
        self._connect_btn.setText(tr("connection.connect"))
        self._disconnect_btn.setText(tr("connection.disconnect"))

        # 更新连接状态文本
        if self._service.is_connected:
            self._status_label.setText(tr("connection.connected"))
        else:
            self._status_label.setText(tr("connection.not_connected"))
