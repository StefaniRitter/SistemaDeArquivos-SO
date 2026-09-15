import struct
import os

class TabelaFAT:
    """
    Gerencia a tabela FAT do FURGfs4, controlando a alocação,
    encadeamento, consulta e liberação dos blocos de dados.
    """

    def __init__(self, fs):
        self.fs = fs
        self.tamanho_bloco = 4096
        self.inicio_fat = 0
        self.inicio_diretorio_raiz = 0
        self.inicio_dados = 0
        self.tabelaFAT = []

        self.retornaFAT() 

    def retornaFAT(self):
        with open(self.fs, "rb") as f:

            # desserialização do cabeçalho
            cabecalho = f.read(48)
            _, self.tamanho_bloco, _, self.inicio_fat, self.inicio_diretorio_raiz, self.inicio_dados = struct.unpack('q q q q q q',cabecalho)

            # manda cursor pro início da fat, que ainda esta serialziada
            f.seek(self.inicio_fat)

            tam_fat_bytes = self.inicio_diretorio_raiz -self.inicio_fat
            conteudo_fat_bytes = f.read(tam_fat_bytes) # o cursor pega o conteúdo do início da fat até o final dela
            num_entradas_fat = tam_fat_bytes // 4 # 4 bytes por entrada # 4096 entradas

            self.tabelaFAT = list(struct.unpack(f"{num_entradas_fat}i", conteudo_fat_bytes))
            
    # retorna o índice do primeiro bloco vazio que encontrar
    def encontra_bloco_livre(self):
        for i, valor in enumerate(self.tabelaFAT):
            # Não podemos usar blocos que ultrapassem o tamanho real do arquivo
            posicao = (self.inicio_dados +i * self.tamanho_bloco)
            if posicao + self.tamanho_bloco > os.path.getsize(self.fs):
                continue

            if valor == 0:
                return i
        raise Exception("Erro! Disco cheio. Não existem blocos livres.")

    def alocar_espaco(self, conteudo_bytes): # tudo que tem no arquivo, em bytes
        blocos_alocados = []
        quantidade_bytes_arquivo = len(conteudo_bytes)    
            
        if quantidade_bytes_arquivo == 0:
            return -1

        #utiliza o -1 pra divisão inteira não dar erro por conta dos quebrados
        blocos_necessarios = (quantidade_bytes_arquivo + self.tamanho_bloco - 1) // self.tamanho_bloco

        if blocos_necessarios == 0:
            return 0

        for i in range(blocos_necessarios):
            livre = self.encontra_bloco_livre()
            self.tabelaFAT[livre] = -1 # preenche com -1 temporariamente pra não ficar como livre
            blocos_alocados.append(livre)

        # pega os valores dos blocos que foram alocados e coloca nas variaveis atual e proximo
        # adiciona no indice da fat do bloco atual, o número do proximo bloco
        for i in range(len(blocos_alocados) - 1):
            atual = blocos_alocados[i]
            proximo = blocos_alocados[i + 1]
            self.tabelaFAT[atual] = proximo

        self.tabelaFAT[blocos_alocados[-1]] = -1

        self.escrever_nos_blocos(blocos_alocados, conteudo_bytes)
        self.atualiza_FAT_no_disco()

        # retorna o primeiro bloco alocado, pra ser salvo no indiceFAT do arquivo
        return blocos_alocados[0]

    def escrever_nos_blocos(self, blocos_alocados, conteudo_bytes):
        with open(self.fs, "r+b") as f:
            for i, bloco in enumerate(blocos_alocados):

                posicao_fisica = (self.inicio_dados + bloco * self.tamanho_bloco)
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

        quantidade_blocos = 0
        atual = indiceFAT

        while atual != -1:
            quantidade_blocos += 1
            atual = self.tabelaFAT[atual]

        # retorna o total de blocos * o tamanho do bloco
        return (quantidade_blocos* self.tamanho_bloco)

    def obter_blocos(self, indiceFAT):
        blocos = []

        if indiceFAT == -1:
            return blocos

        atual = indiceFAT

        while atual != -1:
            blocos.append(atual)
            atual = self.tabelaFAT[atual]

        return blocos

    def liberar_blocos(self, indiceFAT):
        if indiceFAT == -1:
            return

        atual = indiceFAT

        while atual != -1:
            proximo = self.tabelaFAT[atual]
            self.tabelaFAT[atual] = 0
            atual = proximo

        self.atualiza_FAT_no_disco()

    def quantidade_blocos_livres(self):
        livres = 0
        
        for i, valor in enumerate(self.tabelaFAT):
            posicao = (self.inicio_dados + i * self.tamanho_bloco)

            if posicao + self.tamanho_bloco > os.path.getsize(self.fs):
                continue

            if valor == 0:
                livres += 1

        return livres

    def quantidade_blocos_totais(self):
        total = 0
        tamanho_fs = os.path.getsize(self.fs)

        for i in range(len(self.tabelaFAT)):
            posicao = (self.inicio_dados + i * self.tamanho_bloco)

            if posicao + self.tamanho_bloco <= tamanho_fs:
                total += 1

        return total