"""Reference rules only; not a 1C configuration or delivery integration."""
from datetime import datetime,timedelta,time
from zoneinfo import ZoneInfo
ZONE=ZoneInfo('Europe/Moscow')
HOURS={'Высокий':9,'Средний':27,'Низкий':45}
TERMINAL={'Закрыта','Отклонена'}
def due_at(created,priority,holidays=frozenset(),working_weekends=frozenset()):
 if created.tzinfo is None:raise ValueError('Timezone-aware created_at required')
 if priority not in HOURS:raise ValueError('Unknown priority')
 cursor=created.astimezone(ZONE); remaining=timedelta(hours=HOURS[priority])
 def working(day):return day not in holidays and (day.weekday()<5 or day in working_weekends)
 while remaining>timedelta(0):
  start=datetime.combine(cursor.date(),time(9),ZONE);end=datetime.combine(cursor.date(),time(18),ZONE)
  if not working(cursor.date()) or cursor>=end:
   cursor=datetime.combine(cursor.date()+timedelta(days=1),time(9),ZONE);continue
  cursor=max(cursor,start);available=end-cursor
  if remaining<=available:return cursor+remaining
  remaining-=available;cursor=end
 raise AssertionError('Unreachable')
def initial_status(priority,requires_approval=False):
 if priority not in HOURS:raise ValueError('Unknown priority')
 return 'На согласовании' if priority=='Высокий' or requires_approval else 'Новая'
def transition(current,target,role,priority='Средний',requires_approval=False):
 allowed={('Новая','В работе'):{'менеджер'},('Новая','Требует уточнения'):{'менеджер'},
 ('В работе','Требует уточнения'):{'менеджер'},('На согласовании','Требует уточнения'):{'руководитель'},
 ('На согласовании','Согласована'):{'руководитель'},('На согласовании','Отклонена'):{'руководитель'},
 ('Согласована','В работе'):{'менеджер'},('В работе','Выполнена'):{'исполнитель'},
 ('Выполнена','Закрыта'):{'менеджер'},('Выполнена','В работе'):{'менеджер'}}
 if current=='Требует уточнения' and target==initial_status(priority,requires_approval) and role=='менеджер':return target
 if role not in allowed.get((current,target),set()):raise ValueError('Forbidden transition or role')
 return target
