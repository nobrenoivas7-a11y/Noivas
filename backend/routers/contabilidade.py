from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from datetime import date, datetime
from backend.app import db
from backend.models.contrato import Pagamento, Despesa, Contrato
from backend.services.pdf_relatorio import gerar_pdf_relatorio

bp = Blueprint('contabilidade', __name__, url_prefix='/contabilidade')

MESES = ['','Janeiro','Fevereiro','Março','Abril','Maio','Junho',
         'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

@bp.route('/')
@login_required
def index():
    hoje = date.today()
    mes = int(request.args.get('mes', hoje.month))
    ano = int(request.args.get('ano', hoje.year))

    pagamentos = Pagamento.query.filter(
        db.extract('month', Pagamento.data) == mes,
        db.extract('year', Pagamento.data) == ano
    ).order_by(Pagamento.data.desc()).all()

    despesas = Despesa.query.filter(
        db.extract('month', Despesa.data) == mes,
        db.extract('year', Despesa.data) == ano
    ).order_by(Despesa.data).all()

    receita = sum(p.valor for p in pagamentos)
    total_despesas = sum(d.valor for d in despesas)
    lucro = receita - total_despesas

    por_forma = {}
    for p in pagamentos:
        por_forma[p.forma] = por_forma.get(p.forma, 0) + p.valor

    return render_template('contabilidade.html',
        pagamentos=pagamentos, despesas=despesas,
        receita=receita, total_despesas=total_despesas, lucro=lucro,
        por_forma=por_forma, mes=mes, ano=ano, mes_nome=MESES[mes])

@bp.route('/despesas')
@login_required
def despesas():
    hoje = date.today()
    mes = int(request.args.get('mes', hoje.month))
    ano = int(request.args.get('ano', hoje.year))
    meta = float(request.args.get('meta', 0) or 0)

    despesas = Despesa.query.filter(
        db.extract('month', Despesa.data) == mes,
        db.extract('year', Despesa.data) == ano
    ).order_by(Despesa.data.desc()).all()

    pagamentos = Pagamento.query.filter(
        db.extract('month', Pagamento.data) == mes,
        db.extract('year', Pagamento.data) == ano
    ).all()
    receita = sum(p.valor for p in pagamentos)
    total_despesas = sum(d.valor for d in despesas)
    lucro = receita - total_despesas

    por_categoria = {}
    for d in despesas:
        por_categoria[d.categoria] = por_categoria.get(d.categoria, 0) + d.valor

    return render_template('despesas.html',
        despesas=despesas, receita=receita,
        total_despesas=total_despesas, lucro=lucro,
        por_categoria=por_categoria,
        mes=mes, ano=ano, mes_nome=MESES[mes], meta=meta)

@bp.route('/despesas/nova', methods=['POST'])
@login_required
def nova_despesa():
    try:
        despesa = Despesa(
            descricao=request.form['descricao'].strip(),
            valor=float(request.form.get('valor', 0) or 0),
            categoria=request.form.get('categoria', 'Outros'),
            data=datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        )
        db.session.add(despesa)
        db.session.commit()
        flash('Despesa registrada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('contabilidade.despesas'))

@bp.route('/despesas/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_despesa(id):
    d = db.session.get(Despesa, id)
    if d:
        db.session.delete(d)
        db.session.commit()
        flash('Despesa removida.', 'success')
    return redirect(request.referrer or url_for('contabilidade.despesas'))

@bp.route('/relatorio-pdf')
@login_required
def relatorio_pdf():
    hoje = date.today()
    mes = int(request.args.get('mes', hoje.month))
    ano = int(request.args.get('ano', hoje.year))

    pagamentos = Pagamento.query.filter(
        db.extract('month', Pagamento.data) == mes,
        db.extract('year', Pagamento.data) == ano
    ).all()
    despesas = Despesa.query.filter(
        db.extract('month', Despesa.data) == mes,
        db.extract('year', Despesa.data) == ano
    ).all()

    pdf_bytes = gerar_pdf_relatorio(mes, ano, MESES[mes], pagamentos, despesas)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="Relatorio_{MESES[mes]}_{ano}.pdf"'
    return response
