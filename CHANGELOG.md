# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-03-19

### Adicionado
- Funcionalidade inicial de clonagem de canais do Telegram
- Suporte para clonar diferentes tipos de conteúdo:
  - Mensagens de texto
  - Fotos
  - Vídeos
  - Áudios
  - Documentos
  - Stickers
- Sistema de progresso com barra de progresso
- Interface colorida no terminal
- Sistema de logging para erros
- Salvamento automático de credenciais
- Criação automática de canal de destino
- Menu de seleção de tipo de conteúdo
- Respeito aos limites do Telegram com delay configurável

### Documentação
- README.md com instruções detalhadas
- Licença MIT
- Arquivo .gitignore
- CHANGELOG.md

### Dependências
- telethon==1.27.0
- colorama==0.4.6
- tqdm==4.65.0

## [0.1.0] - 2024-03-19

### Adicionado
- Estrutura inicial do projeto
- Configuração básica do ambiente
- Primeira versão funcional do script de clonagem

## [1.1.0] - 2025-06-18

### Adicionado
- Verificação inteligente de proteção de conteúdo do canal antes de iniciar a clonagem
- Mensagens de erro amigáveis e explicativas sobre restrições, permissões e possíveis causas de falha
- Atualização do README.md com recomendações e restrições sobre proteção de conteúdo e permissões do Telegram

### Corrigido
- Melhor tratamento de erros ao criar canal de destino
- Garantia de clonagem completa apenas quando permissões e configurações permitem

### Melhorado
- UX do script, com avisos claros e instruções para o usuário

## [1.2.0] - 2025-03-20

### Adicionado
- Interface gráfica moderna com tema dark usando PyQt6
- Painel de controle intuitivo para gerenciar clonagens
- Visualização em tempo real do progresso de clonagem
- Sistema de filas para múltiplas clonagens simultâneas
- Configurações visuais para personalização da interface
- Indicadores visuais de status e erros
- Suporte a temas personalizáveis
- Histórico de clonagens com detalhes
- Exportação de logs em formato visual

### Dependências
- PyQt6==6.6.1
- qt-material==2.14
- darkdetect==0.8.0

### Melhorado
- Experiência do usuário com interface gráfica amigável
- Acessibilidade com suporte a temas claros e escuros
- Visualização mais clara do progresso e status
- Gerenciamento simplificado de múltiplas clonagens

### Corrigido
- Problemas de usabilidade na interface de linha de comando
- Melhor organização das configurações do usuário
- Tratamento visual de erros e exceções

## [1.4.0] - 2025-06-19

### Adicionado
- Suporte completo a supergrupos com tópicos (fórum): detecção, criação de tópicos no destino e roteamento de mensagens por tópico
- Sistema de retomada (resume): salva progresso a cada 20 mensagens; ao final mantém o estado para clonagem incremental futura
- Preservação de cadeia de respostas (reply chain) entre mensagens clonadas via msg_id_map
- Pipeline de download/upload paralelo: baixa a próxima mídia em background enquanto envia a atual
- Otimização de vídeos via FFmpeg para streaming (codec, resolução, taxa de quadros, faststart)
- Detecção e criação de destino compatível com 4 tipos de chat: canal, grupo comum, supergrupo e fórum
- Duas estratégias de clonagem: envio anônimo (rápido, chats sem proteção) e download+reenvio (chats protegidos)
- Troca dinâmica de estratégia ao detectar erros de proteção de conteúdo durante a clonagem
- Fallback para texto quando o download de mídia falha em chats protegidos
- Persistência de sessão via StringSession em session.txt (evita re-autenticação)

### Melhorado
- Detecção de proteção de conteúdo via GetFullChannelRequest/GetFullChatRequest (noforwards, restricted, protected)
- Filtragem de mensagens de serviço com contagem de puladas
- Exibição de tamanho de arquivo formatado (KB/MB) durante download e upload
- Delays ajustados: 0.5s entre textos, 2s entre mídias
- Feedback visual detalhado para fóruns (RAW reply_to, lotes por tópico)

### Corrigido
- Indentação do loop de lotes que processava apenas o último tópico do fórum
- Exibição da contagem de tópicos criados no destino

### Dependências
- FFmpeg (opcional, para otimização de vídeos)

## [1.3.0] - 2025-06-18

### Adicionado
- Interface gráfica (GUI) aprimorada com barra de progresso funcional em tempo real
- Exportação de histórico de clonagens em CSV
- Exibição de nome e link do canal de destino ao final da clonagem
- Integração segura com sinais (signals) do PyQt para atualização da interface
- Feedback visual detalhado durante todo o processo de clonagem

### Corrigido
- Problemas de atualização da barra de progresso
- Travamentos e erros de thread ao atualizar a interface

### Melhorado
- Experiência do usuário (UX) com status claros e responsivos
- Compatibilidade total entre terminal e GUI

[1.0.0]: https://github.com/seu-usuario/clonecat/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/seu-usuario/clonecat/releases/tag/v0.1.0
[1.1.0]: https://github.com/seu-usuario/clonecat/compare/v1.0.0...v1.1.0
[1.2.0]: https://github.com/seu-usuario/clonecat/compare/v1.1.0...v1.2.0
[1.3.0]: https://github.com/seu-usuario/clonecat/compare/v1.2.0...v1.3.0 