import os
from cabecalho import *
from operacoes import *

def converteBytes(tamanho):
    """
    Converte um tamanho informado pelo usuário, 
    para seu valor correspondente em bytes.
    """
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
    """
    Cria e inicializa o arquivo que representa o sistema de arquivos,
    gravando o cabeçalho e reservando o espaço solicitado.
    """
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
        return False

def main():
    """
    Inicializa o FURGfs4, carrega ou cria o sistema de arquivos e
    executa o terminal interativo com os comandos disponíveis.
    """

    print("======== FURGfs4 ========")

    if not os.path.exists("furgfs4.fs"):
        tamanho = input("Informe o tamanho do sistema de arquivos (ex: '800 MB'): ")
        tamanhoBytes = converteBytes(tamanho)

        if not tamanhoBytes:
            return

        if not criar_fs(tamanhoBytes):
            return

        cabecalho = Cabecalho(tamanhoBytes)

    else:
        print("Sistema de arquivos furgfs4.fs encontrado")
        with open("furgfs4.fs", "rb") as f:
            dados = f.read(48)

        cabecalho = Cabecalho.desserializar(dados)
    operacoes = Operacoes("furgfs4.fs", cabecalho)

    while True:
        try:
            entrada = input("\nfurgfs4> ")
            if not entrada.strip():
                continue

            comando = entrada.strip().split(" ")

            # comando cp
            if comando[0] == "cp":
                if len(comando) != 3:
                    print("Uso: cp <origem> <destino>")
                    continue
                caminho_origem = comando[1]
                caminho_final = comando[2]
                operacoes.cp(caminho_origem, caminho_final)

            # comando cpout
            elif comando[0] == "cpout":
                if len(comando) != 3:
                    print("Uso: cpout <origem> <destino>")
                    continue
                operacoes.cpout(comando[1], comando[2])

            # comando ls
            elif comando[0] == "ls":
                if len(comando) > 1:
                    caminho = comando[1]
                    operacoes.ls(caminho)
                else:
                    operacoes.ls()

            # debug
            elif comando[0] == "debug":
                if len(comando) != 2:
                    print("Uso: debug <caminho>")
                    continue

                nome_arquivo = comando[1]
                operacoes.debug(nome_arquivo)

            # comando mkdir
            elif comando[0] == "mkdir":
                if len(comando) != 2:
                    print("Uso: mkdir <nome>")
                    continue

                nome_arquivo = comando[1]
                operacoes.mkdir(nome_arquivo)

            # comando mv
            elif comando[0] == "mv":
                if len(comando) != 3:
                    print("Uso: mv <origem> <destino>")
                    continue

                operacoes.mv(comando[1], comando[2])

            # comando rm
            elif comando[0] == "rm":
                if len(comando) != 2:
                    print("Uso: rm <caminho>")
                    continue

                operacoes.rm(comando[1])

            # comando df
            elif comando[0] == "df":
                operacoes.df()

            # comando protect
            elif comando[0] == "protect":
                if len(comando) != 2:
                    print("Uso: protect <caminho>")
                    continue

                operacoes.protect(comando[1])

            # comando extra hash
            elif comando[0] == "sha256":
                if len(comando) != 2:
                    print("Uso: sha256 <caminho>")
                    continue

                operacoes.sha256(comando[1])

            # comando extra busca
            elif comando[0] == "find":
                if len(comando) != 2:
                    print("Uso: find <nome>")
                    continue

                operacoes.find(comando[1])

            # sair do fugrfs4
            elif comando[0] == "exit" or comando[0] == "sair":
                print("Saindo do FURGfs4...")
                break

            else:
                print(f"Comando '{comando[0]}' não reconhecido.")

        except KeyboardInterrupt: # se apertar ctrl + c
            print("\nSaindo do FURGfs4...")
            break

if __name__ == "__main__": 
    main()