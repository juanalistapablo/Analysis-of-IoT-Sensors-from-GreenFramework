import os

def criar_pasta(caminho_pasta):
    """Verifica se a pasta existe e cria caso não exista."""
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
        print(f"Pasta criada: {caminho_pasta}")
    else:
        print(f"A pasta já existe: {caminho_pasta}")

def salvar_tabelas_csv(dicionario_tabelas, caminho_pasta):
    """
    Recebe o dicionário de prédios, cria a pasta de destino e salva cada 
    DataFrame como um arquivo CSV separado.
    """
    criar_pasta(caminho_pasta)
    
    for nome_predio, df in dicionario_tabelas.items():
        # Substitui espaços por underlines para evitar problemas com nomes de arquivos
        nome_arquivo = nome_predio.replace(" ", "_") + ".csv"
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
        
        # Salva o arquivo sem a coluna de índice numérico padrão do pandas
        df.to_csv(caminho_completo, index=False)
        print(f"Arquivo salvo com sucesso: {caminho_completo}")