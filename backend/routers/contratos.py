from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from backend.app import db
from backend.models.contrato import Contrato, ContratoItem, Pagamento
from backend.models.peca import Peca
from backend.models.cliente import Cliente
from sqlalchemy import text
import datetime

bp = Blueprint('contratos', __name__, url_prefix='/contratos')


@bp.route('/')
@login_required
def lista():
    status_filter = request.args.get('status', '')
    q = request.args.get('q', '')
    query = Contrato.query.join(Cliente, Contrato.cliente_id == Cliente.id)
    if status_filter:
        query = query.filter(Contrato.status == status_filter)
    if q:
        query = query.filter(Cliente.nome.ilike(f'%{q}%'))
    contratos = query.order_by(Contrato.id.desc()).all()
    return render_template('contratos_lista.html', contratos=contratos,
                           status_filter=status_filter, q=q)


@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    pecas = Peca.query.filter_by(status='disponivel').order_by(Peca.codigo).all()
    if request.method == 'POST':
        try:
            # Dados da cliente
            nome_cliente = request.form.get('nome_cliente', '').strip()
            telefone = request.form.get('telefone', '').strip()
            cpf = request.form.get('cpf', '').strip()
            email = request.form.get('email', '').strip()
            endereco = request.form.get('endereco', '').strip()

            # Buscar cliente existente pelo telefone ou nome
            cliente = None
            if telefone:
                cliente = Cliente.query.filter_by(telefone=telefone).first()
            if not cliente and nome_cliente:
                cliente = Cliente.query.filter(
                    Cliente.nome.ilike(nome_cliente)
                ).first()

            # Criar cliente se não existir
            if not cliente:
                cliente = Cliente(
                    nome=nome_cliente,
                    telefone=telefone,
                    cpf=cpf if cpf else None,
                    email=email if email else None,
                    endereco=endereco if endereco else None,
                )
                db.session.add(cliente)
                db.session.flush()
            else:
                # Atualizar dados se vieram preenchidos
                if cpf: cliente.cpf = cpf
                if email: cliente.email = email
                if endereco: cliente.endereco = endereco

            # Datas
            data_retirada = datetime.date.fromisoformat(request.form['data_retirada'])
            data_devolucao = datetime.date.fromisoformat(request.form['data_devolucao'])
            data_prova = request.form.get('data_prova') or None
            if data_prova:
                data_prova = datetime.date.fromisoformat(data_prova)

            valor_total = float(request.form.get('valor_total') or 0)
            valor_pago = float(request.form.get('valor_pago') or 0)
            forma_pagamento = request.form.get('forma_pagamento', '')
            observacoes = request.form.get('observacoes', '')

            contrato = Contrato(
                cliente_id=cliente.id,
                usuario_id=current_user.id,
                data_retirada=data_retirada,
                data_devolucao=data_devolucao,
                data_prova=data_prova,
                valor_total=valor_total,
                valor_pago=valor_pago,
                observacoes=observacoes,
                status='ativo'
            )
            db.session.add(contrato)
            db.session.flush()

            peca_ids = request.form.getlist('peca_ids')
            for peca_id in peca_ids:
                if peca_id:
                    item = ContratoItem(contrato_id=contrato.id, peca_id=int(peca_id))
                    db.session.add(item)

            if valor_pago > 0:
                pag = Pagamento(
                    contrato_id=contrato.id,
                    valor=valor_pago,
                    forma=forma_pagamento,
                    data=datetime.datetime.now()
                )
                db.session.add(pag)

            db.session.execute(text("""
                INSERT INTO contrato_historico (contrato_id, autor, mensagem)
                VALUES (:cid, :autor, :msg)
            """), {'cid': contrato.id, 'autor': current_user.nome,
                   'msg': 'Contrato criado.'})

            db.session.commit()
            flash(f'Contrato criado com sucesso! Cliente: {cliente.nome}', 'success')
            return redirect(url_for('contratos.detalhe', id=contrato.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('contrato_novo.html', pecas=pecas)


@bp.route('/<int:id>')
@login_required
def detalhe(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    historico = db.session.execute(
        text("SELECT * FROM contrato_historico WHERE contrato_id=:id ORDER BY criado_em DESC"),
        {'id': id}
    ).fetchall()
    return render_template('contrato_detalhe.html', contrato=contrato, historico=historico)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        flash('Contrato não encontrado.', 'danger')
        return redirect(url_for('contratos.lista'))
    clientes = Cliente.query.order_by(Cliente.nome).all()
    pecas = Peca.query.filter_by(status='disponivel').order_by(Peca.codigo).all()
    peca_ids_atuais = [str(i.peca_id) for i in contrato.itens]

    if request.method == 'POST':
        try:
            alteracoes = []
            mensagem_manual = request.form.get('mensagem_historico', '').strip()

            novo_status = request.form.get('status', contrato.status)
            if novo_status != contrato.status:
                alteracoes.append(f'Status alterado para "{novo_status}".')
            contrato.status = novo_status

            nova_prova = request.form.get('data_prova') or None
            if nova_prova:
                nova_prova = datetime.date.fromisoformat(nova_prova)
            contrato.data_prova = nova_prova

            nova_devolucao = datetime.date.fromisoformat(request.form['data_devolucao'])
            if nova_devolucao != contrato.data_devolucao:
                alteracoes.append(f'Data de devolução alterada para {nova_devolucao.strftime("%d/%m/%Y")}.')
            contrato.data_devolucao = nova_devolucao

            novo_valor = float(request.form.get('valor_total') or 0)
            if novo_valor != contrato.valor_total:
                alteracoes.append(f'Valor total alterado para R$ {novo_valor:.2f}.')
            contrato.valor_total = novo_valor

            novo_obs = request.form.get('observacoes', '')
            if novo_obs != (contrato.observacoes or ''):
                alteracoes.append('Observações atualizadas.')
            contrato.observacoes = novo_obs

            contrato.data_retirada = datetime.date.fromisoformat(request.form['data_retirada'])

            novas_peca_ids = request.form.getlist('peca_ids')
            antigas = set(peca_ids_atuais)
            novas = set(novas_peca_ids)
            if antigas != novas:
                alteracoes.append('Peças do contrato atualizadas.')
            ContratoItem.query.filter_by(contrato_id=contrato.id).delete()
            for peca_id in novas_peca_ids:
                if peca_id:
                    item = ContratoItem(contrato_id=contrato.id, peca_id=int(peca_id))
                    db.session.add(item)

            novo_pagamento = float(request.form.get('novo_pagamento') or 0)
            nova_forma = request.form.get('nova_forma_pagamento', '')
            if novo_pagamento > 0:
                pag = Pagamento(
                    contrato_id=contrato.id,
                    valor=novo_pagamento,
                    forma=nova_forma,
                    data=datetime.datetime.now()
                )
                db.session.add(pag)
                contrato.valor_pago = (contrato.valor_pago or 0) + novo_pagamento
                alteracoes.append(f'Pagamento de R$ {novo_pagamento:.2f} registrado.')

            msg_final = mensagem_manual
            if alteracoes:
                msg_final = (mensagem_manual + '\n' if mensagem_manual else '') + '\n'.join(alteracoes)
            if msg_final:
                db.session.execute(text("""
                    INSERT INTO contrato_historico (contrato_id, autor, mensagem)
                    VALUES (:cid, :autor, :msg)
                """), {'cid': contrato.id, 'autor': current_user.nome, 'msg': msg_final})

            db.session.commit()
            flash('Contrato atualizado!', 'success')
            return redirect(url_for('contratos.detalhe', id=contrato.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')

    return render_template('contrato_editar.html', contrato=contrato,
                           clientes=clientes, pecas=pecas,
                           peca_ids_atuais=peca_ids_atuais)


@bp.route('/<int:id>/status', methods=['POST'])
@login_required
def alterar_status(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return redirect(url_for('contratos.lista'))
    novo_status = request.form.get('status')
    if novo_status and novo_status != contrato.status:
        msg = f'Status alterado para "{novo_status}".'
        db.session.execute(text("""
            INSERT INTO contrato_historico (contrato_id, autor, mensagem)
            VALUES (:cid, :autor, :msg)
        """), {'cid': contrato.id, 'autor': current_user.nome, 'msg': msg})
        contrato.status = novo_status
        db.session.commit()
        flash('Status atualizado!', 'success')
    return redirect(url_for('contratos.lista'))


@bp.route('/<int:id>/historico', methods=['POST'])
@login_required
def add_historico(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return redirect(url_for('contratos.lista'))
    mensagem = request.form.get('mensagem', '').strip()
    if mensagem:
        db.session.execute(text("""
            INSERT INTO contrato_historico (contrato_id, autor, mensagem)
            VALUES (:cid, :autor, :msg)
        """), {'cid': id, 'autor': current_user.nome, 'msg': mensagem})
        db.session.commit()
        flash('Atualização registrada!', 'success')
    return redirect(url_for('contratos.detalhe', id=id))


@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
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
    return render_template('contrato_pdf.html', contrato=contrato)
