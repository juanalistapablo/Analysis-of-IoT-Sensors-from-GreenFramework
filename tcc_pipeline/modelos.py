"""Detectores não supervisionados: Isolation Forest e LOF, individual × multivariado.

Um modelo por prédio. O limiar de alarme é o percentil `PCT_LIMIAR` dos escores
no próprio treino (taxa de alarme esperada ≈ 100 − PCT_LIMIAR %).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler

PCT_LIMIAR = 99.5
MAX_TREINO_LOF = 20000
SEMENTE = 42


def _novo_modelo(nome):
    if nome == "IF":
        return IsolationForest(n_estimators=200, contamination="auto", random_state=SEMENTE, n_jobs=-1)
    if nome == "LOF":
        return LocalOutlierFactor(n_neighbors=35, novelty=True, n_jobs=-1)
    raise ValueError(nome)


class DetectorPorPredio:
    """Treina um detector (IF ou LOF) por prédio sobre um conjunto de atributos."""

    def __init__(self, algoritmo, atributos):
        self.algoritmo = algoritmo
        self.atributos = atributos
        self.modelos, self.escaladores, self.limiares = {}, {}, {}

    def fit(self, treino):
        rng = np.random.default_rng(SEMENTE)
        for predio, d in treino.groupby("predio"):
            X = d[self.atributos].values
            if self.algoritmo == "LOF" and len(X) > MAX_TREINO_LOF:
                X = X[rng.choice(len(X), MAX_TREINO_LOF, replace=False)]
            esc = RobustScaler().fit(X)
            Xs = np.clip(esc.transform(X), -50, 50)
            m = _novo_modelo(self.algoritmo).fit(Xs)
            escore = -m.score_samples(Xs)          # maior = mais anômalo
            self.modelos[predio], self.escaladores[predio] = m, esc
            self.limiares[predio] = np.percentile(escore, PCT_LIMIAR)
        return self

    def escore(self, dados):
        out = pd.Series(np.nan, index=dados.index)
        for predio, d in dados.groupby("predio"):
            if predio not in self.modelos:
                continue
            Xs = np.clip(self.escaladores[predio].transform(d[self.atributos].values), -50, 50)
            out.loc[d.index] = -self.modelos[predio].score_samples(Xs)
        return out

    def alarme(self, dados):
        e = self.escore(dados)
        lim = dados["predio"].map(self.limiares)
        return e > lim, e / lim
