import sqlite3
from datetime import datetime, timezone, timedelta

# Configuração de datetime para SQLite
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda value: datetime.fromisoformat(value.decode() if isinstance(value, bytes) else value))

def inicializar_bd(cursor, conn, turmas, alunos):
    """Cria tabelas de votos e de turmas com alunos cadastrados."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            turma TEXT NOT NULL,
            voto TEXT NOT NULL,
            horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    for turma in turmas:
        turma = turma.replace(" ", "_").replace("#", "")  # Garante nomes seguros para tabelas
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{turma}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
        ''')

        if turma in alunos:
            cursor.executemany(f'INSERT OR IGNORE INTO "{turma}" (nome, email) VALUES (?, ?)', alunos[turma])
    
    conn.commit()

def contar_alunos_por_periodo(cursor, periodo_turmas):
    """Conta o total de alunos cadastrados em todas as turmas de um período."""
    return sum(cursor.execute(f'SELECT COUNT(*) FROM "{turma}"').fetchone()[0] for turma in periodo_turmas)

def contar_votantes_por_periodo(cursor, periodo_turmas):
    """Conta o total de alunos que já votaram em um período."""
    return sum(cursor.execute("SELECT COUNT(DISTINCT email) FROM votos WHERE turma = ?", (turma,)).fetchone()[0] or 0 for turma in periodo_turmas)

def processar_voto(turma, cursor, conn):
    """Solicita o nome de usuário e processa o voto do aluno."""
    email_usuario = input(f"Digite seu nome de usuário (sem @escola.pr.gov.br) para a turma {turma}: ").strip()
    email = f"{email_usuario}@escola.pr.gov.br"

    cursor.execute(f'SELECT nome FROM "{turma}" WHERE email = ?', (email,))
    aluno = cursor.fetchone()
    cursor.execute("SELECT * FROM votos WHERE email = ?", (email,))
    duplicado = bool(aluno and cursor.fetchone())

    if aluno:
        nome = aluno[0]
        if duplicado:
            print(f"{nome}, você já votou.")
        else:
            print(f"Bem-vindo(a), {nome}!")
            opcoes = {'1': 'Chapa 1', '2': 'Voto Nulo', '3': 'Voto em Branco'}
            voto = input("\nEscolha sua opção:\n1 - Chapa 1\n2 - Voto Nulo\n3 - Voto em Branco\nDigite o número correspondente: ")
            if voto in opcoes:
                horario_local = datetime.now(timezone.utc) - timedelta(hours=3)
                cursor.execute("INSERT INTO votos (email, turma, voto, horario) VALUES (?, ?, ?, ?)", (email, turma, opcoes[voto], horario_local))
                conn.commit()
                print("Voto registrado com sucesso!")
                print()  # Primeira quebra de linha
                print()  # Segunda quebra de linha 
            else:
                print("Opção inválida.")
    else:
        print("E-mail não cadastrado.")

def exibir_relatorios(cursor, turmas):
    """Solicita senha antes de exibir os relatórios sobre a votação."""
    senha_correta = "s3nh4s3cr3t4"
    senha = input("Digite a senha para acessar os relatórios: ")

    if senha != senha_correta:
        print("Senha incorreta. Acesso negado.")
        return

    while True:
        print("\nEscolha o relatório desejado:")
        print("1 - Relatório de turmas")
        print("2 - Relatório da quantidade de votos")
        print("3 - Voltar ao menu principal")

        opcao_relatorio = input("Escolha: ").strip()

        if opcao_relatorio == "1":
            print("\nRelatórios de Votação por Turma:")
            for turma in turmas:
                total_alunos = cursor.execute(f'SELECT COUNT(*) FROM "{turma}"').fetchone()[0]
                total_votantes = cursor.execute("SELECT COUNT(DISTINCT email) FROM votos WHERE turma = ?", (turma,)).fetchone()[0] or 0

                print(f"\nTurma: {turma}")
                print(f"- Total de alunos cadastrados: {total_alunos}")
                print(f"- Total de votantes até agora: {total_votantes}")
                print(f"- Alunos que ainda não votaram: {total_alunos - total_votantes}")

        elif opcao_relatorio == "2":
            print("\nRelatório da quantidade de votos:")
            resultados = cursor.execute("""
                SELECT voto, COUNT(*) FROM votos GROUP BY voto
            """).fetchall()

            for voto, quantidade in resultados:
                print(f"{voto}: {quantidade} votos")

        elif opcao_relatorio == "3":
            break
        else:
            print("Opção inválida.")

    input("\nPressione Enter para voltar ao menu principal...")

def main():
    """Fluxo principal do sistema de votação."""
    turmas = {
        "Matutino": ["9MA", "9MB", "9MC", "9MD", "1MA", "1MB", "1ADM", "2MA", "2DS", "3DS", "3MA"],
        "Vespertino": ["6TA", "6TB", "6TC", "6TD", "7TA", "7TB", "7TC", "7TD", "8TA", "8TB", "8TC", "8TD"]
    }
    alunos = {
        "1MB": [("Aluno C", "alunoC@exemplo.com"), ("Aluno D", "alunoD@exemplo.com")]
    }

    conn = sqlite3.connect('sisvoto.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    inicializar_bd(cursor, conn, turmas["Matutino"] + turmas["Vespertino"], alunos)

    while True:
        print("\nBem-vindo ao Sistema de Votação!")
        print("\nSelecione a opção desejada:")
        print("1 - Votação - Matutino")
        print("2 - Votação - Vespertino")
        print("3 - Relatórios")
        print("4 - Sair")

        opcao = input("Escolha: ").strip()

        if opcao in ("1", "2"):
            periodo_turmas = turmas["Matutino"] if opcao == "1" else turmas["Vespertino"]
            total_alunos = contar_alunos_por_periodo(cursor, periodo_turmas)
            total_votantes = contar_votantes_por_periodo(cursor, periodo_turmas)

            print(f"\nPeríodo {'Matutino' if opcao == '1' else 'Vespertino'}:")
            print(f"- Total de alunos cadastrados: {total_alunos}")
            print(f"- Total de votantes até agora: {total_votantes}")
            print(f"- Alunos que ainda não votaram: {total_alunos - total_votantes}")

            while True:
                for i, turma in enumerate(periodo_turmas, 1):
                    print(f"{i} - Votar na turma {turma}")
                print(f"{len(periodo_turmas) + 1} - Voltar ao menu principal")

                escolha_turma = input("Escolha: ")
                if escolha_turma.isdigit():
                    escolha_turma = int(escolha_turma)
                    if 1 <= escolha_turma <= len(periodo_turmas):
                        processar_voto(periodo_turmas[escolha_turma - 1], cursor, conn)
                    elif escolha_turma == len(periodo_turmas) + 1:
                        break
                    else:
                        print("Opção inválida.")
                else:
                    print("Opção inválida.")

        elif opcao == "3":
            exibir_relatorios(cursor, turmas["Matutino"] + turmas["Vespertino"])
        elif opcao == "4":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

    conn.close()

if __name__ == "__main__":
    main()