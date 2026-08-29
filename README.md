# Wo Long: Fallen Dynasty — Platina (PT-BR)

Guia de platina do **Wo Long: Fallen Dynasty** (jogo base) em português,
empacotado como plugin do [Streamer Sidekick](https://github.com/ricardothezouro-debug)
na categoria `platina` (aba **Platinas**).

São 51 troféus, nenhum perdível e **uma run só**. O guia é montado em volta da
única coisa que decide se a platina leva ~40 horas ou vira uma limpeza infernal:
o que você faz **dentro de cada batalha**, na primeira vez que a joga.

| Conteúdo | Qtd. |
|---|---:|
| Batalhas (16 principais + 30 secundárias) | 46 |
| **Bandeiras com foto** (Batalha + Marcação), em 29 batalhas | 265 |
| Coletáveis **com foto** e descrição de onde estão | 75 |
| Troféus do jogo base | 51 |
| Passos de fecho (depois da história) | 8 |
| Companheiros recrutáveis | 17 |
| Fases de feitiço (14 feitiços cada) | 5 |
| Hábitos de preparo | 5 |
| Imagens no total (bandeiras, coletáveis e ícones) | 389 |
| **Itens marcáveis no total** | **490** |

## A regra que o guia inteiro persegue

> Em **cada uma das 46 batalhas**: chame um reforço, erga **todas** as bandeiras
> (Batalha e Marcação), recolha os itens daquela missão — e só então vá ao chefe.

Bandeira de Marcação sobe a **Fortitude**, que é o **piso do seu Rank de Moral**
naquela batalha. Quem ergue tudo entra na missão seguinte mais forte; quem ignora
apanha no meio do jogo **e** ainda termina com centenas de bandeiras para refazer.

Seguindo essa regra, saem de graça, junto com a história: *Fly It High*,
*Side by Side*, *Well-read*, *How Precious!*, *Ascension* e os 13 Juramentos.

## Como o guia é organizado

Em Wo Long **tudo acontece dentro de uma batalha** — então o guia não separa rota,
coletáveis e bandeiras em abas diferentes. A batalha é a unidade: você abre a que
vai jogar e o card dela traz tudo.

Cada card de batalha tem:

- a caixa de **batalha concluída** e o nível recomendado;
- os **troféus que saem ali** (juramentos, easter eggs, o que for);
- **cada bandeira daquela batalha** — Batalha ou Marcação, numerada, com descrição
  e **foto**, e uma caixa por bandeira;
- **cada coletável daquela missão**, com tipo, descrição de onde está e **foto**.

As bandeiras vêm de guias publicados por missão, que cobrem **29 das 46 batalhas**.
Nas 17 restantes (quase todas secundárias curtas) o card mantém uma caixa única de
"todas as bandeiras erguidas" e avisa que ali não há guia publicado — o total por
batalha aparece na tela de seleção de missão do próprio jogo.

| # | Aba | O que tem |
|---|-----|-----------|
| 01 | Batalhas | As 46 batalhas agrupadas por Parte, mais a Base e o Fecho. É a única aba necessária com o jogo aberto. Filtro por texto, Parte e "só pendentes". |
| 02 | 51 Troféus | Nome, tier, requisito e caminho mais curto, com o ícone oficial de cada um. |
| 03 | Sistemas | O que não cabe dentro de uma batalha: os hábitos de preparo, as Cinco Fases e os 17 companheiros. |
| 04 | Fontes | Os 6 guias cruzados na elaboração da rota. |

## Três armadilhas que este guia resolve antes de acontecerem

**A missão que trava o *Wizardry Master*.** Os feitiços de tier alto só aparecem
depois da batalha secundária **Wizardry Spell Mastery** (Parte 3, nível 32). Quem
pula descobre no fim da run, com os 70 feitiços impossíveis de completar.

**O *Eye for an Eye* que não conta.** O troféu só conta invasores **NPC**. Com a
invasão por jogadores ligada, um jogador real entra no lugar do NPC e a contagem
não anda. O guia manda desativar isso antes da primeira missão.

**O juramento do Cao Cao em co-op.** *Awakening of the Unscrupulous Hero* tem
relatos de não estourar quando **Fall of the Corrupted Eunuch** é feita em co-op.
O guia manda fazer essa missão sozinho.

## Recursos

- **Busca global**: procura ao mesmo tempo em batalhas, troféus e coletáveis,
  ignorando acentuação. Digite `Lu Bu`, `tábua`, `Guandu` ou `balista`.
- **Progresso salvo automaticamente** em
  `%APPDATA%\StreamerSidekick\platinas\wolong\progress.json` — fora da pasta do
  plugin, então **sobrevive a atualizações**.
- **Exportar / Importar progresso** em JSON.
- **Imagens com cache em disco**: baixadas uma vez, funcionam offline depois.

## Instalação

Pelo Streamer Sidekick: aba **Platinas** → card **“+”** → **Wo Long — Platina**.

## Rodar standalone (sem o Sidekick)

```bash
pip install -r requirements.txt
set PYTHONPATH=src
python -m platina_wolong
```

## Entrada para o `platinas.json` do Sidekick

Também disponível no arquivo [`platinas-entry.json`](platinas-entry.json):

```json
{
  "id": "wolong",
  "name": "Wo Long — Platina",
  "description": "Guia PT-BR do jogo base: as 46 batalhas na ordem, cada uma com seus troféus e coletáveis com foto.",
  "repo": "ricardothezouro-debug/Guia-de-Platina-Wolong",
  "ref": "main",
  "version": "1.0.0",
  "src_subdir": "src",
  "module": "platina_wolong.module",
  "accent": "#C8102E",
  "icon": "src/platina_wolong/assets/brand/icon.png",
  "min_sidekick_version": "0.6.0",
  "changelog": "Primeira versão: as 46 batalhas na ordem com os coletáveis de cada uma, os 51 troféus e as armadilhas do Wizardry Master e do Eye for an Eye."
}
```

## Estrutura

```
src/platina_wolong/
  __init__.py
  module.py          contrato do plugin: module_info() / build_page() / help_text()
  page.py            a página: as 4 abas, busca global, filtros e progresso
  guide_data.py      TODO o conteúdo do guia (único arquivo específico do jogo)
  progress.py        formato das chaves de progresso
  storage.py         progresso em %APPDATA% (genérico do template)
  image_loader.py    download de imagens com cache em disco (genérico do template)
  __main__.py        execução standalone
  assets/brand/icon.png
```

### Diferenças em relação aos arquivos genéricos do template

Duas mudanças em `image_loader.py`, as mesmas dos guias de DREDGE e House Flipper:

1. **Cabeçalhos de navegador** nas requisições — vários hosts devolvem 403 para
   um `User-Agent` genérico sem `Referer`/`Sec-Fetch-*`.
2. **`ImageLoader.shutdown()`**, chamado no `aboutToQuit` e no `closeEvent` da
   página. Sem isso, fechar o app com um download em andamento destrói um
   `QThread` ainda rodando e o Qt aborta o processo.

`page.py` é próprio: o template genérico renderiza uma lista simples de troféus,
o que jogaria fora a estrutura que faz este guia funcionar — o card de batalha
com bandeiras, troféus e coletáveis com foto no mesmo lugar. O contrato do
`PLUGIN_STANDARD.md` (`module_info()` / `build_page()`) e os `objectName`s do
design system são respeitados; as dependências são só PySide6 + stdlib.

## Escopo

Cobre o **jogo base**. As DLCs (*Battle of Zhongyuan*, *Conqueror of Jiangdong*
e *Upheaval in Jingxiang*) têm listas de troféus separadas e não contam para
esta platina.

## Créditos

Guia não oficial, sem vínculo com a KOEI TECMO / Team NINJA.

As **fotos dos 75 coletáveis** são do [PowerPyx](https://www.powerpyx.com/wo-long-fallen-dynasty-all-collectible-locations/)
e as **fotos das 265 bandeiras** são do [100% Guides](https://www.100pguides.com/guides/wo-long-all-flag-locations),
ambos creditados na aba **Fontes**. Os ícones dos troféus vêm do CDN do Steam.

As imagens são baixadas sob demanda, no máximo 6 por vez, e ficam em cache local —
depois da primeira visita o guia funciona offline.
