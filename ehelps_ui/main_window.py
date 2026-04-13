from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ehelps_backend.application.facade import ExpertSystemFacade
from ehelps_ui.pages.actions_page import ActionsPage
from ehelps_ui.pages.diagnostics_page import DiagnosticsPage
from ehelps_ui.pages.diagnoses_page import DiagnosesPage
from ehelps_ui.pages.features_page import FeaturesPage
from ehelps_ui.pages.protocols_page import ProtocolsPage
from ehelps_ui.pages.treatments_page import TreatmentsPage
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

        completeness_button = QPushButton("Проверка полноты знаний")
        completeness_button.clicked.connect(self.check_knowledge_integrity)
        top_bar.addWidget(completeness_button)

        status = QLabel("JSON-хранилище подключено")
        status.setObjectName("StatusPill")
        top_bar.addWidget(status, 0, Qt.AlignRight | Qt.AlignVCenter)
        shell_layout.addLayout(top_bar)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        shell_layout.addLayout(body_layout, 1)

        self.sidebar = Sidebar(
            [
                SidebarItem("diagnostics", "Диагностика"),
                SidebarItem("features", "Признаки"),
                SidebarItem("diagnoses", "Диагнозы"),
                SidebarItem("actions", "Действия"),
                SidebarItem("treatments", "Названия лечения"),
                SidebarItem("protocols", "Протоколы помощи"),
            ]
        )
        self.sidebar.setFixedWidth(280)
        self.sidebar.page_selected.connect(self.set_current_page)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)

        self.page_indexes: dict[str, int] = {}
        self._add_page(
            "diagnostics",
            DiagnosticsPage(self.facade),
        )
        self._add_page("features", FeaturesPage(self.facade.editor))
        self._add_page(
            "diagnoses",
            DiagnosesPage(self.facade.editor),
        )
        self._add_page(
            "actions", ActionsPage(self.facade.editor)
        )
        self._add_page("treatments", TreatmentsPage(self.facade.editor))
        self._add_page(
            "protocols",
            ProtocolsPage(self.facade.editor),
        )

        self.set_current_page("features")

    def set_current_page(self, key: str) -> None:
        self.stack.setCurrentIndex(self.page_indexes[key])
        self.sidebar.set_current(key)

    def _add_page(self, key: str, widget: QWidget) -> None:
        self.page_indexes[key] = self.stack.addWidget(widget)

    def check_knowledge_integrity(self) -> None:
        try:
            self.facade.editor.reload()
            self.facade.editor.validate_integrity()
            stats = self.facade.editor.get_statistics()
        except Exception as error:
            QMessageBox.critical(self, "Проверка полноты знаний", str(error))
            return

        message = (
            "База знаний корректна и не содержит нарушений целостности.\n\n"
            f"Признаков: {stats['features']}\n"
            f"Диагнозов: {stats['diagnoses']}\n"
            f"Действий: {stats['actions']}\n"
            f"Названий лечения: {stats['treatments']}\n"
            f"Протоколов: {stats['protocols']}"
        )
        QMessageBox.information(self, "Проверка полноты знаний", message)
