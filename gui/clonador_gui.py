import logging
import time
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError
from telethon.tl.types import MessageService

MESSAGE_DELAY = 5

# Função para verificar se a proteção de conteúdo está ativada

def is_content_protected(client, origin_chat_id):
    try:
        full_channel = client(GetFullChannelRequest(origin_chat_id))
        if hasattr(full_channel.full_chat, 'protected'):
            return full_channel.full_chat.protected
        return False
    except Exception as e:
        logging.error(f"Erro ao verificar proteção de conteúdo: {e}")
        return False

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
        return channel_id, origin_title, channel_description
    except Exception as e:
        logging.error(f"Erro ao criar canal de destino: {e}")
        raise

# Função principal para uso na GUI

def clonar_canal_gui(api_id, api_hash, origem, destino, content_types, on_progress, on_status, on_finish, on_error):
    try:
        def run():
            try:
                on_status("Conectando ao Telegram...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                with TelegramClient("session_name", api_id, api_hash, loop=loop) as client:
                    on_status("Conexão estabelecida.")
                    origin_chat = int(origem)
                    if is_content_protected(client, origin_chat):
                        on_error("Proteção de conteúdo ativada no canal de origem.")
                        return
                    if not destino:
                        destino_id, channel_name, channel_description = create_destination_channel(client, origin_chat)
                    else:
                        destino_id = destino
                        channel_name = "Canal de destino informado"
                        channel_description = "-"
                    on_status("Obtendo mensagens...")
                    messages = list(client.iter_messages(origin_chat, limit=None))
                    total_messages = len(messages)
                    on_status(f"Total de mensagens: {total_messages}")
                    if total_messages == 0:
                        on_error("Nenhuma mensagem encontrada no canal de origem.")
                        return
                    clonaveis = [
                        m for m in messages
                        if not isinstance(m, MessageService)
                    ]
                    total_clonaveis = len(clonaveis)
                    clonados = 0

                    print(f"Total de mensagens: {len(messages)}, clonáveis: {total_clonaveis}")
                    if total_clonaveis == 0:
                        on_progress(100, "Nenhuma mensagem clonável encontrada.")
                    for idx, message in enumerate(reversed(messages)):
                        try:
                            if isinstance(message, MessageService):
                                on_progress(int((clonados+1)/total_clonaveis*100) if total_clonaveis else 100, f"Ignorando mensagens de serviço... {idx+1}/{len(messages)}")
                                print(f"Ignorando serviço: {idx+1}/{len(messages)} | Progresso: {clonados}/{total_clonaveis}")
                                continue
                            caption = message.caption if hasattr(message, "caption") else message.message or ""
                            if "photo" in content_types and message.photo:
                                client.send_file(destino_id, message.photo, caption=caption)
                            elif "video" in content_types and message.video:
                                client.send_file(destino_id, message.video, caption=caption, supports_streaming=True)
                            elif "audio" in content_types and message.audio:
                                client.send_file(destino_id, message.audio, caption=caption)
                            elif "document" in content_types and message.document:
                                client.send_file(destino_id, message.document, caption=caption)
                            elif "text" in content_types and message.text:
                                client.send_message(destino_id, message.text)
                            elif "sticker" in content_types and message.sticker:
                                client.send_file(destino_id, message.sticker)
                            time.sleep(MESSAGE_DELAY)
                            clonados += 1
                            on_progress(int((clonados)/total_clonaveis*100), f"Clonando mensagens... {clonados}/{total_clonaveis}")
                            print(f"Clonando: {clonados}/{total_clonaveis} | Progresso: {int((clonados)/total_clonaveis*100)}%")
                        except FloodWaitError as e:
                            on_status(f"FloodWait: aguardando {e.seconds} segundos...")
                            time.sleep(e.seconds)
                        except RPCError as e:
                            logging.error(f"Erro RPC: {e}")
                            continue
                    on_finish(destino_id, channel_name, channel_description)
            except Exception as e:
                on_error(str(e))
        run()
    except Exception as e:
        on_error(str(e)) 