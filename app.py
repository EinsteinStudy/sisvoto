from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"  # Necessário para utilizar mensagens flash (e sessões)

# Configuração de datetime para SQLite
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda value: datetime.fromisoformat(value.decode() if isinstance(value, bytes) else value))

# Função para obter conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect('sisvoto.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # Para retornar resultados como dict-like (facilitando o uso no template)
    return conn

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para votação em uma turma específica
@app.route('/votar/<turma>', methods=['GET', 'POST'])
def votar(turma):
    if request.method == 'POST':
        # Extrai os dados enviados do formulário HTML
        email_usuario = request.form.get('email', '').strip()
        email = f"{email_usuario}@escola.pr.gov.br"
        voto_opcao = request.form.get('voto')

        # Conecta ao BD e verifica se o aluno está cadastrado na turma
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT nome FROM "{turma}" WHERE email = ?', (email,))
        aluno = cursor.fetchone()

        if aluno is None:
            flash("E-mail não cadastrado para essa turma!", "error")
            conn.close()
            return redirect(url_for('votar', turma=turma))

        # Verifica se o aluno já votou
        cursor.execute("SELECT * FROM votos WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            flash("Você já votou.", "info")
            conn.close()
            return redirect(url_for('votar', turma=turma))

        # Define as opções de voto
        opcoes = {'1': 'Chapa 1', '2': 'Voto Nulo', '3': 'Voto em Branco'}
        if voto_opcao not in opcoes:
            flash("Opção inválida.", "error")
            conn.close()
            return redirect(url_for('votar', turma=turma))

        # Registra o voto
        horario_local = datetime.now(timezone.utc) - timedelta(hours=3)
        cursor.execute("INSERT INTO votos (email, turma, voto, horario) VALUES (?, ?, ?, ?)",
                       (email, turma, opcoes[voto_opcao], horario_local))
        conn.commit()
        conn.close()

        flash("Voto registrado com sucesso!", "success")
        return redirect(url_for('index'))

    # Para método GET, renderiza o formulário de votação
    return render_template('votar.html', turma=turma)

# Rota para exibir um relatório simples (pode ser expandido conforme sua necessidade)
@app.route('/relatorios')
def relatorios():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Exemplo: consulta simples dos votos agrupados
    cursor.execute("SELECT voto, COUNT(*) AS total FROM votos GROUP BY voto")
    resultados = cursor.fetchall()
    conn.close()

    return render_template('relatorios.html', resultados=resultados)

if __name__ == '__main__':
    app.run(debug=True)
