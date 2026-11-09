import pandas as pd

def remover_colunas_rede_nulas(df):
    """
    Verifica TODAS as colunas do DataFrame.
    Qualquer coluna que esteja 100% preenchida com valores nulos (NaN) será removida.
    Imprime o nome das colunas que foram apagadas.
    """
    # Guarda a lista de colunas originais antes da limpeza
    colunas_antes = set(df.columns)
    
    # O dropna(how='all', axis=1) remove magicamente qualquer coluna onde todos os valores sejam nulos
    df_limpo = df.dropna(axis=1, how='all')
    
    # Descobre quais colunas desapareceram fazendo a diferença entre o antes e o depois
    colunas_removidas = list(colunas_antes - set(df_limpo.columns))
    
    if colunas_removidas:
        print(f"✅ Foram removidas {len(colunas_removidas)} colunas totalmente vazias:")
        # Ordena em ordem alfabética para facilitar a sua leitura no terminal
        for col in sorted(colunas_removidas):
            print(f"  - {col}")
    else:
        print("✅ Nenhuma coluna 100% nula foi encontrada.")
        
    return df_limpo
import pandas as pd


def gerar_resumo_colunas(df):
    """
    Analisa um DataFrame e retorna uma tabela com o resumo estrutural 
    detalhado de todas as colunas (tipo de dado, preenchidos e faltantes).
    """
    import pandas as pd
    
    resumo_colunas = pd.DataFrame({
        'Tipo de Dado': df.dtypes,
        'Valores Preenchidos': df.notnull().sum(),
        'Valores Faltantes (NaN)': df.isnull().sum()
    })
    
    return resumo_colunas

# Constante global definida a nível de módulo (boa prática)
COLS_POTENCIA = [
    'active_power.phase.a', 
    'active_power.phase.b', 
    'active_power.phase.c', 
    'active_power.total'
]

def calcular_potencia_ativa_total(df):
    """
    Calcula a Potência Ativa Total de um sistema trifásico somando as fases A, B e C.
    Cria uma nova coluna baseada na constante COLS_POTENCIA.
    """
    # Pega apenas as 3 primeiras posições da lista para somar as fases
    colunas_fases = COLS_POTENCIA[:3]
    nome_coluna_total = COLS_POTENCIA[3]
    
    # Verifica se as 3 colunas existem no DataFrame
    colunas_presentes = [col for col in colunas_fases if col in df.columns]
    
    if len(colunas_presentes) == 3:
        # Soma as fases e guarda na coluna total
        df[nome_coluna_total] = df[colunas_fases].sum(axis=1, min_count=1)
        print(f"⚡ Coluna '{nome_coluna_total}' calculada e adicionada com sucesso!")
    else:
        colunas_faltantes = set(colunas_fases) - set(colunas_presentes)
        print(f"❌ Erro: Faltam colunas para o cálculo trifásico. Não encontradas: {colunas_faltantes}")
        
    return df

def calcular_estatisticas_globais(df, coluna, percentis_extras=[0.95, 0.98, 0.99, 0.999]):
    """
    Calcula as estatísticas descritivas globais (Mínimo, Máximo, Média, Quartis)
    e percentis customizados para uma coluna específica do DataFrame.
    """
    import pandas as pd
    
    if coluna not in df.columns:
        print(f"❌ Erro: A coluna '{coluna}' não existe no DataFrame.")
        return None
        
    # Remove os valores nulos (NaN) temporariamente apenas para o cálculo matemático
    serie = df[coluna].dropna()
    
    if serie.empty:
        print(f"❌ Erro: A coluna '{coluna}' está completamente vazia.")
        return None

    # Dicionário base com as métricas que você solicitou
    estatisticas = {
        'Mínimo (Min)': serie.min(),
        'Máximo (Max)': serie.max(),
        'Média (Mean)': serie.mean(),
        'Q1 (25%)': serie.quantile(0.25),
        'Q2 / Mediana (50%)': serie.median(),
        'Q3 (75%)': serie.quantile(0.75)
    }
    
    # Adiciona os percentis extremos dinamicamente
    for p in percentis_extras:
        nome_percentil = f"Percentil {p*100}%"
        estatisticas[nome_percentil] = serie.quantile(p)
        
    # Converte o dicionário numa tabela vertical (Series) para ficar bonito no Notebook
    tabela_estatisticas = pd.Series(estatisticas, name=f"Estatísticas Globais: {coluna}")
    
    print(f"📊 Estatísticas processadas para a coluna: '{coluna}'")
    return tabela_estatisticas