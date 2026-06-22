"""
硬件自检面板

提供标准化的硬件连接检测程序，用于验证：
  1. 通信连接 —— 各轴 Modbus 从站是否在线、可读写
  2. 上下限位开关 —— 自动低速运动撞限位，验证开关触发、方向极性、驱动器是否停机

自动运动测试在后台线程执行，面板提供醒目的急停按钮。
"""

import logging
import time
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from servo_service import AxisName, ServoService

from ..i18n import tr

logger = logging.getLogger(__name__)

# 驱动器限位开关故障码 (撞限位时驱动器暂停并锁轴)
LIMIT_FAULT_CODE = 0x8614

# DI 功能编号
DI_FUNC_POSITIVE_LIMIT = 14
DI_FUNC_NEGATIVE_LIMIT = 15


class HardwareTestWorker(QThread):
    """硬件测试后台工作线程"""

    log_msg = pyqtSignal(str)
    # 通信结果: 行号, 是否在线, 详情
    comm_row = pyqtSignal(int, bool, str)
    # 限位结果: which('upper'/'lower'), result('pass'/'fail'/'warn'), detail
    limit_result = pyqtSignal(str, str, str)
    finished_all = pyqtSignal(bool, str)

    def __init__(
        self,
        service: ServoService,
        mode: str,
        axis: Optional[AxisName] = None,
        speed: float = 5.0,
        axes_list: Optional[List[AxisName]] = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._mode = mode  # 'comm' 或 'limit'
        self._axis = axis
        self._speed = speed
        self._axes_list = axes_list or []
        self._stop_flag = False

    def request_stop(self) -> None:
        """请求急停 (线程安全，由工作线程在轮询点执行实际停机)"""
        self._stop_flag = True

    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            if self._mode == "comm":
                self._run_comm()
            else:
                self._run_limit()
            self.finished_all.emit(not self._stop_flag, "")
        except Exception as e:  # noqa: BLE001
            logger.exception("硬件测试异常")
            self.finished_all.emit(False, str(e))

    # ------------------------------------------------------------------
    def _run_comm(self) -> None:
        """通信连接检测: 逐轴读取状态字"""
        for i, axis in enumerate(self._axes_list):
            if self._stop_flag:
                break
            try:
                motor = self._service.get_motor(axis)
                t0 = time.monotonic()
                sw = motor.read_status_word()
                dt = (time.monotonic() - t0) * 1000
                self.log_msg.emit(
                    f"{axis.value}: 状态字=0x{sw:04X} (耗时 {dt:.0f}ms) ✓"
                )
                self.comm_row.emit(i, True, f"0x{sw:04X}  {dt:.0f}ms")
            except Exception as e:  # noqa: BLE001
                self.log_msg.emit(f"{axis.value}: 无响应 / 离线 ({e})")
                self.comm_row.emit(i, False, str(e)[:48])

    # ------------------------------------------------------------------
    def _run_limit(self) -> None:
        """上下限位自动测试"""
        service = self._service
        axis = self._axis
        config = service.get_axis_config(axis)

        # 从配置映射 DI: 哪个 DI 是正/负限位
        di_map: Dict[str, int] = {}
        for di_num, func in (
            (1, config.di1_function),
            (2, config.di2_function),
            (3, config.di3_function),
        ):
            if func == DI_FUNC_POSITIVE_LIMIT:
                di_map["pos"] = di_num
            elif func == DI_FUNC_NEGATIVE_LIMIT:
                di_map["neg"] = di_num

        try:
            # 先测上限位 (正方向)
            if "pos" in di_map:
                self._test_one_limit("upper", +1, di_map["pos"], config)
            else:
                self.limit_result.emit("upper", "warn", "未配置正限位 DI，跳过")
            if self._stop_flag:
                return
            # 再测下限位 (负方向)
            if "neg" in di_map:
                self._test_one_limit("lower", -1, di_map["neg"], config)
            else:
                self.limit_result.emit("lower", "warn", "未配置负限位 DI，跳过")
        finally:
            self._safe_release(config, di_map)

    # ------------------------------------------------------------------
    def _test_one_limit(self, which: str, direction: int, di_num: int, config) -> None:
        """测试单个限位"""
        service = self._service
        axis = self._axis
        motor = service.get_motor(axis)
        bit = 1 << (di_num - 1)
        name = "上限位" if which == "upper" else "下限位"
        dir_sym = "+" if direction > 0 else "-"

        self.log_msg.emit(f"===== 测试{name} (DI{di_num}, 方向{dir_sym}) =====")

        # 清故障
        self._try(lambda: service.fault_reset(axis))
        time.sleep(0.1)

        # 若已在该限位上，先反向退出
        di = motor.read_di_physical_state()
        if not (di & bit):
            self.log_msg.emit(f"{name}当前已触发，先反向退出...")
            self._jog_until(
                -direction, lambda d: bool(d & bit), config, extra_mm=2.0
            )
            self._try(lambda: service.fault_reset(axis))
            time.sleep(0.1)

        start_pos = config.pulses_to_mm(motor.read_position())
        service.enable(axis)
        self.log_msg.emit(f"使能，以 {self._speed} mm/s 向{name}运动 (起点 {start_pos:.2f}mm)")
        service.jog(direction * self._speed, axis)

        triggered = False
        driver_faulted = False
        wrong_dir = False
        trig_pos: Optional[float] = None
        max_travel = config.stroke + 5.0  # 行程 + 余量
        t0 = time.monotonic()

        # 阶段一: 朝限位运动, 等待限位触发 (不主动停机)
        while not self._stop_flag:
            if time.monotonic() - t0 > 30.0:
                self.log_msg.emit("⚠ 测试超时 (30s)")
                break
            try:
                di = motor.read_di_physical_state()
                pos = config.pulses_to_mm(motor.read_position())
                err = motor.read_error_code()
            except Exception as e:  # noqa: BLE001
                self.log_msg.emit(f"读取异常: {e}")
                break

            delta = pos - start_pos
            # 方向校验: 运动方向应与预期一致
            if abs(delta) > 1.0 and delta * direction < 0:
                wrong_dir = True
                self.log_msg.emit(f"⚠ 运动方向与预期相反 (Δ={delta:.1f}mm)，中止！")
                break
            # 行程保护
            if abs(delta) > max_travel:
                self.log_msg.emit(f"⚠ 已移动 {delta:.1f}mm 仍未触发限位，中止！")
                break
            # 驱动器限位故障 (若配置成进故障态)
            if err == LIMIT_FAULT_CODE:
                driver_faulted = True
                triggered = not (di & bit)
                trig_pos = pos
                self.log_msg.emit(f"驱动器报限位故障 0x{err:04X}，位置={pos:.2f}mm")
                break
            # 物理限位触发 (低电平有效)
            if not (di & bit):
                triggered = True
                trig_pos = pos
                self.log_msg.emit(f"{name}开关触发，位置={pos:.2f}mm")
                break
            time.sleep(0.03)

        # 阶段二: 观察驱动器是否自动停机 (响应码3=急停锁轴, 不报故障)
        # 限位触发后先不主动停, 留窗口看电机是否靠驱动器自己减速到 0,
        # 越过触发点 2mm 安全距离则判定驱动器未停并立即接管停机。
        auto_stopped = False
        SAFE_MARGIN_MM = 2.0
        if triggered and not wrong_dir and not self._stop_flag:
            obs_t0 = time.monotonic()
            while time.monotonic() - obs_t0 < 1.2 and not self._stop_flag:
                try:
                    pos2 = config.pulses_to_mm(motor.read_position())
                    vel2 = abs(config.velocity_pulses_to_mm(motor.read_velocity()))
                except Exception:  # noqa: BLE001
                    break
                if trig_pos is not None and abs(pos2 - trig_pos) > SAFE_MARGIN_MM:
                    self.log_msg.emit(
                        f"⚠ 越过限位 {abs(pos2 - trig_pos):.1f}mm 仍未停，驱动器未自停，接管停机！"
                    )
                    break
                if vel2 < 1.0:
                    auto_stopped = True
                    self.log_msg.emit(f"驱动器已自动停机，停止位置={pos2:.2f}mm，速度≈0")
                    break
                time.sleep(0.02)

        # 备份停机 (无论如何都停, 留安全状态)
        self._try(lambda: service.quick_stop(axis))
        time.sleep(0.3)

        # 判定
        if self._stop_flag:
            self.limit_result.emit(which, "fail", "用户急停，测试中断")
            return
        if wrong_dir:
            self.limit_result.emit(which, "fail", "运动方向与预期相反，极性/接线错误")
            return
        if not triggered:
            self.limit_result.emit(which, "fail", "运动到行程末端仍未检测到限位触发")
            return

        detail = f"触发位置 {trig_pos:.2f}mm; "
        if driver_faulted:
            detail += "驱动器报限位故障(0x8614)并停机锁轴"
            self.limit_result.emit(which, "pass", detail)
        elif auto_stopped:
            detail += "驱动器自动停机锁轴(响应码3，不报故障)"
            self.limit_result.emit(which, "pass", detail)
        else:
            detail += "驱动器未在限位处自动停机(由软件接管停机)"
            self.limit_result.emit(which, "warn", detail)

    # ------------------------------------------------------------------
    def _jog_until(
        self,
        direction: int,
        released: Callable[[int], bool],
        config,
        timeout: float = 8.0,
        extra_mm: float = 2.0,
    ) -> None:
        """朝 direction 方向点动，直到 released(di) 为真后再多走 extra_mm"""
        service = self._service
        axis = self._axis
        motor = service.get_motor(axis)
        self._try(lambda: service.fault_reset(axis))
        service.enable(axis)
        service.jog(direction * self._speed, axis)
        t0 = time.monotonic()
        released_pos: Optional[float] = None
        while not self._stop_flag and time.monotonic() - t0 < timeout:
            try:
                di = motor.read_di_physical_state()
                pos = config.pulses_to_mm(motor.read_position())
            except Exception:  # noqa: BLE001
                break
            if released(di):
                if released_pos is None:
                    released_pos = pos
                elif abs(pos - released_pos) >= extra_mm:
                    break
            time.sleep(0.03)
        self._try(lambda: service.quick_stop(axis))
        time.sleep(0.2)

    # ------------------------------------------------------------------
    def _safe_release(self, config, di_map: Dict[str, int]) -> None:
        """测试结束后将电机退出限位并停止、禁用，留在安全状态"""
        service = self._service
        axis = self._axis
        try:
            self._try(lambda: service.fault_reset(axis))
            time.sleep(0.1)
            motor = service.get_motor(axis)
            di = motor.read_di_physical_state()
            if "neg" in di_map and not (di & (1 << (di_map["neg"] - 1))):
                self.log_msg.emit("退出下限位...")
                self._jog_until(
                    +1, lambda d: bool(d & (1 << (di_map["neg"] - 1))), config, extra_mm=3.0
                )
            elif "pos" in di_map and not (di & (1 << (di_map["pos"] - 1))):
                self.log_msg.emit("退出上限位...")
                self._jog_until(
                    -1, lambda d: bool(d & (1 << (di_map["pos"] - 1))), config, extra_mm=3.0
                )
        except Exception as e:  # noqa: BLE001
            self.log_msg.emit(f"安全退出异常: {e}")
        finally:
            self._try(lambda: service.quick_stop(axis))
            self._try(lambda: service.disable(axis))
            self.log_msg.emit("电机已停止并禁用，测试结束。")

    @staticmethod
    def _try(fn: Callable[[], None]) -> None:
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass


# ======================================================================
class HardwareTestPanel(QWidget):
    """硬件自检面板"""

    # 通知主窗口暂停/恢复状态轮询定时器，避免串口冲突
    test_started = pyqtSignal()
    test_finished = pyqtSignal()

    _RESULT_STYLE = {
        "pending": "color: #888888;",
        "pass": "color: #28a745; font-weight: bold;",
        "fail": "color: #dc3545; font-weight: bold;",
        "warn": "color: #ff8c00; font-weight: bold;",
    }

    def __init__(self, service: ServoService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._service = service
        self._worker: Optional[HardwareTestWorker] = None
        self._comm_axes: List[AxisName] = []
        self._init_ui()

    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # 警告 + 急停
        top = QHBoxLayout()
        self._warn_label = QLabel(tr("hwtest.limit.warn"))
        self._warn_label.setWordWrap(True)
        self._warn_label.setStyleSheet("color: #ffc107;")
        top.addWidget(self._warn_label, 1)

        self._estop_btn = QPushButton(tr("hwtest.estop"))
        self._estop_btn.setProperty("class", "danger")
        self._estop_btn.setMinimumHeight(48)
        self._estop_btn.setMinimumWidth(120)
        self._estop_btn.setEnabled(False)
        self._estop_btn.clicked.connect(self._on_estop)
        top.addWidget(self._estop_btn)
        root.addLayout(top)

        # 1. 通信检测
        self._comm_group = QGroupBox(tr("hwtest.comm.title"))
        comm_layout = QVBoxLayout(self._comm_group)
        self._comm_btn = QPushButton(tr("hwtest.comm.run"))
        self._comm_btn.clicked.connect(self._on_run_comm)
        comm_layout.addWidget(self._comm_btn)

        self._comm_table = QTableWidget(0, 4)
        self._comm_table.setHorizontalHeaderLabels(
            [
                tr("hwtest.comm.col_axis"),
                tr("hwtest.comm.col_slave"),
                tr("hwtest.comm.col_result"),
                tr("hwtest.comm.col_detail"),
            ]
        )
        self._comm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._comm_table.verticalHeader().setVisible(False)
        self._comm_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._comm_table.setMaximumHeight(160)
        comm_layout.addWidget(self._comm_table)
        root.addWidget(self._comm_group)

        # 2. 限位测试
        self._limit_group = QGroupBox(tr("hwtest.limit.title"))
        limit_layout = QVBoxLayout(self._limit_group)

        form = QFormLayout()
        self._axis_combo = QComboBox()
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(1.0, 20.0)
        self._speed_spin.setValue(5.0)
        self._speed_spin.setSingleStep(1.0)
        self._speed_spin.setSuffix(" mm/s")
        self._axis_label = QLabel(tr("hwtest.limit.axis"))
        self._speed_label = QLabel(tr("hwtest.limit.speed"))
        form.addRow(self._axis_label, self._axis_combo)
        form.addRow(self._speed_label, self._speed_spin)
        limit_layout.addLayout(form)

        self._limit_btn = QPushButton(tr("hwtest.limit.run"))
        self._limit_btn.setProperty("class", "warning")
        self._limit_btn.clicked.connect(self._on_run_limit)
        limit_layout.addWidget(self._limit_btn)

        # 结果行
        self._limit_name_labels: Dict[str, QLabel] = {}
        self._limit_result_labels: Dict[str, QLabel] = {}
        for which, key in (("upper", "hwtest.limit.upper"), ("lower", "hwtest.limit.lower")):
            row = QHBoxLayout()
            name = QLabel(tr(key))
            name.setMinimumWidth(160)
            result = QLabel(tr("hwtest.result.pending"))
            result.setStyleSheet(self._RESULT_STYLE["pending"])
            result.setWordWrap(True)
            row.addWidget(name)
            row.addWidget(result, 1)
            limit_layout.addLayout(row)
            self._limit_name_labels[which] = name
            self._limit_result_labels[which] = result

        root.addWidget(self._limit_group)

        # 日志
        self._log_group = QGroupBox(tr("hwtest.log.title"))
        log_layout = QVBoxLayout(self._log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        log_layout.addWidget(self._log)
        root.addWidget(self._log_group, 1)

        self._refresh_axis_combo()

    # ------------------------------------------------------------------
    def _configured_axes(self) -> List[AxisName]:
        """返回已配置的轴 (按固定顺序)"""
        axes = []
        for axis in (AxisName.Z4, AxisName.Y2, AxisName.Z3, AxisName.X):
            try:
                self._service.get_axis_config(axis)
                axes.append(axis)
            except Exception:  # noqa: BLE001
                pass
        return axes

    def _refresh_axis_combo(self) -> None:
        """填充可测试限位的轴 (至少配置了一个限位 DI)"""
        self._axis_combo.clear()
        for axis in self._configured_axes():
            cfg = self._service.get_axis_config(axis)
            funcs = (cfg.di1_function, cfg.di2_function, cfg.di3_function)
            if DI_FUNC_POSITIVE_LIMIT in funcs or DI_FUNC_NEGATIVE_LIMIT in funcs:
                self._axis_combo.addItem(axis.value, axis)
        # 默认选中当前轴
        try:
            cur = self._service.current_axis
            idx = self._axis_combo.findData(cur)
            if idx >= 0:
                self._axis_combo.setCurrentIndex(idx)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    def _append_log(self, msg: str) -> None:
        self._log.append(msg)

    def _set_running(self, running: bool) -> None:
        self._comm_btn.setEnabled(not running)
        self._limit_btn.setEnabled(not running)
        self._axis_combo.setEnabled(not running)
        self._speed_spin.setEnabled(not running)
        self._estop_btn.setEnabled(running)

    def _start_worker(self, worker: HardwareTestWorker) -> None:
        self._worker = worker
        worker.log_msg.connect(self._append_log)
        worker.finished_all.connect(self._on_finished)
        self._set_running(True)
        self.test_started.emit()
        worker.start()

    # ------------------------------------------------------------------
    def _on_run_comm(self) -> None:
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("hwtest.title"), tr("hwtest.msg.not_connected"))
            return
        self._comm_axes = self._configured_axes()
        self._comm_table.setRowCount(len(self._comm_axes))
        for i, axis in enumerate(self._comm_axes):
            cfg = self._service.get_axis_config(axis)
            self._comm_table.setItem(i, 0, QTableWidgetItem(axis.value))
            self._comm_table.setItem(i, 1, QTableWidgetItem(str(cfg.slave_id)))
            self._comm_table.setItem(i, 2, QTableWidgetItem("..."))
            self._comm_table.setItem(i, 3, QTableWidgetItem(""))

        worker = HardwareTestWorker(self._service, mode="comm", axes_list=self._comm_axes)
        worker.comm_row.connect(self._on_comm_row)
        self._append_log("--- 通信连接检测 ---")
        self._start_worker(worker)

    def _on_comm_row(self, row: int, online: bool, detail: str) -> None:
        result = tr("hwtest.comm.online") if online else tr("hwtest.comm.offline")
        item = QTableWidgetItem(result)
        item.setForeground(Qt.green if online else Qt.red)
        self._comm_table.setItem(row, 2, item)
        self._comm_table.setItem(row, 3, QTableWidgetItem(detail))

    # ------------------------------------------------------------------
    def _on_run_limit(self) -> None:
        if not self._service.is_connected:
            QMessageBox.warning(self, tr("hwtest.title"), tr("hwtest.msg.not_connected"))
            return
        axis = self._axis_combo.currentData()
        if axis is None:
            return
        reply = QMessageBox.question(
            self,
            tr("hwtest.title"),
            tr("hwtest.msg.confirm_limit", axis=axis.value),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # 重置结果灯
        for which in ("upper", "lower"):
            lbl = self._limit_result_labels[which]
            lbl.setText(tr("hwtest.result.pending"))
            lbl.setStyleSheet(self._RESULT_STYLE["pending"])

        worker = HardwareTestWorker(
            self._service,
            mode="limit",
            axis=axis,
            speed=self._speed_spin.value(),
        )
        worker.limit_result.connect(self._on_limit_result)
        self._append_log(f"--- 限位自动测试: {axis.value} 轴 ---")
        self._start_worker(worker)

    def _on_limit_result(self, which: str, result: str, detail: str) -> None:
        lbl = self._limit_result_labels.get(which)
        if lbl is None:
            return
        text_map = {
            "pass": tr("hwtest.result.pass"),
            "fail": tr("hwtest.result.fail"),
            "warn": tr("hwtest.result.warn"),
        }
        lbl.setText(f"{text_map.get(result, result)} — {detail}")
        lbl.setStyleSheet(self._RESULT_STYLE.get(result, self._RESULT_STYLE["pending"]))

    # ------------------------------------------------------------------
    def _on_estop(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._append_log("⚠⚠ 用户请求急停 ⚠⚠")
            self._estop_btn.setEnabled(False)

    def _on_finished(self, success: bool, message: str) -> None:
        self._set_running(False)
        if message:
            self._append_log(f"测试异常结束: {message}")
        elif not success:
            self._append_log("测试被中断。")
        else:
            self._append_log("测试完成。")
        self.test_finished.emit()

    # ------------------------------------------------------------------
    def refresh_texts(self) -> None:
        """刷新界面文本 (语言切换时调用)"""
        self._warn_label.setText(tr("hwtest.limit.warn"))
        self._estop_btn.setText(tr("hwtest.estop"))
        self._comm_group.setTitle(tr("hwtest.comm.title"))
        self._comm_btn.setText(tr("hwtest.comm.run"))
        self._comm_table.setHorizontalHeaderLabels(
            [
                tr("hwtest.comm.col_axis"),
                tr("hwtest.comm.col_slave"),
                tr("hwtest.comm.col_result"),
                tr("hwtest.comm.col_detail"),
            ]
        )
        self._limit_group.setTitle(tr("hwtest.limit.title"))
        self._axis_label.setText(tr("hwtest.limit.axis"))
        self._speed_label.setText(tr("hwtest.limit.speed"))
        self._limit_btn.setText(tr("hwtest.limit.run"))
        self._limit_name_labels["upper"].setText(tr("hwtest.limit.upper"))
        self._limit_name_labels["lower"].setText(tr("hwtest.limit.lower"))
        self._log_group.setTitle(tr("hwtest.log.title"))
