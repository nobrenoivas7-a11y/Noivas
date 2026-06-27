from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date, timedelta
from backend.app import db
from backend.models.contrato import Contrato, Pagamento
from backend.models.peca import Peca
from backend.models.cliente import Cliente

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
@login_required
def index():
    hoje = date.today()
    ativos = Contrato.query.filter(Contrato.status == 'ativo').all()
    for c in ativos:
        c.atualizar_status()
    db.session.commit()

    total_contratos = Contrato.query.filter(Contrato.status.in_(['ativo', 'atrasado'])).count()
    total_atrasados = Contrato.query.filter_by(status='atrasado').count()

    mes, ano = hoje.month, hoje.year
    pagamentos_mes = Pagamento.query.filter(
        db.extract('month', Pagamento.data) == mes,
        db.extract('year', Pagamento.data) == ano
    ).all()
    receita_mes = sum(p.valor for p in pagamentos_mes)

    por_forma = {}
    for p in pagamentos_mes:
        por_forma[p.forma] = por_forma.get(p.forma, 0) + p.valor

    contratos_ativos = Contrato.query.filter(Contrato.status.in_(['ativo', 'atrasado'])).all()
    a_receber = sum(c.saldo_restante for c in contratos_ativos)

    saidas_hoje = Contrato.query.filter(
        Contrato.data_retirada == hoje,
        Contrato.status.in_(['ativo', 'atrasado'])
    ).count()

    limite = hoje + timedelta(days=3)
    alertas = Contrato.query.join(Cliente).filter(
        Contrato.status.in_(['ativo', 'atrasado']),
        Contrato.data_devolucao >= hoje,
        Contrato.data_devolucao <= limite
    ).order_by(Contrato.data_devolucao).all()

    contratos_recentes = Contrato.query.order_by(Contrato.id.desc()).limit(8).all()

    return render_template('dashboard.html',
        hoje=hoje,
        total_contratos=total_contratos,
        total_atrasados=total_atrasados,
        receita_mes=receita_mes,
        por_forma=por_forma,
        a_receber=a_receber,
        saidas_hoje=saidas_hoje,
        alertas=alertas,
        contratos_recentes=contratos_recentes,
    )
