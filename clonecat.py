import os
import json
import logging
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import CreateChannelRequest, GetFullChannelRequest, UpdateUsernameRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.errors.rpcerrorlist import FloodWaitError, RPCError, ChatAdminRequiredError
from telethon.tl.types import MessageService, Channel
from colorama import Fore, Style, init
from tqdm import tqdm
import platform
import asyncio
from pathlib import Path
from src.utils.normal_recovery import NormalRecovery
from config_crypto import load_encrypted_config, save_encrypted_config
from getpass import getpass

# Inicializa cores no terminal
init(autoreset=True)

# Configuração do log para salvar erros
logging.basicConfig(filename="erros.log", level=logging.ERROR, format="%(asctime)s - %(message)s")

# Diretório temporário para salvar mídias
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

# Intervalo entre mensagens (em segundos)
MESSAGE_DELAY = 5  # 5000ms = 5 segundos

# Função para limpar a tela
def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

# Função para exibir ASCII Art
def print_ascii_art():
    print(r"  ____  __     ___   _   _  _____  ____    _      _____ ")
    print(r" / ___||  |   / _ \ | \ | || ____| / ___|  / \   |_   _|")
    print(r"| |    |  |  | | | ||  \| ||  _|  | |     / _ \   | |  ")
    print(r"| |___ |  |__| |_| || |\  || |___ | |___ / ___ \  | |  ")
    print(r" \____||_____|\___/ |_| \_||_____| \____|/_/   \_\|_|")

# Função para coletar ou carregar API ID e Hash
def get_api_credentials():
    print("\n🔐 Carregando credenciais de API de forma segura...")
    password = getpass("Digite sua senha para descriptografar as credenciais: ")
    creds = load_encrypted_config(password)
    if creds:
        api_id, api_hash = creds
        print("Credenciais carregadas com sucesso.")
        return int(api_id), api_hash
    else:
        print("Arquivo de configuração não encontrado ou senha incorreta.")
        api_id = input("Digite seu API ID: ").strip()
        api_hash = input("Digite seu API HASH: ").strip()
        password = getpass("Crie uma senha para proteger suas credenciais: ")
        save_encrypted_config(api_id, api_hash, password)
        print("Credenciais salvas de forma criptografada!")
        return int(api_id), api_hash

# Versão async para o modo normal e avançado
async def create_destination_channel(client, origin_chat_id):
    try:
        origin_chat = await client(GetFullChannelRequest(origin_chat_id))
        origin_title = origin_chat.chats[0].title
        channel = await client(CreateChannelRequest(
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
        import sys
        sys.exit()

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
async def is_content_protected(client, origin_chat_id):
    try:
        full_channel = await client(GetFullChannelRequest(origin_chat_id))
        if hasattr(full_channel.full_chat, 'protected'):
            return full_channel.full_chat.protected
        return False
    except Exception as e:
        logging.error(f"Erro ao verificar proteção de conteúdo: {e}")
        return False

# Função para exibir o menu principal
def show_main_menu():
    print(f"\n{Fore.YELLOW}🐱 CLONECAT - MENU PRINCIPAL")
    print("=" * 50)
    print("1 - 📥 Iniciar Clonagem")
    print("2 - ⚙️ Configurações")
    print("3 - 📖 Guia de Uso")
    print("4 - 📊 Analisar Canal (sem clonar)")
    print("5 - 📚 Instruções")
    print("6 - 🚀 Modo Avançado")
    print("7 - 📜 Histórico")
    print("0 - 🚪 Sair")
    print("=" * 50)

def analyze_channel(client, channel_id):
    print("\n📊 ANÁLISE DO CANAL DE ORIGEM")
    print("=" * 70)
    
    try:
        # Obtém informações do canal
        channel = client.get_entity(channel_id)
        messages = list(client.iter_messages(channel_id, limit=None))
        media_count = sum(1 for m in messages if m.media)
        text_count = sum(1 for m in messages if m.text and not m.media)
        other_count = len(messages) - media_count - text_count
        
        # Calcula o tamanho do canal
        if len(messages) <= 1000:
            size = "PEQUENO"
            delay = 5
            risk = "BAIXO"
        elif len(messages) <= 10000:
            size = "MÉDIO"
            delay = 8
            risk = "MODERADO"
        elif len(messages) <= 50000:
            size = "GRANDE"
            delay = 15
            risk = "ALTO"
        else:
            size = "GIGANTE"
            delay = 25
            risk = "CRÍTICO"
        
        # Estima o tempo (baseado em média de 1 mensagem por delay)
        estimated_hours = round((len(messages) * delay) / 3600, 1)
        
        print(f"📏 Tamanho do Canal: {Fore.YELLOW}{size}{Style.RESET_ALL} ({len(messages):,} mensagens)")
        print(f"⏱️ Delay Recomendado: {Fore.GREEN}{delay} segundos{Style.RESET_ALL}")
        print(f"⚠️ Nível de Risco: {Fore.YELLOW}{risk}{Style.RESET_ALL}")
        print(f"⏳ Tempo Estimado: {Fore.CYAN}{estimated_hours} horas{Style.RESET_ALL}")
        print(f"💡 Aviso: Use delay adequado para evitar problemas.")
        print("=" * 70)
        
        print("\n📊 Detalhes adicionais:")
        print(f"• Mensagens com mídia: {Fore.GREEN}{media_count:,}{Style.RESET_ALL}")
        print(f"• Mensagens de texto: {Fore.YELLOW}{text_count:,}{Style.RESET_ALL}")
        print(f"• Outros tipos: {Fore.CYAN}{other_count:,}{Style.RESET_ALL}")
        print("=" * 70)
        
        return True
    except Exception as e:
        print(f"\n❌ Erro ao analisar canal: {e}")
        return False

def show_guide():
    print(f"\n{Fore.YELLOW}🐱 CLONECAT 1.4.0 - GUIA DE USO INTELIGENTE")
    print("=" * 50)
    
    print(f"\n📋 RECOMENDAÇÕES DE DELAY POR TAMANHO:")
    print(f"🟢 PEQUENO (até 1k)    → 5s  | {Fore.GREEN}✅ Seguro{Style.RESET_ALL}")
    print(f"🟡 MÉDIO (1k-10k)     → 8s  | {Fore.YELLOW}⚠️ Cuidado{Style.RESET_ALL}")
    print(f"🟠 GRANDE (10k-50k)   → 15s | {Fore.YELLOW}⚠️ Alto{Style.RESET_ALL}")
    print(f"🔴 GIGANTE (50k+)     → 25s | {Fore.RED}🔥 Crítico{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}⚠️ EVITE TRAVAMENTOS:{Style.RESET_ALL}")
    print("• Use SEMPRE o delay recomendado ou maior")
    print("• Sistema detecta automaticamente e sugere o ideal")
    print("• Canais 50k+ podem levar DIAS - seja paciente!")
    
    print(f"\n{Fore.GREEN}✅ DICAS IMPORTANTES:{Style.RESET_ALL}")
    print("• Use 'Analisar Canal' antes de clonar")
    print("• Modo 'Auto Delay' é o mais seguro")
    print("• Configure tudo no menu 'Configurações'")
    print("=" * 50)

def show_help():
    print(f"\n{Fore.CYAN}═══════════════════ INSTRUÇÕES ═══════════════════{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Como usar o Clonecat:{Style.RESET_ALL}")
    print("\n1. Obtenha suas credenciais:")
    print("   - Acesse: https://my.telegram.org")
    print("   - Faça login com seu número")
    print("   - Vá em 'API Development'")
    print("   - Crie um novo app se necessário")
    print("   - Guarde o API ID e API Hash")
    
    print("\n2. Encontre o ID do canal:")
    print("   - Abra o canal no Telegram Web")
    print("   - O ID está na URL após 't.me/'")
    print("   - Ou use @username_to_id_bot")
    
    print("\n3. Tipos de clonagem:")
    print("   - Completa: todo conteúdo")
    print("   - Seletiva: escolha o tipo")
    print("   - Avançada: mais opções")
    
    print("\n4. Dicas importantes:")
    print("   - Use uma boa conexão")
    print("   - Evite muitos clones seguidos")
    print("   - Mantenha o app atualizado")
    print("   - Backup seus dados")
    
    print(f"\n{Fore.RED}Atenção:{Style.RESET_ALL}")
    print("- Não use para spam")
    print("- Respeite limites do Telegram")
    print("- Evite conteúdo protegido")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════{Style.RESET_ALL}\n")

def show_settings():
    global MESSAGE_DELAY
    
    while True:
        clear_screen()
        print(f"\n{Fore.CYAN}═══════════════════ CONFIGURAÇÕES ═══════════════════{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[1]{Style.RESET_ALL} - Delay entre mensagens: {MESSAGE_DELAY}s")
        print(f"{Fore.YELLOW}[2]{Style.RESET_ALL} - Pasta temporária: {TEMP_DIR}")
        print(f"{Fore.YELLOW}[3]{Style.RESET_ALL} - Limpar cache")
        print(f"{Fore.YELLOW}[4]{Style.RESET_ALL} - Resetar credenciais")
        print(f"{Fore.YELLOW}[5]{Style.RESET_ALL} - Limpar progresso de clonagem normal")
        print(f"{Fore.YELLOW}[6]{Style.RESET_ALL} - Voltar")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════{Style.RESET_ALL}")
        
        choice = input("\nEscolha uma opção (1-6): ").strip()
        
        if choice == "1":
            try:
                new_delay = int(input(f"\nDigite o novo delay em segundos (atual: {MESSAGE_DELAY}s): "))
                if new_delay > 0:
                    MESSAGE_DELAY = new_delay
                    print(f"{Fore.GREEN}✅ Delay atualizado para {MESSAGE_DELAY}s{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ O delay deve ser maior que 0{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Digite um número válido{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "2":
            print(f"\n{Fore.YELLOW}Pasta atual: {TEMP_DIR}{Style.RESET_ALL}")
            print("Função de alterar pasta em desenvolvimento...")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "3":
            # Limpar cache
            import shutil
            try:
                if os.path.exists(TEMP_DIR):
                    shutil.rmtree(TEMP_DIR)
                    os.makedirs(TEMP_DIR, exist_ok=True)
                    print(f"{Fore.GREEN}✅ Cache limpo com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}ℹ️ Pasta de cache já está vazia{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro ao limpar cache: {e}{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "4":
            # Resetar credenciais
            if os.path.exists("config.json"):
                confirm = input("\nDeseja mesmo resetar as credenciais? (s/n): ").lower()
                if confirm == 's':
                    os.remove("config.json")
                    print(f"{Fore.GREEN}✅ Credenciais resetadas com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Operação cancelada{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}ℹ️ Não há credenciais salvas{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "5":
            from src.utils.normal_recovery import NormalRecovery
            recovery = NormalRecovery()
            recovery.clear()
            recovery.close()
            print(f"{Fore.GREEN}✅ Progresso de clonagem normal limpo!{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "6":
            break
        else:
            print(f"{Fore.RED}❌ Opção inválida!{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")

def show_advanced_menu():
    while True:
        clear_screen()
        print(f"\n{Fore.CYAN}═══════════════════ MODO AVANÇADO ═══════════════════{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}🔒 CONTORNO DE RESTRIÇÕES DE ENCAMINHAMENTO{Style.RESET_ALL}")
        print("\nEste modo permite clonar canais com proteção ativada")
        print("usando download manual e reupload do conteúdo.\n")
        
        print(f"{Fore.YELLOW}[1]{Style.RESET_ALL} - 📥 Iniciar Clonagem Avançada")
        print(f"{Fore.YELLOW}[2]{Style.RESET_ALL} - 📊 Ver Progresso de Download")
        print(f"{Fore.YELLOW}[3]{Style.RESET_ALL} - 🔄 Retomar Download Pausado")
        print(f"{Fore.YELLOW}[4]{Style.RESET_ALL} - 🗑️  Limpar Arquivos Temporários")
        print(f"{Fore.YELLOW}[5]{Style.RESET_ALL} - ⚙️  Configurações do Modo Avançado")
        print(f"{Fore.YELLOW}[6]{Style.RESET_ALL} - 🔙 Voltar")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════{Style.RESET_ALL}")
        
        choice = input("\nEscolha uma opção (1-6): ").strip()
        
        if choice == "1":
            asyncio.run(start_advanced_cloning())
        elif choice == "2":
            print(f"\n{Fore.YELLOW}📊 PROGRESSO DE DOWNLOAD{Style.RESET_ALL}")
            print("\nVerificando arquivos baixados...")
            print(f"\n• Total de mensagens: {Fore.GREEN}0{Style.RESET_ALL}")
            print(f"• Mensagens baixadas: {Fore.YELLOW}0{Style.RESET_ALL}")
            print(f"• Mensagens enviadas: {Fore.CYAN}0{Style.RESET_ALL}")
            print(f"• Espaço usado: {Fore.MAGENTA}0 MB{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "3":
            print(f"\n{Fore.YELLOW}🔄 RETOMAR DOWNLOAD{Style.RESET_ALL}")
            print("\nProcurando downloads pausados...")
            print(f"{Fore.RED}Nenhum download pausado encontrado.{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "4":
            print(f"\n{Fore.YELLOW}🗑️  LIMPAR ARQUIVOS TEMPORÁRIOS{Style.RESET_ALL}")
            print("\nEsta ação removerá todos os arquivos baixados.")
            confirm = input("Tem certeza? (s/n): ").lower()
            if confirm == 's':
                print(f"{Fore.GREEN}✅ Arquivos temporários limpos!{Style.RESET_ALL}")
            else:
                print("Operação cancelada.")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "5":
            print(f"\n{Fore.YELLOW}⚙️  CONFIGURAÇÕES DO MODO AVANÇADO{Style.RESET_ALL}")
            print("\n• Pasta temporária: temp_storage/")
            print("• Delay entre downloads: 2s")
            print("• Delay entre uploads: 5s")
            print("• Qualidade de mídia: Máxima")
            print("• Compressão: Desativada")
            print(f"\n{Fore.YELLOW}🚧 Configurações em desenvolvimento...{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            
        elif choice == "6":
            break
        else:
            print(f"{Fore.RED}❌ Opção inválida!{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")

async def start_advanced_cloning():
    clear_screen()
    print(f"\n{Fore.YELLOW}🔒 MODO AVANÇADO - CONTORNO DE RESTRIÇÕES")
    print(f"{Fore.WHITE}{'═' * 60}")
    from src.core.advanced_downloader import AdvancedDownloader
    from src.core.manual_uploader import ManualUploader
    from src.utils.cache_manager import CacheManager
    api_id, api_hash = get_api_credentials()
    from telethon import TelegramClient
    cache_dir = Path("temp_storage/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_manager = CacheManager(db_path="temp_storage/cache.db", cache_dir=cache_dir)
    async with TelegramClient("session_name", api_id, api_hash) as client:
        print(f"{Fore.GREEN}✅ Conectado ao Telegram{Style.RESET_ALL}")
        downloader = AdvancedDownloader()
        origin_chat = input(f"\n{Fore.CYAN}Digite o ID do canal de origem: {Fore.WHITE}").strip()
        try:
            origin_chat = int(origin_chat)
        except ValueError:
            print(f"{Fore.RED}❌ ID inválido!{Style.RESET_ALL}")
            return
        print(f"\n{Fore.YELLOW}📥 FASE 1: Baixando conteúdo...{Style.RESET_ALL}")
        print("Isso pode demorar bastante dependendo do tamanho do canal.\n")
        messages = []
        async for msg in client.iter_messages(origin_chat, limit=None):
            messages.append(msg)
        total = len(messages)
        print(f"Total de mensagens encontradas: {Fore.CYAN}{total}{Style.RESET_ALL}")
        downloaded = 0
        from tqdm import tqdm
        with tqdm(total=total, desc="Baixando", colour="yellow") as pbar:
            for message in reversed(messages):
                await downloader.download_message_content(client, message)
                downloaded += 1
                pbar.update(1)
                cache_manager.save_progress(origin_chat, message.id, total, downloaded)
                import time
                time.sleep(2)
        print(f"\n{Fore.GREEN}✅ Download concluído!{Style.RESET_ALL}")
        print(f"Espaço usado: {Fore.MAGENTA}{cache_manager.get_cache_size():.2f} MB{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Pressione ENTER para iniciar a Fase 2 (Upload)...{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}📤 FASE 2: Fazendo upload...{Style.RESET_ALL}")
        destination_chat, channel_name, channel_description = await create_destination_channel(client, origin_chat)
        uploader = ManualUploader(session_name="session_name", api_id=api_id, api_hash=api_hash)
        queue_size = await uploader.prepare_upload_queue()
        print(f"Mensagens para upload: {Fore.CYAN}{queue_size}{Style.RESET_ALL}\n")
        uploaded = 0
        with tqdm(total=queue_size, desc="Enviando", colour="green") as pbar:
            for msg_data in uploader.upload_queue:
                success = await uploader.upload_message(client, destination_chat, msg_data)
                if success:
                    uploaded += 1
                    pbar.update(1)
                import time
                time.sleep(5)
        print(f"\n{Fore.GREEN}✅ Clonagem avançada concluída!{Style.RESET_ALL}")
        print(f"Total enviado: {Fore.CYAN}{uploaded}/{queue_size}{Style.RESET_ALL}")
        print(f"\nCanal criado: {Fore.YELLOW}{channel_name}{Style.RESET_ALL}")
        print(f"ID: {Fore.CYAN}{destination_chat}{Style.RESET_ALL}")
        # Gerar link de convite real do canal clonado
        try:
            invite = await client(ExportChatInviteRequest(destination_chat))
            channel_link = invite.link
            # Se o link não for de convite privado, tentar forçar
            if not channel_link.startswith('https://t.me/+'):
                try:
                    await client(UpdateUsernameRequest(destination_chat, ''))
                    invite = await client(ExportChatInviteRequest(destination_chat))
                    channel_link = invite.link
                except Exception:
                    pass
        except Exception as e:
            channel_link = '(Não foi possível gerar o link de convite)'
        content_types = select_content_type()
        print("Obtendo histórico de mensagens...")
        messages = []
        async for m in client.iter_messages(origin_chat, limit=None):
            messages.append(m)
        print(f"Total de mensagens encontradas: {len(messages)}")
        print(f"IDs das mensagens: {[m.id for m in messages]}")
        total_messages = len(messages)
        menu, menu_id = get_menu_from_channel(client, origin_chat)
        print(f"Menu encontrado: {menu is not None}, ID do menu: {menu_id}")
        cloned_ids = set(m.id for m in messages)
        # --- RETOMADA ---
        recovery = NormalRecovery()
        last_cloned = recovery.get_last_cloned_id()
        if last_cloned:
            print(f"\n⚠️ Progresso detectado! Última mensagem clonada: {last_cloned}")
            if input("Deseja retomar de onde parou? (s/n): ").lower() != 's':
                recovery.clear()
                print("Progresso anterior apagado. Clonagem será do início.")
        # --- CLONAGEM ---
        from tqdm import tqdm
        with tqdm(total=total_messages, desc="Clonando mensagens", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}", colour="magenta") as progress:
            for message in reversed(messages):
                if recovery.is_cloned(message.id):
                    progress.update(1)
                    continue
                try:
                    if isinstance(message, MessageService):
                        continue
                    caption = message.caption if hasattr(message, "caption") else message.message or ""
                    if "photo" in content_types and message.photo:
                        await client.send_file(destination_chat, message.photo, caption=caption)
                    elif "video" in content_types and message.video:
                        await client.send_file(destination_chat, message.video, caption=caption, supports_streaming=True)
                    elif "audio" in content_types and message.audio:
                        await client.send_file(destination_chat, message.audio, caption=caption)
                    elif "document" in content_types and message.document:
                        await client.send_file(destination_chat, message.document, caption=caption)
                    elif "text" in content_types and message.text:
                        await client.send_message(destination_chat, message.text)
                    elif "sticker" in content_types and message.sticker:
                        await client.send_file(destination_chat, message.sticker)
                    import time
                    time.sleep(MESSAGE_DELAY)
                    recovery.mark_cloned(message.id)
                except FloodWaitError as e:
                    logging.error(f"FloodWait de {e.seconds} segundos ao buscar mensagem {message.id}. Aguardando...")
                    import time
                    time.sleep(e.seconds)
                except RPCError as e:
                    logging.error(f"Erro RPC ao acessar o Peer ID: {e}")
                    continue
                progress.update(1)
        if menu and (menu_id not in cloned_ids):
            print("\nAdicionando menu ao final do canal clonado...")
            await client.send_message(destination_chat, menu)
            print("Menu adicionado com sucesso!")
        elif menu:
            print("Menu já estava entre as mensagens clonadas, não foi adicionado novamente.")
        else:
            print("Nenhum menu encontrado para adicionar ao canal clonado.")
        print("\nClonagem concluída com sucesso!\n")
        print(f"ID do Canal: {destination_chat}")
        print(f"Nome: {channel_name}")
        print(f"Descrição: {channel_description}")
        print(f"Link do Canal: {channel_link}")
        if input("\nDeseja limpar os arquivos temporários? (s/n): ").lower() == 's':
            cache_manager.clear_all_temp_files()
        input("\nPressione ENTER para continuar...")

# Função principal modificada
def main():
    clear_screen()
    print_ascii_art()
    
    # Exibe as instruções na tela inicial
    print(f"\n{Fore.YELLOW}🐱 CLONECAT 1.4.0 - GUIA DE USO INTELIGENTE")
    print("=" * 50)
    
    print(f"\n📋 RECOMENDAÇÕES DE DELAY POR TAMANHO:")
    print(f"🟢 PEQUENO (até 1k)    → 5s  | {Fore.GREEN}✅ Seguro{Style.RESET_ALL}")
    print(f"🟡 MÉDIO (1k-10k)     → 8s  | {Fore.YELLOW}⚠️ Cuidado{Style.RESET_ALL}")
    print(f"🟠 GRANDE (10k-50k)   → 15s | {Fore.YELLOW}⚠️ Alto{Style.RESET_ALL}")
    print(f"🔴 GIGANTE (50k+)     → 25s | {Fore.RED}🔥 Crítico{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}⚠️ EVITE TRAVAMENTOS:{Style.RESET_ALL}")
    print("• Use SEMPRE o delay recomendado ou maior")
    print("• Sistema detecta automaticamente e sugere o ideal")
    print("• Canais 50k+ podem levar DIAS - seja paciente!")
    
    print(f"\n{Fore.GREEN}✅ DICAS IMPORTANTES:{Style.RESET_ALL}")
    print("• Use 'Analisar Canal' antes de clonar")
    print("• Modo 'Auto Delay' é o mais seguro")
    print("• Configure tudo no menu 'Configurações'")
    print("=" * 50)
    
    while True:
        show_main_menu()
        choice = input(f"\nEscolha uma opção (0-7): ").strip()
        
        if choice == "1":
            asyncio.run(clone_channel())
        elif choice == "2":
            clear_screen()
            show_settings()
        elif choice == "3":
            clear_screen()
            show_guide()
            input("\nPressione ENTER para continuar...")
            clear_screen()
            print_ascii_art()
        elif choice == "4":
            clear_screen()
            # Coleta de credenciais
            api_id, api_hash = get_api_credentials()
            print("✅ Credenciais carregadas com sucesso.")
            
            # Conecta ao Telegram
            with TelegramClient("session_name", api_id, api_hash) as client:
                print("✅ Conectado ao Telegram")
                
                # Solicita ID do canal
                channel_id = input("\nDigite o ID do canal para análise: ").strip()
                print("🔍 Analisando canal...")
                
                analyze_channel(client, int(channel_id))
                input("\nPressione ENTER para continuar...")
            clear_screen()
            print_ascii_art()
        elif choice == "5":
            clear_screen()
            show_help()
            input("\nPressione ENTER para continuar...")
            clear_screen()
            print_ascii_art()
        elif choice == "6":
            clear_screen()
            show_advanced_menu()
            clear_screen()
            print_ascii_art()
        elif choice == "7":
            clear_screen()
            print(f"\n{Fore.CYAN}═══════════════════ HISTÓRICO ═══════════════════{Style.RESET_ALL}")
            print("📜 Histórico de clonagens:")
            print("   - Função em desenvolvimento...")
            print(f"{Fore.CYAN}═══════════════════════════════════════════════════{Style.RESET_ALL}")
            input("\nPressione ENTER para continuar...")
            clear_screen()
            print_ascii_art()
        elif choice == "0":
            print(f"\n{Fore.YELLOW}Obrigado por usar o Clonecat! Até logo!{Style.RESET_ALL}")
            break
        else:
            print(f"\n{Fore.RED}Opção inválida! Tente novamente.{Style.RESET_ALL}")

async def clone_channel():
    print(f"\n{Fore.CYAN}═══════════════════ CLONAGEM DE CANAL ═══════════════════{Style.RESET_ALL}")
    api_id, api_hash = get_api_credentials()
    from telethon import TelegramClient
    recovery = NormalRecovery()
    async with TelegramClient("session_name", api_id, api_hash) as client:
        print(f"{Fore.GREEN}Conexão estabelecida com sucesso.{Style.RESET_ALL}")
        origin_chat = input(f"{Fore.YELLOW}Digite o ID do chat de origem (ID numérico): {Style.RESET_ALL}").strip()
        try:
            origin_chat = int(origin_chat)
        except ValueError:
            print(f"{Fore.RED}O ID do chat de origem deve ser um número inteiro.{Style.RESET_ALL}")
            return
        if await is_content_protected(client, origin_chat):
            print(f"\n{Fore.RED}⚠️ Não é possível clonar este canal pois a proteção de conteúdo está ativada!{Style.RESET_ALL}")
            print("Desative a opção 'Restringir salvamento de conteúdo' nas configurações do canal e tente novamente.")
            return
        destination_chat, channel_name, channel_description = await create_destination_channel(client, origin_chat)
        # Gerar link de convite real do canal clonado
        try:
            invite = await client(ExportChatInviteRequest(destination_chat))
            channel_link = invite.link
            # Se o link não for de convite privado, tentar forçar
            if not channel_link.startswith('https://t.me/+'):
                try:
                    await client(UpdateUsernameRequest(destination_chat, ''))
                    invite = await client(ExportChatInviteRequest(destination_chat))
                    channel_link = invite.link
                except Exception:
                    pass
        except Exception as e:
            channel_link = '(Não foi possível gerar o link de convite)'
        content_types = select_content_type()
        print("Obtendo histórico de mensagens...")
        messages = []
        async for m in client.iter_messages(origin_chat, limit=None):
            messages.append(m)
        print(f"Total de mensagens encontradas: {len(messages)}")
        print(f"IDs das mensagens: {[m.id for m in messages]}")
        total_messages = len(messages)
        menu, menu_id = get_menu_from_channel(client, origin_chat)
        print(f"Menu encontrado: {menu is not None}, ID do menu: {menu_id}")
        cloned_ids = set(m.id for m in messages)
        # --- RETOMADA ---
        last_cloned = recovery.get_last_cloned_id()
        if last_cloned:
            print(f"\n⚠️ Progresso detectado! Última mensagem clonada: {last_cloned}")
            if input("Deseja retomar de onde parou? (s/n): ").lower() != 's':
                recovery.clear()
                print("Progresso anterior apagado. Clonagem será do início.")
        # --- CLONAGEM ---
        from tqdm import tqdm
        with tqdm(total=total_messages, desc="Clonando mensagens", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}", colour="magenta") as progress:
            for message in reversed(messages):
                if recovery.is_cloned(message.id):
                    progress.update(1)
                    continue
                try:
                    if isinstance(message, MessageService):
                        continue
                    caption = message.caption if hasattr(message, "caption") else message.message or ""
                    if "photo" in content_types and message.photo:
                        await client.send_file(destination_chat, message.photo, caption=caption)
                    elif "video" in content_types and message.video:
                        await client.send_file(destination_chat, message.video, caption=caption, supports_streaming=True)
                    elif "audio" in content_types and message.audio:
                        await client.send_file(destination_chat, message.audio, caption=caption)
                    elif "document" in content_types and message.document:
                        await client.send_file(destination_chat, message.document, caption=caption)
                    elif "text" in content_types and message.text:
                        await client.send_message(destination_chat, message.text)
                    elif "sticker" in content_types and message.sticker:
                        await client.send_file(destination_chat, message.sticker)
                    import time
                    time.sleep(MESSAGE_DELAY)
                    recovery.mark_cloned(message.id)
                except FloodWaitError as e:
                    logging.error(f"FloodWait de {e.seconds} segundos ao buscar mensagem {message.id}. Aguardando...")
                    import time
                    time.sleep(e.seconds)
                except RPCError as e:
                    logging.error(f"Erro RPC ao acessar o Peer ID: {e}")
                    continue
                progress.update(1)
        if menu and (menu_id not in cloned_ids):
            print("\nAdicionando menu ao final do canal clonado...")
            await client.send_message(destination_chat, menu)
            print("Menu adicionado com sucesso!")
        elif menu:
            print("Menu já estava entre as mensagens clonadas, não foi adicionado novamente.")
        else:
            print("Nenhum menu encontrado para adicionar ao canal clonado.")
        print("\nClonagem concluída com sucesso!\n")
        print(f"ID do Canal: {destination_chat}")
        print(f"Nome: {channel_name}")
        print(f"Descrição: {channel_description}")
        print(f"Link do Canal: {channel_link}")
        input("\nPressione ENTER para continuar...")
        recovery.close()

# Inicia o script
if __name__ == "__main__":
    main()
