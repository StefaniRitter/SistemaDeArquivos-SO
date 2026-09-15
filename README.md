# FURGfs4 - Sistema de Arquivos

Trabalho desenvolvido para a disciplina de Sistemas Operacionais.

O FURGfs4 é um sistema de arquivos implementado em Python que funciona dentro de um arquivo do sistema operacional real. A implementação utiliza FAT (File Allocation Table) para controlar a alocação dos blocos e permite operações básicas de arquivos e diretórios.

### Integrantes
- Stefani Ritter - 169599
- Victória Horita - 169595


### Estrutura do projeto
```
SistemaDeArquivos-SO/ 
├── main.py            # Execução do programa, criação/abertura do FS e interpretação dos comandos.
├── cabecalho.py       # Define e gerencia o cabeçalho do sistema de arquivos.
├── tabelaFAT.py       # Implementa a FAT, alocação, liberação e consulta dos blocos.
├── arquivo.py         # Representa e serializa as entradas de arquivos e diretórios.
├── diretorio.py       # Gerencia diretórios, entradas, buscas e resolução de caminhos.
├── operacoes.py       # Implementa as operações do usuário: cp, cpout, mv, rm, ls, df, mkdir, protect, debug, find e sha256.
└── README.md          # Documentação do projeto.
```

### Como executar

``
python main.py
``

Na primeira execução, informe o tamanho do sistema de arquivos:

``
800 MB
``

O arquivo furgfs4.fs será criado. Nas próximas execuções, o sistema existente será reutilizado.


### Comandos 
- ls mkdir <nome> 
- cp <arquivo_externo> 
- <nome> cpout <nome> <arquivo_externo> 
- mv <nome_atual> <novo_nome> 
- rm <nome> 
- df 
- protect <nome> 
- debug <nome> 
- find <nome> sha256 <nome> exit

### Exemplo 
```
python main.py 
10 MB 
mkdir documentos 
ls 
cp teste.txt teste2.txt 
debug teste2.txt 
df 
mv teste2.txt teste3.txt 
sha256 teste3.txt 
rm teste3.txt 
exit
```

### Observações 
-> O diretório raiz não guarda o conteúdo do arquivo. Guarda apenas nome, tamanho real, onde o arquivo começa na FAT e outros metadados. No diretório raiz, ficam apenas os arquivos e subdiretórios da raiz (/). Os arquivos e pastas contidos dentro desses subdiretórios se encontram percorrendo a sequência a partir do indiceFAT de cada um.

Arquivos -> os metadados são armazenados no diretório raiz, e o conteúdo de fato é armazenado nos blocos.
Subdiretórios -> são quase como os arquivos, mas o que está gravado nos blocos dele não é o conteúdo e sim uma lista de entradas de 64 bytes (outros arquivos), assim como fica no bloco do diretório raiz.

-> A tabela FAT gerencia a navegação, apontando apenas para os blocos onde se encontram os dados, e também não guarda os conteúdos. A FAT contem o índice, que é o número do bloco atual, e o valor é o número do próximo bloco. 
O número do bloco é o próprio índice da FAT, então se for realizada uma busca a partir do bloco 8, por exemplo, e o arquivo possui mais de um bloco, para descobrir o próximo bloco do arquivo basta acessar a FAT no índice 8, o valor contido lá dentro é o valor do próximo bloco e por ai vai...

-> Blocos: arquivos não dividem blocos com outros arquivos. Se um arquivo for menor que o espaço do bloco, os bytes restantes são desperdiçados. Se o arquivo for maior que o espaço do bloco, vai precisar de mais de um bloco só pra ele.