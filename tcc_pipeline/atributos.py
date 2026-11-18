"""Atributos (features) para os modelos de detecção de anomalias.

Dois conjuntos:
  INDIVIDUAL    — só grandezas do próprio prédio + contexto temporal.
  MULTIVARIADO  — os mesmos + atributos que comparam o prédio com o campus
                  (tensão relativa ao barramento comum de 13,8 kV, número de
                  prédios com tensão baixa no mesmo instante, etc.).
"""
import numpy as np
import pandas as pd

ATR_INDIVIDUAL = [
    "v_med", "v_spread", "i_total", "p_total", "q_total", "fp_total", "deseq_i",
    "p_min_fase", "p_std_30min", "v_std_30min",
    "hora_sin", "hora_cos", "fds_ou_feriado", "letivo",
]
ATR_CAMPUS = ["v_dev_campus", "v_campus", "frac_v_baixa_campus"]
ATR_MULTIVARIADO = ATR_INDIVIDUAL + ATR_CAMPUS


def atributos_temporais(base):
    """Variabilidade recente (30 min) calculada na grade completa, por prédio.

    Um sensor travado tem variabilidade zero; janelas com lacuna ficam NaN.
    """
    b = base.sort_values(["predio", "slot"]).copy()
    g = b.groupby("predio")
    b["p_std_30min"] = g["p_total"].transform(lambda s: s.rolling(6, min_periods=6).std())
    b["v_std_30min"] = g["v_a"].transform(lambda s: s.rolling(6, min_periods=6).std())
    return b


def atributos_basicos(base):
    """Calcula os atributos individuais (por prédio e janela de 5 min)."""
    b = base.copy()
    b["p_min_fase"] = b[["p_a", "p_b", "p_c"]].min(axis=1)
    V = b[["v_a", "v_b", "v_c"]]
    b["v_med"] = V.mean(axis=1)
    b["v_spread"] = V.max(axis=1) - V.min(axis=1)
    b["fds_ou_feriado"] = b["tipo_dia"].isin(["fim_de_semana", "feriado", "recesso"]).astype(float)
    b["letivo"] = (b["tipo_dia"] == "letivo").astype(float)
    b["deseq_i"] = b["deseq_i"].fillna(0.0)  # prédio sem carga: sem desequilíbrio
    return b


def atributos_campus(b, ref_v=None):
    """Acrescenta atributos que comparam cada prédio com os demais no mesmo instante.

    `ref_v`: mediana de tensão de cada prédio no período de treino (remove o offset
    fixo, ex.: CCET ~10 V abaixo). Se None, é calculada a partir de `b`.
    """
    b = b.copy()
    if ref_v is None:
        ref_v = b.groupby("predio")["v_med"].median()
    b["v_rel"] = b["v_med"] - b["predio"].map(ref_v)          # desvio do próprio "normal"
    campus = b.groupby("slot")["v_rel"].median().rename("v_campus")
    baixa = (b.assign(baixa=b["v_min"] < 0.9 * b["predio"].map(ref_v))
               .groupby("slot")["baixa"].mean().rename("frac_v_baixa_campus"))
    b = b.merge(campus, left_on="slot", right_index=True, how="left")
    b = b.merge(baixa, left_on="slot", right_index=True, how="left")
    b["v_dev_campus"] = b["v_rel"] - b["v_campus"]           # o quanto o prédio destoa do campus
    return b, ref_v


def preparar(base, ref_v=None):
    """Atributos completos para as janelas com dado."""
    b = atributos_temporais(base)
    b = atributos_basicos(b[b["tem_dado"]])
    b, ref_v = atributos_campus(b, ref_v)
    b = b.dropna(subset=ATR_MULTIVARIADO)
    return b, ref_v
