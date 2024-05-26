# bibliotecas em uso
from flask import Flask
from flask import render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# difiniçao da aplicaçao e banco de dados
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///project.sqlite3'
db = SQLAlchemy(app)


# TABELAS ----------------------------------------------------------------------------------------#
# tbIngredientes
class ingredientes(db.Model):
  idIngrediente = db.Column(db.Integer, primary_key=True, autoincrement=True)
  nomeIngrediente = db.Column(db.String(30))
  def __init__(self, nomeIngrediente):
    self.nomeIngrediente = nomeIngrediente

# tbReceitas
class receitas(db.Model):
  idReceita = db.Column(db.Integer, primary_key=True, autoincrement=True)
  nomeReceita = db.Column(db.String(30))
  preparo = db.Column(db.String(760))
  def __init__(self, nomeReceita, preparo):
    self.nomeReceita = nomeReceita
    self.preparo = preparo
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
#---------------------------------------------------------------------------------------------------#



# ROTAS --------------------------------------------------------------------------------------------#
# index
@app.route('/')
def index():

  return render_template('index.html')

# pag. de exibiçao das receitas e ingredientes
@app.route('/lista')
def lista():
  todasReceitas = getTodasReceitas()
  todosIngredientes = getTodosIngredientes()

  return render_template('lista.html', receitas = todasReceitas, ingredientes = todosIngredientes)

# form. de adiçao de novas receitas
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
  nomeReceita = request.form.get('nomeReceita')
  preparo = request.form.get('preparo')
  nomeIngrediente = request.form.get('nomeIngrediente')

  if request.method == 'POST':
    receita = receitas(nomeReceita, preparo)
    ingrediente = ingredientes(nomeIngrediente)

    db.session.add(receita)
    db.session.add(ingrediente)
    db.session.commit()

    return redirect(url_for('lista'))
  
  return render_template('adicionar.html')

# form. ediçao de receitas e ingredientes, atualiza dados no db
@app.route('/editar/<int:idReceita>', methods=['GET', 'POST'])
def editar(idReceita):
  receita = receitas.query.get(idReceita)

  if request.method == 'POST':
    receita.nomeReceita = request.form.get('nomeReceita')
    receita.preparo = request.form.get('preparo')
    db.session.commit()

    return redirect(url_for('lista'))
  
  return render_template('editar.html', receita = receita)

# requisiçao para exclusao de item 
@app.route('/deletar/<int:idReceita>')
def deletar(idReceita):
  receita = receitas.query.get(idReceita)

  db.session.delete(receita)
  db.session.commit()

  return redirect(url_for('lista'))
#--------------------------------------------------------------------------------------------------#


# criacao do banco de dados e ativacao do modo debug
if __name__ == "__main__":
  with app.app_context():
    db.create_all()
  app.run(debug=True)