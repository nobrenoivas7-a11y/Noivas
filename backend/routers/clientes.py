from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required
from backend.app import db
from backend.models.cliente import Cliente

bp = Blueprint('clientes', __name__, url_prefix='/clientes')

@bp.route('/')
@login_required
def lista():
    q = request.args.get('q', '')
    clientes = Cliente.query.order_by(Cliente.nome).all()
    if q:
        q_lower = q.lower()
        clientes = [c for c in clientes if q_lower in c.nome.lower() or (c.telefone and q_lower in c.telefone)]
    return render_template('clientes.html', clientes=clientes, q=q)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            cpf = request.form.get('cpf', '').strip() or None
            cliente = Cliente(
                nome=request.form['nome'].strip(),
                cpf=cpf,
                telefone=request.form.get('telefone', '').strip(),
                email=request.form.get('email', '').strip(),
                endereco=request.form.get('endereco', '').strip(),
                observacoes=request.form.get('observacoes', '').strip()
            )
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente cadastrada com sucesso!', 'success')
            return redirect(url_for('clientes.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('clientes_form.html', cliente=None)

@bp.route('/<int:id>')
@login_required
def detalhe(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        flash('Cliente não encontrada.', 'danger')
        return redirect(url_for('clientes.lista'))
    return render_template('clientes_detalhe.html', cliente=cliente)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        flash('Cliente não encontrada.', 'danger')
        return redirect(url_for('clientes.lista'))
    if request.method == 'POST':
        try:
            cliente.nome = request.form['nome'].strip()
            cliente.cpf = request.form.get('cpf', '').strip() or None
            cliente.telefone = request.form.get('telefone', '').strip()
            cliente.email = request.form.get('email', '').strip()
            cliente.endereco = request.form.get('endereco', '').strip()
            cliente.observacoes = request.form.get('observacoes', '').strip()
            db.session.commit()
            flash('Cliente atualizada.', 'success')
            return redirect(url_for('clientes.detalhe', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('clientes_form.html', cliente=cliente)

@bp.route('/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    clientes = Cliente.query.filter(
        db.or_(
            Cliente.nome.ilike(f'%{q}%'),
            Cliente.cpf.ilike(f'%{q}%'),
            Cliente.telefone.ilike(f'%{q}%')
        )
    ).limit(10).all()
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'cpf': c.cpf or '',
        'telefone': c.telefone or '',
        'email': c.email or '',
        'endereco': c.endereco or ''
    } for c in clientes])
