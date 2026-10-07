"""Reproduce analysis from the author's existing CSV; raw data is never rewritten."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

RAW_COLUMNS = ['order_id', 'order_date', 'customer_id', 'region', 'channel', 'manager',
               'category', 'product', 'quantity', 'discount', 'revenue', 'cost',
               'rating', 'feedback_reason', 'response_time_hours', 'is_return']
WEIGHTS = {'revenue': 0.4, 'problem_share': 0.4, 'rating': 0.2}


def prepare_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate first; fail with actionable errors rather than silently discard orders."""
    missing = sorted(set(RAW_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    df = raw[RAW_COLUMNS].copy()
    if df.empty:
        raise ValueError('Input contains no orders')
    if df.isna().any().any():
        raise ValueError(f'Missing values: {df.isna().sum()[lambda s: s.gt(0)].to_dict()}')
    if df['order_id'].duplicated().any():
        raise ValueError('order_id must identify a single order; duplicates require source review')
    for col in ['customer_id', 'region', 'channel', 'manager', 'category', 'product', 'feedback_reason']:
        df[col] = df[col].astype(str).str.strip()
        if df[col].eq('').any():
            raise ValueError(f'Empty required value in {col}')
    df['order_date'] = pd.to_datetime(df['order_date'], errors='raise')
    for col in ['quantity', 'discount', 'revenue', 'cost', 'rating', 'response_time_hours', 'is_return']:
        df[col] = pd.to_numeric(df[col], errors='raise')
    checks = {
        'quantity must be a positive integer': df.quantity.gt(0) & df.quantity.mod(1).eq(0),
        'discount must be between 0 and 1': df.discount.between(0, 1),
        'revenue and cost must be non-negative': df.revenue.ge(0) & df.cost.ge(0),
        'rating must be an integer from 1 to 5': df.rating.between(1, 5) & df.rating.mod(1).eq(0),
        'response_time_hours must be non-negative': df.response_time_hours.ge(0),
        'is_return must be 0 or 1': df.is_return.isin([0, 1]),
    }
    for message, valid in checks.items():
        if not valid.all():
            raise ValueError(f'{message}; invalid order IDs: {df.loc[~valid, "order_id"].head(10).tolist()}')
    df['month'] = df.order_date.dt.to_period('M').astype(str)
    df['profit'] = df.revenue - df.cost
    df['margin_pct'] = df.profit.div(df.revenue.where(df.revenue.ne(0))).round(3)
    df['has_problem'] = df.feedback_reason.ne('нет проблемы')
    df['rating_group'] = pd.cut(df.rating, [0, 3, 4, 5], labels=['низкая', 'средняя', 'высокая'])
    df['rating_balance_group'] = df.rating.map(lambda r: 'positive' if r == 5 else 'neutral' if r == 4 else 'negative')
    return df


def rating_balance(ratings: pd.Series) -> float:
    """Difference of shares of 5 and 1–3 ratings, in percentage points; not a NPS survey."""
    return float((ratings.eq(5).mean() - ratings.le(3).mean()) * 100)


def analyse(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    revenue, profit = df.revenue.sum(), df.profit.sum()
    summary = pd.DataFrame([{
        'orders': len(df), 'customers': df.customer_id.nunique(), 'revenue': revenue,
        'profit': profit, 'margin_pct': profit / revenue if revenue else None,
        'avg_rating': df.rating.mean(), 'rating_balance_pp': rating_balance(df.rating),
        'problem_share': df.has_problem.mean(), 'avg_response_hours': df.response_time_hours.mean(),
        'return_share': df.is_return.mean(),
    }])
    product = df.groupby(['category', 'product'], as_index=False).agg(
        orders=('order_id', 'count'), revenue=('revenue', 'sum'), profit=('profit', 'sum'),
        avg_rating=('rating', 'mean'), problem_share=('has_problem', 'mean'),
        avg_response_hours=('response_time_hours', 'mean'), return_share=('is_return', 'mean'),
        rating_balance_pp=('rating', rating_balance))
    product['margin_pct'] = product.profit.div(product.revenue.where(product.revenue.ne(0)))
    product['priority_score'] = (
        product.revenue.rank(pct=True) * WEIGHTS['revenue']
        + product.problem_share.rank(pct=True) * WEIGHTS['problem_share']
        + (1 - product.avg_rating.rank(pct=True)) * WEIGHTS['rating'])
    product = product.sort_values(['priority_score', 'product'], ascending=[False, True]).reset_index(drop=True)
    channel = df.groupby('channel', as_index=False).agg(
        orders=('order_id', 'count'), revenue=('revenue', 'sum'), avg_rating=('rating', 'mean'),
        problem_share=('has_problem', 'mean'), avg_response_hours=('response_time_hours', 'mean'))
    issues = df[df.has_problem].groupby('feedback_reason', as_index=False).agg(
        problem_orders=('order_id', 'count'), revenue_of_affected_orders=('revenue', 'sum'), avg_rating=('rating', 'mean'))
    issues = issues.sort_values('problem_orders', ascending=False)
    bucket = pd.cut(df.response_time_hours, [0, 12, 24, float('inf')],
                    labels=['0–12h', '>12–24h', '>24h'], include_lowest=True)
    response = df.assign(response_bucket=bucket).groupby('response_bucket', observed=True, as_index=False).agg(
        orders=('order_id', 'count'), avg_rating=('rating', 'mean'),
        rating_std=('rating', 'std'), problem_share=('has_problem', 'mean'))
    # Descriptive uncertainty is displayed, without a claim of causality or a hypothesis test.
    response['rating_se'] = response.rating_std.div(response.orders.pow(0.5))
    response['approx_ci95_low'] = response.avg_rating - 1.96 * response.rating_se
    response['approx_ci95_high'] = response.avg_rating + 1.96 * response.rating_se
    monthly = df.groupby('month', as_index=False).agg(orders=('order_id', 'count'), revenue=('revenue', 'sum'))
    rows = []
    for i, row in product.head(3).iterrows():
        reasons = df.loc[df['product'].eq(row['product']) & df.has_problem, 'feedback_reason'].value_counts()
        reason = str(reasons.index[0]) if len(reasons) else 'нет зарегистрированной проблемы'
        rows.append({'priority': i + 1, 'focus': row['product'], 'priority_score': row['priority_score'],
                     'most_common_reason': reason, 'action': f'Проверить первопричину: {reason}; согласовать действие и измерение эффекта',
                     'owner': 'руководитель отдела продаж', 'success_metric': 'динамика доли проблемных заказов'})
    quality = pd.DataFrame({'metric': ['rows', 'duplicate_order_id', 'missing_raw_values', 'zero_revenue_orders'],
                            'value': [len(df), int(df.order_id.duplicated().sum()),
                                      int(df[RAW_COLUMNS].isna().sum().sum()), int(df.revenue.eq(0).sum())]})
    return {'kpi_summary': summary, 'product_metrics': product, 'channel_metrics': channel,
            'issue_metrics': issues, 'response_analysis': response, 'monthly_sales': monthly,
            'action_plan': pd.DataFrame(rows), 'data_quality': quality}


def build_charts(df: pd.DataFrame, tables: dict[str, pd.DataFrame], directory: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    for language in ['ru', 'en']:
        english = language == 'en'
        suffix = '.en' if english else ''
        def save(fig, name):
            fig.tight_layout()
            for ext in ['png', 'svg']:
                fig.savefig(directory / f'{name}{suffix}.{ext}', dpi=140, facecolor='white')
            plt.close(fig)
        monthly = tables['monthly_sales']
        fig, ax = plt.subplots(figsize=(9, 4.8)); ax.plot(monthly.month, monthly.revenue / 1e6, marker='o', color='#216c7a')
        ax.set(title='Revenue by month' if english else 'Выручка по месяцам', ylabel='RUB million' if english else 'млн руб.')
        save(fig, '01_revenue_by_month')
        product = tables['product_metrics'].sort_values('avg_rating')
        fig, ax = plt.subplots(figsize=(10, 5.5)); ax.barh(product['product'], product.avg_rating, color='#216c7a')
        ax.set(title='Average customer rating by product' if english else 'Средняя оценка по продуктам', xlim=(0, 5), xlabel='Rating, 1–5' if english else 'Оценка, 1–5')
        save(fig, '02_rating_by_product')
        issues = tables['issue_metrics'].sort_values('problem_orders')
        fig, ax = plt.subplots(figsize=(10, 5)); ax.barh(issues.feedback_reason, issues.problem_orders, color='#b96b36')
        ax.set(title='Reported issue reasons' if english else 'Причины проблемной обратной связи', xlabel='Orders' if english else 'Заказы')
        save(fig, '03_feedback_reasons')
        product = tables['product_metrics']
        fig, ax = plt.subplots(figsize=(11, 6)); ax.scatter(product.margin_pct * 100, product.problem_share * 100,
                  s=product.revenue / max(product.revenue.max(), 1) * 1100 + 40, color='#216c7a', alpha=.6)
        for row in product.itertuples(): ax.annotate(row.product, (row.margin_pct * 100, row.problem_share * 100), xytext=(5, 5), textcoords='offset points', fontsize=8)
        ax.set(title='Product priorities (bubble size: revenue)' if english else 'Приоритеты продуктов (размер точки — выручка)',
               xlabel='Weighted margin, %' if english else 'Взвешенная маржинальность, %',
               ylabel='Issue rate, %' if english else 'Доля проблемных заказов, %')
        save(fig, '04_priority_matrix')
        s = tables['kpi_summary'].iloc[0]
        fig, axes = plt.subplots(2, 3, figsize=(11, 5))
        cards = [('Revenue, RUB' if english else 'Выручка, руб.', f'{s.revenue:,.0f}'),
                 ('Average rating (1–5)' if english else 'Средняя оценка (1–5)', f'{s.avg_rating:.2f}'),
                 ('Rating balance, pp (1–5)' if english else 'Баланс оценок, п.п. (1–5)', f'{s.rating_balance_pp:.1f}'),
                 ('Issue rate' if english else 'Проблемные заказы', f'{s.problem_share:.1%}'),
                 ('Response time, hours' if english else 'Время ответа, часы', f'{s.avg_response_hours:.1f}'),
                 ('Orders' if english else 'Заказы', f'{s.orders:,.0f}')]
        for ax, (label, value) in zip(axes.flat, cards):
            ax.axis('off'); ax.text(.05, .72, label, fontsize=11, transform=ax.transAxes); ax.text(.05, .32, value, fontsize=23, color='#216c7a', transform=ax.transAxes)
        save(fig, '00_executive_dashboard')


def run(project_root: Path, charts: bool = True) -> dict[str, pd.DataFrame]:
    root = project_root.resolve()
    raw = pd.read_csv(root / 'data/raw/sales_feedback_raw.csv')
    df = prepare_data(raw)
    (root / 'data/processed').mkdir(parents=True, exist_ok=True)
    df.to_csv(root / 'data/processed/sales_feedback_clean.csv', index=False)
    tables = analyse(df)
    result = root / 'result'; result.mkdir(exist_ok=True)
    for name, frame in tables.items(): frame.to_csv(result / f'{name}.csv', index=False, float_format='%.6f')
    summary = tables['kpi_summary'].iloc[0]
    response = tables['response_analysis']
    (result / 'analytics_summary.md').write_text(
        '# Аналитическая записка\n\nДанные предоставлены автором проекта. Исходный CSV сохраняется без перезаписи.\n\n'
        f'Период: {df.order_date.min():%Y-%m-%d} — {df.order_date.max():%Y-%m-%d}. Заказы: {len(df)}. '
        f'Выручка: {summary.revenue:,.0f} руб. Средняя оценка: {summary.avg_rating:.2f}. '
        f'Доля проблемных заказов: {summary.problem_share:.1%}.\n\n'
        f'Баланс оценок 1–5: {summary.rating_balance_pp:.2f} п.п. Это разность долей оценок 5 и 1–3. '
        'Для показателя NPS необходим отдельный вопрос о рекомендации со шкалой 0–10.\n\n'
        '## Наблюдаемые связи\n\n' + response[['response_bucket', 'orders', 'avg_rating', 'problem_share']].to_csv(index=False)
        + '\nРазличия описательные. Время ответа может быть связано с каналом и сложностью заказа; причинный эффект не установлен. '
        'Интервалы в CSV — приближённые интервалы среднего при независимости наблюдений; повторные клиенты могут нарушать эту предпосылку.\n\n'
        '## Приоритеты\n\n' + tables['action_plan'].to_csv(index=False)
        + '\nВес выручки — 0,4; доли проблем — 0,4; обратного ранга оценки — 0,2. Это явно заданная эвристика приоритизации, '
        'а не модель предсказания эффекта. План действий следует тому же рейтингу.\n\n'
        '## Ограничения\n\nВыручка и себестоимость берутся из исходных полей без повторного применения скидки. '
        'is_return используется для расчёта доли возвратов; корректировка выручки по возвратам без суммы возврата не выполняется. '
        'При нулевой выручке маржинальность недоступна. Динамика повторных покупок и причинное влияние на продажи здесь не исследуются.\n', encoding='utf-8')
    if charts: build_charts(df, tables, root / 'screenshots')
    (result / 'run_manifest.json').write_text(json.dumps({'rows': len(df), 'raw_columns': RAW_COLUMNS, 'priority_weights': WEIGHTS,
        'period': [str(df.order_date.min().date()), str(df.order_date.max().date())]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return tables


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--no-charts', action='store_true')
    args = parser.parse_args()
    result = run(args.project_root, charts=not args.no_charts)
    print(result['kpi_summary'].to_string(index=False))
