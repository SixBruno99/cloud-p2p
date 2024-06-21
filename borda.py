import xmlrpc
import logging
import xmlrpc.server
import xmlrpc.client
import base64
import os
import schedule
import time
import threading

logging.basicConfig(level=logging.INFO)

# Litas de clientes para conexão e lista de arquivos para aramazenar os aruivos dos nós regulares
lista_de_clientes = []
lista_de_arquivos = []

# Servidor do próprio nó
server_borda = xmlrpc.server.SimpleXMLRPCServer(('0.0.0.0', 8000), allow_none=True)

# Função para enviar o nó que possue o arquivo escolhido pelo usuário
def envia_localizacao_arquivo(nome_arquivo):
    lista_de_nos = [] # Lista que armazenará os nós que possuam o arquivo
    for arquivo in lista_de_arquivos:
        if arquivo[0] == nome_arquivo:
            lista_de_nos.append(f"{arquivo[1]}")
    return lista_de_nos # Retorna a lista de nós que possuam o arquivo

# Função periódica de listagem de arquivos dos nós conectados
def listar_arquivos():
    global lista_de_arquivos
    global lista_de_clientes
    lista_temporaria_arquivos = [] # Lista temporária para armazenar os arquivos durante o loop nos nós regulares
    lista_temporaria_clientes = lista_de_clientes # Lista temporária de clientes para rodar durante o loop

    print("Processando listagem periódica de arquivos...\n\n")
    for cliente in lista_temporaria_clientes:
        try:
            server = xmlrpc.client.ServerProxy(cliente)  # Conexão com o nó regular para oter os arquivos dele
            resposta = server.retorna_arquivos(lista_temporaria_arquivos) # Solicita ao nó regular os arquivos presentes na pasta dele
            lista_temporaria_arquivos.extend(resposta) # Adiciona à lista de arquivos temporária os arquivos retornados do nó regular
        except (ConnectionRefusedError, TimeoutError):
            print(f"Erro de conexão com {cliente}\n\n")
            lista_de_clientes.remove(cliente)

    print("Listagem periódica de arquivos: ")
    # Filtra a lista para retirar valores repetidos
    lista_de_arquivos_tuples = [tuple(sublist) for sublist in lista_temporaria_arquivos]
    unique_data_tuples = list(set(lista_de_arquivos_tuples))
    unique_data = [list(sublist) for sublist in unique_data_tuples]

    lista_de_arquivos = unique_data
    print("Arquivo\t\tEndereco\tChecksum")
    for arquivo in lista_de_arquivos:
        print(f"{arquivo[0]}\t{arquivo[1]}\t{arquivo[2]}")


def envia_endereco(endereco):
    print(endereco)
    return lista_de_clientes.append(endereco)

# Registra as duas funções do servidor borda
server_borda.register_function(listar_arquivos, "listar_arquivos")
server_borda.register_function(envia_localizacao_arquivo, "envia_localizacao_arquivo")
server_borda.register_function(envia_endereco, "envia_endereco")

# A biblioteca schedule irá realizar a função "listar_arquivos()" periodicamente a cada 5 segundos
schedule.every(5).seconds.do(listar_arquivos)

# Função responsável por deixar o servidor rodando
def inicializa_servidor():
    logging.info(f" Nó borda inicialiado na porta {server_borda.server_address[1]}...")
    server_borda.serve_forever()

# Separamos uma thread para ficar responsável pelo servidor
server_thread = threading.Thread(target=inicializa_servidor)
server_thread.start()

while True:
    schedule.run_pending()
    time.sleep(1)  # Adding a sleep to prevent busy waiting
