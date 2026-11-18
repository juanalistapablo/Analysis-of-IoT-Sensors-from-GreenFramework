"""Injeção de falhas sintéticas para validar os detectores (não há rótulos reais).

Cada falha altera a base de 5 min (antes do cálculo dos atributos) e é registrada
com seu tipo, escopo, categoria e janelas afetadas — o "gabarito".

Tipos (categoria da Tabela 3.2 entre parênteses):
  afundamento_local_forte   (A) tensão de UM prédio cai 20–30% por 30–60 min
  afundamento_local_leve    (A) tensão de UM prédio cai 6–10% por 30–60 min
  afundamento_sistemico     (A) tensão de TODOS os prédios com dado cai 10–20%
  desperdicio_noturno       (B) carga noturna de um prédio +60–120% durante 3 h
  desequilibrio_fase        (C) corrente de uma fase ×1,8–2,5 por 1–2 h
  tc_invertido              (D) potência de uma fase com sinal trocado à noite por 3 h
  sensor_travado            (D) todas as grandezas congeladas por 2 h
"""
import numpy as np
import pandas as pd

TIPOS = {
    "afundamento_local_forte": ("A", "LOCAL"),
    "afundamento_local_leve": ("A", "LOCAL"),
    "afundamento_sistemico": ("A", "SISTEMICO"),
    "desperdicio_noturno": ("B", "LOCAL"),
    "desequilibrio_fase": ("C", "LOCAL"),
    "tc_invertido": ("D", "LOCAL"),
    "sensor_travado": ("D", "LOCAL"),
}
GRANDEZAS = ([f"{g}_{f}" for g in ("v", "i", "p", "q", "s", "fp") for f in "abc"]
             + ["fp_total", "freq", "temp", "v_min", "p_total", "q_total", "s_total", "i_total"])


def _recalcular(b, idx):
    for g in ("p", "q", "s", "i"):
        b.loc[idx, f"{g}_total"] = b.loc[idx, [f"{g}_a", f"{g}_b", f"{g}_c"]].sum(axis=1)
    b.loc[idx, "v_min"] = b.loc[idx, ["v_a", "v_b", "v_c"]].min(axis=1)
    I = b.loc[idx, ["i_a", "i_b", "i_c"]]
    med = I.mean(axis=1)
    b.loc[idx, "deseq_i"] = (I.sub(med, axis=0).abs().max(axis=1) / med.where(med > 1)) * 100


def injetar(base, n_por_tipo=40, semente=42, slots_validos=None):
    """Devolve (base_alterada, gabarito). Só usa janelas com dado em todos os prédios afetados."""
    rng = np.random.default_rng(semente)
    b = base.copy()
    b["injetado"] = ""
    pos = {k: v for k, v in b.groupby("predio").groups.items()}
    com_dado = b[b["tem_dado"]]
    if slots_validos is not None:
        com_dado = com_dado[com_dado["slot"].isin(slots_validos)]
    predios = sorted(b["predio"].unique())
    gabarito = []
    ocupado = set()

    def escolher(predio, dur, noite=None):
        cand = com_dado[com_dado["predio"] == predio]
        if noite is not None:
            cand = cand[cand["hora"].between(*noite)]
        for _ in range(50):
            s0 = cand["slot"].iloc[rng.integers(len(cand))]
            janela = pd.date_range(s0, periods=dur, freq="5min")
            idx = b.index[(b["predio"] == predio) & b["slot"].isin(janela) & b["tem_dado"]]
            chave = {(predio, s) for s in janela}
            if len(idx) == dur and not (chave & ocupado):
                ocupado.update(chave)
                return idx, janela
        return None, None

    for tipo, (cat, escopo) in TIPOS.items():
        feitos = 0
        while feitos < n_por_tipo:
            if tipo == "afundamento_sistemico":
                # instante em que 3+ prédios têm dado
                cnt = com_dado.groupby("slot")["predio"].nunique()
                s0 = cnt[cnt >= 3].index[rng.integers((cnt >= 3).sum())]
                dur = int(rng.integers(6, 13))
                janela = pd.date_range(s0, periods=dur, freq="5min")
                idx = b.index[b["slot"].isin(janela) & b["tem_dado"]]
                fator = 1 - rng.uniform(0.10, 0.20)
                b.loc[idx, ["v_a", "v_b", "v_c"]] *= fator
                _recalcular(b, idx)
                b.loc[idx, "injetado"] = tipo
                afetados = sorted(b.loc[idx, "predio"].unique())
                for p in afetados:
                    ocupado.update({(p, s) for s in janela})
                gabarito.append(dict(tipo=tipo, categoria=cat, escopo=escopo, predio=",".join(afetados),
                                     inicio=janela[0], fim=janela[-1], n_slots=dur))
                feitos += 1
                continue

            predio = predios[rng.integers(len(predios))]
            if tipo.startswith("afundamento_local"):
                dur = int(rng.integers(6, 13))
                idx, janela = escolher(predio, dur)
                if idx is None:
                    continue
                q = rng.uniform(0.20, 0.30) if tipo.endswith("forte") else rng.uniform(0.06, 0.10)
                b.loc[idx, ["v_a", "v_b", "v_c"]] *= (1 - q)
            elif tipo == "desperdicio_noturno":
                dur = 36
                idx, janela = escolher(predio, dur, noite=(0, 2))
                if idx is None:
                    continue
                extra = 1 + rng.uniform(0.6, 1.2)
                for g in ("i", "p", "q", "s"):
                    for f in "abc":
                        b.loc[idx, f"{g}_{f}"] = b.loc[idx, f"{g}_{f}"].abs() * extra * np.sign(b.loc[idx, f"{g}_{f}"].replace(0, 1))
            elif tipo == "desequilibrio_fase":
                dur = int(rng.integers(12, 25))
                idx, janela = escolher(predio, dur)
                if idx is None:
                    continue
                f = "abc"[rng.integers(3)]
                k = rng.uniform(1.8, 2.5)
                for g in ("i", "p", "q", "s"):
                    b.loc[idx, f"{g}_{f}"] *= k
            elif tipo == "tc_invertido":
                dur = 36
                idx, janela = escolher(predio, dur, noite=(0, 2))
                if idx is None:
                    continue
                f = "abc"[rng.integers(3)]
                b.loc[idx, f"p_{f}"] = -b.loc[idx, f"p_{f}"].abs()
                b.loc[idx, f"fp_{f}"] = -b.loc[idx, f"fp_{f}"].abs()
            elif tipo == "sensor_travado":
                dur = 24
                idx, janela = escolher(predio, dur)
                if idx is None:
                    continue
                for c in GRANDEZAS:
                    b.loc[idx, c] = b.loc[idx[0], c]
            _recalcular(b, idx)
            b.loc[idx, "injetado"] = tipo
            gabarito.append(dict(tipo=tipo, categoria=cat, escopo=escopo, predio=predio,
                                 inicio=janela[0], fim=janela[-1], n_slots=len(janela)))
            feitos += 1
    return b, pd.DataFrame(gabarito)
