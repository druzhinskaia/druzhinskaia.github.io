/* Pure aggregation model, shared by the browser and Node tests. */
(function (global) {
  function aggregate(data, filters = {}) {
    const orders = data.orders.filter(o => (!filters.month || o.order_date.slice(0,7) === filters.month)
      && (!filters.channel || o.channel === filters.channel));
    const ids = new Set(orders.map(o => o.order_id));
    const sum = (rows, key) => rows.reduce((total, r) => total + Number(r[key]), 0);
    const revenue = sum(orders,'revenue'), profit = sum(orders,'profit');
    function groups(rows, key, revenueKey='revenue', profitKey='profit') {
      const result = new Map();
      for (const row of rows) {
        const name = typeof key === 'function' ? key(row) : row[key];
        if (!result.has(name)) result.set(name,{name,revenue:0,profit:0,orders:new Set(),receivables:0});
        const g=result.get(name); g.revenue+=Number(row[revenueKey]||0); g.profit+=Number(row[profitKey]||0);
        g.orders.add(row.order_id); g.receivables+=Number(row.receivables||0);
      }
      return [...result.values()].map(g => ({...g,orders:g.orders.size,margin:g.revenue ? g.profit/g.revenue : null}));
    }
    const items=data.items.filter(i=>ids.has(i.order_id)).map(i=>({...i,profit:i.line_revenue-i.line_cost}));
    return {orders:orders.length,revenue,profit,margin:revenue ? profit/revenue : null,
      avg_order_value:orders.length ? revenue/orders.length : null,
      receivables:sum(orders,'receivables'), overpayments:sum(orders,'overpayment'),
      monthly:groups(orders,o=>o.order_date.slice(0,7)).sort((a,b)=>a.name.localeCompare(b.name)),
      channels:groups(orders,'channel').sort((a,b)=>b.revenue-a.revenue),
      categories:groups(items,'category','line_revenue').sort((a,b)=>b.revenue-a.revenue),
      debtors:groups(orders.filter(o=>o.receivables>0),'customer_name').sort((a,b)=>b.receivables-a.receivables).slice(0,15)};
  }
  if (typeof module !== 'undefined') module.exports={aggregate}; else global.SalesModel={aggregate};
})(typeof window === 'undefined' ? globalThis : window);
