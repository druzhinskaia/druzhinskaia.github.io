'use strict';
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scenes = [...document.querySelectorAll('.ambient-canvas,.case-ambient')].map(canvas => ({canvas, c:canvas.getContext('2d'), mode:canvas.dataset.caseScene, w:0,h:0,visible:false}));
  const observer = new IntersectionObserver(entries => entries.forEach(e => { const s=scenes.find(s=>s.canvas===e.target); if(s)s.visible=e.isIntersecting; }), {rootMargin:'80px'});
  scenes.forEach(s => {const resize=()=>{const r=s.canvas.getBoundingClientRect();s.w=r.width;s.h=r.height;const d=Math.min(devicePixelRatio||1,2);s.canvas.width=Math.round(r.width*d);s.canvas.height=Math.round(r.height*d);s.c.setTransform(d,0,0,d,0,0);};new ResizeObserver(resize).observe(s.canvas);observer.observe(s.canvas);resize();});
  const box=(c,x,y,w,h,color)=>{c.fillStyle='#12171ddd';c.fillRect(x,y,w,h);c.strokeStyle=color+'55';c.lineWidth=1;c.strokeRect(x+.5,y+.5,w-1,h-1);};
  const text=(c,value,x,y,color,size=12)=>{c.font=`${size}px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace`;c.fillStyle=color;c.fillText(value,x,y);};
  const line=(c,x,y,x2,y2,color)=>{c.strokeStyle=color;c.lineWidth=1;c.beginPath();c.moveTo(x,y);c.lineTo(x2,y2);c.stroke();};
  function draw(s,t){
    const {c,w,h,mode}=s;c.clearRect(0,0,w,h);if(w<1||h<1)return;
    if(mode===undefined){const radius=Math.min(w,h)*.3,x=w*.8,y=h*.5;c.strokeStyle='#cfb8cb10';for(let i=0;i<3;i++){c.beginPath();c.arc(x,y,radius*(.6+i*.2),0,Math.PI*2);c.stroke();}return;}
    const x=12,y=24,W=w-24,fs=w<330?11:12;
    if(mode==='0'){
      const cols=[.34,.36,.3],rh=30,top=y+32,color='#e5b4ca';box(c,x,y,W,212,color);text(c,'EXPORT / CHECK',x+12,y+20,color,11);
      let xx=x;['record','value','status'].forEach((v,i)=>{text(c,v,xx+10,top+19,'#afa9b6',fs);xx+=W*cols[i];});
      const rows=[['12041','4 800','OK'],['12042','—','CHECK'],['12043','5 180','OK'],['12044','—','CHECK'],['12045','6 320','OK']];
      rows.forEach((row,j)=>{const yy=top+(j+1)*rh;line(c,x,yy,x+W,yy,'#ffffff12');let cx=x;row.forEach((v,i)=>{text(c,v,cx+10,yy+20,i===2&&v==='CHECK'?color:'#adb5bf',fs);cx+=W*cols[i];});});
      const scan=top+rh+((t*.2)%1)*rh*5;line(c,x,scan,x+W,scan,'#e5b4ca45');
      text(c,'CHECKS → ISSUE REGISTER',x+10,y+240,color,11);
    }else if(mode==='1'){
      const color='#a9cebf',labels=['01  SOURCE DATA','02  VALIDATION','03  REQUIREMENTS','04  TO-BE PROCESS'],bh=42,gap=16;
      labels.forEach((v,i)=>{const yy=y+i*(bh+gap);box(c,x,yy,W,bh,color);text(c,v,x+16,yy+26,color,fs);if(i<3)line(c,x+W/2,yy+bh,x+W/2,yy+bh+gap,'#a9cebf55');});
    }else{
      const color=mode==='2'?'#c9b5d6':'#aec6d8';
      const lines=mode==='2'?['import pandas as pd','','data = pd.read_csv("export.csv")','clean = data.drop_duplicates()','result = clean.groupby("status")','  .size()']:['WITH checked AS (','  SELECT order_id, customer_id','  FROM orders','  WHERE status = \'complete\'',')','SELECT COUNT(*) FROM checked;'];
      const maxChars=Math.floor((W-24)/(fs*.61));
      const fitted=[];for(const l of lines){if(l.length<=maxChars)fitted.push(l);else{const cut=l.lastIndexOf(' ',maxChars);const n=cut>5?cut:maxChars;fitted.push(l.slice(0,n), '  '+l.slice(n).trim());}}
      const gap=22,H=46+fitted.length*gap;box(c,x,y,W,H,color);text(c,mode==='2'?'analysis.py':'checks.sql',x+12,y+23,color,11);line(c,x,y+34,x+W,y+34,'#ffffff14');
      const progress=reduce||paused?1:(t%12)/8;
      fitted.forEach((v,i)=>{const count=Math.floor(Math.max(0,Math.min(1,progress*fitted.length-i))*v.length);text(c,v.slice(0,count),x+12,y+56+i*gap,i===0?color:'#b6bcc8',fs);});
      if(y+H+28<h)text(c,mode==='2'?'CLEAN → GROUP → EXPORT':'QUERY → RESULT',x+12,y+H+25,color,11);
    }
  }
  let last=0,time=0;
  function frame(now){if(now-last>40){const dt=Math.min((now-last)/1000,.1);last=now;if(!paused&&!reduce)time+=dt;for(const s of scenes)if(s.visible)draw(s,time);}requestAnimationFrame(frame);}
  requestAnimationFrame(frame);
})();
