# Regras de Ouro — Invioláveis

Estas regras valem para toda skill do sistema de análise de opções B3. Nenhuma
skill pode contradizê-las, reescrevê-las ou "flexibilizar" seu conteúdo. Os
números citados aqui vêm de `portfolio_params.yaml` — se um número mudar,
muda lá, não aqui.

1. **Nunca inventar dados.** Se um dado (cotação, grega, prêmio, IV) não foi
   obtido de uma fonte real (API, planilha, cockpit), a análise para e reporta
   a ausência. Não estimar, não "chutar", não usar valores de exemplos
   anteriores como se fossem atuais.

2. **Delta é a lei suprema.** Delta da opção vendida governa a decisão de
   entrada, alerta e saída — não a distância nominal do strike em relação ao
   preço do ativo, não a percepção visual de "quão longe" o strike está.
   Sempre classificar pela faixa de delta definida em `portfolio_params.yaml`.

3. **Nunca PUT nua fora de spread.** Toda venda de PUT deve estar protegida
   por uma perna comprada formando um spread (Bull Put Spread) ou equivalente
   com risco definido. Venda de PUT nua (sem trava) é proibida.

4. **Nunca entrar ATM ou ITM.** A entrada em uma estrutura de venda de
   volatilidade só é válida com a opção vendida OTM (fora do dinheiro) no
   momento da entrada. ATM ou ITM na entrada é proibido, independente de
   quão atrativo o prêmio pareça.

5. **Stop em 2x o prêmio recebido.** Se o custo de recompra/encerramento da
   posição atingir 2 vezes o prêmio líquido recebido na entrada, a posição é
   encerrada. Sem exceção discricionária.

6. **Nunca aumentar posição para recuperar perda.** É proibido dobrar,
   piramidar ou abrir nova estrutura no mesmo ativo com o objetivo de
   compensar uma perda em aberto. Recuperação de perda não é justificativa
   para aumento de exposição.

7. **Bid/ask só valem como referência de liquidez durante o pregão.** Para
   qualquer cálculo de P&L, eficiência, delta ou decisão de manejo, usar
   sempre o preço de **fechamento (CLOSE)**. Bid/ask intradiário serve apenas
   para avaliar se há liquidez suficiente para executar a ordem, nunca como
   base de cálculo.
