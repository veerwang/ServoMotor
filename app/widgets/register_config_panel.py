"""
寄存器配置面板组件

提供电机关键寄存器的查看和修改功能，支持分类显示和解释说明。
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from servo_service import ServoService
from servo_service.motor_control.registers import Registers

from ..i18n import tr

logger = logging.getLogger(__name__)


class RegisterCategory(Enum):
    """寄存器分类"""
    CONTROL = "control"      # 核心控制
    POSITION = "position"    # 位置控制
    VELOCITY = "velocity"    # 速度控制
    HOMING = "homing"        # 回零控制
    DI_CONFIG = "di_config"  # DI 配置
    ENCODER = "encoder"      # 编码器配置


@dataclass
class RegisterInfo:
    """寄存器信息"""
    name: str               # 寄存器名称
    address: int            # Modbus 地址
    cia402_index: str       # CiA402 索引 (如 "6040h")
    size: int               # 1=16位, 2=32位
    access: str             # "RO", "RW", "WO"
    signed: bool            # 是否有符号
    category: RegisterCategory
    description_zh: str     # 中文描述
    description_en: str     # 英文描述
    unit: str = ""          # 单位
    default_value: Optional[int] = None  # 默认值
    critical: bool = False  # 是否关键 (外部修改可能导致问题)


# 定义所有关键寄存器
REGISTER_DEFINITIONS: List[RegisterInfo] = [
    # ==================== 核心控制寄存器 ====================
    RegisterInfo(
        name="CONTROL_WORD",
        address=0x0380,
        cia402_index="6040h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.CONTROL,
        description_zh="控制字 - 状态机控制、运动触发",
        description_en="Control Word - State machine control, motion trigger",
        critical=True,
    ),
    RegisterInfo(
        name="STATUS_WORD",
        address=0x0381,
        cia402_index="6041h",
        size=1,
        access="RO",
        signed=False,
        category=RegisterCategory.CONTROL,
        description_zh="状态字 - 状态反馈、目标到达检测",
        description_en="Status Word - State feedback, target reached detection",
    ),
    RegisterInfo(
        name="MODES_OF_OPERATION",
        address=0x03C2,
        cia402_index="6060h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.CONTROL,
        description_zh="操作模式设置 (1=PP, 3=PV, 6=HM)",
        description_en="Operation Mode (1=PP, 3=PV, 6=HM)",
        critical=True,
    ),
    RegisterInfo(
        name="MODES_OF_OPERATION_DISPLAY",
        address=0x03C3,
        cia402_index="6061h",
        size=1,
        access="RO",
        signed=False,
        category=RegisterCategory.CONTROL,
        description_zh="操作模式显示 - 当前模式读取",
        description_en="Operation Mode Display - Current mode readback",
    ),
    RegisterInfo(
        name="ERROR_CODE",
        address=0x0382,
        cia402_index="603Fh",
        size=1,
        access="RO",
        signed=False,
        category=RegisterCategory.CONTROL,
        description_zh="错误码 - 当前故障代码",
        description_en="Error Code - Current fault code",
    ),

    # ==================== 位置控制寄存器 ====================
    RegisterInfo(
        name="TARGET_POSITION",
        address=0x03E7,
        cia402_index="607Ah",
        size=2,
        access="RW",
        signed=True,
        category=RegisterCategory.POSITION,
        description_zh="目标位置",
        description_en="Target Position",
        unit="pulse",
        critical=True,
    ),
    RegisterInfo(
        name="POSITION_ACTUAL",
        address=0x03C8,
        cia402_index="6064h",
        size=2,
        access="RO",
        signed=True,
        category=RegisterCategory.POSITION,
        description_zh="实际位置",
        description_en="Actual Position",
        unit="pulse",
    ),
    RegisterInfo(
        name="PROFILE_VELOCITY",
        address=0x03F8,
        cia402_index="6081h",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.POSITION,
        description_zh="轮廓速度 (PP模式)",
        description_en="Profile Velocity (PP Mode)",
        unit="pulse/s",
        critical=True,
    ),
    RegisterInfo(
        name="PROFILE_ACCELERATION",
        address=0x03FC,
        cia402_index="6083h",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.POSITION,
        description_zh="轮廓加速度",
        description_en="Profile Acceleration",
        unit="pulse/s²",
        critical=True,
    ),
    RegisterInfo(
        name="PROFILE_DECELERATION",
        address=0x03FE,
        cia402_index="6084h",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.POSITION,
        description_zh="轮廓减速度",
        description_en="Profile Deceleration",
        unit="pulse/s²",
        critical=True,
    ),
    RegisterInfo(
        name="QUICK_STOP_DECELERATION",
        address=0x0400,
        cia402_index="6085h",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.POSITION,
        description_zh="快速停止减速度",
        description_en="Quick Stop Deceleration",
        unit="pulse/s²",
    ),

    # ==================== 速度控制寄存器 ====================
    RegisterInfo(
        name="TARGET_VELOCITY",
        address=0x0448,
        cia402_index="60FFh",
        size=2,
        access="RW",
        signed=True,
        category=RegisterCategory.VELOCITY,
        description_zh="目标速度 (PV模式)",
        description_en="Target Velocity (PV Mode)",
        unit="pulse/s",
        critical=True,
    ),
    RegisterInfo(
        name="VELOCITY_ACTUAL",
        address=0x03D5,
        cia402_index="606Ch",
        size=2,
        access="RO",
        signed=True,
        category=RegisterCategory.VELOCITY,
        description_zh="实际速度",
        description_en="Actual Velocity",
        unit="RPM",
    ),

    # ==================== 回零控制寄存器 ====================
    RegisterInfo(
        name="HOMING_METHOD",
        address=0x0416,
        cia402_index="6098h",
        size=1,
        access="RW",
        signed=True,
        category=RegisterCategory.HOMING,
        description_zh="回零方式 (17=负限位, 38=负向堵转)",
        description_en="Homing Method (17=Neg Limit, 38=Neg Blocking)",
        critical=True,
    ),
    RegisterInfo(
        name="HOMING_SPEED_HIGH",
        address=0x0417,
        cia402_index="6099h:01",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="回零高速 (搜索开关)",
        description_en="Homing Speed High (Search Switch)",
        unit="pulse/s",
    ),
    RegisterInfo(
        name="HOMING_SPEED_LOW",
        address=0x0419,
        cia402_index="6099h:02",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="回零低速 (搜索零点)",
        description_en="Homing Speed Low (Search Zero)",
        unit="pulse/s",
    ),
    RegisterInfo(
        name="HOMING_ACCELERATION",
        address=0x041B,
        cia402_index="609Ah",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="回零加速度",
        description_en="Homing Acceleration",
        unit="pulse/s²",
    ),
    RegisterInfo(
        name="HOMING_TIMEOUT",
        address=0x012E,
        cia402_index="2005h:1Ch",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="回零超时 (默认0会立即超时!)",
        description_en="Homing Timeout (Default 0 = instant timeout!)",
        unit="ms",
        default_value=60000,
        critical=True,
    ),
    RegisterInfo(
        name="BLOCKING_TORQUE",
        address=0x0170,
        cia402_index="2007h:13h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="堵转扭矩阈值 (0.1% 单位, 300=30%)",
        description_en="Blocking Torque Threshold (0.1% unit, 300=30%)",
        unit="0.1%",
        default_value=300,
    ),
    RegisterInfo(
        name="BLOCKING_TIME",
        address=0x0172,
        cia402_index="2007h:15h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.HOMING,
        description_zh="堵转检测时间",
        description_en="Blocking Detection Time",
        unit="ms",
        default_value=500,
    ),

    # ==================== DI 配置寄存器 ====================
    RegisterInfo(
        name="DI1_FUNCTION",
        address=0x00D5,
        cia402_index="2003h:03h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI1 功能 (14=正限位, 15=负限位, 31=原点)",
        description_en="DI1 Function (14=PosLimit, 15=NegLimit, 31=Home)",
        critical=True,
    ),
    RegisterInfo(
        name="DI1_LOGIC",
        address=0x00D6,
        cia402_index="2003h:04h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI1 逻辑 (0=低电平有效, 1=高电平有效)",
        description_en="DI1 Logic (0=Active Low, 1=Active High)",
    ),
    RegisterInfo(
        name="DI2_FUNCTION",
        address=0x00D7,
        cia402_index="2003h:05h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI2 功能",
        description_en="DI2 Function",
        critical=True,
    ),
    RegisterInfo(
        name="DI2_LOGIC",
        address=0x00D8,
        cia402_index="2003h:06h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI2 逻辑",
        description_en="DI2 Logic",
    ),
    RegisterInfo(
        name="DI3_FUNCTION",
        address=0x00D9,
        cia402_index="2003h:07h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI3 功能",
        description_en="DI3 Function",
        critical=True,
    ),
    RegisterInfo(
        name="DI3_LOGIC",
        address=0x00DA,
        cia402_index="2003h:08h",
        size=1,
        access="RW",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI3 逻辑",
        description_en="DI3 Logic",
    ),
    RegisterInfo(
        name="DI_PHYSICAL_STATE",
        address=0x01E2,
        cia402_index="200Bh:05h",
        size=1,
        access="RO",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="DI 物理状态 (位0=DI1, 位1=DI2, 位2=DI3)",
        description_en="DI Physical State (bit0=DI1, bit1=DI2, bit2=DI3)",
    ),
    RegisterInfo(
        name="DIGITAL_INPUTS_60FD",
        address=0x0447,
        cia402_index="60FDh",
        size=2,
        access="RO",
        signed=False,
        category=RegisterCategory.DI_CONFIG,
        description_zh="CiA402 数字输入 (位0=负限位, 位1=正限位)",
        description_en="CiA402 Digital Inputs (bit0=NegLimit, bit1=PosLimit)",
    ),

    # ==================== 编码器配置寄存器 ====================
    RegisterInfo(
        name="ENCODER_RESOLUTION_NUM",
        address=0x0408,
        cia402_index="608Fh:01",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.ENCODER,
        description_zh="编码器分辨率-分子 (脉冲/转)",
        description_en="Encoder Resolution Numerator (pulses/rev)",
        default_value=10000,
        critical=True,
    ),
    RegisterInfo(
        name="ENCODER_RESOLUTION_DEN",
        address=0x040A,
        cia402_index="608Fh:02",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.ENCODER,
        description_zh="编码器分辨率-分母",
        description_en="Encoder Resolution Denominator",
        default_value=1,
    ),
    RegisterInfo(
        name="GEAR_RATIO_NUM",
        address=0x040C,
        cia402_index="6091h:01",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.ENCODER,
        description_zh="减速比-分子 (电机圈数)",
        description_en="Gear Ratio Numerator (Motor Revs)",
        default_value=1,
    ),
    RegisterInfo(
        name="GEAR_RATIO_DEN",
        address=0x040E,
        cia402_index="6091h:02",
        size=2,
        access="RW",
        signed=False,
        category=RegisterCategory.ENCODER,
        description_zh="减速比-分母 (轴圈数)",
        description_en="Gear Ratio Denominator (Shaft Revs)",
        default_value=1,
    ),
]


class RegisterConfigPanel(QGroupBox):
    """
    寄存器配置面板

    用于查看和修改电机的关键寄存器。
    """

    # 信号
    request_pause_timer = pyqtSignal()
    request_resume_timer = pyqtSignal()

    def __init__(
        self,
        service: ServoService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        初始化寄存器配置面板

        Args:
            service: 伺服服务实例
            parent: 父组件
        """
        super().__init__(tr("regconfig.title"), parent)
        self._service = service
        self._register_values: Dict[int, int] = {}  # 地址 -> 值
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 主体使用分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧: 分类选项卡 + 寄存器表格
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 分类选项卡
        self._category_tabs = QTabWidget()
        self._register_tables: Dict[RegisterCategory, QTableWidget] = {}

        for category in RegisterCategory:
            table = self._create_register_table(category)
            self._register_tables[category] = table
            tab_name = tr(f"regconfig.cat.{category.value}")
            self._category_tabs.addTab(table, tab_name)

        left_layout.addWidget(self._category_tabs)

        # 右侧: 详细信息 + 编辑区
        right_widget = self._create_detail_panel()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 读取全部按钮
        self._read_all_btn = QPushButton(tr("regconfig.read_all"))
        self._read_all_btn.clicked.connect(self._read_all_registers)
        layout.addWidget(self._read_all_btn)

        # 读取当前分类
        self._read_category_btn = QPushButton(tr("regconfig.read_category"))
        self._read_category_btn.clicked.connect(self._read_category_registers)
        layout.addWidget(self._read_category_btn)

        # 分隔
        layout.addStretch()

        # 验证配置按钮
        self._verify_btn = QPushButton(tr("regconfig.verify"))
        self._verify_btn.setProperty("class", "warning")
        self._verify_btn.clicked.connect(self._verify_configuration)
        layout.addWidget(self._verify_btn)

        # 保存到 EEPROM 按钮
        self._save_eeprom_btn = QPushButton(tr("regconfig.save_eeprom"))
        self._save_eeprom_btn.setProperty("class", "danger")
        self._save_eeprom_btn.clicked.connect(self._save_to_eeprom)
        layout.addWidget(self._save_eeprom_btn)

        return toolbar

    def _create_register_table(self, category: RegisterCategory) -> QTableWidget:
        """创建寄存器表格"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            tr("regconfig.col.name"),
            tr("regconfig.col.address"),
            tr("regconfig.col.cia402"),
            tr("regconfig.col.value"),
            tr("regconfig.col.access"),
            tr("regconfig.col.unit"),
            tr("regconfig.col.critical"),
        ])

        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        # 填充数据
        registers = [r for r in REGISTER_DEFINITIONS if r.category == category]
        table.setRowCount(len(registers))

        for row, reg in enumerate(registers):
            # 名称
            name_item = QTableWidgetItem(reg.name)
            name_item.setData(Qt.UserRole, reg)  # 存储寄存器信息
            table.setItem(row, 0, name_item)

            # 地址
            addr_item = QTableWidgetItem(f"0x{reg.address:04X}")
            table.setItem(row, 1, addr_item)

            # CiA402 索引
            cia_item = QTableWidgetItem(reg.cia402_index)
            table.setItem(row, 2, cia_item)

            # 值 (初始为空)
            value_item = QTableWidgetItem("--")
            value_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 3, value_item)

            # 访问类型
            access_item = QTableWidgetItem(reg.access)
            access_item.setTextAlignment(Qt.AlignCenter)
            if reg.access == "RO":
                access_item.setForeground(QColor("#808080"))
            table.setItem(row, 4, access_item)

            # 单位
            unit_item = QTableWidgetItem(reg.unit)
            unit_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 5, unit_item)

            # 关键标记
            critical_item = QTableWidgetItem("!" if reg.critical else "")
            critical_item.setTextAlignment(Qt.AlignCenter)
            if reg.critical:
                critical_item.setForeground(QColor("#ff8c00"))
                critical_item.setFont(QFont("", -1, QFont.Bold))
            table.setItem(row, 6, critical_item)

        # 选择变化信号
        table.itemSelectionChanged.connect(self._on_selection_changed)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)

        return table

    def _create_detail_panel(self) -> QWidget:
        """创建详细信息面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 任意寄存器读写组
        arbitrary_group = self._create_arbitrary_register_group()
        layout.addWidget(arbitrary_group)

        # 详细信息组
        detail_group = QGroupBox(tr("regconfig.detail"))
        detail_layout = QVBoxLayout(detail_group)

        # 描述
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("padding: 8px; background-color: #3d3d3d; border-radius: 4px;")
        detail_layout.addWidget(self._desc_label)

        # 地址信息
        addr_layout = QGridLayout()
        addr_layout.addWidget(QLabel(tr("regconfig.modbus_addr")), 0, 0)
        self._addr_label = QLabel("--")
        self._addr_label.setProperty("class", "value")
        addr_layout.addWidget(self._addr_label, 0, 1)

        addr_layout.addWidget(QLabel(tr("regconfig.cia402_idx")), 1, 0)
        self._cia_label = QLabel("--")
        self._cia_label.setProperty("class", "value")
        addr_layout.addWidget(self._cia_label, 1, 1)

        addr_layout.addWidget(QLabel(tr("regconfig.data_type")), 2, 0)
        self._type_label = QLabel("--")
        self._type_label.setProperty("class", "value")
        addr_layout.addWidget(self._type_label, 2, 1)

        addr_layout.addWidget(QLabel(tr("regconfig.default")), 3, 0)
        self._default_label = QLabel("--")
        self._default_label.setProperty("class", "value")
        addr_layout.addWidget(self._default_label, 3, 1)

        detail_layout.addLayout(addr_layout)
        layout.addWidget(detail_group)

        # 编辑组
        edit_group = QGroupBox(tr("regconfig.edit"))
        edit_layout = QVBoxLayout(edit_group)

        # 当前值
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel(tr("regconfig.current_value")))
        self._current_value_label = QLabel("--")
        self._current_value_label.setProperty("class", "value")
        current_layout.addWidget(self._current_value_label)
        current_layout.addStretch()

        self._read_btn = QPushButton(tr("regconfig.read"))
        self._read_btn.clicked.connect(self._read_selected_register)
        current_layout.addWidget(self._read_btn)
        edit_layout.addLayout(current_layout)

        # 新值输入
        new_value_layout = QHBoxLayout()
        new_value_layout.addWidget(QLabel(tr("regconfig.new_value")))
        self._new_value_edit = QLineEdit()
        self._new_value_edit.setPlaceholderText(tr("regconfig.enter_value"))
        new_value_layout.addWidget(self._new_value_edit)

        self._write_btn = QPushButton(tr("regconfig.write"))
        self._write_btn.setProperty("class", "warning")
        self._write_btn.clicked.connect(self._write_selected_register)
        new_value_layout.addWidget(self._write_btn)
        edit_layout.addLayout(new_value_layout)

        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel(tr("regconfig.format")))
        self._format_combo = QComboBox()
        self._format_combo.addItems([
            tr("regconfig.format.dec"),
            tr("regconfig.format.hex"),
            tr("regconfig.format.bin"),
        ])
        format_layout.addWidget(self._format_combo)
        format_layout.addStretch()
        edit_layout.addLayout(format_layout)

        layout.addWidget(edit_group)

        # 警告信息
        self._warning_label = QLabel()
        self._warning_label.setStyleSheet(
            "padding: 8px; background-color: #5a3d00; border: 1px solid #ff8c00; "
            "border-radius: 4px; color: #ffc107;"
        )
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        layout.addWidget(self._warning_label)

        layout.addStretch()

        return widget

    def _create_arbitrary_register_group(self) -> QGroupBox:
        """创建任意寄存器读写组"""
        group = QGroupBox(tr("regconfig.arbitrary.title"))
        layout = QVBoxLayout(group)

        # 地址输入行
        addr_layout = QHBoxLayout()
        self._arb_addr_label = QLabel(tr("regconfig.arbitrary.address"))
        addr_layout.addWidget(self._arb_addr_label)
        self._arb_addr_edit = QLineEdit()
        self._arb_addr_edit.setPlaceholderText("0x0380")
        self._arb_addr_edit.setMaximumWidth(100)
        addr_layout.addWidget(self._arb_addr_edit)

        # 数据类型选择
        self._arb_type_label = QLabel(tr("regconfig.arbitrary.type"))
        addr_layout.addWidget(self._arb_type_label)
        self._arb_type_combo = QComboBox()
        self._arb_type_combo.addItems(["UINT16", "INT16", "UINT32", "INT32"])
        self._arb_type_combo.setMaximumWidth(80)
        addr_layout.addWidget(self._arb_type_combo)

        addr_layout.addStretch()
        layout.addLayout(addr_layout)

        # 读取行
        read_layout = QHBoxLayout()
        self._arb_read_btn = QPushButton(tr("regconfig.arbitrary.read"))
        self._arb_read_btn.clicked.connect(self._read_arbitrary_register)
        read_layout.addWidget(self._arb_read_btn)

        self._arb_read_value_label = QLabel("--")
        self._arb_read_value_label.setProperty("class", "value")
        self._arb_read_value_label.setMinimumWidth(120)
        read_layout.addWidget(self._arb_read_value_label)

        # 显示格式
        self._arb_hex_label = QLabel("")
        self._arb_hex_label.setStyleSheet("color: #888; font-family: monospace;")
        read_layout.addWidget(self._arb_hex_label)

        read_layout.addStretch()
        layout.addLayout(read_layout)

        # 写入行
        write_layout = QHBoxLayout()
        self._arb_write_label = QLabel(tr("regconfig.arbitrary.value"))
        write_layout.addWidget(self._arb_write_label)
        self._arb_write_edit = QLineEdit()
        self._arb_write_edit.setPlaceholderText(tr("regconfig.arbitrary.value_hint"))
        self._arb_write_edit.setMaximumWidth(150)
        write_layout.addWidget(self._arb_write_edit)

        self._arb_write_btn = QPushButton(tr("regconfig.arbitrary.write"))
        self._arb_write_btn.setProperty("class", "warning")
        self._arb_write_btn.clicked.connect(self._write_arbitrary_register)
        write_layout.addWidget(self._arb_write_btn)

        write_layout.addStretch()
        layout.addLayout(write_layout)

        return group

    def _read_arbitrary_register(self) -> None:
        """读取任意寄存器"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        # 解析地址
        addr_str = self._arb_addr_edit.text().strip()
        if not addr_str:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.arbitrary.enter_addr"))
            return

        try:
            if addr_str.startswith("0x") or addr_str.startswith("0X"):
                address = int(addr_str, 16)
            else:
                address = int(addr_str)
        except ValueError:
            QMessageBox.warning(self, tr("common.error"), tr("regconfig.arbitrary.invalid_addr"))
            return

        # 获取数据类型
        type_str = self._arb_type_combo.currentText()
        is_32bit = "32" in type_str
        is_signed = type_str.startswith("INT")

        self.request_pause_timer.emit()
        try:
            motor = self._service.get_motor()
            if motor is None:
                raise RuntimeError("No motor connected")

            client = self._service.get_modbus_client()
            if client is None:
                raise RuntimeError("No Modbus client available")

            if is_32bit:
                value = client.read_register_32bit(
                    motor.slave_id, address, signed=is_signed
                )
                hex_str = f"0x{value & 0xFFFFFFFF:08X}"
            else:
                value = client.read_register(motor.slave_id, address)
                if is_signed and value > 32767:
                    value -= 65536
                hex_str = f"0x{value & 0xFFFF:04X}"

            self._arb_read_value_label.setText(str(value))
            self._arb_hex_label.setText(hex_str)

        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.read_failed')}: {e}")
            self._arb_read_value_label.setText("--")
            self._arb_hex_label.setText("")
        finally:
            self.request_resume_timer.emit()

    def _write_arbitrary_register(self) -> None:
        """写入任意寄存器"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        # 解析地址
        addr_str = self._arb_addr_edit.text().strip()
        if not addr_str:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.arbitrary.enter_addr"))
            return

        try:
            if addr_str.startswith("0x") or addr_str.startswith("0X"):
                address = int(addr_str, 16)
            else:
                address = int(addr_str)
        except ValueError:
            QMessageBox.warning(self, tr("common.error"), tr("regconfig.arbitrary.invalid_addr"))
            return

        # 解析值
        value_str = self._arb_write_edit.text().strip()
        if not value_str:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.enter_value"))
            return

        try:
            if value_str.startswith("0x") or value_str.startswith("0X"):
                value = int(value_str, 16)
            elif value_str.startswith("0b") or value_str.startswith("0B"):
                value = int(value_str, 2)
            else:
                value = int(value_str)
        except ValueError:
            QMessageBox.warning(self, tr("common.error"), tr("regconfig.invalid_value"))
            return

        # 获取数据类型
        type_str = self._arb_type_combo.currentText()
        is_32bit = "32" in type_str
        is_signed = type_str.startswith("INT")

        # 确认写入
        reply = QMessageBox.warning(
            self,
            tr("common.confirm"),
            tr("regconfig.arbitrary.confirm_write", address=f"0x{address:04X}", value=value),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.request_pause_timer.emit()
        try:
            motor = self._service.get_motor()
            if motor is None:
                raise RuntimeError("No motor connected")

            client = self._service.get_modbus_client()
            if client is None:
                raise RuntimeError("No Modbus client available")

            if is_32bit:
                client.write_register_32bit(
                    motor.slave_id, address, value, signed=is_signed
                )
            else:
                client.write_register(motor.slave_id, address, value)

            # 读回验证
            if is_32bit:
                actual = client.read_register_32bit(
                    motor.slave_id, address, signed=is_signed
                )
                hex_str = f"0x{actual & 0xFFFFFFFF:08X}"
            else:
                actual = client.read_register(motor.slave_id, address)
                if is_signed and actual > 32767:
                    actual -= 65536
                hex_str = f"0x{actual & 0xFFFF:04X}"

            self._arb_read_value_label.setText(str(actual))
            self._arb_hex_label.setText(hex_str)

            if actual == value:
                QMessageBox.information(self, tr("common.success"), tr("regconfig.write_success"))
            else:
                QMessageBox.warning(
                    self, tr("common.warning"),
                    tr("regconfig.write_mismatch", expected=value, actual=actual)
                )
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.write_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _get_current_category(self) -> RegisterCategory:
        """获取当前选择的分类"""
        index = self._category_tabs.currentIndex()
        return list(RegisterCategory)[index]

    def _get_selected_register(self) -> Optional[RegisterInfo]:
        """获取当前选择的寄存器"""
        category = self._get_current_category()
        table = self._register_tables[category]
        selected = table.selectedItems()
        if selected:
            row = selected[0].row()
            name_item = table.item(row, 0)
            return name_item.data(Qt.UserRole)
        return None

    def _on_selection_changed(self) -> None:
        """选择变化时更新详情"""
        reg = self._get_selected_register()
        if reg is None:
            return

        # 更新描述
        from ..i18n import is_chinese
        desc = reg.description_zh if is_chinese() else reg.description_en
        self._desc_label.setText(desc)

        # 更新地址信息
        self._addr_label.setText(f"0x{reg.address:04X}")
        self._cia_label.setText(reg.cia402_index)

        # 数据类型
        type_str = "INT32" if reg.size == 2 else "INT16"
        if not reg.signed:
            type_str = "U" + type_str
        type_str += f" ({reg.access})"
        self._type_label.setText(type_str)

        # 默认值
        if reg.default_value is not None:
            self._default_label.setText(str(reg.default_value))
        else:
            self._default_label.setText("--")

        # 当前值
        if reg.address in self._register_values:
            value = self._register_values[reg.address]
            self._current_value_label.setText(str(value))
        else:
            self._current_value_label.setText("--")

        # 编辑按钮状态
        can_write = reg.access in ("RW", "WO")
        self._write_btn.setEnabled(can_write)
        self._new_value_edit.setEnabled(can_write)

        # 警告
        if reg.critical:
            self._warning_label.setText(tr("regconfig.critical_warning"))
            self._warning_label.show()
        else:
            self._warning_label.hide()

    def _read_all_registers(self) -> None:
        """读取所有寄存器"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        self.request_pause_timer.emit()

        try:
            for reg in REGISTER_DEFINITIONS:
                self._read_register(reg)
            QMessageBox.information(self, tr("common.success"), tr("regconfig.read_all_success"))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.read_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _read_category_registers(self) -> None:
        """读取当前分类的寄存器"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        category = self._get_current_category()
        self.request_pause_timer.emit()

        try:
            for reg in REGISTER_DEFINITIONS:
                if reg.category == category:
                    self._read_register(reg)
            QMessageBox.information(self, tr("common.success"), tr("regconfig.read_category_success"))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.read_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _read_register(self, reg: RegisterInfo) -> int:
        """读取单个寄存器"""
        motor = self._service.get_motor()
        if motor is None:
            raise RuntimeError("No motor connected")

        client = self._service.get_modbus_client()
        if client is None:
            raise RuntimeError("No Modbus client available")

        if reg.size == 2:
            value = client.read_register_32bit(
                motor.slave_id, reg.address, signed=reg.signed
            )
        else:
            value = client.read_register(motor.slave_id, reg.address)
            if reg.signed and value > 32767:
                value -= 65536

        # 更新缓存
        self._register_values[reg.address] = value

        # 更新表格
        self._update_table_value(reg, value)

        return value

    def _update_table_value(self, reg: RegisterInfo, value: int) -> None:
        """更新表格中的值"""
        table = self._register_tables[reg.category]
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(Qt.UserRole) == reg:
                value_item = table.item(row, 3)
                value_item.setText(str(value))

                # 检查是否与默认值不同
                if reg.default_value is not None and value != reg.default_value:
                    value_item.setForeground(QColor("#ff8c00"))
                else:
                    value_item.setForeground(QColor("#e0e0e0"))
                break

    def _read_selected_register(self) -> None:
        """读取选中的寄存器"""
        reg = self._get_selected_register()
        if reg is None:
            return

        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        self.request_pause_timer.emit()
        try:
            value = self._read_register(reg)
            self._current_value_label.setText(str(value))
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.read_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _write_selected_register(self) -> None:
        """写入选中的寄存器"""
        reg = self._get_selected_register()
        if reg is None:
            return

        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        # 获取新值
        value_str = self._new_value_edit.text().strip()
        if not value_str:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.enter_value"))
            return

        # 解析值
        try:
            if value_str.startswith("0x") or value_str.startswith("0X"):
                value = int(value_str, 16)
            elif value_str.startswith("0b") or value_str.startswith("0B"):
                value = int(value_str, 2)
            else:
                value = int(value_str)
        except ValueError:
            QMessageBox.warning(self, tr("common.error"), tr("regconfig.invalid_value"))
            return

        # 关键寄存器确认
        if reg.critical:
            reply = QMessageBox.warning(
                self,
                tr("common.confirm"),
                tr("regconfig.confirm_write", name=reg.name, value=value),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.request_pause_timer.emit()
        try:
            motor = self._service.get_motor()
            if motor is None:
                raise RuntimeError("No motor connected")

            client = self._service.get_modbus_client()
            if client is None:
                raise RuntimeError("No Modbus client available")

            if reg.size == 2:
                client.write_register_32bit(
                    motor.slave_id, reg.address, value, signed=reg.signed
                )
            else:
                client.write_register(motor.slave_id, reg.address, value)

            # 重新读取验证
            actual = self._read_register(reg)
            self._current_value_label.setText(str(actual))

            if actual == value:
                QMessageBox.information(self, tr("common.success"), tr("regconfig.write_success"))
            else:
                QMessageBox.warning(
                    self, tr("common.warning"),
                    tr("regconfig.write_mismatch", expected=value, actual=actual)
                )
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.write_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _verify_configuration(self) -> None:
        """验证配置"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        self.request_pause_timer.emit()
        issues = []

        try:
            for reg in REGISTER_DEFINITIONS:
                if reg.default_value is not None:
                    value = self._read_register(reg)
                    if value != reg.default_value:
                        issues.append(
                            f"{reg.name}: {tr('regconfig.expected')} {reg.default_value}, "
                            f"{tr('regconfig.actual')} {value}"
                        )

            if issues:
                msg = tr("regconfig.verify_issues") + "\n\n" + "\n".join(issues)
                QMessageBox.warning(self, tr("regconfig.verify_result"), msg)
            else:
                QMessageBox.information(
                    self, tr("regconfig.verify_result"),
                    tr("regconfig.verify_ok")
                )
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.verify_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def _save_to_eeprom(self) -> None:
        """保存到 EEPROM"""
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("common.warning"), tr("regconfig.connect_first"))
            return

        reply = QMessageBox.warning(
            self,
            tr("common.confirm"),
            tr("regconfig.confirm_save_eeprom"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.request_pause_timer.emit()
        try:
            motor = self._service.get_motor()
            if motor is None:
                raise RuntimeError("No motor connected")

            client = self._service.get_modbus_client()
            if client is None:
                raise RuntimeError("No Modbus client available")

            # 写入 "save" (0x65766173) 到寄存器 0x0026
            client.write_register_32bit(
                motor.slave_id, 0x0026, 0x65766173
            )

            QMessageBox.information(
                self, tr("common.success"),
                tr("regconfig.save_eeprom_success")
            )
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), f"{tr('regconfig.save_eeprom_failed')}: {e}")
        finally:
            self.request_resume_timer.emit()

    def refresh_texts(self) -> None:
        """刷新界面文本"""
        self.setTitle(tr("regconfig.title"))

        # 工具栏按钮
        self._read_all_btn.setText(tr("regconfig.read_all"))
        self._read_category_btn.setText(tr("regconfig.read_category"))
        self._verify_btn.setText(tr("regconfig.verify"))
        self._save_eeprom_btn.setText(tr("regconfig.save_eeprom"))

        # 分类选项卡
        for i, category in enumerate(RegisterCategory):
            tab_name = tr(f"regconfig.cat.{category.value}")
            self._category_tabs.setTabText(i, tab_name)

        # 更新表格表头
        for table in self._register_tables.values():
            table.setHorizontalHeaderLabels([
                tr("regconfig.col.name"),
                tr("regconfig.col.address"),
                tr("regconfig.col.cia402"),
                tr("regconfig.col.value"),
                tr("regconfig.col.access"),
                tr("regconfig.col.unit"),
                tr("regconfig.col.critical"),
            ])

        # 任意寄存器读写组
        self._arb_addr_label.setText(tr("regconfig.arbitrary.address"))
        self._arb_type_label.setText(tr("regconfig.arbitrary.type"))
        self._arb_read_btn.setText(tr("regconfig.arbitrary.read"))
        self._arb_write_label.setText(tr("regconfig.arbitrary.value"))
        self._arb_write_edit.setPlaceholderText(tr("regconfig.arbitrary.value_hint"))
        self._arb_write_btn.setText(tr("regconfig.arbitrary.write"))

        # 详情面板按钮
        self._read_btn.setText(tr("regconfig.read"))
        self._write_btn.setText(tr("regconfig.write"))
        self._new_value_edit.setPlaceholderText(tr("regconfig.enter_value"))

        # 更新当前选择的详情
        self._on_selection_changed()
