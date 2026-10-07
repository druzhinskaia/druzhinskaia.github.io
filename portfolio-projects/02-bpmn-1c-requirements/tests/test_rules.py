from pathlib import Path
import sys,unittest,re
from datetime import datetime,date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'reference'))
from sla import due_at,ZONE,initial_status,transition
class Rules(unittest.TestCase):
 def at(self,s):return datetime.fromisoformat(s).replace(tzinfo=ZONE)
 def test_friday_weekend_and_end_boundary(self):
  self.assertEqual(due_at(self.at('2026-06-26T09:00'),'Высокий'),self.at('2026-06-26T18:00'))
  self.assertEqual(due_at(self.at('2026-06-26T18:00'),'Высокий'),self.at('2026-06-29T18:00'))
  self.assertEqual(due_at(self.at('2026-06-28T10:00'),'Средний'),self.at('2026-07-01T18:00'))
 def test_explicit_holiday_and_working_weekend(self):
  self.assertEqual(due_at(self.at('2026-06-26T18:00'),'Высокий',holidays={date(2026,6,29)}),self.at('2026-06-30T18:00'))
  self.assertEqual(due_at(self.at('2026-06-26T18:00'),'Высокий',working_weekends={date(2026,6,27)}),self.at('2026-06-27T18:00'))
 def test_priority_recalculated_from_creation(self):
  created=self.at('2026-06-26T12:00');self.assertEqual(due_at(created,'Средний'),self.at('2026-07-01T12:00'));self.assertEqual(due_at(created,'Высокий'),self.at('2026-06-29T12:00'))
 def test_routes_roles_and_terminal(self):
  self.assertEqual(initial_status('Высокий'),'На согласовании');self.assertEqual(initial_status('Средний',True),'На согласовании')
  self.assertEqual(transition('Требует уточнения','На согласовании','менеджер',requires_approval=True),'На согласовании')
  self.assertEqual(transition('Выполнена','Закрыта','менеджер'),'Закрыта')
  for current,target,role in [('Новая','Закрыта','менеджер'),('На согласовании','В работе','менеджер'),('Выполнена','Закрыта','исполнитель'),('Закрыта','В работе','администратор')]:
   with self.assertRaises(ValueError):transition(current,target,role)
 def test_traceability_covers_all_ids(self):
  matrix=(ROOT/'04-requirements/requirements-traceability-matrix.md').read_text()
  for kind,count,file in [('FR',12,'04-requirements/functional-requirements.md'),('US',10,'04-requirements/user-stories.md'),('AC',14,'07-testing/acceptance-criteria.md'),('TS',21,'07-testing/test-scenarios.md'),('NFR',5,'04-requirements/non-functional.md')]:
   existing=set(re.findall(rf'{kind}-\d{{2}}',(ROOT/file).read_text()))
   self.assertEqual(len(existing),count)
   if kind in ['FR','NFR']:self.assertTrue(existing<=set(re.findall(rf'{kind}-\d{{2}}',matrix)))
   self.assertTrue(set(re.findall(rf'(?<![A-Z]){kind}-\d{{2}}',matrix))<=existing)
if __name__=='__main__':unittest.main()
