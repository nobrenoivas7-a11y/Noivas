from datetime import datetime
from backend.app import db

class Peca(db.Model):
    __tablename__ = 'pecas'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), default='Vestido de Noiva')
    cor = db.Column(db.String(50))
    tamanho = db.Column(db.String(20))
    modelo = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    preco_aluguel = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='disponivel')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship('ContratoItem', backref='peca', lazy=True)

    def disponivel_no_periodo(self, data_inicio, data_fim):
        if self.status in ('manutencao', 'inativa'):
            return False
        from backend.models.contrato import ContratoItem, Contrato
        conflito = db.session.query(ContratoItem).join(Contrato).filter(
            ContratoItem.peca_id == self.id,
            Contrato.status.in_(['ativo', 'atrasado']),
            Contrato.data_retirada < data_fim,
            Contrato.data_devolucao > data_inicio
        ).first()
        return conflito is None

    @staticmethod
    def gerar_codigo():
        ultima = Peca.query.filter(
            Peca.codigo.like('VES%'),
            ~Peca.codigo.like('%_IMP')
        ).order_by(Peca.id.desc()).first()
        if ultima:
            try:
                num = int(ultima.codigo[3:]) + 1
            except:
                num = 1
        else:
            num = 1
        return f'VES{num:04d}'

    def __repr__(self):
        return f'<Peca {self.codigo}>'
