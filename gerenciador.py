import struct
from arquivo import *

class Gerenciador:

    def __init__(self, fs: str = "furgfs4.fs"):
        self.fs = fs
        self.tabelaFAT = []
        self.tamanho_bloco = 4096
        '''self.inicio_dados = -1
        self.inicio_fat = -1
        self.fim = -1'''

        self.retornaFAT()

    def retornaFAT(self):
        with open(self.fs, "rb") as f:

            # desserialização do cabeçalho
            cabecalho = f.read(48)
            _, self.tamanho_bloco, _, self.inicio_fat, inicio_diretorio_raiz, self.inicio_dados = struct.unpack('q q q q q q', cabecalho)

            # manda cursor pro início da fat, que ainda esta serialziada
            f.seek(self.inicio_fat)

            tam_fat_bytes = inicio_diretorio_raiz - self.inicio_fat
            conteudo_fat_bytes = f.read(tam_fat_bytes) # o cursor pega o conteúdo do início da fat até o final dela

            num_entradas_fat = tam_fat_bytes // 4 # 4 bytes por entrada # 4096 entradas

            self.tabelaFAT = list(struct.unpack(f"{num_entradas_fat}i", conteudo_fat_bytes))

    # retorna o índice do primeiro bloco vazio que encontrar
    def encontra_bloco_livre(self):
            for i, valor in enumerate(self.tabelaFAT):
                 if valor == -1:
                      return i
            raise Exception("Erro! Disco cheio. Não existem blocos livres.")

    def alocar_espaco(self, conteudo_bytes): # tudo que tem no arquivo, em bytes

            blocos_alocados = []

            # ver o tamanho do arquivo -> cabe em um bloco? se sim: aloca no primeiro livre
            # se não, faz um loop pra alocar

            quantidade_bytes_arquivo = len(conteudo_bytes) # quantos bytes tem o arquivo

            #utiliza o -1 pra divisão inteira não dar erro por conta dos quebrados
            blocos_necessarios = quantidade_bytes_arquivo + (self.tamanho_bloco -1) // self.tamanho_bloco

            if blocos_necessarios == 0:
                return 0

            for i in range (blocos_necessarios):
                livre = self.encontra_bloco_livre()
                self.tabelaFAT[livre] = 0 # preenche com 0 temporariamente
                blocos_alocados.append(livre)

            # pega os valores dos blocos que foram alocados e coloca nas variaveis atual e proximo
            # adiciona no indice da fat do bloco atual, o número do proximo bloco
            for i in range (len(blocos_alocados) -1):
                atual = blocos_alocados[i]
                proximo = blocos_alocados[i+1]
                self.tabelaFAT[atual] = proximo


            self.tabelaFAT[blocos_alocados[-1]] = -1

            self.escrever_nos_blocos(blocos_alocados, conteudo_bytes)
            self.atualiza_FAT_no_disco()

            # retorna o primeiro bloco alocado, pra ser salvo no indiceFAT do arquivo
            return blocos_alocados[0]


    def escrever_nos_blocos(self, blocos_alocados, conteudo_bytes):
        with open(self.fs, "r+b") as f:
            for i, bloco in enumerate(blocos_alocados):

                posicao_fisica = self.inicio_dados + (bloco * self.tamanho_bloco)
                f.seek(posicao_fisica)

                inicio = i * self.tamanho_bloco
                fim = inicio + self.tamanho_bloco
                bloco_dados = conteudo_bytes[inicio:fim] # pega a fatia certa de bytes pro tamanho do bloco

                # preenche com zeros se sobrar espaço
                if len(bloco_dados) < self.tamanho_bloco:
                     bloco_dados += b'\x00' * (self.tamanho_bloco - len(bloco_dados))

            
                f.write(bloco_dados)

    def atualiza_FAT_no_disco(self):
            with open(self.fs, "r+b") as f:
                f.seek(self.inicio_fat)
                fat = struct.pack(f"{len(self.tabelaFAT)}i", *self.tabelaFAT)
                f.write(fat)

    def retorna_tamanho_ocupado(self, indiceFAT):
        if indiceFAT == -1:
             return 0
        i = 0
        atual = indiceFAT
        while atual != -1:
            atual =  self.tabelaFAT[atual]
            i += 1

        return (i*self.tamanho_bloco)


# COMANDOS DO TERMINAL:

    def executar_ls(self):

        bytes_por_arquivo = 64
        numero_arquivos = 128
        AZUL = "\033[94m"
        RESET = "\033[0m"

        with open(self.fs, "rb") as f:
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            f.seek(inicio_diretorio_raiz) # manda o cursor pro inicio do diretório raiz

            print(f"{'NOME':<35}  {'TAMANHO OCUPADO NO SISTEMA':<15}  {'TAMANHO REAL'}")

            for _ in range(numero_arquivos):
                dados = f.read(bytes_por_arquivo)
                if not dados:
                    break

                # desserealiza utilizando o formato da classe Arquivo
                nome, tamanho_arquivo, indiceFAT, status, protecao, reservado = struct.unpack('32s q i b b 18s', dados)

                # limpa os bytes nulos extras
                nome_str = nome.decode('utf-8').rstrip('\x00')

                tamanho_ocupado_sistema = self.retorna_tamanho_ocupado(indiceFAT)

                if status == 1:
                    print(f"{nome_str}    {tamanho_ocupado_sistema}     {tamanho_arquivo}") #Mudar tamanho usado depois com a lógica da FAT
                elif status == 2:
                    print(f"{AZUL}{nome_str}    {tamanho_arquivo}     {tamanho_arquivo}{RESET}") # deixa o nome das pastas em azul

    def executar_cp(self, caminho, nome_destino):
        try:
            with open(caminho, "rb") as cont:
                conteudo = cont.read()
        except FileNotFoundError:
             print(f"Erro! Arquivo {caminho} não foi encontrado no seu PC.")
             return

        tamanho_real = len(conteudo)

        # retorna o primeiro bloco alocado na FAT para o arquivo
        primeiro_bloco_alocado = self.alocar_espaco(conteudo)

        TAMANHO_ENTRADA = 64
        NUM_ENTRADAS = 128

        with open(self.fs, "rb") as f:
            f.seek(0)
            cabecalho = f.read(48)

            _, self.tamanho_bloco, _, _, inicio_diretorio_raiz, _= struct.unpack('q q q q q q', cabecalho)

            tamanho_diretorio_raiz = self.tamanho_bloco * 2

            f.seek(inicio_diretorio_raiz)
            posicao_livre = -1

            for i in range(NUM_ENTRADAS):
                posicao_atual = f.tell() # guarda o endereço do cursor

                dados = f.read(TAMANHO_ENTRADA)

                _, _, _, status, _, _ = struct.unpack('32 q i b b 18s', dados)

                if status == 0: # achou uma gaveta vazia
                    posicao_livre = posicao_atual
                    break

            if posicao_livre == -1:
                print("Erro! O diretório está cheio.")
                return

            novo_arquivo = Arquivo(nome_destino, tamanho_real, primeiro_bloco_alocado, status = 1, protecao = 0)
            f.write(novo_arquivo.serializar()) # grava os dados do arquivo no diretório raiz

            print(f"Sucesso! Arquivo {nome_destino} copiado para o FURGfs4.")
                     



             


             
             
             
               

        
        

                
                 


            

            
            









