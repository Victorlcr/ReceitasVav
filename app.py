# bibliotecas em uso
from flask import Flask
from flask import render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship

# difiniçao da aplicaçao e banco de dados
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)


# TABELAS ----------------------------------------------------------------------------------------#
# tbIngredientes
class ingredientes(db.Model):
  idIngrediente = db.Column(db.Integer, primary_key=True, autoincrement=True)
  #quantidade = db.Column(db.String(30))
  nomeIngrediente = db.Column(db.String(30))
  idReceita = Column(db.Integer, ForeignKey('receitas.idReceita'), nullable=False)
  nomeReceita = relationship('receitas', backref='receitas.idReceita', foreign_keys=[idReceita])

  def __init__(self, nomeIngrediente, idReceita):
    self.nomeIngrediente = nomeIngrediente
    self.idReceita = idReceita

# tbReceitas
class receitas(db.Model):
  idReceita = db.Column(db.Integer, primary_key=True, autoincrement=True)
  nomeReceita = db.Column(db.String(30))
  preparo = db.Column(db.String(760))
  imagem = db.Column(db.String(120))
  tempo = db.Column(db.Integer)
  ingredientes = relationship("ingredientes", backref="receita")

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