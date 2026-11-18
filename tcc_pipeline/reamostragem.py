"""Reamostragem das leituras para uma grade comum de 5 minutos.

CCET e PF leem a cada 5 min; os demais prédios, a cada 1 min, em segundos
diferentes. Para comparar prédios (abordagem multivariada) todos precisam
estar na mesma grade temporal.
"""
import numpy as np
import pandas as pd

FREQ = "5min"
MEDIAS = ([f"{g}_{f}" for g in ("v", "i", "p", "q", "s", "fp") for f in "abc"]
          + ["fp_total", "freq", "temp"])


def reamostrar_predio(dp):
    """Agrega as leituras de um prédio em janelas de 5 min."""
    dp = dp.set_index("ts").sort_index()
    g = dp.resample(FREQ)
    out = g[MEDIAS].mean()
    out["v_min"] = g[["v_a", "v_b", "v_c"]].min().min(axis=1)
    out["n_leituras"] = g["v_a"].count()
    out["e_ativa_rev"] = g["e_ativa_rev"].last()
    # reinício do medidor: uptime diminui dentro da janela ou em relação à anterior
    up = dp["uptime"]
    reinicio = (up.diff() < 0).astype(int)
    out["reinicio"] = reinicio.resample(FREQ).max().fillna(0).astype(bool)
    for g_ in ("p", "q", "s", "i"):
        out[f"{g_}_total"] = out[[f"{g_}_a", f"{g_}_b", f"{g_}_c"]].sum(axis=1, min_count=3)
    return out


def montar_base_5min(df, inicio=None, fim=None):
    """Base longa (predio, slot) numa grade global comum, com flag `tem_dado`."""
    inicio = pd.Timestamp(inicio or df["ts"].min()).floor(FREQ)
    fim = pd.Timestamp(fim or df["ts"].max()).floor(FREQ)
    grade = pd.date_range(inicio, fim, freq=FREQ, name="slot")
    partes = []
    for predio, dp in df.groupby("predio"):
        r = reamostrar_predio(dp).reindex(grade)
        r["n_leituras"] = r["n_leituras"].fillna(0).astype(int)
        r["reinicio"] = r["reinicio"].fillna(False).astype(bool)
        r["predio"] = predio
        partes.append(r.reset_index())
    base = pd.concat(partes, ignore_index=True)
    base["tem_dado"] = base["n_leituras"] > 0
    return base


def matriz(base, coluna):
    """Matriz larga (slot × prédio) de uma grandeza — entrada dos modelos multivariados."""
    return base.pivot(index="slot", columns="predio", values=coluna)


def adicionar_contexto_temporal(base, calendario):
    """Acrescenta hora, dia da semana, tipo de dia e indicador de período noturno."""
    base = base.copy()
    base["data"] = base["slot"].dt.normalize()
    base = base.merge(calendario[["tipo_dia", "semestre"]], left_on="data", right_index=True, how="left")
    base["hora"] = base["slot"].dt.hour + base["slot"].dt.minute / 60
    base["dia_semana"] = base["slot"].dt.dayofweek
    # Noite = sem geração solar relevante em São Luís (nascer ~5h40, pôr ~18h).
    base["noite"] = (base["hora"] < 5) | (base["hora"] >= 19)
    # codificação cíclica da hora (útil para os modelos)
    base["hora_sin"] = np.sin(2 * np.pi * base["hora"] / 24)
    base["hora_cos"] = np.cos(2 * np.pi * base["hora"] / 24)
    return base
