# Tamanho diretório raiz: 2 Blocos (8192 bytes)
# 64 bytes pra cada arquivo
# Número de arquivos suportado: 8192 / 64 = 128 arquivos

import struct

class Arquivo:
    FORMATO = '32s q q b b 14s'
    def __init__(self, nome, tamanhoArquivo, indiceFAT, status, protecao):

        self.nome = nome.encode("utf-8")[:32].ljust(32, b'\x00') # 32 bytes (32s no struct)
        self.tamanhoArquivo = tamanhoArquivo # 8 Bytes (q)
        self.indiceFAT = indiceFAT # 8 Bytes (q)
        self.status = status # 1 Byte (b) -> (Ex: 0=Livre, 1=Ocupado, 2=É um subdiretório)
        self.protecao = protecao # 1 Byte (b) -> para implementar o protect
        self.reservado = b'\x00' * 14 # Sobram 14 Bytes (14s) para usar para outras funcionalidades, como data de criação

    def serializar(self):
        return struct.pack(
            self.FORMATO,
            self.nome,
            self.tamanhoArquivo,
            self.indiceFAT,
            self.status,
            self.protecao,
            self.reservado
        )

# Próximos passos: Ler o bloco de 8192 bytes do diretório raiz do arquivo furgfs4.fs e "fatiar" ele de 64 em 64 bytes para listar os arquivos -> comando ls