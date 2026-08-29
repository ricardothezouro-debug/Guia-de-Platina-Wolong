"""Página do guia: as 9 abas, com progresso, busca global e imagens."""
from __future__ import annotations

import html
import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from . import guide_data
from . import progress as keys
from .image_loader import ImageLoader
from .storage import load_progress, save_progress

_IMG_MAX_W = 620
_IMG_MAX_H = 420
_ICON = 56
_IMG_TIMEOUT_MS = 26000
_SEARCH_LIMIT = 18

_TIER_COLORS = {
    "bronze": "#C77B3B",
    "prata": "#B8C0CC",
    "ouro": "#E7C64A",
    "platina": "#7FE7FF",
}
_KIND_COLORS = {
    "Tábua": "#E7C64A",
    "Shitieshou": "#B9FF43",
    "Casca": "#37F2FF",
}

_PROGRESS_QSS = (
    "QProgressBar{background:#0B111A;border:1px solid #273140;border-radius:9px;"
    "min-height:18px;text-align:center;color:#F3F6FF;font-weight:600}"
    "QProgressBar::chunk{border-radius:8px;background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "stop:0 #37F2FF,stop:0.5 #B9FF43,stop:1 #FF4FD8)}"
)

_NAV_QSS = (
    "QPushButton#NavButton{background:#0D121B;border:1px solid #273140;border-radius:8px;"
    "padding:7px 10px;color:#A8B0BC;text-align:left}"
    "QPushButton#NavButton:hover{border-color:#3C4A5C;color:#F3F6FF}"
    "QPushButton#NavButton:checked{background:#101922;border-color:%s;color:#F3F6FF;font-weight:600}"
    % guide_data.ACCENT
)

_PHASE_QSS = (
    "QPushButton#PhaseHead{background:#101922;border:1px solid #273140;border-radius:9px;"
    "padding:10px 12px;color:#F3F6FF;text-align:left;font-weight:600}"
    "QPushButton#PhaseHead:hover{border-color:%s}" % guide_data.ACCENT
)


def _norm(text) -> str:
    """Minúsculas sem acento, para busca tolerante."""
    stripped = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in stripped if not unicodedata.combining(c)).lower()


def _esc(text) -> str:
    return html.escape(str(text or ""))


def _flat(value) -> str:
    """Junta dict/list/str num texto único, para alimentar a busca."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_flat(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flat(v) for v in value)
    return str(value)


def _label(text: str, object_name: str = "", wrap: bool = True) -> QLabel:
    label = QLabel(str(text or ""))
    if object_name:
        label.setObjectName(object_name)
    label.setWordWrap(wrap)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    return label


def _link(text: str, url: str) -> QLabel:
    label = QLabel(
        f'<a href="{_esc(url)}" style="color:{guide_data.ACCENT}">{_esc(text)}</a>'
    )
    label.setOpenExternalLinks(True)
    label.setWordWrap(True)
    return label


def _card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("NeonPanel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)
    return frame, layout


def _notice(text: str, tone: str = "info") -> QFrame:
    frame = QFrame()
    frame.setObjectName("NeonPanel")
    color = "#F87171" if tone == "red" else guide_data.ACCENT
    frame.setStyleSheet(
        "QFrame{background:#0D121B;border:1px solid #273140;"
        "border-left:3px solid %s;border-radius:10px}" % color
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 11, 14, 11)
    layout.addWidget(_label(text, "Muted"))
    return frame


def _pill(text: str) -> QLabel:
    label = QLabel(str(text or ""))
    label.setObjectName("StatusPill")
    label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return label


def _tag(text: str, color: str) -> QLabel:
    label = QLabel(str(text or "").upper())
    label.setStyleSheet(f"color:{color};font-weight:700;font-size:11px;")
    label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return label


def _detail(layout: QVBoxLayout, title: str, value: str) -> None:
    if not value:
        return
    row = QLabel(f"<b>{_esc(title)}:</b> {_esc(value)}")
    row.setObjectName("Muted")
    row.setWordWrap(True)
    row.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    layout.addWidget(row)


def _scroll_page(build_content) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 10, 0)
    layout.setSpacing(12)
    build_content(layout)
    layout.addStretch(1)

    scroll = QScrollArea()
    scroll.setObjectName("PageScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(container)
    return scroll


class GuidePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._done = load_progress()
        self._image_loader = ImageLoader(self)
        self._boxes: dict[str, list[QCheckBox]] = {}
        self._built: set[int] = set()
        self._phase_pills: list[tuple[QLabel, list[str]]] = []
        self._trophy_rows: list[tuple[QWidget, str, str]] = []
        self._item_rows: list[tuple[QWidget, str, str, str, int]] = []
        self._flag_rows: list[tuple[QWidget, str, int]] = []
        self._section_index = {s["key"]: i for i, s in enumerate(guide_data.SECTIONS)}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 22, 0)
        outer.setSpacing(12)
        self._build_header(outer)
        self._build_search(outer)
        self._build_progress(outer)
        self._build_toolbar(outer)
        self._build_nav(outer)

        self.stack = QStackedWidget()
        self._holders: list[QVBoxLayout] = []
        for _section in guide_data.SECTIONS:
            placeholder = QWidget()
            holder = QVBoxLayout(placeholder)
            holder.setContentsMargins(0, 0, 0, 0)
            holder.addWidget(_label("Carregando…", "Muted"))
            holder.addStretch(1)
            self._holders.append(holder)
            self.stack.addWidget(placeholder)
        self.stack.currentChanged.connect(self._ensure_built)
        outer.addWidget(self.stack, 1)

        outer.addWidget(_label(guide_data.FOOTER, "Muted"))

        self._update_progress()
        # Constrói a primeira aba só depois que o event loop girar, para que
        # build_page() retorne instantaneamente (regra 2 do padrão de plugins).
        QTimer.singleShot(0, lambda: self._ensure_built(0))

        # Downloads em andamento precisam ser encerrados antes que o Qt destrua
        # a página (fechar o app ou atualizar o plugin), senão o processo aborta.
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._image_loader.shutdown)

    def closeEvent(self, event):  # noqa: N802 (assinatura do Qt)
        self._image_loader.shutdown()
        super().closeEvent(event)

    def hideEvent(self, event):  # noqa: N802 (assinatura do Qt)
        if self.window() is not None and self.window().isHidden():
            self._image_loader.shutdown()
        super().hideEvent(event)

    # ------------------------------------------------------------------ topo
    def _build_header(self, outer: QVBoxLayout) -> None:
        outer.addWidget(_label(guide_data.GAME_NAME, "PageTitle", wrap=False))
        outer.addWidget(_label(guide_data.INTRO, "Muted"))
        stats = QHBoxLayout()
        stats.setSpacing(8)
        for stat in guide_data.HERO_STATS:
            stats.addWidget(_pill(f"{stat['value']}  {stat['label']}"))
        stats.addStretch(1)
        outer.addLayout(stats)

    def _build_search(self, outer: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText(
            "Buscar... Ex.: Lu Bu, tábua, Shitieshou, Guandu, feitiço, bandeira, Cao Cao"
        )
        self.global_search.textChanged.connect(self._global_search)
        clear = QPushButton("Limpar")
        clear.clicked.connect(lambda: self.global_search.setText(""))
        row.addWidget(self.global_search, 1)
        row.addWidget(clear, 0)
        outer.addLayout(row)

        self.results_box = QWidget()
        self.results_layout = QVBoxLayout(self.results_box)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(6)
        self.results_box.hide()
        outer.addWidget(self.results_box)

    def _build_progress(self, outer: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)
        self.progress = QProgressBar()
        self.progress.setStyleSheet(_PROGRESS_QSS)
        self.progress.setRange(0, max(1, len(keys.all_keys())))
        self.progress_label = _pill("")
        self.trophy_label = _pill("")
        self.item_label = _pill("")
        row.addWidget(self.progress, 1)
        row.addWidget(self.progress_label, 0)
        row.addWidget(self.trophy_label, 0)
        row.addWidget(self.item_label, 0)
        outer.addLayout(row)

    def _build_toolbar(self, outer: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)
        export = QPushButton("Exportar progresso")
        export.clicked.connect(self._export)
        importer = QPushButton("Importar progresso")
        importer.clicked.connect(self._import)
        reset = QPushButton("Resetar marcações")
        reset.clicked.connect(self._reset)
        for button in (export, importer, reset):
            row.addWidget(button)
        row.addStretch(1)
        outer.addLayout(row)

    def _build_nav(self, outer: QVBoxLayout) -> None:
        holder = QWidget()
        holder.setStyleSheet(_NAV_QSS)
        grid = QGridLayout(holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        self._nav_buttons: list[QPushButton] = []
        for i, section in enumerate(guide_data.SECTIONS):
            button = QPushButton(f"{section['num']}  {section['nav']}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setChecked(i == 0)
            button.clicked.connect(lambda _=False, index=i: self.show_section(index))
            grid.addWidget(button, i // 5, i % 5)
            self._nav_buttons.append(button)
        for column in range(5):
            grid.setColumnStretch(column, 1)
        outer.addWidget(holder)

    def show_section(self, index: int) -> None:
        for i, button in enumerate(self._nav_buttons):
            button.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    # -------------------------------------------------------------- progresso
    def _checkbox(self, key: str, text: str = "") -> QCheckBox:
        box = QCheckBox(text)
        box.setChecked(key in self._done)
        box.toggled.connect(lambda checked, k=key: self._on_toggle(k, checked))
        self._boxes.setdefault(key, []).append(box)
        return box

    def _on_toggle(self, key: str, checked: bool) -> None:
        if checked:
            self._done.add(key)
        else:
            self._done.discard(key)
        for box in self._boxes.get(key, []):
            if box.isChecked() != checked:
                box.blockSignals(True)
                box.setChecked(checked)
                box.blockSignals(False)
        save_progress(self._done)
        self._update_progress()

    def _update_progress(self) -> None:
        all_keys = keys.all_keys()
        done = sum(1 for key in all_keys if key in self._done)
        percent = round(done / len(all_keys) * 100) if all_keys else 0
        self.progress.setValue(done)
        self.progress_label.setText(f"{done} / {len(all_keys)}  •  {percent}%")
        trophies = keys.trophy_keys()
        got = sum(1 for key in trophies if key in self._done)
        self.trophy_label.setText(f"{got}/{len(trophies)} troféus")
        items = keys.collectible_keys()
        got_items = sum(1 for key in items if key in self._done)
        self.item_label.setText(f"{got_items}/{len(items)} coletáveis")
        for pill, phase_keys in self._phase_pills:
            phase_done = sum(1 for key in phase_keys if key in self._done)
            pill.setText(f"{phase_done}/{len(phase_keys)}")

    def _refresh_boxes(self) -> None:
        for key, boxes in self._boxes.items():
            checked = key in self._done
            for box in boxes:
                box.blockSignals(True)
                box.setChecked(checked)
                box.blockSignals(False)
        self._update_progress()
        if self._trophy_rows:
            self._filter_trophies()
        if self._item_rows:
            self._filter_items()
        if self._flag_rows:
            self._filter_flags()

    # ------------------------------------------------------ exportar/importar
    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar progresso", "wolong-platina-progresso.json", "JSON (*.json)",
        )
        if not path:
            return
        payload = {
            "guide": guide_data.GUIDE_ID,
            "version": 1,
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "state": {key: True for key in sorted(self._done)},
        }
        try:
            Path(path).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as error:
            QMessageBox.warning(self, "Exportar", f"Não foi possível salvar: {error}")

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar progresso", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            QMessageBox.warning(self, "Importar", "Arquivo JSON inválido.")
            return
        state = raw.get("state", raw) if isinstance(raw, dict) else raw
        self._done = keys.normalize_imported(state)
        save_progress(self._done)
        self._refresh_boxes()

    def _reset(self) -> None:
        answer = QMessageBox.question(
            self, "Resetar", "Apagar todas as marcações deste guia?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._done = set()
        save_progress(self._done)
        self._refresh_boxes()

    # ------------------------------------------------------------- busca geral
    def _global_search(self) -> None:
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        query = _norm(self.global_search.text()).strip()
        if len(query) < 2:
            self.results_box.hide()
            return

        hits: list[tuple[str, str, str, str, str]] = []
        for step in guide_data.ROUTE:
            if query in _norm(_flat(step)):
                hits.append((f"PASSO {step['num']}", step["title"], step["place"],
                             step["exact"], "route"))
        for trophy in guide_data.TROPHIES:
            if query in _norm(_flat(trophy)):
                hits.append(("TROFÉU", trophy["name"], trophy["tier"].upper(),
                             f"{trophy['requirement']} {trophy['shortcut']}", "trophies"))
        for item in guide_data.COLLECTIBLES:
            if query in _norm(_flat(item)):
                hits.append((item["kind"].upper(), item["name"], item["mission"],
                             item["where"], "collectibles"))
        for mission in guide_data.MISSIONS:
            if query in _norm(_flat(mission)):
                hits.append(("BATALHA", mission["name"],
                             f"{mission['kind']} · nível {mission['level']}",
                             mission["note"] or mission["part"], "flags"))

        if not hits:
            self.results_layout.addWidget(
                _notice("Nada encontrado. Tente o nome de uma batalha, troféu ou coletável.")
            )
            self.results_box.show()
            return

        for kind, name, where, text, page in hits[:_SEARCH_LIMIT]:
            frame, layout = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(_label(kind, "Kicker", wrap=False))
            head.addWidget(_label(f"<b>{_esc(name)}</b>", "SectionTitle"), 1)
            if where:
                head.addWidget(_pill(where))
            layout.addLayout(head)
            layout.addWidget(_label(text, "Muted"))
            go = QPushButton(
                f"Ir para “{guide_data.SECTIONS[self._section_index[page]]['nav']}”"
            )
            go.clicked.connect(
                lambda _=False, target=page: self.show_section(self._section_index[target])
            )
            row = QHBoxLayout()
            row.addWidget(go)
            row.addStretch(1)
            layout.addLayout(row)
            self.results_layout.addWidget(frame)
        if len(hits) > _SEARCH_LIMIT:
            self.results_layout.addWidget(
                _label(f"…e mais {len(hits) - _SEARCH_LIMIT} resultado(s). Refine a busca.",
                       "Muted")
            )
        self.results_box.show()

    # ---------------------------------------------------------------- imagens
    def _add_image(self, layout, url: str, max_w: int = _IMG_MAX_W,
                   max_h: int = _IMG_MAX_H) -> None:
        if not url:
            return
        holder = QLabel("Carregando imagem…")
        holder.setObjectName("Muted")
        layout.addWidget(holder)
        state = {"loaded": False}

        def show(pixmap: QPixmap) -> None:
            state["loaded"] = True
            holder.setText("")
            holder.setPixmap(pixmap.scaled(
                max_w, max_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

        cached = self._image_loader.load(url, show)
        if cached is not None:
            show(cached)
            return

        def timeout() -> None:
            if not state["loaded"]:
                holder.setText(
                    f'Imagem indisponível offline — <a href="{_esc(url)}" '
                    f'style="color:{guide_data.ACCENT}">abrir no navegador</a>')
                holder.setOpenExternalLinks(True)

        QTimer.singleShot(_IMG_TIMEOUT_MS, timeout)

    # ------------------------------------------------------- construção lazy
    def _ensure_built(self, index: int) -> None:
        if index in self._built or index < 0:
            return
        self._built.add(index)
        holder = self._holders[index]
        # Troca o "Carregando…" pelo conteúdo real. Esvaziar o layout (em vez de
        # trocar a página do QStackedWidget) evita depender de deleteLater().
        while holder.count():
            item = holder.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        key = guide_data.SECTIONS[index]["key"]
        builder = getattr(self, f"_build_{key}")
        holder.addWidget(
            _scroll_page(lambda layout: self._with_header(layout, index, builder))
        )
        self._update_progress()

    def _with_header(self, layout: QVBoxLayout, index: int, builder) -> None:
        section = guide_data.SECTIONS[index]
        layout.addWidget(_label(section["eyebrow"], "Kicker", wrap=False))
        layout.addWidget(_label(section["title"], "CardTitle"))
        layout.addWidget(_label(section["lead"], "Muted"))
        for notice in section["notices"]:
            layout.addWidget(_notice(notice["text"], notice["tone"]))
        builder(layout)

    # ------------------------------------------------------- 01 Passo a passo
    def _build_route(self, layout: QVBoxLayout) -> None:
        phases: dict[str, list[dict]] = {}
        for step in guide_data.ROUTE:
            phases.setdefault(step["phase"], []).append(step)

        for phase, steps in phases.items():
            phase_keys = [keys.step_key(step["num"]) for step in steps]
            head_holder = QWidget()
            head_holder.setStyleSheet(_PHASE_QSS)
            head_row = QHBoxLayout(head_holder)
            head_row.setContentsMargins(0, 0, 0, 0)
            head_row.setSpacing(8)
            toggle = QPushButton(f"{phase}   ({len(steps)} passos)")
            toggle.setObjectName("PhaseHead")
            pill = _pill("")
            head_row.addWidget(toggle, 1)
            head_row.addWidget(pill, 0)
            layout.addWidget(head_holder)
            self._phase_pills.append((pill, phase_keys))

            body = QWidget()
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(0, 0, 0, 0)
            body_layout.setSpacing(8)
            for step in steps:
                body_layout.addWidget(self._route_step(step))
            layout.addWidget(body)
            toggle.clicked.connect(
                lambda _=False, target=body: target.setVisible(not target.isVisible())
            )

    def _route_step(self, step: dict) -> QFrame:
        frame, layout = _card()
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._checkbox(keys.step_key(step["num"])), 0,
                       Qt.AlignmentFlag.AlignTop)
        head.addWidget(_label(step["num"], "Kicker", wrap=False), 0,
                       Qt.AlignmentFlag.AlignTop)
        head.addWidget(_label(step["title"], "SectionTitle"), 1)
        head.addWidget(_pill(step["place"]), 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(head)
        _detail(layout, "Quando", step["when"])
        _detail(layout, "Faça exatamente", step["exact"])
        _detail(layout, "Por que agora", step["why"])
        image = step.get("image", "")
        if image:
            small = "community_assets" in image  # ícone de conquista
            self._add_image(layout, image, _ICON if small else _IMG_MAX_W,
                            _ICON if small else _IMG_MAX_H)
        return frame

    # -------------------------------------------------------- 02 Coletáveis
    def _build_collectibles(self, layout: QVBoxLayout) -> None:
        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Buscar item, missão ou local...")
        self.item_search.textChanged.connect(self._filter_items)
        self.item_kind = QComboBox()
        self.item_kind.addItem("Todos os tipos", "")
        for kind in ("Tábua", "Shitieshou", "Casca"):
            self.item_kind.addItem(kind, kind)
        self.item_kind.currentIndexChanged.connect(self._filter_items)
        self.item_mission = QComboBox()
        self.item_mission.addItem("Todas as batalhas", "")
        for mission in dict.fromkeys(c["mission"] for c in guide_data.COLLECTIBLES):
            self.item_mission.addItem(mission, mission)
        self.item_mission.currentIndexChanged.connect(self._filter_items)
        self.item_pending = QCheckBox("só pendentes")
        self.item_pending.toggled.connect(self._filter_items)
        filters.addWidget(self.item_search, 1)
        filters.addWidget(self.item_kind, 0)
        filters.addWidget(self.item_pending, 0)
        layout.addLayout(filters)
        layout.addWidget(self.item_mission)

        self.item_empty = _label("Nenhum coletável corresponde ao filtro.", "Muted")
        self.item_empty.hide()
        layout.addWidget(self.item_empty)

        for i, item in enumerate(guide_data.COLLECTIBLES):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.collectible_key(i)), 0,
                           Qt.AlignmentFlag.AlignTop)
            head.addWidget(_tag(item["kind"], _KIND_COLORS.get(item["kind"], "#A8B0BC")),
                           0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(item["name"], "SectionTitle"), 1)
            card.addLayout(head)
            _detail(card, "Batalha", item["mission"])
            _detail(card, "Onde", item["where"])
            layout.addWidget(frame)
            self._item_rows.append(
                (frame, _norm(_flat(item)), item["kind"], item["mission"], i)
            )

    def _filter_items(self) -> None:
        query = _norm(self.item_search.text()).strip()
        kind = self.item_kind.currentData() or ""
        mission = self.item_mission.currentData() or ""
        pending = self.item_pending.isChecked()
        visible = 0
        for frame, haystack, row_kind, row_mission, index in self._item_rows:
            got = keys.collectible_key(index) in self._done
            show = (query in haystack
                    and (not kind or row_kind == kind)
                    and (not mission or row_mission == mission)
                    and (not pending or not got))
            frame.setVisible(show)
            visible += int(show)
        self.item_empty.setVisible(visible == 0)

    # ---------------------------------------------------------- 03 Troféus
    def _build_trophies(self, layout: QVBoxLayout) -> None:
        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.trophy_search = QLineEdit()
        self.trophy_search.setPlaceholderText("Buscar troféu ou requisito...")
        self.trophy_search.textChanged.connect(self._filter_trophies)
        self.trophy_tier = QComboBox()
        self.trophy_tier.addItem("Todos os tiers", "")
        for tier in ("platina", "ouro", "prata", "bronze"):
            self.trophy_tier.addItem(tier.capitalize(), tier)
        self.trophy_tier.currentIndexChanged.connect(self._filter_trophies)
        self.trophy_pending = QCheckBox("só pendentes")
        self.trophy_pending.toggled.connect(self._filter_trophies)
        filters.addWidget(self.trophy_search, 1)
        filters.addWidget(self.trophy_tier, 0)
        filters.addWidget(self.trophy_pending, 0)
        layout.addLayout(filters)

        self.trophy_empty = _label("Nenhum troféu corresponde ao filtro.", "Muted")
        self.trophy_empty.hide()
        layout.addWidget(self.trophy_empty)

        for trophy in guide_data.TROPHIES:
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(10)
            head.addWidget(self._checkbox(keys.trophy_key(trophy["id"])), 0,
                           Qt.AlignmentFlag.AlignTop)
            if trophy["image"]:
                icon = QVBoxLayout()
                self._add_image(icon, trophy["image"], _ICON, _ICON)
                icon.addStretch(1)
                head.addLayout(icon, 0)
            head.addWidget(_label(trophy["name"], "SectionTitle"), 1)
            head.addWidget(_tag(trophy["tier"], _TIER_COLORS.get(trophy["tier"], "#A8B0BC")),
                           0, Qt.AlignmentFlag.AlignTop)
            card.addLayout(head)
            _detail(card, "Requisito", trophy["requirement"])
            _detail(card, "Como fazer", trophy["shortcut"])
            layout.addWidget(frame)
            self._trophy_rows.append((frame, _norm(_flat(trophy)), trophy["id"]))

    def _filter_trophies(self) -> None:
        query = _norm(self.trophy_search.text()).strip()
        tier = self.trophy_tier.currentData() or ""
        pending = self.trophy_pending.isChecked()
        visible = 0
        for (frame, haystack, trophy_id), trophy in zip(self._trophy_rows,
                                                        guide_data.TROPHIES):
            got = keys.trophy_key(trophy_id) in self._done
            show = (query in haystack
                    and (not tier or trophy["tier"] == tier)
                    and (not pending or not got))
            frame.setVisible(show)
            visible += int(show)
        self.trophy_empty.setVisible(visible == 0)

    # --------------------------------------------------------- 04 Bandeiras
    def _build_flags(self, layout: QVBoxLayout) -> None:
        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.flag_search = QLineEdit()
        self.flag_search.setPlaceholderText("Buscar batalha...")
        self.flag_search.textChanged.connect(self._filter_flags)
        self.flag_pending = QCheckBox("só pendentes")
        self.flag_pending.toggled.connect(self._filter_flags)
        filters.addWidget(self.flag_search, 1)
        filters.addWidget(self.flag_pending, 0)
        layout.addLayout(filters)

        self.flag_empty = _label("Nenhuma batalha corresponde ao filtro.", "Muted")
        self.flag_empty.hide()
        layout.addWidget(self.flag_empty)

        for i, mission in enumerate(guide_data.MISSIONS):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.flag_key(i)), 0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(_tag(mission["kind"],
                                "#E7C64A" if mission["kind"] == "principal" else "#A8B0BC"),
                           0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(mission["name"], "SectionTitle"), 1)
            head.addWidget(_pill(f"nível {mission['level']}"), 0, Qt.AlignmentFlag.AlignTop)
            card.addLayout(head)
            _detail(card, "Parte", mission["part"])
            layout.addWidget(frame)
            self._flag_rows.append((frame, _norm(_flat(mission)), i))

    def _filter_flags(self) -> None:
        query = _norm(self.flag_search.text()).strip()
        pending = self.flag_pending.isChecked()
        visible = 0
        for frame, haystack, index in self._flag_rows:
            got = keys.flag_key(index) in self._done
            show = query in haystack and (not pending or not got)
            frame.setVisible(show)
            visible += int(show)
        self.flag_empty.setVisible(visible == 0)

    # ------------------------------------------------------ 05 Companheiros
    def _build_companions(self, layout: QVBoxLayout) -> None:
        layout.addWidget(_notice(
            "Método rápido do Great Gatherings: depois de terminar a história, vá à "
            "bandeira da Vila Oculta, escolha a missão tutorial (The Village of Calamity) "
            "na dificuldade Dragão Ascendente, chame um companheiro, comece e saia. "
            "Não precisa terminar a missão — basta ter chamado. Repita com os 17."))
        total = len(guide_data.COMPANIONS)
        for i, ally in enumerate(guide_data.COMPANIONS):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.companion_key(i)), 0,
                           Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(f"{i + 1}/{total}", "Kicker", wrap=False), 0)
            head.addWidget(_label(ally["name"], "SectionTitle"), 1)
            card.addLayout(head)
            _detail(card, "Fica disponível em", ally["when"])
            layout.addWidget(frame)

    # ---------------------------------------------------------- 06 Feitiços
    def _build_spells(self, layout: QVBoxLayout) -> None:
        layout.addWidget(_notice(
            "Onde aprender: em qualquer bandeira, Feitiços → Aprender. Os Pontos de "
            "Feitiço vêm de subir de nível, e por volta do nível 80 você tem pontos "
            "para os 70."))
        for i, phase in enumerate(guide_data.PHASES):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.phase_key(i)), 0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(phase["name"], "SectionTitle"), 1)
            head.addWidget(_pill(phase["spells"]), 0, Qt.AlignmentFlag.AlignTop)
            card.addLayout(head)
            _detail(card, "Papel", phase["note"])
            layout.addWidget(frame)

    # ------------------------------------------------------------ 07 Preparo
    def _build_prep(self, layout: QVBoxLayout) -> None:
        for i, item in enumerate(guide_data.PREP):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.prep_key(i)), 0, Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(item["name"], "SectionTitle"), 1)
            head.addWidget(_pill(item["when"]), 0, Qt.AlignmentFlag.AlignTop)
            card.addLayout(head)
            _detail(card, "Por quê", item["why"])
            layout.addWidget(frame)

    # ------------------------------------------------------------ 08 Imagens
    def _build_visuals(self, layout: QVBoxLayout) -> None:
        for visual in guide_data.VISUALS:
            frame, card = _card()
            card.addWidget(_label(visual["title"], "SectionTitle"))
            card.addWidget(_label(visual["caption"], "Muted"))
            self._add_image(card, visual["image"])
            card.addWidget(_label(f"Fonte da imagem: {visual['source']}", "Muted"))
            layout.addWidget(frame)

    # ------------------------------------------------------------ 09 Fontes
    def _build_sources(self, layout: QVBoxLayout) -> None:
        for source in guide_data.SOURCES:
            frame, card = _card()
            card.addWidget(_label(source["title"], "SectionTitle"))
            card.addWidget(_label(source["note"], "Muted"))
            card.addWidget(_link("Abrir fonte ↗", source["url"]))
            layout.addWidget(frame)
