"""Página do guia: 4 abas, com a batalha como unidade central."""
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

_PHOTO_W = 560
_PHOTO_H = 316
_ICON = 44
_IMG_TIMEOUT_MS = 26000
_SEARCH_LIMIT = 18

_TIER_COLORS = {
    "bronze": "#C77B3B", "prata": "#B8C0CC", "ouro": "#E7C64A", "platina": "#7FE7FF",
}
_KIND_COLORS = {"Tábua": "#E7C64A", "Shitieshou": "#B9FF43", "Casca": "#37F2FF"}
# bandeira de Batalha é checkpoint (vermelho do jogo); a de Marcação só sobe Fortitude
_FLAG_COLORS = {"Batalha": "#F87171", "Marcação": "#7FE7FF"}

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
    "QPushButton#NavButton:checked{background:#101922;border-color:%s;color:#F3F6FF;"
    "font-weight:600}" % guide_data.ACCENT
)
_PHASE_QSS = (
    "QPushButton#PhaseHead{background:#101922;border:1px solid #273140;border-radius:9px;"
    "padding:10px 12px;color:#F3F6FF;text-align:left;font-weight:600}"
    "QPushButton#PhaseHead:hover{border-color:%s}" % guide_data.ACCENT
)
# o bloco de um coletável dentro do card da batalha
_ITEM_QSS = (
    "QFrame#ItemBlock{background:#0B111A;border:1px solid #1E2733;border-radius:8px}"
)


def _norm(text) -> str:
    stripped = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in stripped if not unicodedata.combining(c)).lower()


def _esc(text) -> str:
    return html.escape(str(text or ""))


def _flat(value) -> str:
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
    label = QLabel(f'<a href="{_esc(url)}" style="color:{guide_data.ACCENT}">{_esc(text)}</a>')
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
        "border-left:3px solid %s;border-radius:10px}" % color)
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
        self._part_pills: list[tuple[QLabel, list[str]]] = []
        self._mission_rows: list[tuple[QWidget, str, str, int]] = []
        self._part_groups: list[tuple[QWidget, QWidget, list[int]]] = []
        self._trophy_rows: list[tuple[QWidget, str, str]] = []
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
            "Buscar batalha, troféu ou coletável... Ex.: Guandu, tábua, Lu Bu, Shitieshou")
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
        for text, slot in (("Exportar progresso", self._export),
                           ("Importar progresso", self._import),
                           ("Resetar marcações", self._reset)):
            button = QPushButton(text)
            button.clicked.connect(slot)
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
            grid.addWidget(button, 0, i)
            self._nav_buttons.append(button)
            grid.setColumnStretch(i, 1)
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
        self.trophy_label.setText(
            f"{sum(1 for k in trophies if k in self._done)}/{len(trophies)} troféus")
        items = keys.collectible_keys()
        self.item_label.setText(
            f"{sum(1 for k in items if k in self._done)}/{len(items)} coletáveis")
        for pill, part_keys in self._part_pills:
            part_done = sum(1 for key in part_keys if key in self._done)
            pill.setText(f"{part_done}/{len(part_keys)}")

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
        if self._mission_rows:
            self._filter_missions()

    # ------------------------------------------------------ exportar/importar
    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar progresso", "wolong-platina-progresso.json", "JSON (*.json)")
        if not path:
            return
        payload = {
            "guide": guide_data.GUIDE_ID, "version": 2,
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "state": {key: True for key in sorted(self._done)},
        }
        try:
            Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Exportar", f"Não foi possível salvar: {error}")

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importar progresso", "", "JSON (*.json)")
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
        if QMessageBox.question(self, "Resetar",
                                "Apagar todas as marcações deste guia?") != \
                QMessageBox.StandardButton.Yes:
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
        for mission in guide_data.MISSIONS:
            if query in _norm(_flat(mission)):
                hits.append(("BATALHA", mission["name"],
                             f"{mission['kind']} · nível {mission['level']}",
                             mission["note"] or mission["part"], "battles"))
        for item in guide_data.COLLECTIBLES:
            if query in _norm(_flat(item)):
                hits.append((item["kind"].upper(), item["name"], item["mission"],
                             item["where"], "battles"))
        for trophy in guide_data.TROPHIES:
            if query in _norm(_flat(trophy)):
                hits.append(("TROFÉU", trophy["name"], trophy["tier"].upper(),
                             f"{trophy['requirement']} {trophy['shortcut']}", "trophies"))

        if not hits:
            self.results_layout.addWidget(
                _notice("Nada encontrado. Tente o nome de uma batalha, troféu ou coletável."))
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
                f"Ir para “{guide_data.SECTIONS[self._section_index[page]]['nav']}”")
            go.clicked.connect(
                lambda _=False, target=page: self.show_section(self._section_index[target]))
            row = QHBoxLayout()
            row.addWidget(go)
            row.addStretch(1)
            layout.addLayout(row)
            self.results_layout.addWidget(frame)
        if len(hits) > _SEARCH_LIMIT:
            self.results_layout.addWidget(
                _label(f"…e mais {len(hits) - _SEARCH_LIMIT} resultado(s). Refine a busca.",
                       "Muted"))
        self.results_box.show()

    # ---------------------------------------------------------------- imagens
    def _add_image(self, layout, url: str, max_w: int = _PHOTO_W,
                   max_h: int = _PHOTO_H) -> None:
        if not url:
            return
        holder = QLabel("Carregando foto…")
        holder.setObjectName("Muted")
        layout.addWidget(holder)
        state = {"loaded": False}

        def show(pixmap: QPixmap) -> None:
            state["loaded"] = True
            holder.setText("")
            holder.setPixmap(pixmap.scaled(
                max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

        cached = self._image_loader.load(url, show)
        if cached is not None:
            show(cached)
            return

        def timeout() -> None:
            if not state["loaded"]:
                holder.setText(
                    f'Foto indisponível offline — <a href="{_esc(url)}" '
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
        builder = getattr(self, f"_build_{guide_data.SECTIONS[index]['key']}")
        holder.addWidget(_scroll_page(lambda layout: self._with_header(layout, index, builder)))
        self._update_progress()

    def _with_header(self, layout: QVBoxLayout, index: int, builder) -> None:
        section = guide_data.SECTIONS[index]
        layout.addWidget(_label(section["eyebrow"], "Kicker", wrap=False))
        layout.addWidget(_label(section["title"], "CardTitle"))
        layout.addWidget(_label(section["lead"], "Muted"))
        for notice in section["notices"]:
            layout.addWidget(_notice(notice["text"], notice["tone"]))
        builder(layout)

    # ═══════════════════════════════════════════════════════ 01 Batalhas
    def _build_battles(self, layout: QVBoxLayout) -> None:
        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.mission_search = QLineEdit()
        self.mission_search.setPlaceholderText("Buscar batalha ou coletável dela...")
        self.mission_search.textChanged.connect(self._filter_missions)
        self.mission_part = QComboBox()
        self.mission_part.addItem("Todas as partes", "")
        for part in dict.fromkeys(m["part"] for m in guide_data.MISSIONS):
            self.mission_part.addItem(part, part)
        self.mission_part.currentIndexChanged.connect(self._filter_missions)
        self.mission_pending = QCheckBox("só pendentes")
        self.mission_pending.toggled.connect(self._filter_missions)
        filters.addWidget(self.mission_search, 1)
        filters.addWidget(self.mission_part, 0)
        filters.addWidget(self.mission_pending, 0)
        layout.addLayout(filters)

        self.mission_empty = _label("Nenhuma batalha corresponde ao filtro.", "Muted")
        self.mission_empty.hide()
        layout.addWidget(self.mission_empty)

        parts: dict[str, list[tuple[int, dict]]] = {}
        for i, mission in enumerate(guide_data.MISSIONS):
            parts.setdefault(mission["part"], []).append((i, mission))

        for part, entries in parts.items():
            part_keys = [keys.mission_key(i) for i, _ in entries]
            head_holder = QWidget()
            head_holder.setStyleSheet(_PHASE_QSS)
            head_row = QHBoxLayout(head_holder)
            head_row.setContentsMargins(0, 0, 0, 0)
            head_row.setSpacing(8)
            plural = "batalha" if len(entries) == 1 else "batalhas"
            toggle = QPushButton(f"Parte {part}   ({len(entries)} {plural})")
            toggle.setObjectName("PhaseHead")
            pill = _pill("")
            head_row.addWidget(toggle, 1)
            head_row.addWidget(pill, 0)
            layout.addWidget(head_holder)
            self._part_pills.append((pill, part_keys))

            body = QWidget()
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(0, 0, 0, 0)
            body_layout.setSpacing(8)
            for i, mission in entries:
                card = self._mission_card(i, mission)
                body_layout.addWidget(card)
                haystack = _norm(" ".join([
                    _flat(mission),
                    " ".join(_flat(c) for _, c in keys.collectibles_of(mission["name"])),
                    " ".join(_flat(f) for f in keys.flags_of(mission["name"])),
                ]))
                self._mission_rows.append((card, haystack, mission["part"], i))
            layout.addWidget(body)
            self._part_groups.append((head_holder, body, [i for i, _ in entries]))
            toggle.clicked.connect(
                lambda _=False, target=body: (
                    target.setProperty("collapsed", target.isVisible()),
                    target.setVisible(not target.isVisible())))

        # a base e o fecho fecham a aba
        layout.addWidget(self._hub_card())
        layout.addWidget(_label("Fecho — depois da história", "CardTitle"))
        layout.addWidget(_label(
            "O que sobra quando a campanha acaba. Se você seguiu a rotina de cada batalha, "
            "aqui é rápido.", "Muted"))
        for i, step in enumerate(guide_data.CLOSE):
            layout.addWidget(self._close_card(i, step))

    def _mission_card(self, index: int, mission: dict) -> QFrame:
        frame, card = _card()
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._checkbox(keys.mission_key(index)), 0, Qt.AlignmentFlag.AlignTop)
        principal = mission["kind"] == "principal"
        head.addWidget(_tag(mission["kind"], "#E7C64A" if principal else "#A8B0BC"), 0,
                       Qt.AlignmentFlag.AlignTop)
        title = ("★ " if principal else "") + mission["name"]
        head.addWidget(_label(title, "SectionTitle"), 1)
        head.addWidget(_pill(f"nível {mission['level']}"), 0, Qt.AlignmentFlag.AlignTop)
        card.addLayout(head)

        if mission["note"]:
            card.addWidget(_notice(mission["note"],
                                   "red" if principal or "não pule" in mission["note"].lower()
                                   else "info"))
        if mission["trophies"]:
            _detail(card, "Troféus aqui", ", ".join(mission["trophies"]))

        self._add_flags(card, index, mission)

        found = keys.collectibles_of(mission["name"])
        if found:
            card.addWidget(_label(f"<b>Coletáveis ({len(found)}):</b>", "Muted"))
            for item_index, item in found:
                card.addWidget(self._item_block(item_index, item))
        return frame

    def _add_flags(self, card: QVBoxLayout, index: int, mission: dict) -> None:
        """As bandeiras da batalha: uma linha com foto para cada, quando há guia."""
        detalhadas = keys.flags_of(mission["name"])
        if not detalhadas:
            card.addWidget(self._checkbox(
                keys.flag_key(index), "Todas as bandeiras desta batalha erguidas"))
            card.addWidget(_label(
                "Esta batalha não tem guia de bandeira publicado — confira o total na tela "
                "de seleção de missão do jogo.", "Muted"))
            return
        info = guide_data.FLAGS[mission["name"]]
        card.addWidget(_label(
            f"<b>Bandeiras ({info['battle']} de Batalha + {info['marking']} de Marcação):</b>",
            "Muted"))
        for j, flag in enumerate(detalhadas):
            card.addWidget(self._flag_block(index, j, flag))

    def _flag_block(self, mission_index: int, flag_index: int, flag: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("ItemBlock")
        frame.setStyleSheet(_ITEM_QSS)
        box = QVBoxLayout(frame)
        box.setContentsMargins(11, 9, 11, 9)
        box.setSpacing(5)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._checkbox(keys.one_flag_key(mission_index, flag_index)), 0,
                       Qt.AlignmentFlag.AlignTop)
        head.addWidget(_tag(flag["kind"], _FLAG_COLORS.get(flag["kind"], "#A8B0BC")), 0,
                       Qt.AlignmentFlag.AlignTop)
        head.addWidget(_label(f"Bandeira de {flag['kind']} #{flag['num']}", "SectionTitle"), 1)
        box.addLayout(head)
        box.addWidget(_label(flag["where"], "Muted"))
        self._add_image(box, flag["image"])
        return frame

    def _item_block(self, index: int, item: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("ItemBlock")
        frame.setStyleSheet(_ITEM_QSS)
        box = QVBoxLayout(frame)
        box.setContentsMargins(11, 9, 11, 9)
        box.setSpacing(5)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._checkbox(keys.collectible_key(index)), 0,
                       Qt.AlignmentFlag.AlignTop)
        head.addWidget(_tag(item["kind"], _KIND_COLORS.get(item["kind"], "#A8B0BC")), 0,
                       Qt.AlignmentFlag.AlignTop)
        name = item["name"] if item["name"] != item["kind"] else ""
        head.addWidget(_label(name or item["kind"], "SectionTitle"), 1)
        box.addLayout(head)
        box.addWidget(_label(item["where"], "Muted"))
        self._add_image(box, item["image"])
        return frame

    def _hub_card(self) -> QFrame:
        hub = guide_data.HUB_ENTRY
        frame, card = _card()
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._checkbox(keys.HUB_KEY), 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(_tag("base", "#7FE7FF"), 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(_label(hub["name"], "SectionTitle"), 1)
        card.addLayout(head)
        card.addWidget(_label(hub["note"], "Muted"))
        found = keys.collectibles_of(hub["name"])
        if found:
            card.addWidget(_label(f"<b>Coletáveis ({len(found)}):</b>", "Muted"))
            for item_index, item in found:
                card.addWidget(self._item_block(item_index, item))
        return frame

    def _close_card(self, index: int, step: dict) -> QFrame:
        frame, card = _card()
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(self._checkbox(keys.close_key(index)), 0, Qt.AlignmentFlag.AlignTop)
        icon_url = ""
        for trophy in guide_data.TROPHIES:
            if trophy["name"].lower() == step["icon"].lower():
                icon_url = trophy["image"]
                break
        if icon_url:
            icon = QVBoxLayout()
            self._add_image(icon, icon_url, _ICON, _ICON)
            icon.addStretch(1)
            head.addLayout(icon, 0)
        head.addWidget(_label(step["name"], "SectionTitle"), 1)
        head.addWidget(_pill(step["where"]), 0, Qt.AlignmentFlag.AlignTop)
        card.addLayout(head)
        _detail(card, "Por quê", step["why"])
        return frame

    def _filter_missions(self) -> None:
        query = _norm(self.mission_search.text()).strip()
        part = self.mission_part.currentData() or ""
        pending = self.mission_pending.isChecked()
        visible = 0
        self._mission_visible: dict[int, bool] = {}
        for frame, haystack, row_part, index in self._mission_rows:
            done = keys.mission_key(index) in self._done
            show = (query in haystack and (not part or row_part == part)
                    and (not pending or not done))
            frame.setVisible(show)
            self._mission_visible[index] = show
            visible += int(show)
        # esconde a Parte inteira quando nenhuma batalha dela sobrou no filtro
        for head, body, indices in self._part_groups:
            any_visible = any(self._mission_visible.get(i) for i in indices)
            head.setVisible(any_visible)
            body.setVisible(any_visible and not body.property("collapsed"))
        self.mission_empty.setVisible(visible == 0)

    # ═══════════════════════════════════════════════════════ 02 Troféus
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
            show = (query in haystack and (not tier or trophy["tier"] == tier)
                    and (not pending or not got))
            frame.setVisible(show)
            visible += int(show)
        self.trophy_empty.setVisible(visible == 0)

    # ═══════════════════════════════════════════════════════ 03 Sistemas
    def _build_systems(self, layout: QVBoxLayout) -> None:
        layout.addWidget(_label("Hábitos que decidem a run", "CardTitle"))
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

        layout.addWidget(_label("As Cinco Fases — 70 feitiços", "CardTitle"))
        layout.addWidget(_notice(
            "Em qualquer bandeira: Feitiços → Aprender. Os Pontos de Feitiço vêm de subir de "
            "nível; por volta do 80 você tem para os 70. Marque a fase quando comprar os 14 "
            "dela. Sem a batalha Wizardry Spell Mastery, os tiers altos nem aparecem."))
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

        layout.addWidget(_label("Os 17 companheiros", "CardTitle"))
        layout.addWidget(_notice(
            "Great Gatherings: basta CHAMAR cada um uma vez. Depois da história, use a "
            "missão tutorial na dificuldade Dragão Ascendente — chame, comece e saia."))
        total = len(guide_data.COMPANIONS)
        for i, ally in enumerate(guide_data.COMPANIONS):
            frame, card = _card()
            head = QHBoxLayout()
            head.setSpacing(8)
            head.addWidget(self._checkbox(keys.companion_key(i)), 0,
                           Qt.AlignmentFlag.AlignTop)
            head.addWidget(_label(f"{i + 1}/{total}", "Kicker", wrap=False), 0)
            head.addWidget(_label(ally["name"], "SectionTitle"), 1)
            head.addWidget(_pill(ally["when"]), 0, Qt.AlignmentFlag.AlignTop)
            card.addLayout(head)
            layout.addWidget(frame)

    # ═══════════════════════════════════════════════════════ 04 Fontes
    def _build_sources(self, layout: QVBoxLayout) -> None:
        for source in guide_data.SOURCES:
            frame, card = _card()
            card.addWidget(_label(source["title"], "SectionTitle"))
            card.addWidget(_label(source["note"], "Muted"))
            card.addWidget(_link("Abrir fonte ↗", source["url"]))
            layout.addWidget(frame)
