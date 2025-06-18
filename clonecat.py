import os
import json
import logging
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError, ChatAdminRequiredError
from telethon.tl.types import MessageService, Channel
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
    ascii_art = rf"""{Fore.GREEN}
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
        print("\n❌ Não foi possível criar o canal de destino ou acessar o canal de origem.")
        print("Motivos possíveis:")
        print("- O canal de origem está com a proteção de conteúdo ativada (Restringir salvamento de conteúdo)")
        print("- O canal de origem é privado e sua conta não tem permissão de acesso total")
        print("- O ID informado está incorreto ou sua conta não é membro do canal")
        print(f"Detalhes técnicos: {e}")
        logging.error(f"Erro ao criar canal de destino: {e}")
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

# Função para buscar o menu (mensagem fixada) do canal de origem
def get_menu_from_channel(client, origin_chat_id):
    try:
        # 1. Tenta buscar a mensagem fixada
        full_channel = client(GetFullChannelRequest(origin_chat_id))
        pinned_msg_id = getattr(full_channel.full_chat, 'pinned_msg_id', None)
        if pinned_msg_id:
            pinned_msg = client.get_messages(origin_chat_id, ids=pinned_msg_id)
            if pinned_msg and (pinned_msg.text or pinned_msg.message):
                return (pinned_msg.text or pinned_msg.message, pinned_msg.id)
        # 2. Se não houver mensagem fixada, busca entre as primeiras 10 mensagens por palavras-chave
        keywords = ["menu", "navegação", "clique aqui", "#", "conteúdo"]
        for message in client.iter_messages(origin_chat_id, limit=10):
            content = (message.text or message.message or "").lower()
            if any(kw in content for kw in keywords):
                if len(content) > 100 or content.count("#") > 3 or content.count("http") > 2:
                    return (message.text or message.message, message.id)
        return (None, None)
    except Exception as e:
        logging.error(f"Erro ao buscar menu (mensagem fixada ou por análise): {e}")
        return (None, None)

# Função para verificar se a proteção de conteúdo está ativada
def is_content_protected(client, origin_chat_id):
    try:
        full_channel = client(GetFullChannelRequest(origin_chat_id))
        # Para canais, a flag 'protected' indica proteção de conteúdo
        if hasattr(full_channel.full_chat, 'protected'):
            return full_channel.full_chat.protected
        # Algumas versões usam 'can_view_stats' como proxy, mas o correto é 'protected'
        return False
    except Exception as e:
        logging.error(f"Erro ao verificar proteção de conteúdo: {e}")
        return False

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

        # Verifica se a proteção de conteúdo está ativada
        if is_content_protected(client, origin_chat):
            print("\n⚠️ Não é possível clonar este canal pois a proteção de conteúdo está ativada!\n" \
                  "Desative a opção 'Restringir salvamento de conteúdo' nas configurações do canal e tente novamente.")
            return

        # Cria o canal de destino automaticamente
        destination_chat, channel_name, channel_description = create_destination_channel(client, origin_chat)

        # Exibe o menu e seleciona o tipo de conteúdo a clonar
        content_types = select_content_type()

        # Obtém histórico de mensagens
        print("Obtendo histórico de mensagens...")
        messages = list(client.iter_messages(origin_chat, limit=None))
        print(f"Total de mensagens encontradas: {len(messages)}")
        print(f"IDs das mensagens: {[m.id for m in messages]}")
        total_messages = len(messages)

        # Busca o menu antes de clonar as mensagens
        menu, menu_id = get_menu_from_channel(client, origin_chat)
        print(f"Menu encontrado: {menu is not None}, ID do menu: {menu_id}")

        # Coleta todos os IDs das mensagens clonadas
        cloned_ids = set(m.id for m in messages)

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

        # Após clonar as mensagens, adicionar o menu ao final se ele não foi clonado
        if menu and (menu_id not in cloned_ids):
            print("\nAdicionando menu ao final do canal clonado...")
            client.send_message(destination_chat, menu)
            print("Menu adicionado com sucesso!")
        elif menu:
            print("Menu já estava entre as mensagens clonadas, não foi adicionado novamente.")
        else:
            print("Nenhum menu encontrado para adicionar ao canal clonado.")

        # Exibe as informações do canal criado
        print("\nClonagem concluída com sucesso!\n")
        print(f"ID do Canal: {destination_chat}")
        print(f"Nome: {channel_name}")
        print(f"Descrição: {channel_description}")

# Inicia o script
if __name__ == "__main__":
    main()
