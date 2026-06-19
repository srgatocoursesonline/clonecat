import os
import json
import logging
import re
import shutil
import subprocess
import time
import random
from concurrent.futures import ThreadPoolExecutor
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest
from telethon.tl.functions.channels import CreateForumTopicRequest, GetForumTopicsRequest
from telethon.tl.functions.messages import ExportChatInviteRequest, GetFullChatRequest
from telethon.tl.functions.messages import SendMessageRequest, SendMediaRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError, ChatAdminRequiredError
from telethon.tl.types import MessageService, Channel, Chat, UpdateMessageID
from colorama import Fore, Style, init
from tqdm import tqdm

# Inicializa cores no terminal
init(autoreset=True)

# Configuração do log para salvar erros
logging.basicConfig(filename="erros.log", level=logging.WARNING, format="%(asctime)s - %(message)s")

# Diretório temporário para salvar mídias
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

# Arquivo de retomada (resume)
RESUME_FILE = "resume.json"

# Intervalo entre envios (em segundos) - ajustado para nao disparar flood
MEDIA_DELAY = 2    # 2s entre midias
TEXT_DELAY = 0.5   # 0.5s entre textos

# Formata bytes para exibicao humana
def fmt_size(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f}MB"
    return f"{b / 1024:.0f}KB"

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

# ============================================================
# Retomada (resume): salva e carrega progresso
# ============================================================

def save_resume(data):
    """Salva estado da clonagem para retomada futura."""
    try:
        all_resumes = {}
        if os.path.exists(RESUME_FILE):
            with open(RESUME_FILE, "r") as f:
                all_resumes = json.load(f)
        all_resumes[str(data["origin_chat"])] = {
            "destination_chat": data["destination_chat"],
            "chat_type": data["chat_type"],
            "origin_title": data.get("origin_title", ""),
            "topic_map": {str(k): v for k, v in data.get("topic_map", {}).items()},
            "cloned_msg_ids": sorted(data.get("cloned_msg_ids", [])),
            "total_msgs": data.get("total_msgs", 0),
            "skipped_count": data.get("skipped_count", 0),
            "cloned_count": data.get("cloned_count", 0),
            "failed_count": data.get("failed_count", 0),
            "content_types": data.get("content_types", []),
        }
        with open(RESUME_FILE, "w") as f:
            json.dump(all_resumes, f)
    except Exception as e:
        tqdm.write(f"  ⚠ Erro ao salvar resume: {e}")

def load_resume(origin_chat):
    """Carrega estado salvo para o chat de origem, ou None se não existir."""
    if not os.path.exists(RESUME_FILE):
        return None
    try:
        with open(RESUME_FILE, "r") as f:
            all_resumes = json.load(f)
        key = str(origin_chat)
        if key not in all_resumes:
            return None
        data = all_resumes[key]
        data["origin_chat"] = origin_chat
        data["topic_map"] = {int(k): v for k, v in data.get("topic_map", {}).items()}
        data["cloned_msg_ids"] = set(data.get("cloned_msg_ids", []))
        return data
    except Exception as e:
        print(f"  ⚠ Erro ao carregar resume: {e}")
        return None

def delete_resume(origin_chat):
    """Remove o resume de um chat específico."""
    if not os.path.exists(RESUME_FILE):
        return
    try:
        with open(RESUME_FILE, "r") as f:
            all_resumes = json.load(f)
        all_resumes.pop(str(origin_chat), None)
        with open(RESUME_FILE, "w") as f:
            json.dump(all_resumes, f)
    except Exception:
        pass

# ============================================================
# SEÇÃO 1: Detecção do tipo de chat de origem
# ============================================================

def get_chat_info(client, chat_id):
    """Detecta tipo do chat (canal, grupo, supergrupo, forum), proteção e atributos."""
    try:
        entity = client.get_entity(chat_id)
    except Exception as e:
        print(f"\n❌ Não foi possível acessar o chat {chat_id}")
        print(f"Detalhes: {e}")
        exit()

    info = {
        "entity": entity,
        "title": getattr(entity, 'title', None) or getattr(entity, 'first_name', ''),
        "id": entity.id,
        "is_protected": False,
        "is_forum": False,
        "type": "channel",
        "type_label": "Canal",
    }

    if isinstance(entity, Chat):
        info["type"] = "group"
        info["type_label"] = "Grupo Comum"
        try:
            full = client(GetFullChatRequest(chat_id=entity.id))
            fc = full.full_chat
            if hasattr(fc, 'noforwards') and fc.noforwards:
                info["is_protected"] = True
        except Exception:
            pass
    elif isinstance(entity, Channel):
        if getattr(entity, 'megagroup', False):
            if getattr(entity, 'forum', False):
                info["type"] = "forum"
                info["type_label"] = "Supergrupo com Tópicos (Fórum)"
                info["is_forum"] = True
            else:
                info["type"] = "supergroup"
                info["type_label"] = "Supergrupo"
        else:
            info["type"] = "channel"
            info["type_label"] = "Canal"

        try:
            full = client(GetFullChannelRequest(entity))
            fc = full.full_chat
            if hasattr(fc, 'noforwards') and fc.noforwards:
                info["is_protected"] = True
            if hasattr(fc, 'restricted') and fc.restricted:
                info["is_protected"] = True
            if hasattr(fc, 'protected') and fc.protected:
                info["is_protected"] = True
        except Exception:
            pass

    print(f"\n{Fore.CYAN}Chat detectado: {info['title']}{Style.RESET_ALL}")
    print(f"  Tipo: {info['type_label']}")
    print(f"  ID: {info['id']}")
    if info["is_protected"]:
        print(f"  {Fore.YELLOW}Proteção de conteúdo: ATIVADA{Style.RESET_ALL}")
    else:
        print(f"  Proteção de conteúdo: desativada")
    if info["is_forum"]:
        print(f"  Tópicos: SIM")

    return info

# ============================================================
# SEÇÃO 2: Criação do destino compatível
# ============================================================

def create_destination(client, chat_info):
    """Cria destino com mesmo tipo da origem (canal, supergrupo, grupo ou fórum)."""
    title = f"{chat_info['title']} - Clone"
    about = "Chat gerado automaticamente para clonagem de mensagens."

    type_label = {"channel": "Canal", "group": "Grupo", "supergroup": "Supergrupo", "forum": "Fórum"}

    try:
        if chat_info["type"] == "channel":
            result = client(CreateChannelRequest(
                title=title, about=about, megagroup=False
            ))
        elif chat_info["type"] in ("group", "supergroup"):
            result = client(CreateChannelRequest(
                title=title, about=about, megagroup=True
            ))
        elif chat_info["type"] == "forum":
            result = client(CreateChannelRequest(
                title=title, about=about, megagroup=True, forum=True
            ))
        else:
            result = client(CreateChannelRequest(
                title=title, about=about, megagroup=False
            ))

        dest_id = result.chats[0].id
        label = type_label.get(chat_info["type"], "Chat")
        print(f"\n{Fore.GREEN}{label} de destino criado!{Style.RESET_ALL}")
        print(f"  Nome: {title}")
        print(f"  ID: {dest_id}")

        # Verifica se foi realmente criado
        try:
            verify = client.get_entity(dest_id)
            actual_forum = getattr(verify, 'forum', False)
            print(f"  Verificacao: entidade existe, forum={actual_forum}")
        except Exception:
            print(f"  {Fore.YELLOW}Aviso: nao foi possivel verificar entidade{Style.RESET_ALL}")

        return dest_id
    except Exception as e:
        print(f"\n❌ Não foi possível criar o destino.")
        print(f"Motivos possíveis:")
        print(f"- Sua conta pode não ter permissão para criar este tipo de chat")
        print(f"- O nome do chat pode estar em uso")
        print(f"- Limite diario de criacao de grupos atingido (max 10/dia)")
        print(f"Detalhes técnicos: {e}")
        logging.error(f"Erro ao criar destino: {e}")
        exit()

# ============================================================
# SEÇÃO 3: Tópicos (enumeração, criação, mapeamento)
# ============================================================

def setup_topics(client, origin_chat_id, dest_chat_id, origin_title):
    """Enumera tópicos do fórum de origem e cria no destino.
    Retorna topic_map: {orig_topic_id: dest_msg_id}
    O valor é um MESSAGE ID (top_message) dentro do tópico destino,
    usado no parametro reply_to para rotear mensagens ao tópico correto.
    O tópico Geral (id=1) NAO entra no mapa — mensagens sem reply_to vao para ele."""
    topic_map = {}
    print(f"\n{Fore.CYAN}=== Tópicos do Fórum ==={Style.RESET_ALL}")
    print("Enumerando tópicos da origem...")

    try:
        result = client(GetForumTopicsRequest(
            channel=origin_chat_id,
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=100
        ))
        source_topics = result.topics
        print(f"  {len(source_topics)} tópicos encontrados (incluindo Geral).")

        if len(source_topics) <= 1:
            print("  Apenas o tópico Geral existe. Nada a criar.")
            return topic_map

        # Cria os tópicos no destino e captura o message ID de cada um
        print("\nCriando tópicos no destino...")
        created_msg_ids = {}  # {source_topic_id: dest_topic_msg_id}

        for topic in source_topics:
            if topic.id == 1:
                continue

            try:
                icon_color = getattr(topic, 'icon_color', 0x6FB9F0)
                icon_emoji_id = getattr(topic, 'icon_emoji_id', None)
                response = client(CreateForumTopicRequest(
                    channel=dest_chat_id,
                    title=topic.title,
                    icon_color=icon_color,
                    icon_emoji_id=icon_emoji_id,
                    random_id=random.randint(1, 2**63 - 1)
                ))
                # Extrai o message ID da criacao do topico (ancora do topico)
                topic_msg_id = 0
                for update in response.updates:
                    if isinstance(update, UpdateMessageID):
                        topic_msg_id = update.id
                        break
                if topic_msg_id:
                    created_msg_ids[topic.id] = topic_msg_id
                    print(f"  Tópico '{topic.title}' criado (msg_id={topic_msg_id})")
                else:
                    print(f"  {Fore.YELLOW}Tópico '{topic.title}' criado mas msg_id nao capturado{Style.RESET_ALL}")
                time.sleep(0.3)
            except FloodWaitError as e:
                print(f"  ⏳ Aguardando {e.seconds}s (FloodWait)...")
                time.sleep(e.seconds)
                try:
                    response = client(CreateForumTopicRequest(
                        channel=dest_chat_id,
                        title=topic.title,
                        icon_color=icon_color,
                        icon_emoji_id=icon_emoji_id,
                        random_id=random.randint(1, 2**63 - 1)
                    ))
                    topic_msg_id = 0
                    for update in response.updates:
                        if isinstance(update, UpdateMessageID):
                            topic_msg_id = update.id
                            break
                    if topic_msg_id:
                        created_msg_ids[topic.id] = topic_msg_id
                    print(f"  Tópico '{topic.title}' criado (após espera, msg_id={topic_msg_id})")
                except Exception as e2:
                    print(f"  {Fore.RED}Falha ao criar '{topic.title}': {e2}{Style.RESET_ALL}")
                    logging.error(f"Erro criar tópico {topic.title}: {e2}")
            except Exception as e:
                print(f"  {Fore.RED}Falha ao criar '{topic.title}': {e}{Style.RESET_ALL}")
                logging.error(f"Erro criar tópico {topic.title}: {e}")

        # Se algum topico ficou sem msg_id, tenta pegar via GetForumTopicsRequest
        missing = [t for t in source_topics if t.id != 1 and t.id not in created_msg_ids]
        if missing:
            print("\nBuscando message IDs complementares...")
            try:
                dest_result = client(GetForumTopicsRequest(
                    channel=dest_chat_id,
                    offset_date=None,
                    offset_id=0,
                    offset_topic=0,
                    limit=100
                ))
                dest_by_title = {}
                for dt in dest_result.topics:
                    if dt.top_message and dt.top_message > 0:
                        dest_by_title[dt.title] = dt.top_message

                for topic in missing:
                    msg_id = dest_by_title.get(topic.title, 0)
                    if msg_id:
                        created_msg_ids[topic.id] = msg_id
                        print(f"  '{topic.title}' → msg_id={msg_id} (via top_message)")
                    else:
                        print(f"  {Fore.YELLOW}'{topic.title}' sem msg_id no destino{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.RED}Erro ao buscar msg_ids complementares: {e}{Style.RESET_ALL}")

        # Monta o mapeamento final usando o msg_id de criacao do topico
        # (mensagem de servico MessageActionTopicCreate).
        # Esse ID serve como ancora do topico: enviar com reply_to=ancora
        # posta no topico sem criar thread visivel (msg de servico nao gera reply).
        print(f"\n{Fore.GREEN}Mapeamento origem → destino (msg de criacao como ancora):{Style.RESET_ALL}")
        for topic in source_topics:
            if topic.id == 1:
                continue
            topic_msg_id = created_msg_ids.get(topic.id, 0)
            if topic_msg_id:
                topic_map[topic.id] = topic_msg_id
                print(f"  '{topic.title}' → reply_to={topic_msg_id}")
            else:
                print(f"  {Fore.YELLOW}'{topic.title}' — nao mapeado{Style.RESET_ALL}")

        # Verifica se os topicos realmente foram criados no destino
        try:
            dest_verify = client(GetForumTopicsRequest(
                channel=dest_chat_id, offset_date=None,
                offset_id=0, offset_topic=0, limit=100
            ))
            print(f"\n  Verificacao: {len(dest_verify.topics)} topicos no destino")
        except Exception as ve:
            print(f"  {Fore.YELLOW}Aviso: nao foi possivel verificar topicos no destino: {ve}{Style.RESET_ALL}")

    except Exception as e:
        print(f"  {Fore.YELLOW}Não foi possível enumerar tópicos: {e}{Style.RESET_ALL}")
        print(f"  O chat será tratado como supergrupo normal.")
        logging.error(f"Erro ao enumerar tópicos: {e}")

    return topic_map

# ============================================================
# SEÇÃO 4: Busca de menu (mensagem fixada/pinada)
# ============================================================

def get_menu_from_chat(client, chat_id, chat_info):
    """Busca mensagem fixada ou palavras-chave de menu no chat de origem."""
    try:
        if chat_info["type"] in ("channel", "supergroup", "forum"):
            full_channel = client(GetFullChannelRequest(chat_id))
            pinned_msg_id = getattr(full_channel.full_chat, 'pinned_msg_id', None)
        elif chat_info["type"] == "group":
            try:
                full_chat = client(GetFullChatRequest(chat_id=chat_info["entity"].id))
                pinned_msg_id = getattr(full_chat.full_chat, 'pinned_msg_id', None)
            except Exception:
                pinned_msg_id = None
        else:
            pinned_msg_id = None

        if pinned_msg_id:
            pinned_msg = client.get_messages(chat_id, ids=pinned_msg_id)
            if pinned_msg and (pinned_msg.text or pinned_msg.message):
                return (pinned_msg.text or pinned_msg.message, pinned_msg.id)

        keywords = ["menu", "navegação", "clique aqui", "#", "conteúdo"]
        for message in client.iter_messages(chat_id, limit=10):
            content = (message.text or message.message or "").lower()
            if any(kw in content for kw in keywords):
                if len(content) > 100 or content.count("#") > 3 or content.count("http") > 2:
                    return (message.text or message.message, message.id)
        return (None, None)
    except Exception as e:
        logging.error(f"Erro ao buscar menu: {e}")
        return (None, None)

# ============================================================
# SEÇÃO 5: Verificação de proteção de conteúdo
# ============================================================

def is_content_protected(client, chat_id):
    """Verifica se o chat possui proteção de conteúdo ativada."""
    try:
        info = get_chat_info(client, chat_id)
        return info["is_protected"]
    except Exception as e:
        logging.error(f"Erro ao verificar proteção de conteúdo: {e}")
        return False

# ============================================================
# SEÇÃO 6: Menu de seleção de tipo de conteúdo
# ============================================================

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

# ============================================================
# SEÇÃO 7: Função principal de clonagem
# ============================================================

def main():
    print_ascii_art()
    print("\nIniciando a clonagem de mensagens...\n")

    # Coleta de credenciais
    api_id, api_hash = get_api_credentials()

    # Carrega/gerencia sessao como string para compartilhar entre clientes
    session_file = "session.txt"
    if os.path.exists(session_file):
        with open(session_file) as f:
            session_str = f.read().strip()
    else:
        session_str = ""

    client = TelegramClient(StringSession(session_str), api_id, api_hash,
                            connection_retries=5, request_retries=5)
    client.start()
    session_str = client.session.save()
    with open(session_file, "w") as f:
        f.write(session_str)
    print("Conexão estabelecida com sucesso.")

    executor = ThreadPoolExecutor(max_workers=1)

    # Entrada de dados
    origin_chat = input("Digite o ID do chat de origem (ID numérico): ").strip()
    try:
        origin_chat = int(origin_chat)
    except ValueError:
        print("O ID do chat de origem deve ser um número inteiro.")
        exit()

    # ================================================================
    # PASSO 1: Detecta tipo do chat, proteção e atributos
    # ================================================================
    chat_info = get_chat_info(client, origin_chat)

    if chat_info["is_protected"]:
        print(f"\n{Fore.YELLOW}Atenção: proteção de conteúdo detectada no chat de origem.")
        print("Mídias serão baixadas localmente e reenviadas. Caso o download falhe, apenas o texto será clonado.{Style.RESET_ALL}")

    # ================================================================
    # PASSO 1.5: Verifica se há retomada (resume) salva
    # ================================================================
    resume_data = load_resume(origin_chat)
    resuming = False
    if resume_data:
        print(f"\n{Fore.CYAN}Retomada encontrada para este chat:{Style.RESET_ALL}")
        print(f"  Destino: {resume_data['destination_chat']}")
        print(f"  Já clonadas: {len(resume_data['cloned_msg_ids'])} de {resume_data['total_msgs']} msgs")
        resp = input("\nRetomar de onde parou? (s/n): ").strip().lower()
        if resp == "s":
            resuming = True
            destination_chat = resume_data["destination_chat"]
            # Garante que a entidade de destino esta no cache da sessao
            try:
                client.get_entity(destination_chat)
            except Exception:
                # Tenta com prefixo -100 (supergrupo/canal)
                try:
                    client.get_entity(int(f"-100{destination_chat}"))
                    destination_chat = int(f"-100{destination_chat}")
                except Exception:
                    print(f"  {Fore.YELLOW}Aviso: nao foi possivel acessar o destino {destination_chat}{Style.RESET_ALL}")
            topic_map = resume_data.get("topic_map", {})
            content_types = resume_data.get("content_types", [])
            if content_types:
                print(f"  Tipos de conteúdo: {content_types}")
            else:
                content_types = []
            print(f"\n{Fore.GREEN}Retomando clonagem...{Style.RESET_ALL}")
        else:
            delete_resume(origin_chat)
            resume_data = None
            print("Iniciando nova clonagem.")

    # ================================================================
    # PASSO 2: Cria o destino com o mesmo tipo
    # ================================================================
    if not resuming:
        destination_chat = create_destination(client, chat_info)

    # ================================================================
    # PASSO 3: Se for fórum, clona os tópicos
    # ================================================================
    if not resuming:
        topic_map = {}
        if chat_info["is_forum"]:
            topic_map = setup_topics(client, origin_chat, destination_chat, chat_info["title"])
            if len(topic_map) > 0:
                print(f"\n{Fore.GREEN}{len(topic_map)} tópicos criados no destino.{Style.RESET_ALL}")
    else:
        print(f"  Tópicos carregados do resume: {len(topic_map)} mapeamentos")

    # ================================================================
    # PASSO 4: Seleciona tipo de conteúdo
    # ================================================================
    if not resuming:
        content_types = select_content_type()

    # ================================================================
    # PASSO 5: Obtém histórico de mensagens
    # ================================================================
    print("\nObtendo histórico de mensagens...")
    messages = list(client.iter_messages(origin_chat, limit=None))
    print(f"Total de mensagens encontradas: {len(messages)}")
    total_messages = len(messages)

    # Debug RAW: mostra estrutura do reply_to das primeiras msgs com reply
    if chat_info["is_forum"]:
        count = 0
        for m in messages:
            if getattr(m, 'reply_to', None) and count < 10:
                rt = m.reply_to
                tqdm.write(f"  [RAW] msg {m.id} reply_to type={type(rt).__name__} "
                           f"top_id={getattr(rt, 'reply_to_top_id', '??')} "
                           f"msg_id={getattr(rt, 'reply_to_msg_id', '??')}")
                count += 1
        tqdm.write(f"  [RAW] topic_map keys={list(topic_map.keys())[:5]}...")

    # Busca o menu antes de clonar as mensagens
    menu, menu_id = get_menu_from_chat(client, origin_chat, chat_info)

    # ================================================================
    # PASSO 6: Pipeline de clonagem
    # ================================================================

    # Contadores + estado
    if resuming and resume_data:
        cloned_ids = resume_data.get("cloned_msg_ids", set())
        cloned_count = resume_data.get("cloned_count", 0)
        skipped_count = resume_data.get("skipped_count", 0)
        failed_count = resume_data.get("failed_count", 0)
    else:
        cloned_ids = set()
        cloned_count = 0
        skipped_count = 0
        failed_count = 0
    chat_protected = chat_info["is_protected"]
    msg_id_map = {}  # {source_msg_id: dest_msg_id} para preservar reply chain

    ext_map = {"photo": ".jpg", "video": ".mp4", "audio": ".ogg", "document": "", "sticker": ".webp"}

    def _get_msg_text(msg):
        return (getattr(msg, 'text', None) or
                getattr(msg, 'message', None) or
                getattr(msg, 'caption', None) or "")

    def _has_media(msg, ct):
        return (("photo" in ct and msg.photo) or
                ("video" in ct and msg.video) or
                ("audio" in ct and msg.audio) or
                ("document" in ct and msg.document) or
                ("sticker" in ct and msg.sticker))

    def _get_media(msg, ct):
        if "photo" in ct and msg.photo:
            return "photo", msg.photo
        if "video" in ct and msg.video:
            return "video", msg.video
        if "audio" in ct and msg.audio:
            return "audio", msg.audio
        if "document" in ct and msg.document:
            return "document", msg.document
        if "sticker" in ct and msg.sticker:
            return "sticker", msg.sticker
        return None, None

    def _resolve_reply_target(msg, topic_map, msg_id_map):
        """Determina o reply_to correto para preservar tópicos e reply chain."""
        reply_to = None
        reply_info = getattr(msg, 'reply_to', None)

        if reply_info is None:
            return None

        reply_to_top_id = getattr(reply_info, 'reply_to_top_id', None)
        reply_to_msg_id = getattr(reply_info, 'reply_to_msg_id', None)

        # Se a mensagem responde a outra mensagem clonada, usa o ID mapeado
        if reply_to_msg_id and reply_to_msg_id in msg_id_map:
            return msg_id_map[reply_to_msg_id]

        # Se pertence a um tópico, usa o ID do tópico no destino
        if reply_to_top_id and reply_to_top_id in topic_map:
            return topic_map[reply_to_top_id]

        # Se responde a uma mensagem não clonada mas tem tópico, usa o tópico
        if reply_to_msg_id and reply_to_top_id and reply_to_top_id in topic_map:
            return topic_map[reply_to_top_id]

        return None

    # Pre-filtra mensagens nao-servico em ordem cronologica
    ordered = [m for m in reversed(messages) if not isinstance(m, MessageService)]
    skipped_count = total_messages - len(ordered)

    # Para forums, agrupa mensagens por topico de origem
    batches = []
    if chat_info["is_forum"] and topic_map:
        topic_buckets = {}  # {source_topic_id: [msgs]}
        general_msgs = []
        for m in ordered:
            rt = getattr(m, 'reply_to', None)
            if rt is None:
                general_msgs.append(m)
                continue
            tid = getattr(rt, 'reply_to_top_id', None)
            mid = getattr(rt, 'reply_to_msg_id', None)
            # Alguns foruns usam reply_to_top_id, outros reply_to_msg_id
            # como identificador do topico
            matched = False
            if tid and tid in topic_map:
                topic_buckets.setdefault(tid, []).append(m)
                matched = True
            elif mid and mid in topic_map:
                topic_buckets.setdefault(mid, []).append(m)
                matched = True
            if not matched:
                general_msgs.append(m)

        if general_msgs:
            batches.append(("Geral", None, general_msgs))
            tqdm.write(f"  lote Geral: {len(general_msgs)} msgs (sem reply_to)")
        for tid in topic_map:
            if tid == 1:
                continue
            msgs = topic_buckets.get(tid, [])
            dest_target = topic_map[tid]
            batches.append((f"topic_{tid}", dest_target, msgs))
            tqdm.write(f"  lote topico {tid} → reply_to={dest_target}: {len(msgs)} msgs")
    else:
        batches = [(None, None, ordered)]

    total_msgs_to_process = sum(len(b[2]) for b in batches)
    tqdm.write(f"Total a processar: {total_msgs_to_process} msgs em {len(batches)} lote(s)")

    # Pipeline: future da proxima midia sendo baixada em background
    next_dl_future = None
    next_dl_info = None   # (filepath, media_type, text, msg_id)

    with tqdm(total=total_messages, desc="Clonando", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}",
              colour="magenta", initial=skipped_count) as progress:

        # ================================================================
        # Helper: salva progresso para retomada (debounced a cada 20 msgs)
        # ================================================================
        _save_counter = [0]

        def _save_resume_progress():
            nonlocal cloned_count, skipped_count, failed_count
            _save_counter[0] += 1
            if _save_counter[0] % 20 == 0:
                resume_info = {
                    "origin_chat": origin_chat,
                    "destination_chat": destination_chat,
                    "chat_type": chat_info["type"],
                    "origin_title": chat_info["title"],
                    "topic_map": topic_map,
                    "cloned_msg_ids": cloned_ids,
                    "total_msgs": total_messages,
                    "skipped_count": skipped_count,
                    "cloned_count": cloned_count,
                    "failed_count": failed_count,
                    "content_types": content_types,
                }
                save_resume(resume_info)

        def _save_resume_now():
            """Força save imediato (usado no fim de cada lote)."""
            resume_info = {
                "origin_chat": origin_chat,
                "destination_chat": destination_chat,
                "chat_type": chat_info["type"],
                "origin_title": chat_info["title"],
                "topic_map": topic_map,
                "cloned_msg_ids": cloned_ids,
                "total_msgs": total_messages,
                "skipped_count": skipped_count,
                "cloned_count": cloned_count,
                "failed_count": failed_count,
                "content_types": content_types,
            }
            save_resume(resume_info)

        # ================================================================
        # Funções internas do pipeline
        # ================================================================

        def _send_text(msg_id, text, reply_to=None):
            nonlocal cloned_count
            kwargs = {}
            if reply_to is not None:
                kwargs["reply_to"] = reply_to
            sent = client.send_message(destination_chat, text, **kwargs)
            cloned_ids.add(msg_id)
            cloned_count += 1
            _save_resume_progress()
            return sent.id if sent else None

        def _ffmpeg_to_streaming(input_path, output_path, msg_id, duration=None):
            if not os.path.exists(input_path):
                return False

            if not shutil.which("ffmpeg"):
                tqdm.write(f"  FFmpeg nao encontrado, enviando video original msg {msg_id}")
                return False

            tqdm.write(f"  Processando video msg {msg_id} (ffmpeg)...")

            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
                "-pix_fmt", "yuv420p",
                "-vf", "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease",
                "-r", "30",
                "-crf", "23", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                "-movflags", "+faststart",
                output_path
            ]

            proc = None
            try:
                proc = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                        universal_newlines=True, bufsize=1)
            except FileNotFoundError:
                tqdm.write(f"  FFmpeg nao encontrado, enviando original msg {msg_id}")
                return False
            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

            total_sec = None
            if duration is not None:
                total_sec = duration

            for line in proc.stderr:
                match = time_pattern.search(line)
                if match:
                    h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
                    current_sec = h * 3600 + m * 60 + s
                    if total_sec is None:
                        total_sec = current_sec
                    pct = (current_sec / total_sec * 100) if total_sec > 0 else 0
                    progress.set_description(
                        f"Msg {msg_id} ffmpeg {pct:.0f}%"
                    )

            proc.wait()
            if proc.returncode != 0:
                tqdm.write(f"  FFmpeg falhou na msg {msg_id}, enviando original")
                return False
            return True

        def _download_sync(client_instance, media_obj, filepath, msg_id, media_type):
            dl_start = time.time()

            def dl_cb(current, total):
                elapsed = time.time() - dl_start or 0.001
                speed = current / elapsed
                pct = current / total * 100 if total else 0
                progress.set_description(
                    f"Msg {msg_id} {pct:.0f}% ({fmt_size(current)}/{fmt_size(total)})"
                    f" {fmt_size(speed)}/s"
                )

            client_instance.download_media(media_obj, file=filepath,
                                           progress_callback=dl_cb)

        def _upload(path, media_type, text, msg_id, reply_to=None):
            nonlocal cloned_count
            if not os.path.exists(path):
                return None
            file_sz = fmt_size(os.path.getsize(path))
            tqdm.write(f"  Enviando msg {msg_id} ({file_sz})...")

            up_start = time.time()

            def up_cb(current, total):
                elapsed = time.time() - up_start or 0.001
                speed = current / elapsed
                pct = current / total * 100 if total else 0
                progress.set_description(
                    f"Msg {msg_id} {pct:.0f}% ({fmt_size(current)}/{fmt_size(total)})"
                    f" {fmt_size(speed)}/s"
                )

            kwargs = {"caption": text, "progress_callback": up_cb} if text else {"progress_callback": up_cb}
            if media_type == "video":
                kwargs["supports_streaming"] = True
            if reply_to is not None:
                kwargs["reply_to"] = reply_to
            sent = client.send_file(destination_chat, path, **kwargs)
            cloned_ids.add(msg_id)
            cloned_count += 1
            _save_resume_progress()
            tqdm.write(f"  Msg {msg_id} enviada ({file_sz})")
            return sent.id if sent else None

        def _send_anonymous(msg, reply_to=None):
            """Envia mensagem anonimamente (sem forward) reaproveitando referência da mídia."""
            kwargs = {}
            if reply_to is not None:
                kwargs["reply_to"] = reply_to
            text_content = _get_msg_text(msg)

            try:
                if msg.photo and "photo" in content_types:
                    kwargs["caption"] = text_content
                    sent = client.send_file(destination_chat, msg.photo, **kwargs)
                elif msg.document and _has_media(msg, content_types):
                    kwargs["caption"] = text_content
                    if msg.video:
                        kwargs["supports_streaming"] = True
                    sent = client.send_file(destination_chat, msg.document, **kwargs)
                elif text_content:
                    sent = client.send_message(destination_chat, text_content, **kwargs)
                else:
                    return None

                if sent:
                    nonlocal cloned_count
                    cloned_ids.add(msg.id)
                    cloned_count += 1
                    _save_resume_progress()
                    return sent.id
            except RPCError as e:
                err = str(e).lower()
                if "protected" in err or "restricted" in err or "noforwards" in err:
                    nonlocal chat_protected
                    chat_protected = True
                    tqdm.write(f"  Msg {msg.id}: proteção detectada no envio, baixando midia localmente")
                else:
                    raise
            except FloodWaitError:
                raise
            except Exception:
                raise
            return None

        # ================================================================
        # LOOP PRINCIPAL: processa por lotes (topicos)
        # ================================================================

        try:
            for batch_name, batch_reply_to, batch_msgs in batches:
                if batch_name:
                    tqdm.write(f"\n--- Lote: {batch_name} (reply_to={batch_reply_to}) ---")

                for i, message in enumerate(batch_msgs):
                    msg_id = message.id

                    # Pula mensagem ja clonada (retomada)
                    if msg_id in cloned_ids:
                        progress.update(1)
                        continue

                    temp_filepath = None
                    ffmpeg_out = None
                    text_content = _get_msg_text(message)

                    # Determina reply_to: se for forum, usa o reply_to do lote (topico)
                    # mas preserva reply chain se msg responde a outra ja clonada
                    if batch_reply_to is not None:
                        reply_to = batch_reply_to
                        rt = getattr(message, 'reply_to', None)
                        reply_msg_id = getattr(rt, 'reply_to_msg_id', None) if rt else None
                        if reply_msg_id and reply_msg_id in msg_id_map:
                            reply_to = msg_id_map[reply_msg_id]
                            tqdm.write(f"  [reply] msg {msg_id} responde a {reply_msg_id} → reply_to={reply_to}")
                    else:
                        reply_to = None

                    try:
                        media_type, media_obj = None, None
                        if "photo" in content_types and message.photo:
                            media_type, media_obj = "photo", message.photo
                        elif "video" in content_types and message.video:
                            media_type, media_obj = "video", message.video
                        elif "audio" in content_types and message.audio:
                            media_type, media_obj = "audio", message.audio
                        elif "document" in content_types and message.document:
                            media_type, media_obj = "document", message.document
                        elif "sticker" in content_types and message.sticker:
                            media_type, media_obj = "sticker", message.sticker

                        # ----------------------------------------------------------
                        # ESTRATÉGIA A: Chat NÃO protegido → envio anônimo (rápido)
                        # ----------------------------------------------------------
                        if not chat_protected:
                            sent_id = None
                            try:
                                sent_id = _send_anonymous(message, reply_to)
                            except FloodWaitError as e:
                                tqdm.write(f"  FloodWait {e.seconds}s msg {msg_id}")
                                time.sleep(e.seconds)
                                try:
                                    sent_id = _send_anonymous(message, reply_to)
                                except Exception:
                                    failed_count += 1
                                    progress.update(1)
                                    continue
                            except RPCError as e:
                                tqdm.write(f"  Erro RPC msg {msg_id}: {e}")
                                logging.error(f"Erro RPC msg {msg_id}: {e}")
                                failed_count += 1
                                progress.update(1)
                                continue
                            except Exception as e:
                                tqdm.write(f"  Erro msg {msg_id}: {e}")
                                logging.error(f"Erro inesperado msg {msg_id}: {e}")
                                failed_count += 1
                                progress.update(1)
                                continue

                            if sent_id is not None:
                                msg_id_map[msg_id] = sent_id
                                if media_obj:
                                    time.sleep(MEDIA_DELAY)
                                else:
                                    time.sleep(TEXT_DELAY)
                            else:
                                skipped_count += 1
                            progress.update(1)
                            continue

                        # ----------------------------------------------------------
                        # ESTRATÉGIA B: Chat protegido → download + reupload
                        # ----------------------------------------------------------

                        if media_obj is not None:
                            ext = ext_map.get(media_type, "")
                            filename = f"{origin_chat}_{msg_id}{ext}"
                            temp_filepath = os.path.join(TEMP_DIR, filename)

                            tqdm.write(f"  Baixando msg {msg_id} ({media_type})...")

                            try:
                                _download_sync(client, media_obj, temp_filepath, msg_id, media_type)
                            except FloodWaitError as e:
                                tqdm.write(f"  FloodWait {e.seconds}s download msg {msg_id}")
                                time.sleep(e.seconds)
                                try:
                                    _download_sync(client, media_obj, temp_filepath, msg_id, media_type)
                                except Exception:
                                    failed_count += 1
                                    if text_content:
                                        tqdm.write(f"  Falha download, enviando texto msg {msg_id}")
                                        sent_id = _send_text(msg_id, text_content, reply_to)
                                        if sent_id:
                                            msg_id_map[msg_id] = sent_id
                                    else:
                                        skipped_count += 1
                                    progress.update(1)
                                    if temp_filepath and os.path.exists(temp_filepath):
                                        os.remove(temp_filepath)
                                    continue
                            except Exception as dl_err:
                                err = str(dl_err).lower()
                                if "protected" in err or "restricted" in err or "noforwards" in err:
                                    chat_protected = True
                                    tqdm.write(f"  Download msg {msg_id} bloqueado (protegido)")
                                else:
                                    tqdm.write(f"  Erro download msg {msg_id}: {dl_err}")
                                    logging.error(f"Erro download msg {msg_id}: {dl_err}")

                                if media_type == "sticker":
                                    skipped_count += 1
                                elif text_content:
                                    sent_id = _send_text(msg_id, text_content, reply_to)
                                    if sent_id:
                                        msg_id_map[msg_id] = sent_id
                                    tqdm.write(f"  Texto msg {msg_id} enviado (fallback)")
                                else:
                                    skipped_count += 1
                                progress.update(1)
                                if temp_filepath and os.path.exists(temp_filepath):
                                    os.remove(temp_filepath)
                                continue

                            # -- FFMPEG: otimiza video para streaming --
                            upload_path = temp_filepath
                            ffmpeg_out = None
                            if media_type == "video" and os.path.exists(temp_filepath):
                                ffmpeg_out = temp_filepath + ".stream.mp4"
                                if _ffmpeg_to_streaming(temp_filepath, ffmpeg_out, msg_id):
                                    upload_path = ffmpeg_out
                                else:
                                    if os.path.exists(ffmpeg_out):
                                        os.remove(ffmpeg_out)
                                    ffmpeg_out = None

                            # -- PIPELINE: sobe a midia atual enquanto baixa a proxima em background --
                            next_media_idx = None
                            for j in range(i + 1, len(batch_msgs)):
                                nm = batch_msgs[j]
                                if _has_media(nm, content_types):
                                    next_media_idx = j
                                    break

                            if next_media_idx is not None:
                                nm = batch_msgs[next_media_idx]
                                nm_text = _get_msg_text(nm)
                                nm_mt, nm_mo = _get_media(nm, content_types)
                                nm_ext = ext_map.get(nm_mt, "")
                                nm_fp = os.path.join(TEMP_DIR, f"{origin_chat}_{nm.id}{nm_ext}")

                                tqdm.write(f"  [bg] Baixando proxima msg {nm.id} ({nm_mt})...")

                                def _bg_download(mo=nm_mo, fp=nm_fp, mid=nm.id, mt=nm_mt,
                                                 ss=session_str, aid=api_id, ah=api_hash):
                                    import asyncio
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    bg = TelegramClient(StringSession(ss), aid, ah)
                                    bg.connect()
                                    try:
                                        _download_sync(bg, mo, fp, mid, mt)
                                    finally:
                                        bg.disconnect()
                                        loop.close()

                                next_dl_future = executor.submit(_bg_download)
                                next_dl_info = (nm_fp, nm_mt, nm_text, nm.id)

                            sent_id = _upload(upload_path, media_type, text_content, msg_id, reply_to)
                            if sent_id:
                                msg_id_map[msg_id] = sent_id
                                os.remove(upload_path)
                                time.sleep(MEDIA_DELAY)
                            if ffmpeg_out and os.path.exists(ffmpeg_out):
                                os.remove(ffmpeg_out)
                            progress.update(1)

                            # Aguarda o download em background da proxima midia
                            if next_dl_future is not None:
                                try:
                                    next_dl_future.result()
                                except Exception as bg_err:
                                    tqdm.write(f"  Erro download bg: {bg_err}")
                                    if next_dl_info:
                                        fp = next_dl_info[0]
                                        if fp and os.path.exists(fp):
                                            os.remove(fp)
                                finally:
                                    next_dl_future = None
                                    next_dl_info = None

                        elif text_content:
                            sent_id = _send_text(msg_id, text_content, reply_to)
                            if sent_id:
                                msg_id_map[msg_id] = sent_id
                            progress.update(1)
                            time.sleep(TEXT_DELAY)
                        else:
                            skipped_count += 1
                            progress.update(1)

                    except FloodWaitError as e:
                        tqdm.write(f"  FloodWait {e.seconds}s, aguardando...")
                        time.sleep(e.seconds)
                        failed_count += 1
                        progress.update(1)
                    except RPCError as e:
                        err = str(e).lower()
                        if "protected" in err or "restricted" in err or "noforwards" in err:
                            chat_protected = True
                            if text_content:
                                try:
                                    sent_id = _send_text(msg_id, text_content, reply_to)
                                    if sent_id:
                                        msg_id_map[msg_id] = sent_id
                                    tqdm.write(f"  Msg {msg_id}: midia protegida, texto enviado")
                                except Exception:
                                    failed_count += 1
                            else:
                                skipped_count += 1
                        else:
                            tqdm.write(f"  Erro RPC msg {msg_id}: {e}")
                            logging.error(f"Erro RPC msg {msg_id}: {e}")
                            failed_count += 1
                        progress.update(1)
                    except Exception as e:
                        tqdm.write(f"  Erro msg {msg_id}: {e}")
                        logging.error(f"Erro inesperado msg {msg_id}: {e}")
                        failed_count += 1
                        progress.update(1)
                    finally:
                        if temp_filepath and os.path.exists(temp_filepath):
                            os.remove(temp_filepath)
                        if ffmpeg_out and os.path.exists(ffmpeg_out):
                            os.remove(ffmpeg_out)

        except KeyboardInterrupt:
            tqdm.write(f"\n{Fore.YELLOW}Interrompido pelo usuario.{Style.RESET_ALL}")
            save_resume({
                "origin_chat": origin_chat,
                "destination_chat": destination_chat,
                "chat_type": chat_info["type"],
                "origin_title": chat_info["title"],
                "topic_map": topic_map,
                "cloned_msg_ids": cloned_ids,
                "total_msgs": total_messages,
                "skipped_count": skipped_count,
                "cloned_count": cloned_count,
                "failed_count": failed_count,
                "content_types": content_types,
            })
            print(f"\n{Fore.CYAN}Progresso salvo. Para retomar, execute novamente.{Style.RESET_ALL}")
            print(f"  Mensagens clonadas: {cloned_count}")
            print(f"  Falhas: {failed_count}")
            client.disconnect()
            executor.shutdown(wait=False)
            return

    # ================================================================
    # PASSO 7: Resumo final e menu
    # ================================================================

    # Salva estado final antes do menu
    save_resume({
        "origin_chat": origin_chat,
        "destination_chat": destination_chat,
        "chat_type": chat_info["type"],
        "origin_title": chat_info["title"],
        "topic_map": topic_map,
        "cloned_msg_ids": cloned_ids,
        "total_msgs": total_messages,
        "skipped_count": skipped_count,
        "cloned_count": cloned_count,
        "failed_count": failed_count,
        "content_types": content_types,
    })

    if chat_protected:
        print(f"\n{Fore.YELLOW}Atenção: o chat de origem possui proteção de conteúdo ativada.")
        print("Apenas textos e legendas foram clonados. Mídias não puderam ser baixadas.{Style.RESET_ALL}")

    if menu and (menu_id not in cloned_ids):
        print("\nAdicionando menu ao final do chat clonado...")
        client.send_message(destination_chat, menu)
        cloned_ids.add(menu_id)
        cloned_count += 1
        print("Menu adicionado com sucesso!")
    elif menu:
        print("Menu já estava entre as mensagens clonadas, não foi adicionado novamente.")
    else:
        print("Nenhum menu encontrado para adicionar ao chat clonado.")

    # Resumo final
    print(f"\n{Fore.GREEN}Clonagem concluída!{Style.RESET_ALL}\n")
    print(f"  Mensagens clonadas: {cloned_count}")
    print(f"  Mensagens puladas (serviço/sem conteúdo): {skipped_count}")
    if failed_count > 0:
        print(f"  {Fore.RED}Mensagens com falha: {failed_count}{Style.RESET_ALL}")
    if msg_id_map:
        print(f"  Replies preservados: {len(msg_id_map)}")
    print(f"\nID do Destino: {destination_chat}")
    print(f"Nome: {chat_info['title']} - Clone")
    print(f"Tipo: {chat_info['type_label']}")

    # Clone completo — mantém resume para futuras execuções incrementais
    print(f"\n{Fore.CYAN}Estado salvo. Execute novamente para clonar apenas novas mensagens.{Style.RESET_ALL}")

    # Cleanup
    client.disconnect()
    executor.shutdown(wait=False)

# Inicia o script
if __name__ == "__main__":
    main()
