import struct

from arquivo import Arquivo

class Diretorio:
    """
    Gerencia os diretórios do FURGfs4, incluindo leitura, escrita,
    busca, inserção, remoção, atualização e resolução de caminhos.
    """

    def __init__(self, fs, cabecalho, tabelaFAT):
        self.fs = fs
        self.cabecalho = cabecalho
        self.tabelaFAT = tabelaFAT

# LEITURA | ESCRITA BLOCOS 
    def ler_bloco(self, bloco): 
        posicao = ( self.cabecalho.inicio_dados + bloco * self.cabecalho.tamanho_bloco ) 

        with open(self.fs, "rb") as f: 
            f.seek(posicao) 
            return f.read(self.cabecalho.tamanho_bloco)

    def escrever_bloco(self, bloco, dados):
        posicao = (
            self.cabecalho.inicio_dados
            + bloco * self.cabecalho.tamanho_bloco
        )

        with open(self.fs, "r+b") as f:
            f.seek(posicao)
            f.write(dados)

    def ler_entrada(self, posicao):
        with open(self.fs, "rb") as f:
            f.seek(posicao)
            dados = f.read(Arquivo.TAMANHO)

            if len(dados) != Arquivo.TAMANHO:
                return None

            return Arquivo.desserializar(dados)

    def escrever_entrada(self, posicao, arquivo):
        with open(self.fs, "r+b") as f:
            f.seek(posicao)
            f.write(arquivo.serializar())

# BUSCA EM DIRETÓRIOS
    def buscar_no_diretorio(self, indice_bloco_dir, nome_procurado):
        bytes_por_arquivo = 64

        # Lê todas as entradas(arquivos) de 64 bytes de uma pasta específica e procura até achar o nome da pasta
        with open(self.fs, "rb") as f:
            atual = indice_bloco_dir

            while atual != -1:
                posicao_fisica = self.cabecalho.inicio_dados + (atual * self.cabecalho.tamanho_bloco)
                f.seek(posicao_fisica)

                entradas_por_bloco = self.cabecalho.tamanho_bloco // bytes_por_arquivo

                for i in range(entradas_por_bloco):
                    dados = f.read(bytes_por_arquivo)
                    if not dados:
                        break

                    nome, tamanho_arquivo, indiceFAT, status, protecao, reservado = struct.unpack('32s q i b b 18s', dados)
                    nome_str = nome.decode('utf-8').rstrip('\x00')

                    if status != 0 and nome_str == nome_procurado:
                        return {
                            "nome": nome_str,
                            "tamanho": tamanho_arquivo,
                            "indiceFAT": indiceFAT,
                            "status": status
                        }

                atual = self.tabelaFAT[atual]

        return None # não encontrou
    
    def buscar_no_diretorio_info(self, indiceFAT, nome):
        blocos = self.tabelaFAT.obter_blocos(indiceFAT)

        for bloco in blocos:
            posicao_bloco = (self.cabecalho.inicio_dados + bloco * self.cabecalho.tamanho_bloco)
            dados = self.ler_bloco(bloco)

            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]

                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if arquivo.status != 0 and arquivo.nome_string() == nome:
                    return {
                        "arquivo": arquivo,
                        "bloco": bloco,
                        "indice": posicao // Arquivo.TAMANHO,
                        "posicao": posicao_bloco + posicao
                    }
        return None

    def buscar_no_raiz_por_nome(self, nome_procurado):
        """busca rápida na raiz para o primeiro nível de diretório/arquivo"""
        bytes_por_arquivo = 64
        numero_arquivos = 128
        
        with open(self.fs, "rb") as f:
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)
            f.seek(inicio_diretorio_raiz)
            
            for _ in range(numero_arquivos):
                dados = f.read(bytes_por_arquivo)
                if not dados:
                    break
                nome, tamanho_arquivo, indiceFAT, status, protecao, reservado = struct.unpack('32s q i b b 18s', dados)
                nome_str = nome.decode('utf-8').rstrip('\x00')
                
                if status != 0 and nome_str == nome_procurado:
                    return {
                        "nome": nome_str,
                        "tamanho": tamanho_arquivo,
                        "indiceFAT": indiceFAT,
                        "status": status
                    }
        return None

    def buscar_no_raiz_por_nome_info(self, nome):

        quantidade_blocos = (self.cabecalho.tamanho_diretorio_raiz // self.cabecalho.tamanho_bloco)

        for bloco in range(quantidade_blocos):
            posicao_bloco = (self.cabecalho.inicio_diretorio_raiz + bloco * self.cabecalho.tamanho_bloco)
            dados = self.ler_bloco_raiz(bloco)

            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]

                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if (arquivo.status != 0 and arquivo.nome_string() == nome):
                    return {
                        "arquivo": arquivo,
                        "bloco": bloco,
                        "indice": posicao // Arquivo.TAMANHO,
                        "posicao": posicao_bloco + posicao
                    }
        return None

# ENTRADAS
    def encontrar_entrada_livre_raiz(self):

        quantidade_blocos = (self.cabecalho.tamanho_diretorio_raiz // self.cabecalho.tamanho_bloco)
        
        for bloco in range(quantidade_blocos):

            posicao_bloco = (self.cabecalho.inicio_diretorio_raiz + bloco * self.cabecalho.tamanho_bloco)
            dados = self.ler_bloco_raiz(bloco)

            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]
                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if arquivo.status == 0:
                    return posicao_bloco + posicao

        return None

    def encontrar_entrada_livre(self, indiceFAT):

        blocos = self.tabelaFAT.obter_blocos(indiceFAT)
        for bloco in blocos:

            dados = self.ler_bloco(bloco)
            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]

                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if arquivo.status == 0:
                    return (self.cabecalho.inicio_dados + bloco * self.cabecalho.tamanho_bloco + posicao)
        return None

# BLOCOS DA RAIZ
    def ler_bloco_raiz(self, bloco):
        posicao = (self.cabecalho.inicio_diretorio_raiz + bloco * self.cabecalho.tamanho_bloco)

        with open(self.fs, "rb") as f:
            f.seek(posicao)
            return f.read(self.cabecalho.tamanho_bloco)

# INSERIR | REMOVER | ATUALIZAR
    def inserir_na_raiz(self, arquivo):

        posicao = self.encontrar_entrada_livre_raiz()
        if posicao is None:
            raise Exception("Diretório raiz está cheio.")

        self.escrever_entrada(posicao, arquivo)
        return posicao

    def inserir_no_diretorio(self, indiceFAT, arquivo):

        posicao = self.encontrar_entrada_livre(indiceFAT)
        if posicao is None:
            raise Exception("Diretório cheio.")

        self.escrever_entrada(posicao, arquivo)
        return posicao

    def remover_entrada(self, posicao):
        arquivo_vazio = Arquivo("", 0, -1, 0, 0)
        self.escrever_entrada(posicao,arquivo_vazio)

    def atualizar_entrada(self, posicao, arquivo):
        self.escrever_entrada(posicao, arquivo)

# RESOLUÇÃO DE CAMINHO
    def resolver_caminho(self, caminho):

        if not caminho or caminho == "/":
            return None

        partes = [p for p in caminho.split("/")if p]
        diretorio_atual_bloco = None
        primeiro_nivel = partes[0]
        item_encontrado = self.buscar_no_raiz_por_nome(primeiro_nivel)

        if not item_encontrado:
            raise Exception(f"Diretório ou arquivo '{primeiro_nivel}' não encontrado.")

        if len(partes) == 1:
            return item_encontrado["indiceFAT"]

        atual_info = item_encontrado

        for parte in partes[1:]:
            if atual_info["status"] != 2:
                raise Exception(f"'{atual_info['nome']}' não é um diretório.")

            atual_info = self.buscar_no_diretorio(atual_info["indiceFAT"], parte)

            if not atual_info:
                raise Exception(f"Caminho '{parte}' não encontrado.")

        return atual_info["indiceFAT"]

    # retorna entrada completa e da posição física 
    def resolver_caminho_info(self, caminho):

        if not caminho or caminho == "/":
            return {"indiceFAT": -1,"arquivo": None,"posicao": None,"raiz": True} 

        caminho = caminho.strip("/")
        partes = caminho.split("/")
        atual = -1

        for i, parte in enumerate(partes):

            if i == 0:
                resultado = (self.buscar_no_raiz_por_nome_info(parte))

            else:
                resultado = (self.buscar_no_diretorio_info(atual, parte))

            if resultado is None:
                return None

            arquivo = resultado["arquivo"]

            if i < len(partes) - 1:
                if arquivo.status != 2:
                    return None

                atual = arquivo.indiceFAT

            else:
                return resultado

        return None

# LISTAGEM
    def obter_entradas_raiz(self):

        quantidade_blocos = (self.cabecalho.tamanho_diretorio_raiz // self.cabecalho.tamanho_bloco)
        entradas = []

        for bloco in range(quantidade_blocos):
            dados = self.ler_bloco_raiz(bloco)

            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]

                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if arquivo.status != 0:
                    entradas.append(arquivo)

        return entradas

    def obter_entradas(self, indiceFAT):

        entradas = []
        blocos = self.tabelaFAT.obter_blocos(indiceFAT)

        for bloco in blocos:
            dados = self.ler_bloco(bloco)

            for posicao in range(0, len(dados), Arquivo.TAMANHO):
                trecho = dados[posicao:posicao + Arquivo.TAMANHO]

                if len(trecho) != Arquivo.TAMANHO:
                    continue

                arquivo = Arquivo.desserializar(trecho)
                if arquivo.status != 0:
                    entradas.append(arquivo)

        return entradas