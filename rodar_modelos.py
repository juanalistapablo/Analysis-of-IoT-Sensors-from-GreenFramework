"""Treina IF e LOF (individual × multivariado) e avalia com falhas sintéticas.

Uso:
    python rodar_modelos.py <pasta_saida_da_base_limpa>

Divisão cronológica: treino até 31/03/2026; teste de 01/04/2026 em diante.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from tcc_pipeline.atributos import ATR_INDIVIDUAL, ATR_MULTIVARIADO, preparar
from tcc_pipeline.injecao import injetar
from tcc_pipeline.modelos import DetectorPorPredio

CORTE = pd.Timestamp("2026-04-01")
TAXAS_ALARME = (0.5, 1.0, 2.0, 5.0)   # pontos de operação (% de alarmes nas janelas sem falha)
MIN_PREDIOS_SISTEMICO = 3


def avaliar(teste_inj, alarmes, gabarito):
    """Recall por tipo de falha (evento), escopo previsto e taxa de alarme fora das injeções."""
    t = teste_inj.assign(alarme=alarmes.values)
    linhas = []
    flag = t[t["alarme"]]
    n_flag_slot = flag.groupby("slot")["predio"].nunique()
    for _, g in gabarito.iterrows():
        predios = g["predio"].split(",")
        jan = (t["slot"] >= g["inicio"]) & (t["slot"] <= g["fim"]) & t["predio"].isin(predios)
        det_pred = t.loc[jan & t["alarme"], "predio"].unique()
        if g["escopo"] == "SISTEMICO":
            detectado = len(det_pred) >= max(1, int(np.ceil(len(predios) / 2)))
        else:
            detectado = len(det_pred) > 0
        escopo_prev = None
        if detectado:
            slots = t.loc[jan & t["alarme"], "slot"].unique()
            maxjunto = n_flag_slot.reindex(slots).max()
            escopo_prev = "SISTEMICO" if maxjunto >= MIN_PREDIOS_SISTEMICO else "LOCAL"
        linhas.append(dict(tipo=g["tipo"], escopo=g["escopo"], detectado=detectado, escopo_prev=escopo_prev))
    r = pd.DataFrame(linhas)
    limpo = t[t["injetado"] == ""]
    taxa_alarme = limpo["alarme"].mean() * 100
    return r, taxa_alarme


def main(pasta):
    t0 = time.time()
    base = pd.read_pickle(os.path.join(pasta, "base_5min.pkl"))
    treino_base = base[base["slot"] < CORTE]
    teste_base = base[base["slot"] >= CORTE]

    treino, ref_v = preparar(treino_base)
    teste_real, _ = preparar(teste_base, ref_v)
    teste_inj_base, gabarito = injetar(teste_base, n_por_tipo=40)
    teste_inj, _ = preparar(teste_inj_base, ref_v)
    gabarito.to_csv(os.path.join(pasta, "gabarito_injecao.csv"), index=False)
    print(f"treino {len(treino)} | teste {len(teste_inj)} | injeções {len(gabarito)} ({time.time()-t0:.0f}s)")

    resumo, por_tipo, alarmes_reais = [], [], {}
    for alg in ("IF", "LOF"):
        for nome, atr in (("individual", ATR_INDIVIDUAL), ("multivariado", ATR_MULTIVARIADO)):
            det = DetectorPorPredio(alg, atr).fit(treino)
            esc = det.escore(teste_inj)
            y = (teste_inj["injetado"] != "").values
            auc = roc_auc_score(y, esc)
            ap = average_precision_score(y, esc)
            limpo = teste_inj["injetado"] == ""
            for taxa_alvo in TAXAS_ALARME:
                # limiar por prédio que gera `taxa_alvo`% de alarmes nas janelas sem falha
                lim = esc[limpo].groupby(teste_inj.loc[limpo, "predio"]).quantile(1 - taxa_alvo / 100)
                al = esc > teste_inj["predio"].map(lim)
                r, taxa = avaliar(teste_inj, al, gabarito)
                r["modelo"], r["taxa_alvo"] = f"{alg}-{nome}", taxa_alvo
                por_tipo.append(r)
                sis = r[r["tipo"].str.startswith("afundamento") & r["detectado"]]
                acerto_escopo = (sis["escopo"] == sis["escopo_prev"]).mean() * 100 if len(sis) else np.nan
                resumo.append(dict(modelo=f"{alg}-{nome}", taxa_alarme=taxa_alvo, roc_auc=auc, pr_auc=ap,
                                   recall_eventos=r["detectado"].mean() * 100,
                                   acerto_escopo_afundamentos=acerto_escopo))
            # alarmes no teste REAL (sem injeção), para cruzar com as regras
            alr, razao = det.alarme(teste_real)
            alarmes_reais[f"{alg}-{nome}"] = alr
            print(f"{alg}-{nome}: ok ({time.time()-t0:.0f}s)")

    resumo = pd.DataFrame(resumo).round({"roc_auc": 3, "pr_auc": 3, "recall_eventos": 1, "acerto_escopo_afundamentos": 1})
    pt = pd.concat(por_tipo)
    pt.to_csv(os.path.join(pasta, "deteccao_por_evento.csv"), index=False)
    tab = pt[pt["taxa_alvo"] == 1.0].groupby(["modelo", "tipo"])["detectado"].mean().mul(100).round(0).unstack(0)
    resumo.to_csv(os.path.join(pasta, "resumo_modelos.csv"), index=False)
    tab.to_csv(os.path.join(pasta, "recall_por_tipo.csv"))
    ar = teste_real[["predio", "slot", "tipo_dia", "hora"]].copy()
    for k, v in alarmes_reais.items():
        ar[k] = v.values
    ar.to_pickle(os.path.join(pasta, "alarmes_teste_real.pkl"))
    pd.set_option("display.width", 200)
    print("\n", resumo.to_string(index=False))
    print("\nRecall (%) por tipo de falha injetada (taxa de alarme 1%):\n", tab.to_string())


if __name__ == "__main__":
    main(sys.argv[1])
