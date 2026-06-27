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
            # Cliente
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

            # Medidas / observações
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
            valor_total = float(request.form.get('valor_total', 0) or 0)
            valor_sinal = float(request.form.get('valor_sinal', 0) or 0)

            contrato = Contrato(
                cliente_id=cliente.id,
                usuario_id=current_user.id,
                data_retirada=data_retirada,
                data_devolucao=data_devolucao,
                valor_total=valor_total,
                valor_sinal=valor_sinal,
                valor_pago=valor_sinal,
                status='ativo',
                observacoes=observacoes
            )
            db.session.add(contrato)
            db.session.flush()

            # Peças
            pecas_ids = request.form.getlist('pecas_ids')
            for pid in pecas_ids:
                peca = db.session.get(Peca, int(pid))
                if peca:
                    item = ContratoItem(contrato_id=contrato.id, peca_id=peca.id, preco_cobrado=peca.preco_aluguel)
                    db.session.add(item)

            # Sinal
            if valor_sinal > 0:
                forma = request.form.get('forma_pagamento', 'pix')
                pag = Pagamento(contrato_id=contrato.id, valor=valor_sinal, tipo='sinal', forma=forma)
                db.session.add(pag)

            db.session.commit()

            acao = request.form.get('acao', 'novo')
            if acao == 'pdf':
                return redirect(url_for('contratos.pdf', id=contrato.id))
            flash('Contrato salvo com sucesso!', 'success')
            return redirect(url_for('contratos.novo'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar contrato: {str(e)}', 'danger')

    return render_template('contrato_novo.html')

@bp.route('/<int:id>')
@login_required
def detalhe(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    contrato.atualizar_status()
    db.session.commit()
    return render_template('contrato_detalhe.html', contrato=contrato)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('contratos.detalhe', id=id))
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    if request.method == 'POST':
        try:
            contrato.data_retirada = datetime.strptime(request.form['data_retirada'], '%Y-%m-%d').date()
            contrato.data_devolucao = datetime.strptime(request.form['data_devolucao'], '%Y-%m-%d').date()
            contrato.valor_total = float(request.form.get('valor_total', 0) or 0)
            contrato.observacoes = request.form.get('observacoes', '')
            db.session.commit()
            flash('Contrato atualizado.', 'success')
            return redirect(url_for('contratos.detalhe', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('contrato_editar.html', contrato=contrato)

@bp.route('/<int:id>/status', methods=['POST'])
@login_required
def alterar_status(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return jsonify({'erro': 'Não encontrado'}), 404
    novo_status = request.form.get('status')
    if novo_status in ('ativo', 'atrasado', 'devolvido', 'cancelado'):
        contrato.status = novo_status
        if novo_status == 'devolvido' and not contrato.data_devolucao_real:
            contrato.data_devolucao_real = date.today()
        db.session.commit()
    return redirect(request.referrer or url_for('contratos.lista'))

@bp.route('/<int:id>/pagamento', methods=['POST'])
@login_required
def registrar_pagamento(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    valor = float(request.form.get('valor', 0) or 0)
    if valor > 0:
        pag = Pagamento(
            contrato_id=id,
            valor=valor,
            tipo=request.form.get('tipo', 'complemento'),
            forma=request.form.get('forma', 'pix'),
            observacao=request.form.get('observacao', '')
        )
        db.session.add(pag)
        contrato.valor_pago = (contrato.valor_pago or 0) + valor
        db.session.commit()
        flash('Pagamento registrado.', 'success')
    return redirect(url_for('contratos.detalhe', id=id))

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('contratos.lista'))
    contrato = db.session.get(Contrato, id)
    if contrato:
        db.session.delete(contrato)
        db.session.commit()
        flash('Contrato excluído.', 'success')
    return redirect(url_for('contratos.lista'))

@bp.route('/<int:id>/pdf')
@login_required
def pdf(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    pdf_bytes = gerar_pdf_contrato(contrato)
    nome_arquivo = f"Contrato_{id:04d}_{contrato.cliente.nome.replace(' ', '_')}.pdf"
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response
