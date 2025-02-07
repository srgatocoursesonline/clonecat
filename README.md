# CLONECAT

# CloneCat - Telegram Channel Cloner

CloneCat é uma ferramenta poderosa e automatizada para clonar canais do Telegram. Com ela, você pode copiar mensagens, mídias (fotos, vídeos, áudios, documentos) e menus de um canal de origem para um novo canal automaticamente criado.

## Funcionalidades

- Clona mensagens de texto, fotos, vídeos, áudios e documentos.
- Mantém as legendas associadas às mídias.
- Adiciona automaticamente o menu existente no canal original ao final do canal clonado.
- Gera automaticamente um canal de destino com nome baseado no canal original.
- Respeita limites do Telegram para evitar bans, com intervalo configurável entre as mensagens.

## Pré-requisitos

Antes de usar o CloneCat, certifique-se de ter:

1. Python 3.8 ou superior instalado.
2. Biblioteca `telethon` e outras dependências listadas em `requirements.txt`.

## Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/clonecat.git
   cd clonecat

Instale as dependências:

pip install -r requirements.txt

Configure suas credenciais do Telegram:

Na primeira execução, o script solicitará seu API ID e API Hash, que podem ser obtidos aqui (https://my.telegram.org/). Essas credenciais serão salvas automaticamente para reutilização futura.

Uso
Execute o script principal:

python clonecat.py

Siga os passos no terminal:

Digite o ID do canal de origem.

O script criará automaticamente um canal de destino e iniciará a clonagem das mensagens.

Ao final, será exibido o link do canal clonado.

Considerações

O script respeita os limites de envio do Telegram com um intervalo padrão de 5 segundos entre as mensagens. Esse valor pode ser ajustado diretamente no código.

Cuidado: Evite clonar canais com grandes volumes de dados em curto intervalo de tempo para não violar as políticas do Telegram.

Contribuindo
Sinta-se à vontade para abrir issues ou enviar pull requests para melhorias no CloneCat.

By Mr. Cat
