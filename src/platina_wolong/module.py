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
        "Guia de platina de Wo Long: Fallen Dynasty (jogo base) em PT-BR, em 9 abas.\n\n"
        "A regra que decide a run:\n"
        "Em cada uma das 46 batalhas, chame um reforço, erga TODAS as bandeiras e "
        "recolha os itens daquela missão ANTES de ir ao chefe. Bandeira de Marcação "
        "sobe a Fortitude, que é o piso do seu Rank de Moral — quem coleta fica mais "
        "forte a cada missão, e quem ignora apanha no meio do jogo e ainda tem 145 "
        "bandeiras para refazer no fim.\n\n"
        "Dois ajustes antes de começar:\n"
        "• Desative a invasão por jogadores — o troféu Eye for an Eye só conta "
        "invasores NPC.\n"
        "• Faça a missão Fall of the Corrupted Eunuch sozinho: o juramento com Cao Cao "
        "tem relatos de bug em co-op.\n\n"
        "E uma armadilha: a batalha secundária Wizardry Spell Mastery (Parte 3) é o que "
        "libera os feitiços de tier alto. Sem ela, o Wizardry Master é impossível.\n\n"
        "Como usar:\n"
        "• “Passo a passo” traz as 46 batalhas na ordem, já com o que recolher em cada.\n"
        "• “Coletáveis” tem os 75 itens com missão e local — filtre pela batalha que "
        "você vai jogar.\n"
        "• “145 Bandeiras” marca as batalhas já 100% de bandeira.\n"
        "• A busca do topo procura em passos, troféus, coletáveis e batalhas.\n\n"
        "O progresso é salvo em %APPDATA%/StreamerSidekick/platinas/wolong/ e "
        "sobrevive a atualizações."
    )


def build_page(config=None):
    from .page import GuidePage

    return GuidePage()
