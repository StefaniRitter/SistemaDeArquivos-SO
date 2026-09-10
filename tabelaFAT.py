import struct

class Fat:

    def __init__(self, tamanhoFAT, fs: str = "furgfs4.fs"):
        self.max = tamanhoFAT
        self.tabelaFAT = []
        self.inicio_dados = -1
        self.inicio_fat = -1
        self.fim = -1

        with open(fs, "rb") as f:

            # desserialização do cabeçalho
            cabecalho = f.read(48)
            _, tamanho_bloco, _, self.inicio_fat, _, self.inicio_dados = struct.unpack('q q q q q q', cabecalho)

            # manda cursor pro início da fat, que ainda esta serialziada
            f.seek(self.inicio_fat)
            num_entradas_fat = 












            f.seek(inicioFAT)
            for i in range(self.inicio, self.fim)



    def adiciona_arquivo(arquivo):


