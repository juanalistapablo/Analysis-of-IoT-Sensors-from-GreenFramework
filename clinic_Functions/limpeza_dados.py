import pandas as pd
import json

def expandir_coluna_json(df, coluna='dados'):
    """Converte a string JSON e achata em múltiplas colunas, mantendo as originais."""
    # 1. Remove linhas nulas e cria uma cópia segura
    df_clean = df.dropna(subset=[coluna]).copy()
    
    # 2. Função segura para converter string em dicionário
    def parse_json(x):
        try:
            return json.loads(x) if isinstance(x, str) else x
        except:
            return {}
            
    df_clean[coluna] = df_clean[coluna].apply(parse_json)
    df_clean = df_clean[df_clean[coluna].apply(lambda x: isinstance(x, dict))]
    
    # 3. Expande os dicionários em novas colunas
    df_expandido = pd.json_normalize(df_clean[coluna])
    
    # 4. Reseta os índices para garantir que a colagem (concat) alinhe perfeitamente
    df_clean.reset_index(drop=True, inplace=True)
    df_expandido.reset_index(drop=True, inplace=True)
    
    # 5. Cola as colunas originais (removendo a 'dados' bruta) com as novas colunas
    return pd.concat([df_clean.drop(columns=[coluna]), df_expandido], axis=1)

def configurar_indice_temporal(df):
    """Converte as colunas de data para o formato datetime correto."""
    if 'timestamp_leitura' in df.columns:
        df['timestamp_leitura'] = pd.to_datetime(df['timestamp_leitura'])
        df.set_index('timestamp_leitura', inplace=True)
        df.sort_index(inplace=True)
        
    if 'timestamp_leitura_anterior' in df.columns:
        df['timestamp_leitura_anterior'] = pd.to_datetime(df['timestamp_leitura_anterior'])
        
    return df

def pipeline_completo(df):
    """Executa a limpeza mantendo TODAS as colunas originais junto com as calculadas."""
    df = expandir_coluna_json(df)
    df = configurar_indice_temporal(df)
    return df