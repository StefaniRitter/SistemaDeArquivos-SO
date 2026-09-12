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
                 if valor == 0:
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
                self.tabelaFAT[livre] = -1 # preenche com -1 temporariamente pra não ficar como livre
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

        # retorna o total de blocos * o tamanho do bloco
        return (i*self.tamanho_bloco)


# COMANDOS DO TERMINAL:

    def executar_ls(self, arquivo=None):

        bytes_por_arquivo = 64
        AZUL = "\033[94m"
        RESET = "\033[0m"

        try:
            indice_bloco_dir = self.resolver_caminho(arquivo)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "rb") as f:
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            if indice_bloco_dir is None:
                inicio_atual = inicio_diretorio_raiz

                # o diretório raiz ocupa dois blocos
                numero_arquivos = (self.tamanho_bloco * 2) // bytes_por_arquivo

            else:
                # se passou um subdiretório, lê a partir dos blocos de dados dele via FAT
                numero_arquivos = self.tamanho_bloco // bytes_por_arquivo
                inicio_atual = self.inicio_dados + (indice_bloco_dir * self.tamanho_bloco)

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
                    tamanho_ocupado_sistema = self.retorna_tamanho_ocupado(indiceFAT)

                    ocupado_str = f"{tamanho_ocupado_sistema} bytes"
                    real_str = f"{tamanho_arquivo} bytes"

                    if status == 1:
                        print(f"{nome_str:<35}  {ocupado_str:<32}  {real_str}")

                    elif status == 2:
                        print(f"{AZUL}{nome_str:<35}  {ocupado_str:<32}  {real_str}{RESET}") # deixa o nome das pastas em azul

    def executar_cp(self, caminho, destino_completo="/"):

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
        primeiro_bloco_alocado = self.alocar_espaco(conteudo)

        TAMANHO_ENTRADA = 64
        NUM_ENTRADAS = 128

        try:
            indice_dir = self.resolver_caminho(caminho_destino)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "r+b") as f:
            f.seek(0)
            cabecalho = f.read(48)

            _, self.tamanho_bloco, _, _, inicio_diretorio_raiz, _= struct.unpack('q q q q q q', cabecalho)

            # define onde o cursor vai começar a procurar gaveta vazia
            if indice_dir is None:
                inicio_atual = inicio_diretorio_raiz
                NUM_ENTRADAS = (self.tamanho_bloco * 2) // TAMANHO_ENTRADA
            else:
                inicio_atual = self.inicio_dados + (indice_dir * self.tamanho_bloco)
                NUM_ENTRADAS = self.tamanho_bloco // TAMANHO_ENTRADA

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

    def executar_debug(self, nome_arquivo):
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
                atual = self.tabelaFAT[atual] # pega o valor que ta no índice, que é o número do próximo bloco e índice da FAT

            print(f"Cadeia de blocos do arquivo {nome_arquivo}:")
            print(cadeia)
                    

    def executar_mkdir(self, caminho_completo):

        if "/" in caminho_completo:
            partes = caminho_completo.rsplit("/", 1)
            caminho_destino = partes[0] if partes[0] != "" else "/"
            nome_pasta = partes[1]
        else:
            caminho_destino = "/"
            nome_pasta = caminho_completo

        # cria um bloco de dados vazio (4096 bytes de \x00) para a nova pasta
        conteudo_vazio = b'\x00' * self.tamanho_bloco
        
        # aloca espaço na FAT para essa pasta e escreve o bloco vazio no disco
        primeiro_bloco = self.alocar_espaco(conteudo_vazio)
        
        # procura uma vaga livre no Diretório Raiz (ou diretório atual) para registrar a pasta
        TAMANHO_ENTRADA = 64
        NUM_ENTRADAS = 128

        try:
            indice_dir = self.resolver_caminho(caminho_destino)
        except Exception as e:
            print(e)
            return

        with open(self.fs, "r+b") as f:
            f.seek(0)
            cabecalho = f.read(48)
            _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

            if indice_dir is None:
                inicio_atual = inicio_diretorio_raiz
                NUM_ENTRADAS = (self.tamanho_bloco * 2) // TAMANHO_ENTRADA
            else:
                inicio_atual = self.inicio_dados + (indice_dir * self.tamanho_bloco)
                NUM_ENTRADAS = self.tamanho_bloco // TAMANHO_ENTRADA

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

    # Em vez de ler fixo o inicio_diretorio_raiz, essa função lê o conteúdo de qualquer bloco apontado por uma FAT.
    def buscar_no_diretorio(self, indice_bloco_dir, nome_procurado):

        bytes_por_arquivo = 64

        # Lê todas as entradas(arquivos) de 64 bytes de uma pasta específica e procura até achar o nome da pasta

        with open(self.fs, "rb") as f:
            atual = indice_bloco_dir

            while atual != -1:
                posicao_fisica = self.inicio_dados + (atual * self.tamanho_bloco)
                f.seek(posicao_fisica)

                entradas_por_bloco = self.tamanho_bloco // bytes_por_arquivo

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

    def resolver_caminho(self, caminho):
        """Recebe um caminho (ex: '/pasta1/subpasta') e retorna o índice do bloco de dados 
           do diretório final, ou levanta um erro se não encontrar."""
        if not caminho or caminho == "/":
            return None # vai pra raiz padrão

        # remove barras extras e divide o caminho
        partes = [p for p in caminho.split("/") if p]
        
        # começa buscando no Diretório Raiz
        # como a raiz ocupa 2 blocos físicos, varre esses blocos iniciais
        diretorio_atual_bloco = None
        
        # se for procurar na raiz, usamos a  função de busca do diretório raiz
        # busca o primeiro componente na raiz
        primeiro_nivel = partes[0]
    
        item_encontrado = self.buscar_no_raiz_por_nome(primeiro_nivel)
        if not item_encontrado:
            raise Exception(f"Diretório ou arquivo '{primeiro_nivel}' não encontrado.")
            
        if len(partes) == 1:
            return item_encontrado["indiceFAT"]

        # se tiver mais subníveis, continua navegando pelos subdiretórios
        atual_info = item_encontrado
        for parte in partes[1:]:
            if atual_info["status"] != 2:
                raise Exception(f"'{atual_info['nome']}' não é um diretório.")
            
            atual_info = self.buscar_no_diretorio(atual_info["indiceFAT"], parte)
            if not atual_info:
                raise Exception(f"Caminho '{parte}' não encontrado.")
                
        return atual_info["indiceFAT"]

    def interface_ls(self, caminho=None):
        if not caminho or caminho == "/":
            self.executar_ls(None) # lista a raiz
        else:
            try:
                indice_pasta = self.resolver_caminho(caminho)
                self.executar_ls(indice_pasta) # lista o subdiretório
            except Exception as e:
                print(e)

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









                     



             


             
             
             
               

        
        

                
                 


            

            
            









