#!/usr/bin/env python3
"""
NiMotion 伺服电机控制系统

应用程序主入口。
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow


def setup_logging() -> None:
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    """主函数"""
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("启动 NiMotion 伺服电机控制系统")

    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("NiMotion Servo")  # 英文名称避免任务栏乱码
    app.setOrganizationName("NiMotion")
    app.setOrganizationDomain("nimotion.com")

    # 设置默认字体 (增大字体以提高可读性)
    font = QFont("Microsoft YaHei", 12)
    app.setFont(font)

    # 设置应用图标
    icon_path = Path(__file__).parent / "resources" / "motor_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        logger.info(f"已加载应用图标: {icon_path}")
    else:
        logger.warning(f"图标文件不存在: {icon_path}")

    # 创建主窗口
    window = MainWindow()
    window.show()

    logger.info("应用程序已启动")

    # 运行事件循环
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
