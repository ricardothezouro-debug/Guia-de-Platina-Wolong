"""Chaves de progresso do guia.

O guia tem itens marcáveis em sete listas (rota, coletáveis, troféus, bandeiras
por batalha, companheiros, fases e preparo). Este módulo centraliza o formato
das chaves para que `module.py`, `page.py` e o importador/exportador falem a
mesma língua.
"""
from __future__ import annotations

from . import guide_data


def step_key(num: str) -> str:
    return "step_" + str(num).replace(".", "_")


def collectible_key(index: int) -> str:
    return f"item_{index}"


def trophy_key(trophy_id: str) -> str:
    return f"trophy_{trophy_id}"


def flag_key(index: int) -> str:
    return f"flags_{index}"


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


def flag_keys() -> list[str]:
    return [flag_key(i) for i in range(len(guide_data.MISSIONS))]


def all_keys() -> list[str]:
    """Todas as chaves marcáveis do guia, na ordem das abas."""
    keys = [step_key(step["num"]) for step in guide_data.ROUTE]
    keys += collectible_keys()
    keys += trophy_keys()
    keys += flag_keys()
    keys += [companion_key(i) for i in range(len(guide_data.COMPANIONS))]
    keys += [phase_key(i) for i in range(len(guide_data.PHASES))]
    keys += [prep_key(i) for i in range(len(guide_data.PREP))]
    return keys


def normalize_imported(raw) -> set[str]:
    """Aceita o formato deste plugin e um dicionário `{chave: bool}`."""
    if isinstance(raw, dict):
        raw = [key for key, value in raw.items() if value]
    return {str(key) for key in raw}
