#!/usr/bin/env python3
"""DMS Mango Workstation Settings - Qt companion settings UI."""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

HOME = Path.home()
PROJECT = HOME / "dms-kde-workstation"
MANGO_CONFIG = HOME / ".config/mango/config.conf"
BACKUP_ROOT = HOME / ".local/state/dms-kde-workstation/backups"
HEALTH_SCRIPT = PROJECT / "scripts/dms-workstation-health"
APPLY_BASELINE_SCRIPT = PROJECT / "scripts/apply-mango-baseline"
STARTUP_JSON = HOME / ".config/dms-kde-workstation/startup.json"
QT_ENV_FILE = HOME / ".config/environment.d/90-dms-kde-qt.conf"
PORTAL_OVERRIDE = HOME / ".config/systemd/user/xdg-desktop-portal.service"
PORTAL_CONFIG = HOME / ".config/xdg-desktop-portal/mango-portals.conf"
SETTINGS_BIN = HOME / ".local/bin/dms-mango-settings"
SETTINGS_AUTOSTART = HOME / ".config/autostart/dms-mango-settings.desktop"
POST_STARTUP_HELPER = HOME / ".local/bin/dms-mango-post-startup"
FIRST_LOGIN_READINESS_SCRIPT = PROJECT / "scripts/test-first-mango-readiness"
FRESH_VALIDATION_CHECKLIST = PROJECT / "docs/fresh-machine-validation-checklist.md"
FRESH_VALIDATION_RESULTS_TEMPLATE = PROJECT / "docs/fresh-machine-validation-results-template.md"
MANGO_SESSION_FILE = Path("/usr/share/wayland-sessions/mango.desktop")
CONSOLIDATE_SCRIPT = HOME / ".local/lib/dms-kde-workstation/sddm-consolidate-autologin.py"
POLKIT_POLICY = Path("/usr/share/polkit-1/actions/io.dms-kde-workstation.sddm-autologin.policy")

PORTAL_PACKAGES = [
    ("xdg-desktop-portal", "Core portal framework"),
    ("xdg-desktop-portal-wlr", "Wayland portal backend"),
    ("xdg-desktop-portal-gtk", "GTK portal backend"),
    ("xdg-desktop-portal-kde", "KDE portal backend"),
]

ENV_REQUIRED_VARS = {
    "QT_QPA_PLATFORM": "wayland",
    "QT_QPA_PLATFORMTHEME": "qt6ct",
    "QT_QPA_PLATFORMTHEME_QT6": "qt6ct",
    "ELECTRON_OZONE_PLATFORM_HINT": "auto",
}


def rgb_to_hex(value: str, fallback: str) -> str:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 3:
        return fallback
    with contextlib.suppress(ValueError):
        return "#" + "".join(f"{max(0, min(255, int(p))):02x}" for p in parts)
    return fallback


def read_kde_color_scheme() -> dict[str, dict[str, str]]:
    candidates = [
        HOME / ".local/share/color-schemes/DankMatugen.colors",
        HOME / ".config/qt6ct/colors/matugen.conf",
        HOME / ".config/qt5ct/colors/matugen.conf",
    ]
    path = next((p for p in candidates if p.exists()), None)
    colors: dict[str, dict[str, str]] = {}
    if not path:
        return colors
    section = ""
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            colors.setdefault(section, {})
            continue
        if "=" in line and section:
            key, value = line.split("=", 1)
            colors.setdefault(section, {})[key.strip()] = value.strip()
    return colors


def palette_color(
    colors: dict[str, dict[str, str]], section: str, key: str, fallback: str
) -> str:
    return rgb_to_hex(colors.get(section, {}).get(key, ""), fallback)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return (0, 0, 0)
    with contextlib.suppress(ValueError):
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    return (0, 0, 0)


def mix(a: str, b: str, amount: float) -> str:
    ar, ag, ab = hex_to_rgb(a)
    br, bg, bb = hex_to_rgb(b)
    amount = max(0.0, min(1.0, amount))
    return f"#{round(ar * (1 - amount) + br * amount):02x}{round(ag * (1 - amount) + bg * amount):02x}{round(ab * (1 - amount) + bb * amount):02x}"


_KDE_COLORS = read_kde_color_scheme()
ACCENT = palette_color(_KDE_COLORS, "Colors:Selection", "BackgroundNormal", "#1042ff")
ACCENT_TEXT = palette_color(
    _KDE_COLORS, "Colors:Selection", "ForegroundNormal", "#e6e0ef"
)
BG = palette_color(_KDE_COLORS, "Colors:Window", "BackgroundNormal", "#14121c")
SURFACE = palette_color(_KDE_COLORS, "Colors:View", "BackgroundAlternate", "#1d1a24")
SURFACE_2 = palette_color(_KDE_COLORS, "Colors:Button", "BackgroundNormal", "#14121c")
TEXT = palette_color(_KDE_COLORS, "Colors:Window", "ForegroundNormal", "#e6e0ef")
MUTED = palette_color(_KDE_COLORS, "Colors:Window", "ForegroundInactive", "#c9c3d1")
SIDEBAR = palette_color(_KDE_COLORS, "Colors:Complementary", "BackgroundNormal", BG)
FIELD = palette_color(_KDE_COLORS, "Colors:View", "BackgroundNormal", mix(BG, SURFACE, 0.45))
BUTTON = palette_color(_KDE_COLORS, "Colors:Button", "BackgroundNormal", SURFACE_2)
BORDER = mix(TEXT, SURFACE, 0.82)
BUTTON_HOVER = mix(TEXT, BUTTON, 0.88)
WARNING = palette_color(_KDE_COLORS, "Colors:Window", "ForegroundNeutral", MUTED)

LAYOUTS = {
    "Scroller": "scroller",
    "Vertical Scroller": "vertical_scroller",
    "Monocle": "monocle",
    "Tile": "tile",
    "Vertical Tile": "vertical_tile",
    "Dwindle": "dwindle",
    "Grid": "grid",
    "Deck": "deck",
    "Center Tile": "center_tile",
}
LAYOUT_SHORT = {
    "scroller": "S",
    "vertical_scroller": "VS",
    "monocle": "M",
    "tile": "T",
    "vertical_tile": "VT",
    "dwindle": "DW",
    "grid": "G",
    "deck": "D",
    "center_tile": "CT",
}

SERVICES = [
    ("Dropbox", "dropbox.service"),
    ("Sunshine", "app-dev.lizardbyte.app.Sunshine.service"),
    ("RustDesk", "rustdesk.service"),
    ("Vicinae", "vicinae.service"),
    ("Portal", "xdg-desktop-portal.service"),
    ("Portal WLR", "xdg-desktop-portal-wlr.service"),
    ("Portal GTK", "xdg-desktop-portal-gtk.service"),
    ("PipeWire", "pipewire.service"),
    ("WirePlumber", "wireplumber.service"),
]


def run_cmd(args: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except Exception as exc:  # UI should display failures instead of hiding them.
        return 1, str(exc)


class MangoConfig:
    def __init__(self, path: Path = MANGO_CONFIG):
        self.path = path
        self.text = ""
        self.reload()

    def reload(self) -> None:
        self.text = self.path.read_text() if self.path.exists() else ""

    def backup(self) -> Path | None:
        if not self.path.exists():
            return None
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUP_ROOT / stamp / ".config/mango/config.conf"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, target)
        return target

    def save(self) -> Path | None:
        backup = self.backup()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.text)
        return backup

    def get(self, key: str, default: str = "") -> str:
        match = re.search(
            rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", self.text, re.MULTILINE
        )
        return match.group(1) if match else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        return self.get(key, "1" if default else "0") == "1"

    def set(self, key: str, value: str | int | float | bool) -> None:
        if isinstance(value, bool):
            value = "1" if value else "0"
        line = f"{key}={value}"
        pattern = rf"^\s*{re.escape(key)}\s*=.*$"
        if re.search(pattern, self.text, re.MULTILINE):
            self.text = re.sub(pattern, line, self.text, count=1, flags=re.MULTILINE)
        else:
            self.text = self.text.rstrip() + "\n" + line + "\n"

    def has_line(self, line: str) -> bool:
        return line in self.text.splitlines()

    def ensure_line(self, line: str, after_marker: str | None = None) -> None:
        if self.has_line(line):
            return
        if after_marker and after_marker in self.text:
            idx = self.text.find(after_marker)
            end = self.text.find("\n", idx)
            self.text = self.text[: end + 1] + line + "\n" + self.text[end + 1 :]
        else:
            self.text = self.text.rstrip() + "\n" + line + "\n"

    def remove_matching(self, pattern: str) -> None:
        self.text = (
            "\n".join(
                line for line in self.text.splitlines() if not re.search(pattern, line)
            )
            + "\n"
        )

    def exec_once_commands(self) -> list[str]:
        return [
            line.strip().split("=", 1)[1]
            for line in self.text.splitlines()
            if line.strip().startswith("exec-once=")
        ]

    def add_exec_once(self, command: str) -> None:
        if command.strip():
            self.ensure_line(
                f"exec-once={command.strip()}",
                "# DMS KDE Workstation autostart parity with niri/KDE",
            )

    def remove_exec_once(self, command: str) -> None:
        self.remove_matching(rf"^\s*exec-once={re.escape(command.strip())}\s*$")

    def set_default_layout(self, layout: str) -> None:
        for tag in range(1, 10):
            pattern = rf"^\s*tagrule=id:{tag},layout_name:.*$"
            line = f"tagrule=id:{tag},layout_name:{layout}"
            if re.search(pattern, self.text, re.MULTILINE):
                self.text = re.sub(
                    pattern, line, self.text, count=1, flags=re.MULTILINE
                )
            else:
                self.text = self.text.rstrip() + "\n" + line
        self.text = self.text.rstrip() + "\n"


class BezierCurvePreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.values = [0.46, 1.0, 0.29, 1.0]
        self.setMinimumSize(180, 120)

    def set_values(self, values: list[float]) -> None:
        self.values = values
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(14, 10, -14, -14)
        painter.fillRect(self.rect(), QColor(FIELD))
        grid_pen = QPen(QColor(BORDER), 1)
        painter.setPen(grid_pen)
        for i in range(5):
            x = rect.left() + rect.width() * i / 4
            y = rect.top() + rect.height() * i / 4
            painter.drawLine(int(x), rect.top(), int(x), rect.bottom())
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        def point(x: float, y: float) -> QPointF:
            return QPointF(rect.left() + x * rect.width(), rect.bottom() - y * rect.height())

        p0 = point(0, 0)
        p1 = point(self.values[0], self.values[1])
        p2 = point(self.values[2], self.values[3])
        p3 = point(1, 1)
        painter.setPen(QPen(QColor(WARNING), 1))
        painter.drawLine(p0, p1)
        painter.drawLine(p2, p3)
        path = QPainterPath(p0)
        path.cubicTo(p1, p2, p3)
        painter.setPen(QPen(QColor(ACCENT), 3))
        painter.drawPath(path)
        painter.setBrush(QColor(ACCENT))
        painter.setPen(QPen(QColor(ACCENT_TEXT), 1))
        for pt in [p1, p2]:
            painter.drawEllipse(pt, 5, 5)
        painter.setBrush(QColor(SURFACE))
        for pt in [p0, p3]:
            painter.drawEllipse(pt, 4, 4)


class BezierCurveEditor(QWidget):
    def __init__(self, value: str = "0.46,1.0,0.29,1") -> None:
        super().__init__()
        self.preview = BezierCurvePreview()
        self.value_label = QLabel()
        self.value_label.setObjectName("pageSub")
        self.sliders: list[QSlider] = []
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self.preview)
        names = ["x1", "y1", "x2", "y2"]
        grid = QGridLayout()
        for row, name in enumerate(names):
            label = QLabel(name)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.valueChanged.connect(self.update_from_sliders)
            value_label = QLabel("0.00")
            value_label.setMinimumWidth(44)
            slider.setProperty("value_label", value_label)
            self.sliders.append(slider)
            grid.addWidget(label, row, 0)
            grid.addWidget(slider, row, 1)
            grid.addWidget(value_label, row, 2)
        box.addLayout(grid)
        box.addWidget(self.value_label)
        self.setText(value)

    def values(self) -> list[float]:
        return [slider.value() / 100 for slider in self.sliders]

    def text(self) -> str:
        return ",".join(f"{value:.2f}".rstrip("0").rstrip(".") for value in self.values())

    def setText(self, value: str) -> None:  # noqa: N802 - mimic QLineEdit API
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 4:
            parts = ["0.46", "1.0", "0.29", "1"]
        parsed: list[float] = []
        for part in parts:
            try:
                parsed.append(max(0.0, min(1.0, float(part))))
            except ValueError:
                parsed.append(0.5)
        for slider, number in zip(self.sliders, parsed, strict=False):
            slider.blockSignals(True)
            slider.setValue(round(number * 100))
            slider.blockSignals(False)
        self.update_from_sliders()

    def update_from_sliders(self) -> None:
        vals = self.values()
        self.preview.set_values(vals)
        for slider, value in zip(self.sliders, vals, strict=False):
            label = slider.property("value_label")
            if isinstance(label, QLabel):
                label.setText(f"{value:.2f}")
        self.value_label.setText(f"Curve: {self.text()}")


class SearchCombo(QWidget):
    """Dropdown with search-on-open: click to open a popup with search + filtered list."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(330)
        self._items: list[tuple[str, str]] = []  # [(display, data), ...]
        self._current_data = ""
        self._current_text = ""

        # The button that looks like a dropdown
        self._btn = QPushButton(self)
        self._btn.setObjectName("searchComboBtn")
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._toggle_popup)
        self._btn.setStyleSheet(f"""
            QPushButton#searchComboBtn {{
                background: {FIELD}; color: {TEXT}; border: 1px solid {BORDER};
                border-radius: 12px; padding: 9px 30px 9px 12px; min-height: 24px;
                text-align: left; font-size: 15px;
            }}
            QPushButton#searchComboBtn:hover {{ border-color: {ACCENT}; }}
        """)

        # The popup frame with dark theme
        self._popup = QFrame(None, Qt.WindowType.Popup)
        self._popup.setObjectName("searchComboPopup")
        self._popup.setStyleSheet(f"""
            QFrame#searchComboPopup {{
                background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
            }}
            QLineEdit {{
                background: {BG}; color: {TEXT}; border: 1px solid {BORDER};
                border-radius: 10px; padding: 8px 12px; font-size: 14px;
            }}
            QListWidget {{
                background: {SURFACE}; color: {TEXT}; border: none; outline: none; font-size: 14px;
            }}
            QListWidget::item {{ padding: 8px 12px; border-radius: 8px; }}
            QListWidget::item:selected {{ background: {ACCENT}; color: {ACCENT_TEXT}; }}
            QListWidget::item:hover {{ background: {FIELD}; }}
            QScrollBar:vertical {{ width: 10px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(6, 6, 6, 6)
        popup_layout.setSpacing(4)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search...")
        self._search.textChanged.connect(self._filter_items)
        popup_layout.addWidget(self._search)
        self._list = QListWidget()
        self._list.setMaximumHeight(320)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.itemClicked.connect(self._pick_item)
        popup_layout.addWidget(self._list)

        # Arrow indicator overlay
        self._arrow = QLabel("\u25BE", self)
        self._arrow.setStyleSheet(f"color: {MUTED}; font-size: 16px; background: transparent;")
        self._arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._btn.setGeometry(0, 0, self.width(), self.height())
        self._arrow.move(self.width() - 26, (self.height() - self._arrow.height()) // 2)

    def _toggle_popup(self) -> None:
        if self._popup.isVisible():
            self._popup.hide()
            return
        self._rebuild_list()
        self._search.clear()
        # Position popup below this widget
        pos = self.mapToGlobal(self.rect().bottomLeft())
        # Adjust if it would go off-screen
        screen = self.screen().availableGeometry() if self.screen() else self.rect()
        w = max(self.width(), 300)
        self._popup.setFixedWidth(w)
        self._popup.move(pos)
        self._popup.show()
        self._search.setFocus()

    def _rebuild_list(self, filt: str = "") -> None:
        self._list.clear()
        low = filt.lower()
        for display, data in self._items:
            if not low or low in display.lower() or low in data.lower():
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self._list.addItem(item)
        # Highlight current
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == self._current_data:
                self._list.setCurrentRow(i)
                self._list.scrollToItem(self._list.item(i))
                break

    def _filter_items(self, text: str) -> None:
        self._rebuild_list(text)

    def _pick_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole) or ""
        display = item.text()
        self._current_data = data
        self._current_text = display
        self._btn.setText(display)
        self._popup.hide()

    def _update_btn_text(self) -> None:
        for display, data in self._items:
            if data == self._current_data:
                self._btn.setText(display)
                return
        self._btn.setText(self._current_text or "Select...")

    def add_item(self, display: str, data: str) -> None:
        self._items.append((display, data))
        if not self._current_data:
            self._current_data = data
            self._current_text = display
        self._update_btn_text()

    def clear_items(self) -> None:
        self._items.clear()
        self._current_data = ""
        self._current_text = ""
        self._btn.setText("Select...")

    def current_data(self) -> str:
        return self._current_data

    def set_current_data(self, data: str) -> None:
        self._current_data = data
        for display, d in self._items:
            if d == data:
                self._current_text = display
                break
        self._update_btn_text()

    def block_signals(self, block: bool) -> None:
        pass


class SettingRow(QFrame):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("settingRow")
        self.box = QHBoxLayout(self)
        self.box.setContentsMargins(18, 14, 18, 14)
        self.box.setSpacing(18)
        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("rowTitle")
        text_box.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("rowSub")
            sub.setWordWrap(True)
            text_box.addWidget(sub)
        self.box.addLayout(text_box, 1)

    def add_control(self, widget: QWidget) -> None:
        self.box.addWidget(
            widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = MangoConfig()
        self.controls: dict[str, QWidget] = {}
        self.service_rows: list[tuple[str, QLabel]] = []

        self.setWindowTitle("DMS Mango Workstation Settings")
        self.resize(1250, 820)
        self.setMinimumSize(980, 650)
        self.apply_style()

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(300)
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("stack")
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.pages = [
            ("⚙", "Overview", self.page_overview),
            ("★", "First Run Setup", self.page_first_run),
            ("▣", "Layout & Scroller", self.page_layout),
            ("✨", "Animations & Effects", self.page_animation),
            ("🖱", "Input", self.page_input),
            ("⌨", "Keyboard", self.page_keyboard),
            ("⌘", "Keybindings", self.page_keybindings),
            ("▥", "Window Rules", self.page_window_rules),
            ("🚀", "Startup", self.page_startup),
            ("●", "Services", self.page_services),
            ("◉", "Portals", self.page_portals),
            ("🎨", "Theme Bridge", self.page_theme_bridge),
            ("▤", "Default Apps", self.page_default_apps),
            ("📸", "Screenshots", self.page_screenshots),
            ("🖥", "Remote Desktop", self.page_remote_desktop),
            ("🔐", "Login", self.page_login),
            ("↩", "Backup & Recovery", self.page_backup),
            ("🛠", "Tools", self.page_tools),
        ]
        for icon, name, builder in self.pages:
            item = QListWidgetItem(f"  {icon}  {name}")
            item.setSizeHint(item.sizeHint() * 1.7)
            self.sidebar.addItem(item)
            self.stack.addWidget(builder())
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self.login_page_index = next((i for i, (_, n, _) in enumerate(self.pages) if n == "Login"), 0)

        refresh = QAction("Refresh", self)
        refresh.triggered.connect(self.refresh_all)
        self.menuBar().addAction(refresh)
        self.refresh_all()
        self.setup_tray_icon()

    def setup_tray_icon(self) -> None:
        """Create a system tray icon so the app appears in DMS's tray."""
        # Create a simple colored icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(ACCENT))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(4, 4, 56, 56, 12, 12)
        p.setPen(QPen(QColor(ACCENT_TEXT), 5))
        p.setFont(QFont("sans-serif", 32, QFont.Weight.Bold))
        p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "M")
        p.end()
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("DMS Mango Settings")

        menu = QMenu()
        menu.setStyleSheet(f"background: {BG}; color: {TEXT}; padding: 6px;")
        show_action = menu.addAction("Open Settings")
        show_action.triggered.connect(self._tray_show)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._tray_quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._tray_show()

    def _handle_single_instance(self, server) -> None:
        """Handle a second instance trying to start — bring window to front."""
        socket = server.nextPendingConnection()
        if socket:
            socket.waitForReadyRead(1000)
            socket.readAll()
            socket.disconnectFromServer()
        self._tray_show()
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._tray_show()

    def _tray_show(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_quit(self) -> None:
        self._quitting = True
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        """Hide to tray instead of quitting."""
        if getattr(self, '_quitting', False):
            event.accept()
            return
        event.ignore()
        self.hide()

    def apply_style(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; font-size: 15px; }}
            QMenuBar {{ background: {BG}; color: {TEXT}; }}
            #sidebar {{ background: {SIDEBAR}; border: none; padding: 18px 12px; outline: none; }}
            #sidebar::item {{ color: {TEXT}; padding: 13px 16px; border-radius: 14px; margin: 3px 0; }}
            #sidebar::item:selected {{ background: {ACCENT}; color: {ACCENT_TEXT}; }}
            #sidebar::item:hover:!selected {{ background: {SURFACE}; }}
            #stack {{ background: {BG}; }}
            #pageActions {{ background: {BG}; border-top: 1px solid {BORDER}; padding: 14px 34px; }}
            #pageTitle {{ font-size: 31px; font-weight: 650; color: {TEXT}; margin-bottom: 4px; }}
            #pageSub {{ color: {MUTED}; font-size: 15px; }}
            #card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px; }}
            #cardTitle {{ font-size: 22px; font-weight: 600; color: {TEXT}; }}
            #settingRow {{ background: transparent; border-top: 1px solid {BORDER}; }}
            #rowTitle {{ font-size: 16px; color: {TEXT}; }}
            #rowSub {{ font-size: 13px; color: {MUTED}; }}
            QCheckBox {{ spacing: 10px; color: {TEXT}; }}
            QCheckBox::indicator {{ width: 46px; height: 24px; border-radius: 12px; border: 1px solid {BORDER}; background: {FIELD}; }}
            QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
            QPushButton {{ background: {BUTTON}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 9px 14px; }}
            QPushButton:hover {{ background: {BUTTON_HOVER}; }}
            QPushButton#primary {{ background: {ACCENT}; color: {ACCENT_TEXT}; border-color: {ACCENT}; font-weight: 650; }}
            QComboBox, QLineEdit {{ background: {FIELD}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 9px 12px; min-height: 24px; }}
            QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px; selection-background-color: {ACCENT}; selection-color: {ACCENT_TEXT}; outline: none; }}
            #searchComboBtn {{ background: {FIELD}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 9px 12px; min-height: 24px; text-align: left; padding-right: 30px; }}
            #searchComboBtn:hover {{ border-color: {ACCENT}; }}
            #searchComboPopup {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
            #searchComboPopup QLineEdit {{ background: {BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px 12px; }}
            #searchComboPopup QListWidget {{ background: {SURFACE}; color: {TEXT}; border: none; outline: none; }}
            #searchComboPopup QListWidget::item {{ padding: 8px 12px; border-radius: 8px; }}
            #searchComboPopup QListWidget::item:selected {{ background: {ACCENT}; color: {ACCENT_TEXT}; }}
            #searchComboPopup QListWidget::item:hover {{ background: {FIELD}; }}
            QSlider::groove:horizontal {{ height: 6px; background: {BORDER}; border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ width: 20px; height: 20px; margin: -8px 0; border-radius: 10px; background: {TEXT}; }}
            QScrollArea {{ border: none; background: {BG}; }}
            QScrollBar:vertical {{ width: 12px; background: {BG}; }}
            QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 6px; }}
        """)

    def make_page(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(34, 28, 34, 0)
        outer_layout.setSpacing(20)
        header = QLabel(title)
        header.setObjectName("pageTitle")
        outer_layout.addWidget(header)
        sub = QLabel(subtitle)
        sub.setObjectName("pageSub")
        sub.setWordWrap(True)
        outer_layout.addWidget(sub)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 8, 12, 34)
        layout.setSpacing(22)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll, 1)
        outer._page_outer_layout = outer_layout
        outer._page_footer = None
        return outer, layout

    def card(self, layout: QVBoxLayout, title: str, subtitle: str = "") -> QVBoxLayout:
        frame = QFrame()
        frame.setObjectName("card")
        box = QVBoxLayout(frame)
        box.setContentsMargins(22, 20, 22, 20)
        box.setSpacing(0)
        head = QLabel(title)
        head.setObjectName("cardTitle")
        box.addWidget(head)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("pageSub")
            sub.setWordWrap(True)
            box.addWidget(sub)
            box.addSpacing(10)
        layout.addWidget(frame)
        return box

    def action_button(self, text: str, action, primary: bool = False, tooltip: str = "") -> QPushButton:
        btn = QPushButton(text)
        if primary:
            btn.setObjectName("primary")
        if tooltip:
            btn.setToolTip(tooltip)
            btn.setStatusTip(tooltip)
        btn.clicked.connect(action)
        return btn

    def add_page_actions(self, page: QWidget, actions: list[tuple[str, object, bool, str]]) -> None:
        outer_layout = getattr(page, "_page_outer_layout", None)
        if outer_layout is None:
            return
        footer = getattr(page, "_page_footer", None)
        if footer is not None:
            outer_layout.removeWidget(footer)
            footer.deleteLater()
        footer = QFrame()
        footer.setObjectName("pageActions")
        row = QHBoxLayout(footer)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        for text, action, primary, tooltip in actions:
            row.addWidget(self.action_button(text, action, primary, tooltip))
        row.addStretch(1)
        outer_layout.addWidget(footer)
        page._page_footer = footer

    def row(
        self, parent: QVBoxLayout, title: str, subtitle: str, control: QWidget
    ) -> QWidget:
        r = SettingRow(title, subtitle)
        r.add_control(control)
        parent.addWidget(r)
        return control

    def toggle(
        self, key: str, title: str, subtitle: str, default: bool = False
    ) -> QCheckBox:
        cb = QCheckBox()
        cb.setChecked(default)
        self.controls[key] = cb
        return cb

    def combo(self, key: str, values: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        self.controls[key] = combo
        return combo

    def line(self, key: str, placeholder: str = "") -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        self.controls[key] = edit
        return edit

    def curve_editor(self, key: str, value: str = "0.46,1.0,0.29,1") -> BezierCurveEditor:
        editor = BezierCurveEditor(value)
        self.controls[key] = editor
        return editor

    def slider(
        self, key: str, minimum: int, maximum: int, suffix: str = "", scale: int = 1
    ) -> QWidget:
        wrap = QWidget()
        box = QHBoxLayout(wrap)
        box.setContentsMargins(0, 0, 0, 0)
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(minimum, maximum)
        s.setMinimumWidth(220)
        label = QLabel()
        label.setMinimumWidth(74)

        def update(v: int) -> None:
            val = v / scale
            label.setText(f"{val:g}{suffix}")

        s.valueChanged.connect(update)
        update(s.value())
        box.addWidget(s)
        box.addWidget(label)
        self.controls[key] = s
        s.setProperty("scale", scale)
        return wrap

    def page_overview(self) -> QWidget:
        page, layout = self.make_page(
            "Workstation Settings",
            "Mango + DMS + KDE/Qt workstation profile status and quick actions.",
        )
        c = self.card(layout, "Current session")
        self.session_label = QLabel()
        self.layout_label = QLabel()
        self.keyboard_label = QLabel()
        for w in [self.session_label, self.layout_label, self.keyboard_label]:
            w.setObjectName("rowTitle")
            c.addWidget(w)
        c.addSpacing(14)
        log_card = self.card(layout, "Activity Log", "Output from setup actions. Text is selectable for copy/paste.")
        self.log_box = QTextEdit("Ready.")
        self.log_box.setReadOnly(True)
        self.log_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.log_box.setMinimumHeight(280)
        self.log_box.setObjectName("logBox")
        log_card.addWidget(self.log_box)
        self.status_label = QLabel("")
        self.status_label.setObjectName("pageSub")
        self.status_label.setStyleSheet(f"color: {MUTED};")
        log_card.addWidget(self.status_label)
        self.add_page_actions(page, [
            ("Run Health Check", self.run_health, True, "Run the workstation verification script and show the results here."),
            ("Reload Mango", self.reload_mango, False, "Reload Mango config without logging out."),
            ("Open Project Folder", lambda: self.open_folder(str(PROJECT)), False, "Open the dms-kde-workstation project folder in Dolphin."),
        ])
        layout.addStretch(1)
        return page

    def _first_run_row(self, parent: QVBoxLayout, title: str, subtitle: str, action_text: str, action, primary: bool = False) -> QLabel:
        """Create a dashboard row with title/subtitle, status label, and action button. Returns the status QLabel."""
        row = SettingRow(title, subtitle)
        status = QLabel("Checking...")
        status.setObjectName("rowSub")
        row.box.addWidget(status)
        if action_text:
            btn = self.action_button(action_text, action, primary)
            row.box.addWidget(btn)
        parent.addWidget(row)
        return status

    def page_first_run(self) -> QWidget:
        page, layout = self.make_page(
            "First Run Setup",
            "Run this from your current working KDE/niri session before you ever log into Mango. Each row shows current status and safe next actions.",
        )

        self.first_run_rows: dict[str, QLabel] = {}

        overall = self.card(layout, "Status")
        self.first_run_overall_label = QLabel("Checking...")
        self.first_run_overall_label.setStyleSheet(f"color: {WARNING}; font-weight: 650; font-size: 18px;")
        overall.addWidget(self.first_run_overall_label)

        prereq_card = self.card(layout, "Hard prerequisites", "These must be installed before you switch to the Mango session.")
        self.first_run_rows["mango"] = self._first_run_row(
            prereq_card, "Mango installed", "Required compositor package and session entry",
            "Show Install Help", self.show_install_prereq_help,
        )
        self.first_run_rows["dms"] = self._first_run_row(
            prereq_card, "DMS installed", "The shell itself must already be installed",
            "Show Install Help", self.show_install_prereq_help,
        )
        self.first_run_rows["quickshell"] = self._first_run_row(
            prereq_card, "Quickshell available", "Needed by DMS to launch the shell UI",
            "Show Install Help", self.show_install_prereq_help,
        )

        env_card = self.card(layout, "Toolkit Environment", "Stable Qt/Electron toolkit variables via environment.d")
        self.first_run_rows["env"] = self._first_run_row(
            env_card, "Environment variables", "QT_QPA_PLATFORM, qt6ct, Electron Wayland hint",
            "Fix Environment", self.fix_environment, primary=True,
        )

        portal_card = self.card(layout, "Portal Packages", "Required xdg-desktop-portal backends")
        self.first_run_rows["portals"] = self._first_run_row(
            portal_card, "Portal RPMs", "xdg-desktop-portal, wlr, gtk, kde",
            "Install Missing", self.install_portals, primary=True,
        )

        baseline_card = self.card(layout, "Baseline Files", "Core workstation config and helpers")
        self.first_run_rows["baseline"] = self._first_run_row(
            baseline_card, "Baseline deployed", "Mango config, portal overrides, helpers",
            "Apply Baseline", self.first_run_apply_baseline, primary=True,
        )
        self.first_run_rows["dms_startup"] = self._first_run_row(
            baseline_card, "DMS startup in Mango", "exec-once with qt6ct env",
            "", lambda: None,
        )
        self.first_run_rows["dms_ownership"] = self._first_run_row(
            baseline_card, "DMS startup ownership", "Avoid running both dms.service and Mango exec-once at the same time",
            "Fix Startup Ownership", self.fix_dms_startup_ownership,
        )

        login_card = self.card(layout, "Login / Autologin", "SDDM autologin to Mango session")
        self.first_run_rows["login"] = self._first_run_row(
            login_card, "Autologin", "SDDM auto-login session and user",
            "Fix Login", self.first_run_fix_login, primary=True,
        )
        self.first_run_rows["script"] = self._first_run_row(
            login_card, "Autologin script", "sddm-consolidate-autologin.py deployed",
            "", lambda: None,
        )

        theme_card = self.card(layout, "Theme", "DMS Matugen export status")
        self.first_run_rows["theme"] = self._first_run_row(
            theme_card, "DMS Theme export", "GTK3/4 + QT5/6 colors exported once",
            "Open DMS Theme", lambda: self.detach(["dms", "run", "--config-module", "theme"]),
        )

        note = QLabel(
            "Safe order:\n"
            "• Stay in your current working KDE/niri session\n"
            "• Install Mango and DMS first\n"
            "• Apply this baseline and make sure all blockers are green\n"
            "• Only then log out and choose Mango in SDDM\n"
            "• After the first successful Mango login, export DMS Theme/Colors once"
        )
        note.setObjectName("pageSub")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)

        self.add_page_actions(page, [
            ("Refresh Status", self.refresh_first_run, False, "Re-check all system-level items."),
            ("Dry-Run Baseline", self.dry_run_first_run_setup, False, "Preview what the baseline installer would change."),
            ("Apply Full Baseline", self.first_run_apply_baseline, True, "Deploy all user-level config files and helpers. Refuses to run while hard prerequisites are missing."),
            ("Check Ready for First Mango Login", self.run_first_login_readiness, False, "Verify from your current working session whether it is safe to log out and choose Mango."),
            ("Open Validation Checklist", lambda: self.open_text_file(FRESH_VALIDATION_CHECKLIST), False, "Open the fresh-machine validation checklist used to verify the full install flow."),
            ("Open Results Template", lambda: self.open_text_file(FRESH_VALIDATION_RESULTS_TEMPLATE), False, "Open the template used to record a real fresh-machine validation run."),
            ("Run Health Check", self.run_health, False, "Run the workstation verification script."),
        ])
        return page

    def page_layout(self) -> QWidget:
        page, layout = self.make_page(
            "Layout & Scroller",
            "Mango-specific layouts, scroller centering, proportions, gaps, borders, and tiling behavior.",
        )
        live = self.card(
            layout,
            "Live layout",
            "Changes the current monitor layout immediately with Mango IPC.",
        )
        self.live_layout = self.combo("__live_layout", list(LAYOUTS.keys()))
        self.row(live, "Active layout", "Set current layout now", self.live_layout)
        live_btn = QPushButton("Apply active layout")
        live_btn.setObjectName("primary")
        live_btn.clicked.connect(self.set_active_layout)
        live.addWidget(live_btn, 0, Qt.AlignmentFlag.AlignRight)

        scroller = self.card(
            layout,
            "Scroller",
            "Niri-like workflow controls. Centering focused windows is controlled here.",
        )
        self.default_layout = self.combo("__default_layout", list(LAYOUTS.keys()))
        self.row(
            scroller,
            "Default layout for tags 1-9",
            "Applied as tagrule layout_name for each tag",
            self.default_layout,
        )
        self.row(
            scroller,
            "Center focused window",
            "Mango scroller_focus_center",
            self.toggle("scroller_focus_center", "", "", True),
        )
        self.row(
            scroller,
            "Prefer center",
            "Mango scroller_prefer_center",
            self.toggle("scroller_prefer_center", "", "", True),
        )
        self.row(
            scroller,
            "Edge pointer focus",
            "Mango edge_scroller_pointer_focus",
            self.toggle("edge_scroller_pointer_focus", "", "", True),
        )
        self.row(
            scroller,
            "Default proportion",
            "Width/size ratio used by scroller",
            self.slider("scroller_default_proportion", 10, 200, "", 100),
        )
        self.row(
            scroller,
            "Single-window proportion",
            "Size ratio when one window is present",
            self.slider("scroller_default_proportion_single", 10, 200, "", 100),
        )
        self.row(
            scroller,
            "Scroller structures",
            "Number of scroller structures",
            self.slider("scroller_structs", 1, 100),
        )
        self.row(
            scroller,
            "Proportion presets",
            "Comma-separated values, e.g. 0.5,0.8,1.0",
            self.line("scroller_proportion_preset"),
        )

        tile = self.card(
            layout, "Tile / Dwindle", "Master-stack and dwindle layout tuning."
        )
        self.row(
            tile,
            "New window is master",
            "Mango new_is_master",
            self.toggle("new_is_master", "", "", True),
        )
        self.row(
            tile,
            "Master factor",
            "Mango default_mfact",
            self.slider("default_mfact", 10, 90, "", 100),
        )
        self.row(
            tile,
            "Master windows",
            "Mango default_nmaster",
            self.slider("default_nmaster", 1, 10),
        )
        self.row(
            tile,
            "Smart gaps",
            "Mango smartgaps",
            self.toggle("smartgaps", "", "", False),
        )
        for key, label in [
            ("dwindle_smart_split", "Dwindle smart split"),
            ("dwindle_drop_simple_split", "Drop simple split"),
            ("dwindle_manual_split", "Manual split"),
            ("dwindle_hsplit", "Horizontal split"),
            ("dwindle_vsplit", "Vertical split"),
            ("dwindle_preserve_split", "Preserve split"),
        ]:
            self.row(tile, label, key, self.toggle(key, "", ""))

        appearance = self.card(layout, "Gaps and borders")
        for key, label, maxv in [
            ("gappih", "Inner gap horizontal", 80),
            ("gappiv", "Inner gap vertical", 80),
            ("gappoh", "Outer gap horizontal", 100),
            ("gappov", "Outer gap vertical", 100),
            ("borderpx", "Border width", 12),
            ("border_radius", "Border radius", 48),
        ]:
            self.row(appearance, label, key, self.slider(key, 0, maxv, " px"))
        self.add_page_actions(page, [
            ("Apply Active Layout", self.set_active_layout, False, "Send the selected layout to Mango immediately for the current monitor."),
            ("Save Layout Settings", self.save_layout, True, "Back up Mango config and save layout, scroller, gap, and border settings."),
        ])
        return page

    def page_animation(self) -> QWidget:
        page, layout = self.make_page(
            "Animations & Effects",
            "Animation, blur, shadows, opacity, and transition settings exposed with sliders and dropdowns.",
        )
        effects = self.card(layout, "Effects")
        for key, label in [
            ("blur", "Blur"),
            ("blur_layer", "Layer blur"),
            ("blur_optimized", "Optimized blur"),
            ("shadows", "Shadows"),
            ("layer_shadows", "Layer shadows"),
            ("shadow_only_floating", "Shadows only on floating windows"),
        ]:
            self.row(effects, label, key, self.toggle(key, "", ""))
        for key, label, minv, maxv in [
            ("blur_params_num_passes", "Blur passes", 1, 8),
            ("blur_params_radius", "Blur radius", 0, 40),
            ("shadows_size", "Shadow size", 0, 60),
            ("shadows_blur", "Shadow blur", 0, 80),
        ]:
            self.row(effects, label, key, self.slider(key, minv, maxv))
        for key, label in [
            ("focused_opacity", "Focused opacity"),
            ("unfocused_opacity", "Unfocused opacity"),
        ]:
            self.row(effects, label, key, self.slider(key, 20, 100, "%", 100))

        fade_zoom = self.card(layout, "Fade and zoom parameters")
        for key, label in [
            ("fadein_begin_opacity", "Fade-in starting opacity"),
            ("fadeout_begin_opacity", "Fade-out starting opacity"),
            ("zoom_initial_ratio", "Zoom initial scale"),
            ("zoom_end_ratio", "Zoom end scale"),
        ]:
            self.row(fade_zoom, label, key, self.slider(key, 0, 100, "%", 100))

        anim = self.card(layout, "Animations")
        for key, label in [
            ("animations", "Window animations"),
            ("layer_animations", "Layer animations"),
            ("animation_fade_in", "Fade in"),
            ("animation_fade_out", "Fade out"),
        ]:
            self.row(anim, label, key, self.toggle(key, "", ""))
        self.row(
            anim,
            "Open animation",
            "animation_type_open",
            self.combo("animation_type_open", ["slide", "zoom", "fade", "none"]),
        )
        self.row(
            anim,
            "Close animation",
            "animation_type_close",
            self.combo("animation_type_close", ["slide", "zoom", "fade", "none"]),
        )
        self.row(
            anim,
            "Tag animation direction",
            "tag_animation_direction",
            self.combo("tag_animation_direction", ["horizontal", "vertical"]),
        )
        for key, label, maxv in [
            ("animation_duration_move", "Move duration", 2000),
            ("animation_duration_open", "Open duration", 2000),
            ("animation_duration_tag", "Tag duration", 2000),
            ("animation_duration_close", "Close duration", 2000),
            ("animation_duration_focus", "Focus duration", 1000),
        ]:
            self.row(anim, label, key, self.slider(key, 0, maxv, " ms"))

        curves = self.card(
            layout,
            "Animation curves",
            "Cubic bezier values: x1,y1,x2,y2. Presets fill every curve; individual rows can then be adjusted.",
        )
        preset_row = QHBoxLayout()
        self.animation_curve_preset = QComboBox()
        for name in self.animation_curve_presets():
            self.animation_curve_preset.addItem(name)
        preset_row.addWidget(self.animation_curve_preset)
        apply_preset = QPushButton("Apply curve preset")
        apply_preset.clicked.connect(self.apply_animation_curve_preset)
        preset_row.addWidget(apply_preset)
        preset_row.addStretch(1)
        curves.addLayout(preset_row)
        for key, label in self.animation_curve_keys():
            self.row(curves, label, key, self.curve_editor(key))

        self.add_page_actions(page, [
            ("Apply Curve Preset", self.apply_animation_curve_preset, False, "Fill all curve fields with the selected preset. Save afterwards to write it to Mango config."),
            ("Save Animations & Effects", self.save_effects, True, "Back up Mango config and save animation, blur, shadow, and opacity settings."),
        ])
        return page

    def page_input(self) -> QWidget:
        page, layout = self.make_page(
            "Input", "Mouse, trackpad, pointer focus, dragging, and scrolling behavior."
        )
        c = self.card(layout, "Focus and pointer")
        for key, title in [
            ("sloppyfocus", "Focus follows mouse"),
            ("warpcursor", "Warp cursor"),
            ("focus_cross_monitor", "Focus across monitors"),
            ("focus_cross_tag", "Focus across tags"),
            ("enable_floating_snap", "Floating snap"),
            ("drag_tile_to_tile", "Drag tile to tile"),
            ("drag_tile_small", "Drag small tiled windows"),
        ]:
            self.row(c, title, key, self.toggle(key, "", ""))
        self.row(
            c,
            "Snap distance",
            "enable_floating_snap distance",
            self.slider("snap_distance", 0, 120, " px"),
        )
        self.row(
            c,
            "Cursor size",
            "Mango cursor_size",
            self.slider("cursor_size", 12, 64, " px"),
        )
        t = self.card(layout, "Trackpad and mouse")
        for key, title in [
            ("disable_trackpad", "Disable trackpad"),
            ("tap_to_click", "Tap to click"),
            ("tap_and_drag", "Tap and drag"),
            ("drag_lock", "Drag lock"),
            ("trackpad_natural_scrolling", "Trackpad natural scrolling"),
            ("disable_while_typing", "Disable while typing"),
            ("left_handed", "Left handed"),
            ("middle_button_emulation", "Middle button emulation"),
            ("mouse_natural_scrolling", "Mouse natural scrolling"),
        ]:
            self.row(t, title, key, self.toggle(key, "", ""))
        self.row(
            t,
            "Swipe threshold",
            "swipe_min_threshold",
            self.slider("swipe_min_threshold", 0, 20),
        )
        self.add_page_actions(page, [
            ("Save Input Settings", lambda: self.save_keys(self.input_keys(), "input"), True, "Back up Mango config and save mouse, pointer, and trackpad settings."),
        ])
        return page

    def page_keyboard(self) -> QWidget:
        page, layout = self.make_page(
            "Keyboard",
            "Layouts and switching. Approved baseline keeps Alt+Shift for English/Greek.",
        )
        c = self.card(layout, "Keyboard layout")
        self.row(
            c,
            "Layouts",
            "Comma-separated XKB layouts",
            self.line("xkb_rules_layout", "us,gr"),
        )
        self.row(c, "Repeat rate", "Keys per second", self.slider("repeat_rate", 5, 80))
        self.row(
            c,
            "Repeat delay",
            "Delay before repeat",
            self.slider("repeat_delay", 100, 1200, " ms"),
        )
        self.row(c, "Numlock on", "Mango numlockon", self.toggle("numlockon", "", ""))
        self.alt_shift = QCheckBox()
        self.direct_layouts = QCheckBox()
        self.row(
            c,
            "Alt+Shift toggles layout",
            "Preserve required English/Greek switching",
            self.alt_shift,
        )
        self.row(
            c,
            "Super+Ctrl+1/2 direct layouts",
            "English/Greek direct selection",
            self.direct_layouts,
        )
        self.add_page_actions(page, [
            ("Save Keyboard Settings", self.save_keyboard, True, "Back up Mango config and save keyboard layouts, repeat settings, and layout shortcuts."),
        ])
        return page

    def page_keybindings(self) -> QWidget:
        page, layout = self.make_page(
            "Keybindings",
            "DMS has a built-in keybinding editor that reads and writes Mango config directly.",
        )
        c = self.card(layout, "Managed by DMS", "DMS Settings includes a full keybinding editor with search, categories, compositor actions, DMS actions, and custom commands. It writes directly to your Mango config — no need for a separate editor here.")
        info = QLabel(
            "DMS Keybinds supports:\n"
            "• Compositor actions (close, minimize, focus, layout switch…)\n"
            "• DMS actions (launcher, clipboard, notifications, control center, lock…)\n"
            "• Custom commands (spawn any app or script)\n"
            "• Shell commands\n"
            "• Search, categories, and per-binding editing"
        )
        info.setObjectName("pageSub")
        info.setWordWrap(True)
        c.addWidget(info)
        layout.addStretch(1)
        self.add_page_actions(page, [
            ("Open DMS Keybinds", lambda: self.detach(["dms", "ipc", "call", "keybinds", "open"]), True, "Open the DMS keybinding editor."),
            ("Open DMS Settings", lambda: self.detach(["dms", "ipc", "call", "settings", "open"]), False, "Open the full DMS Settings panel."),
        ])
        return page

    def page_window_rules(self) -> QWidget:
        page, layout = self.make_page(
            "Window Rules",
            "Per-app Mango window rules. Match by app ID and/or title, then apply opacity, floating, blur, decoration, and behavior rules to that app only.",
        )

        current = self.card(
            layout,
            "Current rules",
            "These are the windowrule= lines currently present in your Mango config.",
        )
        self.window_rules_list = QListWidget()
        self.window_rules_list.setMinimumHeight(220)
        self.window_rules_list.itemClicked.connect(self.load_selected_window_rule)
        current.addWidget(self.window_rules_list)

        inspect = self.card(
            layout,
            "Focused window inspector",
            "Mango only exposes the focused window directly. Use delayed capture so this settings app gets out of the way first.",
        )
        self.window_rule_focus_label = QLabel()
        self.window_rule_focus_label.setObjectName("pageSub")
        self.window_rule_focus_label.setWordWrap(True)
        inspect.addWidget(self.window_rule_focus_label)
        inspect_row = QHBoxLayout()
        inspect_row.addWidget(self.action_button("Refresh Focused Window", self.refresh_focused_window_rule_target, False, "Query Mango for the currently focused window title and app ID."))
        inspect_row.addWidget(self.action_button("Capture After 3 Seconds", self.capture_window_rule_target_delayed, True, "Hide this app, switch to the target app, then capture its app ID and title after 3 seconds."))
        inspect_row.addWidget(self.action_button("Use Focused Window Now", self.use_focused_window_for_rule, False, "Copy the currently focused window title and app ID into the editor below immediately."))
        inspect_row.addStretch(1)
        inspect.addLayout(inspect_row)

        editor = self.card(
            layout,
            "Rule editor",
            "Create or replace one Mango windowrule entry. Match by app ID, title, or both. Mango supports per-window opacity here. Per-window blur strength is not available — only blur disable/enable via noblur.",
        )
        form = QGridLayout()
        self.window_rule_appid = QLineEdit()
        self.window_rule_appid.setPlaceholderText("com.mitchellh.ghostty or app.zen_browser.zen")
        self.window_rule_title = QLineEdit()
        self.window_rule_title.setPlaceholderText("Optional title match / regex")
        self.window_rule_enable_title = QCheckBox("Match title too")
        self.window_rule_focused_opacity = QSlider(Qt.Orientation.Horizontal)
        self.window_rule_focused_opacity.setRange(0, 100)
        self.window_rule_focused_opacity.setValue(100)
        self.window_rule_focused_opacity_value = QLabel("disabled")
        self.window_rule_unfocused_opacity = QSlider(Qt.Orientation.Horizontal)
        self.window_rule_unfocused_opacity.setRange(0, 100)
        self.window_rule_unfocused_opacity.setValue(100)
        self.window_rule_unfocused_opacity_value = QLabel("disabled")
        self.window_rule_enable_focused_opacity = QCheckBox("Use focused opacity override")
        self.window_rule_enable_unfocused_opacity = QCheckBox("Use unfocused opacity override")
        form.addWidget(QLabel("App ID match"), 0, 0)
        form.addWidget(self.window_rule_appid, 0, 1)
        form.addWidget(self.window_rule_enable_title, 1, 0)
        form.addWidget(self.window_rule_title, 1, 1)
        form.addWidget(self.window_rule_enable_focused_opacity, 2, 0)
        focus_row = QHBoxLayout()
        focus_row.addWidget(self.window_rule_focused_opacity, 1)
        focus_row.addWidget(self.window_rule_focused_opacity_value)
        form.addLayout(focus_row, 2, 1)
        form.addWidget(self.window_rule_enable_unfocused_opacity, 3, 0)
        unfocus_row = QHBoxLayout()
        unfocus_row.addWidget(self.window_rule_unfocused_opacity, 1)
        unfocus_row.addWidget(self.window_rule_unfocused_opacity_value)
        form.addLayout(unfocus_row, 3, 1)
        editor.addLayout(form)
        self.window_rule_focused_opacity.valueChanged.connect(lambda v: self.window_rule_focused_opacity_value.setText(f"{v}% / {v/100:.2f}"))
        self.window_rule_unfocused_opacity.valueChanged.connect(lambda v: self.window_rule_unfocused_opacity_value.setText(f"{v}% / {v/100:.2f}"))
        self.window_rule_enable_title.toggled.connect(lambda _=False: self.build_window_rule_line())
        self.window_rule_enable_focused_opacity.toggled.connect(lambda _=False: self.build_window_rule_line())
        self.window_rule_enable_unfocused_opacity.toggled.connect(lambda _=False: self.build_window_rule_line())
        self.window_rule_focused_opacity.valueChanged.connect(lambda _=0: self.build_window_rule_line())
        self.window_rule_unfocused_opacity.valueChanged.connect(lambda _=0: self.build_window_rule_line())
        self.window_rule_focused_opacity_value.setText("100% / 1.00")
        self.window_rule_unfocused_opacity_value.setText("100% / 1.00")

        self.window_rule_toggles: dict[str, QCheckBox] = {}
        toggles = QGridLayout()
        toggle_defs = [
            ("isfloating", "Floating"),
            ("isglobal", "Sticky / global"),
            ("isoverlay", "Overlay / top layer"),
            ("noblur", "Disable blur"),
            ("isnoborder", "No border"),
            ("isnoshadow", "No shadow"),
            ("isnoradius", "No corner radius"),
            ("isnoanimation", "No animation"),
            ("noopenmaximized", "Do not open maximized"),
            ("force_tiled_state", "Force tiled state"),
            ("allow_csd", "Allow client-side decoration"),
        ]
        for i, (key, label) in enumerate(toggle_defs):
            cb = QCheckBox(label)
            self.window_rule_toggles[key] = cb
            toggles.addWidget(cb, i // 2, i % 2)
        editor.addLayout(toggles)

        self.window_rule_appid.textChanged.connect(lambda _="": self.build_window_rule_line())
        self.window_rule_title.textChanged.connect(lambda _="": self.build_window_rule_line())
        self.window_rule_preview = QLabel()
        self.window_rule_preview.setObjectName("pageSub")
        self.window_rule_preview.setWordWrap(True)
        editor.addWidget(self.window_rule_preview)
        self.add_page_actions(page, [
            ("Refresh Rules", self.refresh_window_rules, False, "Reload window rules and focused-window info from the current Mango config/session."),
            ("Remove Selected Rule", self.remove_selected_window_rule, False, "Remove the selected windowrule entry from the in-memory list."),
            ("Add or Replace Rule", self.add_or_replace_window_rule, True, "Add a new Mango window rule or replace an existing one with the same app ID/title match."),
            ("Save Window Rules", self.save_window_rules, True, "Back up Mango config, write all window rules, and reload Mango."),
        ])
        return page

    def page_startup(self) -> QWidget:
        page, layout = self.make_page(
            "Startup",
            "Apps added here start automatically after you log in and the desktop is ready.",
        )

        apps = self.card(
            layout,
            "Startup Apps",
            "Select an app and click Add to Startup. It will launch automatically on next login after the desktop and tray are ready.",
        )
        self.autostart_apps_list = QListWidget()
        self.autostart_apps_list.setMinimumHeight(250)
        apps.addWidget(self.autostart_apps_list)
        app_row = QHBoxLayout()
        self.desktop_app_combo = SearchCombo()
        app_row.addWidget(self.desktop_app_combo, 1)
        for text, action, primary, tooltip in [
            ("Add to Startup", self.add_selected_desktop_autostart, True, "Copy the selected launcher into the startup apps folder."),
            ("Remove from Startup", self.remove_selected_autostart_app, False, "Remove the selected launcher from the startup apps folder."),
            ("Open Startup Folder", lambda: self.open_folder(str(HOME / ".config/autostart")), False, "Open the startup apps folder in Dolphin."),
        ]:
            app_row.addWidget(self.action_button(text, action, primary, tooltip))
        apps.addLayout(app_row)

        return page

    def page_services(self) -> QWidget:
        page, layout = self.make_page(
            "Services", "Start, stop, restart, and inspect workstation user services that actually exist on this machine."
        )
        c = self.card(layout, "User services")
        self.service_rows.clear()
        visible = 0
        for label, unit in SERVICES:
            if not self.user_unit_exists(unit):
                continue
            r = SettingRow(label, unit)
            status = QLabel("unknown")
            status.setMinimumWidth(80)
            r.add_control(status)
            for action in ["start", "stop", "restart", "status"]:
                btn = QPushButton(action.capitalize())
                btn.clicked.connect(
                    lambda _=False, a=action, u=unit: self.service_action(a, u)
                )
                r.add_control(btn)
            c.addWidget(r)
            self.service_rows.append((unit, status))
            visible += 1
        if visible == 0:
            note = QLabel("No known workstation user services were detected on this machine yet.")
            note.setObjectName("pageSub")
            note.setWordWrap(True)
            c.addWidget(note)
        return page

    def page_portals(self) -> QWidget:
        page, layout = self.make_page(
            "Portals",
            "xdg-desktop-portal status, Mango override files, and quick repair/test actions.",
        )
        c = self.card(layout, "Portal services")
        self.portal_rows: list[tuple[str, QLabel]] = []
        for label, unit in [
            ("Core portal", "xdg-desktop-portal.service"),
            ("WLR portal", "xdg-desktop-portal-wlr.service"),
            ("GTK portal", "xdg-desktop-portal-gtk.service"),
            ("KDE portal", "plasma-xdg-desktop-portal-kde.service"),
        ]:
            r = SettingRow(label, unit)
            status = QLabel("unknown")
            status.setMinimumWidth(90)
            r.add_control(status)
            self.portal_rows.append((unit, status))
            c.addWidget(r)
        row = QHBoxLayout()
        for text, action, primary in [
            ("Restart portals", self.restart_portals, True),
            ("Test file chooser", self.test_file_chooser, False),
            ("Open portal config", lambda: self.open_text_file(HOME / ".config/xdg-desktop-portal/mango-portals.conf"), False),
            ("Open portal unit", lambda: self.open_text_file(HOME / ".config/systemd/user/xdg-desktop-portal.service"), False),
        ]:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("primary")
            btn.clicked.connect(action)
            row.addWidget(btn)
        row.addStretch(1)
        c.addLayout(row)
        files = self.card(layout, "Portal files", "Expected Mango portal override/config files.")
        self.portal_files_label = QLabel()
        self.portal_files_label.setObjectName("pageSub")
        self.portal_files_label.setWordWrap(True)
        files.addWidget(self.portal_files_label)
        return page

    def page_theme_bridge(self) -> QWidget:
        page, layout = self.make_page(
            "Theme Bridge",
            "Font and theme bridge between DMS, KDE globals, GTK, and Qt toolkit configs.",
        )

        font_card = self.card(
            layout,
            "Workstation font",
            "Set one font and size for DMS, KDE apps, GTK apps, and Qt toolkit configs at the same time.",
        )
        font_row = QHBoxLayout()
        self.font_family_combo = QComboBox()
        self.font_family_combo.setMinimumWidth(260)
        self.font_size_combo = QComboBox()
        self.font_size_combo.setMinimumWidth(80)
        font_row.addWidget(QLabel("Font family"), 0)
        font_row.addWidget(self.font_family_combo, 1)
        font_row.addWidget(QLabel("Size"), 0)
        font_row.addWidget(self.font_size_combo, 0)
        font_card.addLayout(font_row)
        self.font_status_label = QLabel()
        self.font_status_label.setObjectName("pageSub")
        self.font_status_label.setWordWrap(True)
        font_card.addWidget(self.font_status_label)
        font_actions = QHBoxLayout()
        for text, action, primary in [
            ("Apply font everywhere", self.apply_font_bridge, True),
            ("Refresh font status", self.refresh_font_bridge, False),
        ]:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("primary")
            btn.clicked.connect(action)
            font_actions.addWidget(btn)
        font_actions.addStretch(1)
        font_card.addLayout(font_actions)
        font_scope = QLabel(
            "Writes: DMS settings.json fontFamily, kdeglobals [General] font/fixed/menuFont/toolBarFont, "
            "gtk-3.0/settings.ini gtk-font-name, gtk-4.0/settings.ini gtk-font-name, "
            "qt5ct/qt6ct [Fonts] general/fixed. Requires app restart to take effect."
        )
        font_scope.setObjectName("pageSub")
        font_scope.setWordWrap(True)
        font_card.addWidget(font_scope)

        theme_card = self.card(layout, "Theme files", "DMS Matugen export and toolkit palette validation.")
        self.theme_status_label = QLabel()
        self.theme_status_label.setObjectName("pageSub")
        self.theme_status_label.setWordWrap(True)
        theme_card.addWidget(self.theme_status_label)
        row = QHBoxLayout()
        for text, cmd in [
            ("Open DMS settings", ["bash", "-lc", "dms ipc call settings 2>/dev/null || dms run &"]),
            ("Open qt6ct", ["qt6ct"]),
            ("Open qt5ct", ["qt5ct"]),
            ("Open theme notes", ["env", "QT_QPA_PLATFORMTHEME=qt6ct", "QT_QPA_PLATFORMTHEME_QT6=qt6ct", "dolphin", "--new-window", str(PROJECT / "notes/theme-export-working-20260516")]),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _=False, c=cmd: self.detach(c))
            row.addWidget(btn)
        row.addStretch(1)
        theme_card.addLayout(row)
        hint = QLabel(
            "If KDE apps look wrong: install qt5ct/qt6ct-kde first, then re-export GTK3/4 and QT5/6 "
            "from DMS Theme & Colors. Restart this settings app after a Matugen export to reload the palette."
        )
        hint.setObjectName("pageSub")
        hint.setWordWrap(True)
        theme_card.addWidget(hint)
        return page

    def page_default_apps(self) -> QWidget:
        page, layout = self.make_page(
            "Default Apps",
            "Choose your own default applications with category rows, app dropdowns, backup, and verification. Baseline install does not force personal app choices.",
        )
        c = self.card(
            layout,
            "Default application categories",
            "Choose one app per category. Applying backs up ~/.config/mimeapps.list first and sets the related MIME types.",
        )
        self.default_app_combos: dict[str, QComboBox] = {}
        self.default_app_statuses: dict[str, QLabel] = {}
        for group in self.default_app_groups():
            key, title, subtitle, _mimes, _recommended = group
            row = SettingRow(title, subtitle)
            status = QLabel("unknown")
            status.setMinimumWidth(170)
            status.setObjectName("pageSub")
            combo = SearchCombo()
            self.default_app_combos[key] = combo
            self.default_app_statuses[key] = status
            row.add_control(status)
            row.add_control(combo)
            c.addWidget(row)
        actions = QHBoxLayout()
        c.addLayout(actions)
        notes = self.card(layout, "Verification", "Current MIME values after the last refresh/apply.")
        self.default_apps_label = QLabel()
        self.default_apps_label.setObjectName("pageSub")
        self.default_apps_label.setWordWrap(True)
        notes.addWidget(self.default_apps_label)
        self.add_page_actions(page, [
            ("Refresh Defaults", self.refresh_default_apps, False, "Reload MIME/default app status from the current system state."),
            ("Open mimeapps.list", lambda: self.open_text_file(HOME / ".config/mimeapps.list"), False, "Open the MIME defaults file in your editor."),
            ("Open KDE Default Apps", lambda: self.launch_kde_module("componentchooser", "kcm_componentchooser"), False, "Open KDE's component chooser for comparison."),
            ("Apply Approved Baseline", self.apply_default_apps, False, "Apply the tested KDE/Qt default app baseline."),
            ("Apply Selected Defaults", self.apply_selected_default_apps, True, "Back up mimeapps.list and apply the apps selected above."),
        ])
        return page

    def page_screenshots(self) -> QWidget:
        page, layout = self.make_page(
            "Screenshots & Recording",
            "grim/slurp/swappy screenshot workflow and wf-recorder helpers for Mango.",
        )
        c = self.card(layout, "Screenshot actions")
        self.screenshot_status_label = QLabel()
        self.screenshot_status_label.setObjectName("pageSub")
        self.screenshot_status_label.setWordWrap(True)
        c.addWidget(self.screenshot_status_label)
        grid = QGridLayout()
        actions = [
            ("Region → Swappy", [str(HOME / ".local/bin/dms-region-screenshot-edit")]),
            ("Full → Swappy", [str(HOME / ".local/bin/dms-full-screenshot-edit")]),
            ("Region → Clipboard", [str(HOME / ".local/bin/dms-region-screenshot-copy")]),
            ("Open screenshots", ["env", "QT_QPA_PLATFORMTHEME=qt6ct", "QT_QPA_PLATFORMTHEME_QT6=qt6ct", "dolphin", "--new-window", str(HOME / "Pictures/Screenshots")]),
            ("Open Swappy", ["swappy", "-h"]),
        ]
        for i, (name, cmd) in enumerate(actions):
            btn = QPushButton(name)
            btn.clicked.connect(lambda _=False, c=cmd: self.detach(c))
            grid.addWidget(btn, i // 3, i % 3)
        c.addLayout(grid)
        rec = self.card(layout, "Recording")
        self.recording_command = QLineEdit()
        self.recording_command.setText(f"wf-recorder -f {HOME}/Videos/recording-$(date +%Y%m%d-%H%M%S).mp4")
        rec.addWidget(self.recording_command)
        row = QHBoxLayout()
        start = QPushButton("Start recording command in terminal")
        start.setObjectName("primary")
        start.clicked.connect(lambda: self.detach(self.get_terminal() + ["-e", "bash", "-lc", self.recording_command.text() + "; read -p 'Press Enter...'"]))
        row.addWidget(start)
        row.addStretch(1)
        rec.addLayout(row)
        return page

    def page_remote_desktop(self) -> QWidget:
        page, layout = self.make_page(
            "Remote Desktop",
            "Sunshine, RustDesk, capture/encoder status, and accepted environment notes.",
        )
        c = self.card(layout, "Status")
        self.remote_status_label = QLabel()
        self.remote_status_label.setObjectName("pageSub")
        self.remote_status_label.setWordWrap(True)
        c.addWidget(self.remote_status_label)
        row = QHBoxLayout()
        for text, action, primary in [
            ("Open Sunshine UI", lambda: self.detach(["xdg-open", "https://localhost:47990"]), True),
            ("Restart Sunshine", lambda: self.service_action("restart", "app-dev.lizardbyte.app.Sunshine.service"), False),
            ("Open RustDesk", lambda: self.detach(["rustdesk"]), False),
            ("Run nvidia-smi", lambda: self.detach(self.get_terminal() + ["-e", "bash", "-lc", "nvidia-smi; read -p 'Press Enter...'"]), False),
        ]:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("primary")
            btn.clicked.connect(action)
            row.addWidget(btn)
        row.addStretch(1)
        c.addLayout(row)
        note = QLabel("RustDesk is known to run from its privileged/background service with a weird DISPLAY=:0 environment, but user confirmed it works. Do not change it unless it breaks.")
        note.setObjectName("pageSub")
        note.setWordWrap(True)
        c.addWidget(note)
        return page

    def detect_display_manager(self) -> str:
        dm_link = Path("/etc/systemd/system/display-manager.service")
        if dm_link.is_symlink():
            return dm_link.resolve().name
        return ""

    def available_sessions(self) -> list[tuple[str, str]]:
        sessions: list[tuple[str, str]] = []
        for session_dir in [Path("/usr/share/wayland-sessions"), Path("/usr/share/xsessions")]:
            if not session_dir.exists():
                continue
            for desktop in sorted(session_dir.glob("*.desktop")):
                name = desktop.stem
                try:
                    text = desktop.read_text(errors="ignore")
                    for line in text.splitlines():
                        if line.startswith("Name="):
                            name = line.split("=", 1)[1].strip()
                            break
                except OSError:
                    pass
                sessions.append((name, desktop.name))
        return sessions

    def autologin_conflicts(self) -> list[dict[str, str]]:
        dm = self.detect_display_manager()
        if "sddm" not in dm.lower():
            return []
        entries: list[dict[str, str]] = []
        paths = [Path("/etc/sddm.conf"), *sorted(Path("/etc/sddm.conf.d").glob("*.conf"))]
        for path in paths:
            if not path.exists():
                continue
            text = path.read_text(errors="ignore")
            if "[Autologin]" not in text:
                continue
            section = re.search(r"(?ms)^\[Autologin\]\s*(.*?)(?:^\[|\Z)", text)
            body = section.group(1) if section else ""
            user = re.search(r"(?m)^\s*User\s*=\s*(.*)\s*$", body)
            session = re.search(r"(?m)^\s*Session\s*=\s*(.*)\s*$", body)
            entries.append({
                "path": str(path),
                "user": user.group(1).strip() if user else "",
                "session": session.group(1).strip() if session else "",
            })
        return entries

    def page_login(self) -> QWidget:
        page, layout = self.make_page(
            "Login",
            "SDDM autologin management. Detects conflicting config files and consolidates them into a single managed file.",
        )
        dm = self.detect_display_manager() or "not detected"
        is_sddm = "sddm" in dm.lower()

        status_card = self.card(layout, "Display manager and autologin status",
                                "Read-only detection from system config.")
        self.display_manager_label = QLabel(dm)
        self.autologin_state_label = QLabel()
        self.autologin_user_label = QLabel()
        self.autologin_session_label = QLabel()
        self.autologin_file_label = QLabel()
        for title, subtitle, label in [
            ("Display manager", "System display manager", self.display_manager_label),
            ("Autologin", "Enabled, disabled, or conflicting", self.autologin_state_label),
            ("Autologin user", "Configured user", self.autologin_user_label),
            ("Autologin session", "Configured session file", self.autologin_session_label),
            ("Config file(s)", "Files containing [Autologin] sections", self.autologin_file_label),
        ]:
            label.setWordWrap(True)
            self.row(status_card, title, subtitle, label)

        if not is_sddm:
            note = QLabel(f"Display manager is {dm}, not SDDM. Autologin controls below are SDDM-specific. "
                          "For other display managers, use their native configuration tools.")
            note.setObjectName("pageSub")
            note.setWordWrap(True)
            layout.addWidget(note)

        self.polkit_label = QLabel()
        self.row(status_card, "Polkit policy", "Required for GUI autologin changes", self.polkit_label)

        conflicts_card = self.card(
            layout,
            "Autologin conflicts",
            "Files with [Autologin] sections. Multiple files can conflict — only one managed file should exist.",
        )
        self.autologin_conflicts_list = QListWidget()
        self.autologin_conflicts_list.setMinimumHeight(100)
        conflicts_card.addWidget(self.autologin_conflicts_list)
        self.conflict_detail_label = QLabel()
        self.conflict_detail_label.setObjectName("pageSub")
        self.conflict_detail_label.setWordWrap(True)
        conflicts_card.addWidget(self.conflict_detail_label)

        control_card = self.card(
            layout,
            "Manage autologin",
            "Consolidates all [Autologin] sections into one managed file and removes conflicts. "
            "Other settings (theme, display, etc.) in those files are preserved.",
        )
        self.row(control_card, "User", "Linux account to log in automatically", self.line("__login_user"))
        session_row = QHBoxLayout()
        session_row.addWidget(QLabel("Session"))
        self.session_combo = QComboBox()
        self.session_combo.setMinimumWidth(300)
        for name, filename in self.available_sessions():
            self.session_combo.addItem(f"{name}  ({filename})", filename)
        session_row.addWidget(self.session_combo, 1)
        control_card.addLayout(session_row)

        self.login_feedback = QLabel("\n")
        self.login_feedback.setObjectName("loginFeedback")
        self.login_feedback.setWordWrap(True)
        self.login_feedback.setMinimumHeight(80)
        self.login_feedback.setStyleSheet("padding: 8px; background: rgba(255,255,255,10); border-radius: 6px;")
        control_card.addWidget(self.login_feedback)
        self.add_page_actions(page, [
            ("Refresh Login Status", self.refresh_login, False, "Re-read SDDM autologin state and conflicts."),
            ("Open SDDM Config Folder", lambda: self.open_folder("/etc/sddm.conf.d"), False, "Open SDDM config files in Dolphin."),
            ("Disable Autologin", self.disable_autologin, False, "Disable the managed SDDM autologin entry."),
            ("Enable & Consolidate Autologin", self.enable_autologin, True, "Merge conflicting SDDM autologin settings into one managed file."),
        ])
        return page

    def page_backup(self) -> QWidget:
        page, layout = self.make_page(
            "Backup & Recovery",
            "Restore previous Mango configs, create manual checkpoints, or reset to the known working baseline.",
        )
        c = self.card(
            layout,
            "Mango config backups",
            "Backups are created before the settings app writes ~/.config/mango/config.conf.",
        )
        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(260)
        c.addWidget(self.backup_list)

        row = QHBoxLayout()
        for text, action, primary in [
            ("Refresh", self.refresh_backups, False),
            ("Create checkpoint", self.create_checkpoint, True),
            ("Restore selected", self.restore_selected_backup, False),
            (
                "Open backups folder",
                lambda: self.open_folder(str(BACKUP_ROOT)),
                False,
            ),
        ]:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("primary")
            btn.clicked.connect(action)
            row.addWidget(btn)
        row.addStretch(1)
        c.addLayout(row)

        baseline = self.card(
            layout,
            "Known working baseline",
            "Use this if experimentation breaks Mango. A backup is created before reset.",
        )
        self.baseline_path_label = QLabel(
            str(PROJECT / "configs/mango/config.conf.working-20260516")
        )
        self.baseline_path_label.setObjectName("pageSub")
        baseline.addWidget(self.baseline_path_label)
        row2 = QHBoxLayout()
        export_btn = QPushButton("Export current as project baseline")
        export_btn.clicked.connect(self.export_current_baseline)
        reset_btn = QPushButton("Reset to project baseline")
        reset_btn.clicked.connect(self.reset_to_project_baseline)
        row2.addWidget(export_btn)
        row2.addWidget(reset_btn)
        row2.addStretch(1)
        baseline.addLayout(row2)

        note = QLabel(
            "Recovery rule: every restore/reset first creates another backup of the current file, "
            "so you can undo the undo."
        )
        note.setObjectName("pageSub")
        note.setWordWrap(True)
        baseline.addWidget(note)
        return page

    def page_tools(self) -> QWidget:
        page, layout = self.make_page(
            "Tools",
            "KDE/Qt workstation tools with scope labels so Plasma-only settings are not confused with Mango settings.",
        )
        c = self.card(layout, "Application launchers", "Normal workstation apps. These do not change Mango compositor settings.")
        tools = [
            ("Dolphin", "File manager / global XDG folders", ["env", "QT_QPA_PLATFORMTHEME=qt6ct", "QT_QPA_PLATFORMTHEME_QT6=qt6ct", "dolphin"]),
            ("Text editor", "Uses your default text editor via xdg-open", ["xdg-open", str(HOME / ".config/mimeapps.list")]),
            ("Kate", "Explicit KDE editor launcher", ["kate"]),
            ("Okular", "PDF viewer", ["okular"]),
            ("Gwenview", "Image viewer", ["gwenview"]),
            ("Ark", "Archive manager", ["ark"]),
            ("KWalletManager", "KDE wallet manager; affects KDE wallet", ["kwalletmanager5"]),
            ("Flatseal", "Flatpak permissions", ["flatseal"]),
            ("Blueman", "Bluetooth manager; global/user Bluetooth", ["blueman-manager"]),
            ("Audio", "PipeWire/PulseAudio mixer", ["pavucontrol"]),
            ("PipeWire graph", "PipeWire node graph", ["qpwgraph"]),
            ("Printer settings", "CUPS/system printer config", ["system-config-printer"]),
            ("GParted", "Disk partitions; admin/system", ["gparted"]),
            ("Region screenshot", "Mango grim/slurp/swappy workflow", [str(HOME / ".local/bin/dms-region-screenshot-edit")]),
        ]
        grid = QGridLayout()
        for i, (name, scope, command) in enumerate(tools):
            btn = QPushButton(f"{name}\n{scope}")
            btn.clicked.connect(lambda _=False, c=command: self.detach(c))
            grid.addWidget(btn, i // 3, i % 3)
        c.addLayout(grid)

        settings = self.card(
            layout,
            "External KDE/System settings",
            "Scope labels explain whether the tool affects Mango, global XDG/system config, KDE apps only, or Plasma-only settings.",
        )
        for title, scope, action in [
            (
                "Default Applications",
                "Global XDG MIME defaults. Affects Mango apps and portals; safe to use, but this app's Default Apps page is clearer.",
                lambda: self.launch_kde_module("componentchooser", "kcm_componentchooser"),
            ),
            (
                "SDDM Login Screen",
                "System SDDM config. Affects login manager globally; requires admin permission.",
                lambda: self.launch_kde_module("kcm_sddm", "kcm_sddm"),
            ),
            (
                "Autostart",
                "Mixed scope. Desktop entries affect Mango if XDG autostart is honored; Plasma-only entries may not. Prefer this app's Startup page.",
                lambda: self.launch_kde_module("kcm_autostart", "kcm_autostart"),
            ),
            (
                "Colors/Appearance",
                "Mostly KDE/Plasma/KDE-app settings. Mango/DMS theming still comes from DMS Matugen export and qtct configs.",
                lambda: self.launch_kde_module("kcm_colors", "kcm_colors"),
            ),
        ]:
            row = SettingRow(title, scope)
            btn = QPushButton("Open")
            btn.clicked.connect(action)
            row.add_control(btn)
            settings.addWidget(row)
        note = QLabel(
            "KDE modules are launched with QT_QPA_PLATFORMTHEME=qt6ct/QT_QPA_PLATFORMTHEME_QT6=qt6ct to reduce white/unthemed windows under Mango. If a module changes only Plasma/KWin state, it is not a Mango control."
        )
        note.setObjectName("pageSub")
        note.setWordWrap(True)
        settings.addWidget(note)
        return page

    def refresh_all(self) -> None:
        self.cfg.reload()
        self.refresh_status()
        self.refresh_first_run()
        self.refresh_controls()
        self.refresh_keyboard_specials()
        self.refresh_keybindings()
        self.refresh_window_rules()
        self.refresh_startup()
        self.refresh_services()
        self.refresh_portals()
        self.refresh_theme_bridge()
        self.refresh_font_bridge()
        self.refresh_default_apps()
        self.refresh_screenshots()
        self.refresh_remote_desktop()
        self.refresh_login()
        self.refresh_backups()

    def refresh_status(self) -> None:
        self.session_label.setText(
            f"Session: {os.environ.get('XDG_CURRENT_DESKTOP', 'unset')} / {os.environ.get('XDG_SESSION_DESKTOP', 'unset')}"
        )
        code, out = run_cmd(["mmsg", "-g", "-l"])
        self.layout_label.setText(
            f"Current layout: {out if code == 0 else 'unavailable'}"
        )
        code, out = run_cmd(["mmsg", "-g", "-k"])
        self.keyboard_label.setText(
            f"Keyboard layout: {out if code == 0 else 'unavailable'}"
        )

    # ------------------------------------------------------------------
    # First-run / system-setup helpers
    # ------------------------------------------------------------------

    def rpm_installed(self, pkg: str) -> bool:
        code, _ = run_cmd(["rpm", "-q", pkg], timeout=10)
        return code == 0

    def command_exists(self, name: str) -> bool:
        return shutil.which(name) is not None

    def user_unit_exists(self, unit: str) -> bool:
        code, _ = run_cmd(["systemctl", "--user", "list-unit-files", unit], timeout=8)
        return code == 0

    def first_run_blockers(self) -> list[str]:
        blockers: list[str] = []
        if not self.command_exists("mango"):
            blockers.append("Mango is not installed yet.")
        if not MANGO_SESSION_FILE.exists():
            blockers.append("Mango session entry is missing (/usr/share/wayland-sessions/mango.desktop).")
        if not self.command_exists("dms"):
            blockers.append("DMS is not installed yet.")
        if not self.command_exists("qs") and not self.command_exists("quickshell"):
            blockers.append("Quickshell is missing, so DMS cannot launch its shell UI.")
        if self.missing_portal_packages():
            blockers.append("Required portal packages are still missing.")
        if self.dms_startup_ownership_conflict():
            blockers.append("DMS startup ownership conflict: dms.service is enabled while Mango also starts dms run.")
        return blockers

    def show_install_prereq_help(self) -> None:
        self.say(
            "Install prerequisites from your current working session before switching to Mango.\n\n"
            "Fedora DMS install (official DMS docs):\n"
            "  sudo dnf copr enable avengemedia/dms\n"
            "  sudo dnf install dms\n\n"
            "Fedora Mango install (official Mango docs):\n"
            "  sudo dnf install --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release\n"
            "  sudo dnf install mangowm\n\n"
            "Then return here, refresh status, apply the baseline, and only switch to Mango after all hard prerequisites are green."
        )

    def dms_service_enabled(self) -> bool:
        code, _ = run_cmd(["systemctl", "--user", "is-enabled", "dms.service"], timeout=8)
        return code == 0

    def dms_startup_ownership_conflict(self) -> bool:
        mango_line = "exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run"
        return self.dms_service_enabled() and mango_line in self.cfg.text

    def fix_dms_startup_ownership(self) -> None:
        if not self.dms_startup_ownership_conflict():
            self.say("DMS startup ownership already looks safe for Mango.")
            return
        if QMessageBox.question(
            self,
            "Fix DMS startup ownership",
            "Disable dms.service autostart so Mango's explicit dms run line is the only DMS startup path?\n\nThis does not stop your current session immediately. It prevents future double-start conflicts.",
        ) != QMessageBox.StandardButton.Yes:
            self.say("Cancelled DMS startup ownership fix.")
            return
        code, out = run_cmd(["systemctl", "--user", "disable", "dms.service"], timeout=25)
        if code == 0:
            self.say("OK: Disabled dms.service autostart for future sessions. Mango will use its explicit dms run startup line.\n\nLog out/in later to verify the new startup path.\n" + out)
        else:
            self.say("FAIL: Could not disable dms.service autostart.\n\nDo not switch to Mango yet. Run manually from your current session:\n  systemctl --user disable dms.service\n\nDetails:\n" + out)
        self.refresh_first_run()

    def env_file_status(self) -> dict[str, tuple[bool, str]]:
        """Return {var: (ok, current_or_missing)} for required env vars."""
        result: dict[str, tuple[bool, str]] = {}
        if not QT_ENV_FILE.exists():
            for var, expected in ENV_REQUIRED_VARS.items():
                result[var] = (False, "env file missing")
            return result
        text = QT_ENV_FILE.read_text(errors="ignore")
        for var, expected in ENV_REQUIRED_VARS.items():
            m = re.search(rf"(?m)^{re.escape(var)}\s*=\s*(.*)\s*$", text)
            if m:
                actual = m.group(1).strip()
                result[var] = (actual == expected, actual)
            else:
                result[var] = (False, "not set")
        return result

    def missing_portal_packages(self) -> list[tuple[str, str]]:
        return [(pkg, desc) for pkg, desc in PORTAL_PACKAGES if not self.rpm_installed(pkg)]

    def all_portals_ok(self) -> bool:
        return len(self.missing_portal_packages()) == 0

    def consolidate_script_ok(self) -> tuple[bool, str]:
        if not CONSOLIDATE_SCRIPT.exists():
            return False, "Script missing — run Apply Baseline or reinstall"
        try:
            code, out = run_cmd(["python3", str(CONSOLIDATE_SCRIPT)], timeout=5)
            # Usage error (exit 2) means the script exists and is runnable
            return True, "OK"
        except Exception as exc:
            return False, str(exc)

    def autologin_status(self) -> tuple[str, str]:
        """Return (state_label, detail) for SDDM autologin."""
        conflicts = self.autologin_conflicts()
        active = next((e for e in reversed(conflicts) if e.get("user") or e.get("session")), None)
        if not active:
            return "Disabled", "No autologin configured"
        if len(conflicts) > 1:
            return "Conflicting", f"{len(conflicts)} files have [Autologin]"
        if active.get("session") != "mango.desktop":
            return "Wrong session", f"Session is {active.get('session', '?')}"
        return "OK", f"User {active.get('user')} → {active.get('session')}"

    def install_portals(self) -> None:
        missing = self.missing_portal_packages()
        if not missing:
            self.say("All portal packages are already installed.")
            return
        pkg_list = " ".join(pkg for pkg, _ in missing)
        if QMessageBox.question(
            self,
            "Install portal packages",
            f"These portal packages are missing:\n\n" + "\n".join(f"  • {pkg} — {desc}" for pkg, desc in missing)
            + f"\n\nInstall them now with dnf?\n\nCommand: pkexec dnf install -y {pkg_list}",
        ) != QMessageBox.StandardButton.Yes:
            self.say("Cancelled portal installation.")
            return
        self.set_working("Installing portal packages via dnf...")

        def do_install() -> None:
            code, out = run_cmd(["pkexec", "dnf", "install", "-y"] + [pkg for pkg, _ in missing], timeout=300)
            if code == 0:
                self.say(f"OK: Portal packages installed.\n{out}")
            else:
                self.say(f"FAIL: Portal installation failed (exit {code}).\n{out}")
            self.refresh_first_run()

        QTimer.singleShot(100, do_install)

    def fix_environment(self) -> None:
        if QMessageBox.question(
            self,
            "Fix environment",
            f"Rewrite {QT_ENV_FILE} with the required toolkit variables?\n\n"
            "This writes only stable Qt/Electron toolkit variables. It does not hardcode dynamic session values like WAYLAND_DISPLAY or compositor identity.",
        ) != QMessageBox.StandardButton.Yes:
            self.say("Cancelled environment fix.")
            return
        self.set_working("Writing environment file...")
        backup = BACKUP_ROOT / dt.datetime.now().strftime("%Y%m%d-%H%M%S") / "environment.d" / "90-dms-kde-qt.conf"
        backup.parent.mkdir(parents=True, exist_ok=True)
        if QT_ENV_FILE.exists():
            shutil.copy2(QT_ENV_FILE, backup)
        QT_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# DMS KDE Workstation: toolkit environment for Mango + DMS.",
            "# Keep only stable toolkit variables here.",
            "# Do NOT hardcode dynamic session variables like WAYLAND_DISPLAY here.",
            "# Do NOT hardcode compositor identity here when multiple sessions may exist.",
            "# Mango is responsible for its runtime session environment.",
        ]
        for var, value in ENV_REQUIRED_VARS.items():
            lines.append(f"{var}={value}")
        QT_ENV_FILE.write_text("\n".join(lines) + "\n")
        self.say(f"OK: Environment file written.\nPrevious version backed up to: {backup}\n\nLog out and back in for all services to pick up the new values.")
        self.refresh_first_run()

    def first_run_apply_baseline(self) -> None:
        blockers = self.first_run_blockers()
        if blockers:
            self.say(
                "FAIL: First Run Setup is blocked.\n\n"
                + "Fix these first from your current working session:\n"
                + "\n".join(f"  • {item}" for item in blockers)
                + "\n\nUse 'Show Install Help' and 'Install Missing' where offered. Do not switch to Mango yet."
            )
            return
        if QMessageBox.question(
            self,
            "Apply First Run Setup",
            "Apply the full DMS Mango workstation baseline now?\n\nThis writes user config files and deploys helpers. Do this before your first Mango login.",
        ) != QMessageBox.StandardButton.Yes:
            self.say("Cancelled.")
            return
        self.set_working("Applying workstation baseline...")

        def do_apply() -> None:
            self.run_baseline_script(["--apply"], "Applied workstation baseline")

        QTimer.singleShot(100, do_apply)

    def first_run_fix_login(self) -> None:
        """Jump to the Login page so the user can use the proper controls there."""
        self.stack.setCurrentIndex(self.login_page_index)
        self.sidebar.setCurrentRow(self.login_page_index)
        self.refresh_login()
        self.say("Switched to Login page. Use 'Enable & Consolidate Autologin' there.")

    # ------------------------------------------------------------------

    def refresh_first_run(self) -> None:
        if not hasattr(self, "first_run_rows"):
            return
        mango_ok = self.command_exists("mango") and MANGO_SESSION_FILE.exists()
        if self.command_exists("mango") and not MANGO_SESSION_FILE.exists():
            mango_detail = "mango installed, but session entry missing"
        else:
            mango_detail = "OK" if mango_ok else "Install mangowm first"
        self._update_first_run_row("mango", mango_ok, mango_detail)

        dms_ok = self.command_exists("dms")
        self._update_first_run_row("dms", dms_ok, "OK" if dms_ok else "Install DMS first")

        quickshell_ok = self.command_exists("qs") or self.command_exists("quickshell")
        self._update_first_run_row("quickshell", quickshell_ok, "OK" if quickshell_ok else "Missing qs/quickshell")

        # Environment
        env_status = self.env_file_status()
        env_all_ok = all(ok for ok, _ in env_status.values())
        env_text = "OK" if env_all_ok else f"{sum(1 for ok, _ in env_status.values() if ok)}/{len(env_status)} vars OK"
        self._update_first_run_row("env", env_all_ok, env_text)

        # Portals
        missing_portals = self.missing_portal_packages()
        portal_text = "OK" if not missing_portals else f"{len(missing_portals)} missing"
        self._update_first_run_row("portals", not missing_portals, portal_text)

        # Baseline files
        baseline_ok = (
            MANGO_CONFIG.exists()
            and PORTAL_OVERRIDE.exists()
            and PORTAL_CONFIG.exists()
            and POST_STARTUP_HELPER.exists()
            and STARTUP_JSON.exists()
            and SETTINGS_BIN.exists()
            and SETTINGS_AUTOSTART.exists()
        )
        self._update_first_run_row("baseline", baseline_ok, "OK" if baseline_ok else "Missing files")

        # DMS startup line in Mango config
        mango_line = "exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run"
        dms_startup_ok = mango_line in self.cfg.text
        self._update_first_run_row("dms_startup", dms_startup_ok, "OK" if dms_startup_ok else "Missing exec-once")

        ownership_ok = not self.dms_startup_ownership_conflict()
        ownership_detail = "OK" if ownership_ok else "dms.service enabled alongside Mango dms run"
        self._update_first_run_row("dms_ownership", ownership_ok, ownership_detail)

        # Autologin
        login_state, login_detail = self.autologin_status()
        login_ok = login_state == "OK"
        self._update_first_run_row("login", login_ok, f"{login_state}: {login_detail}")

        # Consolidate script
        script_ok, script_detail = self.consolidate_script_ok()
        self._update_first_run_row("script", script_ok, script_detail)

        # Theme export
        theme_export_done = (HOME / ".local/share/color-schemes/DankMatugen.colors").exists()
        self._update_first_run_row("theme", theme_export_done, "OK" if theme_export_done else "Not exported yet")

        # Overall
        blockers = self.first_run_blockers()
        all_ok = not blockers and env_all_ok and not missing_portals and baseline_ok and dms_startup_ok and login_ok and script_ok
        if blockers:
            self.first_run_overall_label.setText(
                "BLOCKED — do not switch to Mango yet. Finish the hard prerequisites first."
            )
        else:
            self.first_run_overall_label.setText(
                f"Overall: {'Ready for first Mango login after apply' if all_ok else 'Some items still need attention before session switch'}"
            )
        self.first_run_overall_label.setStyleSheet(f"color: {ACCENT if all_ok else WARNING}; font-weight: 650; font-size: 18px;")

    def _update_first_run_row(self, key: str, ok: bool, detail: str) -> None:
        status_label = self.first_run_rows.get(key)
        if status_label is None:
            return
        status_label.setText(f"{'OK' if ok else 'NEEDS FIX'} — {detail}")
        status_label.setStyleSheet(f"color: {ACCENT if ok else WARNING};")

    def run_baseline_script(self, args: list[str], title: str) -> None:
        if not APPLY_BASELINE_SCRIPT.exists():
            self.say(f"FAIL: Baseline script not found: {APPLY_BASELINE_SCRIPT}\nDo not switch to Mango. Fix the repo checkout first.")
            return
        code, out = run_cmd([str(APPLY_BASELINE_SCRIPT), *args], timeout=180)
        if code == 0:
            self.say(
                f"OK: {title}\n{out}\n\n"
                "Next: stay in your current working session, refresh status, and only switch to Mango after the blockers are gone and the baseline files are present."
            )
        else:
            self.say(
                f"FAIL: {title} exited with code {code}.\n{out}\n\n"
                "Do not switch to Mango. Return to the missing prerequisite or failing step, fix it from your current working session, then run this again."
            )
        self.refresh_first_run()

    def dry_run_first_run_setup(self) -> None:
        self.set_working("Running baseline dry-run...")

        def do_dry_run() -> None:
            self.run_baseline_script([], "Baseline dry-run")

        QTimer.singleShot(100, do_dry_run)

    def refresh_controls(self) -> None:
        for key, widget in self.controls.items():
            if key.startswith("__"):
                continue
            if isinstance(widget, QCheckBox):
                widget.setChecked(self.cfg.get_bool(key))
            elif isinstance(widget, QComboBox):
                value = self.cfg.get(key)
                if key == "tag_animation_direction":
                    value = "horizontal" if value == "1" else "vertical"
                idx = widget.findText(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QLineEdit):
                widget.setText(self.cfg.get(key))
            elif isinstance(widget, BezierCurveEditor):
                widget.setText(self.cfg.get(key, "0.46,1.0,0.29,1"))
            elif isinstance(widget, QSlider):
                scale = int(widget.property("scale") or 1)
                with contextlib.suppress(ValueError):
                    widget.setValue(int(float(self.cfg.get(key, "0")) * scale))
        idx = self.controls["__default_layout"].findText("Scroller")
        self.controls["__default_layout"].setCurrentIndex(max(0, idx))
        self.controls["__login_user"].setText(os.environ.get("USER", ""))

    def refresh_keyboard_specials(self) -> None:
        self.alt_shift.setChecked(
            self.cfg.has_line("bind=ALT,shift_l,switch_keyboard_layout")
            and self.cfg.has_line("bind=ALT,shift_r,switch_keyboard_layout")
        )
        self.direct_layouts.setChecked(
            self.cfg.has_line("bind=SUPER+CTRL,1,switch_keyboard_layout,0")
            and self.cfg.has_line("bind=SUPER+CTRL,2,switch_keyboard_layout,1")
        )

    def binding_lines(self) -> list[str]:
        return [line for line in self.cfg.text.splitlines() if line.strip().startswith(("bind=", "axisbind="))]

    def binding_key(self, line: str) -> str:
        try:
            left = line.split("=", 1)[1]
            parts = left.split(",")
            return ",".join(parts[:2]).strip().lower()
        except Exception:
            return line.strip().lower()

    def duplicate_bindings(self) -> dict[str, list[str]]:
        seen: dict[str, list[str]] = {}
        for line in self.binding_lines():
            seen.setdefault(self.binding_key(line), []).append(line)
        return {k: v for k, v in seen.items() if len(v) > 1}

    def has_binding_conflict(self, line: str) -> bool:
        key = self.binding_key(line)
        return any(self.binding_key(existing) == key for existing in self.binding_lines())

    def keybinding_display(self, line: str) -> str:
        kind, parts = self.parse_binding_line(line)
        if len(parts) < 3:
            return line
        mods, key = parts[0], parts[1]
        action = ",".join(parts[2:])
        prefix = "Wheel" if kind == "axisbind" else "Key"
        return f"{prefix}: {mods}+{key}  →  {action}"

    def parse_binding_line(self, line: str) -> tuple[str, list[str]]:
        stripped = line.strip()
        if stripped.startswith("axisbind="):
            return "axisbind", stripped.split("=", 1)[1].split(",")
        if stripped.startswith("bind="):
            return "bind", stripped.split("=", 1)[1].split(",")
        return "", []

    def refresh_keybindings(self) -> None:
        if not hasattr(self, "keybinds_list"):
            return
        duplicates = self.duplicate_bindings()
        duplicate_keys = set(duplicates)
        self._keybind_items = []
        for line in self.binding_lines():
            display = self.keybinding_display(line)
            if self.binding_key(line) in duplicate_keys:
                display = "DUPLICATE  " + display
            self._keybind_items.append((line, display))
        # Keep current sort mode or default to file order
        active_sort = None
        for btn in getattr(self, "keybind_sort_buttons", []):
            if btn.isChecked():
                active_sort = btn.property("sort_mode")
                break
        if active_sort:
            self._apply_keybind_sort(active_sort)
        self._filter_keybinds(getattr(self, "keybind_search", QLineEdit()).text())
        if duplicates:
            text = "Duplicate Mango shortcuts detected. Remove them before trusting this session:\n" + "\n".join(f"- {k}: {len(v)} entries" for k, v in duplicates.items())
        else:
            text = "No duplicate Mango bind/axisbind shortcuts detected. This page edits Mango compositor bindings only, not DMS shortcuts."
        self.keybind_duplicate_label.setText(text)

    def _filter_keybinds(self, query: str) -> None:
        """Rebuild the visible list from _keybind_items matching the search query."""
        if not hasattr(self, "keybinds_list"):
            return
        self.keybinds_list.clear()
        q = query.strip().lower()
        for raw, display in self._keybind_items:
            if q and q not in display.lower() and q not in raw.lower():
                continue
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, raw)
            self.keybinds_list.addItem(item)

    def _sort_keybinds(self, mode: str) -> None:
        """Toggle sort buttons and re-sort _keybind_items, then re-filter."""
        for btn in getattr(self, "keybind_sort_buttons", []):
            btn.setChecked(btn.property("sort_mode") == mode)
        self._apply_keybind_sort(mode)
        self._filter_keybinds(getattr(self, "keybind_search", QLineEdit()).text())

    def _apply_keybind_sort(self, mode: str) -> None:
        if mode == "alpha":
            self._keybind_items.sort(key=lambda t: t[1].lower())
        elif mode == "mod":
            def mod_key(t: tuple[str, str]) -> str:
                _, parts = self.parse_binding_line(t[0])
                return parts[0].lower() if parts else ""
            self._keybind_items.sort(key=mod_key)
        elif mode == "action":
            def action_key(t: tuple[str, str]) -> str:
                _, parts = self.parse_binding_line(t[0])
                return ",".join(parts[2:]).lower() if len(parts) > 2 else ""
            self._keybind_items.sort(key=action_key)

    def selected_modifiers(self) -> str:
        mods = []
        for label, widget in [
            ("SUPER", self.key_mod_super),
            ("CTRL", self.key_mod_ctrl),
            ("ALT", self.key_mod_alt),
            ("SHIFT", self.key_mod_shift),
        ]:
            if widget.isChecked():
                mods.append(label)
        return "+".join(mods) if mods else "NONE"

    def set_modifier_checks(self, modifiers: str) -> None:
        values = {m.strip().upper() for m in modifiers.split("+") if m.strip()}
        self.key_mod_super.setChecked("SUPER" in values)
        self.key_mod_ctrl.setChecked("CTRL" in values or "CONTROL" in values)
        self.key_mod_alt.setChecked("ALT" in values)
        self.key_mod_shift.setChecked("SHIFT" in values)

    def build_keybinding_line(self) -> str | None:
        key = self.keybind_key.text().strip()
        if not key:
            self.say("Choose a key first.")
            return None
        modifiers = self.selected_modifiers()
        kind = self.keybind_kind.currentData()
        if kind == "spawn":
            command = self.keybind_command.text().strip()
            if not command:
                self.say("Run command shortcut needs a command.")
                return None
            return f"bind={modifiers},{key},spawn,{command}"
        if kind == "axis":
            action = self.keybind_action.currentData() or "focusstack,next"
            if str(action).startswith("spawn,"):
                return f"axisbind={modifiers},{key},{str(action)}"
            return f"axisbind={modifiers},{key},{action}"
        action = str(self.keybind_action.currentData() or "")
        extra = self.keybind_command.text().strip()
        if action.startswith("spawn,"):
            return f"bind={modifiers},{key},{action}"
        if extra:
            return f"bind={modifiers},{key},{action},{extra}"
        return f"bind={modifiers},{key},{action}"

    def add_keybinding_from_controls(self) -> None:
        line = self.build_keybinding_line()
        if not line:
            return
        if self.has_binding_conflict(line):
            self.say("FAIL: A Mango shortcut with the same modifiers+key already exists. Remove the old binding first so this app does not create conflicts.")
            return
        self.cfg.ensure_line(line, "# DMS KDE Workstation Mango window controls")
        self.refresh_keybindings()
        self.say(f"Added shortcut: {line}")

    def clear_keybinding_editor(self) -> None:
        self.key_mod_super.setChecked(True)
        self.key_mod_ctrl.setChecked(False)
        self.key_mod_alt.setChecked(False)
        self.key_mod_shift.setChecked(False)
        self.keybind_key.clear()
        self.keybind_kind.setCurrentIndex(0)
        self.keybind_action.setCurrentIndex(0)
        self.keybind_command.clear()

    def load_selected_keybinding_into_editor(self, item: QListWidgetItem) -> None:
        if not hasattr(self, "keybind_key"):
            return
        line = item.data(Qt.ItemDataRole.UserRole)
        kind, parts = self.parse_binding_line(str(line))
        if len(parts) < 3:
            return
        self.set_modifier_checks(parts[0])
        self.keybind_key.setText(parts[1])
        action = ",".join(parts[2:])
        if kind == "axisbind":
            idx = self.keybind_kind.findData("axis")
            self.keybind_kind.setCurrentIndex(max(0, idx))
        elif action.startswith("spawn,"):
            idx = self.keybind_kind.findData("spawn")
            self.keybind_kind.setCurrentIndex(max(0, idx))
            self.keybind_command.setText(action.split(",", 1)[1] if "," in action else "")
            return
        else:
            idx = self.keybind_kind.findData("bind-action")
            self.keybind_kind.setCurrentIndex(max(0, idx))
        action_idx = self.keybind_action.findData(action)
        if action_idx >= 0:
            self.keybind_action.setCurrentIndex(action_idx)
            self.keybind_command.clear()
        else:
            base, _, extra = action.partition(",")
            action_idx = self.keybind_action.findData(base)
            if action_idx >= 0:
                self.keybind_action.setCurrentIndex(action_idx)
                self.keybind_command.setText(extra)

    def add_keybinding_line(self) -> None:
        line = self.keybind_line.text().strip()
        if not line:
            return
        if not line.startswith(("bind=", "axisbind=")):
            self.say("Binding must start with bind= or axisbind=")
            return
        if self.has_binding_conflict(line):
            self.say("FAIL: A Mango shortcut with the same modifiers+key already exists. Remove the old binding first so this app does not create conflicts.")
            return
        self.cfg.ensure_line(line, "# DMS KDE Workstation Mango window controls")
        self.keybind_line.clear()
        self.refresh_keybindings()
        self.say(f"Added raw shortcut: {line}")

    def remove_selected_keybinding(self) -> None:
        if not hasattr(self, "keybinds_list"):
            return
        selected = self.keybinds_list.selectedItems()
        if not selected:
            self.say("No shortcut selected.")
            return
        for item in selected:
            line = item.data(Qt.ItemDataRole.UserRole)
            self.cfg.remove_matching(rf"^\s*{re.escape(line)}\s*$")
        self.refresh_keybindings()

    def save_keybindings(self) -> None:
        if QMessageBox.question(self, "Save keybindings", "Backup Mango config and save keybinding changes?") != QMessageBox.StandardButton.Yes:
            return
        try:
            backup = self.cfg.save()
        except Exception as exc:
            self.say(f"FAIL: Could not save keybindings: {exc}")
            return
        self.say(f"Saved keybindings. Backup: {backup}")
        self.reload_mango()

    def focused_window_rule_target(self) -> dict[str, str]:
        code, out = run_cmd(["mmsg", "-g", "-c"], timeout=8)
        info = {"appid": "", "title": ""}
        if code != 0:
            return info
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            kind = parts[1].strip()
            value = parts[2].strip()
            if kind == "appid":
                info["appid"] = value
            elif kind == "title":
                info["title"] = value
        return info

    def parse_window_rule_line(self, line: str) -> dict[str, str]:
        raw = line.strip()
        if raw.startswith("windowrule="):
            raw = raw.split("=", 1)[1]
        data: dict[str, str] = {"__raw": raw}
        for part in raw.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            data[key.strip()] = value.strip()
        return data

    def build_window_rule_line(self) -> str | None:
        appid = self.window_rule_appid.text().strip() if hasattr(self, "window_rule_appid") else ""
        title = self.window_rule_title.text().strip() if hasattr(self, "window_rule_title") else ""
        if not appid and not title:
            self.say("FAIL: Window rule needs at least an App ID or Title match.")
            return None
        parts: list[str] = []
        if hasattr(self, "window_rule_enable_focused_opacity") and self.window_rule_enable_focused_opacity.isChecked():
            parts.append(f"focused_opacity:{self.window_rule_focused_opacity.value()/100:.2f}")
        if hasattr(self, "window_rule_enable_unfocused_opacity") and self.window_rule_enable_unfocused_opacity.isChecked():
            parts.append(f"unfocused_opacity:{self.window_rule_unfocused_opacity.value()/100:.2f}")
        for key, widget in getattr(self, "window_rule_toggles", {}).items():
            if widget.isChecked():
                parts.append(f"{key}:1")
        if appid:
            parts.append(f"appid:{appid}")
        if hasattr(self, "window_rule_enable_title") and self.window_rule_enable_title.isChecked() and title:
            parts.append(f"title:{title}")
        line = "windowrule=" + ",".join(parts)
        if hasattr(self, "window_rule_preview"):
            self.window_rule_preview.setText(line)
        return line

    def refresh_focused_window_rule_target(self) -> None:
        if not hasattr(self, "window_rule_focus_label"):
            return
        info = self.focused_window_rule_target()
        if info.get("appid") or info.get("title"):
            self.window_rule_focus_label.setText(
                f"Focused app ID: {info.get('appid') or 'unknown'}\nFocused title: {info.get('title') or 'unknown'}"
            )
        else:
            self.window_rule_focus_label.setText("Could not read focused window from Mango. Focus the target app and try again.")

    def apply_window_rule_target(self, info: dict[str, str]) -> None:
        if hasattr(self, "window_rule_appid"):
            self.window_rule_appid.setText(info.get("appid", ""))
        if hasattr(self, "window_rule_title"):
            self.window_rule_title.setText(info.get("title", ""))
        if hasattr(self, "window_rule_enable_title"):
            self.window_rule_enable_title.setChecked(False)
        self.refresh_focused_window_rule_target()
        self.build_window_rule_line()
        self.say(f"Captured window: {info.get('appid') or info.get('title')}")

    def use_focused_window_for_rule(self) -> None:
        info = self.focused_window_rule_target()
        if not info.get("appid") and not info.get("title"):
            self.say("FAIL: Could not capture focused window.")
            return
        self.apply_window_rule_target(info)

    def capture_window_rule_target_delayed(self) -> None:
        if hasattr(self, "window_rule_focus_label"):
            self.window_rule_focus_label.setText("Capture started. Switch to the target app now — this settings window will hide and capture in 3 seconds.")
        self.hide()
        def finish_capture() -> None:
            info = self.focused_window_rule_target()
            self.show()
            self.raise_()
            self.activateWindow()
            if not info.get("appid") and not info.get("title"):
                self.say("FAIL: Delayed capture could not read the target window.")
                self.refresh_focused_window_rule_target()
                return
            self.apply_window_rule_target(info)
        QTimer.singleShot(3000, finish_capture)

    def refresh_window_rules(self) -> None:
        self.refresh_focused_window_rule_target()
        if not hasattr(self, "window_rules_list"):
            return
        self.window_rules_list.clear()
        for line in self.cfg.text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("windowrule="):
                continue
            data = self.parse_window_rule_line(stripped)
            label_parts = []
            if data.get("appid"):
                label_parts.append(f"appid={data['appid']}")
            if data.get("title"):
                label_parts.append(f"title={data['title']}")
            if data.get("focused_opacity"):
                label_parts.append(f"focus={data['focused_opacity']}")
            if data.get("unfocused_opacity"):
                label_parts.append(f"unfocus={data['unfocused_opacity']}")
            label = " | ".join(label_parts) if label_parts else stripped
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, stripped)
            self.window_rules_list.addItem(item)
        self.build_window_rule_line()

    def load_selected_window_rule(self, item: QListWidgetItem) -> None:
        data = self.parse_window_rule_line(str(item.data(Qt.ItemDataRole.UserRole)))
        self.window_rule_appid.setText(data.get("appid", ""))
        self.window_rule_title.setText(data.get("title", ""))
        self.window_rule_enable_title.setChecked(bool(data.get("title", "")))
        focused = data.get("focused_opacity", "")
        unfocused = data.get("unfocused_opacity", "")
        self.window_rule_enable_focused_opacity.setChecked(bool(focused))
        self.window_rule_enable_unfocused_opacity.setChecked(bool(unfocused))
        if focused:
            with contextlib.suppress(ValueError):
                self.window_rule_focused_opacity.setValue(int(float(focused) * 100))
        if unfocused:
            with contextlib.suppress(ValueError):
                self.window_rule_unfocused_opacity.setValue(int(float(unfocused) * 100))
        for key, widget in self.window_rule_toggles.items():
            widget.setChecked(data.get(key) == "1")
        self.build_window_rule_line()

    def add_or_replace_window_rule(self) -> None:
        line = self.build_window_rule_line()
        if not line or not hasattr(self, "window_rules_list"):
            return
        new_data = self.parse_window_rule_line(line)
        replace_row = None
        for i in range(self.window_rules_list.count()):
            item = self.window_rules_list.item(i)
            old_data = self.parse_window_rule_line(str(item.data(Qt.ItemDataRole.UserRole)))
            if old_data.get("appid", "") == new_data.get("appid", "") and old_data.get("title", "") == new_data.get("title", ""):
                replace_row = i
                break
        label_parts = []
        if new_data.get("appid"):
            label_parts.append(f"appid={new_data['appid']}")
        if new_data.get("title"):
            label_parts.append(f"title={new_data['title']}")
        if new_data.get("focused_opacity"):
            label_parts.append(f"focus={new_data['focused_opacity']}")
        if new_data.get("unfocused_opacity"):
            label_parts.append(f"unfocus={new_data['unfocused_opacity']}")
        item = QListWidgetItem(" | ".join(label_parts) if label_parts else line)
        item.setData(Qt.ItemDataRole.UserRole, line)
        if replace_row is None:
            self.window_rules_list.addItem(item)
            self.say("Added window rule to pending list.")
        else:
            self.window_rules_list.takeItem(replace_row)
            self.window_rules_list.insertItem(replace_row, item)
            self.say("Replaced existing window rule in pending list.")

    def remove_selected_window_rule(self) -> None:
        if not hasattr(self, "window_rules_list"):
            return
        selected = self.window_rules_list.selectedItems()
        if not selected:
            self.say("No window rule selected.")
            return
        for item in selected:
            self.window_rules_list.takeItem(self.window_rules_list.row(item))
        self.say("Removed selected window rule from pending list.")

    def save_window_rules(self) -> None:
        if not hasattr(self, "window_rules_list"):
            return
        if QMessageBox.question(self, "Save window rules", "Backup Mango config and save window rule changes?") != QMessageBox.StandardButton.Yes:
            return
        rules = [str(self.window_rules_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.window_rules_list.count())]
        self.cfg.remove_matching(r"^\s*windowrule=")
        marker = "# layer rule"
        block = ("\n".join(rules) + "\n") if rules else ""
        if marker in self.cfg.text:
            idx = self.cfg.text.find(marker)
            self.cfg.text = self.cfg.text[:idx].rstrip() + "\n\n" + block + self.cfg.text[idx:]
        elif block:
            self.cfg.text = self.cfg.text.rstrip() + "\n\n" + block
        try:
            backup = self.cfg.save()
        except Exception as exc:
            self.say(f"FAIL: Could not save window rules: {exc}")
            return
        self.say(f"Saved window rules. Backup: {backup}")
        self.reload_mango()

    def refresh_portals(self) -> None:
        if hasattr(self, "portal_rows"):
            for unit, label in self.portal_rows:
                code, _ = run_cmd(["systemctl", "--user", "is-active", "--quiet", unit], timeout=6)
                label.setText("active" if code == 0 else "inactive")
                label.setStyleSheet(f"color: {ACCENT if code == 0 else WARNING};")
        if hasattr(self, "portal_files_label"):
            paths = [
                HOME / ".config/systemd/user/xdg-desktop-portal.service",
                HOME / ".config/xdg-desktop-portal/mango-portals.conf",
                Path("/usr/share/xdg-desktop-portal/mango-portals.conf"),
            ]
            self.portal_files_label.setText("\n".join(f"{'OK' if p.exists() else 'MISSING'}  {p}" for p in paths))

    def restart_portals(self) -> None:
        code, out = run_cmd(["systemctl", "--user", "restart", "xdg-desktop-portal.service", "xdg-desktop-portal-wlr.service", "xdg-desktop-portal-gtk.service"], timeout=25)
        if code == 0:
            self.say("Portals restarted successfully.")
        else:
            self.say(f"FAIL: Portal restart failed (exit {code}). {out}\nCheck: systemctl --user status xdg-desktop-portal.service")
        QTimer.singleShot(900, self.refresh_portals)

    def test_file_chooser(self) -> None:
        self.detach(["bash", "-lc", "zen-browser about:blank >/dev/null 2>&1 || xdg-open https://example.com"])
        self.say("Opened browser test target. Use upload/download dialog to verify portal file chooser.")

    def system_fonts(self) -> list[str]:
        fonts: list[str] = []
        with contextlib.suppress(Exception):
            import subprocess
            code, out = run_cmd(["fc-list", "--format=%{family}\n"], timeout=10)
            if code == 0:
                seen: set[str] = set()
                for line in sorted(out.splitlines()):
                    name = line.strip()
                    if name and name not in seen:
                        seen.add(name)
                        fonts.append(name)
        return fonts

    def current_font_state(self) -> dict[str, str]:
        state: dict[str, str] = {}
        kg = HOME / ".config/kdeglobals"
        if kg.exists():
            text = kg.read_text(errors="ignore")
            m = re.search(r"(?m)^font=(.*)$", text)
            if m:
                parts = m.group(1).split(",")
                if parts:
                    state["kdeglobals"] = parts[0].strip()
        for gtk in [HOME / ".config/gtk-3.0/settings.ini", HOME / ".config/gtk-4.0/settings.ini"]:
            if gtk.exists():
                text = gtk.read_text(errors="ignore")
                m = re.search(r"(?m)^gtk-font-name\s*=\s*(.*)$", text)
                if m:
                    parts = m.group(1).split(",")
                    state[gtk.parent.name] = parts[0].strip()
        for qt in [HOME / ".config/qt5ct/qt5ct.conf", HOME / ".config/qt6ct/qt6ct.conf"]:
            if qt.exists():
                text = qt.read_text(errors="ignore")
                m = re.search(r'(?m)^general="?(.*?)"?$', text)
                if m:
                    parts = m.group(1).split(",")
                    if parts:
                        state[qt.parent.name] = parts[0].strip()
        dms = HOME / ".config/DankMaterialShell/settings.json"
        if dms.exists():
            with contextlib.suppress(Exception):
                data = json.loads(dms.read_text())
                if data.get("fontFamily"):
                    state["dms"] = data["fontFamily"]
        return state

    def refresh_font_bridge(self) -> None:
        if not hasattr(self, "font_family_combo"):
            return
        fonts = self.system_fonts()
        current = self.current_font_state()
        current_family = current.get("dms", current.get("kdeglobals", ""))
        current_size = "12"
        kg = HOME / ".config/kdeglobals"
        if kg.exists():
            m = re.search(r"(?m)^font=.*?,(\d+),", kg.read_text(errors="ignore"))
            if m:
                current_size = m.group(1)
        self.font_family_combo.blockSignals(True)
        self.font_family_combo.clear()
        for font in fonts:
            self.font_family_combo.addItem(font)
        idx = self.font_family_combo.findText(current_family, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            self.font_family_combo.setCurrentIndex(idx)
        elif current_family:
            self.font_family_combo.addItem(current_family)
            self.font_family_combo.setCurrentIndex(self.font_family_combo.count() - 1)
        self.font_family_combo.blockSignals(False)
        self.font_size_combo.blockSignals(True)
        self.font_size_combo.clear()
        for size in [str(s) for s in range(8, 25)]:
            self.font_size_combo.addItem(size)
        size_idx = self.font_size_combo.findText(current_size)
        self.font_size_combo.setCurrentIndex(max(0, size_idx))
        self.font_size_combo.blockSignals(False)
        lines = []
        for source, font in sorted(current.items()):
            lines.append(f"  {source}: {font}")
        self.font_status_label.setText("Current fonts:\n" + "\n".join(lines) if lines else "No font settings detected.")

    def apply_font_bridge(self) -> None:
        if not hasattr(self, "font_family_combo"):
            return
        family = self.font_family_combo.currentText().strip()
        size = self.font_size_combo.currentText().strip() or "12"
        if not family:
            self.say("Choose a font family first.")
            return
        if QMessageBox.question(
            self,
            "Apply font everywhere",
            f"Set {family} {size}pt across DMS, KDE, GTK3/4, qt5ct, qt6ct?\n\nAll affected files will be backed up first.",
        ) != QMessageBox.StandardButton.Yes:
            return
        outputs: list[str] = []
        font_kde = f"{family},{size},-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
        font_gtk = f"{family},  {size}"
        font_qt = f'"{family},{size},-1,5,400,0,0,0,0,0,0,0,0,0,0,1"'
        # DMS
        dms = HOME / ".config/DankMaterialShell/settings.json"
        if dms.exists():
            self.backup_file(dms)
            try:
                data = json.loads(dms.read_text())
                data["fontFamily"] = family
                dms.write_text(json.dumps(data, indent=2) + "\n")
                outputs.append(f"DMS: fontFamily={family}")
            except Exception as exc:
                outputs.append(f"DMS: FAIL - {exc}")
        # kdeglobals
        kg = HOME / ".config/kdeglobals"
        if kg.exists():
            self.backup_file(kg)
            text = kg.read_text(errors="ignore")
            for key in ["font", "fixed", "menuFont", "toolBarFont", "smallestReadableFont"]:
                text = re.sub(rf"(?m)^{key}=.*$", f"{key}={font_kde}", text)
            kg.write_text(text)
            outputs.append(f"kdeglobals: {family} {size}")
        # GTK3/4
        for gtk in [HOME / ".config/gtk-3.0/settings.ini", HOME / ".config/gtk-4.0/settings.ini"]:
            if gtk.exists():
                self.backup_file(gtk)
                text = gtk.read_text(errors="ignore")
                text = re.sub(r"(?m)^gtk-font-name\s*=\s*.*$", f"gtk-font-name={font_gtk}", text)
                gtk.write_text(text)
                outputs.append(f"{gtk.parent.name}: {font_gtk}")
        # qt5ct/qt6ct
        for qt in [HOME / ".config/qt5ct/qt5ct.conf", HOME / ".config/qt6ct/qt6ct.conf"]:
            if qt.exists():
                self.backup_file(qt)
                text = qt.read_text(errors="ignore")
                if "[Fonts]" not in text:
                    text = text.rstrip() + "\n\n[Fonts]\n"
                text = re.sub(r'(?m)^general=.*$', f"general={font_qt}", text)
                text = re.sub(r'(?m)^fixed=.*$', f"fixed={font_qt}", text)
                if not re.search(r"(?m)^general=", text):
                    text = text.replace("[Fonts]\n", f"[Fonts]\ngeneral={font_qt}\n", 1)
                if not re.search(r"(?m)^fixed=", text):
                    text = text.replace("[Fonts]\n", f"[Fonts]\nfixed={font_qt}\n", 1)
                qt.write_text(text)
                outputs.append(f"{qt.parent.name}: {font_qt}")
        self.refresh_font_bridge()
        self.say(f"Applied font bridge:\n" + "\n".join(outputs) + "\n\nRestart running apps to see the change.")

    def backup_file(self, path: Path) -> Path | None:
        if not path.exists():
            return None
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUP_ROOT / stamp / str(path).replace(str(HOME) + "/", "", 1)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        return target

    def theme_file_statuses(self) -> list[tuple[str, Path, bool, str]]:
        files = [
            ("DMS settings", HOME / ".config/DankMaterialShell/settings.json", False, ""),
            ("DankMatugen KDE colors", HOME / ".local/share/color-schemes/DankMatugen.colors", False, ""),
            ("qt6ct config", HOME / ".config/qt6ct/qt6ct.conf", True, "custom_palette=true"),
            ("qt6ct matugen palette", HOME / ".config/qt6ct/colors/matugen.conf", False, ""),
            ("qt5ct config", HOME / ".config/qt5ct/qt5ct.conf", True, "custom_palette=true"),
            ("qt5ct matugen palette", HOME / ".config/qt5ct/colors/matugen.conf", False, ""),
            ("GTK3 settings", HOME / ".config/gtk-3.0/settings.ini", False, ""),
            ("GTK4 settings", HOME / ".config/gtk-4.0/settings.ini", False, ""),
        ]
        result = []
        for label, path, needs_text, needle in files:
            ok = path.exists()
            extra = ""
            if ok and needs_text:
                text = path.read_text(errors="ignore")
                ok = needle in text
                extra = f" contains {needle}" if ok else f" missing {needle}"
            result.append((label, path, ok, extra))
        return result

    def refresh_theme_bridge(self) -> None:
        if not hasattr(self, "theme_status_label"):
            return
        lines = []
        for label, path, ok, extra in self.theme_file_statuses():
            lines.append(f"{'OK' if ok else 'WARN'}  {label}: {path}{extra}")
        lines.append(f"\nLoaded palette accent: {ACCENT}  background: {BG}  surface: {SURFACE}")
        self.theme_status_label.setText("\n".join(lines))

    def default_app_groups(self) -> list[tuple[str, str, str, list[str], str]]:
        return [
            (
                "folders",
                "Folders",
                "File manager for directories and portal folder opens",
                ["inode/directory"],
                "org.kde.dolphin.desktop",
            ),
            (
                "pdfs",
                "PDFs",
                "PDF reader/editor default",
                ["application/pdf"],
                "okularApplication_pdf.desktop",
            ),
            (
                "images",
                "Images",
                "PNG, JPEG, WebP viewer",
                ["image/png", "image/jpeg", "image/webp"],
                "org.kde.gwenview.desktop",
            ),
            (
                "archives",
                "Archives",
                "ZIP and tar archive handler",
                ["application/zip", "application/x-tar"],
                "org.kde.ark.desktop",
            ),
            (
                "text_code",
                "Text/code",
                "Plain text and Markdown editor",
                ["text/plain", "text/markdown"],
                "dev.zed.Zed.desktop",
            ),
            (
                "browser",
                "Browser",
                "HTTP and HTTPS URL handler",
                ["x-scheme-handler/http", "x-scheme-handler/https"],
                "app.zen_browser.zen.desktop",
            ),
        ]

    def approved_defaults(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for _key, _title, _subtitle, mimes, desktop in self.default_app_groups():
            pairs.extend((mime, desktop) for mime in mimes)
        return pairs

    def current_default(self, mime: str) -> str:
        code, out = run_cmd(["xdg-mime", "query", "default", mime], timeout=6)
        return out.strip() if code == 0 and out.strip() else "unset"

    def combo_app_items(self, extra_ids: set[str] | None = None) -> list[tuple[str, str]]:
        items = [(name, path.name) for name, path in self.available_desktop_apps()]
        known = {desktop for _name, desktop in items}
        for desktop in sorted(extra_ids or set()):
            if desktop and desktop != "unset" and desktop not in known:
                items.insert(0, (desktop, desktop))
        return items

    def refresh_default_apps(self) -> None:
        if not hasattr(self, "default_apps_label"):
            return
        extra_ids: set[str] = set()
        for _key, _title, _subtitle, mimes, recommended in self.default_app_groups():
            extra_ids.add(recommended)
            extra_ids.update(self.current_default(mime) for mime in mimes)
        app_items = self.combo_app_items(extra_ids)
        lines = []
        for key, title, _subtitle, mimes, recommended in self.default_app_groups():
            current_values = [self.current_default(mime) for mime in mimes]
            actual = current_values[0] if current_values else "unset"
            all_same = all(value == actual for value in current_values)
            expected = all(value == recommended for value in current_values)
            if hasattr(self, "default_app_combos") and key in self.default_app_combos:
                combo = self.default_app_combos[key]
                old = combo.current_data() or actual
                combo.block_signals(True)
                combo.clear_items()
                for name, desktop in app_items:
                    combo.add_item(name, desktop)
                target = actual if actual != "unset" else recommended
                combo.set_current_data(target if any(d == target for _, d in combo._items) else old)
                combo.block_signals(False)
            status = "OK" if expected else ("MIXED" if not all_same else "WARN")
            if hasattr(self, "default_app_statuses") and key in self.default_app_statuses:
                label = self.default_app_statuses[key]
                label.setText(f"{status}: {actual}")
                label.setStyleSheet(f"color: {ACCENT if status == 'OK' else WARNING};")
            lines.append(f"{status}  {title}: {', '.join(f'{mime}={value}' for mime, value in zip(mimes, current_values, strict=False))}")
        self.default_apps_label.setText("\n".join(lines))

    def backup_mimeapps(self) -> Path | None:
        src = HOME / ".config/mimeapps.list"
        if not src.exists():
            return None
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUP_ROOT / stamp / ".config/mimeapps.list"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        return target

    def set_mime_defaults(self, pairs: list[tuple[str, str]]) -> list[str]:
        outputs = []
        for mime, desktop in pairs:
            code, out = run_cmd(["xdg-mime", "default", desktop, mime], timeout=8)
            outputs.append(f"{mime} -> {desktop}: exit {code} {out}")
        return outputs

    def apply_selected_default_apps(self) -> None:
        if not hasattr(self, "default_app_combos"):
            return
        pairs: list[tuple[str, str]] = []
        for key, _title, _subtitle, mimes, _recommended in self.default_app_groups():
            combo = self.default_app_combos.get(key)
            if not combo:
                continue
            desktop = combo.current_data()
            if not desktop:
                continue
            pairs.extend((mime, str(desktop)) for mime in mimes)
        if not pairs:
            self.say("No default app selections found.")
            return
        if QMessageBox.question(self, "Apply selected default apps", "Backup mimeapps.list and apply the selected defaults?") != QMessageBox.StandardButton.Yes:
            return
        backup = self.backup_mimeapps()
        outputs = self.set_mime_defaults(pairs)
        self.say(f"Applied selected defaults. Backup: {backup}\n" + "\n".join(outputs[-8:]))
        self.refresh_default_apps()

    def apply_default_apps(self) -> None:
        if QMessageBox.question(self, "Apply approved defaults", "Backup mimeapps.list and apply the approved KDE/Qt workstation baseline?") != QMessageBox.StandardButton.Yes:
            return
        backup = self.backup_mimeapps()
        outputs = self.set_mime_defaults(self.approved_defaults())
        self.say(f"Applied approved defaults. Backup: {backup}\n" + "\n".join(outputs[-8:]))
        self.refresh_default_apps()

    def refresh_screenshots(self) -> None:
        if not hasattr(self, "screenshot_status_label"):
            return
        cmds = ["grim", "slurp", "swappy", "wf-recorder", "wl-copy"]
        lines = []
        for cmd in cmds:
            code, out = run_cmd(["bash", "-lc", f"command -v {shlex.quote(cmd)}"], timeout=5)
            lines.append(f"{'OK' if code == 0 else 'WARN'}  {cmd}: {out if out else 'missing'}")
        for script in ["dms-region-screenshot-edit", "dms-full-screenshot-edit", "dms-region-screenshot-copy"]:
            path = HOME / ".local/bin" / script
            lines.append(f"{'OK' if path.exists() else 'WARN'}  {path}")
        self.screenshot_status_label.setText("\n".join(lines))

    def refresh_remote_desktop(self) -> None:
        if not hasattr(self, "remote_status_label"):
            return
        lines = []
        for label, unit in [("Sunshine", "app-dev.lizardbyte.app.Sunshine.service")]:
            code, _ = run_cmd(["systemctl", "--user", "is-active", "--quiet", unit], timeout=5)
            lines.append(f"{'OK' if code == 0 else 'WARN'}  {label} service: {'active' if code == 0 else 'inactive'}")
        for proc in ["rustdesk", "nvidia-smi"]:
            code, out = run_cmd(["bash", "-lc", f"pgrep -af {shlex.quote(proc)} | head -3 || true"], timeout=5)
            lines.append(f"INFO {proc}: {out if out else 'not running/no process'}")
        code, out = run_cmd(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], timeout=8)
        lines.append(f"{'OK' if code == 0 else 'WARN'}  NVIDIA: {out if out else 'unavailable'}")
        self.remote_status_label.setText("\n".join(lines))

    def load_startup_config(self) -> dict:
        default = {
            "tray_ready_services": [],
            "post_start_commands": [],
            "wait_timeout_seconds": 30,
        }
        if not STARTUP_JSON.exists():
            STARTUP_JSON.parent.mkdir(parents=True, exist_ok=True)
            STARTUP_JSON.write_text(json.dumps(default, indent=2) + "\n")
            return default
        with contextlib.suppress(Exception):
            data = json.loads(STARTUP_JSON.read_text())
            if isinstance(data, dict):
                merged = dict(default)
                merged.update(data)
                return merged
        return default

    def save_startup_config(self, data: dict) -> None:
        STARTUP_JSON.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if STARTUP_JSON.exists():
            stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = BACKUP_ROOT / stamp / ".config/dms-kde-workstation/startup.json"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STARTUP_JSON, backup)
        STARTUP_JSON.write_text(json.dumps(data, indent=2) + "\n")
        self.say(f"Saved tray-ready startup config. Backup: {backup}")

    def refresh_startup(self) -> None:
        self.refresh_desktop_app_combo()
        self.refresh_autostart_apps()

    def desktop_name(self, path: Path) -> str:
        try:
            for line in path.read_text(errors="ignore").splitlines():
                if line.startswith("Name="):
                    return line.split("=", 1)[1].strip()
        except OSError:
            pass
        return path.stem

    def desktop_hidden(self, path: Path) -> bool:
        try:
            return any(
                line.strip() == "Hidden=true"
                for line in path.read_text(errors="ignore").splitlines()
            )
        except OSError:
            return False

    def available_desktop_apps(self) -> list[tuple[str, Path]]:
        seen: set[str] = set()
        apps: list[tuple[str, Path]] = []
        directories = [
            HOME / ".local/share/applications",
            Path("/usr/share/applications"),
            Path("/var/lib/flatpak/exports/share/applications"),
            HOME / ".local/share/flatpak/exports/share/applications",
        ]
        for directory in directories:
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.desktop")):
                if path.name in seen:
                    continue
                seen.add(path.name)
                try:
                    text = path.read_text(errors="ignore")
                except OSError:
                    continue
                if "NoDisplay=true" in text or "Hidden=true" in text:
                    continue
                apps.append((self.desktop_name(path), path))
        return sorted(apps, key=lambda item: item[0].lower())

    def refresh_desktop_app_combo(self) -> None:
        if not hasattr(self, "desktop_app_combo"):
            return
        current = self.desktop_app_combo.current_data()
        self.desktop_app_combo.block_signals(True)
        self.desktop_app_combo.clear_items()
        for name, path in self.available_desktop_apps():
            self.desktop_app_combo.add_item(name, str(path))
        if current:
            self.desktop_app_combo.set_current_data(current)
        self.desktop_app_combo.block_signals(False)

    def refresh_autostart_apps(self) -> None:
        if not hasattr(self, "autostart_apps_list"):
            return
        self.autostart_apps_list.clear()
        autostart_dir = HOME / ".config/autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(autostart_dir.glob("*.desktop")):
            if self.desktop_hidden(path):
                continue
            label = f"{self.desktop_name(path)}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.autostart_apps_list.addItem(item)

    def set_autostart_hidden(self, path: Path, hidden: bool) -> None:
        if not path.exists():
            return
        text = path.read_text(errors="ignore")
        if re.search(r"(?m)^Hidden=", text):
            text = re.sub(
                r"(?m)^Hidden=.*$", f"Hidden={'true' if hidden else 'false'}", text
            )
        else:
            text = text.rstrip() + f"\nHidden={'true' if hidden else 'false'}\n"
        path.write_text(text)

    def selected_autostart_path(self) -> Path | None:
        items = (
            self.autostart_apps_list.selectedItems()
            if hasattr(self, "autostart_apps_list")
            else []
        )
        if not items:
            self.say("No autostart app selected.")
            return None
        return Path(items[0].data(Qt.ItemDataRole.UserRole))

    def add_selected_desktop_autostart(self) -> None:
        if not hasattr(self, "desktop_app_combo"):
            return
        source_data = self.desktop_app_combo.current_data()
        if not source_data:
            self.say("FAIL: No app selected.")
            return
        source = Path(source_data)
        if not source.exists():
            self.say(f"FAIL: Desktop file not found: {source}")
            return
        target = HOME / ".config/autostart" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, target)
            self.set_autostart_hidden(target, False)
            self.say(f"Added autostart app: {self.desktop_name(target)}")
        except Exception as exc:
            self.say(f"FAIL: Could not copy desktop file: {exc}")
        self.refresh_autostart_apps()

    def remove_selected_autostart_app(self) -> None:
        path = self.selected_autostart_path()
        if not path:
            return
        if (
            QMessageBox.question(self, "Remove autostart app", f"Remove {path}?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            path.unlink(missing_ok=True)
            self.say(f"Removed autostart app: {path.name}")
        except Exception as exc:
            self.say(f"FAIL: Could not remove {path}: {exc}")
        self.refresh_autostart_apps()

    def refresh_services(self) -> None:
        for unit, label in self.service_rows:
            code, _ = run_cmd(
                ["systemctl", "--user", "is-active", "--quiet", unit], timeout=6
            )
            label.setText("active" if code == 0 else "inactive")
            label.setStyleSheet(f"color: {ACCENT if code == 0 else WARNING};")

    def sddm_autologin_entries(self) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        paths = [Path("/etc/sddm.conf"), *sorted(Path("/etc/sddm.conf.d").glob("*.conf"))]
        for path in paths:
            if not path.exists():
                continue
            text = path.read_text(errors="ignore")
            if "[Autologin]" not in text:
                continue
            section = re.search(r"(?ms)^\[Autologin\]\s*(.*?)(?:^\[|\Z)", text)
            body = section.group(1) if section else text
            user = re.search(r"(?m)^\s*User\s*=\s*(.*)\s*$", body)
            session = re.search(r"(?m)^\s*Session\s*=\s*(.*)\s*$", body)
            relogin = re.search(r"(?m)^\s*Relogin\s*=\s*(.*)\s*$", body)
            entries.append(
                {
                    "path": str(path),
                    "user": user.group(1).strip() if user else "",
                    "session": session.group(1).strip() if session else "",
                    "relogin": relogin.group(1).strip() if relogin else "",
                }
            )
        return entries

    def refresh_login(self) -> None:
        dm = self.detect_display_manager()
        is_sddm = "sddm" in dm.lower()
        if hasattr(self, "display_manager_label"):
            self.display_manager_label.setText(dm or "not detected")

        if hasattr(self, "polkit_label"):
            if POLKIT_POLICY.exists():
                self.polkit_label.setText("Installed")
                self.polkit_label.setStyleSheet(f"color: {ACCENT};")
            else:
                self.polkit_label.setText("MISSING — run: sudo cp <repo>/configs/polkit/io.dms-kde-workstation.sddm-autologin.policy /usr/share/polkit-1/actions/")
                self.polkit_label.setStyleSheet(f"color: {WARNING};")

        conflicts = self.autologin_conflicts()
        managed = next((e for e in conflicts if "dms-mango-autologin" in e["path"]), None)
        active = next((e for e in reversed(conflicts) if e.get("user") or e.get("session")), None)

        if hasattr(self, "autologin_conflicts_list"):
            self.autologin_conflicts_list.clear()
            for entry in conflicts:
                managed_tag = "  ← managed" if "dms-mango-autologin" in entry["path"] else "  ← CONFLICT"
                item = QListWidgetItem(f"{entry['path']}: {entry['user'] or '?'} / {entry['session'] or '?'}{managed_tag}")
                self.autologin_conflicts_list.addItem(item)
            if hasattr(self, "conflict_detail_label"):
                if len(conflicts) > 1:
                    sessions = set(e["session"] for e in conflicts if e.get("session"))
                    self.conflict_detail_label.setText(
                        f"WARNING: {len(conflicts)} files have [Autologin]. "
                        f"{'Same session — still risky.' if len(sessions) <= 1 else 'DIFFERENT sessions — last file alphabetically wins.'}\n"
                        "Click 'Enable and consolidate' to fix."
                    )
                elif len(conflicts) == 1:
                    self.conflict_detail_label.setText("1 managed file. No conflicts.")
                else:
                    self.conflict_detail_label.setText("No [Autologin] sections found. Autologin is disabled.")

        if active and is_sddm:
            state = "Enabled"
            if len(conflicts) > 1:
                state = "Enabled but CONFLICTING"
            color = ACCENT if len(conflicts) <= 1 else WARNING
        elif active:
            state = "Configured but display manager is not SDDM"
            color = WARNING
        else:
            state = "Disabled"
            color = WARNING

        if hasattr(self, "autologin_state_label"):
            self.autologin_state_label.setText(state)
            self.autologin_state_label.setStyleSheet(f"color: {color};")
        if hasattr(self, "autologin_user_label"):
            self.autologin_user_label.setText(active.get("user", "unset") if active else "unset")
        if hasattr(self, "autologin_session_label"):
            self.autologin_session_label.setText(active.get("session", "unset") if active else "unset")
        if hasattr(self, "autologin_file_label"):
            detail = active.get("path", "none") if active else "none"
            self.autologin_file_label.setText(detail)

        effective_session = active.get("session", "mango.desktop") if active else "mango.desktop"
        effective_user = active.get("user", os.environ.get("USER", "")) if active else os.environ.get("USER", "")
        if hasattr(self, "session_combo"):
            idx = self.session_combo.findData(effective_session)
            self.session_combo.setCurrentIndex(max(0, idx))
        if "__login_user" in self.controls:
            self.controls["__login_user"].setText(effective_user)

    CONSOLIDATE_SCRIPT = str(HOME / ".local/lib/dms-kde-workstation/sddm-consolidate-autologin.py")

    def enable_autologin(self) -> None:
        self.trace("enable_autologin CALLED")
        if not Path(self.CONSOLIDATE_SCRIPT).exists():
            self.login_msg(
                f"ERROR: Consolidate script is missing.\n\n"
                f"Expected: {self.CONSOLIDATE_SCRIPT}\n\n"
                f"Run 'Apply Baseline' on the First Run page to deploy it, then try again."
            )
            return
        user = self.controls["__login_user"].text().strip()
        session = self.session_combo.currentData() if hasattr(self, "session_combo") else "mango.desktop"
        if not session:
            session = "mango.desktop"
        self.trace(f"enable_autologin user={user} session={session}")
        if not user:
            self.login_msg("Autologin user cannot be empty.")
            return
        conflicts = self.autologin_conflicts()
        conflict_msg = ""
        if len(conflicts) > 1:
            conflict_msg = (
                f"\n\nCONFLICT DETECTED: {len(conflicts)} files have [Autologin]:\n"
                + "\n".join(f"  • {c['path']}: {c['session']}" for c in conflicts)
                + "\n\nConsolidating will strip [Autologin] from all other files and keep only the managed file."
            )
        if QMessageBox.question(
            self,
            "Enable and consolidate autologin",
            f"Set autologin for user '{user}' → session '{session}'?\n\n"
            f"This will:\n"
            f"  1. Write /etc/sddm.conf.d/dms-mango-autologin.conf\n"
            f"  2. Remove [Autologin] from all other SDDM .conf files\n"
            f"  3. Other settings in those files (theme, display) are kept{conflict_msg}",
        ) != QMessageBox.StandardButton.Yes:
            return
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = str(BACKUP_ROOT / stamp / "sddm-autologin")
        self.run_privileged(
            "Enable autologin",
            ["python3", self.CONSOLIDATE_SCRIPT, "write", user, session, backup_dir],
        )

    def disable_autologin(self) -> None:
        self.trace("disable_autologin CALLED")
        if not Path(self.CONSOLIDATE_SCRIPT).exists():
            self.login_msg(
                f"ERROR: Consolidate script is missing.\n\n"
                f"Expected: {self.CONSOLIDATE_SCRIPT}\n\n"
                f"Run 'Apply Baseline' on the First Run page to deploy it, then try again."
            )
            return
        conflicts = self.autologin_conflicts()
        detail = "\n".join(f"  • {c['path']}: {c['session']}" for c in conflicts) if conflicts else "  (none found)"
        if QMessageBox.question(
            self,
            "Disable autologin",
            f"Remove the managed autologin file and strip [Autologin] from all other SDDM files?\n\n"
            f"Files affected:\n{detail}\n\n"
            f"Other settings in those files (theme, display) are kept.",
        ) != QMessageBox.StandardButton.Yes:
            return
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = str(BACKUP_ROOT / stamp / "sddm-autologin")
        self.run_privileged(
            "Disable autologin",
            ["python3", self.CONSOLIDATE_SCRIPT, "remove", backup_dir],
        )

    def backup_items(self) -> list[tuple[str, Path]]:
        items: list[tuple[str, Path]] = []
        if not BACKUP_ROOT.exists():
            return items
        for path in sorted(
            BACKUP_ROOT.glob("*/.config/mango/config.conf"), reverse=True
        ):
            stamp = path.parts[-4] if len(path.parts) >= 4 else path.parent.name
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            items.append((f"{stamp}  —  {size} bytes", path))
        return items

    def refresh_backups(self) -> None:
        if not hasattr(self, "backup_list"):
            return
        self.backup_list.clear()
        for label, path in self.backup_items():
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.backup_list.addItem(item)

    def create_checkpoint(self) -> None:
        backup = self.cfg.backup()
        self.say(f"Created checkpoint: {backup}")
        self.refresh_backups()

    def selected_backup_path(self) -> Path | None:
        if not hasattr(self, "backup_list"):
            return None
        items = self.backup_list.selectedItems()
        if not items:
            self.say("No backup selected.")
            return None
        return Path(items[0].data(Qt.ItemDataRole.UserRole))

    def restore_selected_backup(self) -> None:
        source = self.selected_backup_path()
        if not source or not source.exists():
            self.say("Selected backup is missing.")
            return
        if (
            QMessageBox.question(
                self,
                "Restore Mango config",
                f"Restore this backup?\n\n{source}\n\nCurrent config will be backed up first.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        current_backup = self.cfg.backup()
        try:
            MANGO_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, MANGO_CONFIG)
            self.cfg.reload()
            self.say(
                f"Restored {source}\nPrevious config backed up to: {current_backup}"
            )
            self.reload_mango()
        except Exception as exc:
            self.say(f"FAIL: Could not restore backup: {exc}")

    def reset_to_project_baseline(self) -> None:
        source = PROJECT / "configs/mango/config.conf.working-20260516"
        if not source.exists():
            self.say(f"Project baseline missing: {source}")
            return
        if (
            QMessageBox.question(
                self,
                "Reset to baseline",
                f"Reset Mango config to project baseline?\n\n{source}\n\nCurrent config will be backed up first.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        current_backup = self.cfg.backup()
        try:
            shutil.copy2(source, MANGO_CONFIG)
            self.cfg.reload()
            self.say(
                f"Reset to project baseline. Previous config backed up to: {current_backup}"
            )
            self.reload_mango()
        except Exception as exc:
            self.say(f"FAIL: Could not reset to baseline: {exc}")

    def export_current_baseline(self) -> None:
        target = PROJECT / "configs/mango/config.conf.working-20260516"
        if (
            QMessageBox.question(
                self,
                "Export current baseline",
                f"Overwrite the project working baseline with the current Mango config?\n\n{target}",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(MANGO_CONFIG, target)
            self.say(f"Exported current Mango config as project baseline: {target}")
        except Exception as exc:
            self.say(f"FAIL: Could not export baseline: {exc}")

    def input_keys(self) -> list[str]:
        return [
            "sloppyfocus",
            "warpcursor",
            "focus_cross_monitor",
            "focus_cross_tag",
            "enable_floating_snap",
            "drag_tile_to_tile",
            "drag_tile_small",
            "snap_distance",
            "cursor_size",
            "disable_trackpad",
            "tap_to_click",
            "tap_and_drag",
            "drag_lock",
            "trackpad_natural_scrolling",
            "disable_while_typing",
            "left_handed",
            "middle_button_emulation",
            "mouse_natural_scrolling",
            "swipe_min_threshold",
        ]

    def animation_curve_keys(self) -> list[tuple[str, str]]:
        return [
            ("animation_curve_open", "Open curve"),
            ("animation_curve_move", "Move curve"),
            ("animation_curve_tag", "Tag/workspace curve"),
            ("animation_curve_close", "Close curve"),
            ("animation_curve_focus", "Focus curve"),
            ("animation_curve_opafadeout", "Opacity fade-out curve"),
            ("animation_curve_opafadein", "Opacity fade-in curve"),
        ]

    def animation_curve_presets(self) -> dict[str, dict[str, str]]:
        smooth = "0.46,1.0,0.29,1"
        return {
            "Balanced / Mango default": {
                "animation_curve_open": smooth,
                "animation_curve_move": smooth,
                "animation_curve_tag": smooth,
                "animation_curve_close": "0.08,0.92,0,1",
                "animation_curve_focus": smooth,
                "animation_curve_opafadeout": "0.5,0.5,0.5,0.5",
                "animation_curve_opafadein": smooth,
            },
            "Snappy": {
                key: "0.2,0.0,0.0,1.0" for key, _label in self.animation_curve_keys()
            },
            "Soft / DMS-like": {
                key: "0.16,1.0,0.3,1.0" for key, _label in self.animation_curve_keys()
            },
            "Linear / minimal": {
                key: "0.0,0.0,1.0,1.0" for key, _label in self.animation_curve_keys()
            },
            "Slow ease": {
                key: "0.25,0.1,0.25,1.0" for key, _label in self.animation_curve_keys()
            },
        }

    def apply_animation_curve_preset(self) -> None:
        if not hasattr(self, "animation_curve_preset"):
            return
        name = self.animation_curve_preset.currentText()
        preset = self.animation_curve_presets().get(name, {})
        for key, value in preset.items():
            widget = self.controls.get(key)
            if isinstance(widget, (QLineEdit, BezierCurveEditor)):
                widget.setText(value)
        self.say(f"Applied animation curve preset: {name}. Save animation/effects to write it to Mango config.")

    def valid_animation_curve(self, value: str) -> bool:
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 4:
            return False
        with contextlib.suppress(ValueError):
            nums = [float(part) for part in parts]
            return all(0.0 <= n <= 1.0 for n in nums)
        return False

    def effect_keys(self) -> list[str]:
        return [
            "blur",
            "blur_layer",
            "blur_optimized",
            "shadows",
            "layer_shadows",
            "shadow_only_floating",
            "blur_params_num_passes",
            "blur_params_radius",
            "shadows_size",
            "shadows_blur",
            "focused_opacity",
            "unfocused_opacity",
            "fadein_begin_opacity",
            "fadeout_begin_opacity",
            "zoom_initial_ratio",
            "zoom_end_ratio",
            "animations",
            "layer_animations",
            "animation_fade_in",
            "animation_fade_out",
            "animation_type_open",
            "animation_type_close",
            "tag_animation_direction",
            "animation_duration_move",
            "animation_duration_open",
            "animation_duration_tag",
            "animation_duration_close",
            "animation_duration_focus",
            "animation_curve_open",
            "animation_curve_move",
            "animation_curve_tag",
            "animation_curve_close",
            "animation_curve_focus",
            "animation_curve_opafadeout",
            "animation_curve_opafadein",
        ]

    def layout_keys(self) -> list[str]:
        return [
            "scroller_focus_center",
            "scroller_prefer_center",
            "edge_scroller_pointer_focus",
            "scroller_default_proportion",
            "scroller_default_proportion_single",
            "scroller_structs",
            "scroller_proportion_preset",
            "new_is_master",
            "default_mfact",
            "default_nmaster",
            "smartgaps",
            "dwindle_smart_split",
            "dwindle_drop_simple_split",
            "dwindle_manual_split",
            "dwindle_hsplit",
            "dwindle_vsplit",
            "dwindle_preserve_split",
            "gappih",
            "gappiv",
            "gappoh",
            "gappov",
            "borderpx",
            "border_radius",
        ]

    def save_keys(self, keys: list[str], label: str) -> None:
        if (
            QMessageBox.question(
                self, f"Save {label}", f"Backup Mango config and save {label} settings?"
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        for key in keys:
            widget = self.controls.get(key)
            if widget is None:
                continue
            if isinstance(widget, QCheckBox):
                self.cfg.set(key, widget.isChecked())
            elif isinstance(widget, QComboBox):
                val = widget.currentText()
                if key == "tag_animation_direction":
                    val = "1" if val == "horizontal" else "0"
                self.cfg.set(key, val)
            elif isinstance(widget, (QLineEdit, BezierCurveEditor)):
                value = widget.text().strip()
                if key.startswith("animation_curve_") and not self.valid_animation_curve(value):
                    self.say(f"Invalid curve for {key}: use x1,y1,x2,y2 values between 0 and 1")
                    return
                self.cfg.set(key, value)
            elif isinstance(widget, QSlider):
                scale = int(widget.property("scale") or 1)
                self.cfg.set(
                    key, widget.value() / scale if scale != 1 else widget.value()
                )
        try:
            backup = self.cfg.save()
        except Exception as exc:
            self.say(f"FAIL: Could not save Mango config: {exc}")
            return
        self.say(f"Saved {label}. Backup: {backup}")
        self.reload_mango()

    def save_layout(self) -> None:
        layout_name = LAYOUTS[self.controls["__default_layout"].currentText()]
        self.cfg.set_default_layout(layout_name)
        self.save_keys(self.layout_keys(), "layout")

    def save_effects(self) -> None:
        self.save_keys(self.effect_keys(), "effects")

    def save_keyboard(self) -> None:
        if (
            QMessageBox.question(
                self, "Save keyboard", "Backup config and save keyboard settings?"
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        for key in ["xkb_rules_layout", "repeat_rate", "repeat_delay", "numlockon"]:
            widget = self.controls[key]
            if isinstance(widget, QCheckBox):
                self.cfg.set(key, widget.isChecked())
            elif isinstance(widget, QLineEdit):
                self.cfg.set(key, widget.text().strip() or "us,gr")
            elif isinstance(widget, QSlider):
                self.cfg.set(key, widget.value())
        self.cfg.remove_matching(r"^bind=ALT,shift_[lr],switch_keyboard_layout")
        self.cfg.remove_matching(r"^bind=SUPER\+CTRL,[12],switch_keyboard_layout")
        if self.alt_shift.isChecked():
            self.cfg.ensure_line(
                "bind=ALT,shift_l,switch_keyboard_layout", "# keyboard"
            )
            self.cfg.ensure_line(
                "bind=ALT,shift_r,switch_keyboard_layout", "# keyboard"
            )
        if self.direct_layouts.isChecked():
            self.cfg.ensure_line(
                "bind=SUPER+CTRL,1,switch_keyboard_layout,0", "# keyboard"
            )
            self.cfg.ensure_line(
                "bind=SUPER+CTRL,2,switch_keyboard_layout,1", "# keyboard"
            )
        try:
            backup = self.cfg.save()
        except Exception as exc:
            self.say(f"FAIL: Could not save keyboard settings: {exc}")
            return
        self.say(f"Saved keyboard. Backup: {backup}")
        self.reload_mango()

    def add_startup_preset(self, command: str) -> None:
        self.startup_command.setText(command)
        self.add_startup_command()

    def set_active_layout(self) -> None:
        layout = LAYOUTS.get(self.live_layout.currentText(), "")
        if not layout:
            self.say("FAIL: No layout selected.")
            return
        code, out = run_cmd(["mmsg", "-s", "-l", LAYOUT_SHORT.get(layout, layout)])
        if code == 0:
            self.say(f"Set active layout to: {layout}")
        else:
            self.say(f"FAIL: Could not set layout (exit {code}). {out}\nMango may not be running.")
        self.refresh_status()

    def reload_mango(self) -> None:
        code, out = run_cmd(["mmsg", "-s", "-d", "reload_config"], timeout=10)
        if code == 0:
            self.say("Mango config reloaded successfully.")
        else:
            self.say(f"FAIL: Mango reload failed (exit {code}). {out}\nMango may not be running or mmsg not found.")
        QTimer.singleShot(900, self.refresh_all)

    def service_action(self, action: str, unit: str) -> None:
        if action == "status":
            self.detach(
                self.get_terminal() + [
                    "-e",
                    "bash",
                    "-lc",
                    f"systemctl --user status {shlex.quote(unit)}; read -p 'Press Enter...'",
                ]
            )
            return
        code, out = run_cmd(["systemctl", "--user", action, unit], timeout=25)
        if code == 0:
            self.say(f"OK: systemctl --user {action} {unit}")
        else:
            self.say(f"FAIL: systemctl --user {action} {unit} (exit {code}).\n{out}\nCheck: systemctl --user status {unit}")
        self.refresh_services()

    POLKIT_ACTION = "io.dms-kde-workstation.sddm-autologin"

    TRACE_LOG = HOME / ".local/state/dms-kde-workstation/settings-trace.log"

    def trace(self, msg: str) -> None:
        try:
            self.TRACE_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(self.TRACE_LOG, "a") as f:
                f.write(f"{dt.datetime.now().strftime('%H:%M:%S')} {msg}\n")
        except Exception:
            pass

    def login_msg(self, text: str) -> None:
        """Show feedback directly on the Login page."""
        if hasattr(self, "login_feedback"):
            self.login_feedback.setText(text)
        self.say(text)

    def run_privileged(self, title: str, args: list[str]) -> None:
        """Run a command with elevated privileges using pkexec."""
        self.trace(f"run_privileged START title={title} args={args}")
        try:
            proc = subprocess.Popen(
                ["pkexec", *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.trace(f"run_privileged Popen OK pid={proc.pid}")
        except FileNotFoundError:
            self.trace("run_privileged FAIL: pkexec not found")
            self.login_msg("ERROR: pkexec not found. Install polkit.")
            return
        except Exception as exc:
            self.trace(f"run_privileged FAIL: {exc}")
            self.login_msg(f"ERROR: {exc}")
            return

        self.login_msg(f"[waiting] {title} - waiting for authentication...")

        def check():
            # Guard against window being destroyed during auth
            try:
                rc = proc.poll()
            except Exception:
                return
            self.trace(f"run_privileged check rc={rc}")
            if rc is not None:
                output = proc.stdout.read() if proc.stdout else ""
                self.trace(f"run_privileged DONE rc={rc} output[:300]={output[:300]}")
                if rc == 0:
                    self.login_msg(f"[OK] {title} - completed successfully.\n{output}")
                elif rc == 126 or rc == 127:
                    self.login_msg(f"[WARN] {title} - authentication failed (exit {rc}).\n{output}")
                else:
                    self.login_msg(f"[FAIL] {title} - failed (exit {rc}).\n{output}")
                self.refresh_login()
            else:
                QTimer.singleShot(500, check)

        QTimer.singleShot(500, check)

    def run_first_login_readiness(self) -> None:
        if not FIRST_LOGIN_READINESS_SCRIPT.exists():
            self.say(
                "FAIL: First-login readiness script not found at "
                + str(FIRST_LOGIN_READINESS_SCRIPT)
                + "\nDo not switch to Mango. Fix the repo checkout first."
            )
            return
        code, out = run_cmd([str(FIRST_LOGIN_READINESS_SCRIPT)], timeout=45)
        if code == 0:
            self.say(f"First Mango login readiness passed.\n{out}")
        else:
            self.say(
                f"FAIL: First Mango login readiness check failed.\n{out}\n\n"
                "Do not switch to Mango yet. Fix the FAIL items from your current working session, then run this check again."
            )

    def run_health(self) -> None:
        if not HEALTH_SCRIPT.exists():
            self.say("FAIL: Health script not found at " + str(HEALTH_SCRIPT))
            return
        if os.environ.get("XDG_CURRENT_DESKTOP", "").startswith("mango") is False:
            self.say(
                "INFO: Health Check is mainly for after a successful Mango login.\n"
                "If you have not switched to Mango yet, use 'Check Ready for First Mango Login' instead.\n"
            )
        code, out = run_cmd([str(HEALTH_SCRIPT)], timeout=45)
        if code == 0:
            self.say(f"Health check passed.\n{out}")
        else:
            self.say(
                f"FAIL: Health check exited with code {code}.\n{out}\n\n"
                f"Run manually: {HEALTH_SCRIPT}\n"
                "If Mango is unusable, return to a working session or TTY, re-run the baseline apply, and compare the reported missing files/services before trying Mango again."
            )

    def open_text_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.touch()
        self.detach(["xdg-open", str(path)])

    def launch_kde_module(self, module: str, fallback_module: str | None = None) -> None:
        fallback = fallback_module or module
        env = "QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct"
        command = f"{env} kcmshell6 {shlex.quote(module)} || {env} systemsettings {shlex.quote(fallback)}"
        self.detach(["bash", "-lc", command])

    def open_folder(self, path: str) -> None:
        """Open Dolphin with correct qt6ct theming."""
        self.detach(["env", "QT_QPA_PLATFORMTHEME=qt6ct", "QT_QPA_PLATFORMTHEME_QT6=qt6ct", "dolphin", "--new-window", path])

    def get_terminal(self) -> list[str]:
        """Return a terminal command prefix for the first available terminal emulator."""
        for term in os.environ.get("TERMINAL", "").split(), ["ghostty"], ["kitty"], ["alacritty"], ["konsole"], ["gnome-terminal"], ["xfce4-terminal"]:
            if term and shutil.which(term[0]):
                return term
        return ["xterm"]

    def detach(self, command: list[str]) -> None:
        try:
            subprocess.Popen(command, start_new_session=True)
            self.say("Started: " + " ".join(command))
        except Exception as exc:
            self.say(f"Failed: {exc}")

    def say(self, text: str) -> None:
        if hasattr(self, "log_box"):
            self.log_box.append(text)
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())
        if hasattr(self, "status_label"):
            self.status_label.setText("")

    def set_working(self, text: str) -> None:
        """Show a working status and force the UI to repaint before a blocking call."""
        self.say(f"[WORKING] {text}")
        if hasattr(self, "status_label"):
            self.status_label.setText(f"⏳  {text}")
        QApplication.processEvents()


SINGLE_INSTANCE_KEY = "dms-mango-settings-single-instance"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DMS Mango Workstation Settings")

    # Single-instance: if already running, tell it to show itself
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_KEY)
    if socket.waitForConnected(500):
        # Another instance is running — ask it to show
        socket.write(b"SHOW")
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return 0

    font = QFont("Inter", 10)
    app.setFont(font)
    win = MainWindow()
    win.show()

    # Listen for future instances trying to start
    from PySide6.QtNetwork import QLocalServer
    server = QLocalServer()
    server.newConnection.connect(lambda: win._handle_single_instance(server))
    server.listen(SINGLE_INSTANCE_KEY)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
