# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2024-03-30

### Adicionado
- Nova interface gráfica moderna com PyQt5
- Sistema de temas claro/escuro
- Barra de progresso avançada
- Histórico de downloads com exportação CSV
- Sistema de cache SQLite para retomar downloads
- Sistema de recuperação automática
- Suporte a múltiplos downloads simultâneos

### Alterado
- Migração de PyQt6 para PyQt5 para melhor compatibilidade
- Reestruturação completa do código em módulos
- Melhorias na organização dos arquivos
- Atualização das dependências

### Removido
- Suporte a clonagem de canais (agora focado em download)
- Dependências desnecessárias

## [1.0.0] - 2024-02-15

### Adicionado
- Interface gráfica inicial com PyQt6
- Funcionalidade básica de clonagem de canais
- Suporte a diferentes tipos de mídia
- Sistema básico de logs
- Documentação inicial

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