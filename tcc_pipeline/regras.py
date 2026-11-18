"""Camada de regras determinísticas (baseadas em conhecimento do domínio elétrico).

As regras detectam e classificam os eventos que têm assinatura física clara.
Os modelos de aprendizado de máquina (Isolation Forest, LOF) ficam com o que
sobra: desvios de padrão sem regra explícita.

Categorias (Tabela 3.2 do TCC):
  A  Interrupção de energia (queda/afundamento de tensão, carga zerada)
  B  Desperdício (consumo fora do padrão em período ocioso) — tratado pelos modelos
  C  Sobrecarga / desequilíbrio — tratado pelos modelos + indicador de desequilíbrio
  D  Falha de medição/telemetria (lacuna, TC invertido, sensor travado)

Escopo: LOCAL (um prédio, os demais normais), SISTEMICO (vários prédios ao
mesmo tempo) ou INDETERMINADO (não havia outro prédio com dado para comparar).
"""
import numpy as np
import pandas as pd

LIMIAR_TENSAO = 190.0      # V fase-neutro (~0,82 pu de 231 V); abaixo disso: afundamento/queda
MIN_SLOTS_LACUNA = 3       # 3 janelas de 5 min = lacuna de 15 min ou mais
TOL_SIMULTANEO = pd.Timedelta("10min")
MIN_PREDIOS_SISTEMICO = 3  # lacuna sistêmica: 3+ prédios perdem dados juntos
LIMIAR_P_NEG = -0.2        # kW por fase
FRAC_NOITE_NEG = 0.8       # TC invertido: >=80% da noite com potência negativa
MIN_TRAVADO_MIN = 30       # sensor travado: leituras idênticas por >= 30 min


def _episodios(flag, slot, tolerancia=1):
    """Agrupa janelas marcadas consecutivas (permitindo `tolerancia`-1 janelas de folga)."""
    idx = np.flatnonzero(flag.values)
    if len(idx) == 0:
        return []
    cortes = np.flatnonzero(np.diff(idx) > tolerancia) + 1
    grupos = np.split(idx, cortes)
    return [(slot.iloc[g[0]], slot.iloc[g[-1]], len(g)) for g in grupos]


def regra_lacunas(base):
    """Lacunas de telemetria (>=15 min sem leitura) e sua simultaneidade entre prédios."""
    eventos = []
    for predio, b in base.groupby("predio"):
        b = b.sort_values("slot").reset_index(drop=True)
        com = np.flatnonzero(b["tem_dado"].values)
        if len(com) == 0:
            continue
        b = b.iloc[com[0]:com[-1] + 1].reset_index(drop=True)  # só dentro do período de operação
        for ini, fim, n in _episodios(~b["tem_dado"], b["slot"]):
            if n >= MIN_SLOTS_LACUNA:
                eventos.append(dict(predio=predio, inicio=ini, fim=fim + pd.Timedelta("5min")))
    ev = pd.DataFrame(eventos)
    if ev.empty:
        return ev
    ev = ev.sort_values("inicio").reset_index(drop=True)
    # quantos prédios começam a perder dados juntos (±10 min)
    ini = ev["inicio"].values
    ev["n_predios_juntos"] = [int(((abs(ini - t)) <= TOL_SIMULTANEO.to_timedelta64()).sum()) for t in ini]
    ev["escopo"] = np.where(ev["n_predios_juntos"] >= MIN_PREDIOS_SISTEMICO, "SISTEMICO", "LOCAL")
    ev["regra"] = "lacuna_telemetria"
    ev["categoria"] = "D"
    return ev


def regra_tensao(base):
    """Afundamentos/quedas de tensão (<190 V em qualquer fase) e escopo local × sistêmico."""
    V = base.pivot(index="slot", columns="predio", values="v_min")
    baixo = V < LIMIAR_TENSAO
    com_dado = V.notna()
    eventos = []
    for predio in V.columns:
        s = baixo[predio]
        for ini, fim, n in _episodios(s, pd.Series(V.index), tolerancia=2):
            janela = slice(ini, fim)
            outros = [c for c in V.columns if c != predio]
            afetados = [c for c in outros if baixo.loc[janela, c].any()]
            com_outros = [c for c in outros if com_dado.loc[janela, c].any()]
            if afetados:
                escopo = "SISTEMICO"
            elif com_outros:
                escopo = "LOCAL"
            else:
                escopo = "INDETERMINADO"
            eventos.append(dict(predio=predio, inicio=ini, fim=fim + pd.Timedelta("5min"),
                                v_min=float(V.loc[janela, predio].min()),
                                outros_afetados=",".join(afetados), n_outros_com_dado=len(com_outros),
                                escopo=escopo))
    ev = pd.DataFrame(eventos)
    if ev.empty:
        return ev
    ev["regra"] = np.where(ev["v_min"] < 50, "tensao_zero", "afundamento_tensao")
    ev["categoria"] = "A"
    return ev


def regra_tc_invertido(base):
    """Potência de fase negativa durante a noite inteira (sem sol) → TC invertido/ligação trocada."""
    noite = base[base["noite"] & base["tem_dado"]].copy()
    # a "noite" que começa às 19h pertence ao dia seguinte (madrugada)
    noite["noite_ref"] = (noite["slot"] + pd.Timedelta("5h")).dt.normalize()
    eventos = []
    for f in "abc":
        noite["neg"] = noite[f"p_{f}"] < LIMIAR_P_NEG
        g = noite.groupby(["predio", "noite_ref"])["neg"].agg(["mean", "size"])
        g = g[g["size"] >= 24]  # ao menos 2 h de dados na noite
        g["flag"] = g["mean"] >= FRAC_NOITE_NEG
        for predio, gp in g.groupby(level=0):
            gp = gp.droplevel(0)
            datas = pd.Series(gp.index)
            for ini, fim, n in _episodios(gp["flag"].reset_index(drop=True), datas, tolerancia=3):
                eventos.append(dict(predio=predio, inicio=ini, fim=fim + pd.Timedelta("1D"),
                                    fase=f, noites=n))
    ev = pd.DataFrame(eventos)
    if ev.empty:
        return ev
    ev["regra"] = "tc_invertido"
    ev["categoria"] = "D"
    ev["escopo"] = "LOCAL"
    return ev


def regra_sensor_travado(df_bruto):
    """Leituras idênticas (tensão e corrente) por >= 30 min com o medidor energizado."""
    cols = ["v_a", "v_b", "v_c", "i_a", "i_b", "i_c"]
    eventos = []
    for predio, d in df_bruto.groupby("predio"):
        d = d.sort_values("ts")
        mudou = d[cols].ne(d[cols].shift()).any(axis=1)
        grupo = mudou.cumsum()
        r = d.groupby(grupo).agg(inicio=("ts", "first"), fim=("ts", "last"),
                                 n=("ts", "size"), v=("v_a", "first"))
        r["dur"] = (r["fim"] - r["inicio"]).dt.total_seconds() / 60
        r = r[(r["dur"] >= MIN_TRAVADO_MIN) & (r["n"] >= 3) & (r["v"] > 50)]
        for _, x in r.iterrows():
            eventos.append(dict(predio=predio, inicio=x["inicio"], fim=x["fim"], n_leituras=int(x["n"])))
    ev = pd.DataFrame(eventos)
    if ev.empty:
        return ev
    ev["regra"] = "sensor_travado"
    ev["categoria"] = "D"
    ev["escopo"] = "LOCAL"
    return ev


def desequilibrio_corrente(base):
    """Desequilíbrio de corrente (definição NEMA): máximo desvio em relação à média / média × 100.

    Retorna NaN quando a corrente média é ~0 (prédio desligado), em vez de 0%.
    """
    I = base[["i_a", "i_b", "i_c"]]
    med = I.mean(axis=1)
    desvio = I.sub(med, axis=0).abs().max(axis=1)
    return (desvio / med.where(med > 1.0) * 100)


def aplicar_regras(base, df_bruto):
    """Executa todas as regras e devolve uma única tabela de eventos."""
    partes = [regra_lacunas(base), regra_tensao(base), regra_tc_invertido(base),
              regra_sensor_travado(df_bruto)]
    ev = pd.concat([p for p in partes if not p.empty], ignore_index=True)
    ev["duracao_min"] = (ev["fim"] - ev["inicio"]).dt.total_seconds() / 60

    # Refinamento: lacuna sistêmica precedida de afundamento de tensão nos mesmos
    # prédios indica QUEDA DE ENERGIA (categoria A), não falha do servidor (D).
    tens = ev[ev["regra"].isin(["afundamento_tensao", "tensao_zero"])]
    lac = ev["regra"] == "lacuna_telemetria"
    precedida = []
    for i, r in ev[lac].iterrows():
        t = tens[(tens["predio"] == r["predio"]) & (tens["fim"] >= r["inicio"] - pd.Timedelta("15min"))
                 & (tens["inicio"] <= r["inicio"])]
        precedida.append((i, not t.empty))
    for i, flag in precedida:
        ev.loc[i, "apos_afundamento"] = flag
        if flag:
            ev.loc[i, "categoria"] = "A"
    ev["apos_afundamento"] = ev["apos_afundamento"].fillna(False).astype(bool)
    cols = ["predio", "regra", "categoria", "escopo", "inicio", "fim", "duracao_min"]
    return ev[cols + [c for c in ev.columns if c not in cols]].sort_values("inicio").reset_index(drop=True)
