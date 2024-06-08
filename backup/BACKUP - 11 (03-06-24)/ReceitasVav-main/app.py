# bibliotecas em uso
from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, func, distinct
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timedelta

# difiniçao da aplicaçao e banco de dados
app = Flask(__name__)
app.secret_key = 'receitasregionais'
app.permanent_session_lifetime = timedelta(days=365*100)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///receitas.sqlite3'
db = SQLAlchemy(app)

# listas

lista_ingredientes = []
lista_ingredientes_invalidos = []
lista_ingredientes_manter = []
lista_mostrar_receitas = []
lista_ingredientes_consulta = []
lista_char_proibidos = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
                   '_', '-', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', 
                   '.', '?', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                   '<', '>', '&', '"', "'", '/', '\\', ';', '#', '--', '/', '/', '<!--', '-->', '<?', '?>', '<%', '%>', ]
lista_palavras_proibidas = ['<script', '</script>',
                   'alert(', 'confirm(', 'prompt(', 'document.cookie', 'onerror', 'onload', 'onmouseover', 'onmousemove', 'onmousedown', 'onmouseup', 'onclick',
                   'javascript:', 'data:', 'xmlns:', 'xlink:', 'iframe', 'object', 'embed', 'applet', 'meta', 'link', 'base', 'body', 'head', 'html', 'svg',
                   'window.location', 'location.href', 'window.open', 'eval(', 'exec(', 'setTimeout(', 'setInterval(',
                   'expression(', 'style=', 'url(', 'behavior:', 'vbscript:', 'mocha:', 'livescript:', 'jaVascript:', 'mozBinding:', 'mozSystem:', 'mozSettings:',
                   'mozIDOMWindow', 'mozIDOMWindowProxy', 'Function(', 'Proxy(', 'ActiveXObject', 'VBScript:', 'fromCharCode(', 'String.fromCharCode(',
                   'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE',
                   'UNION', 'JOIN', 'WHERE', 'FROM', 'INTO', 'VALUES', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIKE', 'AND', 'OR', 'NOT', 'BETWEEN', 'IN',
                   'EXECUTE', 'EXEC', 'EXECUTE IMMEDIATE', 'PREPARE', 'EXECUTE', 'EXECUTE AS', 'OPENQUERY', 'OPENROWSET',
                   'sp_', 'xp_', 'sys.', 'sysobjects', 'syscolumns', 'xp_cmdshell', 'DECLARE', 'WHILE', 'CURSOR', 'FETCH', 'NEXT', 'FOR XML', 'FOR JSON']

char_proibidos_encontrados = []
ing_proibidos_encontrados = []
lista_proibidos_formatada = []

# TABELAS ----------------------------------------------------------------------------------------#
# tbIngredientes
class ingredientes(db.Model):
    __tablename__ = 'ingredientes'
    idIngrediente = db.Column(Integer, primary_key=True, autoincrement=True)
    nomeIngrediente = db.Column(String(30)) 
    idReceita = db.Column(Integer, ForeignKey('receitas.idReceita'), nullable=False)
    receita = relationship('receitas', back_populates='ingredientes')
    
    def __init__(self, nomeIngrediente, idReceita):
        self.nomeIngrediente = nomeIngrediente
        self.idReceita = idReceita


# tbReceitas
class receitas(db.Model):
  __tablename__ = 'receitas'
  idReceita = db.Column(Integer, primary_key=True, autoincrement=True)
  nomeReceita = db.Column(String(30))
  preparo = db.Column(String(760))
  imagem = db.Column(db.String(120))
  tempo = db.Column(db.String(50))
  ingredientes = relationship('ingredientes', back_populates='receita')
  
  def __init__(self, nomeReceita, preparo, imagem, tempo):
      self.nomeReceita = nomeReceita
      self.preparo = preparo
      self.imagem = imagem
      self.tempo = tempo
#--------------------------------------------------------------------------------------------------#



# CONSULTAS ---------------------------------------------------------------------------------------#
# busca todas receitas existentes
def getTodasReceitas():
  todasReceitas = receitas.query.all()

  return todasReceitas


# busca todos ingredientes existentes
def getTodosIngredientes():
  todosIngredientes = ingredientes.query.all()

  return todosIngredientes


# busca todas receitas e seus respectivos ingredientes
def getTodasReceitasComIngredientes():
    consulta = db.session.query(receitas.idReceita, receitas.nomeReceita, receitas.preparo, receitas.imagem,
      func.group_concat(ingredientes.nomeIngrediente)).\
    join(ingredientes).group_by(receitas.idReceita).all()

    return consulta


# busca uma receita utilizando seu id como parametro
def getReceitaComIngredientesPorId(idReceita):
    consulta = db.session.query(receitas, ingredientes.nomeIngrediente).\
        join(ingredientes).\
        filter(receitas.idReceita == idReceita).\
        all()
    
    # agrupa os ingredientes para a receita
    receitas_com_ingredientes = {}
    for receita, ingrediente in consulta:
        if receita.idReceita not in receitas_com_ingredientes:
            receitas_com_ingredientes[receita.idReceita] = {
                'receita': receita,
                'ingredientes': []
            }
        receitas_com_ingredientes[receita.idReceita]['ingredientes'].append(ingrediente)

    return list(receitas_com_ingredientes.values())
#---------------------------------------------------------------------------------------------------#



# ROTAS --------------------------------------------------------------------------------------------#
# index
@app.route('/')
def index():
  return render_template('index.html')


# receitabase
@app.route('/receita/<int:idReceita>', methods=['GET', 'POST'])
def receita(idReceita):
  receitasComIngredientes = getReceitaComIngredientesPorId(idReceita)
  return render_template('receita.html', receitasComIngredientes = receitasComIngredientes)


# pag. de exibiçao das receitas e ingredientes
@app.route('/lista')
def lista():
  receitasComIngredientes = getTodasReceitasComIngredientes()

  return render_template('lista.html', receitas = receitasComIngredientes)

@app.route('/estoque_usuario', methods=['GET', 'POST'])
def cadastroIngrediente():

    global lista_ingredientes
    global lista_proibidos_formatada
    global char_proibidos_encontrados 
    global ing_proibidos_encontrados
    
    char_invalido = False
    ing_invalido = False
    repetido = False
    vazio = False
  
    if request.method == 'POST': # VERIFICA SE O MÉTODO DO FORMULÁRIO É POST
        ingrediente = request.form['ingrediente'] # PEGA O VALOR DO INPUT E ARMAZENA NA VARIÁVEL INGREDIENTE
        char_proibidos_encontrados.clear()
        ing_proibidos_encontrados.clear()
        
        char_invalido = any(char in lista_char_proibidos for char in ingrediente)
        ing_invalido = any(ingProibido.lower() in ingrediente.lower() for ingProibido in lista_palavras_proibidas)
        repetido = any(ingrediente.replace(" ", "").lower() == ingrediente_na_lista.replace(" ", "").lower()
                        for ingrediente_na_lista in lista_ingredientes)
        vazio = ingrediente.strip() == ""

        char_proibidos_encontrados = [char for char in ingrediente if char in lista_char_proibidos]
        ing_proibidos_encontrados = [ingProibido for ingProibido in lista_palavras_proibidas if ingProibido.lower() in ingrediente.lower()]

        if char_invalido:
            lista_proibidos_formatada = ', '.join(set(char_proibidos_encontrados))
            flash(f"O ingrediente não pode conter: {lista_proibidos_formatada} \U0001F914")
        elif ing_invalido:
            lista_proibidos_formatada = ', '.join(set(ing_proibidos_encontrados))
            flash(f"O ingrediente não pode conter: {lista_proibidos_formatada} \U0001F914")
        elif repetido:
            flash(f"{ingrediente.capitalize()} já foi inserido anteriormente \U0001F914")
        elif vazio:
            flash("Parece que você não digitou o nome do ingrediente \U0001F914")
        else:
            flash(f"{ingrediente.strip().capitalize()} adicionado com sucesso \U0001F60E\U0001F44C")  
            lista_ingredientes.append(ingrediente.lower())# ADICIONA O INGREDIENTE NA LISTA, CASO A VARIAVEL EXISTA

        print(ingrediente)

        return redirect(url_for('cadastroIngrediente'))
    
    ingredientes_no_banco = db.session.query(ingredientes.nomeIngrediente).distinct().all()
    
    return render_template('estoqueUsuario.html', lista_ingredientes=lista_ingredientes, ingredientes_no_banco=ingredientes_no_banco)

@app.route('/remover_ingrediente', methods=['POST','GET'])
def remover_ingrediente():

    global lista_ingredientes
    global lista_ingredientes_manter

    lista_checkbox = request.form.getlist('ingredientes-remover')
    lista_ingredientes = [ingrediente for ingrediente in lista_ingredientes if ingrediente not in lista_checkbox]
    #flash ("Ingrediente(s) removido(s) com sucesso \U0001F60E\U0001F44D) 
    return redirect(url_for('cadastroIngrediente', lista_ingredientes=lista_ingredientes))                                                                                             

@app.route('/receitas_mostrar', methods=['POST', 'GET'])
def get_receitas_com_ingredientes():
    global lista_ingredientes
    global lista_ingredientes_invalidos

    ingredientes_formatados = ', '.join([ingrediente.capitalize() for ingrediente in lista_ingredientes])

    # Consulta SQL para encontrar receitas que possuem pelo menos um ingrediente da lista fornecida
    receitas_com_ingredientes = db.session.query(receitas).\
        join(ingredientes).\
        filter(ingredientes.nomeIngrediente.in_(lista_ingredientes)).\
        group_by(receitas.idReceita).\
        having(func.count(receitas.idReceita) == len(lista_ingredientes)).\
        all()
    
    # Lista dos ingredientes presentes nas receitas encontradas no banco de dados
    ingredientes_nas_receitas = set()
    for receita in receitas_com_ingredientes:
        for ingrediente in receita.ingredientes:
            ingredientes_nas_receitas.add(ingrediente.nomeIngrediente)

    # Lista dos ingredientes presentes na lista Python, mas não no banco de dados
    lista_ingredientes_invalidos = [ingrediente for ingrediente in lista_ingredientes if ingrediente not in ingredientes_nas_receitas]

    if lista_ingredientes_invalidos:
        invalidos_formatados = ', '.join([ingrediente.capitalize() for ingrediente in lista_ingredientes_invalidos])
        msg = f'Receitas não encontradas com {invalidos_formatados}'
    else:
        msg = f'Receitas com {ingredientes_formatados}'

    return render_template('receitasEncontradas.html', receitas=receitas_com_ingredientes, msg=msg)



# form. de adiçao de novas receitas
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
  nomeReceita = request.form.get('nomeReceita')
  preparo = request.form.get('preparo')
  imagem = request.form.get('imagem')
  tempo = request.form.get('tempo')
  listaIngredientes = request.form.getlist('ingredientes[]')

  if request.method == 'POST':
    receita = receitas(nomeReceita, preparo, imagem, tempo)

    db.session.add(receita)
    db.session.commit()

    for ingrediente in listaIngredientes:
      db.session.add(ingredientes(ingrediente, receita.idReceita))
      db.session.commit()

    return redirect(url_for('lista'))
  
  return render_template('adicionar.html')


# form. ediçao de receitas e ingredientes, atualiza dados no db
@app.route('/editar/<int:idReceita>', methods=['GET', 'POST'])
def editar(idReceita):
  receita = receitas.query.get(idReceita)
  ingrediente = getReceitaComIngredientesPorId(idReceita)[0]

  if request.method == 'POST':
    receita.nomeReceita = request.form.get('nomeReceita')
    receita.preparo = request.form.get('preparo')
    for ingrediente in receita.ingredientes:
          ingrediente.nomeIngrediente = request.form.get('nomeIngrediente')
    db.session.commit()

    return redirect(url_for('lista'))
  
  return render_template('editar.html', receita = receita, ingrediente = ingrediente)


# requisiçao para exclusao de item 
@app.route('/deletar/<int:idReceita>')
def deletar(idReceita):
  receita = receitas.query.get(idReceita)
  
  for ingrediente in receita.ingredientes:
    db.session.delete(ingrediente)

  db.session.delete(receita)
  db.session.commit()

  return redirect(url_for('lista'))
#--------------------------------------------------------------------------------------------------#


# criacao do banco de dados e ativacao do modo debug
if __name__ == "__main__":
  with app.app_context():
    db.create_all()
  app.run(debug=True)