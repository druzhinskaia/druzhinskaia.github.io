import importlib.util,sqlite3,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'scripts/build.py'); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
class Queries(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)/'project';shutil.copytree(ROOT,self.root);b.build(self.root)
  self.db=sqlite3.connect(self.root/'data/retail_sales.db');self.db.row_factory=sqlite3.Row;self.db.execute('PRAGMA foreign_keys=ON')
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def test_totals(self):
  row=self.db.execute('SELECT COUNT(*) n,SUM(revenue) rev FROM sales_order_mart').fetchone();self.assertEqual(row['n'],1660);self.assertEqual(row['rev'],152442883)
 def test_multiple_payments_do_not_duplicate_sales(self):
  before=dict(self.db.execute('SELECT * FROM sales_order_mart LIMIT 1').fetchone());oid=before['order_id']
  self.db.execute("INSERT INTO payments VALUES(999999,?,'карта','оплачен',10,'2026-01-30')",(oid,))
  after=dict(self.db.execute('SELECT * FROM sales_order_mart WHERE order_id=?',(oid,)).fetchone())
  self.assertEqual(after['revenue'],before['revenue']);self.assertEqual(after['paid_amount'],before['paid_amount']+10)
 def test_missing_payment_preserves_order_and_overpayment_is_separate(self):
  oid=self.db.execute('SELECT order_id FROM sales_order_mart LIMIT 1').fetchone()[0]
  self.db.execute('DELETE FROM payments WHERE order_id=?',(oid,));row=self.db.execute('SELECT * FROM sales_order_mart WHERE order_id=?',(oid,)).fetchone();self.assertEqual(row['receivables'],row['revenue'])
  self.db.execute("INSERT INTO payments VALUES(999999,?,'карта','оплачен',?,'2026-01-30')",(oid,row['revenue']+100))
  row=self.db.execute('SELECT * FROM sales_order_mart WHERE order_id=?',(oid,)).fetchone();self.assertEqual(row['receivables'],0);self.assertEqual(row['overpayment'],100)
 def test_foreign_keys_and_negative_money(self):
  with self.assertRaises(sqlite3.IntegrityError):self.db.execute("INSERT INTO payments VALUES(999999,-1,'x','x',1,'2026-01-01')")
  with self.assertRaises(sqlite3.IntegrityError):self.db.execute("UPDATE order_items SET line_revenue=-1 WHERE item_id=1")
if __name__=='__main__':unittest.main()
