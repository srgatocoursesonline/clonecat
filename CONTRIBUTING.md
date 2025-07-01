# Contribuindo com o Clonecat

Primeiramente, obrigado por considerar contribuir com o Clonecat! 🎉

## Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Contribuir](#como-contribuir)
3. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
4. [Padrões de Código](#padrões-de-código)
5. [Testes](#testes)
6. [Documentação](#documentação)
7. [Pull Requests](#pull-requests)

## Código de Conduta

Este projeto segue um Código de Conduta. Ao participar, você concorda em seguir suas diretrizes.

### Nosso Compromisso

- Ser respeitoso com diferentes pontos de vista
- Aceitar críticas construtivas
- Focar no que é melhor para a comunidade
- Mostrar empatia com outros membros

## Como Contribuir

### Reportando Bugs

1. Verifique se o bug já não foi reportado
2. Abra uma issue usando o template de bug
3. Inclua:
   - Versão do software
   - Sistema operacional
   - Passos para reproduzir
   - Comportamento esperado
   - Screenshots se possível

### Sugerindo Melhorias

1. Verifique se a sugestão já não existe
2. Abra uma issue usando o template de feature
3. Descreva detalhadamente:
   - O problema que resolve
   - Como deveria funcionar
   - Possíveis impactos

### Contribuindo com Código

1. Fork do repositório
2. Clone seu fork
3. Crie uma branch:
   ```bash
   git checkout -b feature/MinhaFeature
   ```
4. Faça suas alterações
5. Commit usando mensagens descritivas:
   ```bash
   git commit -m "Adiciona: nova feature X"
   ```
6. Push para seu fork:
   ```bash
   git push origin feature/MinhaFeature
   ```
7. Abra um Pull Request

## Ambiente de Desenvolvimento

### Requisitos

- Python 3.8+
- PyQt5
- Git

### Setup

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/clonecat.git
   cd clonecat
   ```

2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Padrões de Código

### Python

- Siga o PEP 8
- Use type hints
- Docstrings em todas as funções
- Nomes descritivos em português
- Comentários quando necessário

### Commits

- Mensagens em português
- Primeira linha <= 50 caracteres
- Corpo <= 72 caracteres por linha
- Use prefixos:
  - `Adiciona:` nova feature
  - `Corrige:` correção de bug
  - `Atualiza:` atualização
  - `Remove:` remoção
  - `Refatora:` refatoração

### Branches

- `master`: produção
- `develop`: desenvolvimento
- `feature/*`: novas features
- `bugfix/*`: correções
- `hotfix/*`: correções urgentes

## Testes

### Executando Testes

```bash
# Todos os testes
pytest

# Módulo específico
pytest tests/test_downloader.py

# Com cobertura
pytest --cov=src
```

### Escrevendo Testes

- Um teste por funcionalidade
- Nomes descritivos
- Setup e teardown quando necessário
- Mocks para dependências externas
- Cobertura mínima de 80%

## Documentação

### Código

- Docstrings em todas as classes/funções
- Exemplos de uso
- Parâmetros e retornos
- Exceções lançadas

### Projeto

- README atualizado
- Documentação de API
- Guias de uso
- Exemplos práticos

## Pull Requests

### Checklist

- [ ] Testes passando
- [ ] Cobertura mantida/aumentada
- [ ] Código seguindo padrões
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Versão bumped se necessário

### Review

- Seja construtivo
- Explique suas sugestões
- Use exemplos
- Agradeça contribuições

## Dúvidas?

- Abra uma issue
- Pergunte no Discord
- Envie um email
- Consulte a documentação 