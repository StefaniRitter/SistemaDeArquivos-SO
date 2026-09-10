# Sistema De Arquivos

Sistema de Arquivos criado para a disciplina de Sistemas Operacionais

-> O diretório raiz não guarda o conteúdo do arquivo. Guarda apenas nome, tamanho real, onde o arquivo começa na FAT e outros dados. No diretório raiz, ficam apenas os arquivos e subdiretórios da raiz (/). Os arquivos e pastas contidos dentro desses subdiretórios se encontram percorrendo a sequência a partir do indiceFAT de cada um.

-> A tabela FAT gerencia a navegação, apontando apenas para os blocos onde se encontram os dados, e também não guarda os conteúdos. A FAT contem o índice, que é o número do bloco atual, e o valor é o número do próximo bloco. 
O número do bloco é o próprio índice da FAT, então se for realizada uma busca a partir do bloco 8, por exemplo, e o arquivo possui mais de um bloco, para descobrir o próximo bloco do arquivo basta acessar a FAT no índice 8, o valor contido lá dentro é o valor do próximo bloco e por ai vai...
1   2   3   4   5   6   7   8   9   10
[]  []  []  []  []  []  []  []  []  []

-> Blocos: arquivos não dividem blocos com outros arquivos. Se um arquivo for menor que o espaço do bloco, os bytes restantes são desperdiçados. Se o arquivo for maior que o espaço do bloco, vai precisar de mais de um bloco só pra ele.

