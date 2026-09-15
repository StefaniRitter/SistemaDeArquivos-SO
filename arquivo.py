import struct

class Arquivo:
    """
    Representa uma entrada de arquivo ou diretório armazenada no FURGfs4.
    Cada entrada possui 64 bytes e contém nome, tamanho, posição na FAT,
    status, proteção e espaço reservado.
    """
    FORMATO = '32s q i b b 18s'
    TAMANHO = struct.calcsize(FORMATO)  # 64 bytes

    def __init__(self, nome, tamanhoArquivo, indiceFAT, status, protecao=0):
        self.nome = nome.encode("utf-8")[:32].ljust(32, b'\x00') # 32 bytes (32s no struct)
        self.tamanhoArquivo = tamanhoArquivo # 8 Bytes (q) indicam qual o tamanho
        self.indiceFAT = indiceFAT # 8 Bytes (q) # indice do bloco onde o arquivo começa na FAT
        self.status = status # 1 Byte (b) -> (0=Livre, 1=Ocupado, 2=É um subdiretório)
        self.protecao = protecao # 1 Byte (b) -> para implementar o protect
        self.reservado = b'\x00' * 18 # Sobram 18 Bytes (18s) para usar para outras funcionalidades, como data de criação

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
    
    def nome_string(self):
        return self.nome.split(b'\x00', 1)[0].decode('utf-8')

    @classmethod
    def desserializar(cls, dados):
        (nome, tamanho, indice_fat, status, protecao, _) = struct.unpack(cls.FORMATO, dados)
        nome = nome.split(b'\x00', 1)[0].decode("utf-8")

        return cls(
            nome=nome,
            tamanhoArquivo=tamanho,
            indiceFAT=indice_fat,
            status=status,
            protecao=protecao
        )