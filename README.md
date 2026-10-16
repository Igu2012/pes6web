# PES 6 — Tela cheia local

Cópia local do cliente web **PES 6 Web Online Port** publicado em [pes6.optijuegos.net](https://pes6.optijuegos.net/), incluindo motor WebAssembly e pacote de dados. Este repositório mantém o pacote em quatro partes (`payload/pes6.pak.parts/`) para respeitar o limite de tamanho por arquivo do GitHub; o launcher remonta o arquivo automaticamente antes de abrir o jogo.

## Como abrir

- **Windows:** execute `START-GAME.cmd`.
- **Linux/macOS:** execute `./start-game.sh`.

O launcher precisa de **Python 3** e chama `assemble_pak.py` antes de iniciar o servidor. A montagem verifica o tamanho e o SHA-256; se algum chunk estiver ausente ou alterado, o jogo não inicia. O arquivo reconstruído fica em `site/assets/pes6.pak` (352.054.197 bytes). O servidor HTTP local usa `127.0.0.1:8765` e apenas a biblioteca padrão do Python, sem `pip`. Não abra `site/index.html` diretamente como `file://`: o navegador bloqueia o WebAssembly e as requisições por intervalos do pacote.

Pressione **F11** se quiser ocultar também as barras do navegador. Para parar o servidor no Windows, feche a janela minimizada do servidor ou execute `STOP-GAME.cmd`.

## O que esperar

A página mostra só a imagem do jogo, ocupa toda a área visível do navegador e inicia a emulação sozinha. A tela de loading do site e as opções de início foram ocultadas; o motor ainda faz a preparação necessária dos arquivos locais antes de exibir a primeira imagem. A configuração inicial seleciona inglês e pula a intro.

O primeiro menu visível pode ser a tela **Game Level**, que pertence ao próprio PES 6. **Regular** já fica selecionado. Confirme essa escolha para continuar; o launcher não escolhe dificuldade, times nem inicia uma partida por conta própria.

O pacote de dados é lido localmente conforme necessário. O modo individual não precisa buscar o pacote pela Internet; o modo online continua dependendo de conexão e do relay do projeto original.

## Compatibilidade e origem

Use um navegador atualizado com **WebGL 2** e aceleração gráfica habilitada. Esta é a versão PSP de PES 6 portada para WebAssembly, não a edição nativa de PC.

Cliente web e motor: **OptiProjects / PES 6 Web Online Port** — https://pes6.optijuegos.net/. Os dados vieram do pacote configurado pelo próprio site. O projeto original declara não ser afiliado à Konami; Pro Evolution Soccer e seu conteúdo pertencem aos respectivos titulares. Esta cópia destina-se ao uso local; **não redistribua publicamente**.
