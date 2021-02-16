from flask import session, flash, redirect, url_for
from app.models.tables import *
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,SelectField,TextAreaField,FloatField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed


def ocuparMesa(mesa):
    mesaSelecionada= Mesa.query.filter_by(numero_mesa = mesa).first()
    mesaSelecionada.situacao = "ocupada"
    db.session.flush()
    db.session.commit()

def situacaoMesa(mesa):
    mesaSelecionada= Mesa.query.filter_by(numero_mesa = mesa).first()
    if mesaSelecionada.situacao == "ocupada":
        return False
    else:
        return True


def mesalogada():
    if 'mesa' not in session:
        return False
    else:
        return True


def extrairepessistircarrinho(produtoId):
    mesaId = Mesa.query.with_entities(Mesa.mesa_id).filter(Mesa.mesa_id == session['mesa']).first()
    mesaId = mesaId[0]

    subquery = Carrinho.query.filter(Carrinho.mesa_id == mesaId).filter(Carrinho.produto_id == produtoId).subquery()
    query = db.session.query(Carrinho.quantidade).select_entity_from(subquery).all()

    if len(query) == 0:
        carrinho = Carrinho(mesa_id=mesaId, produto_id=produtoId, quantidade=1)
    else:
        carrinho = Carrinho(mesa_id=mesaId, produto_id=produtoId, quantidade=query[0][0] + 1)

    db.session.merge(carrinho)
    db.session.flush()
    db.session.commit()


def detalhesdecarrinhopormesa():
    mesa_id = Mesa.query.with_entities(Mesa.mesa_id).filter(Mesa.mesa_id == session['mesa']).first()

    produtosnocarrinho = Produto.query.join(Carrinho, Produto.produto_id == Carrinho.produto_id) \
        .add_columns(Produto.produto_id, Produto.nome_produto, Produto.valor, Produto.imagem,
                     Carrinho.quantidade) \
        .add_columns(Produto.valor * Carrinho.quantidade).filter(Carrinho.mesa_id == mesa_id)
    
    somatotal = 0

    for row in produtosnocarrinho:
        somatotal += row[6]

    somatotal = int(somatotal)
    return (produtosnocarrinho, somatotal)


def adm_logado():
    if 'nome' not in session:
        return False
    else:
        return True


class addcategoria(FlaskForm):
    nome_categoria = StringField('Nome da Categoria: ', validators=[DataRequired()])
    submit = SubmitField('Salvar')


class addProduto(FlaskForm):
    categoria = SelectField('Categoria:', coerce=int, id='selecionar_categoria')
    nome_produto = StringField('Nome do Produto:', validators=[DataRequired()])
    descricao = TextAreaField('Descrição:', validators=[DataRequired()])
    valor = FloatField('Valor:', validators=[DataRequired()])
    imagem = FileField('Imagem', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Salvar')


def removerproddocarrinho(produto_id):
    mesa_id = Mesa.query.with_entities(Mesa.mesa_id).filter(Mesa.mesa_id == session['mesa']).first()
    mesa_id = mesa_id[0]
    kwargs = {'mesa_id': mesa_id, 'produto_id': produto_id}
    carrinho = Carrinho.query.filter_by(**kwargs).first()
    if produto_id is not None:
        db.session.delete(carrinho)
        db.session.commit()
        flash("Produto removido do carrinho !!")
    else:
        flash("Erro ao remover produto do carrinho, tente novamente !!")
    return redirect(url_for('carrinho'))


def extrairtodosprodutos():
    itemData = Produto.query.join(CategoriaProduto, Produto.produto_id == CategoriaProduto.produto_id) \
        .add_columns(Produto.produto_id, Produto.nome_produto, Produto.imagem, Produto.descricao,
                     Produto.valor) \
        .join(Categoria, Categoria.categoria_id == CategoriaProduto.categoria_id) \
        .order_by(Categoria.categoria_id.desc()) \
        .all()
    return itemData


def extraircategorias():
    itemData = Categoria.query.join(CategoriaProduto, Categoria.categoria_id == CategoriaProduto.categoria_id) \
        .join(Produto, Produto.produto_id == CategoriaProduto.produto_id) \
        .order_by(Categoria.categoria_id.desc()) \
        .distinct(Categoria.categoria_id) \
        .all()
    return itemData


def massageItemData(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(6):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


def detalhesdamesa():
    produtototalnamesa = 0

    if 'mesa' not in session:
        logado = False
        numero_mesa = ''
    else:
        logado = True
        mesa_id, numero_mesa = Mesa.query.with_entities(Mesa.mesa_id, Mesa.numero_mesa).filter(
            Mesa.mesa_id == session['mesa']).first()

        produtosnocarrinho = []

        # for Cart in Cart.query.filter(Cart.userId == userId).distinct(Products.productId):
        for carrinho in Carrinho.query.filter(Carrinho.mesa_id == mesa_id).all():
            produtosnocarrinho.append(carrinho.produto_id)
            produtototalnamesa = len(produtosnocarrinho)

    return (logado, numero_mesa) #produtototalnamesa)


def extrairdetalhesdoproduto(produto_id):
    detalhesdoprodutoporid = Produto.query.filter(Produto.produto_id == produto_id).first()
    return detalhesdoprodutoporid
    

def extrairdetalhesdopedido(request, valor_total):
    mesa_id = Mesa.query.with_entities(Mesa.mesa_id).filter(Mesa.mesa_id == session['mesa']).first()
    mesa_id = mesa_id[0]
    pedido = Pedido(valor_total=valor_total, mesa_id=mesa_id, status="Recebido")
    db.session.add(pedido)
    db.session.flush()
    db.session.commit()

    pedido_id = Pedido.query.with_entities(Pedido.pedido_id).filter(Pedido.mesa_id == mesa_id).order_by(Pedido.pedido_id.desc()).first()

    # add details to ordered;
    #  products table
    adicionarprodutospedidos(mesa_id, pedido_id)
    # add transaction details to the table
    atualizarpagamento(valor_total, pedido_id)

    # remove ordered products from cart after transaction is successful
    removerprodutodopedido(mesa_id)
    # sendtextconfirmation(phone,fullname,orderid)
    return (pedido_id)


# adds data to orderdproduct table

def adicionarprodutospedidos(mesa_id, pedido_id):
    carrinho = Carrinho.query.with_entities(Carrinho.produto_id, Carrinho.quantidade).filter(Carrinho.mesa_id == mesa_id)

    for item in carrinho:
        pedidosolicitado = PedidoSolicitado(pedido_id=pedido_id, produto_id=item.produto_id, quantidade=item.quantidade)
        db.session.add(pedidosolicitado)
        db.session.flush()
        db.session.commit()


def removerprodutodopedido(mesa_id):
    mesa_id = mesa_id
    db.session.query(Carrinho).filter(Carrinho.mesa_id == mesa_id).delete()
    db.session.commit()


def atualizarpagamento(valor_total, pedido_id):
    pagamento = Pagamento(pedido_id=pedido_id, montante=valor_total)
    db.session.add(pagamento)
    db.session.flush()
    db.session.commit()

def desocuparMesa(mesa):
    mesaSelecionada= Mesa.query.filter_by(numero_mesa = mesa).first()
    mesaSelecionada.situacao = "livre"
    db.session.flush()
    db.session.commit()

def finalizarMesa(mesa):
    mesaSelecionada= Mesa.query.filter_by(numero_mesa = mesa).first()
    mesaSelecionada.situacao = "livre"
    db.session.flush()
    db.session.commit()


