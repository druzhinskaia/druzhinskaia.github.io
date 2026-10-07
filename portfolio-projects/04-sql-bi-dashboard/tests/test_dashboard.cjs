const assert=require('node:assert/strict'), fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');const scope={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,'dashboard/data.js'),'utf8'),scope);
const {aggregate}=require('../dashboard/model.js'),data=scope.window.SALES_DATA,all=aggregate(data);
assert.equal(all.orders,1660);assert.equal(all.revenue,152442883);
for(const channel of new Set(data.orders.map(o=>o.channel))){const m=aggregate(data,{channel});const expected=data.orders.filter(o=>o.channel===channel);assert.equal(m.orders,expected.length);assert.equal(m.revenue,expected.reduce((s,o)=>s+o.revenue,0));assert.equal(m.channels.length,1);assert.equal(m.categories.reduce((s,r)=>s+r.revenue,0),m.revenue);assert.equal(m.monthly.reduce((s,r)=>s+r.revenue,0),m.revenue);}
const empty=aggregate(data,{channel:'missing'});assert.equal(empty.orders,0);assert.equal(empty.margin,null);assert.equal(empty.revenue,0);
const marchSite=aggregate(data,{month:'2026-03',channel:'сайт'});assert(marchSite.orders>0);assert.equal(marchSite.monthly.length,1);assert.equal(marchSite.channels.length,1);
console.log('Dashboard totals, every channel, joint month/channel filters and empty selection: OK');
