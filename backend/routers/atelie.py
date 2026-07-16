from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from backend.app import db
from backend.models.atelie import AteliePedido, AtelieMaterial, AtelieHistorico
from backend.models.cliente import Cliente

bp = Blueprint('atelie', __name__, url_prefix='/atelie')

@bp.route('/')
@login_required
def index():
    status_filtro = request.args.get('status', '')
    pedidos = AteliePedido.query.order_by(AteliePedido.data_entrega.asc().nullslast(), AteliePedido.id.desc()).all()
    if status_filtro:
        pedidos = [p for p in pedidos if p.status == status_filtro]
    total = AteliePedido.query.count()
    em_producao = AteliePedido.query.filter(
        AteliePedido.status.in_(['em_corte','em_costura','com_bordadeira','ajustes_finais','compra_material','croqui_aprovado'])
    ).count()
    prontos = AteliePedido.query.filter_by(status='pronto').count()
    atrasados = [p for p in AteliePedido.query.all() if p.dias_para_entrega is not None and p.dias_para_entrega < 0 and p.status != 'entregue']
    return render_template('atelie/index.html',
        pedidos=pedidos, status_filtro=status_filtro,
        total=total, em_producao=em_producao, prontos=prontos,
        atrasados=len(atrasados),
        status_labels=AteliePedido.STATUS_LABELS)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            cliente_id = request.form.get('cliente_id', '').strip() or None
            data_entrega_str = request.form.get('data_entrega', '').strip()
            data_prova_str = request.form.get('data_prova', '').strip()
            pedido = AteliePedido(
                cliente_id=int(cliente_id) if cliente_id else None,
                nome_cliente=request.form['nome_cliente'].strip(),
                telefone=request.form.get('telefone', '').strip(),
                modelo=request.form.get('modelo', '').strip(),
                descricao=request.form.get('descricao', '').strip(),
                data_entrega=datetime.strptime(data_entrega_str, '%Y-%m-%d').date() if data_entrega_str else None,
                data_prova=datetime.strptime(data_prova_str, '%Y-%m-%d').date() if data_prova_str else None,
                costureira=request.form.get('costureira', '').strip(),
                status='aguardando_croqui',
                observacoes=request.form.get('observacoes', '').strip()
            )
            db.session.add(pedido)
            db.session.flush()

            # Histórico inicial
            hist = AtelieHistorico(
                pedido_id=pedido.id,
                autor=current_user.nome,
                mensagem='Pedido criado.',
                status_novo='aguardando_croqui'
            )
            db.session.add(hist)
            db.session.commit()
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('atelie.detalhe', id=pedido.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('atelie/novo.html', clientes=clientes)

@bp.route('/<int:id>')
@login_required
def detalhe(id):
    pedido = db.session.get(AteliePedido, id)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('atelie.index'))
    return render_template('atelie/detalhe.html', pedido=pedido, status_labels=AteliePedido.STATUS_LABELS)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    pedido = db.session.get(AteliePedido, id)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('atelie.index'))
    if request.method == 'POST':
        try:
            data_entrega_str = request.form.get('data_entrega', '').strip()
            data_prova_str = request.form.get('data_prova', '').strip()
            pedido.nome_cliente = request.form['nome_cliente'].strip()
            pedido.telefone = request.form.get('telefone', '').strip()
            pedido.modelo = request.form.get('modelo', '').strip()
            pedido.descricao = request.form.get('descricao', '').strip()
            pedido.data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date() if data_entrega_str else None
            pedido.data_prova = datetime.strptime(data_prova_str, '%Y-%m-%d').date() if data_prova_str else None
            pedido.costureira = request.form.get('costureira', '').strip()
            pedido.observacoes = request.form.get('observacoes', '').strip()
            db.session.commit()
            flash('Pedido atualizado.', 'success')
            return redirect(url_for('atelie.detalhe', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('atelie/editar.html', pedido=pedido)

@bp.route('/<int:id>/status', methods=['POST'])
@login_required
def alterar_status(id):
    pedido = db.session.get(AteliePedido, id)
    if not pedido:
        return jsonify({'erro': 'Não encontrado'}), 404
    novo_status = request.form.get('status')
    autor = request.form.get('autor', current_user.nome)
    mensagem = request.form.get('mensagem', f'Status alterado para: {AteliePedido.STATUS_LABELS.get(novo_status, novo_status)}')
    if novo_status in AteliePedido.STATUS_LABELS:
        pedido.status = novo_status
        hist = AtelieHistorico(
            pedido_id=id,
            autor=autor,
            mensagem=mensagem,
            status_novo=novo_status
        )
        db.session.add(hist)
        db.session.commit()
    return redirect(url_for('atelie.detalhe', id=id))

@bp.route('/<int:id>/historico', methods=['POST'])
@login_required
def add_historico(id):
    pedido = db.session.get(AteliePedido, id)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('atelie.index'))
    mensagem = request.form.get('mensagem', '').strip()
    autor = request.form.get('autor', current_user.nome).strip()
    if mensagem:
        hist = AtelieHistorico(
            pedido_id=id,
            autor=autor,
            mensagem=mensagem
        )
        db.session.add(hist)
        db.session.commit()
    return redirect(url_for('atelie.detalhe', id=id))

@bp.route('/<int:id>/material', methods=['POST'])
@login_required
def add_material(id):
    try:
        mat = AtelieMaterial(
            pedido_id=id,
            nome=request.form['nome'].strip(),
            quantidade=request.form.get('quantidade', '').strip(),
            unidade=request.form.get('unidade', 'metros'),
            cor=request.form.get('cor', '').strip(),
            fornecedor=request.form.get('fornecedor', '').strip(),
            status=request.form.get('status', 'pendente')
        )
        db.session.add(mat)
        db.session.commit()
        flash('Material adicionado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'danger')
    return redirect(url_for('atelie.detalhe', id=id))

@bp.route('/material/<int:id>/status', methods=['POST'])
@login_required
def material_status(id):
    mat = db.session.get(AtelieMaterial, id)
    if mat:
        mat.status = request.form.get('status', 'pendente')
        db.session.commit()
    return redirect(request.referrer or url_for('atelie.index'))

@bp.route('/material/<int:id>/excluir', methods=['POST'])
@login_required
def material_excluir(id):
    mat = db.session.get(AtelieMaterial, id)
    if mat:
        pedido_id = mat.pedido_id
        db.session.delete(mat)
        db.session.commit()
        flash('Material removido.', 'success')
        return redirect(url_for('atelie.detalhe', id=pedido_id))
    return redirect(url_for('atelie.index'))

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    if not current_user.is_admin:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('atelie.index'))
    pedido = db.session.get(AteliePedido, id)
    if pedido:
        db.session.delete(pedido)
        db.session.commit()
        flash('Pedido excluído.', 'success')
    return redirect(url_for('atelie.index'))
