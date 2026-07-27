# Roadmap — Skills e Agentes de Análise de Opções B3

> Documento de planejamento colado por Bruno no chat em 27/07/2026, preservado
> aqui na íntegra (verbatim) para servir de referência única do roadmap
> completo. Este arquivo só recebe acréscimos — nenhuma informação enviada
> por Bruno deve ser removida dele.

Bruno, essa lista eu montei no turno anterior como o arquivo **ROADMAP_SKILLS_AGENTES_B3.md** — ele continua disponível. Mas como você pediu de novo, é bem possível que o arquivo não tenha aberto aí (costuma acontecer no mobile), então vou colar **tudo direto aqui no chat** pra garantir. Cada bloco de código é pra colar direto no Claude Code, na ordem.

## Ordem de construção

| # | Peça | Tipo | Por quê nessa posição |
|---|---|---|---|
| 0 | `_shared/` | Infraestrutura | Fonte única de verdade — tudo depende dela |
| 1 | `auditoria-diaria` | Skill | Porta de entrada diária, gera os alertas |
| 2 | `protocolo3-manejo` | Skill | Você tem VALE3/EGIE3 ITM agora — maior risco de capital |
| 3 | `protocolo2-oportunidades` | Skill | Só depois de auditoria + manejo sólidos |
| 4 | `performance-mensal` | Skill | Avaliação de resultado, não bloqueia o dia |
| 5 | `analise-cenarios` | Skill | Stress test, usa dados já validados |
| 6+ | Subagentes | Claude Code only | Fase 2, só depois das 5 estáveis |

---

### 0 — `_shared/` (núcleo — construa primeiro)

```
Crie a infraestrutura compartilhada em .claude/skills/_shared/ para um
sistema de Skills de opções B3 (venda de volatilidade, Bull Put / Bear
Call Spread). É o PRIMEIRO módulo — as outras skills dependem dele.
OBJETIVO: eliminar duplicação de parâmetros entre skills.

1. portfolio_params.yaml — fonte única de verdade dos números fixos:
   capital_base_brl: 120000
   meta_mensal_min_brl: 5000
   colchao_minimo_pct: 15
   concentracao_maxima_pct: 20
   delta_entrada_min: -0.15
   delta_entrada_max: -0.30
   delta_alerta_protocolo3: -0.50
   delta_exit_sem_discussao: -0.70
   dte_critico_dias: 10
   eficiencia_minima_pct: 25   # crédito líquido ÷ largura
   iv_rank_minimo_pct: 50
   whitelist_best: [B3SA3, BBAS3, BBDC4, BRAV3, BRKM5, CMIG4, CMIN3,
     COGN3, CSAN3, CSNA3, DIRR3, EMBJ3, FLRY3, GGBR4, ITSA4, ITUB4,
     NATU3, PETR4, PRIO3, PSSA3, SANB11, SUZB3, USIM5, VALE3]
   Comentário no topo: "ÚNICA fonte de verdade — nunca duplicar estes
   números em prosa dentro de um SKILL.md individual."

2. golden_rules.md — regras invioláveis em prosa curta: nunca inventar
   dados; Delta é a lei suprema (nunca usar distância de strike como
   risco); nunca naked PUT fora de spread; nunca entrar ATM/ITM; stop
   em 2x o prêmio recebido; nunca aumentar posição para recuperar perda;
   bid/ask só valem como liquidez durante pregão — cálculo sempre por
   CLOSE.

3. risk_checks.py — funções puras e testáveis, SEM chamada de API:
   - check_colchao(patrimonio_total, margem_utilizada) -> (pct, status)
   - check_concentracao(exposicao_por_ativo: dict, patrimonio_total) -> dict
   - classify_delta(delta) -> "entrada_ok"|"atencao"|"protocolo3"|"exit_imediato"
   - check_eficiencia(credito_liquido, largura) -> (pct, aprovado: bool)
   Cada função com docstring, type hints e teste em
   if __name__ == "__main__": usando números reais do meu histórico
   (ex.: BRAV3 com crédito e largura reais) para validar contra o
   cálculo manual.

4. README.md — deixar claro que é módulo de INFRAESTRUTURA, não uma
   skill invocável; outras skills leem estes arquivos, nunca reescrevem.

5. build_skill_bundle.sh — para cada skill em .claude/skills/<nome>/,
   copiar uma cópia sincronizada de portfolio_params.yaml e
   golden_rules.md para dentro da pasta da skill antes de zipar, porque
   Skills no claude.ai são enviadas como zip autocontido e não enxergam
   _shared/ fora da própria pasta.

Não crie ainda as skills de protocolo. Ao terminar, rode risk_checks.py
e me mostre a saída dos testes.
```

---

### 1 — `auditoria-diaria` · gatilho: "AUDITORIA"

```
Crie a skill .claude/skills/auditoria-diaria/ — checagem diária de
carteira de opções B3. DEPENDÊNCIAS: leia _shared/portfolio_params.yaml,
golden_rules.md, risk_checks.py; não redeclare números.
Frontmatter com description que ative por semântica ("revisar carteira",
"P&L de hoje") e pela palavra "AUDITORIA".

PROCEDIMENTO (silencioso, entrega só o relatório final):
1. get_cockpit_ativas (Sheets) — posições, strikes, qtd, prêmios,
   moneyness.
2. Saldo/patrimônio real via Banco AI MCP (openfinance_get_account_
   balance ou equiv.) + ativos em garantia.
3. get_quote (OpLab) para o spot de cada ticker.
4. Para posições ITM/próximas do dinheiro: get_instrument_options ou
   get_options_bs para Delta REAL. Nunca usar distância de strike. Se
   não obtiver Delta, marcar "DELTA PENDENTE — verificar no book" e
   seguir; não inventar.
5. risk_checks.check_colchao() e check_concentracao() sobre o patrimônio
   real do passo 2.
6. classify_delta() em cada posição; isolar "protocolo3" e "exit_imediato".
7. Isolar também DTE < dte_critico_dias, independente do delta.
8. P&L MtM: prêmio recebido menos recompra ao CLOSE; nunca BID/ASK fora
   do pregão.
9. OBRIGATÓRIO — teste "posição mascarando outras": se uma única posição
   responde por >50% do P&L positivo agregado, mostrar o líquido SEM ela
   ao lado do líquido com ela. Padrão que já se repetiu nesta carteira.

SAÍDA (Markdown): cabeçalho (hora, mercado aberto/fechado, dado de
pregão ou fechamento) | tabela posições (ticker|estrutura|strikes|delta
ou PENDENTE|DTE|MtM) | bloco compliance (colchão%, concentração,
✅/⚠️/🔴) | bloco "sem a âncora" | alertas críticos com recomendação
(assumir/rolar/encerrar) | se algum MCP falhar, declarar o dado faltante,
nunca estimar.

TESTES: valide o P&L à mão em pelo menos 2 posições de um snapshot real
do cockpit antes de dar como pronta.
```

---

### 2 — `protocolo3-manejo` · gatilho: "MANEJO [TICKER]"

```
Crie a skill .claude/skills/protocolo3-manejo/ — decisão de manejo de
posição em risco. DEPENDÊNCIAS: _shared/. Normalmente chamada depois da
auditoria isolar a posição crítica; recebe as pernas por contexto ou
pergunta.

PROCEDIMENTO:
1. Receber pernas exatas (ticker, lado, strike, qtd, preço entrada); se
   faltar, extrair de get_cockpit_ativas.
2. get_analise_manejo (OpLab) com as pernas — retorna custo de
   desmontagem, candidatos de rolagem já como travas completas, Monte
   Carlo e decisão sugerida.
3. classify_delta() na perna vendida: acima de -0.50 (protocolo3) →
   manejo obrigatório hoje; acima de -0.70 → encerrar sem discussão, não
   considerar rolagem.
4. Comparar candidatos de rolagem por DELTA primeiro (menor = mais
   seguro), nunca por prêmio bruto; rejeitar delta pior que o atual
   mesmo com crédito maior.
5. check_eficiencia() em qualquer trava nova candidata; abaixo do mínimo,
   descartar.
6. Resultado líquido de cada via: assumir / rolar (crédito ou débito) /
   encerrar (custo de desmontagem real + buffer 5-15% sobre CLOSE p/
   spread de execução).
7. Se a posição for desvio de playbook (fora da whitelist BEST, ou naked
   sem proteção), sinalizar como agravante, não só o delta.

SAÍDA: situação atual (delta, DTE, moneyness, prêmio original) | tabela
comparativa (Assumir/Rolar/Encerrar com delta resultante, líquido, risco)
| decisão em uma frase ancorada em delta | se delta indisponível:
"DADOS INCOMPLETOS — Impossível recomendar manejo sem Delta real".

TESTES: rode contra uma posição real ITM atual e confira o custo de
desmontagem à mão.
```

---

### 3 — `protocolo2-oportunidades` · gatilho: "PROTOCOLO 2"

```
Crie a skill .claude/skills/protocolo2-oportunidades/ — descoberta de
novas entradas (Bull Put prioritário; Bear Call para tendência de baixa).
DEPENDÊNCIAS: _shared/ (whitelist_best, deltas, iv_rank_minimo_pct,
eficiencia_minima_pct vêm de lá; não redeclarar).

PROCEDIMENTO:
1. get_iv_rank_bulk na whitelist inteira; filtrar IV Rank >
   iv_rank_minimo_pct. Se nenhum passar, parar e reportar; não forçar.
2. Cruzar tendência via get_m9m21_ranking: descartar M9/M21 < 1.0 para
   PUT; para Bear Call, exigir M9/M21 < 1.0.
3. Variação intradiária: se caiu < -2% no dia, marcar "entrada
   pressionada" mesmo com tendência semanal ok (não descarta, sinaliza).
4. get_instrument_options: strike com Delta entre delta_entrada_min/max,
   DTE 15-30, Volume >= 1000, book líquido.
5. check_eficiencia() em cada estrutura; descartar abaixo do mínimo mesmo
   com prêmio atrativo.
6. get_backtest_protocolo2 (use_spread=true) nos finalistas — extrair
   win_rate_pct e retorno médio.
7. Limite de concentração: nenhuma entrada pode levar exposição por ativo
   acima de concentracao_maxima_pct (checar exposição atual via
   get_cockpit_ativas antes).

SAÍDA: Tese do dia (2-3 frases) | Top 3 (Ticker|Estrutura|Strikes|Delta|
IV Rank|Prêmio Líquido|Eficiência|Volume) | Prova (win_rate_pct + retorno)
| Checklist pré-execução confirmando Delta, Volume, Spread e Concentração
com dados reais; se algum faltar, "DADOS INCOMPLETOS" naquele item.

TESTES: rode em 3 ativos e confira que o filtro de IV Rank e M9/M21
excluiu corretamente os que deviam sair.
```

---

### 4 — `performance-mensal` · gatilho: "PERFORMANCE"

```
Crie a skill .claude/skills/performance-mensal/ — revisão de resultado
mensal e histórico. DEPENDÊNCIAS: _shared/.

PROCEDIMENTO:
1. get_resumo_mensal (Sheets) — usar campo premio_liquido como verdade.
   Nunca somar só vendas brutas; líquido = vendas menos todos os débitos
   (compras, hedges, rolagens).
2. get_dashboard_mensal do mês corrente.
3. get_resumo_por_ativo — identificar piores/melhores ativos históricos;
   marcar ativo com taxa de exercício alta + P&L realizado negativo como
   "só operar em trava, nunca a seco" ou candidato a sair da whitelist.
4. Eficiência do mês: premio_liquido ÷ premio_bruto; comparar com
   eficiencia_minima_pct e com a média histórica.
5. OBRIGATÓRIO: comparar prêmio líquido do mês x P&L REALIZADO (não só
   MtM). Líquido positivo com realizado negativo = alerta de saúde
   crítico, com destaque. É o principal indicador de saúde do sistema.
6. Teste "posição mascarando outras" sobre o mês inteiro.
7. Trajetória: ritmo atual x meta_mensal_min_brl; quantos meses bateram
   a meta.

SAÍDA: dashboard do mês (bruto, líquido, eficiência, realizado) |
histórico mês a mês | Top 3 / Bottom 3 ativos | alerta líquido+ x
realizado- se aplicável | recomendação de ajuste de whitelist.

TESTES: valide contra 2 meses do histórico real e confirme que bate com
o cálculo manual.
```

---

### 5 — `analise-cenarios` · gatilho: "CENÁRIOS"

```
Crie a skill .claude/skills/analise-cenarios/ — stress test da carteira
por preço do subjacente. DEPENDÊNCIAS: _shared/.

PROCEDIMENTO:
1. get_cockpit_ativas + get_quote para spots de todos os ativos abertos.
2. Para 3 cenários por ativo — Adverso (-5% a -7%, usar o pior como
   padrão), Base (+1%), Otimista (+3% a +4%) — recalcular:
   a. Novo preço do subjacente
   b. P&L de cada posição via payoff da estrutura (cálculo determinístico,
      não reestimar delta)
   c. Quais travas ficariam ITM ou seriam exercidas
3. check_colchao() e check_concentracao() em cada cenário, com
   patrimônio recalculado (atual + P&L do cenário).
4. Identificar posições que "desarmariam" no Adverso (sem proteção ou
   estourando risco máximo).
5. Correlação: se várias posições no mesmo setor / correlacionadas com
   IBOV (get_correl_ibov se disponível), marcar risco de fator.

SAÍDA: tabela (Cenário|P&L agregado|Colchão|Concentração máx|Compliance)
| lista de travas que desarmariam no Adverso com ação preventiva | nota
de correlação.

TESTES: rode com a carteira atual e confira o payoff de pelo menos uma
Bull Put Spread nos 3 cenários à mão.
```

---

### Fase 2 — Subagentes (Claude Code apenas)

Subagentes (`.claude/agents/*.md`, contexto isolado) **não existem** em claude.ai web/mobile — são exclusivos do Claude Code. Só construa depois das 5 skills rodando estáveis por 1-2 semanas. Saída deve gravar de volta no Sheets pra eu consultar daqui.

```
reconciliador-dados.md — roda em paralelo comparando get_cockpit_ativas
(Sheets) contra o Banco AI MCP no mesmo período; detecta divergências
(posições não mapeadas, strikes divergentes, patrimônio inconsistente).
Saída só com divergências (silêncio se não houver). 1x/dia fora do pregão.
```
```
backtest-profundo.md — varredura histórica ampla (além do Protocolo 2):
testa venda de PUT OTM (delta -0.15 a -0.30) em TODA a B3 com opções
líquidas, janela 12-24 meses, para achar candidatos a inclusão na
whitelist por win_rate_pct e eficiência consistente. Sob demanda. Saída:
lista de candidatos para revisão manual antes de qualquer adição.
```
```
montecarlo-manejo.md — aprofunda protocolo3-manejo quando há múltiplos
caminhos de rolagem plausíveis: Monte Carlo sobre trajetórias de preço
até o vencimento por alternativa (assumir/rolar/encerrar), estimando
distribuição de resultado. Invocar só quando o manejo sinalizar
ambiguidade entre duas vias próximas.
```

---

### Empacotamento web + mobile

Skills **não sincronizam** entre Claude Code e claude.ai. Depois de testar cada uma no Code: rode `build_skill_bundle.sh <nome>` → zip autocontido → claude.ai: Settings → Features → Custom Skills → upload (precisa Pro/Max/Team/Enterprise com code execution). Teste no web e no mobile antes de dar como publicada.

**Handoff pra mim:** a cada peça pronta, me traga o `SKILL.md`, a saída de 1 execução real (não simulada) e qualquer divergência entre o cálculo da skill e o seu manual. Eu confiro contra o histórico antes de você seguir.

---

Se preferir, em vez de tudo de uma vez, eu te passo **uma peça por vez** conforme você constrói e testa — você me diz "próxima" e eu solto a seguinte já com os ajustes do que aprendemos na anterior. E enquanto isso o mercado segue comigo aqui normal: "AUDITORIA", "MANEJO", o que precisar.

---

## Status de execução (acréscimo — não faz parte do texto original de Bruno)

Registro de progresso, atualizado conforme cada peça é construída e validada. Esta seção é adicionada por baixo do conteúdo original e nunca substitui nada do que está acima.

- [x] **Bloco 0 — `_shared/`**: construído em `.claude/skills/_shared/` (branch
  `claude/shared-skills-b3-infrastructure-yqim6f`, PR #1). Contém
  `portfolio_params.yaml`, `golden_rules.md`, `risk_checks.py` (testado com
  dados reais do cockpit — BRAV3, concentração por ativo, colchão da
  carteira) e `README.md`. `build_skill_bundle.sh` criado em
  `.claude/skills/` e validado contra uma skill de teste.
- [ ] **Bloco 1 — `auditoria-diaria`**: não iniciado.
- [ ] **Bloco 2 — `protocolo3-manejo`**: não iniciado.
- [ ] **Bloco 3 — `protocolo2-oportunidades`**: não iniciado.
- [ ] **Bloco 4 — `performance-mensal`**: não iniciado.
- [ ] **Bloco 5 — `analise-cenarios`**: não iniciado.
- [ ] **Fase 2 — Subagentes**: aguardando as 5 skills estáveis por 1-2 semanas
  em uso real, conforme o próprio roadmap determina.
