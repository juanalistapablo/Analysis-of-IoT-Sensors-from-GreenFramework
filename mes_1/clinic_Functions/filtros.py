import pandas as pd

def obter_predios_unicos(df, coluna='item_name'):
    """Retorna uma lista com os nomes únicos dos prédios encontrados nos dados."""
    return df[coluna].dropna().unique().tolist()

def filtrar_por_predio(df, nome_predio, coluna='item_name'):
    """Filtra e retorna uma tabela apenas com os dados do prédio especificado."""
    if nome_predio not in df[coluna].values:
        raise ValueError(f"O prédio '{nome_predio}' não foi encontrado na coluna '{coluna}'.")
    
    return df[df[coluna] == nome_predio].copy()

def separar_todos_predios(df, coluna='item_name'):
    """
    Cria um dicionário separando automaticamente todos os prédios únicos.
    A chave é o nome do prédio e o valor é a tabela (DataFrame) correspondente.
    """
    predios = obter_predios_unicos(df, coluna)
    tabelas_separadas = {}
    
    for predio in predios:
        tabelas_separadas[predio] = df[df[coluna] == predio].copy()
        
    return tabelas_separadas