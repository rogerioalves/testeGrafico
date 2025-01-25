import sqlite3
from flask import Flask, render_template_string, jsonify, request, redirect
import numpy as np
from io import BytesIO
import base64
import os

app = Flask(__name__)

DATABASE_FILE = os.getenv('DATABASE_FILE')  
HOST = os.getenv('HOST')  
PORT = os.getenv('PORT')  

# DATABASE_FILE = "pontuacoes.db"
# HOST = '127.0.0.1'
# PORT = 5000

# Cores fixas para as equipes
FIXED_COLORS = [
    'rgba(54, 162, 235, 1)',  # Azul
    'rgba(255, 159, 64, 1)',   # Amarelo
    'rgba(255, 71, 87, 1)', 
    'rgba(75, 192, 192, 1)',   # Verde
    'rgba(153, 102, 255, 1)'   # Roxo
]

# Dicionário global para armazenar as cores das equipes
team_color_dict = {}

# Função para recuperar os dados do gráfico
def get_data_for_chart():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT dynamic, code, score FROM Report ORDER BY code")
    rows = cursor.fetchall()
    conn.close()

    # Se não houver dados, retorna um gráfico vazio
    if not rows:
        return {
            'labels': [],
            'datasets': []
        }

    # Criando um dicionário para armazenar os dados das equipes
    scores = {}
    for row in rows:
        dynamic, code, score = row
        if code not in scores:
            scores[code] = []
        scores[code].append(score)

    # Garantir que todas as equipes tenham o mesmo número de registros
    max_len = max(len(score_list) for score_list in scores.values())
    for equipe, score_list in scores.items():
        while len(score_list) < max_len:
            score_list.append(score_list[-1])  # Repete a última pontuação

    # Criando a estrutura de dados para o gráfico
    chart_data = {
        'labels': list(range(1, max_len + 1)),
        'datasets': []
    }

    # Preenche os datasets com os dados das equipes
    for equipe, score_list in scores.items():
        cor = get_team_color(equipe)
        chart_data['datasets'].append({
            'label': equipe,
            'data': score_list,
            'borderColor': cor,
            'backgroundColor': cor,
            'fill': False,
            'tension': 0.1,
            'borderWidth': 3,
            'pointBackgroundColor': cor,
            'pointBorderColor': '#fff',
            'pointBorderWidth': 3,
            'pointRadius': 6,
        })

    return chart_data

# Função para recuperar os dados da tabela
def get_data_for_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code AS equipe, MAX(score) AS pontuacao
        FROM Report
        GROUP BY code
        ORDER BY pontuacao DESC;
    """)
    rows = cursor.fetchall()
    conn.close()

    # Se não houver dados, retorna uma lista vazia
    if not rows:
        return []

    return rows

# Função para criar ou recuperar a cor da equipe
def get_team_color(equipe):
    if equipe not in team_color_dict:
        # Se a equipe não tem cor, atribui uma nova cor da lista
        color = FIXED_COLORS[len(team_color_dict) % len(FIXED_COLORS)]
        team_color_dict[equipe] = color
    return team_color_dict[equipe]

@app.route('/')
def index():
    chart_data = get_data_for_chart()
    dynamic_title = chart_data['labels'][0] if chart_data['labels'] else "Sem dados disponíveis"
    table_data = get_data_for_table()
    table = [{'code': row[0], 'score': row[1]} for row in table_data]

    return render_template_string(html, dynamic_title=dynamic_title, chart_data=chart_data, cores=team_color_dict, table_data=table)

@app.route('/get_table_data')
def get_table_data():
    table_data = get_data_for_table()
    table = [{'code': row[0], 'score': row[1]} for row in table_data]
    return jsonify(table)

@app.route('/get_chart_data')
def get_chart_data():
    chart_data = get_data_for_chart()
    return jsonify(chart_data)

# Função para adicionar uma nova pontuação e equipe no banco de dados
@app.route('/add_score', methods=['POST'])
def add_score():
    new_team_code = request.form['code']
    new_score = int(request.form['score'])

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pontuacoes (code, score) VALUES (?, ?)", (new_team_code, new_score))
    conn.commit()
    conn.close()

    # Atualizar a cor da nova equipe, se necessário
    get_team_color(new_team_code)

    # Retorna os dados atualizados da tabela e gráfico
    return jsonify({
        'table_data': get_data_for_table(),
        'chart_data': get_data_for_chart()
    })

html = '''
<html>
    <head>
        <title>Gráfico de Pontuação</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f7f6;
                color: #333;
                text-align: center;
                padding: 50px;
            }
            h1 {
                color: #1e90ff;
                margin-bottom: 30px;
                word-wrap: break-word;
                white-space: normal;
                text-overflow: ellipsis;
                overflow: hidden;
                max-width: 100%;
                font-size: 2rem;
            }
            .container {
                max-width: 1000px;
                margin: auto;
                padding: 20px;
                background: #fff;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
            .card {
                border: none;
                background-color: #f9f9f9;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            .table-wrapper {
                overflow-x: auto;
                max-width: 100%;
                padding-top: 20px;
            }
            table {
                margin-top: 40px;
            }
            table th, table td {
                text-align: center;
                vertical-align: middle;
                padding: 12px 15px;
                border: 2px solid white;  
            }
            table th {
                background-color: #6c757d !important;
                color: white !important;
                font-size: 16px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            table td {
                font-size: 14px;
                color: white;
            }
            table tbody tr:hover {
                background-color: #a0a0a0;
                cursor: pointer;
            }
            table tbody tr:first-child {
                font-weight: bold;
            }
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
            #scoreChart {
                width: 100% !important;
                height: auto !important;
            }
        </style>
        <script>
            let lastChartData = null;

            // Função para atualizar a tabela
            function refreshTable() {
                fetch("/get_table_data")
                    .then(response => response.json())
                    .then(data => {
                        const tableBody = document.getElementById("table_body");
                        tableBody.innerHTML = ""; // Limpa a tabela antes de preenchê-la

                        // Garantir que as cores das equipes estejam disponíveis
                        const teamColors = {{ cores | tojson }};  // Cores no formato JSON para uso no JS

                        data.forEach(row => {
                            const tr = document.createElement("tr");
                            const tdCode = document.createElement("td");
                            const tdScore = document.createElement("td");
                            tdCode.textContent = row.code;
                            tdScore.textContent = row.score;

                            // Atribuindo a cor da equipe a partir do dicionário `teamColors`
                            const corEquipe = teamColors[row.code] || '#fff';  // Default white if no color is found

                            // Aplicando a cor de fundo da equipe
                            tr.style.backgroundColor = corEquipe;

                            // Adicionando as células à linha
                            tr.appendChild(tdCode);
                            tr.appendChild(tdScore);

                            // Adicionando a linha à tabela
                            tableBody.appendChild(tr);
                        });
                    })
                    .catch(error => console.error('Erro ao atualizar a tabela:', error));
            }

            // Função para atualizar o gráfico
            function refreshChart() {
                fetch("/get_chart_data")
                    .then(response => response.json())
                    .then(data => {
                        if (JSON.stringify(data) !== JSON.stringify(lastChartData)) {
                            lastChartData = data;
                            const chartData = {
                                labels: data.labels,
                                datasets: data.datasets
                            };
                            const ctx = document.getElementById('scoreChart').getContext('2d');
                            window.myChart.data = chartData;
                            window.myChart.update();
                        }
                    });
            }

            // Função para adicionar uma nova pontuação e atualizar automaticamente
            function addScore(event) {
                event.preventDefault();
                const form = event.target;
                const formData = new FormData(form);
                fetch("/add_score", {
                    method: "POST",
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Atualiza a tabela e o gráfico com os novos dados
                    refreshTable();
                    refreshChart();
                })
                .catch(error => console.error('Erro ao adicionar pontuação:', error));
            }

            // Inicialização da página
            window.onload = function() {
                const ctx = document.getElementById('scoreChart').getContext('2d');
                window.myChart = new Chart(ctx, {
                    type: 'line',
                    data: {{ chart_data | tojson }},
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                            },
                            title: {
                                display: false,  
                            },
                        },
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Rodadas',
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Pontuação',
                                },
                                beginAtZero: true
                            }
                        }
                    }
                });

                refreshTable();
                setInterval(refreshTable, 5000);
                setInterval(refreshChart, 5000);
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>PONTUAÇÃO</h1>     
            <div class="card">
                <canvas id="scoreChart"></canvas>
            </div>

            <div class="table-wrapper">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Equipe</th>
                            <th>Pontuação</th>
                        </tr>
                    </thead>
                    <tbody id="table_body"></tbody>
                </table>
            </div>

            <button class="btn-refresh" onclick="refreshTable(); refreshChart();">Atualizar</button>

        </div>
    </body>
</html>
'''

if __name__ == "__main__":
    app.run(debug=True)
