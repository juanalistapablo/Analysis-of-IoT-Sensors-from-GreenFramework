import os

def exportar_dados_separados(dicionario_tabelas, caminho_pasta):
    """
    Recebe as tabelas geradas pelo filtro dinâmico e salva cada uma 
    como um arquivo CSV separado na pasta de destino.
    """
    # Cria a pasta caso não exista
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
        print(f"Pasta de destino criada: {caminho_pasta}\n")
    else:
        print(f"Salvando na pasta existente: {caminho_pasta}\n")
        
    # Salva cada tabela automaticamente usando o nome do próprio elemento único
    for nome_elemento, df in dicionario_tabelas.items():
        # Converte para string e troca espaços por underlines (ex: 'Medidor CCET' -> 'Medidor_CCET.csv')
        nome_arquivo = str(nome_elemento).replace(" ", "_") + ".csv"
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
        
        # Salva o arquivo sem a coluna de índice do Pandas
        df.to_csv(caminho_completo, index=False)
        print(f"✅ Arquivo gerado: {nome_arquivo} ({len(df)} linhas salvas)")