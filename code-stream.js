'use strict';
(() => {
  const snippets = [
    ['import pandas as pd','data = pd.read_csv("export.csv")','clean = data.drop_duplicates()','clean.to_excel("result.xlsx")'],
    ['WITH checked AS (','  SELECT order_id, customer_id','  FROM orders',"  WHERE status = 'complete'",') SELECT COUNT(*) FROM checked;'],
    ['data = pd.read_excel("data.xlsx")','valid = data.dropna()','result = valid.groupby("status")','result.size().to_csv("out.csv")'],
    ['SELECT customer_id, COUNT(*)','FROM orders','GROUP BY customer_id','ORDER BY COUNT(*) DESC;']
  ];
  const streams = [...document.querySelectorAll('[data-code-row]')].map((node,i)=>{
    const lines=snippets[i];
    return {node,lines,line:3%lines.length,history:lines.slice(0,3),index:12,last:0,hold:0,speed:65+i*12};
  });
  function render(s){s.node.textContent=[...s.history,s.lines[s.line].slice(0,s.index)].join('\n');}
  streams.forEach(render);
  function frame(now){
    if(!paused&&!document.hidden){for(const s of streams){if(now-s.last>s.speed){s.last=now;const current=s.lines[s.line];if(s.index<current.length)s.index++;else if(++s.hold>7){s.history.push(current);s.history=s.history.slice(-3);s.line=(s.line+1)%s.lines.length;s.index=0;s.hold=0;}render(s);}}}
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
