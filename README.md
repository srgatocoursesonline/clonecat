# CloneCat - Telegram Channel Cloner 🐱

![CloneCat Logo](https://github.com/user-attachments/assets/30f8f1de-3f37-48b6-9b2a-9918b4a3f7c8)

CloneCat é uma ferramenta poderosa e automatizada para clonar chats do Telegram. Com ela, você pode copiar mensagens, mídias (fotos, vídeos, áudios, documentos) e menus de um chat de origem para um destino automaticamente criado — com suporte a canais, grupos, supergrupos e fóruns com tópicos.

## ✨ Funcionalidades

- 📝 Clona mensagens de texto, fotos, vídeos, áudios e documentos
- 🖼️ Mantém as legendas associadas às mídias
- 📋 Adiciona automaticamente o menu existente no chat original
- 🎯 Gera automaticamente um destino com nome baseado no chat original
- 🧵 Suporte completo a supergrupos com tópicos (fórum): cria e mapeia todos os tópicos no destino
- 💬 Preserva cadeias de respostas (reply chain) entre mensagens clonadas
- 🔄 Retomada inteligente: salva progresso a cada 20 mensagens e permite continuar de onde parou
- ⏯️ Clonagem incremental: execute novamente para clonar apenas mensagens novas
- 🎬 Otimização de vídeos via FFmpeg para streaming no Telegram
- ⚡ Pipeline paralelo: baixa a próxima mídia em background enquanto envia a atual
- 🛡️ Duas estratégias de clonagem: envio anônimo (rápido) e download+reenvio (para chats protegidos)
- ⏱️ Respeita limites do Telegram para evitar bans, com intervalo configurável
- 🔄 Suporte a diferentes tipos de conteúdo (texto, mídia, stickers)
- 📊 Barra de progresso em tempo real
- 🎨 Interface colorida no terminal

## 🚀 Pré-requisitos

- Python 3.8 ou superior
- Conta no Telegram
- API ID e API Hash do Telegram

## 📦 Instalação

1. Clone este repositório:
```bash
git clone https://github.com/seu-usuario/clonecat.git
cd clonecat
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Obtenha suas credenciais do Telegram:
   - Acesse https://my.telegram.org/
   - Faça login com seu número de telefone
   - Vá em "API development tools"
   - Crie um novo aplicativo
   - Copie o `api_id` e `api_hash`

## 💻 Uso

1. Execute o script:
```bash
python clonecat.py
```

2. Na primeira execução, insira suas credenciais do Telegram (API ID e API Hash)

3. Digite o ID do chat de origem (ID numérico)

4. Selecione o tipo de conteúdo que deseja clonar:
   - Todas as Mensagens
   - Apenas Imagens
   - Apenas Vídeos
   - Apenas Áudios
   - Apenas Documentos
   - Apenas Texto
   - Apenas Stickers
   - Tudo (Mensagens, Imagens, Vídeos, Áudios, Stickers, Documentos...)

5. Aguarde a conclusão do processo. Se precisar interromper, pressione Ctrl+C — o progresso será salvo automaticamente. Execute novamente e escolha retomar de onde parou.

## 🖥️ Interface Gráfica (GUI)

- Interface moderna com tema escuro
- Barra de progresso em tempo real
- Exportação de histórico de clonagens em CSV
- Exibição de nome e link do canal de destino ao final da clonagem
- Totalmente integrada com a lógica do terminal (CLI)

### Como usar a GUI

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a interface gráfica:
   ```bash
   python -m gui.main_window
   ```
3. Preencha o ID do chat de origem e, se quiser, o destino manualmente (opcional).
4. Clique em "Iniciar Clonagem" e acompanhe o progresso em tempo real.
5. Ao final, exporte o histórico se desejar.

## ⚠️ Considerações Importantes

- O script respeita os limites do Telegram com intervalo de 0.5s entre textos e 2s entre mídias
- Evite clonar chats com grandes volumes de dados em curto intervalo
- Mantenha suas credenciais do Telegram seguras
- O script salva logs de erros em `erros.log`
- **Proteção de conteúdo:** Se o chat de origem tiver "Restringir salvamento de conteúdo" ativado, mídias serão baixadas localmente e reenviadas. Caso o download também seja bloqueado, apenas o texto/legenda será clonado.
- O script detecta automaticamente o tipo de chat (canal, grupo, supergrupo, fórum) e cria o destino compatível.
- Para fóruns, todos os tópicos são recriados no destino e as mensagens são roteadas para o tópico correto.
- **FFmpeg:** Instale o FFmpeg no sistema para otimização de vídeos (opcional, mas recomendado).

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

Mr. Cat

---
⭐️ Se este projeto te ajudou, considere dar uma estrela!
