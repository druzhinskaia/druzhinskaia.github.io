import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const rootDir = process.cwd();
const projectDir = path.join(rootDir, "portfolio-projects/01-data-quality-excel-reporting");
const rawDir = path.join(projectDir, "data/raw");
const processedDir = path.join(projectDir, "data/processed");
const docsDir = path.join(projectDir, "docs");
const resultDir = path.join(projectDir, "result");
const screenshotsDir = path.join(projectDir, "screenshots");
const outputDir = path.join(rootDir, "outputs/data-quality-excel-reporting");

const COLORS = {
  navy: "#1F4E78",
  blue: "#5B9BD5",
  lightBlue: "#DDEBF7",
  green: "#70AD47",
  lightGreen: "#E2F0D9",
  orange: "#F4B183",
  lightOrange: "#FCE4D6",
  red: "#C00000",
  lightRed: "#F4CCCC",
  gray: "#F2F2F2",
  darkGray: "#595959",
  white: "#FFFFFF",
  border: "#D9E2F3",
};

const managers = ["Иванова", "Петрова", "Сидорова", "Кузнецова", "Смирнова", "Орлова"];
const cities = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Краснодар", "Самара"];
const categories = {
  "Ноутбуки": ["Lenovo IdeaPad", "ASUS VivoBook", "HP Pavilion", "Acer Aspire"],
  "Мониторы": ["Samsung 27", "LG UltraFine", "AOC 24", "Dell P2422H"],
  "Периферия": ["Logitech Mouse", "Keychron K2", "Canon Scanner", "Jabra Headset"],
  "ПО": ["CRM License", "Office Suite", "Antivirus Pro", "BI Connector"],
  "Сервис": ["Setup Service", "Maintenance Pack", "Training Session", "Data Migration"],
};
const statuses = ["Выполнен", "В работе", "Отменен", "Ожидает оплаты"];
const paymentStatuses = ["Оплачено", "Частично оплачено", "Не оплачено"];

function seededRandom(seed) {
  let value = seed;
  return () => {
    value = (value * 1664525 + 1013904223) % 4294967296;
    return value / 4294967296;
  };
}

const random = seededRandom(20260625);
const pick = (arr) => arr[Math.floor(random() * arr.length)];
const pad = (n, size = 3) => String(n).padStart(size, "0");
const date = (y, m, d) => new Date(Date.UTC(y, m - 1, d));
const addDays = (base, days) => new Date(base.getTime() + days * 86400000);

function makeInn(i, invalid = false) {
  if (invalid) return `77${pad(i, 6)}`;
  return `77${pad(i, 8)}`;
}

function buildData() {
  const clients = [];
  for (let i = 1; i <= 45; i++) {
    clients.push({
      client_id: `C${pad(i)}`,
      client_name: `Клиент ${pad(i)}`,
      inn: makeInn(i),
      city: pick(cities),
      registration_date: addDays(date(2024, 1, 1), Math.floor(random() * 720)),
      client_segment: pick(["B2B", "B2C", "Enterprise", "SMB"]),
    });
  }

  clients[4].inn = "";
  clients[11].inn = makeInn(12, true);
  clients[17].city = "";
  clients[24].registration_date = "";
  clients.push({ ...clients[8], client_name: "Клиент 009 дубль" });

  const orders = [];
  for (let i = 1; i <= 160; i++) {
    const category = pick(Object.keys(categories));
    const product = pick(categories[category]);
    const quantity = 1 + Math.floor(random() * 6);
    const price = [4500, 8900, 12000, 24000, 39000, 55000, 72000][Math.floor(random() * 7)];
    const orderDate = addDays(date(2026, 1, 5), Math.floor(random() * 150));
    orders.push({
      order_id: 1000 + i,
      order_date: orderDate,
      client_id: `C${pad(1 + Math.floor(random() * 45))}`,
      manager: pick(managers),
      product_category: category,
      product_name: product,
      quantity,
      price,
      order_sum: quantity * price,
      status: pick(statuses),
    });
  }

  orders[7].order_id = orders[6].order_id;
  orders[15].client_id = "";
  orders[28].manager = "";
  orders[39].order_sum = orders[39].quantity * orders[39].price + 5000;
  orders[52].price = -12000;
  orders[52].order_sum = orders[52].quantity * orders[52].price;
  orders[73].order_date = date(2027, 2, 10);
  orders[91].status = "Выполен";
  orders[116].client_id = "C999";
  orders[130].order_sum = "";

  const payments = [];
  for (let i = 1; i <= 120; i++) {
    const order = orders[Math.floor(random() * orders.length)];
    const orderSum = Number(order.order_sum) || Math.max(0, order.quantity * Math.abs(order.price));
    const status = pick(paymentStatuses);
    let paymentSum = status === "Оплачено" ? orderSum : status === "Частично оплачено" ? Math.round(orderSum * (0.25 + random() * 0.5)) : 0;
    payments.push({
      payment_id: `P${pad(i)}`,
      order_id: order.order_id,
      payment_date: addDays(order.order_date instanceof Date ? order.order_date : date(2026, 1, 1), 1 + Math.floor(random() * 20)),
      payment_sum: paymentSum,
      payment_status: status,
    });
  }

  payments[9].order_id = 9999;
  payments[18].payment_sum = 999999;
  payments[26].payment_status = "";
  payments[37].payment_date = addDays(orders[20].order_date, -4);
  payments[37].order_id = orders[20].order_id;

  return { clients, orders, payments };
}

function aoaFromObjects(rows, headers) {
  return [headers, ...rows.map((row) => headers.map((header) => row[header] ?? ""))];
}

function errorCriticality(errorType) {
  if (["Нет связи", "Ошибка расчета", "Отрицательная цена", "Дата", "Статус"].includes(errorType)) return "High";
  if (errorType === "Пустое поле") return "Medium";
  return "Low";
}

function errorRecommendation(errorType) {
  const map = {
    "Дубль": "Проверить источник дубля и оставить одну корректную запись.",
    "Пустое поле": "Заполнить обязательное поле или вернуть запись ответственному.",
    "Нет связи": "Проверить справочник и восстановить связь между таблицами.",
    "Ошибка расчета": "Пересчитать сумму и сверить количество, цену и оплату.",
    "Отрицательная цена": "Проверить цену в первичной системе.",
    "Дата": "Проверить дату документа и порядок событий.",
    "Статус": "Исправить значение по утвержденному справочнику статусов.",
  };
  return map[errorType] || "Проверить запись вручную.";
}

function buildCompactErrors(data) {
  const { orders, clients, payments } = data;
  const errors = [];
  const orderIds = orders.map((row) => row.order_id);
  const clientIds = clients.map((row) => row.client_id);
  const clientSet = new Set(clientIds);
  const orderSet = new Set(orderIds);
  const orderById = new Map(orders.map((row) => [row.order_id, row]));
  const count = (arr, value) => arr.filter((item) => item === value).length;
  const add = (entity, recordId, sourceRow, errorType, sourceField) => {
    errors.push([
      entity,
      recordId,
      sourceRow,
      errorType,
      errorCriticality(errorType),
      sourceField,
      errorRecommendation(errorType),
    ]);
  };

  for (let i = 0; i < orders.length; i++) {
    const order = orders[i];
    const sourceRow = i + 2;
    if (count(orderIds, order.order_id) > 1) add("Order", order.order_id, sourceRow, "Дубль", "order_id");
    if (order.client_id === "" || order.manager === "") add("Order", order.order_id, sourceRow, "Пустое поле", order.client_id === "" ? "client_id" : "manager");
    if (!clientSet.has(order.client_id)) add("Order", order.order_id, sourceRow, "Нет связи", "client_id");
    if (order.order_sum !== order.quantity * order.price) add("Order", order.order_id, sourceRow, "Ошибка расчета", "order_sum");
    if (order.price < 0) add("Order", order.order_id, sourceRow, "Отрицательная цена", "price");
    if (order.order_date > date(2026, 6, 25)) add("Order", order.order_id, sourceRow, "Дата", "order_date");
    if (!statuses.includes(order.status)) add("Order", order.order_id, sourceRow, "Статус", "status");
  }

  for (let i = 0; i < clients.length; i++) {
    const client = clients[i];
    const sourceRow = i + 2;
    if (count(clientIds, client.client_id) > 1) add("Client", client.client_id, sourceRow, "Дубль", "client_id");
    if (client.inn === "" || client.city === "" || client.registration_date === "") {
      add("Client", client.client_id, sourceRow, "Пустое поле", client.inn === "" ? "inn" : client.city === "" ? "city" : "registration_date");
    }
    if (client.inn !== "" && String(client.inn).length !== 10) add("Client", client.client_id, sourceRow, "Ошибка расчета", "inn");
  }

  for (let i = 0; i < payments.length; i++) {
    const payment = payments[i];
    const sourceRow = i + 2;
    const order = orderById.get(payment.order_id);
    if (payment.order_id === "" || payment.payment_status === "") add("Payment", payment.payment_id, sourceRow, "Пустое поле", payment.order_id === "" ? "order_id" : "payment_status");
    if (!orderSet.has(payment.order_id)) add("Payment", payment.payment_id, sourceRow, "Нет связи", "order_id");
    if (!order || payment.payment_sum > order.order_sum) add("Payment", payment.payment_id, sourceRow, "Ошибка расчета", "payment_sum");
    if (!order || payment.payment_date < order.order_date) add("Payment", payment.payment_id, sourceRow, "Дата", "payment_date");
    if (!paymentStatuses.includes(payment.payment_status)) add("Payment", payment.payment_id, sourceRow, "Статус", "payment_status");
  }

  return errors;
}

function col(n) {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - m) / 26);
  }
  return s;
}

function styleTitle(sheet, range, title) {
  range.merge();
  range.values = [[title]];
  range.format.fill.color = COLORS.navy;
  range.format.font.color = COLORS.white;
  range.format.font.bold = true;
  range.format.font.size = 16;
  range.format.horizontalAlignment = "center";
  range.format.verticalAlignment = "center";
  range.format.rowHeight = 30;
  sheet.showGridLines = false;
}

function styleHeader(range) {
  range.format.fill.color = COLORS.navy;
  range.format.font.color = COLORS.white;
  range.format.font.bold = true;
  range.format.wrapText = true;
  range.format.horizontalAlignment = "center";
  range.format.verticalAlignment = "center";
}

function styleTableRange(range) {
  range.format.borders = { preset: "all", style: "thin", color: COLORS.border };
  range.format.verticalAlignment = "center";
}

function setColWidths(sheet, widths) {
  widths.forEach((width, idx) => {
    sheet.getRange(`${col(idx + 1)}:${col(idx + 1)}`).format.columnWidth = width;
  });
}

function addExcelTable(sheet, rangeAddress, name, style = "TableStyleMedium2") {
  const table = sheet.tables.add(rangeAddress, true, name);
  table.style = style;
  table.showFilterButton = true;
  return table;
}

async function saveWorkbook(workbook, filePath) {
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(filePath);
}

async function buildRawWorkbook(filePath, sheetName, rows, headers, tableName) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;
  const values = aoaFromObjects(rows, headers);
  sheet.getRangeByIndexes(0, 0, values.length, headers.length).values = values;
  styleHeader(sheet.getRangeByIndexes(0, 0, 1, headers.length));
  styleTableRange(sheet.getRangeByIndexes(0, 0, values.length, headers.length));
  addExcelTable(sheet, `A1:${col(headers.length)}${values.length}`, tableName);
  sheet.freezePanes.freezeRows(1);
  sheet.getRangeByIndexes(0, 0, values.length, headers.length).format.autofitColumns();
  await saveWorkbook(workbook, filePath);
}

function buildReportWorkbook(data) {
  const { orders, clients, payments } = data;
  const workbook = Workbook.create();

  const ordersSheet = workbook.worksheets.add("01_orders_raw");
  const clientsSheet = workbook.worksheets.add("02_clients_raw");
  const paymentsSheet = workbook.worksheets.add("03_payments_raw");
  const checksSheet = workbook.worksheets.add("04_checks");
  const errorsSheet = workbook.worksheets.add("05_errors");
  const summarySheet = workbook.worksheets.add("06_summary");
  const dashboardSheet = workbook.worksheets.add("07_dashboard");
  const actionSheet = workbook.worksheets.add("08_action_plan");
  const compactErrors = buildCompactErrors(data);

  const orderHeaders = ["order_id", "order_date", "client_id", "manager", "product_category", "product_name", "quantity", "price", "order_sum", "status"];
  const clientHeaders = ["client_id", "client_name", "inn", "city", "registration_date", "client_segment"];
  const paymentHeaders = ["payment_id", "order_id", "payment_date", "payment_sum", "payment_status"];

  const orderValues = aoaFromObjects(orders, orderHeaders);
  ordersSheet.getRangeByIndexes(0, 0, orderValues.length, orderHeaders.length).values = orderValues;
  styleHeader(ordersSheet.getRange("A1:J1"));
  styleTableRange(ordersSheet.getRange(`A1:J${orderValues.length}`));
  addExcelTable(ordersSheet, `A1:J${orderValues.length}`, "tbl_orders");
  setColWidths(ordersSheet, [11, 13, 11, 14, 18, 21, 11, 12, 14, 16]);
  ordersSheet.getRange(`B2:B${orderValues.length}`).setNumberFormat("yyyy-mm-dd");
  ordersSheet.getRange(`G2:I${orderValues.length}`).setNumberFormat("#,##0");
  ordersSheet.freezePanes.freezeRows(1);
  ordersSheet.showGridLines = false;

  const clientValues = aoaFromObjects(clients, clientHeaders);
  clientsSheet.getRangeByIndexes(0, 0, clientValues.length, clientHeaders.length).values = clientValues;
  styleHeader(clientsSheet.getRange("A1:F1"));
  styleTableRange(clientsSheet.getRange(`A1:F${clientValues.length}`));
  addExcelTable(clientsSheet, `A1:F${clientValues.length}`, "tbl_clients");
  setColWidths(clientsSheet, [12, 20, 15, 18, 17, 16]);
  clientsSheet.getRange(`E2:E${clientValues.length}`).setNumberFormat("yyyy-mm-dd");
  clientsSheet.freezePanes.freezeRows(1);
  clientsSheet.showGridLines = false;

  const paymentValues = aoaFromObjects(payments, paymentHeaders);
  paymentsSheet.getRangeByIndexes(0, 0, paymentValues.length, paymentHeaders.length).values = paymentValues;
  styleHeader(paymentsSheet.getRange("A1:E1"));
  styleTableRange(paymentsSheet.getRange(`A1:E${paymentValues.length}`));
  addExcelTable(paymentsSheet, `A1:E${paymentValues.length}`, "tbl_payments");
  setColWidths(paymentsSheet, [12, 12, 15, 15, 20]);
  paymentsSheet.getRange(`C2:C${paymentValues.length}`).setNumberFormat("yyyy-mm-dd");
  paymentsSheet.getRange(`D2:D${paymentValues.length}`).setNumberFormat("#,##0");
  paymentsSheet.freezePanes.freezeRows(1);
  paymentsSheet.showGridLines = false;

  const checkHeaders = [
    "entity",
    "record_id",
    "check_duplicate_id",
    "check_empty_required",
    "check_reference_exists",
    "check_calculation",
    "check_negative_price",
    "check_future_date",
    "check_status",
    "error_count",
    "comment",
  ];
  checksSheet.getRange("A1:K1").values = [checkHeaders];
  styleHeader(checksSheet.getRange("A1:K1"));
  styleTableRange(checksSheet.getRange(`A1:K${orders.length + clients.length + payments.length + 1}`));
  checksSheet.showGridLines = false;
  checksSheet.freezePanes.freezeRows(1);
  setColWidths(checksSheet, [12, 12, 18, 20, 22, 18, 18, 16, 15, 12, 38]);

  const checkRows = [];
  for (let i = 0; i < orders.length; i++) {
    const r = i + 2;
    checkRows.push([
      `="Order"`,
      `='01_orders_raw'!A${r}`,
      `=IF(COUNTIF('01_orders_raw'!$A$2:$A$${orders.length + 1},'01_orders_raw'!A${r})>1,"ERROR","OK")`,
      `=IF(OR('01_orders_raw'!C${r}="",'01_orders_raw'!D${r}=""),"ERROR","OK")`,
      `=IF(COUNTIF('02_clients_raw'!$A$2:$A$${clients.length + 1},'01_orders_raw'!C${r})=0,"ERROR","OK")`,
      `=IF('01_orders_raw'!I${r}<>'01_orders_raw'!G${r}*'01_orders_raw'!H${r},"ERROR","OK")`,
      `=IF('01_orders_raw'!H${r}<0,"ERROR","OK")`,
      `=IF('01_orders_raw'!B${r}>DATE(2026,6,25),"ERROR","OK")`,
      `=IF(OR('01_orders_raw'!J${r}="Выполнен",'01_orders_raw'!J${r}="В работе",'01_orders_raw'!J${r}="Отменен",'01_orders_raw'!J${r}="Ожидает оплаты"),"OK","ERROR")`,
      `=COUNTIF(C${checkRows.length + 2}:I${checkRows.length + 2},"ERROR")`,
      `=IF(J${checkRows.length + 2}>0,"Проверить заказ","")`,
    ]);
  }
  for (let i = 0; i < clients.length; i++) {
    const r = i + 2;
    checkRows.push([
      `="Client"`,
      `='02_clients_raw'!A${r}`,
      `=IF(COUNTIF('02_clients_raw'!$A$2:$A$${clients.length + 1},'02_clients_raw'!A${r})>1,"ERROR","OK")`,
      `=IF(OR('02_clients_raw'!C${r}="",'02_clients_raw'!D${r}="",'02_clients_raw'!E${r}=""),"ERROR","OK")`,
      `="OK"`,
      `=IF(AND('02_clients_raw'!C${r}<>"",LEN('02_clients_raw'!C${r})<>10),"ERROR","OK")`,
      `="OK"`,
      `="OK"`,
      `="OK"`,
      `=COUNTIF(C${checkRows.length + 2}:I${checkRows.length + 2},"ERROR")`,
      `=IF(J${checkRows.length + 2}>0,"Проверить клиента","")`,
    ]);
  }
  for (let i = 0; i < payments.length; i++) {
    const r = i + 2;
    checkRows.push([
      `="Payment"`,
      `='03_payments_raw'!A${r}`,
      `="OK"`,
      `=IF(OR('03_payments_raw'!B${r}="",'03_payments_raw'!E${r}=""),"ERROR","OK")`,
      `=IF(COUNTIF('01_orders_raw'!$A$2:$A$${orders.length + 1},'03_payments_raw'!B${r})=0,"ERROR","OK")`,
      `=IFERROR(IF('03_payments_raw'!D${r}>INDEX('01_orders_raw'!$I$2:$I$${orders.length + 1},MATCH('03_payments_raw'!B${r},'01_orders_raw'!$A$2:$A$${orders.length + 1},0)),"ERROR","OK"),"ERROR")`,
      `="OK"`,
      `=IFERROR(IF('03_payments_raw'!C${r}<INDEX('01_orders_raw'!$B$2:$B$${orders.length + 1},MATCH('03_payments_raw'!B${r},'01_orders_raw'!$A$2:$A$${orders.length + 1},0)),"ERROR","OK"),"ERROR")`,
      `=IF(OR('03_payments_raw'!E${r}="Оплачено",'03_payments_raw'!E${r}="Частично оплачено",'03_payments_raw'!E${r}="Не оплачено"),"OK","ERROR")`,
      `=COUNTIF(C${checkRows.length + 2}:I${checkRows.length + 2},"ERROR")`,
      `=IF(J${checkRows.length + 2}>0,"Проверить оплату","")`,
    ]);
  }
  checksSheet.getRangeByIndexes(1, 0, checkRows.length, checkHeaders.length).formulas = checkRows;
  checksSheet.getRange(`C2:I${checkRows.length + 1}`).format.fill.color = COLORS.lightGreen;
  checksSheet.getRange(`C2:I${checkRows.length + 1}`).format.font.color = "#000000";
  checksSheet.getRange(`C2:I${checkRows.length + 1}`).conditionalFormats.add("containsText", {
    text: "ERROR",
    format: { fill: { color: COLORS.lightRed }, font: { color: COLORS.red, bold: true } },
  });
  checksSheet.getRange(`J2:J${checkRows.length + 1}`).conditionalFormats.add("cellIs", {
    operator: "greaterThan",
    formula: 0,
    format: { fill: { color: COLORS.lightOrange }, font: { bold: true } },
  });

  const errorHeaders = ["entity", "record_id", "source_row", "error_type", "criticality", "source_field", "recommendation"];
  errorsSheet.getRange("A1:G1").values = [errorHeaders];
  styleHeader(errorsSheet.getRange("A1:G1"));
  errorsSheet.getRangeByIndexes(1, 0, compactErrors.length, errorHeaders.length).values = compactErrors;
  styleTableRange(errorsSheet.getRange(`A1:G${compactErrors.length + 1}`));
  addExcelTable(errorsSheet, `A1:G${compactErrors.length + 1}`, "tbl_errors", "TableStyleLight1");
  setColWidths(errorsSheet, [14, 14, 12, 20, 13, 18, 62]);
  errorsSheet.getRange(`G2:G${compactErrors.length + 1}`).format.wrapText = true;
  errorsSheet.freezePanes.freezeRows(1);
  errorsSheet.showGridLines = false;
  errorsSheet.getRange(`E2:E${compactErrors.length + 1}`).format.font.bold = true;

  styleTitle(summarySheet, summarySheet.getRange("A1:H1"), "Сводка по качеству данных и отчетности");
  summarySheet.getRange("A3:B9").values = [
    ["Показатель", "Значение"],
    ["Всего заказов", ""],
    ["Сумма заказов", ""],
    ["Всего клиентов", ""],
    ["Всего оплат", ""],
    ["Всего найдено ошибок", ""],
    ["Доля записей с ошибками", ""],
  ];
  summarySheet.getRange("B4:B9").formulas = [
    [`=COUNTA('01_orders_raw'!$A$2:$A$${orders.length + 1})`],
    [`=SUM('01_orders_raw'!$I$2:$I$${orders.length + 1})`],
    [`=COUNTA('02_clients_raw'!$A$2:$A$${clients.length + 1})`],
    [`=COUNTA('03_payments_raw'!$A$2:$A$${payments.length + 1})`],
    [`=COUNTA('05_errors'!$A$2:$A$${compactErrors.length + 1})`],
    [`=COUNTIF('04_checks'!$J$2:$J$${checkRows.length + 1},">0")/COUNTA('04_checks'!$A$2:$A$${checkRows.length + 1})`],
  ];
  styleHeader(summarySheet.getRange("A3:B3"));
  styleTableRange(summarySheet.getRange("A3:B9"));
  summarySheet.getRange("B5").setNumberFormat("#,##0");
  summarySheet.getRange("B9").setNumberFormat("0.0%");

  summarySheet.getRange("D3:E6").values = [
    ["Статус", "Количество заказов"],
    ["Выполнен", ""],
    ["В работе", ""],
    ["Ожидает оплаты", ""],
  ];
  summarySheet.getRange("E4:E6").formulas = [
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},D4)`],
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},D5)`],
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},D6)`],
  ];
  styleHeader(summarySheet.getRange("D3:E3"));
  styleTableRange(summarySheet.getRange("D3:E6"));

  summarySheet.getRange("D8:E16").values = [
    ["Тип ошибки", "Количество"],
    ["Дубли", ""],
    ["Пустые обязательные поля", ""],
    ["Нет связи со справочником", ""],
    ["Ошибка расчета", ""],
    ["Отрицательная цена", ""],
    ["Дата", ""],
    ["Статус", ""],
    ["Итого", ""],
  ];
  summarySheet.getRange("E9:E16").formulas = [
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Дубль")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Пустое поле")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Нет связи")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Ошибка расчета")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Отрицательная цена")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Дата")`],
    [`=COUNTIF('05_errors'!$D$2:$D$${compactErrors.length + 1},"Статус")`],
    [`=SUM(E9:E15)`],
  ];
  styleHeader(summarySheet.getRange("D8:E8"));
  styleTableRange(summarySheet.getRange("D8:E16"));

  summarySheet.getRange("A12:B17").values = [
    ["Месяц", "Сумма заказов"],
    ["Январь", ""],
    ["Февраль", ""],
    ["Март", ""],
    ["Апрель", ""],
    ["Май", ""],
  ];
  const monthNums = [1, 2, 3, 4, 5];
  summarySheet.getRange("B13:B17").formulas = monthNums.map((month) => [
    `=SUMIFS('01_orders_raw'!$I$2:$I$${orders.length + 1},'01_orders_raw'!$B$2:$B$${orders.length + 1},">="&DATE(2026,${month},1),'01_orders_raw'!$B$2:$B$${orders.length + 1},"<"&DATE(2026,${month + 1},1))`,
  ]);
  styleHeader(summarySheet.getRange("A12:B12"));
  styleTableRange(summarySheet.getRange("A12:B17"));
  summarySheet.getRange("B13:B17").setNumberFormat("#,##0");

  summarySheet.getRange("D19:E25").values = [["Менеджер", "Сумма заказов"], ...managers.map((m) => [m, ""])];
  summarySheet.getRange(`E20:E${19 + managers.length}`).formulas = managers.map((_, i) => [
    `=SUMIF('01_orders_raw'!$D$2:$D$${orders.length + 1},D${20 + i},'01_orders_raw'!$I$2:$I$${orders.length + 1})`,
  ]);
  styleHeader(summarySheet.getRange("D19:E19"));
  styleTableRange(summarySheet.getRange(`D19:E${19 + managers.length}`));
  summarySheet.getRange(`E20:E${19 + managers.length}`).setNumberFormat("#,##0");
  summarySheet.getRange("G3:H7").values = [
    ["Объект", "Количество ошибок"],
    ["Order", ""],
    ["Client", ""],
    ["Payment", ""],
    ["High criticality", ""],
  ];
  summarySheet.getRange("H4:H7").formulas = [
    [`=COUNTIF('05_errors'!$A$2:$A$${compactErrors.length + 1},G4)`],
    [`=COUNTIF('05_errors'!$A$2:$A$${compactErrors.length + 1},G5)`],
    [`=COUNTIF('05_errors'!$A$2:$A$${compactErrors.length + 1},G6)`],
    [`=COUNTIF('05_errors'!$E$2:$E$${compactErrors.length + 1},"High")`],
  ];
  styleHeader(summarySheet.getRange("G3:H3"));
  styleTableRange(summarySheet.getRange("G3:H7"));
  setColWidths(summarySheet, [26, 16, 4, 24, 16, 4, 18, 18]);
  summarySheet.showGridLines = false;

  styleTitle(dashboardSheet, dashboardSheet.getRange("A1:N1"), "Дашборд: контроль качества данных из 1С");
  dashboardSheet.getRange("A3:B6").values = [["Сумма заказов", ""], ["Количество заказов", ""], ["Количество ошибок", ""], ["Критичные ошибки", ""]];
  dashboardSheet.getRange("D3:E6").values = [["Клиенты", ""], ["Оплаты", ""], ["Доля записей с ошибками", ""], ["Главный риск", ""]];
  dashboardSheet.getRange("B3:B5").formulas = [["='06_summary'!B5"], ["='06_summary'!B4"], ["='06_summary'!B8"]];
  dashboardSheet.getRange("B6").formulas = [[`='06_summary'!H7`]];
  dashboardSheet.getRange("E3:E6").formulas = [["='06_summary'!B6"], ["='06_summary'!B7"], ["='06_summary'!B9"], [`="Расчеты и связи"`]];
  dashboardSheet.getRange("A3:E6").format.fill.color = COLORS.lightBlue;
  dashboardSheet.getRange("A3:E6").format.borders = { preset: "all", style: "thin", color: COLORS.border };
  dashboardSheet.getRange("A3:A6").format.font.bold = true;
  dashboardSheet.getRange("D3:D6").format.font.bold = true;
  dashboardSheet.getRange("B3").setNumberFormat("#,##0");
  dashboardSheet.getRange("E5").setNumberFormat("0.0%");

  dashboardSheet.getRange("A8:B13").values = [["Месяц", "Сумма заказов"], ["Январь", ""], ["Февраль", ""], ["Март", ""], ["Апрель", ""], ["Май", ""]];
  dashboardSheet.getRange("B9:B13").formulas = [["='06_summary'!B13"], ["='06_summary'!B14"], ["='06_summary'!B15"], ["='06_summary'!B16"], ["='06_summary'!B17"]];
  dashboardSheet.getRange("D8:E15").values = [["Тип ошибки", "Количество"], ["Дубли", ""], ["Пустые поля", ""], ["Нет связи", ""], ["Ошибка расчета", ""], ["Отрицательная цена", ""], ["Дата", ""], ["Статус", ""]];
  dashboardSheet.getRange("E9:E15").formulas = [["='06_summary'!E9"], ["='06_summary'!E10"], ["='06_summary'!E11"], ["='06_summary'!E12"], ["='06_summary'!E13"], ["='06_summary'!E14"], ["='06_summary'!E15"]];
  dashboardSheet.getRange("G8:H13").values = [["Статус", "Количество"], ["Выполнен", ""], ["В работе", ""], ["Ожидает оплаты", ""], ["Отменен", ""], ["Опечатка/прочее", ""]];
  dashboardSheet.getRange("H9:H13").formulas = [
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},G9)`],
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},G10)`],
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},G11)`],
    [`=COUNTIF('01_orders_raw'!$J$2:$J$${orders.length + 1},G12)`],
    [`=COUNTA('01_orders_raw'!$J$2:$J$${orders.length + 1})-SUM(H9:H12)`],
  ];
  styleHeader(dashboardSheet.getRange("A8:B8"));
  styleHeader(dashboardSheet.getRange("D8:E8"));
  styleHeader(dashboardSheet.getRange("G8:H8"));
  styleTableRange(dashboardSheet.getRange("A8:B13"));
  styleTableRange(dashboardSheet.getRange("D8:E15"));
  styleTableRange(dashboardSheet.getRange("G8:H13"));
  dashboardSheet.getRange("B9:B13").setNumberFormat("#,##0");
  setColWidths(dashboardSheet, [17, 16, 3, 19, 20, 3, 19, 14, 3, 14, 14, 14, 14, 14]);
  dashboardSheet.showGridLines = false;

  const salesChart = dashboardSheet.charts.add("line", dashboardSheet.getRange("A8:B13"));
  salesChart.setPosition("J3", "N14");
  salesChart.title = "Сумма заказов по месяцам";
  salesChart.hasLegend = false;

  dashboardSheet.getRange("A31:B35").values = [["Объект", "Количество ошибок"], ["Order", ""], ["Client", ""], ["Payment", ""], ["High", ""]];
  dashboardSheet.getRange("B32:B35").formulas = [["='06_summary'!H4"], ["='06_summary'!H5"], ["='06_summary'!H6"], ["='06_summary'!H7"]];
  styleHeader(dashboardSheet.getRange("A31:B31"));
  styleTableRange(dashboardSheet.getRange("A31:B35"));

  const errorChart = dashboardSheet.charts.add("bar", dashboardSheet.getRange("D8:E15"));
  errorChart.setPosition("A16", "F30");
  errorChart.title = "Ошибки по типам";
  errorChart.hasLegend = false;

  const statusChart = dashboardSheet.charts.add("column", dashboardSheet.getRange("G8:H13"));
  statusChart.setPosition("H16", "N30");
  statusChart.title = "Статусы заказов";
  statusChart.hasLegend = false;

  const entityChart = dashboardSheet.charts.add("column", dashboardSheet.getRange("A31:B34"));
  entityChart.setPosition("J31", "N43");
  entityChart.title = "Ошибки по объектам";
  entityChart.hasLegend = false;

  styleTitle(actionSheet, actionSheet.getRange("A1:F1"), "План действий по исправлению ошибок");
  const actionRows = [
    ["Приоритет", "Проблема", "Действие", "Ответственный", "Ожидаемый эффект", "Статус"],
    ["High", "Нет связи между таблицами", "Проверить отсутствующие client_id/order_id и обновить справочники", "Аналитик + владелец 1С", "Корректные связи в отчетности", "Запланировано"],
    ["High", "Ошибки расчета", "Сверить суммы заказов и оплат с первичными документами", "Аналитик", "Снижение риска неверных финансовых показателей", "Запланировано"],
    ["High", "Некорректные даты и статусы", "Исправить даты документов и статусы по справочнику", "Операционная команда", "Корректная динамика и воронка заказов", "Запланировано"],
    ["Medium", "Пустые обязательные поля", "Вернуть записи на дозаполнение ответственным", "Менеджеры", "Полная карточка клиента/заказа", "Запланировано"],
    ["Low", "Дубли", "Определить актуальную запись и удалить или объединить дубль", "Аналитик", "Чистые справочники и отсутствие двойного учета", "Запланировано"],
  ];
  actionSheet.getRangeByIndexes(2, 0, actionRows.length, actionRows[0].length).values = actionRows;
  styleHeader(actionSheet.getRange("A3:F3"));
  styleTableRange(actionSheet.getRange(`A3:F${2 + actionRows.length}`));
  addExcelTable(actionSheet, `A3:F${2 + actionRows.length}`, "tbl_action_plan", "TableStyleLight1");
  setColWidths(actionSheet, [12, 28, 48, 24, 38, 18]);
  actionSheet.getRange(`C4:E${2 + actionRows.length}`).format.wrapText = true;
  actionSheet.showGridLines = false;
  actionSheet.freezePanes.freezeRows(3);

  return workbook;
}

async function renderProjectScreenshots(workbook) {
  const shots = [
    { sheetName: "01_orders_raw", range: "A1:J20", file: "01_raw_data.png" },
    { sheetName: "04_checks", range: "A1:K25", file: "02_error_check.png" },
    { sheetName: "05_errors", range: "A1:G30", file: "03_error_registry.png" },
    { sheetName: "06_summary", range: "A1:H26", file: "04_summary_report.png" },
    { sheetName: "07_dashboard", range: "A1:N43", file: "05_dashboard.png" },
    { sheetName: "08_action_plan", range: "A1:F9", file: "06_action_plan.png" },
  ];
  for (const shot of shots) {
    const blob = await workbook.render({ sheetName: shot.sheetName, range: shot.range, scale: 1.5, format: "png" });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    await fs.writeFile(path.join(screenshotsDir, shot.file), bytes);
  }
}

async function removeInspectFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  await Promise.all(entries.map(async (entry) => {
    const itemPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await removeInspectFiles(itemPath);
    } else if (entry.name.endsWith(".inspect.ndjson")) {
      await fs.rm(itemPath, { force: true });
    }
  }));
}

async function main() {
  await Promise.all([rawDir, processedDir, docsDir, resultDir, screenshotsDir, outputDir].map((dir) => fs.mkdir(dir, { recursive: true })));

  const data = buildData();
  await buildRawWorkbook(path.join(rawDir, "orders_raw.xlsx"), "orders_raw", data.orders, ["order_id", "order_date", "client_id", "manager", "product_category", "product_name", "quantity", "price", "order_sum", "status"], "tbl_orders_raw");
  await buildRawWorkbook(path.join(rawDir, "clients_raw.xlsx"), "clients_raw", data.clients, ["client_id", "client_name", "inn", "city", "registration_date", "client_segment"], "tbl_clients_raw");
  await buildRawWorkbook(path.join(rawDir, "payments_raw.xlsx"), "payments_raw", data.payments, ["payment_id", "order_id", "payment_date", "payment_sum", "payment_status"], "tbl_payments_raw");

  const report = buildReportWorkbook(data);
  const finalPath = path.join(resultDir, "data_quality_report.xlsx");
  const outputPath = path.join(outputDir, "data_quality_report.xlsx");
  await saveWorkbook(report, finalPath);
  await saveWorkbook(report, outputPath);
  await renderProjectScreenshots(report);

  const errors = await report.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
    maxChars: 4000,
  });
  console.log(errors.ndjson);

  const dashboard = await report.inspect({
    kind: "table",
    range: "07_dashboard!A1:N29",
    include: "values,formulas",
    tableMaxRows: 20,
    tableMaxCols: 14,
    maxChars: 6000,
  });
  console.log(dashboard.ndjson);
  await removeInspectFiles(projectDir);
  await removeInspectFiles(outputDir);
  console.log(JSON.stringify({ finalPath, outputPath }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
