"""Funções puras de checagem de risco para o sistema de skills B3.

Sem chamadas de API, sem I/O — apenas lógica determinística sobre os
parâmetros definidos em portfolio_params.yaml. Toda skill que precise
validar colchão, concentração, delta ou eficiência de uma estrutura deve
importar (ou reimplementar de forma idêntica) estas funções, nunca
reescrever os limiares em prosa.
"""

from __future__ import annotations

# Limiares — espelham portfolio_params.yaml. Se os valores mudarem lá,
# mudam aqui também (fonte única de verdade continua sendo o YAML).
COLCHAO_MINIMO_PCT = 15
CONCENTRACAO_MAXIMA_PCT = 20
DELTA_ENTRADA_MIN = -0.15
DELTA_ENTRADA_MAX = -0.30
DELTA_ALERTA_PROTOCOLO3 = -0.50
DELTA_EXIT_SEM_DISCUSSAO = -0.70
EFICIENCIA_MINIMA_PCT = 25


def check_colchao(patrimonio_total: float, margem_utilizada: float) -> tuple[float, str]:
    """Calcula o colchão de segurança da carteira e classifica seu status.

    Colchão = (patrimônio_total - margem_utilizada) / patrimônio_total, em %.

    Args:
        patrimonio_total: patrimônio total da carteira, em R$.
        margem_utilizada: margem/risco total já comprometido, em R$.

    Returns:
        Tupla (colchao_pct, status), onde status é "ok" se o colchão está
        acima do mínimo (COLCHAO_MINIMO_PCT) ou "critico" caso contrário.
    """
    colchao_pct = (patrimonio_total - margem_utilizada) / patrimonio_total * 100
    status = "ok" if colchao_pct >= COLCHAO_MINIMO_PCT else "critico"
    return colchao_pct, status


def check_concentracao(exposicao_por_ativo: dict[str, float], patrimonio_total: float) -> dict:
    """Calcula a concentração de risco por ativo e sinaliza excessos.

    Args:
        exposicao_por_ativo: mapa {ticker: exposição/risco em R$}.
        patrimonio_total: patrimônio total da carteira, em R$.

    Returns:
        Dict {ticker: {"pct": float, "acima_limite": bool}} usando
        CONCENTRACAO_MAXIMA_PCT como limiar.
    """
    resultado = {}
    for ticker, exposicao in exposicao_por_ativo.items():
        pct = exposicao / patrimonio_total * 100
        resultado[ticker] = {
            "pct": pct,
            "acima_limite": pct > CONCENTRACAO_MAXIMA_PCT,
        }
    return resultado


def classify_delta(delta: float) -> str:
    """Classifica o delta (absoluto) de uma opção vendida conforme o protocolo.

    Faixas (delta em módulo, |delta|):
        < 0.15                      -> "entrada_ok" (delta muito baixo, mas dentro do aceitável)
        0.15 a 0.30                 -> "entrada_ok" (faixa ideal de entrada)
        0.30 a 0.50 (exclusive)     -> "atencao"
        0.50 a 0.70 (exclusive)     -> "protocolo3"
        >= 0.70                     -> "exit_imediato"

    Args:
        delta: delta da opção vendida (tipicamente negativo para PUT).

    Returns:
        Uma das strings: "entrada_ok", "atencao", "protocolo3", "exit_imediato".
    """
    abs_delta = abs(delta)
    if abs_delta >= abs(DELTA_EXIT_SEM_DISCUSSAO):
        return "exit_imediato"
    if abs_delta >= abs(DELTA_ALERTA_PROTOCOLO3):
        return "protocolo3"
    if abs_delta > abs(DELTA_ENTRADA_MAX):
        return "atencao"
    return "entrada_ok"


def check_eficiencia(credito_liquido: float, largura: float) -> tuple[float, bool]:
    """Calcula a eficiência de uma estrutura de spread e se ela é aprovada.

    Eficiência = crédito líquido ÷ largura do spread, em %.

    Args:
        credito_liquido: crédito líquido recebido na estrutura, em R$.
        largura: largura do spread (diferença entre strikes), em R$.

    Returns:
        Tupla (eficiencia_pct, aprovado), onde aprovado é True se a
        eficiência atinge EFICIENCIA_MINIMA_PCT.
    """
    eficiencia_pct = credito_liquido / largura * 100
    aprovado = eficiencia_pct >= EFICIENCIA_MINIMA_PCT
    return eficiencia_pct, aprovado


if __name__ == "__main__":
    # Testes rápidos com números reais do cockpit (validados contra o que já
    # foi calculado manualmente antes de existir esta infraestrutura).

    # --- check_eficiencia: Bull Put Spread ativo em BRAV3 (STR_BRAV3_AUG_21_2026,
    #     vencimento 21/08/2026) — venda BRAVT180 (strike 17.88, entrada R$ 1.13)
    #     x compra BRAVT160 (strike 15.88, entrada R$ 0.50), qty 3200. ---
    largura_brav3 = 17.88 - 15.88  # R$ 2.00
    credito_liquido_brav3 = 1.13 - 0.50  # R$ 0.63 por ação
    eficiencia_pct, aprovado = check_eficiencia(credito_liquido_brav3, largura_brav3)
    print(f"[check_eficiencia] BRAV3 (17.88/15.88): {eficiencia_pct:.2f}% aprovado={aprovado}")
    assert round(eficiencia_pct, 2) == 31.50
    assert aprovado is True

    # --- check_colchao: carteira real via cockpit (patrimonio=120000,
    #     risco_travado_carteira=29389.75, risco_descoberto_carteira=89331) ---
    patrimonio_total = 120_000
    margem_utilizada = 29_389.75 + 89_331  # 118,720.75
    colchao_pct, status = check_colchao(patrimonio_total, margem_utilizada)
    print(f"[check_colchao] patrimonio=120000 margem={margem_utilizada}: "
          f"{colchao_pct:.2f}% status={status}")
    assert round(colchao_pct, 2) == 1.07
    assert status == "critico"

    # --- check_concentracao: exposição real por ativo (risco travado +
    #     descoberto por ticker, cockpit em 27/07/2026) ---
    exposicao_por_ativo = {
        "EGIE3": 41_425.00,
        "VALE3": 25_740.00,
        "SANB11": 15_515.00,
        "BBDC4": 14_472.00,
        "ITUB4": 9_900.75,
        "BRAV3": 4_384.00,
        "EQTL3": 4_244.00,
        "BBAS3": 3_040.00,
    }
    concentracao = check_concentracao(exposicao_por_ativo, patrimonio_total)
    for ticker, dados in concentracao.items():
        print(f"[check_concentracao] {ticker}: {dados['pct']:.2f}% "
              f"acima_limite={dados['acima_limite']}")
    assert concentracao["EGIE3"]["acima_limite"] is True
    assert concentracao["VALE3"]["acima_limite"] is True
    assert concentracao["BRAV3"]["acima_limite"] is False

    # --- classify_delta: faixas de referência do protocolo ---
    casos_delta = [-0.10, -0.20, -0.45, -0.60, -0.80]
    esperado_delta = ["entrada_ok", "entrada_ok", "atencao", "protocolo3", "exit_imediato"]
    for delta, esperado in zip(casos_delta, esperado_delta):
        classe = classify_delta(delta)
        print(f"[classify_delta] delta={delta:+.2f} -> {classe}")
        assert classe == esperado, f"delta={delta} esperado={esperado} obtido={classe}"

    print("\nTodos os testes passaram.")
