from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date, timedelta
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente
from backend.app import db

bp = Blueprint('agenda', __name__, url_prefix='/agenda')


def calcular_periodo(periodo, hoje, ano_mes=None):
    if periodo == 'hoje':
        inicio = hoje
        fim = hoje
    elif periodo == 'mes':
        if ano_mes:
            ano, mes = map(int, ano_mes.split('-'))
            ref = date(ano, mes, 1)
        else:
            ref = hoje.replace(day=1)
        inicio = ref.replace(day=1)
        fim = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        inicio = hoje
        fim = hoje + timedelta(days=7)
    return inicio, fim


def mes_adjacente(ref, delta):
    ano, mes = ref.year, ref.month + delta
    while mes > 12:
        mes -= 12
        ano += 1
    while mes < 1:
        mes += 12
        ano -= 1
    return f'{ano:04d}-{mes:02d}'


@bp.route('/')
@login_required
def index():
    periodo = request.args.get('periodo', 'semana')
    ano_mes = request.args.get('mes', '')
    hoje = date.today()
    inicio, fim = calcular_periodo(periodo, hoje, ano_mes)

    mes_anterior = mes_adjacente(inicio, -1)
    mes_seguinte = mes_adjacente(inicio, 1)

    contratos = Contrato.query.join(Cliente).filter(
        Contrato.data_retirada >= inicio,
        Contrato.data_retirada <= fim,
        Contrato.status.in_(['ativo', 'atrasado', 'devolvido'])
    ).order_by(Contrato.data_retirada).all()
    for c in contratos:
        c.atualizar_status()
    db.session.commit()
    return render_template('agenda.html', contratos=contratos, periodo=periodo, hoje=hoje,
                           inicio=inicio, fim=fim, mes_anterior=mes_anterior, mes_seguinte=mes_seguinte)


@bp.route('/provas')
@login_required
def provas():
    periodo = request.args.get('periodo', 'semana')
    ano_mes = request.args.get('mes', '')
    hoje = date.today()
    inicio, fim = calcular_periodo(periodo, hoje, ano_mes)

    mes_anterior = mes_adjacente(inicio, -1)
    mes_seguinte = mes_adjacente(inicio, 1)

    contratos = Contrato.query.join(Cliente).filter(
        Contrato.data_prova >= inicio,
        Contrato.data_prova <= fim,
        Contrato.status.in_(['ativo', 'atrasado', 'devolvido'])
    ).order_by(Contrato.data_prova).all()
    return render_template('agenda_provas.html', contratos=contratos, periodo=periodo, hoje=hoje,
                           inicio=inicio, fim=fim, mes_anterior=mes_anterior, mes_seguinte=mes_seguinte)
