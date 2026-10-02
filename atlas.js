'use strict';
(() => {
  const section=document.querySelector('.visual-atlas');
  const art=section.querySelector('.atlas-art');
  const buttons=[...section.querySelectorAll('[data-atlas-case]')];
  const open=section.querySelector('.atlas-open');
  const expand=document.getElementById('atlas-expand');
  const imageDialog=document.getElementById('atlas-image-dialog');
  const colors=['#f8b9bb','#a8e7db','#e8b5ef','#c7c5ff'];
  const copy={
    ru:{label:'Атлас решений',title:'Данные можно<br><em>почувствовать.</em>',intro:'Четыре визуальных образа моих проектов. Выбери тему, затем открой разбор проекта.',open:'Смотреть кейс <span aria-hidden="true">↗</span>',choices:'Выбрать кейс',expand:'Развернуть изображение',close:'Закрыть изображение',choice:['Качество данных','Логика процесса','Сигналы клиентов','Связи в данных'],kicker:['ПРОВЕРИТЬ','ОПИСАТЬ','УСЛЫШАТЬ','СВЯЗАТЬ'],detail:['Найти то, что не сходится.','Сделать процесс понятным.','Превратить отзывы в решения.','Собрать целую картину.']},
    en:{label:'The atlas',title:'Data you can<br><em>feel.</em>',intro:'Four visual interpretations of my projects. Choose a theme, then explore the case.',open:'Explore the case <span aria-hidden="true">↗</span>',choices:'Choose a case',expand:'Expand image',close:'Close image',choice:['Data quality','Process logic','Customer signals','Data relationships'],kicker:['VALIDATE','MODEL','LISTEN','CONNECT'],detail:['Find what does not add up.','Make a process understandable.','Turn feedback into decisions.','See the complete picture.']}
  };
  let active=0;
  function setActive(i){
    active=i;const t=copy[lang];section.style.setProperty('--atlas-accent',colors[i]);
    buttons.forEach((button,j)=>button.setAttribute('aria-pressed',String(i===j)));
    section.querySelector('.atlas-detail-index').textContent=`0${i+1} / 04`;
    section.querySelector('.atlas-detail-kicker').textContent=t.kicker[i];
    section.querySelector('.atlas-detail-title').textContent=t.detail[i];
    art.style.setProperty('--scan',(12+i*25)+'%');
  }
  function localize(){
    const t=copy[lang];section.querySelector('[data-atlas-text="label"]').textContent=t.label;
    section.querySelector('[data-atlas-text="title"]').innerHTML=t.title;
    section.querySelector('[data-atlas-text="intro"]').textContent=t.intro;
    open.innerHTML=t.open;section.querySelector('.atlas-choices').setAttribute('aria-label',t.choices);
    buttons.forEach((b,i)=>b.querySelector('span').textContent=t.choice[i]);
    expand.setAttribute('aria-label',t.expand);expand.title=t.expand;
    imageDialog.querySelector('.atlas-image-close').setAttribute('aria-label',t.close);
    imageDialog.setAttribute('aria-label',t.expand);setActive(active);
  }
  buttons.forEach((button,i)=>button.addEventListener('click',()=>setActive(i)));
  open.addEventListener('click',()=>{activeCase=active;populateCase(active);dialog.showModal();document.body.style.overflow='hidden';});
  expand.addEventListener('click',()=>imageDialog.showModal());
  imageDialog.querySelector('.atlas-image-close').addEventListener('click',()=>imageDialog.close());
  imageDialog.addEventListener('click',e=>{if(e.target===imageDialog)imageDialog.close();});
  document.getElementById('lang').addEventListener('click',localize);
  localize();
})();
