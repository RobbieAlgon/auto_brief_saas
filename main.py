from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
import groq
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import requests

load_dotenv()

# Validar variáveis de ambiente necessárias
required_env_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'GROQ_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuração do Google OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'https://auto-brief-saas.vercel.app/auth/callback')

# Configuração do Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Chave secreta fixa para sessões
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Adicionar filtro para formatar datas
@app.template_filter('datetime')
def format_datetime(value):
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return value
    return value

# Adicionar filtro para converter JSON em objeto Python
@app.template_filter('fromjson')
def from_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return value
    return value

# Initialize Supabase client
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Supabase client initialized successfully")
except Exception as e:
    print(f"Error initializing Supabase client: {str(e)}")
    raise

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email=None):
        self.id = id
        self._email = email
    
    @property
    def email(self):
        # Tentar obter o email da sessão se não estiver disponível
        if not self._email and 'user_email' in session:
            self._email = session['user_email']
        return self._email or "user@example.com"
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    try:
        # Verificar se o user_id está na sessão
        if 'user_id' in session and session['user_id'] == user_id:
            # Criar um usuário com o ID da sessão
            return User(session['user_id'])
        
        # Se não estiver na sessão, tentar criar com o ID fornecido
        if isinstance(user_id, str):
            return User(user_id)
    except Exception as e:
        print(f"Error loading user: {str(e)}")
    return None

@app.route('/')
def index():
    try:
        print("Accessing index route")
        print(f"Environment variables present: SUPABASE_URL={bool(os.getenv('SUPABASE_URL'))}, SUPABASE_KEY={bool(os.getenv('SUPABASE_KEY'))}, GROQ_API_KEY={bool(os.getenv('GROQ_API_KEY'))}")
        return render_template('index.html')
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route('/login')
def login():
    # Verificar se há um token na URL (fragmento)
    if request.args.get('access_token'):
        return redirect(url_for('auth_callback', access_token=request.args.get('access_token')))
    return render_template('login.html')

@app.route('/auth/google')
def google_login():
    try:
        # Usar uma URL dinâmica para o redirecionamento baseada no host atual
        host = request.host_url.rstrip('/')
        redirect_url = f"{host}/login"  # Mudamos para redirecionar para /login
        
        print(f"Redirect URL: {redirect_url}")
        
        auth_url = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url,
                "queryParams": {
                    "access_type": "offline",
                    "prompt": "consent"
                }
            }
        })
        return redirect(auth_url.url)
    except Exception as e:
        print(f"Error during Google login: {str(e)}")
        flash(f"Error during Google login: {str(e)}")
        return redirect(url_for('login'))

@app.route('/auth/callback')
def auth_callback():
    try:
        # Get the access token from the URL
        access_token = request.args.get('access_token')
        
        print(f"Callback received with params: {dict(request.args)}")
        print(f"Access token received: {access_token[:10] if access_token else 'None'}")
        
        if not access_token:
            flash("No access token provided")
            return redirect(url_for('login'))
        
        # Use the access token to get the user
        try:
            user_data = supabase.auth.get_user(access_token)
            print(f"User data response: {user_data}")
            
            if user_data and user_data.user:
                # Armazenar o email e ID na sessão
                session['user_email'] = user_data.user.email
                session['user_id'] = str(user_data.user.id)  # Garantir que o ID é uma string
                
                print(f"User authenticated: {user_data.user.id}, {user_data.user.email}")
                print(f"Session before login: {session}")
                
                # Criar o usuário com o ID e email
                user = User(str(user_data.user.id), user_data.user.email)  # Garantir que o ID é uma string
                login_user(user)
                
                # Forçar a sessão a ser salva
                session.modified = True
                
                print(f"Session after login: {session}")
                print(f"User authenticated: {current_user.is_authenticated}")
                print(f"User ID: {current_user.id}")
                
                return redirect(url_for('index'))
            else:
                flash("Failed to get user data")
                return redirect(url_for('login'))
        except Exception as e:
            print(f"Error getting user data: {str(e)}")
            flash(f"Error getting user data: {str(e)}")
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Error processing access token: {str(e)}")
        flash(f"Error processing access token: {str(e)}")
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    print(f"User authenticated: {current_user.is_authenticated}")
    print(f"User ID: {current_user.id}")
    print(f"User email: {current_user.email}")
    print(f"Session: {session}")
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    try:
        supabase.auth.sign_out()
        logout_user()
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error during logout: {str(e)}")
        return redirect(url_for('index'))

def generate_briefing(conversation):
    """
    Gera um briefing a partir de uma conversa usando a API Groq.
    
    Args:
        conversation (str): O texto da conversa a ser transformado em briefing
        
    Returns:
        dict: Um dicionário com o briefing estruturado
    """
    try:
        print(f"Gerando briefing para conversa: {conversation[:100]}...")
        
        # Inicializar o cliente Groq
        try:
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set")
            
            client = groq.Client()
            print("Groq client initialized successfully")
        except Exception as e:
            print(f"Error initializing Groq client: {str(e)}")
            raise
        
        # Prompt para a API Groq
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": """Você é um assistente especializado em criar briefings estruturados a partir de conversas.
                    
Analise cuidadosamente a conversa e extraia as informações relevantes para preencher o briefing.
Preencha TODOS os campos do briefing com informações específicas e detalhadas.
NUNCA deixe campos vazios ou com valores genéricos.

Estrutura do briefing:
- objetivo: O objetivo principal do projeto (obrigatório)
- publico_alvo: Descrição detalhada do público-alvo (obrigatório)
- referencias: Lista de referências mencionadas na conversa
- prazos: Informações sobre prazos
  - prazo_final: Data ou período para entrega final
  - etapas_intermediarias: Lista de etapas intermediárias com prazos
- orcamento: Informações financeiras
  - valor_total: Valor total do projeto
  - descontos: Valor dos descontos aplicados
  - valor_final: Valor final após descontos
- observacoes: Lista de observações importantes mencionadas na conversa

Retorne apenas o JSON puro, sem marcadores de código markdown.
Se alguma informação não estiver disponível na conversa, use valores realistas baseados no contexto."""
                },
                {
                    "role": "user",
                    "content": conversation
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            stream=False
        )
        
        # Extrair o conteúdo da resposta
        content = completion.choices[0].message.content
        print(f"Resposta da API Groq: {content}")
        
        # Converter a resposta para JSON
        try:
            briefing = json.loads(content)
            print(f"Briefing gerado com sucesso: {briefing}")
            return briefing
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON da resposta: {str(e)}")
            print(f"Conteúdo recebido: {content}")
            raise
            
    except Exception as e:
        print(f"Erro ao gerar briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def init_database():
    try:
        print("Inicializando banco de dados...")
        
        # Criar a tabela briefings se não existir
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS briefings (
            id BIGSERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            titulo TEXT,
            conteudo JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES auth.users(id)
        );
        """
        
        # Habilitar RLS e criar políticas
        enable_rls_sql = """
        ALTER TABLE briefings ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users can read their own briefings" ON briefings;
        CREATE POLICY "Users can read their own briefings"
            ON briefings
            FOR SELECT
            USING (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can insert their own briefings" ON briefings;
        CREATE POLICY "Users can insert their own briefings"
            ON briefings
            FOR INSERT
            WITH CHECK (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can update their own briefings" ON briefings;
        CREATE POLICY "Users can update their own briefings"
            ON briefings
            FOR UPDATE
            USING (auth.uid() = user_id)
            WITH CHECK (auth.uid() = user_id);
        
        DROP POLICY IF EXISTS "Users can delete their own briefings" ON briefings;
        CREATE POLICY "Users can delete their own briefings"
            ON briefings
            FOR DELETE
            USING (auth.uid() = user_id);
        """
        
        # Executar os comandos SQL
        supabase.table('briefings').select('*').limit(1).execute()
        print("Tabela briefings já existe")
    except Exception as e:
        print(f"Erro ao verificar tabela: {str(e)}")
        try:
            print("Tentando criar a tabela...")
            supabase.query(create_table_sql).execute()
            print("Tabela criada com sucesso")
            
            print("Configurando políticas...")
            supabase.query(enable_rls_sql).execute()
            print("Políticas configuradas com sucesso")
        except Exception as e:
            print(f"Erro ao criar tabela: {str(e)}")
            import traceback
            traceback.print_exc()

# Inicializar o banco de dados quando o aplicativo iniciar
init_database()

@app.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    if request.method == 'GET':
        return render_template('generate.html')
    
    try:
        data = request.get_json()
        conversation = data.get('conversation', '')
        
        if not conversation:
            return jsonify({"error": "No conversation provided"}), 400
        
        # Gerar o briefing usando a API Groq
        briefing = generate_briefing(conversation)
        
        # Adicionar o texto original da conversa ao briefing
        if isinstance(briefing, dict):
            briefing["texto_original"] = conversation
        
        # Salvar o briefing no Supabase
        if current_user.is_authenticated:
            # Extrair o título do briefing (usando o objetivo como título)
            titulo = "Novo Briefing"
            if isinstance(briefing, dict) and "objetivo" in briefing and briefing["objetivo"]:
                titulo = briefing["objetivo"]
            else:
                # Se não houver objetivo, use as primeiras palavras da conversa
                titulo = conversation[:50] + "..." if len(conversation) > 50 else conversation
            
            try:
                # Criar um objeto JSON com os dados do briefing
                conteudo = {
                    'input_text': conversation,
                    'briefing_result': briefing
                }
                
                # Tentar salvar o briefing
                result = supabase.table('briefings').insert({
                    'user_id': current_user.id,
                    'titulo': titulo,
                    'conteudo': conteudo
                }).execute()
                
                print(f"Resultado da inserção: {result}")
                
                if result.data:
                    print(f"Briefing salvo com ID: {result.data[0]['id']}")
                    briefing["id"] = result.data[0]["id"]
                else:
                    print("Não foi possível salvar o briefing")
                    return jsonify({"error": "Erro ao salvar briefing"}), 500
                    
            except Exception as e:
                print(f"Erro ao salvar briefing: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"Erro ao salvar briefing: {str(e)}"}), 500
        
        return jsonify(briefing)
    except Exception as e:
        print(f"Erro ao gerar briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/briefings')
@login_required
def list_briefings():
    try:
        print("Listando briefings...")
        
        # Buscar todos os briefings do usuário
        response = supabase.table("briefings").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        
        print(f"Resposta do Supabase: {response}")
        
        briefings = response.data
        print(f"Briefings encontrados: {briefings}")
        
        # Processar cada briefing
        for briefing in briefings:
            # Inicializar campos padrão
            briefing['input_text'] = ''
            briefing['briefing_result'] = {}
            briefing['titulo'] = 'Novo Brief'
            
            # Processar o campo conteudo para extrair input_text e briefing_result
            if 'conteudo' in briefing and briefing['conteudo']:
                conteudo = briefing['conteudo']
                print(f"Conteúdo do briefing {briefing['id']}: {conteudo}")
                
                # Converter para dicionário se for string
                if isinstance(conteudo, str):
                    try:
                        conteudo = json.loads(conteudo)
                        print(f"Conteúdo convertido de string para dicionário: {conteudo}")
                    except Exception as e:
                        print(f"Erro ao converter conteúdo para dicionário: {str(e)}")
                        conteudo = {}
                
                # Extrair informações do conteudo
                if isinstance(conteudo, dict):
                    briefing['input_text'] = conteudo.get('input_text', '')
                    briefing_result = conteudo.get('briefing_result', {})
                    print(f"Briefing result extraído: {briefing_result}")
                    
                    # Converter briefing_result para dicionário se for string
                    if isinstance(briefing_result, str):
                        try:
                            briefing_result = json.loads(briefing_result)
                            print(f"Briefing result convertido de string para dicionário: {briefing_result}")
                        except Exception as e:
                            print(f"Erro ao converter briefing_result para dicionário: {str(e)}")
                            briefing_result = {}
                    
                    briefing['briefing_result'] = briefing_result
                    print(f"Briefing result final: {briefing['briefing_result']}")
                    
                    # Extrair título do briefing_result
                    if isinstance(briefing['briefing_result'], dict) and 'objetivo' in briefing['briefing_result']:
                        briefing['titulo'] = briefing['briefing_result']['objetivo']
                        print(f"Título extraído: {briefing['titulo']}")
        
        print(f"Briefings processados para exibição: {briefings}")
        return render_template('briefings.html', briefings=briefings)
    except Exception as e:
        print(f"Erro ao listar briefings: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao listar briefings: {str(e)}")
        return redirect(url_for('index'))

@app.route('/briefing/<id>')
@login_required
def view_briefing(id):
    try:
        print(f"Buscando briefing com ID: {id} (tipo: {type(id)})")
        
        # Buscar o briefing específico e verificar se pertence ao usuário
        response = supabase.table("briefings").select("*").eq("id", id).eq("user_id", current_user.id).single().execute()
        
        print(f"Resposta do Supabase: {response}")
        
        if not response.data:
            flash("Briefing não encontrado")
            return redirect(url_for('list_briefings'))
            
        briefing = response.data
        print(f"Briefing encontrado: {briefing}")
        
        # Processar o campo conteudo para extrair input_text e briefing_result
        if 'conteudo' in briefing and briefing['conteudo']:
            conteudo = briefing['conteudo']
            print(f"Conteúdo do briefing: {conteudo}")
            
            # Se conteudo for uma string, tentar converter para JSON
            if isinstance(conteudo, str):
                try:
                    conteudo = json.loads(conteudo)
                except json.JSONDecodeError as e:
                    print(f"Erro ao decodificar JSON do conteúdo: {str(e)}")
                    conteudo = {}
            
            # Extrair input_text e briefing_result do conteudo
            if isinstance(conteudo, dict):
                briefing['input_text'] = conteudo.get('input_text', '')
                briefing['briefing_result'] = conteudo.get('briefing_result', {})
                
                # Se briefing_result for uma string, tentar converter para JSON
                if isinstance(briefing['briefing_result'], str):
                    try:
                        briefing['briefing_result'] = json.loads(briefing['briefing_result'])
                    except json.JSONDecodeError as e:
                        print(f"Erro ao decodificar JSON do briefing_result: {str(e)}")
                        briefing['briefing_result'] = {}
        
        print(f"Briefing processado para exibição: {briefing}")
        return render_template('briefing.html', briefing=briefing)
    except Exception as e:
        print(f"Erro ao buscar briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao buscar briefing: {str(e)}")
        return redirect(url_for('list_briefings'))

@app.route('/history')
@login_required
def history():
    try:
        print("Listando histórico de briefings...")
        
        # Buscar briefings do usuário ordenados por data
        response = supabase.table("briefings").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        
        print(f"Resposta do Supabase: {response}")
        
        if response.data:
            briefings = response.data
            print(f"Briefings encontrados: {briefings}")
            
            # Processar os briefings para extrair informações do campo conteudo
            for briefing in briefings:
                # Inicializar campos padrão
                briefing['input_text'] = ''
                briefing['briefing_result'] = {}
                briefing['titulo'] = "Novo Briefing"
                
                # Processar o campo conteudo se existir
                if 'conteudo' in briefing and briefing['conteudo']:
                    content = briefing['conteudo']
                    print(f"Content do briefing {briefing['id']}: {content}")
                    
                    # Converter para dicionário se for string
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                            print(f"Content convertido de string para dicionário: {content}")
                        except Exception as e:
                            print(f"Erro ao converter content para dicionário: {str(e)}")
                            content = {}
                    
                    # Extrair informações do content
                    if isinstance(content, dict):
                        briefing['input_text'] = content.get('input_text', '')
                        briefing_result = content.get('briefing_result', {})
                        print(f"Briefing result extraído: {briefing_result}")
                        
                        # Converter briefing_result para dicionário se for string
                        if isinstance(briefing_result, str):
                            try:
                                briefing_result = json.loads(briefing_result)
                                print(f"Briefing result convertido de string para dicionário: {briefing_result}")
                            except Exception as e:
                                print(f"Erro ao converter briefing_result para dicionário: {str(e)}")
                                briefing_result = {}
                        
                        briefing['briefing_result'] = briefing_result
                        print(f"Briefing result final: {briefing['briefing_result']}")
                        
                        # Definir título a partir do objetivo
                        if isinstance(briefing_result, dict) and 'objetivo' in briefing_result:
                            briefing['titulo'] = briefing_result['objetivo']
                            print(f"Título extraído: {briefing['titulo']}")
            
            print(f"Briefings processados para exibição: {briefings}")
            return render_template('history.html', briefings=briefings)
        else:
            print("Nenhum briefing encontrado")
            return render_template('history.html', briefings=[])
            
    except Exception as e:
        print(f"Erro ao carregar histórico de briefings: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Erro ao carregar histórico de briefings', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<id>')
@login_required
def delete_briefing(id):
    try:
        print(f"Tentando excluir briefing com ID: {id} (tipo: {type(id)})")
        
        # Verificar se o briefing existe e pertence ao usuário
        response = supabase.table("briefings").select("id").eq("id", id).eq("user_id", current_user.id).single().execute()
        
        print(f"Resposta da verificação: {response}")
        
        if not response.data:
            flash('Briefing não encontrado ou você não tem permissão para excluí-lo', 'error')
            return redirect(url_for('list_briefings'))
        
        # Excluir o briefing
        delete_response = supabase.table("briefings").delete().eq("id", id).execute()
        print(f"Resposta da exclusão: {delete_response}")
        
        flash('Briefing excluído com sucesso', 'success')
        return redirect(url_for('list_briefings'))
        
    except Exception as e:
        print(f"Erro ao excluir briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Erro ao excluir briefing', 'error')
        return redirect(url_for('list_briefings'))

def save_briefing(user_id, input_text, briefing_result):
    try:
        conteudo = {
            "input_text": input_text,
            "briefing_result": briefing_result
        }
        
        response = supabase.table('briefings').insert({
            "user_id": user_id,
            "titulo": briefing_result.get("objetivo", "Novo Briefing"),
            "conteudo": conteudo
        }).execute()
        
        return response.data[0]
    except Exception as e:
        print(f"Erro ao salvar briefing: {str(e)}")
        raise

@app.route('/save_briefing', methods=['POST'])
@login_required
def save_briefing_route():
    try:
        data = request.get_json()
        input_text = data.get('input_text', '')
        briefing_result = data.get('briefing_result', {})
        
        if not input_text or not briefing_result:
            return jsonify({"error": "Dados incompletos"}), 400
        
        # Extrair o título do briefing (usando o objetivo como título)
        titulo = "Novo Briefing"
        if isinstance(briefing_result, dict) and "objetivo" in briefing_result and briefing_result["objetivo"]:
            titulo = briefing_result["objetivo"]
        else:
            # Se não houver objetivo, use as primeiras palavras do input_text
            titulo = input_text[:50] + "..." if len(input_text) > 50 else input_text
        
        # Criar um objeto JSON com os dados do briefing
        conteudo = {
            'input_text': input_text,
            'briefing_result': briefing_result
        }
        
        # Salvar o briefing no Supabase
        result = supabase.table('briefings').insert({
            'user_id': current_user.id,
            'titulo': titulo,
            'conteudo': conteudo
        }).execute()
        
        print(f"Resultado da inserção: {result}")
        
        if result.data:
            print(f"Briefing salvo com ID: {result.data[0]['id']}")
            return jsonify({"success": True, "id": result.data[0]['id']})
        else:
            print("Não foi possível salvar o briefing")
            return jsonify({"error": "Erro ao salvar briefing"}), 500
            
    except Exception as e:
        print(f"Erro ao salvar briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro ao salvar briefing: {str(e)}"}), 500

@app.errorhandler(Exception)
def handle_error(error):
    print(f"Unhandled error: {str(error)}")
    import traceback
    traceback.print_exc()
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

if __name__ == '__main__':
    app.run(debug=True)