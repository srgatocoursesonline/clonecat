# CloneCat - Telegram Channel Cloner 🐱

![CloneCat Logo](https://github.com/user-attachments/assets/30f8f1de-3f37-48b6-9b2a-9918b4a3f7c8)

CloneCat é uma ferramenta poderosa e automatizada para clonar canais do Telegram. Com ela, você pode copiar mensagens, mídias (fotos, vídeos, áudios, documentos) e menus de um canal de origem para um novo canal automaticamente criado.

## ✨ Funcionalidades

- 📝 Clona mensagens de texto, fotos, vídeos, áudios e documentos
- 🖼️ Mantém as legendas associadas às mídias
- 📋 Adiciona automaticamente o menu existente no canal original
- 🎯 Gera automaticamente um canal de destino com nome baseado no canal original
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

3. Digite o ID do canal de origem

4. Selecione o tipo de conteúdo que deseja clonar:
   - Todas as Mensagens
   - Apenas Imagens
   - Apenas Vídeos
   - Apenas Áudios
   - Apenas Documentos
   - Apenas Texto
   - Apenas Stickers
   - Tudo

5. Aguarde a conclusão do processo

## ⚠️ Considerações Importantes

- O script respeita os limites do Telegram com intervalo padrão de 5 segundos entre mensagens
- Evite clonar canais com grandes volumes de dados em curto intervalo
- Mantenha suas credenciais do Telegram seguras
- O script salva logs de erros em `erros.log`
- **Atenção:** Para clonar mídias (fotos, vídeos, áudios, documentos), é necessário que a opção "Restringir salvamento de conteúdo" esteja DESATIVADA no canal de origem. Caso contrário, o Telegram bloqueia o acesso via API, mesmo para administradores.
- Se o canal for privado, sua conta precisa ser administradora ou membro antigo para acessar todo o histórico.
- O script possui uma verificação inteligente e avisa caso a proteção de conteúdo esteja ativada ou sua conta não tenha permissão suficiente.
- Possíveis mensagens de erro explicam como proceder para liberar o acesso ao conteúdo.

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
