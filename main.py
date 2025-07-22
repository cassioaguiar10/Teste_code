# arquivo main.py
# por boa pratica para evitar problemas o import das modelos deve ser feito no inicio.
import config
import pandas as pd
import sqlite3
import os 
from flask import Flask, request, request, jsonify, render_template_string

app = Flask(__name__)

DB_PATH = config.DB_PATH

# funçao para inicializar o banco de dados

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inadinmplencia(
                mes TEXT PRIMARY KEY,
                inadimplencia REAL             
                )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selic (
                mes TEXT PRIMARY KEY,
                selic_diaria REAL         
                )
        ''')               

        conn.commit()
# em breve =)
vazio = 0
        
@app.route('/')
def index():
    return render_template_string('''
            <h1>Upload de dadods Economicos</h1>
            <form action='/upload' method='POST' enctype='multipart/form-data'>
                <label for='campo_inadimplencia'>Arquivo de Inadimplencia</label>
                                  
            <input name='campo_inadimplencia' type='file' required><br><br>     

           <label for='campo_selic'>Arquivo Taxa Selic</label>
           <input type='file' required name='campo selic' required><br><br>                      
             <input type='submit' value='Fazer Upload'>
            </form> 
            <br><br><hr>
            <a href='/consultar'> Consultar Dados <br>      
            <a href='/graficos'> Visualizar Graficos <br>                      
            <a href='/editar_inadimplencia'> Editar dados de Inadimplencia <br>                      
            <a href='/correlacao'> Analisar a Correlação <br>                             
''') 

@app.route('/upload', methods=['POST','GET'])
def upload():
    inad_file = request.files.get('campo_inadimplencia')
    selic_file = request.files.get('campo_selic')

    #verificar se os aquivos de fato foram enviados
    if not inad_file or not selic_file:
        return jsonify({'Erro': 'Amabos os arquivos devem ser enviados '})
    
    inad_df = pd.read_csv(
        inad_file, 
        sep = ';',
        names=['data', 'inadimplencia'],
        header = 0 
    )

    selic_df = pd.read_csv(
        selic_file, 
        sep = ';',
        names=['data', 'selic_diaria'],
        header = 0 
    )    

# formata o campo de dada como daha hora padrao
    inad_df['data'] = pd.to_datetime(inad_df['data'],format="%d/%m/%Y")
    selic_df['data'] = pd.to_datetime(inad_df['data'],format="%d/%m/%Y")

#gera uma coluna nova mes e preenche de acordo com a data
    inad_df['mes'] = inad_df['data'].dt.to_period('M').astype(str)
    selic_df['mes'] = selic_df['data'].dt.to_period('M').astype(str)

    #limpa as duplicatas de agrupa conjutos
    inad_mensal = inad_df[['mes','inadimplencia']].drop_duplicates()
    selic_mensal = selic_df.groupby('mes')['selic_diaria'].mean().reset_index()

    #agora com tudo limpo e ordenando vamos armazenar no baco de dados
    with sqlite3.connect(DB_PATH) as conn:
        inad_mensal.to_sql('inadimplencia', conn, if_exists='replace', index=False) 
        selic_mensal.to_sql('selic', conn, if_exists='replace', index=False)
    return jsonify({'Mensagem': 'Dados inseridos com sucesso!'})

@app.route('/consultar', methods=['POST', 'GET'])
def consultar():
    #resultados se a pagina for carregada recebendo post
    if request.method == 'POST':
        tabela = request.form.get('Campo_tablea')
        if tabela not in ['inadimplencia','selic']:
            return jsonify({'Error': 'Tabela é invalida'})
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(f'SELEC * FROM {tabela}', conn)
        return df.to_html(index=False)    
    
    #Resultado sem receber um post, ou seja, primeiro carregamente da pagina de consulta
    return render_template_string(''' 
        <h1> Consultar tabela </h1>
        <form action='/consultar' method='POST'>
        <label for='campo_tabela'> Escolha a tabela:  
        </label>
         <select name='campo_tabela'>
         <option value='inadimplencia'> Inadimplencia </option>
         <option value='selic'> Selic </option>
         </select>
                                  
        <input type='submit' value='Consultar'>
                                                          
        </form>
        <br>
        <a href='/'>Voltar</a>

    ''')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)