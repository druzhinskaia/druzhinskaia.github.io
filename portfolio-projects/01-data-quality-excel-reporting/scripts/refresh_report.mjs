/** Refresh author-provided exports. No source records are generated or repaired. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(process.argv[2]||path.join(path.dirname(fileURLToPath(import.meta.url)),'..'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,'templates/report_layout.xlsx')));
const spare=20, registryCapacity=512;
const definitions=[['Order','orders','01_orders_raw',10,[2]],['Client','clients','02_clients_raw',6,[5]],['Payment','payments','03_payments_raw',5,[3]]];
const sources={};
for(const [entity,name,sheetName,cols,dates] of definitions){
 const raw=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,`data/raw/${name}_raw.xlsx`)));
 const sheet=raw.worksheets.getItemAt(0), data=sheet.getUsedRange().values;
 for(const col of dates) sheet.getRangeByIndexes(1,col-1,data.length-1,1).setNumberFormat('yyyy-mm-dd');
 await (await SpreadsheetFile.exportXlsx(raw)).save(path.join(root,`data/raw/${name}_raw.xlsx`));
 const target=wb.worksheets.getItem(sheetName);target.getUsedRange().clear({applyTo:'contents'});
 target.getRangeByIndexes(0,0,data.length,cols).values=data;
 for(const col of dates)target.getRangeByIndexes(1,col-1,data.length+spare-1,1).setNumberFormat('yyyy-mm-dd');
 for(const table of target.tables.items)table.delete();
 const capacity=data.length-1+spare;
 target.tables.add(`A1:${String.fromCharCode(64+cols)}${capacity+1}`,true,`tbl_${name}`);
 sources[entity]={sheetName,capacity,count:data.length-1,cols};
}
const checks=wb.worksheets.getItem('04_checks');for(const t of checks.tables.items)t.delete();checks.getUsedRange().clear({applyTo:'contents'});
checks.getRange('A1:K1').values=[['entity','record_id','duplicate_id','required_fields','reference','calculation_or_INN_format','negative_price','date','status','error_count','source_row']];
const ensureSheet=name=>{try{return wb.worksheets.getItem(name)}catch{return wb.worksheets.add(name)}};
const events=ensureSheet('10_events');const params=ensureSheet('09_parameters');events.getUsedRange()?.clear({applyTo:'contents'});
params.getRange('A1:B6').values=[['Параметр','Значение'],['Дата среза',46198],['Допуск суммы, руб.',0.01],['Вместимость реестра',registryCapacity],['Проверенные строки',0],['Состояние реестра','']];
params.getRange('B2').setNumberFormat('yyyy-mm-dd');
params.getRange('A8:B12').values=[['Источник','Максимум строк'],...definitions.map(([entity,name])=>[name,sources[entity].capacity]),['Важно','Добавляйте строки только в выделенную вместимость; для большего объёма пересоберите книгу.']];
params.getRange('A14:B16').values=[['Источник данных','Выгрузки предоставлены автором проекта'],['SKIP','Зависимая проверка пропущена, если исходные поля пусты или связь не однозначна'],['ИНН','Проверяется только цифровой формат и длина 10/12; контрольная сумма не проверяется']];
const rawRef=(e,col)=>`'${sources[e].sheetName}'!$${col}$2:$${col}$${sources[e].capacity+1}`;
const checksRows=[],eventRows=[];let checkRow=2,eventRow=2;
const error=(condition)=>`IF(${condition},"ERROR","OK")`;
for(const [entity,name,sheetName,cols] of definitions){
 const src=sources[entity];
 for(let row=2;row<=src.capacity+1;row++,checkRow++){
  const v=col=>`'${sheetName}'!${col}${row}`, present=`COUNTA('${sheetName}'!A${row}:${String.fromCharCode(64+cols)}${row})>0`;
  const wrap=f=>`=IF(${present},${f},"")`;
  const duplicate=error(`AND(${v('A')}<>"",COUNTIF(${rawRef(entity,'A')},${v('A')})>1)`);
  let required,reference='"N/A"',calculation='"N/A"',negative='"N/A"',dateCheck,status='"N/A"',relationType='Нет связи';
  if(entity==='Order'){
   required=error(`OR(${v('A')}="",${v('B')}="",${v('C')}="",${v('D')}="",${v('E')}="",${v('F')}="",${v('G')}="",${v('H')}="",${v('I')}="",${v('J')}="")`);
   reference=`IF(${v('C')}="","SKIP",${error(`COUNTIF(${rawRef('Client','A')},${v('C')})<>1`)})`;
   relationType=`=IF(COUNTIF(${rawRef('Client','A')},${v('C')})>1,"Неоднозначная связь","Нет связи")`;
   calculation=`IF(OR(${v('G')}="",${v('H')}="",${v('I')}=""),"SKIP",${`IF(AND(ISNUMBER(${v('G')}),ISNUMBER(${v('H')}),ISNUMBER(${v('I')})),${error(`OR(${v('G')}<=0,MOD(${v('G')},1)<>0,ABS(${v('I')}-${v('G')}*${v('H')})>'09_parameters'!$B$3)`)},"ERROR")`})`;
   negative=`IF(${v('H')}="","SKIP",${error(`${v('H')}<0`)})`;
   dateCheck=`IF(${v('B')}="","SKIP",${error(`OR(NOT(ISNUMBER(${v('B')})),${v('B')}<=0,${v('B')}>'09_parameters'!$B$2)`)})`;
   status=`IF(${v('J')}="","SKIP",${error(`AND(${v('J')}<>"Выполнен",${v('J')}<>"В работе",${v('J')}<>"Отменен",${v('J')}<>"Ожидает оплаты")`)})`;
  }else if(entity==='Client'){
   required=error(`OR(${v('A')}="",${v('B')}="",${v('C')}="",${v('D')}="",${v('E')}="",${v('F')}="")`);
   const digits=Array.from({length:12},(_,i)=>`IF(${i+1}>LEN(${v('C')}&""),TRUE,IFERROR(FIND(MID(${v('C')}&"",${i+1},1),"x0123456789")>=2,FALSE))`).join(',');
   calculation=`IF(${v('C')}="","SKIP",${error(`OR(AND(LEN(${v('C')}&"")<>10,LEN(${v('C')}&"")<>12),NOT(AND(${digits})))`)})`;
   dateCheck=`IF(${v('E')}="","SKIP",${error(`OR(NOT(ISNUMBER(${v('E')})),${v('E')}<=0,${v('E')}>'09_parameters'!$B$2)`)})`;
  }else{
   required=error(`OR(${v('A')}="",${v('B')}="",${v('C')}="",${v('D')}="",${v('E')}="")`);
   const count=`COUNTIF(${rawRef('Order','A')},${v('B')})`, lookup=col=>`INDEX(${rawRef('Order',col)},MATCH(${v('B')},${rawRef('Order','A')},0))`;
   reference=`IF(${v('B')}="","SKIP",${error(`${count}<>1`)})`;
   relationType=`=IF(${count}>1,"Неоднозначная связь","Нет связи")`;
   calculation=`IF(OR(${count}<>1,${v('D')}=""),"SKIP",${error(`OR(NOT(ISNUMBER(${v('D')})),${v('D')}<0,${v('D')}>${lookup('I')}+'09_parameters'!$B$3)`)})`;
   dateCheck=`IF(${v('C')}="","SKIP",IF(${error(`OR(NOT(ISNUMBER(${v('C')})),${v('C')}<=0,${v('C')}>'09_parameters'!$B$2)`)}="ERROR","ERROR",IF(${count}<>1,"SKIP",${error(`${v('C')}<${lookup('B')}`)})))`;
   status=`IF(${v('E')}="","SKIP",${error(`AND(${v('E')}<>"Оплачено",${v('E')}<>"Частично оплачено",${v('E')}<>"Не оплачено")`)})`;
  }
  checksRows.push([wrap(`"${entity}"`),wrap(v('A')),wrap(duplicate),wrap(required),wrap(reference),wrap(calculation),wrap(negative),wrap(dateCheck),wrap(status),`=COUNTIF(C${checkRow}:I${checkRow},"ERROR")`,wrap(String(row))]);
  const types=['Дубль','Пустое поле',relationType,entity==='Client'?'Формат ИНН':'Ошибка расчета','Отрицательная цена','Дата','Статус'];
  const fields=entity==='Order'?['order_id','required_fields','client_id','quantity/price/order_sum','price','order_date','status']:entity==='Client'?['client_id','required_fields','client_id','inn','N/A','registration_date','N/A']:['payment_id','required_fields','order_id','payment_sum','N/A','payment_date','payment_status'];
  const recommendations=['Проверить уникальность ID в источнике; не удалять записи автоматически','Дополнить обязательные поля в источнике','Исправить ссылку или разрешить дубли связанного ID','Сверить исходные значения и правило расчёта','Проверить цену в источнике','Сверить дату со срезом и исходной записью','Выбрать допустимый статус'];
  for(let rule=0;rule<7;rule++,eventRow++){
   const col=String.fromCharCode(67+rule);
   eventRows.push([entity,`='04_checks'!B${checkRow}`,row,`=IF('04_checks'!${col}${checkRow}="ERROR",1,0)`,`${entity}:${row}:${rule+1}`,types[rule],['High','High','High','High','High','Medium','Medium'][rule],fields[rule],entity==='Client'&&rule===3?'Сверить длину ИНН 10/12 цифр с источником':recommendations[rule],`=IF(D${eventRow}=1,K${eventRow},0)`,`=D${eventRow}+${eventRow===2?'0':`K${eventRow-1}`}`]);
  }
 }
}
// LEN distinguishes a real empty cell from the valid numeric value zero.
const explicitBlank=f=>f.replace(/('[^']+'![A-Z]+[0-9]+)=""/g,'LEN($1&"")=0').replace(/('[^']+'![A-Z]+[0-9]+)<>""/g,'LEN($1&"")>0');
checks.getRange(`A2:K${checkRow-1}`).formulas=checksRows.map(row=>row.map(explicitBlank));
checks.tables.add(`A1:K${checkRow-1}`,true,'tbl_checks');
events.getRange('A1:K1').values=[['entity','record_id','source_row','is_error','rule_id','error_type','criticality','source_field','recommendation','event_number','running_count']];
// Mixed formula/value writes preserve textual rule metadata.
for(let col=0;col<11;col++){
 const letter=String.fromCharCode(65+col), rows=eventRows.map(r=>[r[col]]);
 if([1,3,9,10].includes(col))events.getRange(`${letter}2:${letter}${eventRow-1}`).formulas=rows;
 else if(col===5){events.getRange(`${letter}2:${letter}${eventRow-1}`).values=rows.map(r=>[r[0].startsWith('=')?'':r[0]]);eventRows.forEach((r,i)=>{if(r[col].startsWith('='))events.getRange(`${letter}${i+2}`).formulas=[[r[col]]]});}
 else events.getRange(`${letter}2:${letter}${eventRow-1}`).values=rows;
}
const registry=wb.worksheets.getItem('05_errors');for(const t of registry.tables.items)t.delete();registry.getUsedRange().clear({applyTo:'contents'});
registry.getRange('A1:G1').values=[['entity','record_id','source_row','error_type','criticality','source_field','recommendation']];
const registryRows=[];
for(let n=1;n<=registryCapacity;n++){registryRows.push([0,1,2,5,6,7,8].map(col=>`=IF(${n}>'10_events'!$K$${eventRow-1},"",INDEX('10_events'!$${String.fromCharCode(65+col)}$2:$${String.fromCharCode(65+col)}$${eventRow-1},$H${n+1}))`));}
registry.getRange(`H2:H${registryCapacity+1}`).formulas=Array.from({length:registryCapacity},(_,i)=>[`=IF(${i+1}>'10_events'!$K$${eventRow-1},0,MATCH(${i+1},'10_events'!$J$2:$J$${eventRow-1},0))`]);
registry.getRange(`A2:G${registryCapacity+1}`).formulas=registryRows;registry.tables.add(`A1:G${registryCapacity+1}`,true,'tbl_errors');
params.getRange('B5').formulas=[[`=SUM('06_summary'!B4,'06_summary'!B6,'06_summary'!B7)`]];
params.getRange('B6').formulas=[[`=IF('10_events'!K${eventRow-1}>B4,"OVERFLOW: увеличьте вместимость реестра","OK")`]];
const summary=wb.worksheets.getItem('06_summary');
summary.getRange('B4').formulas=[[`=COUNTIF('04_checks'!A2:A${checkRow-1},"Order")`]];
summary.getRange('B5').formulas=[[`=SUM(${rawRef('Order','I')})`]];
summary.getRange('B6').formulas=[[`=COUNTIF('04_checks'!A2:A${checkRow-1},"Client")`]];
summary.getRange('B7').formulas=[[`=COUNTIF('04_checks'!A2:A${checkRow-1},"Payment")`]];
summary.getRange('B8').formulas=[[`='10_events'!K${eventRow-1}`]];
summary.getRange('B9').formulas=[[`=IFERROR(COUNTIF('04_checks'!J2:J${checkRow-1},">0")/'09_parameters'!B5,0)`]];
summary.getRange('D10:E19').clear({applyTo:'contents'});
const errorTypes=['Дубль','Пустое поле','Нет связи','Неоднозначная связь','Ошибка расчета','Формат ИНН','Отрицательная цена','Дата','Статус'];
summary.getRange('D10:E10').values=[['Тип ошибки','События']];
summary.getRange('D11:D19').values=errorTypes.map(t=>[t]);
summary.getRange('E11:E19').formulas=errorTypes.map((t,i)=>[`=COUNTIFS('10_events'!F2:F${eventRow-1},D${i+11},'10_events'!D2:D${eventRow-1},1)`]);
summary.getRange('H4:H6').formulas=['Order','Client','Payment'].map(t=>[`=COUNTIFS('10_events'!A2:A${eventRow-1},"${t}",'10_events'!D2:D${eventRow-1},1)`]);
summary.getRange('H7').formulas=[[`=COUNTIFS('10_events'!G2:G${eventRow-1},"High",'10_events'!D2:D${eventRow-1},1)`]];
// Replace legacy fixed-range monthly/status formulas with bounded source capacity.
summary.getRange('E4:E7').formulas=['Выполнен','В работе','Ожидает оплаты','Отменен'].map(t=>[`=COUNTIF(${rawRef('Order','J')},"${t}")`]);
summary.getRange('E8').formulas=[['=B4-SUM(E4:E7)']];
for(let month=1;month<=5;month++)summary.getRange(`B${month+12}`).formulas=[[`=SUMIFS(${rawRef('Order','I')},${rawRef('Order','B')},">="&DATE(2026,${month},1),${rawRef('Order','B')},"<"&DATE(2026,${month+1},1))`]];
const dashboard=wb.worksheets.getItem('07_dashboard');dashboard.deleteAllDrawings();dashboard.getRange('D8:E17').clear({applyTo:'contents'});
dashboard.getRange('D8:E8').values=[['Тип ошибки','События']];dashboard.getRange('D9:D17').formulas=errorTypes.map((_,i)=>[`='06_summary'!D${i+11}`]);dashboard.getRange('E9:E17').formulas=errorTypes.map((_,i)=>[`='06_summary'!E${i+11}`]);
dashboard.getRange('A19:H20').merge();dashboard.getRange('A19').values=[['Реестр 05_errors обновляется по формулам; каждая ошибка связана с исходной строкой.']];dashboard.getRange('A21:H22').merge();dashboard.getRange('A21').formulas=[[`="Дата среза: "&TEXT('09_parameters'!B2,"yyyy-mm-dd")&" | Вместимость реестра: "&'09_parameters'!B4&" | "&'09_parameters'!B6`]];
// New charts include the additional reference and INN categories.
const chart=dashboard.charts.add('bar',dashboard.getRange('D8:E17')); chart.title='Ошибки по типам';chart.setPosition('J2','R20');
for(const sheet of [checks,registry,events,params]){sheet.getRange('A1:K1').format.fill='#1F4E78';sheet.getRange('A1:K1').format.font={color:'#FFFFFF',bold:true};sheet.getRange('A1:K1').format.wrapText=true;sheet.getRange('A1:K1').format.rowHeight=42;sheet.freezePanes.freezeRows(1);}
checks.getRange('C2:I'+(checkRow-1)).conditionalFormats.add('containsText',{text:'ERROR',format:{fill:'#F4CCCC',font:{color:'#9C0006'}}});
params.getRange('A1:A16').format.columnWidth=30;params.getRange('B1:B16').format.columnWidth=82;params.getRange('A1:B16').format.wrapText=true;
registry.getRange('A1:C513').format.columnWidth=15;registry.getRange('D1:F513').format.columnWidth=24;registry.getRange('G1:G513').format.columnWidth=76;
registry.getRange('A2:G513').format.rowHeight=25;registry.getRange('G2:G513').format.wrapText=true;
wb.recalculate();
const clientSheet=wb.worksheets.getItem('02_clients_raw'), originalInn=clientSheet.getRange('C2').values, beforeInn=Number(summary.getRange('B8').values[0][0]);
clientSheet.getRange('C2').values=[['12345678x2']];wb.recalculate();assert.equal(Number(summary.getRange('B8').values[0][0]),beforeInn+1);clientSheet.getRange('C2').values=originalInn;wb.recalculate();
const total=Number(summary.getRange('B8').values[0][0]),visible=registry.getRange('A2:A513').values.flat().filter(v=>v!==''&&v!==null).length;
if(!Number.isFinite(total)){console.log((await wb.inspect({kind:'region',sheetId:'04_checks',range:'A1:K5',maxChars:3000})).ndjson);console.log(checks.getRange('F2').formulas);console.log(events.getRange('D2:K3').values);}
assert.equal(total,visible,'Registry must contain every current error');
const before=total, sourceSheet=wb.worksheets.getItem('01_orders_raw'), saved=sourceSheet.getRange('D2').values;
sourceSheet.getRange('D2').values=[['']];wb.recalculate();assert.equal(Number(summary.getRange('B8').values[0][0]),before+1);assert.equal(registry.getRange('A2:A513').values.flat().filter(v=>v!==''&&v!==null).length,before+1);
sourceSheet.getRange('D2').values=saved;wb.recalculate();assert.equal(Number(summary.getRange('B8').values[0][0]),before);
const newRow=sources.Order.count+2;sourceSheet.getRange(`A${newRow}:J${newRow}`).values=[[99999,46100,'C003','Менеджер','Категория','Товар',1,10,10,'Выполнен']];wb.recalculate();assert.equal(Number(summary.getRange('B4').values[0][0]),sources.Order.count+1);
sourceSheet.getRange(`A${newRow}:J${newRow}`).clear({applyTo:'contents'});wb.recalculate();assert.equal(Number(summary.getRange('B4').values[0][0]),sources.Order.count);
await fs.mkdir(path.join(root,'screenshots'),{recursive:true});
for(const [sheetName,range,name] of [['01_orders_raw','A1:J13','01_raw_data'],['04_checks','A1:K14','02_error_check'],['05_errors','A1:G19','03_error_registry'],['06_summary','A1:H19','04_summary_report'],['07_dashboard','A1:R23','05_dashboard'],['08_action_plan','A1:F8','06_action_plan']]){
 const blob=await wb.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(path.join(root,`screenshots/${name}.png`),new Uint8Array(await blob.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(root,'result/data_quality_report.xlsx'));
const metrics={records:sources.Order.count+sources.Client.count+sources.Payment.count,events:total,bad_record_share:Number(summary.getRange('B9').values[0][0]),high:Number(summary.getRange('H7').values[0][0]),cutoff:'2026-06-25',registry_capacity:registryCapacity,checks:'missing manager and appended order mutation tests passed'};
await fs.writeFile(path.join(root,'result/validation_summary.json'),JSON.stringify(metrics,null,2)+'\n');
console.log(metrics);
