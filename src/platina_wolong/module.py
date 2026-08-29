"""Adaptador de plugin do Streamer Sidekick (categoria: platina)."""
from dataclasses import dataclass

from . import guide_data

MODULE_ID = guide_data.GUIDE_ID


@dataclass(frozen=True)
class ModuleInfo:
    module_id: str
    title: str
    subtitle: str
    status: str
    accent: str


def module_info():
    from .progress import trophy_keys
    from .storage import load_progress

    done_keys = load_progress()
    trophies = trophy_keys()
    done = sum(1 for key in trophies if key in done_keys)
    data = dict(
        module_id=guide_data.GUIDE_ID,
        title=guide_data.GAME_NAME,
        subtitle=guide_data.GAME_SUBTITLE,
        status=f"{done}/{len(trophies)} troféus",
        accent=guide_data.ACCENT,
    )
    try:
        from streamer_sidekick.core.modules import ModuleInfo as SidekickModuleInfo

        return SidekickModuleInfo(**data)
    except Exception:
        return ModuleInfo(**data)


def help_text() -> str:
    return (
        "Guia de platina de Wo Long: Fallen Dynasty (jogo base) em PT-BR.\n\n"
        "Em Wo Long tudo acontece dentro de uma batalha, então o guia é uma lista de "
        "batalhas: abra a que você vai jogar e o card mostra os troféus que saem ali, "
        "a caixa das bandeiras e cada coletável daquela missão com foto e descrição "
        "de onde está.\n\n"
        "A rotina de toda batalha:\n"
        "chame um reforço → erga TODAS as bandeiras → pegue os coletáveis do card → "
        "só então vá ao chefe.\n"
        "Bandeira de Marcação sobe a Fortitude, que é o piso do seu Rank de Moral "
        "naquela batalha. Quem ergue tudo entra na próxima mais forte; quem ignora "
        "apanha no meio do jogo e ainda termina com 145 bandeiras para refazer.\n\n"
        "Dois ajustes antes da primeira missão:\n"
        "• Desative a invasão por jogadores — o Eye for an Eye só conta invasores NPC.\n"
        "• Jogue Fall of the Corrupted Eunuch sozinho: o juramento com Cao Cao tem "
        "relatos de bug em co-op.\n\n"
        "E uma armadilha: a batalha secundária Wizardry Spell Mastery (Parte 3) é o "
        "que libera os feitiços de tier alto. Sem ela, o Wizardry Master é impossível.\n\n"
        "O progresso é salvo em %APPDATA%/StreamerSidekick/platinas/wolong/ e "
        "sobrevive a atualizações."
    )


def build_page(config=None):
    from .page import GuidePage

    return GuidePage()
