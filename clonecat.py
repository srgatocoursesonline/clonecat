import os
import json
import logging
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError, ChatAdminRequiredError
from telethon.tl.types import MessageService
from colorama import Fore, Style, init
from tqdm import tqdm

# Inicializa cores no terminal
init(autoreset=True)

# Configuração do log para salvar erros
logging.basicConfig(filename="erros.log", level=logging.ERROR, format="%(asctime)s - %(message)s")

# Diretório temporário para salvar mídias
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

# Intervalo entre mensagens (em segundos)
MESSAGE_DELAY = 5  # 5000ms = 5 segundos

# Função para exibir ASCII Art
def print_ascii_art():
    ascii_art = f"""{Fore.GREEN}
  ______  __        ______   .__   __.  _______   ______      ___      .___________.
 /      ||  |      /  __  \  |  \ |  | |   ____| /      |    /   \     |           |
|  ,----'|  |     |  |  |  | |   \|  | |  |__   |  ,----'   /  ^  \    `---|  |----`
|  |     |  |     |  |  |  | |  . `  | |   __|  |  |       /  /_\  \       |  |     
|  `----.|  `----.|  `--'  | |  |\   | |  |____ |  `----. /  _____  \      |  |     
 \______||_______| \______/  |__| \__| |_______| \______|/__/     \__\     |__|     
    """
    print(ascii_art + Style.RESET_ALL)

# Função para coletar ou carregar API ID e Hash
def get_api_credentials():
    config_path = "config.json"

    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            credentials = json.load(file)
            print("Credenciais carregadas com sucesso.")
            return credentials["api_id"], credentials["api_hash"]

    api_id = input("Digite seu API ID: ").strip()
    api_hash = input("Digite seu API Hash: ").strip()
    if not api_id or not api_hash:
        print("API ID ou API Hash inválidos!")
        exit()

    with open(config_path, "w") as file:
        json.dump({"api_id": int(api_id), "api_hash": api_hash}, file)
        print("Credenciais salvas com sucesso.")

    return int(api_id), api_hash

# Função para criar o canal de destino automaticamente
def create_destination_channel(client, origin_chat_id):
    try:
        origin_chat = client(GetFullChannelRequest(origin_chat_id))
        origin_title = origin_chat.chats[0].title
        channel = client(CreateChannelRequest(
            title=f"{origin_title} - Clone",
            about="Canal gerado automaticamente para clonagem de mensagens.",
            megagroup=False
        ))
        channel_id = channel.chats[0].id
        channel_description = "Canal gerado automaticamente para clonagem de mensagens."
        print(f"Canal criado com sucesso! Nome: {origin_title} - Clone | ID do Canal: {channel_id}")
        return channel_id, origin_title, channel_description
    except Exception as e:
        logging.error(f"Erro ao criar canal de destino: {e}")
        print(f"Erro ao criar canal de destino: {e}")
        exit()

# Função para exibir o menu de seleção de conteúdo
def select_content_type():
    print("\nO que deseja clonar?\n")
    print("1 - Todas as Mensagens")
    print("2 - Apenas Imagens")
    print("3 - Apenas Vídeos")
    print("4 - Apenas Áudios")
    print("5 - Apenas Documentos")
    print("6 - Apenas Texto")
    print("7 - Apenas Stickers")
    print("8 - Tudo (Mensagens, Imagens, Vídeos, Áudios, Stickers, Documentos...)")
    choice = input("\nEscolha uma opção (1-8): ").strip()
    if choice == "1":
        return ["text", "photo", "video", "audio", "document", "sticker"]
    elif choice == "2":
        return ["photo"]
    elif choice == "3":
        return ["video"]
    elif choice == "4":
        return ["audio"]
    elif choice == "5":
        return ["document"]
    elif choice == "6":
        return ["text"]
    elif choice == "7":
        return ["sticker"]
    elif choice == "8":
        return ["text", "photo", "video", "audio", "document", "sticker"]
    else:
        print("Escolha inválida! Tente novamente.")
        return select_content_type()

# Função principal
def main():
    print_ascii_art()
    print("\nIniciando a clonagem de mensagens...\n")

    # Coleta de credenciais
    api_id, api_hash = get_api_credentials()

    # Conecta ao Telegram usando a Telethon
    with TelegramClient("session_name", api_id, api_hash) as client:
        print("Conexão estabelecida com sucesso.")

        # Entrada de dados
        origin_chat = input("Digite o ID do chat de origem (ID numérico): ").strip()
        try:
            origin_chat = int(origin_chat)
        except ValueError:
            print("O ID do chat de origem deve ser um número inteiro.")
            exit()

        # Cria o canal de destino automaticamente
        destination_chat, channel_name, channel_description = create_destination_channel(client, origin_chat)

        # Exibe o menu e seleciona o tipo de conteúdo a clonar
        content_types = select_content_type()

        # Obtém histórico de mensagens
        print("Obtendo histórico de mensagens...")
        messages = list(client.iter_messages(origin_chat))
        total_messages = len(messages)

        # Configura a barra de progresso TQDM
        with tqdm(total=total_messages, desc="Clonando mensagens", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}", colour="magenta") as progress:
            for message in reversed(messages):  # Garantir ordem da primeira para a última
                try:
                    # Ignora mensagens de serviço
                    if isinstance(message, MessageService):
                        continue

                    # Captura a legenda, verificando tanto em "caption" quanto no próprio texto
                    caption = message.caption if hasattr(message, "caption") else message.message or ""

                    # Filtra mensagens com base no tipo selecionado
                    if "photo" in content_types and message.photo:
                        client.send_file(destination_chat, message.photo, caption=caption)
                    elif "video" in content_types and message.video:
                        client.send_file(destination_chat, message.video, caption=caption, supports_streaming=True)
                    elif "audio" in content_types and message.audio:
                        client.send_file(destination_chat, message.audio, caption=caption)
                    elif "document" in content_types and message.document:
                        client.send_file(destination_chat, message.document, caption=caption)
                    elif "text" in content_types and message.text:
                        client.send_message(destination_chat, message.text)
                    elif "sticker" in content_types and message.sticker:
                        client.send_file(destination_chat, message.sticker)

                    # Delay entre os envios
                    time.sleep(MESSAGE_DELAY)
                except FloodWaitError as e:
                    logging.error(f"FloodWait de {e.seconds} segundos ao buscar mensagem {message.id}. Aguardando...")
                    time.sleep(e.seconds)
                except RPCError as e:
                    logging.error(f"Erro RPC ao acessar o Peer ID: {e}")
                    continue
                progress.update(1)

        # Busca o menu no canal original
        menu = get_menu_from_channel(client, origin_chat)

        # Adiciona o menu ao final do canal clonado
        if menu:
            print("\nAdicionando menu ao final do canal...")
            client.send_message(destination_chat, menu)
            print("Menu adicionado com sucesso!")
        else:
            print("Nenhum menu foi encontrado ou adicionado.")

        # Gera o link de acesso ao canal criado
        try:
            invite_link = client(ExportChatInviteRequest(destination_chat)).link
        except Exception as e:
            invite_link = "Não foi possível gerar o link."
            logging.error(f"Erro ao gerar link do canal: {e}")

        # Exibe as informações do canal criado
        print("\nClonagem concluída com sucesso!\n")
        print(f"ID do Canal: {destination_chat}")
        print(f"Nome: {channel_name}")
        print(f"Descrição: {channel_description}")
        print(f"Link: {invite_link}")

# Inicia o script
if __name__ == "__main__":
    main()
