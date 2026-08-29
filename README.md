# Wo Long: Fallen Dynasty — Platina (PT-BR)

Guia de platina do **Wo Long: Fallen Dynasty** (jogo base) em português,
empacotado como plugin do [Streamer Sidekick](https://github.com/ricardothezouro-debug)
na categoria `platina` (aba **Platinas**).

São 51 troféus, nenhum perdível e **uma run só**. O guia é montado em volta da
única coisa que decide se a platina leva ~40 horas ou vira uma limpeza infernal:
o que você faz **dentro de cada batalha**, na primeira vez que a joga.

| Conteúdo | Qtd. |
|---|---:|
| Passos da rota (preparo + 46 batalhas + limpeza) | 57 |
| Batalhas (16 principais + 30 secundárias) | 46 |
| Coletáveis com missão e local | 75 |
| Troféus do jogo base | 51 |
| Companheiros recrutáveis | 17 |
| Fases de feitiço (14 feitiços cada) | 5 |
| Itens de preparo / equipamento | 10 |
| Imagens (ícones de troféu e capturas) | 58 |
| Fontes cruzadas | 6 |
| **Itens marcáveis no total** | **261** |

## A regra que o guia inteiro persegue

> Em **cada uma das 46 batalhas**: chame um reforço, erga **todas** as bandeiras
> (Batalha e Marcação), recolha os itens daquela missão — e só então vá ao chefe.

Bandeira de Marcação sobe a **Fortitude**, que é o **piso do seu Rank de Moral**
naquela batalha. Quem ergue tudo entra na missão seguinte mais forte; quem ignora
apanha no meio do jogo **e** ainda termina com 145 bandeiras para refazer.

Seguindo essa regra, saem de graça, junto com a história: *Fly It High*,
*Side by Side*, *Well-read*, *How Precious!*, *Ascension* e os 13 Juramentos.

## As 9 abas

| # | Aba | O que tem |
|---|-----|-----------|
| 01 | Passo a passo | As 46 batalhas na ordem, por Parte, cada uma já dizendo **o que recolher nela**. Mais 3 passos de preparo e 8 de limpeza final. |
| 02 | Coletáveis | As 31 tábuas, 23 Shitieshou e 21 Cascas de Cigarra com missão e local. **Filtre pela batalha que vai jogar** e leve a lista do lado. |
| 03 | 51 Troféus | Nome, tier, requisito e o caminho mais curto, com o ícone de cada um. Filtro por texto, tier e "só pendentes". |
| 04 | 145 Bandeiras | Uma linha por batalha: marque quando ela estiver 100% de bandeira. |
| 05 | Companheiros | Os 17 guerreiros, quando cada um libera, e o método rápido do *Great Gatherings*. |
| 06 | Feitiços | As 5 fases (14 feitiços cada) e o pré-requisito que trava o *Wizardry Master*. |
| 07 | Preparo | Ajustes de opção, hábitos por missão e os itens de equipamento que viram troféu. |
| 08 | Imagens | As mecânicas que o guia cita, em imagem. |
| 09 | Fontes | Os 6 guias cruzados na elaboração da rota. |

## Três armadilhas que este guia resolve antes de acontecerem

**A missão que trava o *Wizardry Master*.** Os feitiços de tier alto só aparecem
depois da batalha secundária **Wizardry Spell Mastery** (Parte 3, nível 32). Quem
pula descobre no fim da run, com os 70 feitiços impossíveis de completar.

**O *Eye for an Eye* que não conta.** O troféu só conta invasores **NPC**. Com a
invasão por jogadores ligada, um jogador real entra no lugar do NPC e a contagem
não anda — por isso o passo 0.1 é desativar isso nas opções.

**O juramento do Cao Cao em co-op.** *Awakening of the Unscrupulous Hero* tem
relatos de não estourar quando **Fall of the Corrupted Eunuch** é feita em co-op.
O guia manda fazer essa missão sozinho.

## Recursos

- **Busca global**: procura ao mesmo tempo em passos, troféus, coletáveis e
  batalhas, ignorando acentuação. Digite `Lu Bu`, `tábua`, `Guandu` ou `feitiço`.
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
  "description": "Guia PT-BR do jogo base: as 46 batalhas na ordem, 75 coletáveis com local, as 145 bandeiras e os 51 troféus.",
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
  page.py            a página: as 9 abas, busca global, filtros e progresso
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
o que descartaria 8 das 9 abas — e a aba de coletáveis filtrável por batalha é o
que faz o guia ser usável **enquanto** você joga. O contrato do
`PLUGIN_STANDARD.md` (`module_info()` / `build_page()`) e os `objectName`s do
design system são respeitados; as dependências são só PySide6 + stdlib.

## Escopo

Cobre o **jogo base**. As DLCs (*Battle of Zhongyuan*, *Conqueror of Jiangdong*
e *Upheaval in Jingxiang*) têm listas de troféus separadas e não contam para
esta platina.

## Créditos

Guia não oficial, sem vínculo com a KOEI TECMO / Team NINJA. As imagens são de
terceiros e estão creditadas nas legendas; as fontes da rota estão na aba
**Fontes**.
