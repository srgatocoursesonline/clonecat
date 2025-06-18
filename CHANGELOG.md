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

[1.0.0]: https://github.com/seu-usuario/clonecat/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/seu-usuario/clonecat/releases/tag/v0.1.0 