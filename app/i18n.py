"""
国际化 (i18n) 模块

提供中英双语支持，包含语言设置持久化。
"""

import logging
from enum import Enum
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import QSettings

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言"""
    CHINESE = "zh"
    ENGLISH = "en"


# 应用程序配置
_APP_NAME = "NiMotionServoControl"
_ORG_NAME = "NiMotion"
_SETTINGS_KEY_LANGUAGE = "app/language"

# 当前语言
_current_language = Language.CHINESE

# 语言变更回调列表
_language_callbacks: List[Callable[[], None]] = []

# QSettings 实例 (延迟初始化)
_settings: Optional[QSettings] = None


def _get_settings() -> QSettings:
    """获取 QSettings 实例"""
    global _settings
    if _settings is None:
        _settings = QSettings(_ORG_NAME, _APP_NAME)
    return _settings


def load_language() -> Language:
    """
    从配置文件加载保存的语言设置

    Returns:
        保存的语言，如果没有保存则返回默认语言（中文）
    """
    global _current_language
    settings = _get_settings()
    saved_lang = settings.value(_SETTINGS_KEY_LANGUAGE, Language.CHINESE.value)

    # 将保存的值转换为 Language 枚举
    for lang in Language:
        if lang.value == saved_lang:
            _current_language = lang
            logger.info(f"已加载语言设置: {lang.value}")
            return lang

    # 默认返回中文
    _current_language = Language.CHINESE
    return Language.CHINESE


def _save_language(lang: Language) -> None:
    """
    保存语言设置到配置文件

    Args:
        lang: 要保存的语言
    """
    settings = _get_settings()
    settings.setValue(_SETTINGS_KEY_LANGUAGE, lang.value)
    settings.sync()
    logger.info(f"已保存语言设置: {lang.value}")


# 翻译字典
TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    # ==================== 主窗口 ====================
    "app.title": {
        Language.CHINESE: "NiMotion 伺服电机控制系统",
        Language.ENGLISH: "NiMotion Servo Motor Control System",
    },
    "app.version": {
        Language.CHINESE: "版本",
        Language.ENGLISH: "Version",
    },

    # 菜单
    "menu.file": {
        Language.CHINESE: "文件(&F)",
        Language.ENGLISH: "&File",
    },
    "menu.exit": {
        Language.CHINESE: "退出(&X)",
        Language.ENGLISH: "E&xit",
    },
    "menu.view": {
        Language.CHINESE: "视图(&V)",
        Language.ENGLISH: "&View",
    },
    "menu.motor_control": {
        Language.CHINESE: "电机控制(&M)",
        Language.ENGLISH: "&Motor Control",
    },
    "menu.modbus_debug": {
        Language.CHINESE: "Modbus 调试(&D)",
        Language.ENGLISH: "Modbus &Debug",
    },
    "menu.register_config": {
        Language.CHINESE: "寄存器配置(&R)",
        Language.ENGLISH: "&Register Config",
    },
    "menu.connect": {
        Language.CHINESE: "连接(&C)",
        Language.ENGLISH: "&Connect",
    },
    "menu.connect_action": {
        Language.CHINESE: "连接(&C)",
        Language.ENGLISH: "&Connect",
    },
    "menu.disconnect": {
        Language.CHINESE: "断开(&D)",
        Language.ENGLISH: "&Disconnect",
    },
    "menu.control": {
        Language.CHINESE: "控制(&O)",
        Language.ENGLISH: "C&ontrol",
    },
    "menu.enable": {
        Language.CHINESE: "使能电机(&E)",
        Language.ENGLISH: "&Enable Motor",
    },
    "menu.disable": {
        Language.CHINESE: "禁用电机(&D)",
        Language.ENGLISH: "&Disable Motor",
    },
    "menu.stop": {
        Language.CHINESE: "停止(&S)",
        Language.ENGLISH: "&Stop",
    },
    "menu.quick_stop": {
        Language.CHINESE: "快速停止(&Q)",
        Language.ENGLISH: "&Quick Stop",
    },
    "menu.home": {
        Language.CHINESE: "回零(&H)",
        Language.ENGLISH: "&Home",
    },
    "menu.help": {
        Language.CHINESE: "帮助(&H)",
        Language.ENGLISH: "&Help",
    },
    "menu.about": {
        Language.CHINESE: "关于(&A)",
        Language.ENGLISH: "&About",
    },
    "menu.language": {
        Language.CHINESE: "语言(&L)",
        Language.ENGLISH: "&Language",
    },
    "menu.chinese": {
        Language.CHINESE: "中文(&C)",
        Language.ENGLISH: "&Chinese",
    },
    "menu.english": {
        Language.CHINESE: "英文(&E)",
        Language.ENGLISH: "&English",
    },

    # 状态栏
    "status.ready": {
        Language.CHINESE: "就绪",
        Language.ENGLISH: "Ready",
    },
    "status.connected": {
        Language.CHINESE: "已连接",
        Language.ENGLISH: "Connected",
    },
    "status.disconnected": {
        Language.CHINESE: "已断开",
        Language.ENGLISH: "Disconnected",
    },
    "status.view_motor": {
        Language.CHINESE: "电机控制视图",
        Language.ENGLISH: "Motor Control View",
    },
    "status.view_modbus": {
        Language.CHINESE: "Modbus 调试视图",
        Language.ENGLISH: "Modbus Debug View",
    },
    "status.view_register": {
        Language.CHINESE: "寄存器配置视图",
        Language.ENGLISH: "Register Config View",
    },

    # 关于对话框
    "about.title": {
        Language.CHINESE: "关于",
        Language.ENGLISH: "About",
    },
    "about.content": {
        Language.CHINESE: (
            "<h3>NiMotion 伺服电机控制系统</h3>"
            "<p>版本: 0.1.0</p>"
            "<p>基于 PyQt5 和 Modbus RTU 协议</p>"
            "<p>支持 XYG321-A 三轴平台</p>"
        ),
        Language.ENGLISH: (
            "<h3>NiMotion Servo Motor Control System</h3>"
            "<p>Version: 0.1.0</p>"
            "<p>Based on PyQt5 and Modbus RTU Protocol</p>"
            "<p>Supports XYG321-A 3-Axis Platform</p>"
        ),
    },

    # ==================== 连接面板 ====================
    "connection.title": {
        Language.CHINESE: "连接设置",
        Language.ENGLISH: "Connection Settings",
    },
    "connection.port": {
        Language.CHINESE: "串口:",
        Language.ENGLISH: "Port:",
    },
    "connection.baudrate": {
        Language.CHINESE: "波特率:",
        Language.ENGLISH: "Baud Rate:",
    },
    "connection.status": {
        Language.CHINESE: "状态:",
        Language.ENGLISH: "Status:",
    },
    "connection.refresh": {
        Language.CHINESE: "刷新",
        Language.ENGLISH: "Refresh",
    },
    "connection.connect": {
        Language.CHINESE: "连接",
        Language.ENGLISH: "Connect",
    },
    "connection.disconnect": {
        Language.CHINESE: "断开",
        Language.ENGLISH: "Disconnect",
    },
    "connection.connected": {
        Language.CHINESE: "已连接",
        Language.ENGLISH: "Connected",
    },
    "connection.not_connected": {
        Language.CHINESE: "未连接",
        Language.ENGLISH: "Not Connected",
    },
    "connection.no_port": {
        Language.CHINESE: "未检测到串口",
        Language.ENGLISH: "No Port Detected",
    },
    "connection.select_port": {
        Language.CHINESE: "请选择有效的串口",
        Language.ENGLISH: "Please select a valid port",
    },
    "connection.failed": {
        Language.CHINESE: "连接失败",
        Language.ENGLISH: "Connection Failed",
    },
    "connection.failed_msg": {
        Language.CHINESE: "无法连接到串口:",
        Language.ENGLISH: "Failed to connect to port:",
    },
    "connection.disconnect_failed": {
        Language.CHINESE: "断开失败",
        Language.ENGLISH: "Disconnect Failed",
    },
    "connection.disconnect_error": {
        Language.CHINESE: "断开连接时出错:",
        Language.ENGLISH: "Error disconnecting:",
    },

    # ==================== 轴选择面板 ====================
    "axis.title": {
        Language.CHINESE: "轴选择",
        Language.ENGLISH: "Axis Selection",
    },
    "axis.x": {
        Language.CHINESE: "X 轴",
        Language.ENGLISH: "X Axis",
    },
    "axis.y": {
        Language.CHINESE: "Y 轴",
        Language.ENGLISH: "Y Axis",
    },
    "axis.z": {
        Language.CHINESE: "Z 轴",
        Language.ENGLISH: "Z Axis",
    },
    "axis.model": {
        Language.CHINESE: "型号",
        Language.ENGLISH: "Model",
    },
    "axis.power": {
        Language.CHINESE: "功率",
        Language.ENGLISH: "Power",
    },
    "axis.stroke": {
        Language.CHINESE: "行程",
        Language.ENGLISH: "Stroke",
    },
    "axis.slave": {
        Language.CHINESE: "从站",
        Language.ENGLISH: "Slave",
    },
    "axis.max_speed": {
        Language.CHINESE: "最大速度",
        Language.ENGLISH: "Max Speed",
    },
    "axis.with_brake": {
        Language.CHINESE: "带抱闸",
        Language.ENGLISH: "With Brake",
    },

    # ==================== 状态面板 ====================
    "status_panel.title": {
        Language.CHINESE: "状态监控",
        Language.ENGLISH: "Status Monitor",
    },
    "status_panel.position": {
        Language.CHINESE: "位置:",
        Language.ENGLISH: "Position:",
    },
    "status_panel.velocity": {
        Language.CHINESE: "速度:",
        Language.ENGLISH: "Velocity:",
    },
    "status_panel.torque": {
        Language.CHINESE: "转矩:",
        Language.ENGLISH: "Torque:",
    },
    "status_panel.drive_state": {
        Language.CHINESE: "驱动器状态:",
        Language.ENGLISH: "Drive State:",
    },
    "status_panel.op_mode": {
        Language.CHINESE: "操作模式:",
        Language.ENGLISH: "Op Mode:",
    },
    "status_panel.error_code": {
        Language.CHINESE: "错误码:",
        Language.ENGLISH: "Error Code:",
    },
    "status_panel.status_word": {
        Language.CHINESE: "状态字:",
        Language.ENGLISH: "Status Word:",
    },
    "status_panel.none": {
        Language.CHINESE: "无",
        Language.ENGLISH: "None",
    },
    "status_panel.unknown": {
        Language.CHINESE: "未知",
        Language.ENGLISH: "Unknown",
    },
    "status_panel.enabled": {
        Language.CHINESE: "使能",
        Language.ENGLISH: "Enabled",
    },
    "status_panel.fault": {
        Language.CHINESE: "故障",
        Language.ENGLISH: "Fault",
    },
    "status_panel.homed": {
        Language.CHINESE: "回零",
        Language.ENGLISH: "Homed",
    },
    "status_panel.target": {
        Language.CHINESE: "到位",
        Language.ENGLISH: "Target",
    },
    "status_panel.stroke_pos": {
        Language.CHINESE: "行程位置:",
        Language.ENGLISH: "Stroke Position:",
    },

    # ==================== 运动面板 ====================
    "motion.title": {
        Language.CHINESE: "运动控制",
        Language.ENGLISH: "Motion Control",
    },
    "motion.enable": {
        Language.CHINESE: "使能",
        Language.ENGLISH: "Enable",
    },
    "motion.disable": {
        Language.CHINESE: "禁用",
        Language.ENGLISH: "Disable",
    },
    "motion.stop": {
        Language.CHINESE: "停止",
        Language.ENGLISH: "Stop",
    },
    "motion.quick_stop": {
        Language.CHINESE: "急停",
        Language.ENGLISH: "E-Stop",
    },
    "motion.jog": {
        Language.CHINESE: "点动",
        Language.ENGLISH: "Jog",
    },
    "motion.position": {
        Language.CHINESE: "位置",
        Language.ENGLISH: "Position",
    },
    "motion.home": {
        Language.CHINESE: "回零",
        Language.ENGLISH: "Home",
    },
    "motion.jog_speed": {
        Language.CHINESE: "点动速度:",
        Language.ENGLISH: "Jog Speed:",
    },
    "motion.negative": {
        Language.CHINESE: "◀ 负向",
        Language.ENGLISH: "◀ Negative",
    },
    "motion.positive": {
        Language.CHINESE: "正向 ▶",
        Language.ENGLISH: "Positive ▶",
    },
    "motion.step": {
        Language.CHINESE: "步进:",
        Language.ENGLISH: "Step:",
    },
    "motion.target_pos": {
        Language.CHINESE: "目标位置:",
        Language.ENGLISH: "Target Position:",
    },
    "motion.move_speed": {
        Language.CHINESE: "移动速度:",
        Language.ENGLISH: "Move Speed:",
    },
    "motion.move_abs": {
        Language.CHINESE: "绝对移动",
        Language.ENGLISH: "Move Absolute",
    },
    "motion.move_rel": {
        Language.CHINESE: "相对移动",
        Language.ENGLISH: "Move Relative",
    },
    "motion.quick_pos": {
        Language.CHINESE: "快速定位:",
        Language.ENGLISH: "Quick Position:",
    },
    "motion.min": {
        Language.CHINESE: "最小",
        Language.ENGLISH: "Min",
    },
    "motion.mid": {
        Language.CHINESE: "中点",
        Language.ENGLISH: "Mid",
    },
    "motion.max": {
        Language.CHINESE: "最大",
        Language.ENGLISH: "Max",
    },
    "motion.start_home": {
        Language.CHINESE: "开始回零",
        Language.ENGLISH: "Start Homing",
    },
    "motion.set_home": {
        Language.CHINESE: "将当前位置设为原点",
        Language.ENGLISH: "Set Current Position as Home",
    },
    "motion.fault_reset": {
        Language.CHINESE: "故障复位",
        Language.ENGLISH: "Fault Reset",
    },
    "motion.confirm_home": {
        Language.CHINESE: "确定要执行回零操作吗?",
        Language.ENGLISH: "Are you sure you want to perform homing?",
    },
    "motion.home_set": {
        Language.CHINESE: "已将当前位置设为原点",
        Language.ENGLISH: "Current position set as home",
    },
    "motion.fault_cleared": {
        Language.CHINESE: "故障已复位",
        Language.ENGLISH: "Fault cleared",
    },
    "motion.busy": {
        Language.CHINESE: "上一个运动操作尚未完成",
        Language.ENGLISH: "Previous motion operation not completed",
    },
    "motion.failed": {
        Language.CHINESE: "运动失败",
        Language.ENGLISH: "Motion Failed",
    },
    "motion.step_failed": {
        Language.CHINESE: "步进移动失败",
        Language.ENGLISH: "Step move failed",
    },
    "motion.home_confirm": {
        Language.CHINESE: "确定要执行回零操作吗?",
        Language.ENGLISH: "Are you sure you want to perform homing?",
    },
    "motion.set_home_success": {
        Language.CHINESE: "已将当前位置设为原点",
        Language.ENGLISH: "Current position set as home",
    },
    "motion.set_home_failed": {
        Language.CHINESE: "设置原点失败",
        Language.ENGLISH: "Failed to set home position",
    },
    "motion.fault_reset_success": {
        Language.CHINESE: "故障已复位",
        Language.ENGLISH: "Fault has been reset",
    },
    "motion.fault_reset_failed": {
        Language.CHINESE: "故障复位失败",
        Language.ENGLISH: "Fault reset failed",
    },
    "motion.enable_failed": {
        Language.CHINESE: "使能失败",
        Language.ENGLISH: "Enable failed",
    },
    "motion.disable_failed": {
        Language.CHINESE: "禁用失败",
        Language.ENGLISH: "Disable failed",
    },
    "motion.operation_in_progress": {
        Language.CHINESE: "上一个运动操作尚未完成",
        Language.ENGLISH: "Previous motion operation not completed",
    },
    "motion.motion_failed": {
        Language.CHINESE: "运动失败",
        Language.ENGLISH: "Motion Failed",
    },

    # ==================== 参数面板 ====================
    "param.title": {
        Language.CHINESE: "运动参数",
        Language.ENGLISH: "Motion Parameters",
    },
    "param.velocity": {
        Language.CHINESE: "默认速度:",
        Language.ENGLISH: "Default Velocity:",
    },
    "param.acceleration": {
        Language.CHINESE: "加速度:",
        Language.ENGLISH: "Acceleration:",
    },
    "param.deceleration": {
        Language.CHINESE: "减速度:",
        Language.ENGLISH: "Deceleration:",
    },
    "param.apply": {
        Language.CHINESE: "应用参数",
        Language.ENGLISH: "Apply Parameters",
    },
    "param.read": {
        Language.CHINESE: "读取当前",
        Language.ENGLISH: "Read Current",
    },
    "param.load_default": {
        Language.CHINESE: "加载默认值",
        Language.ENGLISH: "Load Defaults",
    },
    "param.connect_first": {
        Language.CHINESE: "请先连接到伺服系统",
        Language.ENGLISH: "Please connect to servo system first",
    },
    "param.applied": {
        Language.CHINESE: "参数已应用",
        Language.ENGLISH: "Parameters applied",
    },
    "param.apply_failed": {
        Language.CHINESE: "应用参数失败",
        Language.ENGLISH: "Failed to apply parameters",
    },
    "param.read_success": {
        Language.CHINESE: "已读取当前参数",
        Language.ENGLISH: "Current parameters read",
    },
    "param.read_failed": {
        Language.CHINESE: "读取参数失败",
        Language.ENGLISH: "Failed to read parameters",
    },
    "param.read_success_detail": {
        Language.CHINESE: "已读取当前参数:\n速度: {vel:.1f} mm/s\n加速度: {accel:.1f} mm/s²\n减速度: {decel:.1f} mm/s²",
        Language.ENGLISH: "Current parameters read:\nVelocity: {vel:.1f} mm/s\nAcceleration: {accel:.1f} mm/s²\nDeceleration: {decel:.1f} mm/s²",
    },

    # ==================== Modbus 调试面板 ====================
    "modbus.title": {
        Language.CHINESE: "Modbus 调试",
        Language.ENGLISH: "Modbus Debug",
    },
    "modbus.quick_access": {
        Language.CHINESE: "快捷操作",
        Language.ENGLISH: "Quick Access",
    },
    "modbus.slave": {
        Language.CHINESE: "从站:",
        Language.ENGLISH: "Slave:",
    },
    "modbus.address": {
        Language.CHINESE: "地址:",
        Language.ENGLISH: "Address:",
    },
    "modbus.count": {
        Language.CHINESE: "数量:",
        Language.ENGLISH: "Count:",
    },
    "modbus.read": {
        Language.CHINESE: "读取",
        Language.ENGLISH: "Read",
    },
    "modbus.manual_send": {
        Language.CHINESE: "手动发送",
        Language.ENGLISH: "Manual Send",
    },
    "modbus.function_code": {
        Language.CHINESE: "功能码:",
        Language.ENGLISH: "Function Code:",
    },
    "modbus.start_addr": {
        Language.CHINESE: "起始地址:",
        Language.ENGLISH: "Start Address:",
    },
    "modbus.data": {
        Language.CHINESE: "数据:",
        Language.ENGLISH: "Data:",
    },
    "modbus.frame_preview": {
        Language.CHINESE: "帧预览:",
        Language.ENGLISH: "Frame Preview:",
    },
    "modbus.send": {
        Language.CHINESE: "发送",
        Language.ENGLISH: "Send",
    },
    "modbus.comm_log": {
        Language.CHINESE: "通信日志",
        Language.ENGLISH: "Communication Log",
    },
    "modbus.clear": {
        Language.CHINESE: "清空",
        Language.ENGLISH: "Clear",
    },
    "modbus.export": {
        Language.CHINESE: "导出",
        Language.ENGLISH: "Export",
    },
    "modbus.export_title": {
        Language.CHINESE: "导出日志",
        Language.ENGLISH: "Export Log",
    },
    "modbus.exported": {
        Language.CHINESE: "日志已导出到:",
        Language.ENGLISH: "Log exported to:",
    },
    "modbus.export_failed": {
        Language.CHINESE: "导出失败:",
        Language.ENGLISH: "Export failed:",
    },
    "modbus.reset_stats": {
        Language.CHINESE: "重置统计",
        Language.ENGLISH: "Reset Stats",
    },
    "modbus.stats": {
        Language.CHINESE: "发送: {tx}  接收: {rx}  错误: {err}  成功率: {rate}",
        Language.ENGLISH: "TX: {tx}  RX: {rx}  Errors: {err}  Success: {rate}",
    },
    "modbus.not_connected": {
        Language.CHINESE: "未连接到设备",
        Language.ENGLISH: "Not connected to device",
    },
    "modbus.read_holding": {
        Language.CHINESE: "读保持寄存器",
        Language.ENGLISH: "Read Holding Registers",
    },
    "modbus.read_input": {
        Language.CHINESE: "读输入寄存器",
        Language.ENGLISH: "Read Input Registers",
    },
    "modbus.write_single": {
        Language.CHINESE: "写寄存器",
        Language.ENGLISH: "Write Register",
    },
    "modbus.write_success": {
        Language.CHINESE: "写入成功",
        Language.ENGLISH: "Write successful",
    },
    "modbus.write_multi_success": {
        Language.CHINESE: "写入 {count} 个寄存器成功",
        Language.ENGLISH: "Written {count} registers successfully",
    },
    "modbus.read_failed": {
        Language.CHINESE: "读取失败:",
        Language.ENGLISH: "Read failed:",
    },
    "modbus.write_failed": {
        Language.CHINESE: "写入失败:",
        Language.ENGLISH: "Write failed:",
    },
    "modbus.send_failed": {
        Language.CHINESE: "发送失败:",
        Language.ENGLISH: "Send failed:",
    },
    "modbus.addr_empty": {
        Language.CHINESE: "地址不能为空",
        Language.ENGLISH: "Address cannot be empty",
    },
    "modbus.data_empty": {
        Language.CHINESE: "数据不能为空",
        Language.ENGLISH: "Data cannot be empty",
    },
    "modbus.success": {
        Language.CHINESE: "成功",
        Language.ENGLISH: "Success",
    },
    "modbus.rx_data": {
        Language.CHINESE: "数据:",
        Language.ENGLISH: "Data:",
    },

    # 寄存器名称
    "reg.status_word": {
        Language.CHINESE: "状态字",
        Language.ENGLISH: "Status",
    },
    "reg.control_word": {
        Language.CHINESE: "控制字",
        Language.ENGLISH: "Control",
    },
    "reg.position": {
        Language.CHINESE: "位置",
        Language.ENGLISH: "Position",
    },
    "reg.velocity": {
        Language.CHINESE: "速度",
        Language.ENGLISH: "Velocity",
    },
    "reg.error_code": {
        Language.CHINESE: "错误码",
        Language.ENGLISH: "Error",
    },
    "reg.mode": {
        Language.CHINESE: "模式",
        Language.ENGLISH: "Mode",
    },

    # 功能码
    "fc.read_holding": {
        Language.CHINESE: "0x03 读保持寄存器",
        Language.ENGLISH: "0x03 Read Holding Registers",
    },
    "fc.read_input": {
        Language.CHINESE: "0x04 读输入寄存器",
        Language.ENGLISH: "0x04 Read Input Registers",
    },
    "fc.write_single": {
        Language.CHINESE: "0x06 写单个寄存器",
        Language.ENGLISH: "0x06 Write Single Register",
    },
    "fc.write_multi": {
        Language.CHINESE: "0x10 写多个寄存器",
        Language.ENGLISH: "0x10 Write Multiple Registers",
    },

    # ==================== 通用 ====================
    "common.confirm": {
        Language.CHINESE: "确认",
        Language.ENGLISH: "Confirm",
    },
    "common.warning": {
        Language.CHINESE: "警告",
        Language.ENGLISH: "Warning",
    },
    "common.error": {
        Language.CHINESE: "错误",
        Language.ENGLISH: "Error",
    },
    "common.success": {
        Language.CHINESE: "成功",
        Language.ENGLISH: "Success",
    },
    "common.yes": {
        Language.CHINESE: "是",
        Language.ENGLISH: "Yes",
    },
    "common.no": {
        Language.CHINESE: "否",
        Language.ENGLISH: "No",
    },
    "common.ok": {
        Language.CHINESE: "确定",
        Language.ENGLISH: "OK",
    },
    "common.cancel": {
        Language.CHINESE: "取消",
        Language.ENGLISH: "Cancel",
    },
    "common.switch_to": {
        Language.CHINESE: "切换到",
        Language.ENGLISH: "Switch to",
    },

    # ==================== 寄存器配置面板 ====================
    "regconfig.title": {
        Language.CHINESE: "寄存器配置",
        Language.ENGLISH: "Register Configuration",
    },
    "regconfig.read_all": {
        Language.CHINESE: "读取全部",
        Language.ENGLISH: "Read All",
    },
    "regconfig.read_category": {
        Language.CHINESE: "读取当前分类",
        Language.ENGLISH: "Read Category",
    },
    "regconfig.verify": {
        Language.CHINESE: "验证配置",
        Language.ENGLISH: "Verify Config",
    },
    "regconfig.save_eeprom": {
        Language.CHINESE: "保存到 EEPROM",
        Language.ENGLISH: "Save to EEPROM",
    },

    # 分类标签
    "regconfig.cat.control": {
        Language.CHINESE: "核心控制",
        Language.ENGLISH: "Core Control",
    },
    "regconfig.cat.position": {
        Language.CHINESE: "位置控制",
        Language.ENGLISH: "Position Control",
    },
    "regconfig.cat.velocity": {
        Language.CHINESE: "速度控制",
        Language.ENGLISH: "Velocity Control",
    },
    "regconfig.cat.homing": {
        Language.CHINESE: "回零控制",
        Language.ENGLISH: "Homing Control",
    },
    "regconfig.cat.di_config": {
        Language.CHINESE: "DI 配置",
        Language.ENGLISH: "DI Config",
    },
    "regconfig.cat.encoder": {
        Language.CHINESE: "编码器配置",
        Language.ENGLISH: "Encoder Config",
    },

    # 表格列
    "regconfig.col.name": {
        Language.CHINESE: "名称",
        Language.ENGLISH: "Name",
    },
    "regconfig.col.address": {
        Language.CHINESE: "地址",
        Language.ENGLISH: "Address",
    },
    "regconfig.col.cia402": {
        Language.CHINESE: "CiA402",
        Language.ENGLISH: "CiA402",
    },
    "regconfig.col.value": {
        Language.CHINESE: "值",
        Language.ENGLISH: "Value",
    },
    "regconfig.col.access": {
        Language.CHINESE: "访问",
        Language.ENGLISH: "Access",
    },
    "regconfig.col.unit": {
        Language.CHINESE: "单位",
        Language.ENGLISH: "Unit",
    },
    "regconfig.col.critical": {
        Language.CHINESE: "关键",
        Language.ENGLISH: "Critical",
    },

    # 详情面板
    "regconfig.detail": {
        Language.CHINESE: "详细信息",
        Language.ENGLISH: "Details",
    },
    "regconfig.modbus_addr": {
        Language.CHINESE: "Modbus 地址:",
        Language.ENGLISH: "Modbus Address:",
    },
    "regconfig.cia402_idx": {
        Language.CHINESE: "CiA402 索引:",
        Language.ENGLISH: "CiA402 Index:",
    },
    "regconfig.data_type": {
        Language.CHINESE: "数据类型:",
        Language.ENGLISH: "Data Type:",
    },
    "regconfig.default": {
        Language.CHINESE: "默认值:",
        Language.ENGLISH: "Default:",
    },

    # 编辑面板
    "regconfig.edit": {
        Language.CHINESE: "编辑",
        Language.ENGLISH: "Edit",
    },
    "regconfig.current_value": {
        Language.CHINESE: "当前值:",
        Language.ENGLISH: "Current Value:",
    },
    "regconfig.new_value": {
        Language.CHINESE: "新值:",
        Language.ENGLISH: "New Value:",
    },
    "regconfig.enter_value": {
        Language.CHINESE: "输入数值 (支持十进制/十六进制0x/二进制0b)",
        Language.ENGLISH: "Enter value (dec/hex 0x/bin 0b)",
    },
    "regconfig.read": {
        Language.CHINESE: "读取",
        Language.ENGLISH: "Read",
    },
    "regconfig.write": {
        Language.CHINESE: "写入",
        Language.ENGLISH: "Write",
    },
    "regconfig.format": {
        Language.CHINESE: "显示格式:",
        Language.ENGLISH: "Display Format:",
    },
    "regconfig.format.dec": {
        Language.CHINESE: "十进制",
        Language.ENGLISH: "Decimal",
    },
    "regconfig.format.hex": {
        Language.CHINESE: "十六进制",
        Language.ENGLISH: "Hexadecimal",
    },
    "regconfig.format.bin": {
        Language.CHINESE: "二进制",
        Language.ENGLISH: "Binary",
    },

    # 警告和消息
    "regconfig.critical_warning": {
        Language.CHINESE: "⚠ 这是关键寄存器，修改可能影响电机正常运行！外部软件可能会修改此值。",
        Language.ENGLISH: "⚠ Critical register! Modification may affect motor operation. External software may modify this value.",
    },
    "regconfig.connect_first": {
        Language.CHINESE: "请先连接到伺服系统",
        Language.ENGLISH: "Please connect to servo system first",
    },
    "regconfig.read_all_success": {
        Language.CHINESE: "已读取所有寄存器",
        Language.ENGLISH: "All registers read successfully",
    },
    "regconfig.read_category_success": {
        Language.CHINESE: "已读取当前分类寄存器",
        Language.ENGLISH: "Category registers read successfully",
    },
    "regconfig.read_failed": {
        Language.CHINESE: "读取失败",
        Language.ENGLISH: "Read failed",
    },
    "regconfig.write_success": {
        Language.CHINESE: "写入成功",
        Language.ENGLISH: "Write successful",
    },
    "regconfig.write_failed": {
        Language.CHINESE: "写入失败",
        Language.ENGLISH: "Write failed",
    },
    "regconfig.write_mismatch": {
        Language.CHINESE: "写入后验证不匹配: 期望 {expected}, 实际 {actual}",
        Language.ENGLISH: "Write verification mismatch: expected {expected}, actual {actual}",
    },
    "regconfig.invalid_value": {
        Language.CHINESE: "无效的数值格式",
        Language.ENGLISH: "Invalid value format",
    },
    "regconfig.confirm_write": {
        Language.CHINESE: "确定要写入寄存器 {name} = {value} 吗?",
        Language.ENGLISH: "Are you sure you want to write {name} = {value}?",
    },

    # 验证相关
    "regconfig.verify_issues": {
        Language.CHINESE: "发现以下配置问题:",
        Language.ENGLISH: "Configuration issues found:",
    },
    "regconfig.verify_result": {
        Language.CHINESE: "验证结果",
        Language.ENGLISH: "Verification Result",
    },
    "regconfig.verify_ok": {
        Language.CHINESE: "所有关键寄存器配置正确",
        Language.ENGLISH: "All critical registers are correctly configured",
    },
    "regconfig.verify_failed": {
        Language.CHINESE: "验证失败",
        Language.ENGLISH: "Verification failed",
    },
    "regconfig.expected": {
        Language.CHINESE: "期望",
        Language.ENGLISH: "expected",
    },
    "regconfig.actual": {
        Language.CHINESE: "实际",
        Language.ENGLISH: "actual",
    },

    # EEPROM 相关
    "regconfig.confirm_save_eeprom": {
        Language.CHINESE: "确定要将当前参数保存到驱动器 EEPROM 吗?\n\n保存后断电重启也会保持这些设置。",
        Language.ENGLISH: "Are you sure you want to save current parameters to driver EEPROM?\n\nSettings will persist after power cycle.",
    },
    "regconfig.save_eeprom_success": {
        Language.CHINESE: "参数已保存到 EEPROM",
        Language.ENGLISH: "Parameters saved to EEPROM",
    },
    "regconfig.save_eeprom_failed": {
        Language.CHINESE: "保存到 EEPROM 失败",
        Language.ENGLISH: "Failed to save to EEPROM",
    },

    # 任意寄存器读写
    "regconfig.arbitrary.title": {
        Language.CHINESE: "任意寄存器读写",
        Language.ENGLISH: "Arbitrary Register Access",
    },
    "regconfig.arbitrary.address": {
        Language.CHINESE: "地址:",
        Language.ENGLISH: "Address:",
    },
    "regconfig.arbitrary.type": {
        Language.CHINESE: "类型:",
        Language.ENGLISH: "Type:",
    },
    "regconfig.arbitrary.read": {
        Language.CHINESE: "读取",
        Language.ENGLISH: "Read",
    },
    "regconfig.arbitrary.value": {
        Language.CHINESE: "写入值:",
        Language.ENGLISH: "Value:",
    },
    "regconfig.arbitrary.value_hint": {
        Language.CHINESE: "十进制或0x开头十六进制",
        Language.ENGLISH: "Decimal or 0x hex",
    },
    "regconfig.arbitrary.write": {
        Language.CHINESE: "写入",
        Language.ENGLISH: "Write",
    },
    "regconfig.arbitrary.enter_addr": {
        Language.CHINESE: "请输入寄存器地址",
        Language.ENGLISH: "Please enter register address",
    },
    "regconfig.arbitrary.invalid_addr": {
        Language.CHINESE: "无效的地址格式",
        Language.ENGLISH: "Invalid address format",
    },
    "regconfig.arbitrary.confirm_write": {
        Language.CHINESE: "确认写入寄存器 {address} = {value}？",
        Language.ENGLISH: "Confirm write register {address} = {value}?",
    },
}


def get_language() -> Language:
    """获取当前语言"""
    return _current_language


def set_language(lang: Language, save: bool = True) -> None:
    """
    设置当前语言

    Args:
        lang: 目标语言
        save: 是否保存到配置文件（默认 True）
    """
    global _current_language
    if _current_language != lang:
        _current_language = lang

        # 保存到配置文件
        if save:
            _save_language(lang)

        # 通知所有注册的回调
        for callback in _language_callbacks:
            try:
                callback()
            except Exception:
                pass


def register_language_callback(callback: Callable[[], None]) -> None:
    """
    注册语言变更回调

    Args:
        callback: 语言变更时调用的函数
    """
    if callback not in _language_callbacks:
        _language_callbacks.append(callback)


def unregister_language_callback(callback: Callable[[], None]) -> None:
    """
    注销语言变更回调

    Args:
        callback: 要注销的回调函数
    """
    if callback in _language_callbacks:
        _language_callbacks.remove(callback)


def tr(key: str, **kwargs) -> str:
    """
    翻译函数

    Args:
        key: 翻译键
        **kwargs: 格式化参数

    Returns:
        翻译后的文本
    """
    if key in TRANSLATIONS:
        text = TRANSLATIONS[key].get(_current_language, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text
    return key


# 便捷函数
def is_chinese() -> bool:
    """是否为中文"""
    return _current_language == Language.CHINESE


def is_english() -> bool:
    """是否为英文"""
    return _current_language == Language.ENGLISH
