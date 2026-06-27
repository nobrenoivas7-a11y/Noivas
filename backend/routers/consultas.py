from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from backend.models.peca import Peca
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente
from backend.app import db

bp = Blueprint('consultas', __name__, url_prefix='/consultas')

@bp.route('/')
@login_required
def index():
    return render_template('consultas.html')

@bp.route('/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'pecas': [], 'contratos': [], 'clientes': []})

    pecas = Peca.query.filter(
        db.or_(
            Peca.codigo.ilike(f'%{q}%'),
            Peca.modelo.ilike(f'%{q}%'),
            Peca.cor.ilike(f'%{q}%')
        )
    ).limit(10).all()

    clientes = Cliente.query.filter(
        db.or_(
            Cliente.nome.ilike(f'%{q}%'),
            Cliente.telefone.ilike(f'%{q}%')
        )
    ).limit(10).all()

    return jsonify({
        'pecas': [{'id': p.id, 'codigo': p.codigo, 'modelo': p.modelo, 'cor': p.cor, 'tamanho': p.tamanho, 'status': p.status} for p in pecas],
        'clientes': [{'id': c.id, 'nome': c.nome, 'telefone': c.telefone or '', 'total_contratos': len(c.contratos)} for c in clientes],
    })
