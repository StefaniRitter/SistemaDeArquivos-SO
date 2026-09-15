import struct


'''
tamanho_cabecalho
tamanho_bloco: decisão de design (ex: 4096 bytes, ou 4KB)
inicio_fat:  byte exato logo após o cabeçalho
inicio_diretorio_raiz: endereço inicial da FAT + (o tamanho que a FAT vai ocupar)
inicio_dados: endereço do diretório raiz + (o tamanho que o diretório vai ocupar)

'''

class Cabecalho:
    """
    Representa o cabeçalho do FURGfs4 e armazena as informações necessárias
    para localizar a FAT, o diretório raiz e a área de dados.
    """

    # FORMATO diz para o struct empacotar 6 variáveis do tipo "long long" (8 bytes cada), suportando tamanhos grandes de arquivo.
    FORMATO = 'q q q q q q'
    TAMANHO_ESTRUTURA = struct.calcsize(FORMATO)
    
    def __init__(self, tamanho_sistema, tamanho_bloco = 4096):
        self.tamanho_cabecalho = self.TAMANHO_ESTRUTURA 
        self.tamanho_bloco = tamanho_bloco 

        self.tamanho_sistema = tamanho_sistema
        self.inicio_fat = self.tamanho_cabecalho 
        self.tamanho_diretorio_raiz = self.tamanho_bloco * 2 # o diretório raiz ocupa 2 blocos inteiros  

        # espaço fixo que não pertence a região de dados
        espaco_fixo = (self.tamanho_cabecalho + self.tamanho_diretorio_raiz)
        self.quantidade_blocos = ( self.tamanho_sistema - espaco_fixo) // (tamanho_bloco + 4)

        self.tamanho_fat_bytes = self.quantidade_blocos * 4 # 4 bytes por entrada na FAT 
        self.inicio_diretorio_raiz = self.inicio_fat + self.tamanho_fat_bytes 
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

    @classmethod
    def desserializar(cls, dados):
        if len(dados) != cls.TAMANHO_ESTRUTURA:
            raise ValueError("Cabeçalho inválido.")

        valores = struct.unpack(cls.FORMATO,dados)
        objeto = cls.__new__(cls)

        (objeto.tamanho_cabecalho, objeto.tamanho_bloco, objeto.tamanho_sistema, objeto.inicio_fat, 
        objeto.inicio_diretorio_raiz, objeto.inicio_dados) = valores

        objeto.tamanho_fat_bytes = (objeto.inicio_diretorio_raiz - objeto.inicio_fat)
        objeto.tamanho_diretorio_raiz = (objeto.inicio_dados - objeto.inicio_diretorio_raiz)
        objeto.quantidade_blocos = (objeto.tamanho_fat_bytes // 4)

        return objeto     