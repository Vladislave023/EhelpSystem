APP_STYLESHEET = """
QWidget {
    color: #1d2426;
    font-family: "Trebuchet MS";
    font-size: 12pt;
    background: transparent;
}

QMainWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f3ecdf,
        stop: 0.5 #ede5d6,
        stop: 1 #e6dccd
    );
}

QLabel {
    background: transparent;
}

QFrame#ShellCard, QFrame#PageCard, QFrame#SidebarCard, QFrame#SectionCard {
    border-radius: 24px;
}

QFrame#ShellCard {
    background: rgba(252, 248, 240, 0.92);
    border: 1px solid #d7c8b2;
}

QFrame#SidebarCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #243842,
        stop: 1 #1b2b33
    );
    border: 1px solid #304752;
}

QFrame#PageCard {
    background: #fbf7ef;
    border: 1px solid #d8ccb8;
}

QFrame#SectionCard {
    background: #fffdf8;
    border: 1px solid #e2d8c7;
}

QLabel#WindowTitle {
    font-size: 24pt;
    font-weight: 600;
    color: #162126;
}

QLabel#PageTitle {
    font-size: 21pt;
    font-weight: 600;
    color: #162126;
}

QLabel#SectionTitle {
    font-size: 14pt;
    font-weight: 600;
    color: #213138;
}

QFrame#SidebarCard QLabel#SectionTitle {
    color: #f7efe2;
    font-size: 17pt;
}

QLabel#MutedText {
    color: #71685c;
}

QLabel#ResultValue {
    color: #1d2426;
    font-size: 12.5pt;
    font-weight: 600;
}

QLabel#SidebarNote {
    color: #c8d5d8;
    font-size: 10.5pt;
    line-height: 1.3em;
}

QLabel#SidebarGroup {
    color: #d8b07d;
    font-size: 10pt;
    font-weight: 600;
    padding-top: 8px;
}

QLabel#StatusPill {
    background: #f4e0d1;
    color: #9a4d1f;
    border: 1px solid #dfbb9f;
    border-radius: 14px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton {
    background: #f0e6d8;
    border: 1px solid #d8c7b1;
    border-radius: 14px;
    padding: 11px 18px;
    font-weight: 600;
}

QPushButton:hover {
    background: #eadbc7;
}

QPushButton#PrimaryButton {
    background: #cb6f3c;
    color: #fffaf4;
    border: 1px solid #ab5a2f;
}

QPushButton#PrimaryButton:hover {
    background: #b96333;
}

QPushButton#DangerButton {
    background: #f6e5df;
    color: #923f2d;
    border: 1px solid #e1b8ac;
}

QPushButton#NavButton {
    text-align: left;
    padding: 15px 16px;
    border-radius: 16px;
    border: 1px solid transparent;
    background: rgba(255, 255, 255, 0.02);
    color: #eff5f2;
    font-size: 13pt;
}

QPushButton#NavButton:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(238, 245, 242, 0.12);
}

QPushButton#NavButton:checked {
    background: #d8b07d;
    color: #1f2b31;
    border-color: #d8b07d;
}

QLineEdit, QComboBox {
    background: #fffdf8;
    border: 1px solid #d5c8b5;
    border-radius: 14px;
    padding: 11px 13px;
    selection-background-color: #cb6f3c;
    selection-color: #fffaf4;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #cb6f3c;
}

QComboBox {
    padding-right: 40px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 34px;
    border: none;
    border-left: 1px solid #d5c8b5;
    border-top-right-radius: 14px;
    border-bottom-right-radius: 14px;
    background: #f7f1e7;
}

QListWidget {
    background: #fffdf8;
    border: 1px solid #d9ceb9;
    border-radius: 18px;
    padding: 8px;
    outline: none;
}

QListWidget::item {
    border-radius: 12px;
    padding: 10px 12px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: #f2dec9;
    color: #1d2426;
}

QSplitter::handle {
    background: transparent;
}

QTableWidget {
    background: #fffdf8;
    border: 1px solid #d9ceb9;
    border-radius: 18px;
    gridline-color: #ece2d2;
    selection-background-color: #f2dec9;
    selection-color: #1d2426;
    alternate-background-color: #faf5ec;
}

QHeaderView::section {
    background: #efe5d3;
    border: none;
    border-right: 1px solid #ded2be;
    border-bottom: 1px solid #ded2be;
    padding: 13px 10px;
    font-weight: 600;
    color: #25343b;
}

QTableCornerButton::section {
    background: #efe5d3;
    border: none;
    border-right: 1px solid #ded2be;
    border-bottom: 1px solid #ded2be;
}

QScrollBar:vertical {
    width: 12px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #cdbfa8;
    border-radius: 6px;
    min-height: 32px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox {
    background: #fffaf2;
}

QMessageBox QLabel {
    color: #1d2426;
    background: transparent;
    min-width: 320px;
}

QMessageBox QPushButton {
    min-width: 88px;
}
"""
