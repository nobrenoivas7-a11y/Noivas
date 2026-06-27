from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from backend.app import db
from backend.models.peca import Peca

bp = Blueprint('estoque', __name__, url_prefix='/estoque')

@bp.route('/')
@login_required
def lista():
    pecas = Peca.query.order_by(Peca.codigo).all()
    return render_template('estoque.html', pecas=pecas)

@bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if request.method == 'POST':
        try:
            modelo = request.form.get('modelo', '').strip()
            cor = request.form.get('cor', '').strip()
            tamanho = request.form.get('tamanho', '').strip()
            forcar = request.form.get('forcar_cadastro', '0') == '1'
            if not forcar:
                duplicata = Peca.query.filter(
                    db.func.lower(Peca.modelo) == modelo.lower(),
                    db.func.lower(Peca.cor) == cor.lower(),
                    db.func.lower(Peca.tamanho) == tamanho.lower()
                ).first()
                if duplicata:
                    flash(f'Já existe um vestido com esse Modelo/Cor/Tamanho ({duplicata.codigo}). Marque "Forçar cadastro" para continuar.', 'warning')
                    return render_template('estoque_form.html', dados=request.form, nova=True)
            peca = Peca(
                codigo=Peca.gerar_codigo(),
                tipo='Vestido de Noiva',
                cor=cor,
                tamanho=tamanho,
                modelo=modelo,
                descricao=request.form.get('descricao', '').strip(),
                preco_aluguel=float(request.form.get('preco_aluguel', 0) or 0),
                status='disponivel'
            )
            db.session.add(peca)
            db.session.commit()
            flash(f'Vestido {peca.codigo} cadastrado com sucesso!', 'success')
            return redirect(url_for('estoque.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('estoque_form.html', nova=True)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    peca = db.session.get(Peca, id)
    if not peca:
        flash('Vestido não encontrado.', 'danger')
        return redirect(url_for('estoque.lista'))
    if request.method == 'POST':
        try:
            peca.modelo = request.form.get('modelo', '').strip()
            peca.cor = request.form.get('cor', '').strip()
            peca.tamanho = request.form.get('tamanho', '').strip()
            peca.descricao = request.form.get('descricao', '').strip()
            peca.preco_aluguel = float(request.form.get('preco_aluguel', 0) or 0)
            peca.status = request.form.get('status', 'disponivel')
            db.session.commit()
            flash('Vestido atualizado.', 'success')
            return redirect(url_for('estoque.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
    return render_template('estoque_form.html', peca=peca, nova=False)

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    if not current_user.is_admin:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('estoque.lista'))
    peca = db.session.get(Peca, id)
    if peca:
        db.session.delete(peca)
        db.session.commit()
        flash('Vestido removido.', 'success')
    return redirect(url_for('estoque.lista'))

@bp.route('/disponibilidade')
@login_required
def disponibilidade():
    inicio_str = request.args.get('inicio')
    fim_str = request.args.get('fim')
    if not inicio_str or not fim_str:
        return jsonify([])
    try:
        data_inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(fim_str, '%Y-%m-%d').date()
    except:
        return jsonify([])
    pecas = Peca.query.filter(Peca.status == 'disponivel').order_by(Peca.codigo).all()
    resultado = []
    for p in pecas:
        resultado.append({
            'id': p.id,
            'codigo': p.codigo,
            'modelo': p.modelo,
            'cor': p.cor,
            'tamanho': p.tamanho,
            'preco_aluguel': p.preco_aluguel,
            'descricao': p.descricao or '',
            'livre': p.disponivel_no_periodo(data_inicio, data_fim)
        })
    return jsonify(resultado)

@bp.route('/verificar-duplicata')
@login_required
def verificar_duplicata():
    modelo = request.args.get('modelo', '')
    cor = request.args.get('cor', '')
    tamanho = request.args.get('tamanho', '')
    duplicata = Peca.query.filter(
        db.func.lower(Peca.modelo) == modelo.lower(),
        db.func.lower(Peca.cor) == cor.lower(),
        db.func.lower(Peca.tamanho) == tamanho.lower()
    ).first()
    if duplicata:
        return jsonify({'duplicata': True, 'codigo': duplicata.codigo})
    return jsonify({'duplicata': False})

@bp.route('/mais-alugados')
@login_required
def mais_alugados():
    from backend.models.contrato import ContratoItem
    from sqlalchemy import func
    resultado = db.session.query(
        Peca, func.count(ContratoItem.id).label('total')
    ).join(ContratoItem).group_by(Peca.id).order_by(func.count(ContratoItem.id).desc()).limit(20).all()
    return render_template('mais_alugados.html', resultado=resultado)
