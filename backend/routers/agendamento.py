from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from datetime import datetime, date, timedelta
from backend.app import db
from backend.models.agendamento import Agendamento

bp = Blueprint('agendamento', __name__, url_prefix='/agendamento')

@bp.route('/')
@login_required
def index():
    periodo = request.args.get('periodo', 'semana')
    hoje = date.today()
    if periodo == 'hoje':
        inicio = hoje
        fim = hoje
    elif periodo == 'mes':
        inicio = hoje.replace(day=1)
        fim = (hoje.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        inicio = hoje
        fim = hoje + timedelta(days=7)

    agendamentos = Agendamento.query.filter(
        Agendamento.data_visita >= inicio,
        Agendamento.data_visita <= fim
    ).order_by(Agendamento.data_visita).all()

    todos = Agendamento.query.order_by(Agendamento.data_visita.desc()).limit(50).all()

    return render_template('agendamento.html',
        agendamentos=agendamentos, todos=todos,
        periodo=periodo, hoje=hoje, inicio=inicio, fim=fim)

@bp.route('/novo', methods=['POST'])
@login_required
def novo():
    try:
        data_visita = datetime.strptime(request.form['data_visita'], '%Y-%m-%d').date()
        data_evento_str = request.form.get('data_evento', '').strip()
        data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date() if data_evento_str else None

        agendamento = Agendamento(
            nome=request.form['nome'].strip(),
            telefone=request.form.get('telefone', '').strip(),
            data_visita=data_visita,
            data_evento=data_evento,
            observacoes=request.form.get('observacoes', '').strip(),
            status='agendado'
        )
        db.session.add(agendamento)
        db.session.commit()
        flash('Agendamento criado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'danger')
    return redirect(url_for('agendamento.index'))

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    ag = db.session.get(Agendamento, id)
    if not ag:
        flash('Agendamento não encontrado.', 'danger')
        return redirect(url_for('agendamento.index'))
    if request.method == 'POST':
        try:
            ag.nome = request.form['nome'].strip()
            ag.telefone = request.form.get('telefone', '').strip()
            ag.data_visita = datetime.strptime(request.form['data_visita'], '%Y-%m-%d').date()
            data_evento_str = request.form.get('data_evento', '').strip()
            ag.data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date() if data_evento_str else None
            ag.observacoes = request.form.get('observacoes', '').strip()
            ag.status = request.form.get('status', 'agendado')
            db.session.commit()
            flash('Agendamento atualizado.', 'success')
            return redirect(url_for('agendamento.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('agendamento_editar.html', ag=ag)

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    ag = db.session.get(Agendamento, id)
    if ag:
        db.session.delete(ag)
        db.session.commit()
        flash('Agendamento removido.', 'success')
    return redirect(url_for('agendamento.index'))

@bp.route('/<int:id>/status', methods=['POST'])
@login_required
def alterar_status(id):
    ag = db.session.get(Agendamento, id)
    if ag:
        ag.status = request.form.get('status', 'agendado')
        db.session.commit()
    return redirect(url_for('agendamento.index'))
