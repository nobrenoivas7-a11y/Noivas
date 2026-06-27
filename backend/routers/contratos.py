from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from backend.app import db
from backend.models.contrato import Contrato, ContratoItem, Pagamento
from backend.models.cliente import Cliente
from backend.models.peca import Peca
from backend.services.pdf_service import gerar_pdf_contrato

bp = Blueprint('contratos', __name__, url_prefix='/contratos')

@bp.route('/')
@login_required
def lista():
    status_filtro = request.args.get('status', '')
    q = request.args.get('q', '')
    contratos = Contrato.query.join(Cliente).order_by(Contrato.id.desc()).all()
    for c in contratos:
        c.atualizar_status()
    db.session.commit()
    if status_filtro:
        contratos = [c for c in contratos if c.status == status_filtro]
    if q:
        q_lower = q.lower()
        contratos = [c for c in contratos if q_lower in c.cliente.nome.lower()]
    return render_template('contratos_lista.html', contratos=contratos, status_filtro=status_filtro, q=q)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            cliente_id = request.form.get('cliente_id', '').strip()
            if cliente_id:
                cliente = db.session.get(Cliente, int(cliente_id))
            else:
                cpf = request.form.get('cpf', '').strip() or None
                cliente = Cliente(
                    nome=request.form['nome_cliente'].strip(),
                    cpf=cpf,
                    telefone=request.form.get('telefone', '').strip(),
                    email=request.form.get('email_cliente', '').strip(),
                    endereco=request.form.get('endereco', '').strip(),
                )
                db.session.add(cliente)
                db.session.flush()

            tipo_evento = request.form.get('tipo_evento', '')
            busto = request.form.get('busto', '')
            cintura = request.form.get('cintura', '')
            quadril = request.form.get('quadril', '')
            barra = request.form.get('barra', '')
            alca = request.form.get('alca', '')
            manga = request.form.get('manga', '')
            obs = request.form.get('obs_medidas', '')
            observacoes = f"Tipo do evento: {tipo_evento}\nBusto: {busto} cm\nCintura: {cintura} cm\nQuadril: {quadril} cm\nBarra/Comprimento: {barra} cm\nAlça: {alca} cm\nManga: {manga} cm\nObs. Medidas: {obs}"

            data_retirada = datetime.strptime(request.form['data_retirada'], '%Y-%m-%d').date()
            data_devolucao = datetime.strptime(request.form['data_devolucao'], '%Y-%m-%d').date()
            data_prova_str = request.form.get('data_prova', '').strip()
            data_prova = datetime.strptime(data_prova_str, '%Y-%m-%d').date() if data_prova_str else None
            valor_total = float(request.form.get('valor_total', 0) or 0)
            valor_sinal = float(request.form.get('valor_sinal', 0) or 0)

            contrato = Contrato(
                cliente_id=cliente.id,
                usuario_id=current_user.id,
                data_retirada=data_retirada,
                data_devolucao=data_devolucao,
                data_prova=data_prova,
                valor_total=valor_total,
                valor_sinal=valor_sinal,
                valor_pago=valor_sinal,
                status='ativo',
                observacoes=observacoes
            )
            db.session.add(contrato)
            db.session.flush()

            pecas_ids = request.form.getlist('pecas_ids')
            for pid in pecas_ids:
                peca = db.session.get(Peca, int(pid))
                if peca:
                    item = ContratoItem(contrato_id=contrato.id, peca_id=peca.id, preco_cobrado=peca.preco_aluguel)
                    db.session.add(item)

            if valor_sinal > 0:
