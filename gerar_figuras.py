"""Figuras do Capítulo 4 (PDF para o LaTeX + PNG para conferência).

Uso:
    python gerar_figuras.py <pasta_saida_da_base_limpa> <pasta_figuras>
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AZUL, LARANJA, AQUA, AMARELO, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
CINZA, TEXTO, TEXTO2, GRADE = "#a8a79f", "#1f1f1e", "#5f5e58", "#e6e5e0"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": CINZA, "axes.labelcolor": TEXTO,
    "xtick.color": TEXTO2, "ytick.color": TEXTO2, "axes.grid": True, "grid.color": GRADE,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.dpi": 150,
})
ESTILO = {  # cor = algoritmo; traço = versão (identidade nunca só pela cor)
    "IF-individual": dict(color=AZUL, ls="--", marker="o", mfc="white"),
    "IF-multivariado": dict(color=AZUL, ls="-", marker="o"),
    "LOF-individual": dict(color=LARANJA, ls="--", marker="s", mfc="white"),
    "LOF-multivariado": dict(color=LARANJA, ls="-", marker="s"),
}
NOMES_TIPO = {
    "afundamento_local_forte": "Afundamento local forte (A)",
    "afundamento_local_leve": "Afundamento local leve (A)",
    "afundamento_sistemico": "Afundamento sistêmico (A)",
    "desperdicio_noturno": "Desperdício noturno (B)",
    "desequilibrio_fase": "Desequilíbrio de fase (C)",
    "tc_invertido": "TC invertido (D)",
    "sensor_travado": "Sensor travado (D)",
}


def salvar(fig, pasta, nome):
    fig.savefig(os.path.join(pasta, nome + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(pasta, nome + ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def fig_recall_x_alarme(pasta, figs):
    r = pd.read_csv(os.path.join(pasta, "resumo_modelos.csv"))
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for m, st in ESTILO.items():
        d = r[r["modelo"] == m].sort_values("taxa_alarme")
        ax.plot(d["taxa_alarme"], d["recall_eventos"], lw=2, ms=6, label=m.replace("-", " "), **st)
        ax.annotate(f"{d['recall_eventos'].iloc[-1]:.0f}%", (d["taxa_alarme"].iloc[-1], d["recall_eventos"].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", color=TEXTO2, fontsize=9)
    ax.set_xscale("log")
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks([0.5, 1, 2, 5])
    ax.set_xticklabels(["0,5%", "1%", "2%", "5%"])
    ax.set_ylim(0, 100)
    ax.set_xlabel("Taxa de alarme nas janelas sem falha")
    ax.set_ylabel("Falhas injetadas detectadas (%)")
    ax.legend(loc="upper left", fontsize=9)
    salvar(fig, figs, "fig_recall_x_alarme")


def fig_recall_por_tipo(pasta, figs):
    t = pd.read_csv(os.path.join(pasta, "recall_por_tipo.csv"), index_col=0)
    t = t.loc[list(NOMES_TIPO)][list(ESTILO)]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("azul", ["#f4f8fd", "#9ec5f4", "#2a78d6", "#0d366b"])
    ax.imshow(t.values, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            v = t.values[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=9.5,
                    color="white" if v >= 60 else TEXTO)
    ax.set_xticks(range(4))
    ax.set_xticklabels([m.replace("-", "\n") for m in t.columns])
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels([NOMES_TIPO[k] for k in t.index])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(t), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    salvar(fig, figs, "fig_recall_por_tipo")


def fig_evento_04_05(pasta, figs):
    df = pd.read_pickle(os.path.join(pasta, "leituras_dedup.pkl"))
    ini, fim = pd.Timestamp("2026-05-04 14:30"), pd.Timestamp("2026-05-04 17:00")
    d = df[(df["ts"] >= ini) & (df["ts"] <= fim)]
    cores = {"CCET": AZUL, "CCH": LARANJA, "CCSO": AQUA, "ODONTO": AMARELO}
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for p, dp in d.groupby("predio"):
        dp = dp.sort_values("ts").set_index("ts")["v_a"]
        # interrompe a linha onde não há leitura por mais de 10 min
        quebra = dp.index.to_series().diff() > pd.Timedelta("10min")
        dp = pd.concat([dp, pd.Series(np.nan, index=dp.index[quebra] - pd.Timedelta("1s"))]).sort_index()
        ax.plot(dp.index, dp.values, lw=1.8, color=cores.get(p, CINZA), label=p, zorder=3 if p in cores else 2)
    ax.axvspan(pd.Timestamp("2026-05-04 15:05"), pd.Timestamp("2026-05-04 15:30"), color=GRADE, alpha=0.7, zorder=1)
    ax.axvline(pd.Timestamp("2026-05-04 15:31"), color=TEXTO2, lw=1, ls=":")
    ax.set_ylim(40, 250)
    ax.text(pd.Timestamp("2026-05-04 15:17:30"), 242, "afundamento simultâneo", fontsize=8.5, color=TEXTO2, ha="center", va="top")
    ax.text(pd.Timestamp("2026-05-04 15:33"), 242, "perda de dados\nnos 4 prédios", fontsize=8.5, color=TEXTO2, va="top")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    ax.set_ylabel("Tensão fase A (V)")
    ax.set_xlabel("04/05/2026")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=9)
    salvar(fig, figs, "fig_evento_04_05_2026")


def fig_correlacao_tensao(pasta, figs):
    b = pd.read_pickle(os.path.join(pasta, "base_5min.pkl"))
    V = b.pivot(index="slot", columns="predio", values="v_a")
    C = V.where(V >= 190).corr()
    ordem = ["BIO", "CCET", "CCH", "CCSO", "IEE", "ODONTO", "PF"]
    C = C.loc[ordem, ordem]
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("azul", ["#f4f8fd", "#9ec5f4", "#2a78d6", "#0d366b"])
    im = ax.imshow(C.values, cmap=cmap, vmin=0.9, vmax=1.0)
    for i in range(7):
        for j in range(7):
            v = C.values[i, j]
            ax.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center", fontsize=8.5,
                    color="white" if v >= 0.96 else TEXTO)
    ax.set_xticks(range(7)); ax.set_xticklabels(ordem, rotation=45, ha="right")
    ax.set_yticks(range(7)); ax.set_yticklabels(ordem)
    ax.grid(False); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.outline.set_visible(False)
    cb.set_label("Correlação de Pearson")
    cb.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:.2f}".replace(".", ",")))
    salvar(fig, figs, "fig_correlacao_tensao")
    return C


if __name__ == "__main__":
    pasta, figs = sys.argv[1], sys.argv[2]
    os.makedirs(figs, exist_ok=True)
    fig_recall_x_alarme(pasta, figs)
    fig_recall_por_tipo(pasta, figs)
    fig_evento_04_05(pasta, figs)
    C = fig_correlacao_tensao(pasta, figs)
    v = C.values[np.triu_indices(7, 1)]
    print("correlação (pares): min %.3f max %.3f" % (v.min(), v.max()))
