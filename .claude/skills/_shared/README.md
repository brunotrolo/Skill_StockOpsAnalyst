# _shared — Infraestrutura das Skills B3

Este diretório **não é uma skill invocável por palavra-chave**. É um módulo
de infraestrutura compartilhada, lido por outras skills (Auditoria, Manejo,
Screener, etc.) que ainda serão criadas.

## Arquivos

- **`portfolio_params.yaml`** — fonte única de verdade para todos os
  parâmetros numéricos fixos (capital, metas, faixas de delta, limiares de
  colchão/concentração/eficiência, whitelist de ativos).
- **`golden_rules.md`** — regras invioláveis em prosa (nunca inventar dados,
  delta como lei suprema, nunca PUT nua fora de spread, etc.).
- **`risk_checks.py`** — funções Python puras e testáveis (`check_colchao`,
  `check_concentracao`, `classify_delta`, `check_eficiencia`), sem chamada
  de API.

## Regra de uso

Skills futuras devem **ler/importar** estes arquivos, nunca copiar os
números ou reescrever as regras em prosa dentro do próprio `SKILL.md`. Se um
parâmetro precisar mudar, a mudança acontece em UM lugar: aqui.

- Skills em execução no Claude Code (com acesso ao filesystem do repo) podem
  ler `.claude/skills/_shared/portfolio_params.yaml` e
  `.claude/skills/_shared/golden_rules.md` diretamente, e importar
  `risk_checks.py`.
- Skills empacotadas para claude.ai (fora do Claude Code) **não enxergam**
  `_shared/` — cada skill é enviada como um zip autocontido. Para essas,
  use `build_skill_bundle.sh` (ver abaixo) para gerar uma cópia sincronizada
  destes arquivos dentro da pasta de cada skill antes de zipar.

## Portabilidade para claude.ai

`build_skill_bundle.sh`, na raiz de `.claude/skills/`, percorre cada
skill em `.claude/skills/<nome>/` (exceto `_shared/`), copia
`portfolio_params.yaml` e `golden_rules.md` para dentro da pasta da skill e
gera um `.zip` pronto para upload em claude.ai. A fonte de edição continua
sendo os arquivos aqui em `_shared/` — as cópias dentro de cada skill são
geradas, não editadas manualmente.
