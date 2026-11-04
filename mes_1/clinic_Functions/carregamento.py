import pandas as pd
import glob
import os

def juntar_csvs_diretorio(caminho_pasta):
    """
    Lê todos os arquivos CSV em uma pasta e os junta em um único DataFrame.
    """
    # Cria o padrão de busca para encontrar qualquer arquivo .csv na pasta especificada
    padrao_busca = os.path.join(caminho_pasta, "*.csv")
    arquivos_csv = glob.glob(padrao_busca)
    
    if not arquivos_csv:
        raise ValueError(f"Nenhum arquivo CSV foi encontrado na pasta: {caminho_pasta}")
        
    lista_dfs = []
    
    # Itera sobre a lista de arquivos, lê cada um e adiciona à lista
    for arquivo in arquivos_csv:
        df_temp = pd.read_csv(arquivo)
        lista_dfs.append(df_temp)
        
    # Concatena todos os DataFrames empilhando as linhas (já que as colunas são iguais)
    df_completo = pd.concat(lista_dfs, ignore_index=True)
    
    return df_completo