import pandas as pd

def separar_todos_predios(df, coluna='item_name'):
    """
    Identifica automaticamente os elementos únicos da coluna e 
    gera uma tabela separada para cada um deles.
    Não é necessário digitar o nome de nenhum prédio manualmente.
    """
    # 1. Calcula os elementos únicos ignorando valores nulos
    elementos_unicos = df[coluna].dropna().unique().tolist()
    
    tabelas_separadas = {}
    
    # 2. Gera uma tabela para cada elemento único encontrado
    for elemento in elementos_unicos:
        tabelas_separadas[elemento] = df[df[coluna] == elemento].copy()
        
    return tabelas_separadas