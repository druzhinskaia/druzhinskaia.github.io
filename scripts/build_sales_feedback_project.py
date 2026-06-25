from __future__ import annotations

import csv
import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
PROJECT = ROOT / "portfolio-projects" / "03-sales-feedback-python-analytics"
RAW = PROJECT / "data" / "raw" / "sales_feedback_raw.csv"
PROCESSED = PROJECT / "data" / "processed" / "sales_feedback_clean.csv"
NOTEBOOK = PROJECT / "notebooks" / "sales_feedback_analysis.ipynb"
DOCS = PROJECT / "docs"
CONTEXT = PROJECT / "01-business-context"
RESULT = PROJECT / "result"
SCREENSHOTS = PROJECT / "screenshots"

random.seed(42)


PRODUCTS = {
    "Компрессор А-120": {"category": "Компрессоры", "base_price": 145000, "margin": 0.28, "issue_bias": ["срок поставки", "цена"]},
    "Насос Н-45": {"category": "Насосы", "base_price": 72000, "margin": 0.24, "issue_bias": ["качество консультации", "комплектация"]},
    "Датчик D-17": {"category": "Датчики", "base_price": 18500, "margin": 0.36, "issue_bias": ["неполное описание", "совместимость"]},
    "Редуктор R-8": {"category": "Редукторы", "base_price": 91000, "margin": 0.22, "issue_bias": ["срок поставки", "документы"]},
    "Фильтр F-30": {"category": "Фильтры", "base_price": 26000, "margin": 0.31, "issue_bias": ["комплектация", "доставка"]},
    "Электродвигатель E-55": {"category": "Электродвигатели", "base_price": 118000, "margin": 0.26, "issue_bias": ["срок поставки", "документы"]},
    "Контроллер C-9": {"category": "Контроллеры", "base_price": 64000, "margin": 0.34, "issue_bias": ["совместимость", "неполное описание"]},
    "Клапан V-12": {"category": "Клапаны", "base_price": 38000, "margin": 0.29, "issue_bias": ["комплектация", "доставка"]},
}

REGIONS = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"]
CHANNELS = ["сайт", "почта", "телефон", "повторная продажа"]
ISSUES = ["нет проблемы", "срок поставки", "цена", "качество консультации", "комплектация", "документы", "доставка", "совместимость", "неполное описание"]
MANAGERS = [
    "Иванова А.А.",
    "Петров М.С.",
    "Сидорова Н.К.",
    "Ким В.В.",
    "Орлова Е.И.",
    "Морозов Д.А.",
    "Волкова Н.П.",
    "Смирнов Р.О.",
    "Егорова Т.С.",
    "Кузнецов И.В.",
    "Федорова М.А.",
    "Новиков П.К.",
    "Алексеева Ю.С.",
    "Громов А.Н.",
    "Зайцева В.Л.",
]
CUSTOMERS = [f"C{idx:05d}" for idx in range(1, 2101)]


def weighted_choice(items: list[str], weights: list[float]) -> str:
    return random.choices(items, weights=weights, k=1)[0]


def generate_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = date(2026, 1, 1)
    order_id = 10001

    for day_offset in range(181):
        current_date = start + timedelta(days=day_offset)
        if current_date.weekday() >= 5:
            continue

        daily_orders = random.randint(32, 46)
        for _ in range(daily_orders):
            product = weighted_choice(list(PRODUCTS), [0.19, 0.15, 0.11, 0.15, 0.1, 0.12, 0.09, 0.09])
            params = PRODUCTS[product]
            channel = weighted_choice(CHANNELS, [0.34, 0.26, 0.2, 0.2])
            region = weighted_choice(REGIONS, [0.34, 0.18, 0.16, 0.17, 0.15])
            quantity = weighted_choice([1, 2, 3, 4], [0.56, 0.25, 0.14, 0.05])
            discount = round(random.choice([0, 0.03, 0.05, 0.07, 0.1]), 2)
            price_noise = random.uniform(0.92, 1.08)
            revenue = int(params["base_price"] * quantity * price_noise * (1 - discount))
            cost = int(revenue * (1 - params["margin"] + random.uniform(-0.025, 0.025)))

            issue_probability = 0.23
            if product in {"Редуктор R-8", "Компрессор А-120"}:
                issue_probability += 0.12
            if channel == "почта":
                issue_probability += 0.06

            has_issue = random.random() < issue_probability
            if has_issue:
                issue_options = params["issue_bias"] + ISSUES[1:]
                issue_weights = [0.24, 0.2] + [0.08] * len(ISSUES[1:])
                issue = weighted_choice(issue_options, issue_weights)
                rating = max(1, min(5, int(round(random.gauss(3.2, 0.9)))))
            else:
                issue = "нет проблемы"
                rating = max(3, min(5, int(round(random.gauss(4.6, 0.45)))))

            response_hours = max(1, int(random.gauss(10, 4)))
            if channel == "почта":
                response_hours += random.randint(4, 12)
            if has_issue:
                response_hours += random.randint(3, 18)

            returned = has_issue and random.random() < 0.14
            rows.append(
                {
                    "order_id": order_id,
                    "order_date": current_date.isoformat(),
                    "customer_id": random.choice(CUSTOMERS),
                    "region": region,
                    "channel": channel,
                    "manager": random.choice(MANAGERS),
                    "category": params["category"],
                    "product": product,
                    "quantity": quantity,
                    "discount": discount,
                    "revenue": revenue,
                    "cost": cost,
                    "rating": rating,
                    "feedback_reason": issue,
                    "response_time_hours": response_hours,
                    "is_return": int(returned),
                }
            )
            order_id += 1

    return rows


def write_raw(rows: list[dict[str, object]]) -> None:
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def clean_data() -> pd.DataFrame:
    df = pd.read_csv(RAW, parse_dates=["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["profit"] = df["revenue"] - df["cost"]
    df["margin_pct"] = (df["profit"] / df["revenue"]).round(3)
    df["has_problem"] = df["feedback_reason"].ne("нет проблемы")
    df["rating_group"] = pd.cut(df["rating"], bins=[0, 3, 4, 5], labels=["низкая", "средняя", "высокая"], include_lowest=True)
    df["nps_group"] = df["rating"].map(lambda value: "promoter" if value == 5 else "passive" if value == 4 else "detractor")
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED, index=False)
    return df


def fmt_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def svg_shell(title: str, body: str, width: int = 960, height: int = 540) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    text{{font-family:Inter,Segoe UI,Arial,sans-serif;letter-spacing:0}}
  </style>
  <rect width="{width}" height="{height}" fill="#F8FAFC"/>
  <rect x="24" y="20" width="{width - 48}" height="{height - 40}" rx="10" fill="#FFFFFF" stroke="#CBD5E1"/>
  <text x="48" y="62" font-size="24" font-weight="750" fill="#1E3A5F">{title}</text>
  {body}
</svg>
"""


def write_svg(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg_shell(title, body), encoding="utf-8")


def build_line_chart(monthly: pd.DataFrame) -> str:
    x0, y0, width, height = 90, 410, 780, 280
    max_value = monthly["revenue"].max()
    points = []
    labels = []
    for idx, row in monthly.reset_index(drop=True).iterrows():
        x = x0 + idx * (width / max(1, len(monthly) - 1))
        y = y0 - (row["revenue"] / max_value) * height
        points.append((x, y))
        labels.append(f'<text x="{x:.1f}" y="448" text-anchor="middle" font-size="12" fill="#64748B">{row["month"]}</text>')
    path = " ".join(f"{'M' if idx == 0 else 'L'} {x:.1f} {y:.1f}" for idx, (x, y) in enumerate(points))
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#FFFFFF" stroke="#24527A" stroke-width="3"/>'
        f'<text x="{x:.1f}" y="{y - 14:.1f}" text-anchor="middle" font-size="12" fill="#334155">{row["revenue"] / 1_000_000:.1f}</text>'
        for (x, y), (_, row) in zip(points, monthly.iterrows())
    )
    grid = "\n".join(f'<path d="M {x0} {y0 - i * 70} L {x0 + width} {y0 - i * 70}" stroke="#E2E8F0"/>' for i in range(5))
    return f"""
  <text x="48" y="92" font-size="14" fill="#64748B">млн руб.</text>
  {grid}
  <path d="M {x0} 130 L {x0} {y0} L {x0 + width} {y0}" fill="none" stroke="#CBD5E1"/>
  <path d="{path}" fill="none" stroke="#24527A" stroke-width="3.2"/>
  {circles}
  {''.join(labels)}
"""


def build_bar_chart(labels: list[str], values: list[float], color: str, suffix: str = "") -> str:
    x0, y0, max_width, bar_height, gap = 330, 130, 520, 38, 22
    max_value = max(values)
    rows = []
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = y0 + idx * (bar_height + gap)
        bar_width = (value / max_value) * max_width
        rows.append(
            f'<text x="{x0 - 18}" y="{y + 25}" text-anchor="end" font-size="14" fill="#172033">{label}</text>'
            f'<rect x="{x0}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" rx="6" fill="{color}"/>'
            f'<text x="{x0 + bar_width + 12:.1f}" y="{y + 25}" font-size="14" font-weight="650" fill="#334155">{value:.1f}{suffix}</text>'
        )
    return "\n  ".join(rows)


def build_scatter(matrix: pd.DataFrame) -> str:
    x0, y0, width, height = 110, 430, 730, 300
    max_revenue = matrix["revenue"].max()
    max_problem = matrix["problem_share"].max() * 100
    min_margin = matrix["margin"].min() * 100
    max_margin = matrix["margin"].max() * 100
    points = []
    for _, row in matrix.iterrows():
        x = x0 + ((row["problem_share"] * 100) / max_problem) * width
        y = y0 - (((row["margin"] * 100) - min_margin) / (max_margin - min_margin)) * height
        radius = 12 + (row["revenue"] / max_revenue) * 28
        points.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="#2F855A" fill-opacity="0.72" stroke="#1E3A5F" stroke-width="2"/>'
            f'<text x="{x + radius + 8:.1f}" y="{y + 5:.1f}" font-size="12" fill="#172033">{row["product"]}</text>'
        )
    return f"""
  <path d="M {x0} 110 L {x0} {y0} L {x0 + width} {y0}" fill="none" stroke="#CBD5E1"/>
  <text x="{x0 + width / 2}" y="482" text-anchor="middle" font-size="14" fill="#64748B">доля проблемных заказов</text>
  <text x="38" y="275" text-anchor="middle" transform="rotate(-90 38 275)" font-size="14" fill="#64748B">маржинальность</text>
  {"".join(points)}
"""


def build_dashboard(df: pd.DataFrame) -> str:
    revenue = fmt_number(df["revenue"].sum())
    avg_rating = df["rating"].mean()
    problem_share = df["has_problem"].mean()
    avg_response = df["response_time_hours"].mean()
    nps = (df["nps_group"].eq("promoter").mean() - df["nps_group"].eq("detractor").mean()) * 100
    worst_category = df.groupby("category")["has_problem"].mean().sort_values(ascending=False).index[0]

    cards = [
        ("Выручка", f"{revenue} ₽"),
        ("Средняя оценка", f"{avg_rating:.2f} / 5"),
        ("NPS", f"{nps:.0f}"),
        ("Проблемные заказы", f"{problem_share:.1%}"),
        ("Среднее время ответа", f"{avg_response:.0f} ч"),
        ("Зона риска", worst_category),
    ]
    card_svg = []
    for idx, (label, value) in enumerate(cards):
        col = idx % 3
        row = idx // 3
        x = 70 + col * 285
        y = 120 + row * 150
        card_svg.append(
            f'<rect x="{x}" y="{y}" width="245" height="112" rx="10" fill="#FFFFFF" stroke="#CBD5E1"/>'
            f'<text x="{x + 22}" y="{y + 38}" font-size="14" fill="#64748B">{label}</text>'
            f'<text x="{x + 22}" y="{y + 78}" font-size="26" font-weight="750" fill="#1E3A5F">{value}</text>'
        )
    return svg_shell("Executive Dashboard", "\n  ".join(card_svg), width=960, height=460)


def build_charts(df: pd.DataFrame) -> None:

    monthly = df.groupby("month", as_index=False).agg(revenue=("revenue", "sum"), orders=("order_id", "count"))
    write_svg(SCREENSHOTS / "01_revenue_by_month.svg", "Выручка по месяцам", build_line_chart(monthly))

    product_rating = df.groupby("product", as_index=False).agg(avg_rating=("rating", "mean"), problem_share=("has_problem", "mean"))
    product_rating = product_rating.sort_values("avg_rating")
    write_svg(
        SCREENSHOTS / "02_rating_by_product.svg",
        "Средняя оценка по продуктам",
        build_bar_chart(product_rating["product"].tolist(), product_rating["avg_rating"].round(2).tolist(), "#2B6CB0"),
    )

    reasons = df[df["has_problem"]]["feedback_reason"].value_counts().head(7).sort_values()
    write_svg(
        SCREENSHOTS / "03_feedback_reasons.svg",
        "Основные причины негативной обратной связи",
        build_bar_chart(reasons.index.tolist(), [float(v) for v in reasons.values], "#C05621"),
    )

    matrix = df.groupby("product", as_index=False).agg(revenue=("revenue", "sum"), problem_share=("has_problem", "mean"), margin=("margin_pct", "mean"))
    write_svg(SCREENSHOTS / "04_priority_matrix.svg", "Матрица приоритетов: проблемы vs маржинальность", build_scatter(matrix))
    (SCREENSHOTS / "00_executive_dashboard.svg").write_text(build_dashboard(df), encoding="utf-8")


def build_outputs(df: pd.DataFrame) -> None:
    RESULT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    CONTEXT.mkdir(parents=True, exist_ok=True)

    segment = (
        df.groupby(["product"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            avg_rating=("rating", "mean"),
            problem_share=("has_problem", "mean"),
            avg_response_hours=("response_time_hours", "mean"),
            return_share=("is_return", "mean"),
        )
        .sort_values("problem_share", ascending=False)
    )
    segment.to_csv(RESULT / "product_metrics.csv", index=False)

    worst_product = segment.iloc[0]["product"]
    worst_product_issue = df[(df["product"].eq(worst_product)) & df["has_problem"]]["feedback_reason"].value_counts().index[0]
    revenue_priority = (
        segment[segment["product"].ne(worst_product)]
        .sort_values(["revenue", "problem_share"], ascending=False)
        .iloc[0]["product"]
    )
    revenue_priority_issue = df[(df["product"].eq(revenue_priority)) & df["has_problem"]]["feedback_reason"].value_counts().index[0]

    actions = pd.DataFrame(
        [
            {
                "priority": 1,
                "focus": worst_product,
                "problem": f"самая высокая доля проблемных заказов, частая причина - {worst_product_issue}",
                "action": f"разобрать причину '{worst_product_issue}' и добавить контрольный шаг перед передачей заказа клиенту",
            },
            {
                "priority": 2,
                "focus": revenue_priority,
                "problem": f"высокая выручка и повторяющаяся причина обратной связи - {revenue_priority_issue}",
                "action": f"подготовить для менеджеров шаблон ответа по причине '{revenue_priority_issue}' и обновить описание в коммерческом предложении",
            },
            {
                "priority": 3,
                "focus": "Почтовый канал",
                "problem": "самое долгое время ответа",
                "action": "ввести SLA на первый ответ и ежедневный список необработанных писем",
            },
        ]
    )
    actions.to_csv(RESULT / "action_plan.csv", index=False)

    total_revenue = df["revenue"].sum()
    avg_rating = df["rating"].mean()
    problem_share = df["has_problem"].mean()
    nps = (df["nps_group"].eq("promoter").mean() - df["nps_group"].eq("detractor").mean()) * 100
    avg_response = df["response_time_hours"].mean()
    top_issue = Counter(df[df["has_problem"]]["feedback_reason"]).most_common(1)[0][0]
    worst_category = df.groupby("category")["has_problem"].mean().sort_values(ascending=False).index[0]
    slow_response_rating = df[df["response_time_hours"] > 24]["rating"].mean()
    fast_response_rating = df[df["response_time_hours"] <= 12]["rating"].mean()

    (RESULT / "analytics_summary.md").write_text(
        f"""# Аналитическая записка

## Короткий вывод

За период с января по июнь 2026 года в выборке {len(df)} заказов на сумму {fmt_number(total_revenue)} руб. Средняя оценка клиентов составила {avg_rating:.2f} из 5, NPS - {nps:.0f}, доля заказов с проблемной обратной связью - {problem_share:.1%}.

Главная повторяющаяся причина негативной обратной связи - **{top_issue}**. Наиболее рискованный продукт по доле проблемных заказов - **{worst_product}**, категория риска - **{worst_category}**.

## Что видно по данным

- Выручка держится стабильно, но качество клиентского опыта отличается по продуктам.
- Проблемные обращения чаще связаны не с самим фактом продажи, а с ожиданиями клиента: срок, комплектация, документы и пояснение цены.
- При ответе быстрее 12 часов средняя оценка составляет {fast_response_rating:.2f}; при ответе дольше 24 часов - {slow_response_rating:.2f}.
- Продукты с высокой выручкой и высокой долей проблем требуют приоритета, потому что влияют и на деньги, и на повторные продажи.

## Рекомендации

1. Для `{worst_product}` разобрать причину `{worst_product_issue}` и добавить контрольный шаг перед передачей заказа клиенту.
2. Ввести контроль первого ответа по почтовому каналу.
3. Для `{revenue_priority}` подготовить шаблон ответа по причине `{revenue_priority_issue}` и обновить описание в коммерческом предложении.
4. Раз в неделю смотреть матрицу “доля проблем x маржинальность”, чтобы выбирать фокус улучшений.
""",
        encoding="utf-8",
    )

    (DOCS / "data_dictionary.md").write_text(
        """# Описание данных

| Поле | Описание |
|---|---|
| order_id | номер заказа |
| order_date | дата заказа |
| customer_id | идентификатор клиента |
| region | регион клиента |
| channel | канал поступления заказа |
| manager | ответственный менеджер |
| category | категория товара |
| product | продукт |
| quantity | количество |
| discount | скидка |
| revenue | выручка |
| cost | себестоимость |
| rating | оценка клиента от 1 до 5 |
| feedback_reason | причина обратной связи |
| response_time_hours | время первого ответа в часах |
| is_return | признак возврата |
| month | месяц заказа, расчетное поле |
| profit | прибыль по заказу, расчетное поле |
| margin_pct | маржинальность заказа, расчетное поле |
| has_problem | признак проблемной обратной связи |
| rating_group | группа оценки клиента |
| nps_group | группа для расчета NPS: promoter, passive, detractor |

Данные синтетические, но структура приближена к типовой выгрузке продаж и клиентской обратной связи.
""",
        encoding="utf-8",
    )

    (CONTEXT / "business-case.md").write_text(
        """# Бизнес-кейс

ООО "ТехСнаб" регулярно анализирует продажи и клиентскую обратную связь после завершения заказов. В последние два квартала выручка оставалась стабильной, однако количество негативных отзывов выросло, а доля повторных заказов начала снижаться.

Руководитель отдела продаж предполагает, что проблема может быть связана с отдельными категориями товаров, скоростью ответа менеджеров или повторяющимися причинами недовольства клиентов. Аналитику поручено исследовать данные и подготовить рекомендации для повышения качества клиентского сервиса.
""",
        encoding="utf-8",
    )
    (CONTEXT / "project-goals.md").write_text(
        """# Цель исследования

- определить категории товаров с максимальной долей негативной обратной связи;
- найти продукты, где проблемы влияют на выручку и маржинальность;
- выявить связь между временем ответа и удовлетворенностью клиентов;
- подготовить рекомендации для повышения NPS и повторных продаж.
""",
        encoding="utf-8",
    )
    (CONTEXT / "kpi.md").write_text(
        f"""# KPI проекта

| Показатель | Значение |
|---|---:|
| Заказы | {len(df)} |
| Клиенты | {df["customer_id"].nunique()} |
| Менеджеры | {df["manager"].nunique()} |
| Категории товаров | {df["category"].nunique()} |
| Период анализа | январь-июнь 2026 |
| Отзывы | {len(df)} |
| NPS | {nps:.0f} |
| Среднее время ответа | {avg_response:.1f} ч |
""",
        encoding="utf-8",
    )


def markdown_cell(source: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code_cell(source: str) -> dict[str, object]:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}


def build_notebook() -> None:
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    notebook = {
        "cells": [
            markdown_cell(
                """# Анализ продаж и клиентской обратной связи

Цель: найти продукты и каналы, где клиентский опыт ухудшает продажи, и сформировать короткий список действий."""
            ),
            code_cell(
                """import pandas as pd

df = pd.read_csv('../data/processed/sales_feedback_clean.csv', parse_dates=['order_date'])
df.head()"""
            ),
            code_cell(
                """summary = {
    'orders': len(df),
    'revenue': df['revenue'].sum(),
    'avg_rating': round(df['rating'].mean(), 2),
    'problem_share': round(df['has_problem'].mean(), 3),
}
summary"""
            ),
            code_cell(
                """product_metrics = (
    df.groupby('product')
      .agg(
          orders=('order_id', 'count'),
          revenue=('revenue', 'sum'),
          avg_rating=('rating', 'mean'),
          problem_share=('has_problem', 'mean'),
          avg_response_hours=('response_time_hours', 'mean'),
      )
      .sort_values('problem_share', ascending=False)
)
product_metrics"""
            ),
            code_cell(
                """channel_metrics = (
    df.groupby('channel')
      .agg(
          orders=('order_id', 'count'),
          avg_response_hours=('response_time_hours', 'mean'),
          problem_share=('has_problem', 'mean'),
      )
      .sort_values('avg_response_hours', ascending=False)
)
channel_metrics"""
            ),
            markdown_cell(
                """## Вывод

Фокус улучшений стоит выбирать не только по количеству жалоб, но и по влиянию продукта на выручку, маржинальность и повторяемость проблемы."""
            ),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.x"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def build_readme(df: pd.DataFrame) -> None:
    total_revenue = df["revenue"].sum()
    avg_rating = df["rating"].mean()
    problem_share = df["has_problem"].mean()
    nps = (df["nps_group"].eq("promoter").mean() - df["nps_group"].eq("detractor").mean()) * 100
    avg_response = df["response_time_hours"].mean()
    worst_product = (
        df.groupby("product")["has_problem"]
        .mean()
        .sort_values(ascending=False)
        .index[0]
    )
    worst_product_issue = df[(df["product"].eq(worst_product)) & df["has_problem"]]["feedback_reason"].value_counts().index[0]
    revenue_priority = (
        df.groupby("product", as_index=False)
        .agg(revenue=("revenue", "sum"), problem_share=("has_problem", "mean"))
        .query("product != @worst_product")
        .sort_values(["revenue", "problem_share"], ascending=False)
        .iloc[0]["product"]
    )
    revenue_priority_issue = df[(df["product"].eq(revenue_priority)) & df["has_problem"]]["feedback_reason"].value_counts().index[0]
    top_issue = Counter(df[df["has_problem"]]["feedback_reason"]).most_common(1)[0][0]
    top_categories = df.groupby("category")["has_problem"].mean().sort_values(ascending=False).head(2).index.tolist()
    slow_rating = df[df["response_time_hours"] > 24]["rating"].mean()
    fast_rating = df[df["response_time_hours"] <= 12]["rating"].mean()

    (PROJECT / "README.md").write_text(
        f"""# Анализ факторов, влияющих на удовлетворенность клиентов и продажи

Компактный коммерческий кейс по Customer Experience Analytics: синтетическая выгрузка продаж и клиентской обратной связи обработана на Python, чтобы найти факторы, влияющие на удовлетворенность клиентов, NPS и повторные продажи.

## Бизнес-кейс

ООО "ТехСнаб" продает промышленное оборудование и регулярно собирает обратную связь после завершения заказов. В последние два квартала выручка оставалась стабильной, однако количество негативных отзывов выросло, а доля повторных заказов начала снижаться.

Руководитель отдела продаж предполагает, что проблема может быть связана с отдельными категориями товаров, скоростью ответа менеджеров или повторяющимися причинами недовольства клиентов. Задача аналитика - исследовать данные и подготовить рекомендации для улучшения клиентского опыта.

## Исходные данные

| Показатель | Значение |
|---|---:|
| Продажи | {len(df)} |
| Клиенты | {df["customer_id"].nunique()} |
| Менеджеры | {df["manager"].nunique()} |
| Категории товаров | {df["category"].nunique()} |
| Период анализа | январь-июнь 2026 |
| Отзывы | {len(df)} |

## Цель исследования

- определить категории товаров с максимальной долей негативной обратной связи;
- найти продукты, где проблемы влияют на выручку и маржинальность;
- выявить связь между временем ответа и удовлетворенностью клиентов;
- подготовить рекомендации для повышения NPS и повторных продаж.

## Executive Dashboard

![Executive Dashboard](screenshots/00_executive_dashboard.svg)

## Выполненные работы

- исследована структура исходных данных;
- выполнена очистка и стандартизация данных;
- проведен исследовательский анализ;
- рассчитаны продуктовые и операционные метрики;
- исследована зависимость оценки клиента от времени ответа и категории товара;
- сформированы рекомендации для бизнеса.

## Ключевые цифры

| Метрика | Значение |
|---|---:|
| Заказы в выборке | {len(df)} |
| Выручка | {fmt_number(total_revenue)} руб. |
| Средняя оценка | {avg_rating:.2f} из 5 |
| NPS | {nps:.0f} |
| Заказы с проблемной обратной связью | {problem_share:.1%} |
| Среднее время ответа | {avg_response:.1f} ч |
| Продукт с максимальной долей проблем | {worst_product} |

## Основные выводы

- Самая частая причина негативной обратной связи - **{top_issue}**.
- Наибольшая доля проблемных заказов у продукта **{worst_product}**.
- Две наиболее проблемные категории: **{top_categories[0]}** и **{top_categories[1]}**.
- При ответе быстрее 12 часов средняя оценка клиента составляет **{fast_rating:.2f}**, при ответе дольше 24 часов - **{slow_rating:.2f}**.
- Продукты с высокой выручкой и высокой долей проблем требуют приоритета, потому что влияют и на деньги, и на повторные продажи.

## Рекомендации

- для `{worst_product}` разобрать причину `{worst_product_issue}` и добавить контрольный шаг перед передачей заказа клиенту;
- ввести SLA на первый ответ по почтовому каналу;
- для `{revenue_priority}` подготовить шаблон ответа по причине `{revenue_priority_issue}` и обновить описание в коммерческом предложении;
- раз в неделю смотреть матрицу “доля проблем x маржинальность”, чтобы выбирать фокус улучшений.

## Процесс работы

| Этап | Результат |
|---|---|
| Бизнес-контекст | сформулированы цель и KPI исследования |
| Сбор данных | подготовлена синтетическая CSV-выгрузка |
| Очистка | обработанные данные с расчетными полями |
| Анализ | продуктовые, клиентские и операционные метрики |
| Визуализация | executive dashboard и графики |
| Выводы | аналитическая записка и action plan |

## Результаты

| Артефакт | Файл |
|---|---|
| Бизнес-кейс | [01-business-context/business-case.md](01-business-context/business-case.md) |
| Цель и KPI | [01-business-context/kpi.md](01-business-context/kpi.md) |
| Исходные данные | [data/raw/sales_feedback_raw.csv](data/raw/sales_feedback_raw.csv) |
| Очищенные данные | [data/processed/sales_feedback_clean.csv](data/processed/sales_feedback_clean.csv) |
| Ноутбук анализа | [notebooks/sales_feedback_analysis.ipynb](notebooks/sales_feedback_analysis.ipynb) |
| Метрики по продуктам | [result/product_metrics.csv](result/product_metrics.csv) |
| План действий | [result/action_plan.csv](result/action_plan.csv) |
| Аналитическая записка | [result/analytics_summary.md](result/analytics_summary.md) |
| Описание данных | [docs/data_dictionary.md](docs/data_dictionary.md) |
| Зависимости для запуска | [requirements.txt](requirements.txt) |

## Ключевые графики

![Executive Dashboard](screenshots/00_executive_dashboard.svg)

![Выручка по месяцам](screenshots/01_revenue_by_month.svg)

![Средняя оценка по продуктам](screenshots/02_rating_by_product.svg)

![Причины обратной связи](screenshots/03_feedback_reasons.svg)

![Матрица приоритетов](screenshots/04_priority_matrix.svg)

## Навыки

Python, pandas, EDA, очистка данных, расчет метрик, NPS, визуализация, customer experience analytics, формирование рекомендаций.

## Формулировка для резюме

Провела анализ факторов, влияющих на удовлетворенность клиентов и продажи: очистила выгрузку на Python, рассчитала продуктовые и операционные метрики, выявила проблемные категории, оценила связь времени ответа с оценкой клиента, подготовила executive dashboard и рекомендации для повышения NPS.
""",
        encoding="utf-8",
    )
    (PROJECT / "requirements.txt").write_text("pandas>=2.0\n", encoding="utf-8")


def main() -> None:
    rows = generate_rows()
    write_raw(rows)
    df = clean_data()
    build_charts(df)
    build_outputs(df)
    build_notebook()
    build_readme(df)


if __name__ == "__main__":
    main()
