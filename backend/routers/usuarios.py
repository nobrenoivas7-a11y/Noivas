from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from backend.app import db
from backend.models.usuario import Usuario

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@bp.route('/')
@login_required
def lista():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('dashboard.index'))
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('usuarios.html', usuarios=usuarios)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        try:
            nome = request.form['nome'].strip()
            email = request.form['email'].strip()
            senha = request.form['senha']
            nivel = request.form.get('nivel', 'funcionaria')
            if Usuario.query.filter_by(email=email).first():
                flash('Este usuário já existe.', 'danger')
                return render_template('usuarios_form.html', novo=True)
            usuario = Usuario(
                nome=nome,
                email=email,
                senha_hash=generate_password_hash(senha),
                nivel=nivel,
                ativo=True
            )
            db.session.add(usuario)
            db.session.commit()
            flash(f'Usuário {nome} criado com sucesso!', 'success')
            return redirect(url_for('usuarios.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('usuarios_form.html', novo=True)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('dashboard.index'))
    usuario = db.session.get(Usuario, id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.lista'))
    if request.method == 'POST':
        try:
            usuario.nome = request.form['nome'].strip()
            usuario.email = request.form['email'].strip()
            usuario.nivel = request.form.get('nivel', 'funcionaria')
            nova_senha = request.form.get('senha', '').strip()
            if nova_senha:
                usuario.senha_hash = generate_password_hash(nova_senha)
            db.session.commit()
            flash('Usuário atualizado.', 'success')
            return redirect(url_for('usuarios.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('usuarios_form.html', usuario=usuario, novo=False)

@bp.route('/<int:id>/ativar', methods=['POST'])
@login_required
def ativar(id):
    if not current_user.is_admin:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('usuarios.lista'))
    usuario = db.session.get(Usuario, id)
    if usuario:
        usuario.ativo = not usuario.ativo
        db.session.commit()
        status = 'ativado' if usuario.ativo else 'desativado'
        flash(f'Usuário {usuario.nome} {status}.', 'success')
    return redirect(url_for('usuarios.lista'))
