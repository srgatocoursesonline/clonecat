# Perguntas Frequentes (FAQ)

## Geral

### O que é o Clonecat?
O Clonecat é uma ferramenta desktop para download e backup de conteúdo do Telegram, com interface gráfica moderna e recursos avançados.

### É gratuito?
Sim, o Clonecat é totalmente gratuito e open source, distribuído sob a licença MIT.

### Quais sistemas operacionais são suportados?
- Windows 10/11
- macOS 10.14+
- Linux (principais distribuições)

## Instalação

### Como obter as credenciais do Telegram?
1. Acesse [my.telegram.org](https://my.telegram.org)
2. Faça login com seu número
3. Vá em "API development tools"
4. Crie um novo aplicativo
5. Guarde o `api_id` e `api_hash`

### Por que preciso de credenciais?
As credenciais são necessárias para acessar a API do Telegram de forma segura e autorizada.

### Como instalar em modo portable?
Basta extrair o arquivo ZIP em qualquer pasta e executar o programa. Todas as configurações serão salvas localmente.

## Uso

### Qual a velocidade máxima de download?
A velocidade depende de vários fatores:
- Sua conexão com a internet
- Limites do Telegram
- Configurações de delay
- Tipo de conteúdo

### Como retomar downloads interrompidos?
O Clonecat possui sistema automático de retomada. Basta reiniciar o download que ele continuará de onde parou.

### Posso baixar de canais privados?
Sim, desde que você seja membro do canal.

### Como exportar o histórico?
1. Acesse a aba "Histórico"
2. Clique em "Exportar"
3. Escolha o formato (CSV)
4. Selecione o destino

## Problemas Comuns

### Downloads muito lentos
- Verifique sua conexão
- Ajuste DOWNLOAD_DELAY no .env
- Use um proxy
- Verifique os limites do Telegram

### Erro de autenticação
- Verifique suas credenciais
- Renove a sessão
- Verifique restrições do canal

### Downloads incompletos
- Verifique permissões
- Libere espaço em disco
- Aumente MAX_RETRIES

## Recursos

### Tipos de mídia suportados
- Vídeos (MP4, AVI, MKV)
- Áudios (MP3, WAV, OGG)
- Imagens (JPG, PNG, GIF)
- Documentos (PDF, DOC, ZIP)
- Stickers (WEBP, TGS)
- Mensagens (TXT, HTML)

### Limites de download
- Tamanho máximo: 2GB por arquivo
- Downloads simultâneos: 5 (configurável)
- Velocidade: 5-10 MB/s (média)

### Recursos de segurança
- Criptografia de credenciais
- Validação de arquivos
- Proteção contra flood
- Rate limiting

## Contribuindo

### Como reportar bugs?
1. Abra uma issue no GitHub
2. Descreva o problema
3. Inclua logs e screenshots
4. Aguarde feedback

### Como sugerir features?
1. Verifique se já não existe
2. Abra uma issue
3. Descreva detalhadamente
4. Justifique a necessidade

### Como contribuir com código?
1. Fork do projeto
2. Nova branch
3. Commit das mudanças
4. Push para a branch
5. Pull Request 