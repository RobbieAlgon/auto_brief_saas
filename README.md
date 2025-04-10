# Sistema de Briefings

Sistema para geração e gerenciamento de briefings usando IA.

## Funcionalidades

- Geração de briefings usando IA (Groq)
- Autenticação de usuários
- Armazenamento de briefings no Supabase
- Interface web responsiva

## Tecnologias Utilizadas

- Python/Flask (Backend)
- Supabase (Banco de dados)
- Groq (IA)
- HTML/CSS/JavaScript (Frontend)

## Configuração do Ambiente

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`:
```
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_do_supabase
GROQ_API_KEY=sua_chave_da_groq
SECRET_KEY=sua_chave_secreta
```

4. Execute o servidor:
```bash
python main.py
```

## Deploy na Vercel

1. Crie uma conta na [Vercel](https://vercel.com)
2. Instale a CLI da Vercel:
```bash
npm i -g vercel
```

3. Faça login na Vercel:
```bash
vercel login
```

4. Deploy do projeto:
```bash
vercel
```

5. Configure as variáveis de ambiente na Vercel:
- SUPABASE_URL
- SUPABASE_KEY
- GROQ_API_KEY
- SECRET_KEY

## Estrutura do Projeto

```
.
├── main.py              # Aplicação Flask
├── requirements.txt     # Dependências Python
├── vercel.json         # Configuração Vercel
├── .env                # Variáveis de ambiente
└── templates/          # Templates HTML
    ├── index.html
    ├── login.html
    └── register.html
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request 