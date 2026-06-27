from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm

ROSE = colors.HexColor('#C9848E')
GOLD = colors.HexColor('#C9A96E')
DARK = colors.HexColor('#1a0d12')
DARK2 = colors.HexColor('#2a1218')
BRANCO = colors.white
CINZA = colors.HexColor('#b08890')
W, H = A4

def gerar_pdf_relatorio(mes, ano, mes_nome, pagamentos, despesas):
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    # Cabeçalho
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(ROSE)
    c.rect(0, H-2.5*cm, W, 2.5*cm, fill=1, stroke=0)
    c.setFillColor(BRANCO)
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(W/2, H-1.4*cm, 'NOBRE ELEGANCY NOIVAS')
    c.setFont('Helvetica', 10)
    c.drawCentredString(W/2, H-2.1*cm, f'Relatório Financeiro — {mes_nome} {ano}')

    receita = sum(p.valor for p in pagamentos)
    total_desp = sum(d.valor for d in despesas)
    lucro = receita - total_desp

    y = H - 3.5*cm

    # Cards resumo
    def card(x, yc, titulo, valor, cor):
        c.setFillColor(DARK2)
        c.roundRect(x, yc-1.2*cm, 5.5*cm, 1.5*cm, 6, fill=1, stroke=0)
        c.setFillColor(cor)
        c.rect(x, yc+0.3*cm, 5.5*cm, 3, fill=1, stroke=0)
        c.setFillColor(CINZA)
        c.setFont('Helvetica', 7)
        c.drawString(x+0.3*cm, yc+0.05*cm, titulo)
        c.setFillColor(cor)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(x+0.3*cm, yc-0.7*cm, f'R$ {valor:,.2f}'.replace(',','X').replace('.',',').replace('X','.'))

    card(1*cm, y, 'RECEITA', receita, ROSE)
    card(7*cm, y, 'DESPESAS', total_desp, colors.HexColor('#f87171'))
    card(13*cm, y, 'LUCRO LÍQUIDO', lucro, GOLD if lucro >= 0 else colors.HexColor('#f87171'))
    y -= 2*cm

    # Por forma
    c.setFillColor(ROSE)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(1*cm, y, 'RECEITA POR FORMA DE PAGAMENTO')
    y -= 0.5*cm
    por_forma = {}
    for p in pagamentos:
        por_forma[p.forma] = por_forma.get(p.forma, 0) + p.valor
    for forma, val in por_forma.items():
        c.setFillColor(CINZA)
        c.setFont('Helvetica', 8)
        c.drawString(1.5*cm, y, forma.replace('_', ' ').title())
        c.setFillColor(GOLD)
        c.setFont('Helvetica-Bold', 8)
        c.drawRightString(W-1*cm, y, f'R$ {val:,.2f}'.replace(',','X').replace('.',',').replace('X','.'))
        y -= 0.45*cm
    y -= 0.3*cm

    # Pagamentos
    if pagamentos:
        c.setFillColor(ROSE)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(1*cm, y, 'PAGAMENTOS DO MÊS')
        y -= 0.5*cm
        c.setFillColor(DARK2)
        c.rect(1*cm, y-0.3*cm, W-2*cm, 0.45*cm, fill=1, stroke=0)
        c.setFillColor(CINZA)
        c.setFont('Helvetica-Bold', 7)
        c.drawString(1.3*cm, y-0.1*cm, 'DATA')
        c.drawString(4*cm, y-0.1*cm, 'CLIENTE')
        c.drawString(11*cm, y-0.1*cm, 'FORMA')
        c.drawString(14*cm, y-0.1*cm, 'TIPO')
        c.drawRightString(W-1*cm, y-0.1*cm, 'VALOR')
        y -= 0.6*cm
        for p in pagamentos:
            if y < 2*cm:
                c.showPage()
                c.setFillColor(DARK)
                c.rect(0, 0, W, H, fill=1, stroke=0)
                y = H - 1.5*cm
            c.setFillColor(BRANCO)
            c.setFont('Helvetica', 7)
            c.drawString(1.3*cm, y, p.data.strftime('%d/%m/%Y'))
            nome = p.contrato.cliente.nome[:28] if p.contrato else '—'
            c.drawString(4*cm, y, nome)
            c.drawString(11*cm, y, p.forma.replace('_',' ').title())
            c.drawString(14*cm, y, p.tipo.title())
            c.setFillColor(ROSE)
            c.setFont('Helvetica-Bold', 7)
            c.drawRightString(W-1*cm, y, f'R$ {p.valor:,.2f}'.replace(',','X').replace('.',',').replace('X','.'))
            y -= 0.42*cm

    # Rodapé
    c.setFillColor(ROSE)
    c.rect(0, 0, W, 1*cm, fill=1, stroke=0)
    c.setFillColor(BRANCO)
    c.setFont('Helvetica', 7)
    c.drawCentredString(W/2, 0.35*cm, f'Nobre Elegancy Noivas — Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}')

    c.save()
    return buf.getvalue()
