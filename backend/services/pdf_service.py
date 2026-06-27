from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm

ROSE_GOLD = colors.HexColor('#B76E79')
ROSE_LIGHT = colors.HexColor('#F5E6E8')
ROSE_MID = colors.HexColor('#E8C5C9')
BRANCO = colors.white
CINZA_ESCURO = colors.HexColor('#3D3D3D')
CINZA_CLARO = colors.HexColor('#F9F4F5')
PRETO = colors.black

W, H = A4

def gerar_pdf_contrato(contrato):
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    _draw_page(c, contrato)
    c.save()
    return buf.getvalue()

def _draw_page(c, contrato):
    y = H

    # ── CABEÇALHO ──────────────────────────────────────────
    c.setFillColor(ROSE_GOLD)
    c.rect(0, H - 3*cm, W, 3*cm, fill=1, stroke=0)

    c.setFillColor(BRANCO)
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(W/2, H - 1.4*cm, 'NOBRE ELEGANCY NOIVAS')
    c.setFont('Helvetica', 10)
    c.drawCentredString(W/2, H - 2.0*cm, 'Aluguel de Vestidos de Noiva  |  Fortaleza/CE')
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, H - 2.7*cm, 'CONTRATO DE LOCAÇÃO DE VESTIDO')

    y = H - 3.5*cm

    # ── SEÇÃO: PARTES ──────────────────────────────────────
    y = _secao(c, y, 'PARTES')
    dados_partes = [
        ('Locador:', 'Nobre Elegancy Noivas — Fortaleza/CE'),
        ('Locatária:', contrato.cliente.nome),
        ('CPF:', contrato.cliente.cpf or 'Não informado'),
        ('Telefone:', contrato.cliente.telefone or 'Não informado'),
        ('Endereço:', contrato.cliente.endereco or 'Não informado'),
    ]
    for label, valor in dados_partes:
        y = _linha(c, y, label, valor)

    y -= 0.3*cm

    # ── SEÇÃO: DADOS DO EVENTO ─────────────────────────────
    y = _secao(c, y, 'DADOS DO EVENTO')
    obs = contrato.observacoes or ''
    tipo_evento = _extrair_obs(obs, 'Tipo do evento:')
    pecas_str = ', '.join([f'{i.peca.codigo} — {i.peca.modelo} ({i.peca.cor}, T{i.peca.tamanho})' for i in contrato.itens]) or 'Não informado'
    dados_evento = [
        ('Tipo do Evento:', tipo_evento or 'Não informado'),
        ('Vestido(s):', pecas_str),
        ('Data de Retirada:', contrato.data_retirada.strftime('%d/%m/%Y')),
        ('Data de Devolução:', contrato.data_devolucao.strftime('%d/%m/%Y')),
        ('Contrato Nº:', f'#{contrato.id:04d}'),
    ]
    for label, valor in dados_evento:
        y = _linha(c, y, label, valor)

    y -= 0.3*cm

    # ── SEÇÃO: MEDIDAS ─────────────────────────────────────
    y = _secao(c, y, 'MEDIDAS DA NOIVA')
    campos_medida = ['Busto', 'Cintura', 'Quadril', 'Barra/Comprimento', 'Alça', 'Manga', 'Obs. Medidas']
    for campo in campos_medida:
        val = _extrair_obs(obs, f'{campo}:')
        if val:
            y = _linha(c, y, f'{campo}:', val)

    y -= 0.3*cm

    # ── SEÇÃO: VALORES ─────────────────────────────────────
    y = _secao(c, y, 'VALORES E PAGAMENTO')
    pagamentos = contrato.pagamentos
    forma = pagamentos[0].forma.replace('_', ' ').title() if pagamentos else 'Não informado'
    dados_valores = [
        ('Valor Total:', f'R$ {contrato.valor_total:.2f}'.replace('.', ',')),
        ('Sinal Pago:', f'R$ {contrato.valor_sinal:.2f}'.replace('.', ',')),
        ('Saldo Restante:', f'R$ {contrato.saldo_restante:.2f}'.replace('.', ',')),
        ('Forma de Pagamento:', forma),
    ]
    for label, valor in dados_valores:
        y = _linha(c, y, label, valor)

    y -= 0.5*cm

    # ── CLÁUSULAS ──────────────────────────────────────────
    clausulas = [
        "1. O(a) LOCATÁRIO(A) compromete-se a devolver o vestido na data acordada, limpo e sem avarias.",
        "2. Em caso de atraso na devolução, será cobrada multa de R$ 50,00 por dia de atraso.",
        "3. Danos, rasgos, manchas ou perdas de peças serão cobrados do(a) LOCATÁRIO(A) pelo valor de reposição.",
        "4. O sinal pago no ato da reserva não é reembolsável em caso de desistência.",
        "5. O vestido será entregue limpo e pronto para uso. Ajustes de costura são de responsabilidade da LOCATÁRIA.",
        "6. O LOCADOR não se responsabiliza por itens pessoais esquecidos nas dependências da loja.",
        "7. A reserva somente é confirmada após o pagamento do sinal.",
        "8. O presente contrato rege-se pelas normas do Código Civil Brasileiro.",
        "9. Fica eleito o foro da comarca de Fortaleza/CE para dirimir quaisquer dúvidas.",
        "10. As partes declaram ter lido e aceito os termos deste contrato.",
    ]

    if y < 7*cm:
        c.showPage()
        y = H - 1.5*cm

    y = _secao(c, y, 'CLÁUSULAS CONTRATUAIS')
    c.setFont('Helvetica', 8)
    c.setFillColor(CINZA_ESCURO)
    for cl in clausulas:
        if y < 5*cm:
            c.showPage()
            y = H - 1.5*cm
        lines = _wrap(c, cl, W - 3*cm, 'Helvetica', 8)
        for line in lines:
            c.drawString(1.5*cm, y, line)
            y -= 0.45*cm
        y -= 0.1*cm

    y -= 0.5*cm

    # ── ASSINATURAS ────────────────────────────────────────
    if y < 4*cm:
        c.showPage()
        y = H - 1.5*cm

    c.setStrokeColor(ROSE_MID)
    c.line(1.5*cm, y, 9*cm, y)
    c.line(11*cm, y, W - 1.5*cm, y)
    c.setFont('Helvetica', 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawCentredString(5.25*cm, y - 0.4*cm, 'Locatária')
    c.drawCentredString(16*cm, y - 0.4*cm, 'Locador(a)')
    c.drawCentredString(5.25*cm, y - 0.75*cm, contrato.cliente.nome)
    c.drawCentredString(16*cm, y - 0.75*cm, 'Nobre Elegancy Noivas')

    # ── RODAPÉ ─────────────────────────────────────────────
    c.setFillColor(ROSE_LIGHT)
    c.rect(0, 0, W, 1.2*cm, fill=1, stroke=0)
    c.setFillColor(ROSE_GOLD)
    c.setFont('Helvetica', 8)
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    c.drawString(1.5*cm, 0.45*cm, f'Gerado em: {agora}')
    c.drawCentredString(W/2, 0.45*cm, 'Nobre Elegancy Noivas — Fortaleza/CE')
    c.drawRightString(W - 1.5*cm, 0.45*cm, f'Contrato #{contrato.id:04d}')


def _secao(c, y, titulo):
    c.setFillColor(ROSE_LIGHT)
    c.rect(1*cm, y - 0.65*cm, W - 2*cm, 0.65*cm, fill=1, stroke=0)
    c.setFillColor(ROSE_GOLD)
    c.rect(1*cm, y - 0.65*cm, 0.25*cm, 0.65*cm, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(ROSE_GOLD)
    c.drawString(1.5*cm, y - 0.45*cm, titulo)
    return y - 0.85*cm


def _linha(c, y, label, valor):
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(ROSE_GOLD)
    c.drawString(1.5*cm, y, label)
    c.setFont('Helvetica', 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawString(6*cm, y, str(valor))
    return y - 0.5*cm


def _extrair_obs(obs, campo):
    for linha in obs.split('\n'):
        if linha.strip().startswith(campo):
            return linha.split(':', 1)[1].strip() if ':' in linha else ''
    return ''


def _wrap(c, text, max_width, font, size):
    words = text.split()
    lines = []
    current = ''
    for word in words:
        test = f'{current} {word}'.strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
