"""Leitura dos CSVs brutos exportados do GreenFramework.

Cada linha do CSV traz metadados da leitura e uma coluna `dados` com o JSON
completo do medidor. Aqui extraímos apenas as grandezas usadas no TCC,
corrigimos o carimbo de tempo e removemos as duplicatas geradas pela query SQL.
"""
import glob
import json
import os
from multiprocessing import Pool

import pandas as pd

COLUNAS_CSV = ["server", "item_name", "timestamp_leitura", "dados"]


def _get(d, *chaves):
    for k in chaves:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def extrair_grandezas(js):
    """Converte o JSON de uma leitura em um dicionário plano com as grandezas de interesse."""
    try:
        d = json.loads(js)
    except (TypeError, ValueError):
        return {}
    out = {
        "uptime": _get(d, "device", "uptime"),
        "temp": _get(d, "temp", "internal", "value"),
        "freq": _get(d, "frequency", "phase", "total"),
        "fp_total": _get(d, "power_factor", "phase", "total"),
        "e_ativa_dir": _get(d, "energy_accumulated", "active", "direct"),
        "e_ativa_rev": _get(d, "energy_accumulated", "active", "reverse"),
    }
    for f in "abc":
        out[f"v_{f}"] = _get(d, "voltage", "phase", f)
        out[f"i_{f}"] = _get(d, "current", "phase", f)
        out[f"p_{f}"] = _get(d, "active_power", "phase", f)
        out[f"q_{f}"] = _get(d, "reactive_power", "phase", f)
        out[f"s_{f}"] = _get(d, "apparent_power", "phase", f)
        out[f"fp_{f}"] = _get(d, "power_factor", "phase", f)
    return out


def ler_csv_bruto(caminho):
    """Lê um CSV mensal bruto e devolve um DataFrame plano (uma linha por leitura)."""
    df = pd.read_csv(caminho, usecols=COLUNAS_CSV)
    grandezas = pd.DataFrame([extrair_grandezas(x) for x in df["dados"].values])
    df = pd.concat([df.drop(columns="dados").reset_index(drop=True), grandezas], axis=1)
    # Usamos o carimbo da PRÓPRIA leitura (não o da leitura anterior).
    df["ts"] = pd.to_datetime(df["timestamp_leitura"], format="ISO8601")
    df["predio"] = df["item_name"].str.replace("Medidor ", "", regex=False).str.strip()
    df = df.drop(columns=["timestamp_leitura", "item_name"])
    for c in df.columns:
        if c not in ("predio", "ts"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def carregar_todos(pasta, processos=2):
    """Lê todos os CSVs da pasta, junta, remove duplicatas e ordena por prédio e tempo.

    Retorna (df, relatorio), em que relatorio resume quantas linhas foram removidas.
    """
    arquivos = sorted(glob.glob(os.path.join(pasta, "*.csv")))
    if not arquivos:
        raise ValueError(f"Nenhum CSV encontrado em {pasta}")
    with Pool(processos) as p:
        partes = p.map(ler_csv_bruto, arquivos)
    df = pd.concat(partes, ignore_index=True)
    n_bruto = len(df)
    # A query de exportação repete leituras (mesmo prédio e instante) com valores de
    # Δt diferentes; mantemos uma única linha por prédio e instante.
    df = df.drop_duplicates(["predio", "ts"], keep="first")
    df = df.sort_values(["predio", "ts"]).reset_index(drop=True)
    # Δt recalculado corretamente, por prédio.
    df["dt_min"] = df.groupby("predio")["ts"].diff().dt.total_seconds() / 60
    relatorio = {
        "arquivos": len(arquivos),
        "linhas_brutas": n_bruto,
        "duplicatas_removidas": n_bruto - len(df),
        "linhas_finais": len(df),
        "predios": sorted(df["predio"].unique()),
        "inicio": df["ts"].min(),
        "fim": df["ts"].max(),
    }
    return df, relatorio
