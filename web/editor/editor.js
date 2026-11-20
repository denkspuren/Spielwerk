/* Spielwerkstatt: Browsereditor, vollständig unabhängig vom Spielprotokoll.
 * Entwurfsmodell -> HTML-Templates + CSS. Java-/Tick-/Event-Code bleibt unberührt.
 */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  let project = {version:1, templates:[]};
  let active = 0, selected = -1, dirty = false, moving = false, assets = [];
  let drag = null;
  const max = (n, a, b) => Math.min(b, Math.max(a, Number(n) || 0));
  const esc = (s) => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
  const ident = (s) => /^sw-[A-Za-z][A-Za-z0-9_-]{0,40}$/.test(s);
  const fileName = (s) => /^[A-Za-z0-9_-]{1,64}\.(png|jpg|jpeg|gif|webp|svg)$/i.test(s);
  const layerNames = {rect:'Rechteck',ellipse:'Ellipse',triangle:'Dreieck',arc:'Kreisbogen',text:'Text',image:'Bild'};
  const part = (type, x=8, y=8) => ({type, x,y,w:type==='text'?60:35,h:type==='text'?22:35,
    color:'#39afd5',color2:'#164e8d',gradient:false,border:0,borderColor:'#e8f7ff',radius:8,shadow:8,opacity:100,
    text:'Hallo!',fontSize:14,image:'',direction:'up',arcStart:35,arcSweep:270,arcThickness:8});
  const robot = () => ({id:'sw-roboter',w:64,h:72,hit:{x:5,y:7,w:54,h:62},layers:[
    {...part('rect',3,4),w:58,h:64,color:'#53caec',color2:'#1576a4',gradient:true,border:3,borderColor:'#caeeff',radius:17,shadow:12},
    {...part('ellipse',15,23),w:9,h:12,color:'#113754',shadow:0},
    {...part('ellipse',40,23),w:9,h:12,color:'#113754',shadow:0},
    {...part('rect',25,51),w:14,h:4,color:'#133b57',radius:4,shadow:0}
  ]});
  function current() {return project.templates[active];}
  function currentLayer() {return current()?.layers[selected];}
  function mark() {dirty=true; $('save-state').textContent='Nicht gespeichert'; $('save-state').className='dirty';}
  function flash(msg) {$('toast').textContent=msg;$('toast').hidden=false;setTimeout(()=>{$('toast').hidden=true;},4500);}
  function textField(key,label,value,kind='number',attrs='') {
    return `<label>${esc(label)}<input data-scope="${key.startsWith('hit.')?'hit':key.startsWith('fig.')?'fig':'layer'}" data-key="${esc(key.split('.').pop())}" type="${kind}" value="${esc(value)}" ${attrs}></label>`;
  }
  function selectField(key,label,options,value) {
    return `<label>${esc(label)}<select data-scope="layer" data-key="${esc(key)}">${options.map(s=>`<option value="${esc(s)}" ${s===value?'selected':''}>${esc(s||'– keines –')}</option>`).join('')}</select></label>`;
  }
  // Genau dieselbe CSS-Beschreibung wird in der Vorschau und im Export verwendet.
  // Es wird keine Grafikbibliothek im Java- oder Python-Spiel benötigt.
  function shapeStyle(l) {
    const shape=l.type;
    const color=l.gradient?`linear-gradient(145deg, ${l.color}, ${l.color2})`:l.color;
    const bg=shape==='image'?(fileName(l.image)?`url("/game/assets/${l.image}") center / contain no-repeat`:'transparent'):
      shape==='arc'?`conic-gradient(from ${Number(l.arcStart)||0}deg, ${l.color} 0deg ${Number(l.arcSweep)||270}deg, transparent ${Number(l.arcSweep)||270}deg 360deg)`:color;
    const style={position:'absolute',left:l.x+'px',top:l.y+'px',width:l.w+'px',height:l.h+'px',
      boxSizing:'border-box',background:bg,border:l.border&&shape!=='triangle'&&shape!=='arc'?`${l.border}px solid ${l.borderColor}`:'none',
      borderRadius:shape==='ellipse'||shape==='arc'?'50%':l.radius+'px',
      boxShadow:l.shadow&&shape!=='arc'?`0 0 ${l.shadow}px ${l.color}99`:'none',
      opacity:String(l.opacity/100),fontSize:l.fontSize+'px',fontWeight:'700',color:'#ffffff',
      textAlign:'center',lineHeight:'normal',display:'flex',alignItems:'center',justifyContent:'center',whiteSpace:'nowrap',overflow:'hidden'};
    if(shape==='triangle') {
      const directions={up:'50% 0%, 100% 100%, 0% 100%',down:'0% 0%, 100% 0%, 50% 100%',
        left:'0% 50%, 100% 0%, 100% 100%',right:'0% 0%, 100% 50%, 0% 100%'};
      style.clipPath=`polygon(${directions[l.direction]||directions.up})`;
    }
    if(shape==='arc') {
      const thickness=Math.max(1,Math.min(Math.round(Number(l.arcThickness)||8), Math.floor(Math.min(l.w,l.h)/2)));
      const mask=`radial-gradient(closest-side, transparent calc(100% - ${thickness}px), #000 calc(100% - ${thickness-1}px))`;
      style.maskImage=mask;
      style.WebkitMaskImage=mask;
      // box-shadow auf dem umfassenden Rechteck wäre irreführend.
      if(l.shadow)style.filter=`drop-shadow(0 0 ${l.shadow}px ${l.color}99)`;
    }
    return style;
  }
  function applyStyle(el,style){Object.assign(el.style,style);}
  function renderCanvas(){
    const t=current(), zoom=Number($('zoom').value), stage=$('zoom-stage'), art=$('artwork');
    $('preview-title').textContent=`${t.id} · ${t.w} × ${t.h} Pixel`;
    stage.style.width=(t.w*zoom)+'px';stage.style.height=(t.h*zoom)+'px';
    art.style.width=t.w+'px';art.style.height=t.h+'px';art.style.transform=`scale(${zoom})`;
    art.replaceChildren();
    t.layers.forEach((l,i)=>{
      const el=document.createElement('div');el.className='part'+(i===selected?' selected':'');el.dataset.layer=String(i);
      applyStyle(el,shapeStyle(l)); if(l.type==='text') el.textContent=l.text;
      art.appendChild(el);
    });
    if($('show-hitbox').checked){const hit=document.createElement('div');hit.className='hitbox';applyStyle(hit,{left:t.hit.x+'px',top:t.hit.y+'px',width:t.hit.w+'px',height:t.hit.h+'px'});art.appendChild(hit);}
    const origin=document.createElement('div');origin.className='origin';art.appendChild(origin);
  }
  function renderLists(){
    $('templates').replaceChildren();
    project.templates.forEach((t,i)=>{
      const b=document.createElement('button');b.className=i===active?'active':'';
      const title=document.createElement('span');title.textContent=t.id;
      const size=document.createElement('small');size.textContent=`${t.w}×${t.h}`;
      b.append(title,size);b.onclick=()=>{active=i;selected=-1;renderAll();};$('templates').appendChild(b);
    });
    $('layers').replaceChildren();
    current().layers.forEach((l,i)=>{
      const b=document.createElement('button');b.className=i===selected?'active':'';
      const title=document.createElement('span');title.textContent=`${i+1}. ${layerNames[l.type]}`;
      const size=document.createElement('small');size.textContent=`${l.w}×${l.h}`;
      b.append(title,size);b.onclick=()=>{selected=i;renderAll();};$('layers').appendChild(b);
    });
    for(const id of ['layer-up','layer-down','layer-delete']) $(id).disabled=selected<0;
  }
  function renderForms(){
    const t=current(),l=currentLayer();
    $('template-form').innerHTML=`${textField('fig.id','Template-ID',t.id,'text','pattern="sw-[A-Za-z][A-Za-z0-9_-]*"')}
      ${textField('fig.w','Breite (px)',t.w,'number','min="8" max="640"')}
      ${textField('fig.h','Höhe (px)',t.h,'number','min="8" max="640"')}
      <p class="notice">Template-ID im Spielprotokoll: <code>CREATE held ${esc(t.id)}</code></p>
      ${textField('hit.x','Kollision X',t.hit.x)}${textField('hit.y','Kollision Y',t.hit.y)}
      ${textField('hit.w','Kollision Breite',t.hit.w)}${textField('hit.h','Kollision Höhe',t.hit.h)}`;
    if(!l){$('layer-form').innerHTML='<p class="notice">Eine Ebene anklicken oder eine neue hinzufügen.</p>';return;}
    $('layer-form').innerHTML=`
      ${textField('x','Position X',l.x)}${textField('y','Position Y',l.y)}
      ${textField('w','Breite (px)',l.w)}${textField('h','Höhe (px)',l.h)}
      ${l.type!=='image'?`${textField('color','Farbe',l.color,'color')}${l.type!=='arc'?`${textField('color2','Verlaufsfarbe',l.color2,'color')}
      <label class="check"><input type="checkbox" data-scope="layer" data-key="gradient" ${l.gradient?'checked':''}> Farbverlauf verwenden</label>`:''}`:''}
      ${l.type==='text'?textField('text','Beschriftung',l.text,'text','class="full"'):''}
      ${l.type==='text'?textField('fontSize','Schriftgröße',l.fontSize):''}
      ${l.type==='triangle'?`<label>Richtung<select data-scope="layer" data-key="direction">${[['up','Oben'],['down','Unten'],['left','Links'],['right','Rechts']].map(([val,label])=>`<option value="${val}" ${l.direction===val?'selected':''}>${label}</option>`).join('')}</select></label>`:''}
      ${l.type==='arc'?`${textField('arcStart','Startwinkel (°)',l.arcStart,'number','min="0" max="359"')}
      ${textField('arcSweep','Bogenwinkel (°)',l.arcSweep,'number','min="1" max="359"')}
      ${textField('arcThickness','Linienstärke (px)',l.arcThickness,'number','min="1" max="320"')}`:''}
      ${l.type==='image'?selectField('image','Bilddatei', ['',...assets],l.image):''}
      ${l.type==='image'?'<label class="full"><button id="upload-image" type="button">Bild hochladen …</button><input id="image-file" type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden></label>':''}
      ${l.type==='rect'||l.type==='text'?textField('radius','Eckenradius',l.radius):''}
      ${!['image','triangle','arc'].includes(l.type)?textField('border','Rahmen (px)',l.border):''}
      ${!['image','triangle','arc'].includes(l.type)?textField('borderColor','Rahmenfarbe',l.borderColor,'color'):''}
      ${textField('shadow','Schatten (px)',l.shadow)}${textField('opacity','Deckkraft (%)',l.opacity)}
    `;
    const button=$('upload-image'); if(button) button.onclick=()=>$('image-file').click();
    const input=$('image-file');if(input) input.onchange=uploadImage;
  }
  function snippet() {
    const language=$('snippet-language').value;
    const generator=window.SpielwerkCodegen?.get(language);
    if(!generator)return '// Für diese Sprache ist noch kein Generator verfügbar.';
    // Eine Kopie des JSON-Modells schützt den Editor vor Änderungen durch Plugins.
    return generator.generate({template:structuredClone(current()), designVersion:project.version});
  }
  function generate(){
    const html=['<!-- Automatisch von Spielwerkstatt erzeugt. Änderungen bitte im Editor vornehmen. -->'];
    const css=['/* Automatisch von Spielwerkstatt erzeugt. CSS-Koordinaten = Spielkoordinaten in Pixeln. */'];
    project.templates.forEach(t=>{
      if(!ident(t.id)) throw new Error(`Ungültige Template-ID: ${t.id} (muss mit sw- beginnen)`);
      const cls='sw-root-'+t.id;
      html.push(`<template id="${t.id}"><div class="sw-sprite ${cls}" data-hitbox="${t.hit.x} ${t.hit.y} ${t.hit.w} ${t.hit.h}">`);
      css.push(`#field .${cls} {width:${t.w}px;height:${t.h}px;box-sizing:border-box;}`);
      t.layers.forEach((l,i)=>{
        const sub=`sw-layer-${i}`;
        html.push(`  <div class="${sub}">${l.type==='text'?esc(l.text):''}</div>`);
        const st=shapeStyle(l);
        css.push(`#field .${cls} .${sub} {${Object.entries(st).map(([k,v])=>k.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())+':'+v).join(';')};}`);
      });
      html.push('</div></template>');
    });
    return {html:html.join('\n')+'\n',css:css.join('\n')+'\n'};
  }
  function updateCode(){
    $('snippet-code').textContent=snippet();
    try{const generated=generate();$('generated-html').textContent=generated.html;$('generated-css').textContent=generated.css;}
    catch(err){$('generated-html').textContent=err.message;$('generated-css').textContent='';}
  }
  function renderAll(){renderLists();renderForms();renderCanvas();updateCode();$("help-template").textContent=current().id;}
  function validate(){
    const seen=new Set();
    for(const t of project.templates){
      if(!ident(t.id)||seen.has(t.id)) throw new Error('Template-IDs müssen eindeutig sein, mit sw- beginnen und nur Buchstaben, Zahlen, - oder _ enthalten.');
      seen.add(t.id);
      if(!(t.w>=8&&t.w<=640&&t.h>=8&&t.h<=640))throw new Error('Figurgröße muss zwischen 8 und 640 Pixeln liegen.');
      for(const k of ['x','y','w','h']) if(!Number.isInteger(t.hit[k]))throw new Error('Kollisionsgrößen müssen ganze Zahlen sein.');
      if(t.hit.w<1||t.hit.h<1)throw new Error('Das Kollisionsrechteck benötigt positive Breite und Höhe.');
      for(const l of t.layers) {
        if(l.type==='image'&&l.image&&!fileName(l.image))throw new Error('Ungültiger Bilddateiname.');
        if(!['rect','ellipse','triangle','arc','text','image'].includes(l.type))throw new Error('Unbekannter Ebenentyp.');
        if(l.type==='arc'&&(!Number.isInteger(l.arcStart)||l.arcStart<0||l.arcStart>359||
          !Number.isInteger(l.arcSweep)||l.arcSweep<1||l.arcSweep>359||
          !Number.isInteger(l.arcThickness)||l.arcThickness<1||l.arcThickness>Math.floor(Math.min(l.w,l.h)/2)))
          throw new Error('Kreisbogen: Start 0–359°, Bogen 1–359°, Stärke maximal halbe Formgröße.');
        if(l.type==='triangle'&&!['up','down','left','right'].includes(l.direction))
          throw new Error('Ungültige Dreiecksrichtung.');
      }
    }
  }
  async function save(){
    try{
      validate();const generated=generate();
      const enc=new TextEncoder();const a=enc.encode(JSON.stringify(project,null,2)),b=enc.encode(generated.html),c=enc.encode(generated.css);
      const header=enc.encode(`${a.length}\n${b.length}\n${c.length}\n`),body=new Uint8Array(header.length+a.length+b.length+c.length);
      let off=0;for(const item of [header,a,b,c]){body.set(item,off);off+=item.length;}
      $('save').disabled=true;$('save-state').textContent='Speichere …';
      const response=await fetch('/editor/api/save',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Spielwerk-Editor':'save'},body});
      if(!response.ok)throw new Error(await response.text());
      dirty=false;$('save-state').textContent='Gespeichert';$('save-state').className='';
      flash('Figuren gespeichert. Spielansicht neu laden, um sie zu verwenden.');
    }catch(err){$('save-state').textContent='Fehler beim Speichern';flash(err.message);}
    finally{$('save').disabled=false;}
  }
  function unique(base){let id=base,i=2;while(project.templates.some(t=>t.id===id)){id=base+'-'+i++;}return id;}
  function newTemplate(){const t={id:unique('sw-figur'),w:80,h:80,hit:{x:0,y:0,w:80,h:80},layers:[part('rect')]};project.templates.push(t);active=project.templates.length-1;selected=0;mark();renderAll();}
  function addLayer(type){const t=current();const l=part(type,Math.round(t.w/5),Math.round(t.h/5));if(type==='image'&&assets.length)l.image=assets[0];t.layers.push(l);selected=t.layers.length-1;mark();renderAll();}
  function updateProperty(event){
    const el=event.target;const key=el.dataset.key,scope=el.dataset.scope;
    if(!key||!scope)return;
    const t=current();const target=scope==='fig'?t:scope==='hit'?t.hit:currentLayer();if(!target)return;
    let value=el.type==='checkbox'?el.checked:el.type==='number'?Math.round(Number(el.value)):el.value;
    if(el.type==='number'){
      if(key==='w'||key==='h')value=max(value,scope==='hit'?1:scope==='fig'?8:1,scope==='fig'?640:700);
      else if(key==='opacity')value=max(value,0,100);
      else if(key==='fontSize')value=max(value,6,64);
      else if(key==='arcStart')value=max(value,0,359);
      else if(key==='arcSweep')value=max(value,1,359);
      else if(key==='arcThickness')value=max(value,1,Math.max(1,Math.floor(Math.min(target.w,target.h)/2)));
      else if(['border','radius','shadow'].includes(key))value=max(value,0,70);
      else value=max(value,-700,700);
    }
    target[key]=value;
    if(scope==='layer'&&target.type==='arc'&&(key==='w'||key==='h'))
      target.arcThickness=Math.min(target.arcThickness,Math.max(1,Math.floor(Math.min(target.w,target.h)/2)));
    mark();renderCanvas();updateCode();
    if(key==='id')$('preview-title').textContent=`${t.id} · ${t.w} × ${t.h} Pixel`;
  }
  async function uploadImage(ev){
    const file=ev.target.files?.[0];if(!file)return;
    let name=file.name.replace(/[^A-Za-z0-9_.-]/g,'_');
    if(!/^[A-Za-z0-9_-]{1,64}\.(png|jpe?g|gif|webp)$/i.test(name)){flash('Bildname nicht zulässig. Nur PNG, JPG, GIF oder WebP.');return;}
    if(file.size>2_000_000){flash('Bild darf höchstens 2 MB groß sein.');return;}
    try{
      const response=await fetch(`/editor/api/assets/${name}`,{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Spielwerk-Editor':'save'},body:file});
      if(!response.ok)throw new Error(await response.text());
      assets=await (await fetch('/editor/api/assets')).json();
      const l=currentLayer();if(l){l.image=name;mark();renderForms();renderCanvas();updateCode();}flash(`Bild gespeichert: ${name}`);
    }catch(err){flash(err.message);}
  }
  async function load(){
    try{
      const response=await fetch('/editor/api/design',{cache:'no-store'});if(!response.ok)throw new Error('Entwurf konnte nicht geladen werden');
      const raw=await response.json();
      if(raw.version!==1||!Array.isArray(raw.templates))throw new Error('Unbekanntes Entwurfsformat');
      project=raw;
      if(!project.templates.length){project.templates=[robot()];dirty=true;$('save-state').textContent='Noch nicht gespeichert';}
      const assetResponse=await fetch('/editor/api/assets',{cache:'no-store'});if(assetResponse.ok)assets=await assetResponse.json();
      active=0;selected=-1;renderAll();
    }catch(err){flash(err.message);}
  }
  $('add-template').onclick=newTemplate;
  document.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>addLayer(b.dataset.add));
  $('delete-template').onclick=()=>{if(project.templates.length<2){flash('Mindestens eine Figur muss erhalten bleiben.');return;}if(!confirm('Diese Figur löschen?'))return;project.templates.splice(active,1);active=0;selected=-1;mark();renderAll();};
  $('duplicate').onclick=()=>{const t=structuredClone(current());t.id=unique(t.id+'-kopie');project.templates.push(t);active=project.templates.length-1;selected=-1;mark();renderAll();};
  $('layer-delete').onclick=()=>{if(selected<0)return;current().layers.splice(selected,1);selected=-1;mark();renderAll();};
  $('layer-up').onclick=()=>reorder(1);$('layer-down').onclick=()=>reorder(-1);
  function reorder(dir){const layers=current().layers;const other=selected+dir;if(selected<0||other<0||other>=layers.length)return;[layers[selected],layers[other]]=[layers[other],layers[selected]];selected=other;mark();renderAll();}
  $('template-form').addEventListener('input',updateProperty);$('layer-form').addEventListener('input',updateProperty);
  $('template-form').addEventListener('change',()=>renderAll());$('layer-form').addEventListener('change',()=>renderAll());
  for(const item of (window.SpielwerkCodegen?.list()||[])){
    const option=document.createElement('option');option.value=item.id;option.textContent=item.label;
    $('snippet-language').appendChild(option);
  }
  $('snippet-language').value='java';
  $('snippet-language').onchange=updateCode;
  $('zoom').onchange=renderCanvas;$('show-hitbox').onchange=renderCanvas;$('save').onclick=save;
  $('copy-code').onclick=async()=>{try{await navigator.clipboard.writeText(snippet());flash('Codeschnipsel kopiert – keine Quelldatei geändert.');}catch{flash('Codeschnipsel oben markieren und kopieren.');}};
  $('test-motion').onclick=()=>{moving=!moving;$('test-motion').textContent=moving?'■ Bewegung anhalten':'▶ Bewegung testen';
    $('zoom-stage').animate?.([{transform:'translateX(-14px)'},{transform:'translateX(14px)'},{transform:'translateX(-14px)'}],{duration:1200,iterations:moving?Infinity:1});
    if(!moving)$('zoom-stage').getAnimations().forEach(a=>a.cancel());};
  $('artwork').addEventListener('pointerdown',(e)=>{
    const hit=e.target.closest('[data-layer]');if(!hit)return;
    selected=Number(hit.dataset.layer);const l=currentLayer();
    drag={x:e.clientX,y:e.clientY,oldX:l.x,oldY:l.y};renderAll();e.preventDefault();
  });
  window.addEventListener('pointermove',(e)=>{
    if(!drag)return;const l=currentLayer();if(!l)return;
    const zoom=Number($('zoom').value);
    l.x=Math.round(drag.oldX+(e.clientX-drag.x)/zoom);
    l.y=Math.round(drag.oldY+(e.clientY-drag.y)/zoom);
    mark();renderCanvas();updateCode();
  });
  window.addEventListener('pointerup',()=>{if(!drag)return;drag=null;renderAll();});
  window.addEventListener('beforeunload',(e)=>{if(dirty){e.preventDefault();e.returnValue='';}});
  load();
})();
