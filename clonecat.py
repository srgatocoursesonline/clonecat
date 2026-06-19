import os
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError, ChatAdminRequiredError
from telethon.tl.types import MessageService, Channel
from colorama import Fore, Style, init
from tqdm import tqdm

# Inicializa cores no terminal
init(autoreset=True)

# Configuração do log para salvar erros
logging.basicConfig(filename="erros.log", level=logging.WARNING, format="%(asctime)s - %(message)s")

# Diretório temporário para salvar mídias
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

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
        fc = full_channel.full_chat
        if hasattr(fc, 'protected') and fc.protected:
            return True
        if hasattr(fc, 'noforwards') and fc.noforwards:
            return True
        for chat in full_channel.chats:
            if hasattr(chat, 'noforwards') and chat.noforwards:
                return True
            if hasattr(chat, 'restricted') and chat.restricted:
                return True
        return False
    except Exception as e:
        logging.error(f"Erro ao verificar protecao de conteudo: {e}")
        return False

# Função principal
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

    # Verifica se a proteção de conteúdo está ativada e avisa
    if is_content_protected(client, origin_chat):
        print(f"\n{Fore.YELLOW}Atencao: protecao de conteudo detectada no canal de origem.")
        print("Midias serao baixadas localmente e reenviadas. Caso o download falhe, apenas o texto sera clonado.{Style.RESET_ALL}")

    # Cria o canal de destino automaticamente
    destination_chat, channel_name, channel_description = create_destination_channel(client, origin_chat)

    # Exibe o menu e seleciona o tipo de conteúdo a clonar
    content_types = select_content_type()

    # Obtém histórico de mensagens
    print("Obtendo histórico de mensagens...")
    messages = list(client.iter_messages(origin_chat, limit=None))
    print(f"Total de mensagens encontradas: {len(messages)}")
    total_messages = len(messages)

    # Busca o menu antes de clonar as mensagens
    menu, menu_id = get_menu_from_channel(client, origin_chat)
    print(f"Menu encontrado: {menu is not None}, ID do menu: {menu_id}")

    # Contadores + estado do pipeline
    cloned_ids = set()
    cloned_count = 0
    skipped_count = 0
    failed_count = 0
    chat_protected = False

    ext_map = {"photo": ".jpg", "video": ".mp4", "audio": ".ogg", "document": "", "sticker": ".webp"}

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

    # Pre-filtra mensagens nao-servico em ordem cronologica
    ordered = [m for m in reversed(messages) if not isinstance(m, MessageService)]
    skipped_count = total_messages - len(ordered)

    # Pipeline: future da proxima midia sendo baixada em background
    next_dl_future = None
    next_dl_info = None   # (filepath, media_type, text, msg_id)

    with tqdm(total=total_messages, desc="Clonando", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}",
              colour="magenta", initial=skipped_count) as progress:

        def _send_text(msg_id, text):
            nonlocal cloned_count
            client.send_message(destination_chat, text)
            cloned_ids.add(msg_id)
            cloned_count += 1

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

        def _upload(path, media_type, text, msg_id, client_instance=client):
            nonlocal cloned_count
            if not os.path.exists(path):
                return False
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
            client_instance.send_file(destination_chat, path, **kwargs)
            cloned_ids.add(msg_id)
            cloned_count += 1
            tqdm.write(f"  Msg {msg_id} enviada ({file_sz})")
            return True

        for i, message in enumerate(ordered):
            msg_id = message.id
            temp_filepath = None
            try:
                text_content = message.text or message.message or message.caption or ""

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
                                _send_text(msg_id, text_content)
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
                            _send_text(msg_id, text_content)
                            tqdm.write(f"  Texto msg {msg_id} enviado (fallback)")
                        else:
                            skipped_count += 1
                        progress.update(1)
                        if temp_filepath and os.path.exists(temp_filepath):
                            os.remove(temp_filepath)
                        continue

                    # -- PIPELINE: sobe a midia atual enquanto baixa a proxima em background --
                    # Procura a proxima mensagem com midia
                    next_media_idx = None
                    for j in range(i + 1, len(ordered)):
                        nm = ordered[j]
                        if _has_media(nm, content_types):
                            next_media_idx = j
                            break

                    if next_media_idx is not None:
                        nm = ordered[next_media_idx]
                        nm_text = nm.text or nm.message or nm.caption or ""
                        nm_mt, nm_mo = _get_media(nm, content_types)
                        nm_ext = ext_map.get(nm_mt, "")
                        nm_fp = os.path.join(TEMP_DIR, f"{origin_chat}_{nm.id}{nm_ext}")

                        tqdm.write(f"  [bg] Baixando proxima msg {nm.id} ({nm_mt})...")

                        def _bg_download(mo=nm_mo, fp=nm_fp, mid=nm.id, mt=nm_mt,
                                         ss=session_str, aid=api_id, ah=api_hash):
                            import asyncio
                            bg = TelegramClient(StringSession(ss), aid, ah)
                            bg.connect()
                            try:
                                _download_sync(bg, mo, fp, mid, mt)
                            finally:
                                bg.disconnect()

                        next_dl_future = executor.submit(_bg_download)
                        next_dl_info = (nm_fp, nm_mt, nm_text, nm.id)

                    # Upload da midia atual (enquanto a proxima baixa em background)
                    if _upload(temp_filepath, media_type, text_content, msg_id):
                        os.remove(temp_filepath)
                        time.sleep(MEDIA_DELAY)
                    progress.update(1)

                    # Aguarda o download em background da proxima midia
                    if next_dl_future is not None:
                        next_dl_future.result()
                        next_dl_future = None

                elif text_content:
                    _send_text(msg_id, text_content)
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
                            _send_text(msg_id, text_content)
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

    if chat_protected:
        print(f"\n{Fore.YELLOW}Atencao: o canal de origem possui protecao de conteudo ativada.")
        print("Apenas textos e legendas foram clonados. Midias nao puderam ser baixadas.{Style.RESET_ALL}")

    # Adicionar o menu ao final se ele nao foi clonado
    if menu and (menu_id not in cloned_ids):
        print("\nAdicionando menu ao final do canal clonado...")
        client.send_message(destination_chat, menu)
        cloned_ids.add(menu_id)
        cloned_count += 1
        print("Menu adicionado com sucesso!")
    elif menu:
        print("Menu ja estava entre as mensagens clonadas, nao foi adicionado novamente.")
    else:
        print("Nenhum menu encontrado para adicionar ao canal clonado.")

    # Resumo final
    print(f"\n{Fore.GREEN}Clonagem concluida!{Style.RESET_ALL}\n")
    print(f"  Mensagens clonadas: {cloned_count}")
    print(f"  Mensagens puladas (servico/sem conteudo): {skipped_count}")
    if failed_count > 0:
        print(f"  {Fore.RED}Mensagens com falha: {failed_count}{Style.RESET_ALL}")
    print(f"\nID do Canal: {destination_chat}")
    print(f"Nome: {channel_name}")
    print(f"Descricao: {channel_description}")

    # Cleanup
    client.disconnect()
    executor.shutdown(wait=False)

# Inicia o script
if __name__ == "__main__":
    main()


