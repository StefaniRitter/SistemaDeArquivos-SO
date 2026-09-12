from cabecalho import *
from gerenciador import *

def converteBytes(tamanho):
    try:
        tamanho = tamanho.strip().upper().split(" ")
        valor = int(tamanho[0])
        unidade = tamanho[1] if len(tamanho) > 1 else "B"

        match unidade:
            case "B":
                return valor
            case "KB":
                return (valor * 1024)
            case "MB":
                return (valor * 1024 * 1024)
            case "GB":
                return (valor * 1024 * 1024 * 1024)
            case _:
                print("Tamanho não permitido.\n\nInforme um valor em B, KB, MB, ou GB.")
                return False
    except ValueError as e:
        print("Formato inválido. Use um espaço entre o número e a unidade (ex: '800 MB').")
        return False

# Cria arquivo furgfs4.fs com o tamanho em bytes informado pelo usuário
# Adiciona cabeçalho com dados definidos na implementação
# Preenche o restante do espaço com bytes null
def criar_fs(tamanho_bytes: int, nome: str = "furgfs4.fs"):
    if tamanho_bytes < (1024 * 1024): # se o tamanho em bytes for menor que 1MB
        print("Erro! Tamanho muito pequeno. Mínimo: 1 MB")
        return False

    cabecalho = Cabecalho(tamanho_sistema=tamanho_bytes)

    try:

        with open(nome, "wb") as f:
            # grava o cabeçalho serializado no início do arquivo
            f.write(cabecalho.serializar())

            # vai pro final do arquivo e preenche tudo com b'\x00'
            f.seek(tamanho_bytes - 1)
            f.write(b'\x00')

        print(f"Sucesso! Sistema de arquivos {nome} criado com {tamanho_bytes} bytes!")
        return True

    except OSError as e:
        print(f"Erro ao criar arquivo: {e}")

          
'''tamanho = input("Informe o tamanho do sistema de arquivos (ex: '800 MB'): ")
tamanhoBytes = converteBytes(tamanho)
if tamanhoBytes:
    criar_fs(tamanhoBytes)'''

gerenciador = Gerenciador(fs="furgfs4.fs")

# cp <origem>/arquivo <furgfs>/arquivo 

while True:
    try:
        entrada = input("furgfs4> ")
        if not entrada.strip():
            continue
            
        comando = entrada.strip().split(" ")

        if comando[0] == "cp":
            if len(comando) < 3:
                print("Uso correto: cp <origem> <destino>")
                continue
            caminho_origem = comando[1]
            caminho_final = comando[2]
            gerenciador.executar_cp(caminho_origem, caminho_final)

        elif comando[0] == "ls":
            if len(comando) > 1:
                caminho = comando[1]
                gerenciador.executar_ls(caminho)
            else:
                gerenciador.executar_ls()

        elif comando[0] == "debug":
                    nome_arquivo = comando[1]
                    gerenciador.executar_debug(nome_arquivo)

        elif comando[0] == "mkdir":
                    nome_arquivo = comando[1]
                    gerenciador.executar_mkdir(nome_arquivo)
            
        elif comando[0] == "exit" or comando[0] == "sair":
            print("Saindo do FURGfs4...")
            break
            
        else:
            print(f"Comando '{comando[0]}' não reconhecido.")
            
    except KeyboardInterrupt: # se apertas ctrl + c
        print("\nSaindo do FURGfs4...")
        break