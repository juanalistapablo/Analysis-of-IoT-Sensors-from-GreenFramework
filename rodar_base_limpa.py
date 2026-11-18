"""Gera a base limpa (5 min) e a tabela de eventos das regras.

Uso:
    python rodar_base_limpa.py "<pasta com dados_AAAA_MM.csv>" <pasta_saida>
"""
import os
import sys
import time

import pandas as pd

from tcc_pipeline.calendario import tabela_calendario
from tcc_pipeline.carregamento import carregar_todos
from tcc_pipeline.reamostragem import adicionar_contexto_temporal, montar_base_5min
from tcc_pipeline.regras import aplicar_regras, desequilibrio_corrente


def main(pasta_dados, saida):
    os.makedirs(saida, exist_ok=True)
    t0 = time.time()
    df, rel = carregar_todos(pasta_dados)
    print("Carregamento:", {k: v for k, v in rel.items()}, f"({time.time()-t0:.0f}s)")
    df.to_pickle(os.path.join(saida, "leituras_dedup.pkl"))

    cal = tabela_calendario(rel["inicio"], rel["fim"])
    cal.to_csv(os.path.join(saida, "calendario.csv"))

    base = montar_base_5min(df)
    base = adicionar_contexto_temporal(base, cal)
    base["deseq_i"] = desequilibrio_corrente(base)
    base.to_pickle(os.path.join(saida, "base_5min.pkl"))
    print("Base 5 min:", base.shape, f"({time.time()-t0:.0f}s)")

    ev = aplicar_regras(base, df)
    ev.to_csv(os.path.join(saida, "eventos_regras.csv"), index=False)
    print("Eventos:", len(ev), f"({time.time()-t0:.0f}s)")
    print(ev.groupby(["regra", "categoria", "escopo"]).size().to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
