import os
import struct
import hashlib

from arquivo import Arquivo
from tabelaFAT import TabelaFAT
from diretorio import Diretorio

class Operacoes:
    """
    Implementa as operações disponibilizadas pelo terminal do FURGfs4,
    utilizando o diretório e a tabela FAT para manipular arquivos e diretórios.
    """

    def __init__(self, fs, cabecalho):

        self.fs = fs
        self.cabecalho = cabecalho
        self.fat = TabelaFAT(fs)
        self.diretorio = Diretorio(fs, cabecalho, self.fat)

    # ls
    def ls(self, arquivo=None): 

        bytes_por_arquivo = 64
        AZUL = "\033[94m"
        RESET = "\033[0m"

        try:
            indice_bloco_dir = self.diretorio.resolver_caminho(arquivo)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "rb") as f:
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            if indice_bloco_dir is None:
                inicio_atual = inicio_diretorio_raiz

                # o diretório raiz ocupa dois blocos
                numero_arquivos = (self.cabecalho.tamanho_bloco * 2) // bytes_por_arquivo

            else:
                # se passou um subdiretório, lê a partir dos blocos de dados dele via FAT
                numero_arquivos = self.cabecalho.tamanho_bloco // bytes_por_arquivo
                inicio_atual = self.cabecalho.inicio_dados + (indice_bloco_dir * self.cabecalho.tamanho_bloco)

            f.seek(inicio_atual) # manda o cursor pro inicio do diretório raiz ou início do bloco de subdiretório

            print(f"{'NOME':<35}  {'TAMANHO OCUPADO NO SISTEMA':<32}  {'TAMANHO REAL'}")

            for _ in range(numero_arquivos):
                dados = f.read(bytes_por_arquivo)
                if not dados:
                    break

                # desserealiza utilizando o formato da classe Arquivo
                nome, tamanho_arquivo, indiceFAT, status, protecao, reservado = struct.unpack('32s q i b b 18s', dados)

                # limpa os bytes nulos extras
                nome_str = nome.decode('utf-8').rstrip('\x00')

                if status == 1 or status == 2:
                    tamanho_ocupado_sistema = self.fat.retorna_tamanho_ocupado(indiceFAT)

                    ocupado_str = f"{tamanho_ocupado_sistema} bytes"
                    real_str = f"{tamanho_arquivo} bytes"

                    if status == 1:
                        print(f"{nome_str:<35}  {ocupado_str:<32}  {real_str}")

                    elif status == 2:
                        print(f"{AZUL}{nome_str:<35}  {ocupado_str:<32}  {real_str}{RESET}") # deixa o nome das pastas em azul

    # cp
    def cp(self, caminho, destino_completo="/"): 

        if "/" in destino_completo:
            # rsplit pega da direita (final) pra esquerda e executa só uma vez
            # pega o último nome do caminho
            partes = destino_completo.rsplit("/", 1)
            caminho_destino = partes[0] if partes[0] != "" else "/"
            nome_destino = partes[1]
        else:
            caminho_destino = "/"
            nome_destino = destino_completo

        try:
            with open(caminho, "rb") as cont:
                conteudo = cont.read()
        except FileNotFoundError:
             print(f"Erro! Arquivo {caminho} não foi encontrado no seu PC.")
             return

        tamanho_real = len(conteudo)

        # retorna o primeiro bloco alocado na FAT para o arquivo
        primeiro_bloco_alocado = self.fat.alocar_espaco(conteudo)

        TAMANHO_ENTRADA = 64
        NUM_ENTRADAS = 128

        try:
            indice_dir = self.diretorio.resolver_caminho(caminho_destino)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "r+b") as f:
            f.seek(0)
            cabecalho = f.read(48)

            _, self.cabecalho.tamanho_bloco, _, _, inicio_diretorio_raiz, _= struct.unpack('q q q q q q', cabecalho)

            # define onde o cursor vai começar a procurar gaveta vazia
            if indice_dir is None:
                inicio_atual = inicio_diretorio_raiz
                NUM_ENTRADAS = (self.cabecalho.tamanho_bloco * 2) // TAMANHO_ENTRADA
            else:
                inicio_atual = self.cabecalho.inicio_dados + (indice_dir * self.cabecalho.tamanho_bloco)
                NUM_ENTRADAS = self.cabecalho.tamanho_bloco // TAMANHO_ENTRADA

            f.seek(inicio_atual)
            posicao_livre = -1

            # procura a gaveta vazia no diretório alvo
            for _ in range(NUM_ENTRADAS):
                posicao_atual = f.tell() # guarda o endereço do cursor

                dados = f.read(TAMANHO_ENTRADA)

                _, _, _, status, _, _ = struct.unpack('32s q i b b 18s', dados)

                if status == 0: # achou uma gaveta vazia
                    posicao_livre = posicao_atual
                    break

            if posicao_livre == -1:
                print("Erro! O diretório está cheio.")
                return
            
            novo_arquivo = Arquivo(nome_destino, tamanho_real, primeiro_bloco_alocado, status = 1, protecao = 0)

            f.seek(posicao_livre)
            f.write(novo_arquivo.serializar()) # grava os dados do arquivo no diretório raiz

            print(f"Sucesso! Arquivo {nome_destino} copiado para o FURGfs4.")

    # debug
    def debug(self, nome_arquivo): 

        bytes_por_arquivo = 64
        numero_arquivos = 128
        arquivo_encontrado = False
        indice_fat_inicial = -1

        with open(self.fs, "rb") as f:
            cabecalho = f.read(48)

            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            f.seek(inicio_diretorio_raiz)

            for i in range(numero_arquivos):

                arquivo = f.read(bytes_por_arquivo)

                nome, _, indiceFAT, _, _, _ = struct.unpack('32s q i b b 18s', arquivo)

                nome = nome.decode('utf-8').rstrip('\x00')

                if nome == nome_arquivo:
                    arquivo_encontrado = True
                    indice_fat_inicial = indiceFAT
                    break

            if not arquivo_encontrado:
                print(f"Erro! Arquivo {nome_arquivo} não encontrado.")
                return

            cadeia = []
            atual = indice_fat_inicial

            while atual != -1:
                cadeia.append(str(atual))
                atual = self.fat.tabelaFAT[atual] # pega o valor que ta no índice, que é o número do próximo bloco e índice da FAT

            print(f"Cadeia de blocos do arquivo {nome_arquivo}:")
            print(cadeia)

    # mkdir
    def mkdir(self, caminho_completo): 

        if "/" in caminho_completo:
            partes = caminho_completo.rsplit("/", 1)
            caminho_destino = partes[0] if partes[0] != "" else "/"
            nome_pasta = partes[1]
        else:
            caminho_destino = "/"
            nome_pasta = caminho_completo

        # cria um bloco de dados vazio (4096 bytes de \x00) para a nova pasta
        conteudo_vazio = b'\x00' * self.cabecalho.tamanho_bloco
        
        # aloca espaço na FAT para essa pasta e escreve o bloco vazio no disco
        primeiro_bloco = self.fat.alocar_espaco(conteudo_vazio)
        
        # procura uma vaga livre no Diretório Raiz (ou diretório atual) para registrar a pasta
        TAMANHO_ENTRADA = 64
        NUM_ENTRADAS = 128

        try:
            indice_dir = self.diretorio.resolver_caminho(caminho_destino)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "r+b") as f:
            f.seek(0)
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            if indice_dir is None:
                inicio_atual = inicio_diretorio_raiz
                NUM_ENTRADAS = (self.cabecalho.tamanho_bloco * 2) // TAMANHO_ENTRADA
            else:
                inicio_atual = self.cabecalho.inicio_dados + (indice_dir * self.cabecalho.tamanho_bloco)
                NUM_ENTRADAS = self.cabecalho.tamanho_bloco // TAMANHO_ENTRADA

            f.seek(inicio_atual)
            posicao_livre = -1

            for _ in range(NUM_ENTRADAS):
                posicao_atual = f.tell()
                dados = f.read(TAMANHO_ENTRADA)
                _, _, _, status, _, _ = struct.unpack('32s q i b b 18s', dados)

                if status == 0:  # Gaveta vazia
                    posicao_livre = posicao_atual
                    break

            if posicao_livre == -1:
                print("Erro! Diretório raiz cheio.")
                return

            # cria o objeto Arquivo com status = 2 (Diretório)
            nova_pasta = Arquivo(nome_pasta, tamanhoArquivo=0, indiceFAT=primeiro_bloco, status=2, protecao=0)
            
            f.seek(posicao_livre)
            f.write(nova_pasta.serializar())
            print(f"Sucesso! Diretório {nome_pasta} criado.")

    # cp furgfs4 -> computador
    def cpout(self, origem, destino):

        resultado = (self.diretorio.resolver_caminho_info(origem))
        if resultado is None:
            print("Erro: arquivo não encontrado.")
            return

        arquivo = resultado["arquivo"]
        if arquivo.status != 1:
            print("Erro: o caminho não corresponde a um arquivo.")
            return

        try:
            blocos = self.fat.obter_blocos(arquivo.indiceFAT)
            restante = arquivo.tamanhoArquivo

            with open(destino, "wb") as saida:
                with open(self.fs, "rb") as fs:

                    for bloco in blocos:
                        if restante <= 0:
                            break

                        posicao = (self.fat.inicio_dados + bloco * self.fat.tamanho_bloco)
                        fs.seek(posicao)

                        quantidade = min(self.fat.tamanho_bloco, restante)
                        dados = fs.read( quantidade )

                        saida.write(dados)
                        restante -= len(dados)

            print(f"Arquivo copiado para {destino}'.")
        except Exception as erro:
            print(f"Erro ao copiar arquivo: {erro}")

    # mv
    def mv(self, origem, destino):

        origem_info = (self.diretorio.resolver_caminho_info(origem))
        if origem_info is None:
            print("Erro: origem não encontrada.")
            return

        arquivo = origem_info["arquivo"]
        if arquivo.protecao == 1:
            print("Erro: arquivo protegido.")
            return

        nome_destino = os.path.basename( destino.rstrip("/"))
        caminho_pai = os.path.dirname(destino.rstrip("/"))

        if caminho_pai == "":
            destino_pai = None

        else:
            pai_info = (self.diretorio.resolver_caminho_info(caminho_pai))
            if pai_info is None:
                print("Erro: diretório de destino existe.")
                return

            if pai_info["arquivo"].status != 2:
                print("Erro: destino não é diretório.")
                return
            destino_pai = (pai_info["arquivo"].indiceFAT)

        if destino_pai is None:
            existe = (self.diretorio.buscar_no_raiz_por_nome_info(nome_destino))

        else:
            existe = (self.diretorio.buscar_no_diretorio_info(destino_pai, nome_destino))

        if existe is not None:
            print("Erro: já existe uma entrada com esse nome.")
            return

        if destino_pai is None:
            nova_posicao = (self.diretorio.encontrar_entrada_livre_raiz())

        else:
            nova_posicao = (self.diretorio.encontrar_entrada_livre(destino_pai))

        if nova_posicao is None:
            print("Erro: diretório de destino está cheio.")
            return

        arquivo.nome = (nome_destino.encode("utf-8")[:32].ljust(32, b'\x00'))

        self.diretorio.escrever_entrada(nova_posicao, arquivo)
        self.diretorio.remover_entrada(origem_info["posicao"])

        print(f"'{origem}' movido para '{destino}'")

    # rm
    def rm(self, caminho):

        resultado = (self.diretorio.resolver_caminho_info(caminho))
        if resultado is None:
            print("Erro: arquivo não encontrado.")
            return

        arquivo = resultado["arquivo"]
        if arquivo.status != 1:
            print("Erro: atualmente rm remove apenas arquivos.")
            return

        if arquivo.protecao == 1:
            print("Erro: arquivo protegido contra remoção.")
            return

        self.fat.liberar_blocos(arquivo.indiceFAT)
        self.diretorio.remover_entrada(resultado["posicao"])

        print(f"'{caminho}' removido")

    # df
    def df(self):

        total = (self.fat.quantidade_blocos_totais())
        livres = (self.fat.quantidade_blocos_livres())

        usados = total - livres
        total_bytes = (total * self.fat.tamanho_bloco)

        livres_bytes = (livres * self.fat.tamanho_bloco)
        usados_bytes = (usados * self.fat.tamanho_bloco)

        print(f"Total: {total_bytes} bytes")
        print(f"Usado: {usados_bytes} bytes")
        print(f"Livre: {livres_bytes} bytes")

    # protec
    def protect(self, caminho):

        resultado = (self.diretorio.resolver_caminho_info(caminho))

        if resultado is None:
            print("Erro: arquivo não encontrado.")
            return

        arquivo = resultado["arquivo"]
        if arquivo.protecao == 0:
            arquivo.protecao = 1
            print(f"'{caminho}' protegido")

        else:
            arquivo.protecao = 0
            print(f"'{caminho}' desprotegido")

        self.diretorio.atualizar_entrada(resultado["posicao"],arquivo)

    # sha-256
    def sha256(self, caminho):

        resultado = (self.diretorio.resolver_caminho_info(caminho))
        if resultado is None:
            print("Erro: arquivo não encontrado")
            return

        arquivo = resultado["arquivo"]
        if arquivo.status != 1:
            print("Erro: o caminho não é um arquivo.")
            return

        sha256 = hashlib.sha256()
        blocos = self.fat.obter_blocos(arquivo.indiceFAT)
        restante = arquivo.tamanhoArquivo

        with open(self.fs, "rb") as f:

            for bloco in blocos:
                if restante <= 0:
                    break

                posicao = (self.fat.inicio_dados + bloco * self.fat.tamanho_bloco)
                f.seek(posicao)

                quantidade = min(self.fat.tamanho_bloco, restante)
                dados = f.read(quantidade)

                sha256.update(dados)
                restante -= len(dados)

        print(sha256.hexdigest())

    # find
    def find(self, nome):

        encontrados = []
        self._buscar_recursivamente(None, "", nome, encontrados)

        if not encontrados:
            print(f"'{nome}' não encontrado.")

        else:
            for caminho in encontrados:
                print(caminho)

    # busca recursiva
    def _buscar_recursivamente(self, indiceFAT, caminho_atual, nome, encontrados):

        if indiceFAT is None:
            entradas = (self.diretorio.obter_entradas_raiz())

        else:
            entradas = (self.diretorio.obter_entradas(indiceFAT))

        for arquivo in entradas:
            nome_arquivo = arquivo.nome_string()

            if caminho_atual == "":
                caminho = "/" + nome_arquivo

            else:
                caminho = (caminho_atual + "/" + nome_arquivo)

            if nome_arquivo == nome:
                encontrados.append(caminho)

            if arquivo.status == 2:
                self._buscar_recursivamente(arquivo.indiceFAT, caminho, nome, encontrados)