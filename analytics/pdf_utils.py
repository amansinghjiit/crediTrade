from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from io import BytesIO

def generate_pdf(transactions, opening_balance, closing_balance, total_debit, total_credit, username, whatsapp_number, start_date, end_date, orders, buffer):
    pdf_title = f"{username}_statement"
    pdf = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=1 * inch, bottomMargin=0.75 * inch, title=pdf_title)
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        name='HeaderStyle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor("#A5B4FC"),
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,
        spaceAfter=12,
        textColor=colors.HexColor("#94A3B8"),
        fontName='Helvetica'
    )
    
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#D1D5DB"),
        fontName='Helvetica'
    )
    
    footer_style = ParagraphStyle(
        name='FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
        fontName='Helvetica',
        alignment=1
    )
    
    table_width = 7.8 * inch
    transaction_col_widths = [1.2 * inch, 3.3 * inch, 1 * inch, 1 * inch, 1.3 * inch]
    orders_col_widths = [1.2 * inch, 1.4 * inch, 3.1 * inch, 0.8 * inch, 1.3 * inch]
    
    elements = []
    
    elements.append(Paragraph("Transaction History", header_style))
    
    if start_date or end_date:
        formatted_start_date = start_date.strftime("%d %B %Y") if start_date else ""
        formatted_end_date = end_date.strftime("%d %B %Y") if end_date else ""
        if start_date == end_date and start_date is not None:
            date_range_text = formatted_start_date
        else:
            date_range_text = f"{formatted_start_date} – {formatted_end_date}".strip(" – ")
        elements.append(Paragraph(date_range_text, subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    user_info_table = Table([
        [Paragraph(f"User: <b>{username}</b>", normal_style), 
         Paragraph(f"Whatsapp: <b>{whatsapp_number}</b>", ParagraphStyle(name='RightAlign', parent=normal_style, alignment=2))],
        [Paragraph(f"Opening Balance: <b>{int(opening_balance):,}</b>", normal_style),
         Paragraph(f"Closing Balance: <b>{int(closing_balance):,}</b>", ParagraphStyle(name='RightAlign', parent=normal_style, alignment=2))]
    ], colWidths=[3.9 * inch, 3.9 * inch], style=[
        ('ALIGN', (0, 0), (0, 1), 'LEFT'),
        ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ])
    elements.append(user_info_table)
    elements.append(Spacer(1, 0.15 * inch))
    
    data = [["Date", "Description", "Credit", "Debit", "Balance"]]
    if transactions:
        for transaction in transactions:
            credit = f"{int(transaction.amount):,}" if transaction.transaction_type == "credit" else ""
            debit = f"{int(transaction.amount):,}" if transaction.transaction_type == "debit" else ""
            balance = f"{int(transaction.balance):,}"
            data.append([transaction.date.strftime("%d %b %Y"), transaction.description[:50], credit, debit, balance])
    else:
        data.append(["No transactions", "", "", "", ""])
    
    data.append(["Total", "", f"{int(total_credit):,}", f"{int(total_debit):,}", f"{int(closing_balance):,}"])
    
    table = Table(data, colWidths=transaction_col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#A5B4FC")),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#111827")),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor("#D1D5DB")),
        ('GRID', (0, 1), (-1, -1), 0.3, colors.HexColor("#4B5563")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#FFFFFF")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.HexColor("#34D399")),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor("#F87171")),
        ('TEXTCOLOR', (4, 1), (4, -1), colors.HexColor("#60A5FA")),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#4B5563")),
        ('INNERGRID', (0, 1), (-1, -1), 0.2, colors.HexColor("#4B5563")),
    ]))
    elements.append(table)
    
    elements.append(PageBreak())
    
    elements.append(Paragraph("Orders History", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    orders_data = [["Date", "Name", "Model", "Return", "Pin"]]
    if orders:
        total_return = 0
        for order in orders:
            return_amount = int(order.return_amount) if order.return_amount else 0
            total_return += return_amount
            orders_data.append([
                order.date.strftime("%d %b %Y"),
                order.name[:15],
                order.model[:40],
                f"{return_amount:,}",
                order.pin
            ])
        orders_data.append(["Total", "", "", f"{total_return:,}", ""])
    else:
        orders_data.append(["No orders", "", "", "", ""])
    
    orders_table = Table(orders_data, colWidths=orders_col_widths)
    orders_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#A5B4FC")),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (2, -1), 'LEFT'),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#111827")),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor("#D1D5DB")),
        ('GRID', (0, 1), (-1, -1), 0.3, colors.HexColor("#4B5563")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#FFFFFF")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor("#34D399")),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#4B5563")),
        ('INNERGRID', (0, 1), (-1, -1), 0.2, colors.HexColor("#4B5563")),
    ]))
    elements.append(orders_table)
    
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("www.creditrade.in", footer_style))
    
    def add_page_decorations(canvas, doc):
        canvas.saveState()
        canvas.linearGradient(0, 10.25 * inch, 8.5 * inch, 10 * inch, 
                             [colors.HexColor("#1E293B"), colors.HexColor("#111827")], 
                             positions=[0, 1])
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        page_num = canvas.getPageNumber()
        canvas.circle(4.25 * inch, 0.55 * inch, 0.2 * inch, fill=0, stroke=1)
        canvas.drawCentredString(4.25 * inch, 0.5 * inch, f"{page_num}")
        canvas.restoreState()
    
    pdf.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    buffer.seek(0)
    return buffer