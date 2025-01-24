import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Função para obter os dados do banco de dados
def get_data_from_db():
    conn = sqlite3.connect('pontuacoes.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT dynamic, code, score FROM report ORDER BY code")
    rows = cursor.fetchall()
    conn.close()

    return rows

# Função para gerar o gráfico
def generate_plot(data):
    equipes = list(set(row[1] for row in data))  # `code` é a equipe
    cores = plt.cm.get_cmap('tab20', len(equipes))  # Melhor paleta de cores

    plt.figure(figsize=(12, 6))

    for i, equipe in enumerate(equipes):
        pontos = [row[2] for row in data if row[1] == equipe]  # `score` é a pontuação
        plt.plot(pontos, label=equipe, color=cores(i), marker='o', markersize=8, linewidth=3)

    plt.title('Pontuação das Equipes', fontsize=16, weight='bold')
    plt.xlabel('Número de Rodadas', fontsize=14)
    plt.ylabel('Pontuação', fontsize=14)
    plt.legend(loc='upper left', fontsize=12)

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Salvando o gráfico em um buffer de memória
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Codificando o gráfico em base64 para exibição em HTML
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return img_str

@app.route('/')
def index():
    # Obtendo os dados do banco de dados
    data = get_data_from_db()
    
    # Obtendo o título dinâmico (campo `dynamic` para a tabela)
    dynamic_title = data[0][0] if data else "Sem dados disponíveis"
    
    # Gerando o gráfico com os dados
    img_str = generate_plot(data)
    
    # HTML com layout melhorado
    html = '''
    <html>
        <head>
            <title>Gráfico de Pontuação</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css">
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f7f6; color: #333; text-align: center; padding: 50px; }
                h1 { color: #1e90ff; margin-bottom: 30px; }
                .container { max-width: 1000px; margin: auto; padding: 20px; background: #fff; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); border-radius: 10px; }
                .card { border: none; background-color: #f9f9f9; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
                img { border-radius: 8px; border: 2px solid #ddd; width: 100%; }
                
                /* Melhorando o layout da tabela */
                table { margin-top: 40px; }
                table th, table td {
                    text-align: center;
                    vertical-align: middle;
                    padding: 12px 15px;
                }
                table th {
                    background-color: #007bff;
                    color: white;
                    font-size: 16px;
                }
                table td {
                    background-color: #f8f9fa;
                    font-size: 14px;
                }
                table tbody tr:nth-child(even) {
                    background-color: #f1f1f1;
                }
                table tbody tr:hover {
                    background-color: #ddd;
                    cursor: pointer;
                }
                .table-wrapper {
                    overflow-x: auto;
                    max-width: 100%;
                    padding-top: 20px;
                }
                
                /* Adicionando estilo para o botão de recarregar a tabela e gráfico */
                .btn-refresh {
                    margin-top: 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                }
                .btn-refresh:hover {
                    background-color: #0056b3;
                }
            </style>
            <script>
                function refreshGraph() {
                    fetch("/get_graph_data")
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById("graph_img").src = "data:image/png;base64," + data.img_str;
                        });
                }
                
                function refreshTable() {
                    fetch("/get_table_data")
                        .then(response => response.json())
                        .then(data => {
                            const tableBody = document.getElementById("table_body");
                            tableBody.innerHTML = "";
                            data.forEach(row => {
                                const tr = document.createElement("tr");
                                const tdCode = document.createElement("td");
                                const tdScore = document.createElement("td");
                                tdCode.textContent = row.code;
                                tdScore.textContent = row.score;
                                tr.appendChild(tdCode);
                                tr.appendChild(tdScore);
                                tableBody.appendChild(tr);
                            });
                        });
                }
                
                setInterval(refreshGraph, 5000);  // Atualiza o gráfico a cada 5 segundos
                setInterval(refreshTable, 5000);  // Atualiza a tabela a cada 5 segundos
            </script>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="card-body">
                        <h1>Gráfico de Pontuação das Equipes</h1>
                        <img id="graph_img" src="data:image/png;base64,{{ img_str }}" />
                    </div>
                </div>
                
                <!-- Tabela de dados -->
                <div class="card mt-4">
                    <div class="card-body">
                        <h3>{{ dynamic_title }}</h3>
                        <div class="table-wrapper">
                            <table class="table table-striped table-bordered">
                                <thead>
                                    <tr>
                                        <th scope="col">Equipe</th>
                                        <th scope="col">Pontuação</th>
                                    </tr>
                                </thead>
                                <tbody id="table_body">
                                    <!-- Dados da tabela serão inseridos aqui dinamicamente -->
                                </tbody>
                            </table>
                        </div>
                        <button class="btn-refresh" onclick="refreshTable(); refreshGraph();">Atualizar Tabela e Gráfico</button>
                    </div>
                </div>
            </div>
        </body>
    </html>
    '''
    return render_template_string(html, img_str=img_str, dynamic_title=dynamic_title)

@app.route('/get_graph_data')
def get_graph_data():
    # Obtendo os dados mais recentes do banco de dados
    data = get_data_from_db()
    
    # Gerando o gráfico e retornando como JSON
    img_str = generate_plot(data)
    return jsonify({'img_str': img_str})

@app.route('/get_table_data')
def get_table_data():
    # Obtendo os dados mais recentes do banco de dados
    data = get_data_from_db()
    
    # Retornando os dados em formato JSON
    table_data = [{'code': row[1], 'score': row[2]} for row in data]
    return jsonify(table_data)

if __name__ == '__main__':
    app.run(debug=True)
