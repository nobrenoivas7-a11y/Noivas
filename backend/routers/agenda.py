from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date, timedelta
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente
from backend.app import db

bp = Blueprint('agenda', __name__, url_prefix='/agenda')

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

    contratos = Contrato.query.join(Cliente).filter(
        Contrato.data_retirada >= inicio,
        Contrato.data_retirada <= fim,
        Contrato.status.in_(['ativo', 'atrasado', 'devolvido'])
    ).order_by(Contrato.data_retirada).all()

    for c in contratos:
        c.atualizar_status()
    db.session.commit()

    return render_template('agenda.html', contratos=contratos, periodo=periodo, hoje=hoje, inicio=inicio, fim=fim)

@bp.route('/provas')
@login_required
def provas():
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

    contratos = Contrato.query.join(Cliente).filter(
        Contrato.data_prova >= inicio,
        Contrato.data_prova <= fim,
        Contrato.status.in_(['ativo', 'atrasado', 'devolvido'])
    ).order_by(Contrato.data_prova).all()

    return render_template('agenda_provas.html', contratos=contratos, periodo=periodo, hoje=hoje, inicio=inicio, fim=fim)
