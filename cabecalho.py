import struct


'''
tamanho_cabecalho
tamanho_bloco: decisão de design (ex: 4096 bytes, ou 4KB)
inicio_fat:  byte exato logo após o cabeçalho
inicio_diretorio_raiz: endereço inicial da FAT + (o tamanho que a FAT vai ocupar)
inicio_dados: endereço do diretório raiz + (o tamanho que o diretório vai ocupar)

'''

class Cabecalho:

    # FORMATO diz para o struct empacotar 6 variáveis do tipo "long long" (8 bytes cada), suportando tamanhos grandes de arquivo.
    FORMATO = 'q q q q q q'
    TAMANHO_ESTRUTURA = struct.calcsize(FORMATO)

    def __init__(self, tamanho_sistema, tamanho_bloco = 4096):

        self.tamanho_cabecalho = self.TAMANHO_ESTRUTURA
        self.tamanho_bloco = tamanho_bloco

        self.tamanho_sistema = tamanho_sistema

        self.inicio_fat = self.tamanho_cabecalho

        self.quantidade_blocos = tamanho_sistema // tamanho_bloco
        self.tamanho_fat_bytes = self.quantidade_blocos * 4 # ajustar os bytes por entrada na FAT

        self.inicio_diretorio_raiz = self.inicio_fat + self.tamanho_fat_bytes

        self.tamanho_diretorio_raiz = self.tamanho_bloco * 2 # o diretório raiz ocupa 2 blocos inteiro

        self.inicio_dados = self.inicio_diretorio_raiz + self.tamanho_diretorio_raiz

    def serializar(self):
        return struct.pack(
                           self.FORMATO,
                           self.tamanho_cabecalho,
                           self.tamanho_bloco,
                           self.tamanho_sistema,
                           self.inicio_fat,
                           self.inicio_diretorio_raiz,
                           self.inicio_dados
        )