"""Chaves de progresso do guia.

A espinha do guia é a batalha: cada uma tem a própria caixa de "concluída", a de
"bandeiras completas" e as caixas dos coletáveis que estão dentro dela. Este
módulo centraliza o formato das chaves para que `module.py`, `page.py` e o
importador/exportador falem a mesma língua.
"""
from __future__ import annotations

from . import guide_data

HUB_KEY = "hub"


def mission_key(index: int) -> str:
    return f"mission_{index}"


def flag_key(index: int) -> str:
    """Caixa única de "todas as bandeiras" — usada nas batalhas sem guia detalhado."""
    return f"flags_{index}"


def one_flag_key(mission_index: int, flag_index: int) -> str:
    """Uma bandeira específica de uma batalha."""
    return f"flag_{mission_index}_{flag_index}"


def flags_of(mission_name: str) -> list[dict]:
    """As bandeiras detalhadas de uma batalha (vazio se não houver guia)."""
    return guide_data.FLAGS.get(mission_name, {}).get("flags", [])


def collectible_key(index: int) -> str:
    return f"item_{index}"


def close_key(index: int) -> str:
    return f"close_{index}"


def trophy_key(trophy_id: str) -> str:
    return f"trophy_{trophy_id}"


def companion_key(index: int) -> str:
    return f"ally_{index}"


def phase_key(index: int) -> str:
    return f"phase_{index}"


def prep_key(index: int) -> str:
    return f"prep_{index}"


def trophy_keys() -> list[str]:
    return [trophy_key(t["id"]) for t in guide_data.TROPHIES]


def collectible_keys(kind: str | None = None) -> list[str]:
    """Chaves dos coletáveis; opcionalmente só de um tipo (Tábua/Shitieshou/Casca)."""
    return [
        collectible_key(i)
        for i, c in enumerate(guide_data.COLLECTIBLES)
        if kind is None or c["kind"] == kind
    ]


def collectibles_of(mission_name: str) -> list[tuple[int, dict]]:
    """Os coletáveis de uma batalha, com o índice global de cada um."""
    return [
        (i, c) for i, c in enumerate(guide_data.COLLECTIBLES)
        if c["mission"] == mission_name
    ]


def all_keys() -> list[str]:
    """Todas as chaves marcáveis do guia, na ordem das abas."""
    keys: list[str] = []
    for i, mission in enumerate(guide_data.MISSIONS):
        keys.append(mission_key(i))
        detalhadas = flags_of(mission["name"])
        if detalhadas:
            keys += [one_flag_key(i, j) for j in range(len(detalhadas))]
        else:
            keys.append(flag_key(i))
    keys.append(HUB_KEY)
    keys += collectible_keys()
    keys += [close_key(i) for i in range(len(guide_data.CLOSE))]
    keys += trophy_keys()
    keys += [companion_key(i) for i in range(len(guide_data.COMPANIONS))]
    keys += [phase_key(i) for i in range(len(guide_data.PHASES))]
    keys += [prep_key(i) for i in range(len(guide_data.PREP))]
    return keys


def normalize_imported(raw) -> set[str]:
    """Aceita o formato deste plugin e um dicionário `{chave: bool}`."""
    if isinstance(raw, dict):
        raw = [key for key, value in raw.items() if value]
    return {str(key) for key in raw}
