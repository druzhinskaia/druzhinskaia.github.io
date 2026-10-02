'use strict';
(() => {
  const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
  const root=document.documentElement,body=document.body;
  const hero=document.querySelector('.hero'),intro=document.querySelector('.intro'),projects=document.querySelector('.projects'),about=document.querySelector('.about'),contact=document.querySelector('.contact');
  const track=document.querySelector('.project-grid'),cards=[...document.querySelectorAll('.project-card')],dots=[...document.querySelectorAll('[data-jump]')];
  const word=document.querySelector('.scene-word'),heroCopy=document.querySelector('.hero-copy'),aura=document.querySelector('.cursor-aura');
  const globalButton=document.getElementById('global-motion');
  let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  let gallery=false,lastY=scrollY,speed=0,burst=0,manualAt=0,active=0,px=-100,py=-100,cx=-100,cy=-100,inside=false,lastLang='',words=[];
  let heroTop=0,heroSpan=1,projectTop=0,projectSpan=1,trackWidth=1,layoutHeight=1;
  window.atlasMotion={progress:0,velocity:0,burst:0};
  function splitWords(){const p=document.querySelector('.intro-main p');const text=translations[lang].introText;p.replaceChildren();words=text.split(' ').map((text,i)=>{const s=document.createElement('span');s.className='reveal-word';s.textContent=text;p.append(s,document.createTextNode(' '));return s;});}
  function measure(){gallery=false;body.classList.toggle('motion-ready',!reduced);body.classList.remove('gallery-ready');heroTop=hero.offsetTop;heroSpan=Math.max(1,hero.offsetHeight*.8);projectTop=projects.offsetTop;projectSpan=Math.max(1,projects.offsetHeight-innerHeight);trackWidth=document.querySelector('.project-window').clientWidth;layoutHeight=document.documentElement.scrollHeight-innerHeight;cards.forEach(c=>{if(!gallery){c.inert=false;c.removeAttribute('aria-hidden');c.style.removeProperty('--card-alpha');c.style.removeProperty('--card-scale');c.style.removeProperty('--card-rotate');}});}
  function labels(){lastLang=lang;splitWords();document.querySelector('.gallery-hint').textContent=lang==='ru'?'Листай свайпом или стрелками':'Swipe or use the arrows';document.querySelector('[data-project-prev]').setAttribute('aria-label',lang==='ru'?'Предыдущий проект':'Previous project');document.querySelector('[data-project-next]').setAttribute('aria-label',lang==='ru'?'Следующий проект':'Next project');document.querySelector('.project-dots').setAttribute('aria-label',lang==='ru'?'Выбрать проект':'Choose a project');dots.forEach((b,i)=>b.setAttribute('aria-label',(lang==='ru'?'Проект ':'Project ')+(i+1)));aura.querySelector('span').textContent=lang==='ru'?'ОТКРЫТЬ':'EXPLORE';syncPause();}
  function syncPause(){body.classList.toggle('is-paused',paused);globalButton.setAttribute('aria-pressed',String(paused));globalButton.setAttribute('aria-label',translations[lang][paused?'play':'pause']);globalButton.querySelector('[aria-hidden]').textContent=paused?'▷':'Ⅱ';globalButton.querySelector('[data-motion-t]').textContent=lang==='ru'?(paused?'Продолжить':'Движение'):(paused?'Resume':'Motion');}
  globalButton.addEventListener('click',()=>{paused=!paused;updateMotion();syncPause();});
  document.getElementById('motion').addEventListener('click',syncPause);
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{manualAt=scrollY;}));
  const windowEl=document.querySelector('.project-window');const goProject=i=>{i=clamp(i,0,cards.length-1);windowEl.scrollTo({left:cards[i].offsetLeft-cards[0].offsetLeft,behavior:paused||reduced?'instant':'smooth'});setCurrent(i);};function setCurrent(i){active=i;document.querySelector('.project-counter b').textContent='0'+(i+1);dots.forEach((b,j)=>{b.classList.toggle('active',i===j);b.setAttribute('aria-pressed',String(i===j));b.style.setProperty('--dot-fill',i===j?1:0);});document.querySelector('[data-project-prev]').disabled=i===0;document.querySelector('[data-project-next]').disabled=i===cards.length-1;}
  dots.forEach((b,i)=>b.addEventListener('click',()=>goProject(i)));document.querySelector('[data-project-prev]').addEventListener('click',()=>goProject(active-1));document.querySelector('[data-project-next]').addEventListener('click',()=>goProject(active+1));windowEl.addEventListener('scroll',()=>{const step=cards[1].offsetLeft-cards[0].offsetLeft;if(step>0)setCurrent(Math.round(windowEl.scrollLeft/step));},{passive:true});setCurrent(0);
  cards.forEach((card,i)=>{card.dataset.chapter='0'+(i+1);card.addEventListener('pointermove',e=>{if(paused||e.pointerType==='touch')return;const r=card.getBoundingClientRect();card.style.setProperty('--tilt-x',((e.clientX-r.left)/r.width-.5)*8+'deg');card.style.setProperty('--tilt-y',-((e.clientY-r.top)/r.height-.5)*8+'deg');});card.addEventListener('pointerleave',()=>{card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg');});});
  hero.addEventListener('pointerdown',e=>{if(!paused&&!e.target.closest('button,a'))burst=1;});
  window.addEventListener('pointermove',e=>{px=e.clientX;py=e.clientY;inside=e.pointerType==='mouse';aura.classList.toggle('over-card',!!e.target.closest('.project-card'));},{passive:true});
  document.addEventListener('pointerleave',()=>inside=false);
  let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(measure,120);});
  document.getElementById('lang').addEventListener('click',()=>{labels();requestAnimationFrame(measure);});
  function sectionProgress(section){const r=section.getBoundingClientRect();return clamp((innerHeight-r.top)/(innerHeight+r.height));}
  function frame(){if(lang!==lastLang)labels();const y=scrollY,delta=y-lastY;lastY=y;speed+=(delta-speed)*.15;burst*=.94;const hp=clamp((y-heroTop)/heroSpan);window.atlasMotion.progress=hp;window.atlasMotion.velocity=paused?0:clamp(speed,-35,35)/35;window.atlasMotion.burst=burst;
    document.querySelector('.reading-progress i').style.transform=`scaleX(${clamp(y/layoutHeight)})`;document.querySelector('.header').classList.toggle('scrolled',y>40);
    if(!reduced){
      if(manualScene&&Math.abs(y-manualAt)>120)manualScene=false;
      if(!manualScene){const mode=hp<.3?0:hp<.67?1:2;if(mode!==sceneMode)setScene(mode);}
      word.textContent=['CHAOS','STRUCTURE','CLARITY'][sceneMode];word.style.transform=`translate3d(${paused?0:-hp*40}px,0,0)`;
      document.querySelector('.hero-chapter').textContent=`0${sceneMode+1} — 03`;
      heroCopy.style.transform='none';heroCopy.style.opacity='1';
      const ip=sectionProgress(intro);intro.style.setProperty('--intro-progress',clamp((ip-.12)*1.7));
      document.querySelector('.intro-main h2').style.transform='none';
      words.forEach(w=>w.classList.add('lit'));
      document.querySelectorAll('.principles>span').forEach((p,i)=>{const f=clamp((ip-.18-i*.045)*4);p.style.setProperty('--rise','0px');p.style.setProperty('--alpha',1);});
      const codeBand=document.querySelector('.code-band');if(codeBand){const r=codeBand.getBoundingClientRect();if(r.top<innerHeight*.88&&r.bottom>0)codeBand.classList.add('is-visible');}
      if(gallery){const pp=clamp((y-projectTop)/projectSpan);const raw=clamp(pp*4-.18,0,3);const nearest=Math.round(raw);active=nearest;const position=paused?nearest:raw;track.style.setProperty('--track-x',-position*trackWidth+'px');cards.forEach((c,i)=>{const distance=Math.abs(i-position);c.style.setProperty('--card-scale',paused?1:1-Math.min(distance,1)*.1);c.style.setProperty('--card-alpha',1-Math.min(distance,1)*.75);c.style.setProperty('--card-rotate',paused?'0deg':(i-position)*-6+'deg');c.inert=i!==nearest;c.setAttribute('aria-hidden',String(i!==nearest));c.classList.toggle('is-current',i===nearest);c.style.setProperty('--scan-x',(raw*210-60)+'%');c.style.setProperty('--wave-scale',.65+Math.sin(raw*2)*.3);});document.querySelector('.project-counter b').textContent='0'+(nearest+1);dots.forEach((b,i)=>{b.classList.toggle('active',i===nearest);b.setAttribute('aria-pressed',String(i===nearest));b.style.setProperty('--dot-fill',clamp(pp*4-i));});}
      const ap=sectionProgress(about);about.style.setProperty('--about-progress',clamp((ap-.07)*1.6));document.querySelectorAll('.experience article').forEach((el,i)=>{const r=el.getBoundingClientRect(),p=clamp((innerHeight-r.top)/ (innerHeight*.65));el.style.transform='none';el.style.opacity=1;});document.querySelectorAll('.tool-row').forEach(el=>{const r=el.getBoundingClientRect(),p=clamp((innerHeight-r.top)/(innerHeight*.7));el.style.setProperty('--tool-progress',p);el.style.setProperty('--tool-offset','0px');});
      const cp=sectionProgress(contact);contact.style.setProperty('--contact-scale',.6+cp);contact.querySelector('h2').style.transform='none';contact.querySelector('h2').style.opacity=1;
      cx+=(px-cx)*.17;cy+=(py-cy)*.17;aura.style.opacity=inside&&!paused?'1':'0';aura.style.transform=`translate3d(${cx-35}px,${cy-35}px,0)`;
    }requestAnimationFrame(frame);
  }
  labels();measure();requestAnimationFrame(frame);
})();
