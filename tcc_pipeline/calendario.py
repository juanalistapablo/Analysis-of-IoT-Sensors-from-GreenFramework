"""Classificação dos dias segundo os calendários acadêmicos oficiais da UFMA.

Fontes: Resolução nº 3.545-CONSEPE/2024 (calendário 2025) e Resolução
nº 4.278-CONSEPE/2026 (calendário 2026). As datas de feriados de 2026 foram
tiradas do quadro do calendário (Anexo Único); a lista textual da resolução
de 2026 repete por engano as datas de 2025 (ex.: Carnaval em 04/03).

Categorias (por prioridade):
  feriado        feriado nacional/estadual/municipal (São Luís) ou ponto facultativo
  fim_de_semana  sábado ou domingo
  recesso        recesso natalino
  ferias         fora de semestre letivo regular (inclui períodos letivos especiais
                 e férias docentes)
  letivo         dia útil dentro de semestre letivo regular
"""
import pandas as pd

SEMESTRES = [
    # 2024.2 ainda em andamento no início de 2025 (antes das férias docentes de 10/03).
    # Data de início anterior aos dados; data de fim inferida do calendário de 2025
    # (férias docentes a partir de 10/03/2025). CONFIRMAR com o calendário de 2024.
    ("2024.2", "2025-01-06", "2025-03-07"),
    ("2025.1", "2025-04-09", "2025-08-09"),
    ("2025.2", "2025-09-15", "2026-01-23"),
    ("2026.1", "2026-03-16", "2026-07-18"),
    ("2026.2", "2026-08-17", "2026-12-19"),
]

RECESSOS = [
    ("2024-12-21", "2025-01-03"),
    ("2025-12-22", "2026-01-03"),
    ("2026-12-21", "2027-01-02"),
]

FERIADOS = {
    # 2025
    "2025-01-01": "Confraternização Universal",
    "2025-03-03": "Carnaval (ponto facultativo)",
    "2025-03-04": "Carnaval",
    "2025-03-05": "Quarta-feira de Cinzas (ponto facultativo)",
    "2025-04-18": "Paixão de Cristo",
    "2025-04-21": "Tiradentes",
    "2025-05-01": "Dia do Trabalho",
    "2025-06-19": "Corpus Christi",
    "2025-06-29": "São Pedro (São Luís)",
    "2025-07-28": "Adesão do Maranhão à Independência",
    "2025-09-07": "Independência do Brasil",
    "2025-09-08": "Natividade de N. Sra. / Aniversário de São Luís",
    "2025-10-12": "Nossa Senhora Aparecida",
    "2025-10-28": "Dia do Servidor Público (ponto facultativo)",
    "2025-11-02": "Finados",
    "2025-11-15": "Proclamação da República",
    "2025-11-20": "Consciência Negra",
    "2025-12-08": "N. Sra. da Conceição (São Luís)",
    "2025-12-24": "Véspera de Natal (ponto facultativo)",
    "2025-12-25": "Natal",
    "2025-12-31": "Véspera de Ano Novo (ponto facultativo)",
    # 2026
    "2026-01-01": "Confraternização Universal",
    "2026-02-16": "Carnaval (ponto facultativo)",
    "2026-02-17": "Carnaval (ponto facultativo)",
    "2026-02-18": "Quarta-feira de Cinzas (ponto facultativo até 14h)",
    "2026-04-03": "Paixão de Cristo",
    "2026-04-20": "Ponto facultativo",
    "2026-04-21": "Tiradentes",
    "2026-05-01": "Dia do Trabalho",
    "2026-06-04": "Corpus Christi (ponto facultativo)",
    "2026-06-05": "Ponto facultativo",
    "2026-06-29": "São Pedro (São Luís)",
    "2026-07-28": "Adesão do Maranhão à Independência",
    "2026-09-07": "Independência do Brasil",
    "2026-09-08": "Natividade de N. Sra. / Aniversário de São Luís",
    "2026-10-12": "Nossa Senhora Aparecida",
    "2026-10-28": "Dia do Servidor Público (ponto facultativo)",
    "2026-11-02": "Finados",
    "2026-11-15": "Proclamação da República",
    "2026-11-20": "Consciência Negra",
    "2026-12-08": "N. Sra. da Conceição (São Luís)",
    "2026-12-24": "Véspera de Natal (ponto facultativo)",
    "2026-12-25": "Natal",
    "2026-12-31": "Véspera de Ano Novo (ponto facultativo)",
}


def tabela_calendario(inicio, fim):
    """Devolve um DataFrame indexado por data com tipo_dia, semestre e nome do feriado."""
    dias = pd.date_range(pd.Timestamp(inicio).normalize(), pd.Timestamp(fim).normalize(), freq="D")
    cal = pd.DataFrame(index=dias)
    cal["semestre"] = None
    for nome, ini, fi in SEMESTRES:
        cal.loc[ini:fi, "semestre"] = nome
    cal["recesso"] = False
    for ini, fi in RECESSOS:
        cal.loc[ini:fi, "recesso"] = True
    cal["feriado"] = pd.Series(FERIADOS).rename(index=pd.Timestamp).reindex(cal.index)
    fds = cal.index.dayofweek >= 5

    tipo = pd.Series("ferias", index=cal.index)
    tipo[cal["semestre"].notna()] = "letivo"
    tipo[cal["recesso"]] = "recesso"
    tipo[fds] = "fim_de_semana"
    tipo[cal["feriado"].notna()] = "feriado"
    cal["tipo_dia"] = tipo
    cal.index.name = "data"
    return cal
