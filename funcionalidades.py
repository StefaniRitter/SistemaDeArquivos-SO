import struct 

# Tamanho diretório raiz: 2 Blocos (8192 bytes)
# 64 bytes pra cada arquivo
# Número de arquivos suportado: 8192 / 64 = 128 arquivos
# cabeçalho: tamanho_bloco = 4096

# Próximos passos: Ler o bloco de 8192 bytes do diretório raiz do arquivo furgfs4.fs e "fatiar" ele de 64 em 64 bytes para listar os arquivos -> comando ls 

def executar_fs(fs: str = "furgfs4.fs"):

    bytes_por_arquivo = 64
    numero_arquivos = 128
    AZUL = "\033[94m"
    RESET = "\033[0m"

    with open(fs, "rb") as f:
        cabecalho = f.read(48)
        _, _, _, _, inicio_diretorio_raiz, _ = struct.unpack('q q q q q q', cabecalho)

        f.seek(inicio_diretorio_raiz) # manda o cursor pro inicio do diretório raiz

        print(f"{'NOME':<35}  {'TAMANHO OCUPADO NO SISTEMA':<15}  {'TAMANHO REAL'}")

        for i in range(numero_arquivos):
            dados = f.read(bytes_por_arquivo)
            if not dados:
                break

            # desserealiza utilizando o formato da classe Arquivo
            nome, tamanho_arquivo, indiceFAT, status, protecao, reservado = struct.unpack('32s q q b b 14s', dados)

            # limpa os bytes nulos extras
            nome_str = nome.decode('utf-8').rstrip('\x00')

            tamanho_ocupado_sistema = 0 

            if status == 1:
                print(f"{nome_str}    {tamanho_ocupado_sistema}     {tamanho_arquivo}") #Mudar tamanho usado depois com a lógica da FAT
            elif status == 2:
                print(f"{AZUL}{nome_str}    {tamanho_arquivo}     {tamanho_arquivo}{RESET}") # deixa o nome das pastas em azul
                



            







executar_fs()