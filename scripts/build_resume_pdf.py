from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "druzhinskaya-ekaterina-resume.pdf"


FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def register_fonts() -> tuple[str, str]:
    regular = "ArialUnicode"
    bold = "ArialBold"
    pdfmetrics.registerFont(TTFont(regular, FONT_REGULAR))
    pdfmetrics.registerFont(TTFont(bold, FONT_BOLD))
    return regular, bold


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullet(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(f"- {text}", style)


def build() -> None:
    regular, bold = register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName=regular,
        fontSize=8.6,
        leading=11,
        textColor=colors.HexColor("#19211F"),
        spaceAfter=3,
    )
    small = ParagraphStyle("Small", parent=base, fontSize=7.8, leading=9.6, textColor=colors.HexColor("#4E5A55"))
    h1 = ParagraphStyle("H1", parent=base, fontName=bold, fontSize=19, leading=22, spaceAfter=2)
    h2 = ParagraphStyle(
        "H2",
        parent=base,
        fontName=bold,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#07534E"),
        spaceBefore=6,
        spaceAfter=4,
    )
    role = ParagraphStyle("Role", parent=base, fontName=bold, fontSize=10, leading=12, textColor=colors.HexColor("#0C776F"))
    label = ParagraphStyle("Label", parent=small, fontName=bold, textColor=colors.HexColor("#07534E"))
    center = ParagraphStyle("Center", parent=small, alignment=TA_CENTER)
    link = ParagraphStyle("Link", parent=small, textColor=colors.HexColor("#0C776F"))
    cell = ParagraphStyle("Cell", parent=small, alignment=TA_LEFT)

    story = []

    header = Table(
        [
            [
                p("Екатерина Дружинская", h1),
                p(
                    "GitHub: <link href='https://github.com/comfe2436-web'>github.com/comfe2436-web</link><br/>"
                    "Портфолио: <link href='https://comfe2436-web.github.io/'>https://comfe2436-web.github.io/</link><br/>"
                    "LinkedIn: <link href='https://www.linkedin.com/in/ekaterinadruzhinskaia/'>linkedin.com/in/ekaterinadruzhinskaia</link><br/>"
                    "Email: <link href='mailto:comfe2436@gmail.com'>comfe2436@gmail.com</link><br/>"
                    "Telegram: <link href='https://t.me/dru_zh'>@dru_zh</link> · Телефон: +7 985 110 01 75",
                    link,
                ),
            ]
        ],
        colWidths=[94 * mm, 83 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(header)
    story.append(p("Аналитик данных, процессов и отчетности", role))
    story.append(
        p(
            "1C · Excel · SQL · Python · BPMN · BI · требования · контроль качества данных",
            small,
        )
    )
    story.append(
        p(
            "Работаю на стыке отчетности, 1C, бизнес-процессов и управленческой аналитики: "
            "структурирую данные, описываю требования, проверяю качество выгрузок и собираю "
            "понятные артефакты для бизнеса и команды разработки.",
            base,
        )
    )

    metrics = Table(
        [
            [
                p("<b>326 записей</b><br/>проверено в кейсе качества данных 1C, выявлено 24 события ошибок", center),
                p("<b>5 таблиц SQL</b><br/>модель продаж, KPI по 1 660 заказам и BI-прототип", center),
                p("<b>BPMN + RTM + ТЗ</b><br/>пакет требований для автоматизации процесса в 1C", center),
            ]
        ],
        colWidths=[59 * mm, 59 * mm, 59 * mm],
    )
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F7F5")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C8DAD5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8DAD5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Spacer(1, 4))
    story.append(metrics)

    three_cols = Table(
        [
            [
                p("<b>Сильные стороны</b><br/>Бизнес-анализ, требования, BPMN, AS-IS/TO-BE, RTM, описание процессов, работа с пользователями.", cell),
                p("<b>Инструменты</b><br/>Excel, сводные таблицы, формулы, 1C-выгрузки, SQL, Python/pandas, BI-прототипы, документация.", cell),
                p("<b>Формат</b><br/>Удаленно / гибрид. Готова к командировкам.", cell),
            ]
        ],
        colWidths=[59 * mm, 59 * mm, 59 * mm],
    )
    three_cols.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDD7CA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDD7CA")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFDF8")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(Spacer(1, 5))
    story.append(three_cols)

    story.append(p("Опыт", h2))
    story.append(bullet("<b>Дек 2025 - апр 2026 · Ведущий аналитик, ГАУ ИТЦ \"Соцзащита\" Москвы.</b> Сбор, обработка и структурирование данных, подготовка отчетов и визуализаций, автоматизация отчетности в Excel, работа с данными в 1C и контроль качества данных.", base))
    story.append(bullet("<b>Янв 2022 - фев 2026 · Администратор, ИП Дружинская.</b> Работа с большим объемом документов и данных, оцифровка и структурирование информации, актуализация баз данных, контроль корректности данных, отчеты и сводные таблицы.", base))
    story.append(bullet("<b>Май 2024 - окт 2024 · Трансферный гид, Fit Holidays.</b> Координация логистики, анализ обратной связи клиентов, выявление повторяющихся проблем и подготовка предложений по улучшению качества сервиса.", base))

    story.append(p("Портфолио проектов", h2))
    projects = [
        ["1C / Excel", "Контроль качества выгрузок из 1C: дубли, пропуски, связи между таблицами, некорректные суммы, статусы и даты. Итог: Excel-отчет, реестр ошибок и план исправлений."],
        ["BPMN / 1C", "Автоматизация обработки заявок: AS-IS, TO-BE, требования, RTM, макет формы, ТЗ, критерии приемки и тестовые сценарии."],
        ["Python / BI", "Аналитика продаж и обратной связи: очистка данных, NPS, операционные метрики, гипотезы, проблемные категории и рекомендации."],
        ["SQL / BI", "SQL-анализ продаж и BI-дашборд: модель данных, SQLite, JOIN, CTE, KPI по выручке, маржинальности и дебиторской задолженности."],
    ]
    project_table = Table(
        [[p(f"<b>{name}</b>", label), p(text, small)] for name, text in projects],
        colWidths=[25 * mm, 152 * mm],
    )
    project_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(project_table)

    story.append(p("Образование", h2))
    story.append(
        p(
            "МФЮА - магистратура по юриспруденции, правовое обеспечение бизнеса, 2025-2028. "
            "РЭУ им. Г.В. Плеханова - бакалавриат по менеджменту, управление гостиничным и туристическим бизнесом, 2021-2025. "
            "Курс: разработка алгоритмов и программных приложений.",
            base,
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=12 * mm,
        title="Резюме Екатерины Дружинской",
        author="Екатерина Дружинская",
    )
    doc.build(story)


if __name__ == "__main__":
    build()
