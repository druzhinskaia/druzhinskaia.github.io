import fs from "node:fs/promises";
import path from "node:path";

const rootDir = process.cwd();
const projectDir = path.join(rootDir, "portfolio-projects/02-bpmn-1c-requirements");
const bpmnDir = path.join(projectDir, "03-bpmn");

const COLORS = {
  navy: "#1F4E78",
  lane: "#F7FAFC",
  laneAlt: "#EEF4FA",
  border: "#B7C9DA",
  green: "#D9EAD3",
  greenBorder: "#70AD47",
  blue: "#DDEBF7",
  blueBorder: "#5B9BD5",
  orange: "#FCE4D6",
  orangeBorder: "#F4B183",
  red: "#F4CCCC",
  redBorder: "#C00000",
  gray: "#F2F2F2",
  text: "#1F2933",
};

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function drawioCell(id, value, style, x, y, width, height, parent = "1") {
  return `    <mxCell id="${id}" value="${esc(value)}" style="${style}" vertex="1" parent="${parent}">
      <mxGeometry x="${x}" y="${y}" width="${width}" height="${height}" as="geometry" />
    </mxCell>`;
}

function edgeSideStyle(edge) {
  const sides = {
    left: { x: 0, y: 0.5 },
    right: { x: 1, y: 0.5 },
    top: { x: 0.5, y: 0 },
    bottom: { x: 0.5, y: 1 },
  };
  const exit = sides[edge.start || "right"];
  const entry = sides[edge.end || "left"];
  return `exitX=${exit.x};exitY=${exit.y};entryX=${entry.x};entryY=${entry.y};`;
}

function drawioEdge(id, edge) {
  const waypoints = edge.points?.length
    ? `
        <Array as="points">
${edge.points.map((point) => `          <mxPoint x="${point.x}" y="${point.y}" />`).join("\n")}
        </Array>`
    : "";
  return `    <mxCell id="${id}" value="${esc(edge.label || "")}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;${edgeSideStyle(edge)}strokeColor=${COLORS.navy};strokeWidth=2;endArrow=block;endFill=1;" edge="1" parent="1" source="${edge.from}" target="${edge.to}">
      <mxGeometry relative="1" as="geometry">${waypoints}
      </mxGeometry>
    </mxCell>`;
}

function drawioDiagram(name, width, height, lanes, nodes, edges) {
  const laneCells = lanes.map((lane, idx) => drawioCell(
    lane.id,
    lane.label,
    `swimlane;html=1;horizontal=0;startSize=34;fillColor=${idx % 2 ? COLORS.laneAlt : COLORS.lane};strokeColor=${COLORS.border};fontColor=${COLORS.text};fontStyle=1;`,
    lane.x,
    lane.y,
    lane.width,
    lane.height,
  ));
  const nodeCells = nodes.map((node) => drawioCell(node.id, node.label, node.style, node.x, node.y, node.width, node.height));
  const edgeCells = edges.map((edge, idx) => drawioEdge(`e${idx + 1}`, edge));
  return `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2026-06-25T00:00:00.000Z" agent="Codex" version="24.7.17" type="device">
  <diagram id="${name.toLowerCase().replaceAll(" ", "-")}" name="${esc(name)}">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${width}" pageHeight="${height}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
${laneCells.join("\n")}
${nodeCells.join("\n")}
${edgeCells.join("\n")}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
`;
}

const taskStyle = `rounded=1;whiteSpace=wrap;html=1;fillColor=${COLORS.blue};strokeColor=${COLORS.blueBorder};fontColor=${COLORS.text};`;
const manualStyle = `rounded=1;whiteSpace=wrap;html=1;fillColor=${COLORS.orange};strokeColor=${COLORS.orangeBorder};fontColor=${COLORS.text};`;
const systemStyle = `rounded=1;whiteSpace=wrap;html=1;fillColor=${COLORS.green};strokeColor=${COLORS.greenBorder};fontColor=${COLORS.text};`;
const gatewayStyle = `rhombus;whiteSpace=wrap;html=1;fillColor=${COLORS.gray};strokeColor=${COLORS.navy};fontColor=${COLORS.text};`;
const startStyle = `ellipse;whiteSpace=wrap;html=1;fillColor=${COLORS.green};strokeColor=${COLORS.greenBorder};fontColor=${COLORS.text};`;
const endStyle = `ellipse;whiteSpace=wrap;html=1;fillColor=${COLORS.red};strokeColor=${COLORS.redBorder};fontColor=${COLORS.text};`;
const noteStyle = `shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;fillColor=${COLORS.red};strokeColor=${COLORS.redBorder};fontColor=${COLORS.text};`;

const lanes = [
  { id: "lane-client", label: "Инициатор", x: 20, y: 80, width: 1640, height: 120 },
  { id: "lane-manager", label: "Менеджер", x: 20, y: 200, width: 1640, height: 170 },
  { id: "lane-1c", label: "1С", x: 20, y: 370, width: 1640, height: 140 },
  { id: "lane-head", label: "Руководитель", x: 20, y: 510, width: 1640, height: 150 },
  { id: "lane-exec", label: "Исполнитель", x: 20, y: 660, width: 1640, height: 120 },
];

const asIsNodes = [
  { id: "as-start", label: "Заявка поступила по почте или в чат", style: startStyle, x: 70, y: 115, width: 120, height: 60 },
  { id: "as-receive", label: "Менеджер вручную принимает заявку", style: manualStyle, x: 240, y: 250, width: 170, height: 70 },
  { id: "as-check", label: "Проверка данных вручную", style: manualStyle, x: 460, y: 250, width: 160, height: 70 },
  { id: "as-gateway-data", label: "Данных достаточно?", style: gatewayStyle, x: 670, y: 240, width: 120, height: 90 },
  { id: "as-clarify", label: "Запросить уточнение у инициатора", style: manualStyle, x: 650, y: 115, width: 180, height: 70 },
  { id: "as-create-1c", label: "Создать документ в 1С вручную", style: manualStyle, x: 860, y: 405, width: 180, height: 70 },
  { id: "as-approve", label: "Согласование вне системы", style: manualStyle, x: 1100, y: 555, width: 170, height: 70 },
  { id: "as-gateway-approve", label: "Согласовано?", style: gatewayStyle, x: 1340, y: 545, width: 110, height: 90 },
  { id: "as-rework", label: "Вернуть на доработку", style: manualStyle, x: 1120, y: 250, width: 170, height: 70 },
  { id: "as-execute", label: "Передать исполнителю", style: manualStyle, x: 1420, y: 700, width: 170, height: 60 },
  { id: "as-close", label: "Закрыть заявку и статус вручную", style: manualStyle, x: 1160, y: 700, width: 170, height: 60 },
  { id: "as-end", label: "Заявка закрыта", style: endStyle, x: 930, y: 700, width: 120, height: 60 },
  { id: "as-note-1", label: "Проблема: нет единого канала и обязательных полей", style: noteStyle, x: 330, y: 95, width: 210, height: 80 },
  { id: "as-note-2", label: "Проблема: статусы и сроки контролируются вручную", style: noteStyle, x: 1210, y: 385, width: 230, height: 80 },
];

const asIsEdges = [
  { from: "as-start", to: "as-receive", points: [{ x: 215, y: 145 }, { x: 215, y: 285 }] },
  { from: "as-receive", to: "as-check" },
  { from: "as-check", to: "as-gateway-data" },
  { from: "as-gateway-data", to: "as-clarify", label: "Нет", start: "top", end: "bottom", points: [{ x: 730, y: 210 }, { x: 740, y: 210 }], labelAt: { x: 760, y: 215 } },
  { from: "as-clarify", to: "as-check", start: "bottom", end: "top", points: [{ x: 740, y: 215 }, { x: 540, y: 215 }] },
  { from: "as-gateway-data", to: "as-create-1c", label: "Да", start: "right", end: "left", points: [{ x: 825, y: 285 }, { x: 825, y: 440 }], labelAt: { x: 835, y: 365 } },
  { from: "as-create-1c", to: "as-approve", start: "bottom", end: "top", points: [{ x: 950, y: 515 }, { x: 1185, y: 515 }] },
  { from: "as-approve", to: "as-gateway-approve" },
  { from: "as-gateway-approve", to: "as-rework", label: "Нет", start: "top", end: "right", points: [{ x: 1395, y: 500 }, { x: 1485, y: 500 }, { x: 1485, y: 335 }, { x: 1320, y: 335 }, { x: 1320, y: 285 }], labelAt: { x: 1500, y: 490 } },
  { from: "as-rework", to: "as-check", start: "left", end: "right", points: [{ x: 1010, y: 285 }, { x: 1010, y: 345 }, { x: 640, y: 345 }] },
  { from: "as-gateway-approve", to: "as-execute", label: "Да", start: "right", end: "top", points: [{ x: 1505, y: 590 }, { x: 1505, y: 680 }], labelAt: { x: 1520, y: 650 } },
  { from: "as-execute", to: "as-close", start: "left", end: "right" },
  { from: "as-close", to: "as-end", start: "left", end: "right" },
];

const toBeNodes = [
  { id: "to-start", label: "Инициатор заполняет единую форму", style: startStyle, x: 70, y: 115, width: 150, height: 60 },
  { id: "to-validate", label: "1С проверяет обязательные поля", style: systemStyle, x: 270, y: 405, width: 180, height: 70 },
  { id: "to-gateway-valid", label: "Данные корректны?", style: gatewayStyle, x: 500, y: 395, width: 120, height: 90 },
  { id: "to-return", label: "Вернуть на дозаполнение", style: systemStyle, x: 500, y: 115, width: 180, height: 70 },
  { id: "to-create", label: "Создать заявку со статусом Новая", style: systemStyle, x: 680, y: 405, width: 190, height: 70 },
  { id: "to-assign", label: "Назначить ответственного и SLA", style: systemStyle, x: 920, y: 405, width: 190, height: 70 },
  { id: "to-work", label: "Менеджер принимает в работу", style: taskStyle, x: 1220, y: 250, width: 180, height: 70 },
  { id: "to-gateway-approve", label: "Нужно согласование?", style: gatewayStyle, x: 1220, y: 545, width: 130, height: 90 },
  { id: "to-approve", label: "Руководитель согласует в 1С", style: taskStyle, x: 1460, y: 555, width: 170, height: 70 },
  { id: "to-execute", label: "Исполнитель выполняет заявку", style: taskStyle, x: 1430, y: 700, width: 180, height: 60 },
  { id: "to-close", label: "1С фиксирует закрытие и обновляет отчет", style: systemStyle, x: 1110, y: 700, width: 210, height: 60 },
  { id: "to-end", label: "Заявка закрыта", style: endStyle, x: 860, y: 700, width: 120, height: 60 },
  { id: "to-notify", label: "Уведомления о новых и просроченных заявках", style: systemStyle, x: 920, y: 535, width: 190, height: 70 },
  { id: "to-report", label: "Отчет руководителя: статусы, SLA, ответственные", style: systemStyle, x: 700, y: 535, width: 190, height: 70 },
];

const toBeEdges = [
  { from: "to-start", to: "to-validate", points: [{ x: 245, y: 145 }, { x: 245, y: 440 }] },
  { from: "to-validate", to: "to-gateway-valid" },
  { from: "to-gateway-valid", to: "to-return", label: "Нет", start: "top", end: "bottom", points: [{ x: 560, y: 360 }, { x: 590, y: 360 }], labelAt: { x: 575, y: 350 } },
  { from: "to-return", to: "to-start", start: "left", end: "right", points: [{ x: 360, y: 150 }, { x: 360, y: 145 }] },
  { from: "to-gateway-valid", to: "to-create", label: "Да", labelAt: { x: 650, y: 430 } },
  { from: "to-create", to: "to-assign" },
  { from: "to-assign", to: "to-work", start: "right", end: "left", points: [{ x: 1165, y: 440 }, { x: 1165, y: 285 }] },
  { from: "to-assign", to: "to-notify", start: "bottom", end: "top", points: [{ x: 1015, y: 505 }] },
  { from: "to-assign", to: "to-report", start: "bottom", end: "top", points: [{ x: 1015, y: 505 }, { x: 795, y: 505 }] },
  { from: "to-work", to: "to-gateway-approve", start: "bottom", end: "top" },
  { from: "to-gateway-approve", to: "to-approve", label: "Да", labelAt: { x: 1400, y: 582 } },
  { from: "to-gateway-approve", to: "to-execute", label: "Нет", start: "right", end: "left", points: [{ x: 1365, y: 590 }, { x: 1365, y: 730 }], labelAt: { x: 1365, y: 718 } },
  { from: "to-approve", to: "to-execute", start: "bottom", end: "top" },
  { from: "to-execute", to: "to-close", start: "left", end: "right" },
  { from: "to-close", to: "to-end", start: "left", end: "right" },
];

function svgNode(node) {
  const label = esc(node.label);
  const lines = label.split(" ").reduce((acc, word) => {
    const last = acc[acc.length - 1] || "";
    if ((last + " " + word).trim().length > 22) acc.push(word);
    else acc[acc.length - 1] = (last + " " + word).trim();
    return acc;
  }, [""]);
  const text = lines.map((line, idx) => `<tspan x="${node.x + node.width / 2}" y="${node.y + node.height / 2 - (lines.length - 1) * 8 + idx * 17}">${line}</tspan>`).join("");
  if (node.style.includes("ellipse")) {
    const fill = node.style.includes(COLORS.red) ? COLORS.red : COLORS.green;
    const stroke = node.style.includes(COLORS.red) ? COLORS.redBorder : COLORS.greenBorder;
    return `<ellipse cx="${node.x + node.width / 2}" cy="${node.y + node.height / 2}" rx="${node.width / 2}" ry="${node.height / 2}" fill="${fill}" stroke="${stroke}" stroke-width="2"/><text text-anchor="middle" font-size="13" fill="${COLORS.text}">${text}</text>`;
  }
  if (node.style.includes("rhombus")) {
    const points = `${node.x + node.width / 2},${node.y} ${node.x + node.width},${node.y + node.height / 2} ${node.x + node.width / 2},${node.y + node.height} ${node.x},${node.y + node.height / 2}`;
    return `<polygon points="${points}" fill="${COLORS.gray}" stroke="${COLORS.navy}" stroke-width="2"/><text text-anchor="middle" font-size="12" fill="${COLORS.text}">${text}</text>`;
  }
  if (node.style.includes("shape=note")) {
    return `<rect x="${node.x}" y="${node.y}" width="${node.width}" height="${node.height}" rx="4" fill="${COLORS.red}" stroke="${COLORS.redBorder}" stroke-width="2"/><text text-anchor="middle" font-size="12" fill="${COLORS.text}">${text}</text>`;
  }
  const fill = node.style.includes(COLORS.orange) ? COLORS.orange : node.style.includes(COLORS.green) ? COLORS.green : COLORS.blue;
  const stroke = node.style.includes(COLORS.orange) ? COLORS.orangeBorder : node.style.includes(COLORS.green) ? COLORS.greenBorder : COLORS.blueBorder;
  return `<rect x="${node.x}" y="${node.y}" width="${node.width}" height="${node.height}" rx="10" fill="${fill}" stroke="${stroke}" stroke-width="2"/><text text-anchor="middle" font-size="13" fill="${COLORS.text}">${text}</text>`;
}

function anchor(node, side = "right") {
  const anchors = {
    left: { x: node.x, y: node.y + node.height / 2 },
    right: { x: node.x + node.width, y: node.y + node.height / 2 },
    top: { x: node.x + node.width / 2, y: node.y },
    bottom: { x: node.x + node.width / 2, y: node.y + node.height },
  };
  return anchors[side];
}

function pointPath(points) {
  return points.map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

function svgEdge(edge, nodes) {
  const from = nodes.find((node) => node.id === edge.from);
  const to = nodes.find((node) => node.id === edge.to);
  const points = [anchor(from, edge.start), ...(edge.points || []), anchor(to, edge.end || "left")];
  const midPoint = points[Math.floor(points.length / 2)];
  const labelPoint = edge.labelAt || { x: midPoint.x, y: midPoint.y - 8 };
  const label = edge.label ? `<text x="${labelPoint.x}" y="${labelPoint.y}" text-anchor="middle" font-size="12" fill="${COLORS.navy}">${esc(edge.label)}</text>` : "";
  return `<path d="${pointPath(points)}" fill="none" stroke="${COLORS.navy}" stroke-width="2" marker-end="url(#arrow)"/>${label}`;
}

function svgDiagram(title, nodes, edges) {
  const laneSvg = lanes.map((lane, idx) => `<rect x="${lane.x}" y="${lane.y}" width="${lane.width}" height="${lane.height}" fill="${idx % 2 ? COLORS.laneAlt : COLORS.lane}" stroke="${COLORS.border}"/><rect x="${lane.x}" y="${lane.y}" width="34" height="${lane.height}" fill="#E6EEF6" stroke="${COLORS.border}"/><text x="${lane.x + 22}" y="${lane.y + lane.height / 2}" text-anchor="middle" transform="rotate(-90 ${lane.x + 22} ${lane.y + lane.height / 2})" font-size="13" font-weight="700" fill="${COLORS.text}">${esc(lane.label)}</text>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="820" viewBox="0 0 1680 820">
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="${COLORS.navy}"/></marker></defs>
  <rect width="1680" height="820" fill="#FFFFFF"/>
  <text x="840" y="45" text-anchor="middle" font-size="24" font-weight="700" fill="${COLORS.navy}">${esc(title)}</text>
  ${laneSvg}
  ${edges.map((edge) => svgEdge(edge, nodes)).join("\n  ")}
  ${nodes.map(svgNode).join("\n  ")}
</svg>
`;
}

async function main() {
  await fs.mkdir(bpmnDir, { recursive: true });
  await fs.writeFile(path.join(bpmnDir, "as-is.drawio"), drawioDiagram("AS-IS process", 1680, 820, lanes, asIsNodes, asIsEdges));
  await fs.writeFile(path.join(bpmnDir, "to-be.drawio"), drawioDiagram("TO-BE process", 1680, 820, lanes, toBeNodes, toBeEdges));
  await fs.writeFile(path.join(bpmnDir, "as-is.svg"), svgDiagram("AS-IS: текущий процесс обработки заявки", asIsNodes, asIsEdges));
  await fs.writeFile(path.join(bpmnDir, "to-be.svg"), svgDiagram("TO-BE: целевой процесс обработки заявки", toBeNodes, toBeEdges));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
