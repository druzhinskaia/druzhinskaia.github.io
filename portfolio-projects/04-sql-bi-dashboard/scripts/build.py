"""Build SQLite, exports and local dashboard from the author's unchanged CSV files."""
import argparse, csv, json, sqlite3
from datetime import date
from pathlib import Path
TABLES=['customers','products','orders','order_items','payments']

def build(root):
    root=Path(root).resolve()
    target=root/'data/retail_sales.db'
    temporary=target.with_suffix('.building.db')
    temporary.unlink(missing_ok=True)
    try:
        with sqlite3.connect(temporary) as db:
            db.row_factory=sqlite3.Row
            db.executescript((root/'sql/01_schema.sql').read_text())
            for table in TABLES:
                with (root/f'data/{table}.csv').open(newline='',encoding='utf-8-sig') as file:
                    reader=csv.DictReader(file)
                    expected=[x[1] for x in db.execute(f'PRAGMA table_info({table})')]
                    if reader.fieldnames != expected: raise ValueError(f'{table}: expected {expected}, got {reader.fieldnames}')
                    records=[]
                    for line,row in enumerate(reader,2):
                        if any(v is None or v.strip()=='' for v in row.values()): raise ValueError(f'{table}:{line}: empty required field')
                        for field,value in row.items():
                            if field.endswith('_date'): date.fromisoformat(value)
                        records.append(tuple(row[c] for c in expected))
                    db.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in expected)})', records)
            db.executescript((root/'sql/03_views.sql').read_text())
            if db.execute('PRAGMA foreign_key_check').fetchall(): raise ValueError('Foreign key violation')
            if db.execute('SELECT COUNT(*) FROM orders LEFT JOIN order_totals USING(order_id) WHERE revenue IS NULL').fetchone()[0]:
                raise ValueError('Order without items; revenue requires source review')
            (root/'result').mkdir(exist_ok=True)
            for statement in (root/'sql/03_analytics_queries.sql').read_text().split(';'):
                if not statement.strip(): continue
                name=statement.strip().splitlines()[0].removeprefix('-- ').strip()
                cursor=db.execute(statement)
                with (root/f'result/{name}.csv').open('w',newline='',encoding='utf-8') as output:
                    writer=csv.writer(output); writer.writerow([c[0] for c in cursor.description]); writer.writerows(cursor.fetchall())
            payload={'orders':[dict(row) for row in db.execute('SELECT * FROM sales_order_mart ORDER BY order_id')],
                'items':[dict(row) for row in db.execute('SELECT i.*,p.category FROM order_items i JOIN products p USING(product_id)')]}
            # A JS literal allows opening index.html directly: no server and no fetch/CORS needed.
            (root/'dashboard/data.js').write_text('window.SALES_DATA = '+json.dumps(payload,ensure_ascii=False).replace('</',r'<\/')+';\n',encoding='utf-8')
            kpi=dict(db.execute('SELECT COUNT(*) orders,SUM(revenue) revenue,SUM(receivables) receivables FROM sales_order_mart').fetchone())
            (root/'result/build_manifest.json').write_text(json.dumps(kpi,indent=2)+'\n')
        temporary.replace(target)
        return kpi
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1])
    print(build(p.parse_args().project_root))
