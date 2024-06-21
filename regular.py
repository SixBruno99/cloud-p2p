import xmlrpc.client
import xmlrpc.server
import xmlrpc
import logging
import os
import base64
import threading
import hashlib
from pathlib import Path

# Constantes globais de  conexão
PORTA_BORDA = "8000"
PORTA = 9000
ENDERECO_COMPLETO = f"http://192.168.100.5:{PORTA}"

logging.basicConfig(level=logging.INFO)

# Servidor do próprio nó
server_regular = xmlrpc.server.SimpleXMLRPCServer(('0.0.0.0', PORTA), allow_none=True, logRequests=False)

# Conexão com o nó borda
server = xmlrpc.client.ServerProxy(f"http://3.80.212.41")

# Função que realiza o checksum do arquivo
def checksum(nome_arquivo):
    with open(nome_arquivo, 'rb') as f:
        dados_do_arquivo = f.read()
        md5 = hashlib.md5()
        md5.update(dados_do_arquivo)
        return md5.hexdigest()

# Função para enviar o arquivo selecionado pelo usuário
def upload_arquivo(nome_arquivo, endereco_noh_receptor):
    path_arquivo = f"{Path.cwd()}/{nome_arquivo}" # Cria o endereço completo do arquivo
    with open(path_arquivo, "rb") as f: # Realiza a leitura do arquivo
        dados_arquivo = f.read()
    file_name = os.path.basename(path_arquivo) # Retorna o nome base do caminho path
    conexao_noh_receptor = xmlrpc.client.ServerProxy(endereco_noh_receptor) # Realiza a conexão com o nó regular que solicitou o arquivo
    result = conexao_noh_receptor.recebe_arquivo(file_name, base64.b64encode(dados_arquivo).decode("utf-8")) # Envia o arquivo para o nó regular solicitante
    print(result)

# Função para a escrita do arquivo no nó regular solicitante
def recebe_arquivo(nome_arquivo, dados_arquivo):
    with open(nome_arquivo, "wb") as f:
        f.write(base64.b64decode(dados_arquivo))
    return f"Sucesso! Foi feito o upload do arquivo: {nome_arquivo}."

# Função responsável por enviar os arquivos presentes no diretório para o nó borda
def retorna_arquivos(lista):
    print(lista)
    lista_de_arquivos = lista
    for arquivo in os.listdir("/files"):
        print(arquivo)
        if(arquivo == ".idea"):
            continue
        arquivo_na_pasta = [arquivo, ENDERECO_COMPLETO, checksum(arquivo)] # Formatamos o arquivo para ser adicionado na lista: [nome do arquivo, endereço do nó que possue o arquivo, checksum do arquivo]
        if (arquivo_na_pasta not in lista_de_arquivos):  # Evita redundância na lista de arquivos
            lista_de_arquivos.append(arquivo_na_pasta)
    return lista_de_arquivos # Retorna a lista de arquivos

# Registra as funções no servidor do nó regular
server_regular.register_function(retorna_arquivos, "retorna_arquivos")
server_regular.register_function(upload_arquivo, "upload_arquivo")
server_regular.register_function(recebe_arquivo, "recebe_arquivo")


# Inicializa o servidor
def inicializa_servidor():
    logging.info(f" Nó regular inicialiado na porta {server_regular.server_address[1]}...")
    server.envia_endereco(ENDERECO_COMPLETO)
    server_regular.serve_forever()


# Cliente escolhe o que fazer
def escolher():
    while True:
        print("\n[0] - Solicitar arquivo\n[-1] - Sair da aplicação\n")
        escolha = input()
        if (escolha == "0"):
            nome_arquivo_escolhido = input("Digite o nome do arquivo: ") # Guardamos o arquivo que o usuário selecionou
            lista = server.envia_localizacao_arquivo(nome_arquivo_escolhido) # Solicita ao nó borda os endereços dos nós regulares que possuem o arquivo
            if len(lista) == 0:
                print("Arquivo não encontrado.") # Caso não exista esse arquivo na listagem do nó borda, informa-se essa mensagem ao usuário
            else:
                print("Nós com o arquivo:\n")
                for endereco in lista: # Mostramos os nós que possuem o arquivo
                    print(f"-> {endereco}")
                conexao_regular = xmlrpc.client.ServerProxy(lista[0]) # Conexão com o nó regular que possue o arquivo selecionado
                conexao_regular.upload_arquivo(nome_arquivo_escolhido, ENDERECO_COMPLETO)  # Solicita ao nó regular o arquivo

        elif escolha == "-1":
            break

# Separamos uma thread para cuidar da inicialização do servidor do nó regular
server_thread = threading.Thread(target=inicializa_servidor)
server_thread.start()

# Separamos uma thread para cuidar da interação com o usuário
escolha_thread = threading.Thread(target=escolher)
escolha_thread.start()
