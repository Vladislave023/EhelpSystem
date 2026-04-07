from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.facade import ExpertSystemFacade
from ehelps_ui.pages.features_page import FeaturesPage
from ehelps_ui.pages.placeholders import PlaceholderPage
from ehelps_ui.widgets.sidebar import Sidebar, SidebarItem


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.facade = ExpertSystemFacade.default()
        self.setWindowTitle("EhelpS")
        self.resize(1320, 860)
        self.setMinimumSize(1080, 720)

        central = QWidget()
        self.setCentralWidget(central)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(18, 18, 18, 18)
        outer_layout.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("ShellCard")
        outer_layout.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(18, 18, 18, 18)
        shell_layout.setSpacing(18)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        title = QLabel("Экспертная система по первой помощи")
        title.setObjectName("WindowTitle")
        title_block.addWidget(title)

        subtitle = QLabel(
            "Диагностика бытовых травм и ведение базы знаний в одном приложении."
        )
        subtitle.setObjectName("MutedText")
        title_block.addWidget(subtitle)

        top_bar.addLayout(title_block, 1)

        status = QLabel("JSON-хранилище подключено")
        status.setObjectName("StatusPill")
        top_bar.addWidget(status, 0, Qt.AlignRight | Qt.AlignVCenter)
        shell_layout.addLayout(top_bar)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        shell_layout.addLayout(body_layout, 1)

        self.sidebar = Sidebar(
            [
                SidebarItem("patient", "Пациенты"),
                SidebarItem("features", "Признаки"),
                SidebarItem("diagnoses", "Диагнозы"),
                SidebarItem("actions", "Действия"),
                SidebarItem("protocols", "Протоколы помощи"),
                SidebarItem("treatments", "Названия лечения"),
            ]
        )
        self.sidebar.setFixedWidth(280)
        self.sidebar.page_selected.connect(self.set_current_page)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)

        self.page_indexes: dict[str, int] = {}
        self._add_page(
            "patient",
            PlaceholderPage(
                "Пациенты",
                "Здесь будет форма ввода признаков состояния пациента и запуск диагностики.",
            ),
        )
        self._add_page("features", FeaturesPage(self.facade.editor))
        self._add_page(
            "diagnoses",
            PlaceholderPage(
                "Диагнозы",
                "Следующим шагом сюда подключим таблицу диагнозов, признаки диагноза и выбор лечения.",
            ),
        )
        self._add_page(
            "actions",
            PlaceholderPage(
                "Действия",
                "Здесь появится редактор элементарных действий первой помощи.",
            ),
        )
        self._add_page(
            "protocols",
            PlaceholderPage(
                "Протоколы помощи",
                "Здесь появится сборка действий в протоколы для выбранного лечения.",
            ),
        )
        self._add_page(
            "treatments",
            PlaceholderPage(
                "Названия лечения",
                "Здесь будет список названий лечения и их описаний.",
            ),
        )

        self.set_current_page("features")

    def set_current_page(self, key: str) -> None:
        self.stack.setCurrentIndex(self.page_indexes[key])
        self.sidebar.set_current(key)

    def _add_page(self, key: str, widget: QWidget) -> None:
        self.page_indexes[key] = self.stack.addWidget(widget)
