from flask import render_template, request, session, redirect, url_for, flash
from app import app
from app.models.tables import *
from app.models.funcoes import *
from PIL import Image
import os
import secrets


@app.route("/")
@app.route("/index/<int:mesa>", methods=['GET', 'POST'])
def index(mesa):
    mesaselecionada = mesa
    lista_mesas = [Mesa.query.all()[i].mesa_id for i in range(len(Mesa.query.all()))]
    if mesaselecionada in lista_mesas:
        session['mesa'] = mesaselecionada
        return render_template('index.html', mesa=mesaselecionada)


@app.route("/adicionaraocarrinho")
def adicionaraocarrinho():
    if mesalogada():
        produto_id = int(request.args.get('produto_id'))

        extrairepessistircarrinho(produto_id)

        flash('Adicionado com sucesso!', 'sucesso')
        return redirect(url_for('cardapio'))
    else:
        return redirect(url_for('index.html'))


@app.route("/carrinho")
def carrinho():
    if mesalogada():
        logado, numero_mesa= detalhesdamesa()
        produtosnocarrinho, somatotal= detalhesdecarrinhopormesa()
        return render_template("carrinho2.html", dataCarrinho=produtosnocarrinho, logado=logado, numero_mesa=numero_mesa, somatotal=somatotal)


@app.route("/cardapio")
def cardapio(): 
    logado, numero_mesa = detalhesdamesa()
    detalhesdetodosprodutos = extrairtodosprodutos()
    armazenartodososdetalhes = massageItemData(detalhesdetodosprodutos)
    categoriaData = extraircategorias()

    return render_template('cardapio2.html', detalhesitens=armazenartodososdetalhes, logado=logado, numero_mesa=numero_mesa, categoriaData=categoriaData)


@app.route("/pratosespeciais")
def pratosespeciais():
    return render_template("pratos_especiais.html")


@app.route("/contato")
def contato():
    return render_template("contato.html")


@app.route("/admin", methods=['POST', 'GET'])
def admin():
        error = None
        if request.method == 'POST':
            nome_usuario = request.form['nome']
            administrador = [Administrador.query.all()[i].nome for i in range(len(Administrador.query.all()))]
            if nome_usuario in administrador:
                senha = Administrador.query.filter_by(nome=nome_usuario).all()[0].senha
                if request.form['senha'] != senha:
                    error = 'Invalid Credentials. Please try again.'
                else:
                    session['nome'] = nome_usuario  # storing session variable
                    return redirect(url_for('areaadmin'))
            error = 'Invalid Credentials. Please try again.'
        return render_template('login.html', error=error)

@app.route("/entrar")
def entrar():
    if 'nome' in session:
        return redirect(url_for('admin'))
    else:
        return render_template("login.html", error = '')

@app.route("/sair")
def sair():
    session.pop('nome', None)
    return redirect(url_for('entrar'))

@app.route("/admin/categoria/<int:categoria_id>", methods=['GET'])
def categoria(categoria_id):
    if adm_logado():
        categoria = Categoria.query.get_or_404(categoria_id)
        return render_template('categoria.html', categoria = categoria)
    return redirect(url_for('admin'))

@app.route("/admin/categoria/nova", methods = ['GET', 'POST'])
def adicionarcategoria():
    if adm_logado():
        form = addcategoria()
        if form.validate_on_submit():
            categoria = Categoria(nome_categoria = form.nome_categoria.data)
            db.session.add(categoria)
            db.session.commit()
            flash(f'Categoria {form.nome_categoria.data} adicionada com sucesso!','sucess')
            return redirect(url_for('todascategorias'))
        return render_template('adicionarcategoria.html', form = form)
    return redirect(url_for('admin'))

@app.route("/admin/categorias", methods=['GET'])
def todascategorias():
    if adm_logado():
        categorias = Categoria.query.all()
        #categorias.execute('SELECT categorias.categoria_id, categorias.nome_categoria, COUNT(categoriasprodutos.produto_id) as noOfProducts FROM categorias LEFT JOIN categoriasprodutos ON categoria.categoria_id = categoriasprodutos.categoria_id GROUP BY categorias.categoria_id');
        return render_template('todascategorias.html', categorias = categorias)
    return redirect(url_for('admin'))

@app.route("/admin/categoria/<int:categoria_id>/update", methods=['GET', 'POST'])
def atualizar_categoria(categoria_id):
    if adm_logado():
        categoria = Categoria.query.get_or_404(categoria_id)
        form = addcategoria()
        if form.validate_on_submit():
            categoria.nome_categoria= form.nome_categoria.data
            db.session.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('todascategorias'))
        elif request.method == 'GET':
            form.nome_categoria.data = categoria.nome_categoria
        return render_template('adicionarcategoria.html', legend="Atulizar Categoria", form=form)
    return redirect(url_for('todascategorias'))

@app.route("/admin/categoria/<int:categoria_id>/delete", methods=['POST'])
def excluir_categoria(categoria_id):
    if adm_logado():
        CategoriaProduto.query.filter_by(categoria_id=categoria_id).delete()
        db.session.commit()
        categoria= Categoria.query.get_or_404(categoria_id)
        db.session.delete(categoria)
        db.session.commit()
        flash('Essa categoria foi deletada', 'success')
    return redirect(url_for('todascategorias'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img', picture_fn)

    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/admin/produtos", methods=['GET'])
def todosprodutos():
    if adm_logado():
        produtos = Produto.query.all()
        return render_template('todosprodutos.html', produtos=produtos)
    return redirect(url_for('admin'))

@app.route("/admin/produto/novo", methods=['GET', 'POST'])
def adicionarproduto():
    if adm_logado():
        form = addProduto()
        form.categoria.choices = [(row.categoria_id, row.nome_categoria) for row in Categoria.query.all()]
        produto_icone = ""
        if form.validate_on_submit():
            if form.imagem.data:
                produto_icone = save_picture(form.imagem.data)
            produto = Produto(nome_produto=form.nome_produto.data, descricao=form.descricao.data, imagem=produto_icone, valor=form.valor.data)

            db.session.add(produto)
            db.session.commit()
            categoriaproduto = CategoriaProduto(categoria_id=form.categoria.data, produto_id=produto.produto_id)
            db.session.add(categoriaproduto)
            db.session.commit()
            flash(f'Produto {form.nome_produto} adicionado com sucesso', 'success')
            return redirect(url_for('todosprodutos'))
        return render_template("adicionarproduto.html", form=form, legend="Novo produto")
    return redirect(url_for('admin'))


@app.route("/admin/produto/<int:produto_id>", methods=['GET'])
def produto(produto_id):
    if adm_logado():
        produto = Produto.query.get_or_404(produto_id)
        return render_template('produto.html', produto=produto)
    return redirect(url_for('admin'))

@app.route("/admin/produto/<int:produto_id>/update", methods=['GET', 'POST'])
def atualizar_produto(produto_id):
    if adm_logado():
        produto = Produto.query.get_or_404(produto_id)
        form = addProduto()
        form.categoria.choices = [(row.categoria_id, row.nome_categoria) for row in Categoria.query.all()]
        if form.validate_on_submit():
            if form.imagem.data:
                produto.imagem = save_picture(form.imagem.data)
            produto.nome_produto= form.nome_produto.data
            produto.descricao = form.descricao.data
            produto.valor = form.valor.data
            db.session.commit()
            categoriaproduto = CategoriaProduto.query.filter_by(produto_id = produto.produto_id).first()
            if form.categoria.data != categoriaproduto.categoria_id:
                nova_categoria_produto = CategoriaProduto(categoria_id=form.categoria.data, produto_id = produto.produto_id)
                db.session.add(nova_categoria_produto)
                db.session.commit()
                db.session.delete(categoriaproduto)
                db.session.commit()

            flash('O produto foi atualizado com sucesso!', 'success')
            return redirect(url_for('todosprodutos'))
        elif request.method == 'GET':
            form.nome_produto.data = produto.nome_produto
            form.descricao.data = produto.descricao
            form.valor.data = produto.valor
        return render_template('adicionarproduto.html', legend="Atualizar produto", form=form)
    return redirect(url_for('admin'))


@app.route("/admin/produto/<int:produto_id>/delete", methods=['POST'])
def excluir_produto(produto_id):
    if adm_logado():
        categoriaproduto = CategoriaProduto.query.filter_by(produto_id=produto_id).first()
        if categoriaproduto is not None:
            db.session.delete(categoriaproduto)
            db.session.commit()
        Carrinho.query.filter_by(produto_id=produto_id).delete()
        db.session.commit()
        produto = Produto.query.get_or_404(produto_id)
        db.session.delete(produto)
        db.session.commit()
        flash('Esse produto foi deletado!', 'success')
    return redirect(url_for('todosprodutos'))


@app.route("/removerdocarrinho")
def removerdocarrinho():
    if mesalogada():
        produto_id = request.args.get('produto_id')
        removerproddocarrinho(produto_id)
        return redirect(url_for('carrinho'))
    else:
        return redirect(url_for('index'))


@app.route("/vercategoria")
def vercategoria():
    logado, numero_mesa = detalhesdamesa()
    categoria_id = request.args.get("categoria_id")

    detalhesdeprodutosporcategoria = Produto.query.join(CategoriaProduto, Produto.produto_id == CategoriaProduto.produto_id) \
        .add_columns(Produto.produto_id, Produto.nome_produto, Produto.imagem, Produto.valor) \
        .join(Categoria, Categoria.categoria_id == CategoriaProduto.categoria_id) \
        .filter(Categoria.categoria_id == int(categoria_id)) \
        .add_columns(Categoria.nome_categoria) \
        .all()

    nome_categoria = detalhesdeprodutosporcategoria[0].nome_categoria
    data = massageItemData(detalhesdeprodutosporcategoria)
    return render_template('vercategoria.html', data=data, logado=logado, numero_mesa=numero_mesa,
                           nome_categoria=nome_categoria)


@app.route("/descricaoproduto")
def descricaoproduto():
    logado, numero_mesa = detalhesdamesa()
    produto_id = request.args.get('produto_id')
    detalhesdoprodutoporid = extrairdetalhesdoproduto(produto_id)
    return render_template("descricaoproduto.html", data=detalhesdoprodutoporid, logado=logado,
                           numero_mesa=numero_mesa)

@app.route("/pagamento")
def pagamento():
    if mesalogada():
        produtosnocarrinho, somatotal= detalhesdecarrinhopormesa()
        return render_template("pagamento.html", dadoscarrinho=produtosnocarrinho, somatotal=somatotal)
    else:
        return redirect(url_for('index'))


@app.route("/criarpedido", methods=['GET', 'POST'])
def criarpedido():
    produtosnocarrinho, somatotal= detalhesdecarrinhopormesa()
    pedido_id = extrairdetalhesdopedido(request,somatotal)
    return render_template("sucesso.html")

@app.route("/areaadmin")
def areaadmin():
    if adm_logado():
        pedidos = Pedido.query.all()
        return render_template('admin.html', pedidos = pedidos)
    return redirect(url_for('admin'))

@app.route("/verpedido/<int:pedido_id>")
def verpedido(pedido_id):
    if adm_logado():
        pedido = Pedido.query.get_or_404(pedido_id)
        produtos = Produto.query.join(PedidoSolicitado, Produto.produto_id == PedidoSolicitado.produto_id) \
            .add_columns(Produto.nome_produto, PedidoSolicitado.quantidade) \
            .join(Pedido, Pedido.pedido_id == PedidoSolicitado.pedido_id) \
            .filter(Pedido.pedido_id == int(pedido_id))
        return render_template('verpedido.html', produtos = produtos)
    return redirect(url_for('admin'))

   