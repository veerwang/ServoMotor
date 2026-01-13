"""
Modbus 调试面板组件

提供 Modbus RTU 通信调试功能。
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QTextCharFormat
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from servo_service import ServoService
from servo_service.modbus_rtu.crc import append_crc
from ..i18n import tr

logger = logging.getLogger(__name__)


# 常用寄存器预设 (name_key 用于翻译)
QUICK_REGISTERS = [
    {"name_key": "reg.status_word", "addr": 0x0381, "size": 1, "desc": "Status Word"},
    {"name_key": "reg.control_word", "addr": 0x0380, "size": 1, "desc": "Control Word"},
    {"name_key": "reg.position", "addr": 0x03C8, "size": 2, "desc": "Position Actual"},
    {"name_key": "reg.velocity", "addr": 0x03D5, "size": 2, "desc": "Velocity Actual"},
    {"name_key": "reg.error_code", "addr": 0x0382, "size": 1, "desc": "Error Code"},
    {"name_key": "reg.mode", "addr": 0x03C3, "size": 1, "desc": "Operation Mode"},
]

# 功能码定义 (key 用于翻译)
FUNCTION_CODES = [
    (0x03, "fc.read_holding"),
    (0x04, "fc.read_input"),
    (0x06, "fc.write_single"),
    (0x10, "fc.write_multi"),
]


class ModbusDebugPanel(QGroupBox):
    """
    Modbus 调试面板

    提供寄存器读写、通信日志、统计等功能。
    """

    # 信号 - 请求暂停/恢复状态定时器
    request_pause_timer = pyqtSignal()
    request_resume_timer = pyqtSignal()

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化 Modbus 调试面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__(tr("modbus.title"), parent)
        self._service = service

        # 统计计数
        self._tx_count = 0
        self._rx_count = 0
        self._err_count = 0

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 快捷操作区
        layout.addWidget(self._create_quick_access_section())

        # 分隔线
        layout.addWidget(self._create_separator())

        # 手动发送区
        layout.addWidget(self._create_manual_send_section())

        # 分隔线
        layout.addWidget(self._create_separator())

        # 通信日志区
        layout.addWidget(self._create_log_section())

        # 统计区
        layout.addWidget(self._create_stats_section())

    def _create_separator(self) -> QFrame:
        """创建分隔线"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _create_quick_access_section(self) -> QWidget:
        """创建快捷操作区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 标题
        self._quick_title = QLabel(tr("modbus.quick_access"))
        self._quick_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._quick_title)

        # 从站和地址输入行
        input_layout = QHBoxLayout()

        # 从站地址
        self._slave_label = QLabel(tr("modbus.slave"))
        input_layout.addWidget(self._slave_label)
        self._slave_spin = QSpinBox()
        self._slave_spin.setRange(1, 247)
        self._slave_spin.setValue(3)  # 默认 Z 轴
        self._slave_spin.setFixedWidth(60)
        input_layout.addWidget(self._slave_spin)

        input_layout.addSpacing(10)

        # 寄存器地址
        self._addr_label = QLabel(tr("modbus.address"))
        input_layout.addWidget(self._addr_label)
        self._addr_edit = QLineEdit()
        self._addr_edit.setPlaceholderText("0x0381")
        self._addr_edit.setFixedWidth(80)
        self._addr_edit.setText("0x0381")
        input_layout.addWidget(self._addr_edit)

        # 数量
        self._count_label = QLabel(tr("modbus.count"))
        input_layout.addWidget(self._count_label)
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 125)
        self._count_spin.setValue(1)
        self._count_spin.setFixedWidth(50)
        input_layout.addWidget(self._count_spin)

        # 读取按钮
        self._read_btn = QPushButton(tr("modbus.read"))
        self._read_btn.clicked.connect(self._quick_read)
        self._read_btn.setFixedWidth(60)
        input_layout.addWidget(self._read_btn)

        input_layout.addStretch()
        layout.addLayout(input_layout)

        # 常用寄存器按钮行
        self._quick_reg_btns = []
        btn_layout = QHBoxLayout()
        for reg in QUICK_REGISTERS:
            btn = QPushButton(tr(reg["name_key"]))
            btn.setToolTip(f'{reg["desc"]} (0x{reg["addr"]:04X})')
            btn.clicked.connect(lambda checked, r=reg: self._quick_reg_click(r))
            btn.setFixedWidth(60)
            btn_layout.addWidget(btn)
            self._quick_reg_btns.append((btn, reg["name_key"]))
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _create_manual_send_section(self) -> QWidget:
        """创建手动发送区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 标题
        self._manual_title = QLabel(tr("modbus.manual_send"))
        self._manual_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._manual_title)

        # 功能码行
        fc_layout = QHBoxLayout()
        self._fc_label = QLabel(tr("modbus.function_code"))
        fc_layout.addWidget(self._fc_label)
        self._fc_combo = QComboBox()
        for code, name_key in FUNCTION_CODES:
            self._fc_combo.addItem(tr(name_key), code)
        self._fc_combo.currentIndexChanged.connect(self._update_preview)
        self._fc_combo.setFixedWidth(180)
        fc_layout.addWidget(self._fc_combo)
        fc_layout.addStretch()
        layout.addLayout(fc_layout)

        # 地址和数据行
        data_layout = QHBoxLayout()
        self._start_addr_label = QLabel(tr("modbus.start_addr"))
        data_layout.addWidget(self._start_addr_label)
        self._manual_addr_edit = QLineEdit()
        self._manual_addr_edit.setPlaceholderText("0x0380")
        self._manual_addr_edit.setText("0x0380")
        self._manual_addr_edit.setFixedWidth(80)
        self._manual_addr_edit.textChanged.connect(self._update_preview)
        data_layout.addWidget(self._manual_addr_edit)

        data_layout.addSpacing(10)

        # 数量/数据
        self._data_label = QLabel(tr("modbus.count"))
        data_layout.addWidget(self._data_label)
        self._manual_data_edit = QLineEdit()
        self._manual_data_edit.setPlaceholderText("1")
        self._manual_data_edit.setText("1")
        self._manual_data_edit.setFixedWidth(100)
        self._manual_data_edit.textChanged.connect(self._update_preview)
        data_layout.addWidget(self._manual_data_edit)

        data_layout.addStretch()
        layout.addLayout(data_layout)

        # 帧预览
        preview_layout = QHBoxLayout()
        self._frame_preview_label = QLabel(tr("modbus.frame_preview"))
        preview_layout.addWidget(self._frame_preview_label)
        self._preview_label = QLabel("")
        self._preview_label.setStyleSheet(
            "font-family: monospace; background-color: #f0f0f0; padding: 4px;"
        )
        preview_layout.addWidget(self._preview_label, 1)
        layout.addLayout(preview_layout)

        # 发送按钮
        btn_layout = QHBoxLayout()
        self._send_btn = QPushButton(tr("modbus.send"))
        self._send_btn.clicked.connect(self._manual_send)
        self._send_btn.setProperty("class", "success")
        self._send_btn.setFixedWidth(80)
        btn_layout.addWidget(self._send_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 初始预览
        self._update_preview()

        return widget

    def _create_log_section(self) -> QWidget:
        """创建通信日志区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 标题行
        title_layout = QHBoxLayout()
        self._log_title = QLabel(tr("modbus.comm_log"))
        self._log_title.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(self._log_title)
        title_layout.addStretch()

        # 清空按钮
        self._clear_btn = QPushButton(tr("modbus.clear"))
        self._clear_btn.clicked.connect(self._clear_log)
        self._clear_btn.setFixedWidth(50)
        title_layout.addWidget(self._clear_btn)

        # 导出按钮
        self._export_btn = QPushButton(tr("modbus.export"))
        self._export_btn.clicked.connect(self._export_log)
        self._export_btn.setFixedWidth(50)
        title_layout.addWidget(self._export_btn)

        layout.addLayout(title_layout)

        # 日志文本框
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 9))
        self._log_text.setMinimumHeight(150)
        self._log_text.setMaximumHeight(250)
        layout.addWidget(self._log_text)

        return widget

    def _create_stats_section(self) -> QWidget:
        """创建统计区"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stats_label = QLabel(tr("modbus.stats", tx=0, rx=0, err=0, rate="--"))
        self._stats_label.setStyleSheet("color: #666;")
        layout.addWidget(self._stats_label)

        layout.addStretch()

        # 重置按钮
        self._reset_btn = QPushButton(tr("modbus.reset_stats"))
        self._reset_btn.clicked.connect(self._reset_stats)
        self._reset_btn.setFixedWidth(70)
        layout.addWidget(self._reset_btn)

        return widget

    # ==================== 事件处理 ====================

    def _quick_reg_click(self, reg: dict) -> None:
        """快捷寄存器按钮点击"""
        self._addr_edit.setText(f"0x{reg['addr']:04X}")
        self._count_spin.setValue(reg["size"])
        self._quick_read()

    def _quick_read(self) -> None:
        """快捷读取"""
        try:
            addr = self._parse_address(self._addr_edit.text())
            count = self._count_spin.value()
            slave_id = self._slave_spin.value()

            self._read_registers(slave_id, addr, count)
        except ValueError as e:
            self._log_error(str(e))

    def _manual_send(self) -> None:
        """手动发送"""
        try:
            fc = self._fc_combo.currentData()
            addr = self._parse_address(self._manual_addr_edit.text())
            slave_id = self._slave_spin.value()
            data_text = self._manual_data_edit.text().strip()

            if fc == 0x03 or fc == 0x04:
                # 读取操作
                count = int(data_text) if data_text else 1
                self._read_registers(slave_id, addr, count, fc == 0x04)
            elif fc == 0x06:
                # 写单个寄存器
                value = self._parse_value(data_text)
                self._write_single_register(slave_id, addr, value)
            elif fc == 0x10:
                # 写多个寄存器
                values = self._parse_values(data_text)
                self._write_multiple_registers(slave_id, addr, values)
        except ValueError as e:
            self._log_error(str(e))
        except Exception as e:
            self._log_error(f"{tr('modbus.send_failed')} {e}")

    def _update_preview(self) -> None:
        """更新帧预览"""
        try:
            fc = self._fc_combo.currentData()
            addr = self._parse_address(self._manual_addr_edit.text())
            slave_id = self._slave_spin.value()
            data_text = self._manual_data_edit.text().strip()

            # 更新数据标签
            if fc == 0x03 or fc == 0x04:
                self._data_label.setText(tr("modbus.count"))
            elif fc == 0x06:
                self._data_label.setText(tr("modbus.data"))
            else:
                self._data_label.setText(tr("modbus.data"))

            # 构建帧
            frame = self._build_frame(fc, slave_id, addr, data_text)
            if frame:
                frame_with_crc = append_crc(frame)
                hex_str = " ".join(f"{b:02X}" for b in frame_with_crc)
                self._preview_label.setText(hex_str)
            else:
                self._preview_label.setText("--")
        except Exception:
            self._preview_label.setText("--")

    def _clear_log(self) -> None:
        """清空日志"""
        self._log_text.clear()

    def _export_log(self) -> None:
        """导出日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            tr("modbus.export_title"),
            f"modbus_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self._log_text.toPlainText())
                self._log_info(f"{tr('modbus.exported')} {filename}")
            except Exception as e:
                self._log_error(f"{tr('modbus.export_failed')} {e}")

    def _reset_stats(self) -> None:
        """重置统计"""
        self._tx_count = 0
        self._rx_count = 0
        self._err_count = 0
        self._update_stats()

    # ==================== Modbus 操作 ====================

    def _read_registers(
        self, slave_id: int, addr: int, count: int, input_reg: bool = False
    ) -> None:
        """读取寄存器"""
        client = self._service.get_modbus_client()
        if client is None:
            self._log_error(tr("modbus.not_connected"))
            return

        # 暂停状态定时器
        self.request_pause_timer.emit()

        try:
            # 构建并记录请求帧
            fc = 0x04 if input_reg else 0x03
            frame = bytes([slave_id, fc, (addr >> 8) & 0xFF, addr & 0xFF,
                          (count >> 8) & 0xFF, count & 0xFF])
            frame_with_crc = append_crc(frame)
            reg_type = tr("modbus.read_input") if input_reg else tr("modbus.read_holding")
            self._log_tx(frame_with_crc, f"{reg_type} 0x{addr:04X}, {tr('modbus.count').rstrip(':')}:{count}")

            # 执行读取
            if count == 1:
                value = client.read_register(slave_id, addr)
                values = [value]
            else:
                if input_reg:
                    values = client.read_input_registers(slave_id, addr, count)
                else:
                    values = client.read_holding_registers(slave_id, addr, count)

            # 记录响应
            self._log_rx_values(values, addr)
            self._rx_count += 1

        except Exception as e:
            self._log_error(f"{tr('modbus.read_failed')} {e}")
            self._err_count += 1
        finally:
            self.request_resume_timer.emit()
            self._update_stats()

    def _write_single_register(self, slave_id: int, addr: int, value: int) -> None:
        """写单个寄存器"""
        client = self._service.get_modbus_client()
        if client is None:
            self._log_error(tr("modbus.not_connected"))
            return

        self.request_pause_timer.emit()

        try:
            # 构建并记录请求帧
            frame = bytes([slave_id, 0x06, (addr >> 8) & 0xFF, addr & 0xFF,
                          (value >> 8) & 0xFF, value & 0xFF])
            frame_with_crc = append_crc(frame)
            self._log_tx(frame_with_crc, f"{tr('modbus.write_single')} 0x{addr:04X} = 0x{value:04X}")

            # 执行写入
            client.write_register(slave_id, addr, value)

            self._log_rx_success(tr("modbus.write_success"))
            self._rx_count += 1

        except Exception as e:
            self._log_error(f"{tr('modbus.write_failed')} {e}")
            self._err_count += 1
        finally:
            self.request_resume_timer.emit()
            self._update_stats()

    def _write_multiple_registers(
        self, slave_id: int, addr: int, values: List[int]
    ) -> None:
        """写多个寄存器"""
        client = self._service.get_modbus_client()
        if client is None:
            self._log_error(tr("modbus.not_connected"))
            return

        self.request_pause_timer.emit()

        try:
            # 记录请求
            values_hex = " ".join(f"0x{v:04X}" for v in values)
            self._log_tx(
                bytes([slave_id, 0x10]),
                f"{tr('fc.write_multi')} 0x{addr:04X}, {tr('modbus.count').rstrip(':')}:{len(values)}, {tr('modbus.data').rstrip(':')}: [{values_hex}]",
            )

            # 执行写入
            client.write_multiple_registers(slave_id, addr, values)

            self._log_rx_success(tr("modbus.write_multi_success", count=len(values)))
            self._rx_count += 1

        except Exception as e:
            self._log_error(f"{tr('modbus.write_failed')} {e}")
            self._err_count += 1
        finally:
            self.request_resume_timer.emit()
            self._update_stats()

    # ==================== 辅助方法 ====================

    def _parse_address(self, text: str) -> int:
        """解析地址"""
        text = text.strip().lower()
        if not text:
            raise ValueError(tr("modbus.addr_empty"))

        if text.startswith("0x"):
            return int(text, 16)
        elif text.endswith("h"):
            return int(text[:-1], 16)
        else:
            # 尝试十六进制
            try:
                return int(text, 16)
            except ValueError:
                return int(text)

    def _parse_value(self, text: str) -> int:
        """解析单个值"""
        text = text.strip().lower()
        if not text:
            return 0

        if text.startswith("0x"):
            return int(text, 16)
        elif text.endswith("h"):
            return int(text[:-1], 16)
        else:
            try:
                return int(text, 16)
            except ValueError:
                return int(text)

    def _parse_values(self, text: str) -> List[int]:
        """解析多个值（空格或逗号分隔）"""
        text = text.strip()
        if not text:
            raise ValueError(tr("modbus.data_empty"))

        # 支持空格或逗号分隔
        parts = text.replace(",", " ").split()
        return [self._parse_value(p) for p in parts]

    def _build_frame(
        self, fc: int, slave_id: int, addr: int, data_text: str
    ) -> Optional[bytes]:
        """构建请求帧（不含 CRC）"""
        try:
            if fc == 0x03 or fc == 0x04:
                count = int(data_text) if data_text else 1
                return bytes([
                    slave_id, fc,
                    (addr >> 8) & 0xFF, addr & 0xFF,
                    (count >> 8) & 0xFF, count & 0xFF,
                ])
            elif fc == 0x06:
                value = self._parse_value(data_text)
                return bytes([
                    slave_id, fc,
                    (addr >> 8) & 0xFF, addr & 0xFF,
                    (value >> 8) & 0xFF, value & 0xFF,
                ])
            elif fc == 0x10:
                values = self._parse_values(data_text)
                count = len(values)
                byte_count = count * 2
                frame = bytes([
                    slave_id, fc,
                    (addr >> 8) & 0xFF, addr & 0xFF,
                    (count >> 8) & 0xFF, count & 0xFF,
                    byte_count,
                ])
                for v in values:
                    frame += bytes([(v >> 8) & 0xFF, v & 0xFF])
                return frame
        except Exception:
            pass
        return None

    # ==================== 日志方法 ====================

    def _log_tx(self, frame: bytes, description: str) -> None:
        """记录发送帧"""
        self._tx_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        hex_str = " ".join(f"{b:02X}" for b in frame)

        self._log_text.setTextColor(QColor("#4a90d9"))  # 蓝色
        self._log_text.append(f"[{timestamp}] TX {hex_str}")
        self._log_text.setTextColor(QColor("#666"))
        self._log_text.append(f"           → {description}")

    def _log_rx_values(self, values: List[int], addr: int) -> None:
        """记录接收的值"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 格式化值
        if len(values) == 1:
            val = values[0]
            value_str = f"0x{val:04X} ({val})"
        elif len(values) == 2:
            # 32位值
            val32 = (values[0] << 16) | values[1]
            # 检查是否为有符号数
            if val32 & 0x80000000:
                val32_signed = val32 - 0x100000000
                value_str = f"0x{val32 & 0xFFFFFFFF:08X} ({val32_signed})"
            else:
                value_str = f"0x{val32:08X} ({val32})"
        else:
            values_hex = " ".join(f"{v:04X}" for v in values)
            value_str = f"[{values_hex}]"

        self._log_text.setTextColor(QColor("#5cb85c"))  # 绿色
        self._log_text.append(f"[{timestamp}] RX {tr('modbus.success')}")
        self._log_text.setTextColor(QColor("#666"))
        self._log_text.append(f"           ← {tr('modbus.rx_data')} {value_str}")

    def _log_rx_success(self, message: str) -> None:
        """记录成功响应"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_text.setTextColor(QColor("#5cb85c"))  # 绿色
        self._log_text.append(f"[{timestamp}] RX {message}")

    def _log_error(self, message: str) -> None:
        """记录错误"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_text.setTextColor(QColor("#d9534f"))  # 红色
        self._log_text.append(f"[{timestamp}] ERR {message}")

    def _log_info(self, message: str) -> None:
        """记录信息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_text.setTextColor(QColor("#666"))
        self._log_text.append(f"[{timestamp}] {message}")

    def _update_stats(self) -> None:
        """更新统计"""
        total = self._tx_count
        if total > 0:
            success_rate = (self._rx_count / total) * 100
            rate_str = f"{success_rate:.1f}%"
        else:
            rate_str = "--"

        self._stats_label.setText(
            tr("modbus.stats", tx=self._tx_count, rx=self._rx_count,
               err=self._err_count, rate=rate_str)
        )

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("modbus.title"))

        # 快捷操作区
        self._quick_title.setText(tr("modbus.quick_access"))
        self._slave_label.setText(tr("modbus.slave"))
        self._addr_label.setText(tr("modbus.address"))
        self._count_label.setText(tr("modbus.count"))
        self._read_btn.setText(tr("modbus.read"))

        # 更新快捷寄存器按钮
        for btn, name_key in self._quick_reg_btns:
            btn.setText(tr(name_key))

        # 手动发送区
        self._manual_title.setText(tr("modbus.manual_send"))
        self._fc_label.setText(tr("modbus.function_code"))
        self._start_addr_label.setText(tr("modbus.start_addr"))
        self._frame_preview_label.setText(tr("modbus.frame_preview"))
        self._send_btn.setText(tr("modbus.send"))

        # 更新功能码下拉框
        current_fc = self._fc_combo.currentData()
        self._fc_combo.clear()
        for code, name_key in FUNCTION_CODES:
            self._fc_combo.addItem(tr(name_key), code)
        # 恢复选中项
        for i in range(self._fc_combo.count()):
            if self._fc_combo.itemData(i) == current_fc:
                self._fc_combo.setCurrentIndex(i)
                break

        # 通信日志区
        self._log_title.setText(tr("modbus.comm_log"))
        self._clear_btn.setText(tr("modbus.clear"))
        self._export_btn.setText(tr("modbus.export"))

        # 统计区
        self._reset_btn.setText(tr("modbus.reset_stats"))
        self._update_stats()

        # 更新数据标签
        self._update_preview()
