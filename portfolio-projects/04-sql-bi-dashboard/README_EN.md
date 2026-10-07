# SQL sales analytics and interactive dashboard

[Русский](README.md) · [Live dashboard](https://druzhinskaia.github.io/portfolio-projects/04-sql-bi-dashboard/dashboard/)

The author's own CSV data is loaded into five SQLite tables. Line items and payments are aggregated separately per order before joining, preventing duplicated sales. Orders with no payment remain in the mart. Cancelled orders are excluded consistently. Outstanding balances and overpayments are separate; margin is total profit / total revenue.

From the root, using Python 3.10–3.12 (standard library only):

```bash
python scripts/build.py
python -m unittest discover -s tests -v
node tests/test_dashboard.cjs
```

The last command needs Node.js 18+. Open `dashboard/index.html`; its local data.js works without a server. Month and channel filters recalculate all panels. The bilingual HTML/JavaScript dashboard is a browser prototype; no Power BI file is supplied.

Verified dataset totals: 1,660 non-cancelled orders, RUB 152,442,883 revenue and RUB 25,128,577 outstanding balance. Tests cover missing/additional payments, overpayments, constraints, every channel and combined filters.

The current source has one payment record per order. Multiple records must represent independent, non-overlapping payment events; cumulative snapshots require another rule. There is no payment date or snapshot history. Month refers to order month with current payment balance, not a historical month-end balance. Outstanding is not necessarily overdue. Discounts are not reapplied to line_revenue. Channel revenue ranking is not marketing ROI: advertising costs are unavailable. Source CSV files are preserved by the build.
