'use strict';
(() => {
  const art=document.querySelector('.atlas-art'), image=art.querySelector('img');
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const canvas=document.createElement('canvas');canvas.className='atlas-assembly';canvas.setAttribute('aria-hidden','true');art.append(canvas);
  const ctx=canvas.getContext('2d'),clamp=x=>Math.max(0,Math.min(1,x));
  const cols=28,rows=16,tiles=[];
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const seed=Math.sin(x*93.7+y*31.9)*43758.54,random=seed-Math.floor(seed);tiles.push({x,y,delay:random*.32,dx:(random-.5)*130,dy:55+random*80,angle:(random-.5)*.3});}
  let w=0,h=0,visible=false,last=0,progress=0;
  function resize(){const r=art.getBoundingClientRect();w=r.width;h=r.height;const d=Math.min(devicePixelRatio||1,1.5);canvas.width=Math.round(w*d);canvas.height=Math.round(h*d);ctx.setTransform(d,0,0,d,0,0);}
  new ResizeObserver(resize).observe(art);
  new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;},{rootMargin:'80px'}).observe(art);
  function ready(){if(!image.naturalWidth)return;resize();art.classList.add('is-interactive');requestAnimationFrame(frame);}
  function frame(now){
    if(visible&&now-last>33&&w&&h){last=now;const rect=art.getBoundingClientRect();const target=clamp((innerHeight*.96-rect.top)/(innerHeight*.57));progress+=(target-progress)*.14;
      ctx.clearRect(0,0,w,h);const tw=w/cols,th=h/rows,sw=image.naturalWidth/cols,sh=image.naturalHeight/rows;
      for(const tile of tiles){const p=clamp((progress-tile.delay)/(1-tile.delay)),ease=1-Math.pow(1-p,3),unassembled=1-ease;const x=(tile.x+.5)*tw,y=(tile.y+.5)*th;
        ctx.save();ctx.globalAlpha=ease;ctx.translate(x+tile.dx*unassembled,y+tile.dy*unassembled);ctx.rotate(tile.angle*unassembled);ctx.drawImage(image,tile.x*sw,tile.y*sh,sw,sh,-tw/2,-th/2,tw+.4,th+.4);ctx.restore();
      }
      if(art.dataset.focus!==undefined){const focus=Number(art.dataset.focus),part=w/4;ctx.fillStyle='#10111555';if(focus>0)ctx.fillRect(0,0,focus*part,h);if(focus<3)ctx.fillRect((focus+1)*part,0,w-(focus+1)*part,h);ctx.strokeStyle='#dfb9cb55';ctx.lineWidth=1;ctx.strokeRect(focus*part+1,1,part-2,h-2);}
    }
    requestAnimationFrame(frame);
  }
  if(image.complete)ready();else image.addEventListener('load',ready,{once:true});
})();
