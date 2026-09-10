# SistemaDeArquivos-SO
Sistema de Arquivos criado para a disciplina de Sistemas Operacionais

-> O diretório raiz não guarda o conteúdo do arquivo. Guarda apenas nome, tamanho real, onde o arquivo começa na FAT e outros dados.

-> A FAT gerencia a navegação

-> Blocos: arquivos não dividem blocos com outros arquivos. Se um arquivo for menor que o espaço do bloco, os bytes restantes são desperdiçados. Se o arquivo for maior que o espaço do bloco, vai precisar de mais de um bloco só pra ele.