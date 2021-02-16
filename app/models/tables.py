from app import db
from datetime import datetime

class Administrador(db.Model):
    __tablename__ = "administador"

    administrador_id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    senha = db.Column(db.String(50))


class Mesa(db.Model):
    __tablename__ = "mesas"

    mesa_id = db.Column(db.Integer, primary_key=True)
    numero_mesa = db.Column(db.Integer, unique=True)
    situacao = db.Column(db.String)


class Produto(db.Model):
    __tablename__ = "produtos"

    produto_id = db.Column(db.Integer, primary_key=True)
    nome_produto = db.Column(db.String)
    valor = db.Column(db.DECIMAL)
    imagem = db.Column(db.String(100))
    descricao = db.Column(db.String(100))
    


class Categoria(db.Model):
    __tablename__ = "categorias"

    categoria_id = db.Column(db.Integer, primary_key=True)
    nome_categoria = db.Column(db.String(100))
    data_postagem = db.Column(db.DateTime, default=datetime.utcnow)


class CategoriaProduto(db.Model):
    __tablename__ = "categoriasprodutos"

    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.categoria_id'), primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.produto_id'), primary_key=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)


class Carrinho(db.Model):
    __tablename__ = "carrinho"

    id =  db.Column(db.Integer)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.mesa_id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.produto_id'), primary_key = True)
    quantidade = db.Column(db.Integer)

    produto = db.relationship('Produto')


class Pedido(db.Model):
    __tablename__ = "pedidos"

    pedido_id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.mesa_id'))
    valor_total = db.Column(db.DECIMAL)
    status = db.Column(db.String)


class PedidoSolicitado(db.Model):
    __tablename__ = "pedidossolicitados"

    pedidosolicitado_id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.pedido_id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.produto_id'))
    quantidade = db.Column(db.Integer)


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    pagamento_id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.pedido_id'))
    nome_pagamento = db.Column(db.String(50))
    montante = db.Column(db.DECIMAL)
    resposta = db.Column(db.String(50))



