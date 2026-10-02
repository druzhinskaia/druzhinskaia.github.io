"""Build the public, one-page resume. Requires reportlab and Cyrillic fonts.

Use RESUME_FONT_DIR for a directory containing DejaVuSans.ttf and
DejaVuSans-Bold.ttf when neither of the platform defaults is available.
"""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "druzhinskaya-ekaterina-resume.pdf"
OUT_EN = ROOT / "output" / "pdf" / "druzhinskaya-ekaterina-resume-en.pdf"
EN = {
    "Екатерина Дружинская": "Ekaterina Druzhinskaia",
    "Аналитик данных и автоматизации": "Data and Automation Analyst",
    "Удалённая работа, готова к командировкам": "Remote work · Available for business travel",
    "Автоматизирую отчётность и проверки данных в Excel и 1С. Описываю требования, тестирую решения, готовлю инструкции и обучаю пользователей.":
        "I automate reporting and validation of data in Excel and 1C. I document requirements, test solutions, prepare user guides and train users.",
    "КОМПЕТЕНЦИИ": "SKILLS",
    "ОПЫТ РАБОТЫ": "EXPERIENCE",
    "ПРОЕКТЫ": "PROJECTS",
    "ОБРАЗОВАНИЕ": "EDUCATION",
    "Инструменты": "Tools",
    "Базовый уровень": "Basic proficiency",
    "Методы": "Methods",
    "Анализ процессов · Требования": "Process analysis · Requirements",
    "Старший аналитик по ИИ-автоматизации": "Senior AI Automation Analyst",
    "МИ ФНС России по управлению долгом": "Interregional Inspectorate for Debt Management, Federal Tax Service of Russia",
    "н. в.": "present",
    "Анализирую данные в 1С и информационных системах, сопоставляю выгрузки, выявляю расхождения, готовлю аналитические материалы. Автоматизирую проверки в Excel и применяю ИИ-инструменты для отдельных рабочих задач.":
        "I analyse data in 1C and information systems and reconcile exports, identify discrepancies and prepare analytical reports. I automate checks in Excel and use AI tools for selected work tasks.",
    "Ведущий аналитик": "Lead Analyst",
    "ГАУ ИТЦ «Соцзащита» Москвы": "Moscow Social Protection IT Centre (GAU ITC)",
    "Вела проект автоматизации Excel-отчётности для <b>120-140 организаций</b>: анализировала процесс, обновляла форму, настраивала контроль качества данных и тестировала решение. Подготовила документацию, обучила пользователей и сопровождала внедрение.":
        "Managed an Excel reporting automation project for <b>120-140 organisations</b>: analysed the process, redesigned the reporting form, configured data quality checks and tested the solution. Prepared documentation, trained users and supported implementation.",
    "Администратор": "Administrator",
    "ИП Дружинская": "Druzhinskaia, Sole Proprietor",
    "Вела реестры, документацию и отчётность, проверяла качество данных. Оптимизировала операции в Excel, координировала задачи и договорённости.":
        "Maintained registers, documentation and reports, and checked data quality. Streamlined Excel operations and coordinated tasks and agreements.",
    "Трансферный гид": "Transfer Guide",
    "Координировала логистику, анализировала обратную связь клиентов и повторяющиеся проблемы, готовила предложения по улучшению сервиса.":
        "Coordinated logistics, analysed customer feedback and recurring issues, and proposed service improvements.",
    "Помощник организатора": "Event Assistant",
    "АРСК": "ARSK",
    "Помогала организовывать мероприятия: согласовывала разрешения, вела документооборот и взаимодействовала с командами. ":
        "Supported event organisation: coordinated permits, managed documentation and worked with teams. ",
    "Рекомендательное письмо": "Recommendation letter",
    "Контроль качества: <b>326 записей, 24 события ошибок</b>. Дубли, пропуски, связи, суммы, статусы и даты. Результат: Excel-отчёт, реестр ошибок и план исправлений.":
        "Data quality checks: <b>326 records, 24 error occurrences</b>. Duplicates, missing values, relationships, amounts, statuses and dates. Deliverables: Excel report, error register and remediation plan.",
    "Автоматизация заявок: AS-IS / TO-BE, требования, RTM, макет формы, ТЗ, критерии приёмки и тестовые сценарии.":
        "Request processing automation: AS-IS / TO-BE, requirements, RTM, form mockup, specification, acceptance criteria and test scenarios.",
    "Продажи и обратная связь: очистка данных, NPS, операционные метрики, гипотезы, проблемные категории и рекомендации.":
        "Sales and customer feedback: data cleaning, NPS, operational metrics, hypotheses, problem categories and recommendations.",
    "Модель из <b>5 таблиц, 1 660 заказов</b>: SQLite, JOIN, CTE, BI-прототип с KPI по выручке, маржинальности и дебиторской задолженности.":
        "Model with <b>5 tables and 1,660 orders</b>: SQLite, JOIN, CTE and a BI prototype with revenue, margin and accounts receivable KPIs.",
    "Кейсы основаны на коммерческих задачах. Публикуемые данные и отдельные показатели обезличены и реконструированы для соблюдения конфиденциальности.":
        "Cases are based on commercial tasks. Published data and selected metrics are anonymised and reconstructed to protect confidentiality.",
    "Магистратура · Бизнес-информатика": "Master's degree · Business Informatics",
    "Профиль: Информационная бизнес-аналитика": "Specialisation: Information Business Analytics",
    "Московский финансово-юридический университет МФЮА, Москва": "Moscow University of Finance and Law (MFUA), Moscow",
    "Бакалавриат · Менеджмент": "Bachelor's degree · Management",
    "Профиль: Управление гостиничным и туристическим бизнесом": "Specialisation: Hospitality and Tourism Business Management",
    "РЭУ им. Г. В. Плеханова": "Plekhanov Russian University of Economics",
    "<b>Курс:</b> разработка алгоритмов и программных приложений.": "<b>Course:</b> Algorithm and Application Development.",
    "<b>Сертификат, 2026:</b> «Кадровый учёт в УАИС „Бюджетный учёт“. 1С». Роль: кадровик. Срок действия: 3 года.":
        "<b>Certificate, 2026:</b> Personnel Records in UAIS Budget Accounting (1C). Role: HR clerk. Valid for 3 years.",
    "1С:БГУ": "1C:BGU",
    "1С / Excel": "1C / Excel",
    "BPMN / 1С": "BPMN / 1C",
}
INK = colors.HexColor("#222C31")
GREEN = colors.HexColor("#24594F")
MUTED = colors.HexColor("#626D72")
LINE = colors.HexColor("#DCE2E0")
PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
# SimpleDocTemplate's content frame adds 6 pt of padding on each side.
WIDTH = PAGE_W - 2 * MARGIN - 12


def register_fonts():
    pairs = []
    if os.getenv("RESUME_FONT_DIR"):
        d = Path(os.environ["RESUME_FONT_DIR"])
        pairs.append((d / "DejaVuSans.ttf", d / "DejaVuSans-Bold.ttf"))
    pairs.extend([
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
         Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
         Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")),
    ])
    for regular, bold in pairs:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Resume", str(regular)))
            pdfmetrics.registerFont(TTFont("ResumeBold", str(bold)))
            pdfmetrics.registerFontFamily("Resume", normal="Resume", bold="ResumeBold")
            return
    raise FileNotFoundError("Install DejaVu Sans or set RESUME_FONT_DIR; see module docstring.")


def build(language="ru"):
    if language not in ("ru", "en"):
        raise ValueError("Supported resume languages: ru, en")
    register_fonts()
    output = OUT_EN if language == "en" else OUT
    output.parent.mkdir(parents=True, exist_ok=True)
    base = ParagraphStyle("Body", fontName="Resume", fontSize=8.6,
                          leading=11.4, textColor=INK)
    small = ParagraphStyle("Small", parent=base, fontSize=7.8, leading=10.5,
                           textColor=MUTED)
    date = ParagraphStyle("Date", parent=small, alignment=TA_RIGHT)
    title = ParagraphStyle("Name", parent=base, fontName="ResumeBold",
                           fontSize=23, leading=27)
    role = ParagraphStyle("Role", parent=base, fontSize=12, leading=16,
                          textColor=GREEN)
    section_style = ParagraphStyle("Section", parent=base, fontName="ResumeBold",
                                   fontSize=9.3, leading=12, textColor=GREEN, keepWithNext=True)
    heading = ParagraphStyle("Heading", parent=base, fontName="ResumeBold",
                             fontSize=9, leading=12)
    note = ParagraphStyle("Note", parent=small, fontSize=7.3, leading=9.6)
    story = []

    def translate(text):
        if language == "ru":
            return text
        if text in EN:
            return EN[text]
        for original in sorted(EN, key=len, reverse=True):
            text = text.replace(original, EN[original])
        if any("А" <= char <= "я" or char in "Ёё" for char in text):
            raise ValueError("Missing English resume translation: " + text)
        return text

    def p(text, style=base):
        return Paragraph(translate(text), style)

    def row(left, right, left_style=heading, right_style=date, right_width=105):
        table = Table([[p(left, left_style), p(right, right_style)]],
                      colWidths=[WIDTH-right_width, right_width])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return table

    def section(label):
        story.extend([Spacer(1, 7), p(label.upper(), section_style),
                      Spacer(1, 3), HRFlowable(width="100%", thickness=.55, color=LINE),
                      Spacer(1, 5)])

    def job(position, employer, dates, description, compact=False):
        if compact:
            story.append(KeepTogether([
                row(position + " · " + employer, dates),
                Spacer(1, 2), p(description), Spacer(1, 5),
            ]))
            return
        story.append(KeepTogether([
            row(position, dates), p(employer, small), Spacer(1, 3),
            p(description), Spacer(1, 5),
        ]))

    story += [p("Екатерина Дружинская", title), Spacer(1, 3),
              p("Аналитик данных и автоматизации", role), Spacer(1, 6)]
    story.append(p(
        '<link href="mailto:comfe2436@gmail.com" color="#24594F">comfe2436@gmail.com</link>'
        '   ·   <link href="tel:+79851100175" color="#24594F">+7 985 110 01 75</link>'
        '   ·   <link href="https://t.me/dru_zh" color="#24594F">Telegram @dru_zh</link>', small))
    story.append(p(
        '<link href="https://druzhinskaia.github.io/" color="#24594F">druzhinskaia.github.io</link>'
        '   ·   <link href="https://github.com/druzhinskaia" color="#24594F">GitHub</link>'
        '   ·   <link href="https://www.linkedin.com/in/ekaterinadruzhinskaia/" color="#24594F">LinkedIn</link>'
        '   ·   Удалённая работа, готова к командировкам', small))
    story.extend([Spacer(1, 8), p(
        "Автоматизирую отчётность и проверки данных в Excel и 1С. "
        "Описываю требования, тестирую решения, готовлю инструкции и обучаю пользователей.")])

    section("Компетенции")
    story.append(p("<b>Инструменты</b>   Excel · Power Query · VBA · 1С:БГУ"))
    story.append(p("<b>Базовый уровень</b>   SQL · Python / pandas · Power BI"))
    story.append(p("<b>Методы</b>   Анализ процессов · Требования · BPMN · AS-IS / TO-BE · RTM"))

    section("Опыт работы")
    job("Старший аналитик по ИИ-автоматизации", "МИ ФНС России по управлению долгом",
        "09.2026 - н. в.",
        "Анализирую данные в 1С и информационных системах, сопоставляю выгрузки, выявляю расхождения, "
        "готовлю аналитические материалы. Автоматизирую проверки в Excel и применяю "
        "ИИ-инструменты для отдельных рабочих задач.")
    job("Ведущий аналитик", 'ГАУ ИТЦ «Соцзащита» Москвы', "12.2025 - 04.2026",
        "Вела проект автоматизации Excel-отчётности для <b>120-140 организаций</b>: "
        "анализировала процесс, обновляла форму, настраивала контроль качества данных и тестировала "
        "решение. Подготовила документацию, обучила пользователей и сопровождала внедрение.")
    job("Администратор", "ИП Дружинская", "01.2022 - 02.2026",
        "Вела реестры, документацию и отчётность, проверяла качество данных. "
        "Оптимизировала операции в Excel, координировала задачи и договорённости.", compact=True)
    job("Трансферный гид", "Fit Holidays", "05.2024 - 11.2024",
        "Координировала логистику, анализировала обратную связь клиентов и повторяющиеся "
        "проблемы, готовила предложения по улучшению сервиса.", compact=True)
    job("Помощник организатора", "АРСК", "09.2022 - 10.2022",
        "Помогала организовывать мероприятия: согласовывала разрешения, вела документооборот "
        "и взаимодействовала с командами. "
        '<link href="https://druzhinskaia.github.io/recommendations/recommendation-arsk-2022.pdf" '
        'color="#24594F">Рекомендательное письмо</link>.', compact=True)

    section("Проекты")
    projects = [
        ("1С / Excel", "Контроль качества: <b>326 записей, 24 события ошибок</b>. "
         "Дубли, пропуски, связи, суммы, статусы и даты. Результат: Excel-отчёт, реестр ошибок и план исправлений."),
        ("BPMN / 1С", "Автоматизация заявок: AS-IS / TO-BE, требования, RTM, макет формы, "
         "ТЗ, критерии приёмки и тестовые сценарии."),
        ("Python / BI", "Продажи и обратная связь: очистка данных, NPS, операционные метрики, "
         "гипотезы, проблемные категории и рекомендации."),
        ("SQL / BI", "Модель из <b>5 таблиц, 1 660 заказов</b>: SQLite, JOIN, CTE, "
         "BI-прототип с KPI по выручке, маржинальности и дебиторской задолженности."),
    ]
    project_rows = [[p(label, heading), p(description, small)] for label, description in projects]
    table = Table(project_rows, colWidths=[77, WIDTH-77])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(p("Кейсы основаны на коммерческих задачах. Публикуемые данные и отдельные "
                   "показатели обезличены и реконструированы для соблюдения конфиденциальности.", note))

    section("Образование")
    story.append(KeepTogether([
        row("Магистратура · Бизнес-информатика", "2025 - 2028"),
        p("Профиль: Информационная бизнес-аналитика"),
        p("Московский финансово-юридический университет МФЮА, Москва", small),
        Spacer(1, 6),
        row("Бакалавриат · Менеджмент", "2021 - 2025"),
        p("Профиль: Управление гостиничным и туристическим бизнесом"),
        p("РЭУ им. Г. В. Плеханова", small),
        Spacer(1, 6),
        p("<b>Курс:</b> разработка алгоритмов и программных приложений.", small),
        p("<b>Сертификат, 2026:</b> «Кадровый учёт в УАИС „Бюджетный учёт“. 1С». "
          "Роль: кадровик. Срок действия: 3 года.", small),
    ]))

    doc = SimpleDocTemplate(str(output), pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN, topMargin=13*mm, bottomMargin=12*mm,
        title=translate("Екатерина Дружинская") + " | " + translate("Аналитик данных и автоматизации"),
        author=translate("Екатерина Дружинская"), pageCompression=1)
    doc.build(story)


if __name__ == "__main__":
    build("ru")
    build("en")

