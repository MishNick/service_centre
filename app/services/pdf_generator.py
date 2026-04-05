import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Пытаемся найти шрифт с поддержкой кириллицы
FONT_NAME = 'Helvetica'  # Запасной вариант
font_paths = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/times.ttf"
]

for path in font_paths:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont('CustomFont', path))
            FONT_NAME = 'CustomFont'
            print(f"✅ Шрифт загружен: {path}")
            break
        except Exception as e:
            print(f"⚠️ Не удалось загрузить шрифт {path}: {e}")


def generate_act_pdf(task, client, engineer):
    """
    Генерирует PDF акта выполненных работ
    """
    # Создаём папку для PDF
    os.makedirs('generated_acts', exist_ok=True)

    # Имя файла
    pdf_filename = f"act_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join('generated_acts', pdf_filename)

    # Создаём документ
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm)

    # Стили
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName=FONT_NAME
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_LEFT,
        spaceAfter=10,
        fontName=FONT_NAME
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=6,
        fontName=FONT_NAME
    )

    # Собираем содержимое
    story = []

    # Заголовок
    story.append(Paragraph(f"АКТ ВЫПОЛНЕННЫХ РАБОТ №{task.id}/{datetime.now().year}", title_style))
    story.append(Paragraph(f"от {datetime.now().strftime('%d.%m.%Y')}", normal_style))
    story.append(Spacer(1, 20))

    # Клиент
    story.append(Paragraph("Информация о клиенте:", heading_style))
    story.append(Paragraph(f"<b>Название:</b> {client.name}", normal_style))
    if client.phone:
        story.append(Paragraph(f"<b>Телефон:</b> {client.phone}", normal_style))
    if client.address:
        story.append(Paragraph(f"<b>Адрес:</b> {client.address}", normal_style))
    story.append(Spacer(1, 15))

    # Оборудование
    story.append(Paragraph("Оборудование:", heading_style))
    story.append(Paragraph(f"<b>Тип:</b> {task.equipment_type}", normal_style))
    if task.equipment_model:
        story.append(Paragraph(f"<b>Модель:</b> {task.equipment_model}", normal_style))
    if task.serial_number:
        story.append(Paragraph(f"<b>Серийный номер:</b> {task.serial_number}", normal_style))
    story.append(Spacer(1, 15))

    # Инженер
    story.append(Paragraph("Инженер:", heading_style))
    story.append(Paragraph(f"{engineer.name if engineer else 'Не назначен'}", normal_style))
    story.append(Spacer(1, 15))

    # Описание работ
    story.append(Paragraph("Выполненные работы:", heading_style))
    story.append(Paragraph(task.description, normal_style))
    story.append(Spacer(1, 20))

    # Таблица
    data = [
        ["№", "Наименование работ", "Кол-во", "Стоимость"],
        ["1", task.description[:50] + ("..." if len(task.description) > 50 else ""), "1", "Договорная"]
    ]

    table = Table(data, colWidths=[30, 280, 50, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))

    story.append(table)
    story.append(Spacer(1, 30))

    # Итого
    story.append(Paragraph("<b>ИТОГО к оплате:</b> Договорная", normal_style))
    story.append(Spacer(1, 40))

    # Подписи
    signatures_data = [
        ["Мастер:", "Клиент:"],
        [engineer.name if engineer else "_______________", "_______________"],
    ]

    signatures_table = Table(signatures_data, colWidths=[200, 200])
    signatures_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('TOPPADDING', (0, 1), (-1, 1), 20),
    ]))

    story.append(signatures_table)
    story.append(Spacer(1, 20))

    # Футер
    story.append(Paragraph("Акт сформирован автоматически в системе Service Center",
                           ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER,
                                          fontName=FONT_NAME)))

    # Создаём PDF
    doc.build(story)

    print(f"✅ PDF создан: {pdf_path}")
    return pdf_path, pdf_filename