import sqlite3

# Crie o banco de dados SQLite e a tabela 'pontuacoes'
conn = sqlite3.connect('pontuacoes.db')
cursor = conn.cursor()

# Criação da tabela
cursor.execute('''
CREATE TABLE IF NOT EXISTS pontuacoes (
    dynamic TEXT,
    code TEXT,
    score INTEGER
)
''')

# Adicionando alguns dados de exemplo
cursor.executemany('''
INSERT INTO pontuacoes (dynamic, code, score) VALUES (?, ?, ?)
''', [
    ('Jogo 1', 'Equipe A', 10),
    ('Jogo 1', 'Equipe B', 12),
    ('Jogo 1', 'Equipe A', 15),
    ('Jogo 1', 'Equipe B', 17),
    ('Jogo 1', 'Equipe A', 20),
    ('Jogo 1', 'Equipe B', 30),
    ('Jogo 1', 'Equipe A', 40),
    ('Jogo 1', 'Equipe B', 50),
    ('Jogo 1', 'Equipe B', 50),
    ('Jogo 1', 'Equipe C', 51),
    ('Jogo 1', 'Equipe C', 49),
    ('Jogo 1', 'Equipe C', 48),
    ('Jogo 1', 'Equipe C', 35),
])

conn.commit()
conn.close()