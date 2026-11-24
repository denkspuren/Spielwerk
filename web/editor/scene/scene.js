/* Spielwerkstatt Szeneneditor – keine Abhängigkeit von der Spielausführung.
 * Mit dem gleichen DOM/CSS wie im Spiel, aber in einem isolierten ShadowRoot.
 */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const Model = window.SpielwerkSceneModel;
  let scene = Model.fresh(), selected = null, dirty = false;
  let originalHtml = '', exportHtml = '', design = {templates:[]}, templates = new Map();
  let stage, shadow, field, drag = null;
  const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  const snap = n => $('snap-grid').checked ? Math.round(n / Number($('grid-size').value)) * Number($('grid-size').value) : Math.round(n);
  const current = () => scene.objects.find(o=>o.id===selected);
  function toast(message){$('toast').textContent=message;$('toast').hidden=false;window.setTimeout(()=>$('toast').hidden=true,4500);}
  function mark(){dirty=true;$('save-state').textContent='Nicht gespeichert';$('save-state').className='dirty';}
  async function fetchOptional(url){const r=await fetch(url,{cache:'no-store'});return r.ok?await r.text():'';}
  function prepareStage(){
    stage=$('scene-frame');shadow=stage.attachShadow({mode:'open'});
    const styles=document.createElement('style');styles.textContent=`
      :host {display:block} #field {position:relative;overflow:hidden;isolation:isolate;box-sizing:border-box;user-select:none;}
      #field .game-object{position:absolute;top:0;left:0;will-change:transform;cursor:grab;touch-action:none;}
      #field [hidden] {display:none!important}
      #field .sw-scene-guide{position:absolute;inset:0;pointer-events:none;z-index:10000;}
      #field .sw-scene-hitbox{position:absolute;pointer-events:none;border:1px dashed #8ee6b8;
       background:#44c98a12;z-index:10002;box-sizing:border-box;}
      #field .sw-scene-selection{position:absolute;pointer-events:none;border:2px dashed #ffe17d;
       box-shadow:0 0 0 1px #162537;z-index:10001;box-sizing:border-box;}
      #field .sw-scene-grid{position:absolute;inset:0;z-index:9000;pointer-events:none;}
      #field .sw-scene-dynamic{filter:drop-shadow(0 0 2px #ffdc84);}
    `;
    shadow.appendChild(styles);
    for (const href of ['/game/style.css','/game/spielwerk/style.css']){
      const link=document.createElement('link');link.rel='stylesheet';link.href=href;shadow.appendChild(link);
    }
    field=document.createElement('div');field.id='field';shadow.appendChild(field);
    field.addEventListener('pointerdown',pointerDown);
    field.addEventListener('pointermove',pointerMove);
    field.addEventListener('pointerup',pointerUp);
    field.addEventListener('pointercancel',pointerUp);
    field.addEventListener('click',e=>e.preventDefault());
  }
  function discover(){
    templates=new Map();
    for (const node of field.querySelectorAll('template[id]')) {
      if (!/^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(node.id) || !node.content.firstElementChild) continue;
      const root=node.content.firstElementChild;
      templates.set(node.id,{id:node.id,element:root});
    }
  }
  function dimensions(templateId) {
    const fromDesign=design.templates?.find(t=>t.id===templateId);
    if(fromDesign) return {w:fromDesign.w,h:fromDesign.h,hit:fromDesign.hit};
    // Vorlagen aus handgeschriebenen scene.html werden mit den wirklichen CSS-Regeln vermessen.
    const t=templates.get(templateId);if(!t)return {w:40,h:40};
    const probe=t.element.cloneNode(true);probe.classList.add('game-object');
    probe.style.cssText+=';position:absolute;left:-10000px;top:-10000px;visibility:hidden;';
    field.appendChild(probe);
    const computed=getComputedStyle(probe);
    const w=parseFloat(computed.width)||40,h=parseFloat(computed.height)||40;
    probe.remove();return {w:Math.round(w),h:Math.round(h)};
  }
  function buildPalette(){
    const palette=$('palette');palette.replaceChildren();
    for (const name of templates.keys()){
      const b=document.createElement('button');b.type='button';
      const title=document.createElement('span');title.textContent=name;
      const s=document.createElement('small');const d=dimensions(name);s.textContent=`${d.w}×${d.h}`;
      b.append(title,s);b.addEventListener('click',()=>add(name));palette.appendChild(b);
    }
    $('empty-palette').hidden=templates.size!==0;
  }
  function listObjects(){
    const list=$('objects');list.replaceChildren();
    scene.objects.forEach(o=>{
      const b=document.createElement('button');b.type='button';
      b.className=(o.id===selected?'active ':'')+o.mode;
      const title=document.createElement('span');title.textContent=o.id;
      const tag=document.createElement('small');tag.textContent=o.mode==='static'?'Statisch':'Dynamisch';
      b.append(title,tag);b.onclick=()=>{selected=o.id;render();};list.appendChild(b);
    });
    const disable=!current();$('delete-object').disabled=disable;$('duplicate-object').disabled=disable;
    $('center-object').disabled=disable;
  }
  function form(){
    const o=current(),root=$('object-form');
    if(!o){root.innerHTML='<p class="notice">Eine Figur in der linken Bibliothek hinzufügen und auswählen.</p>';return;}
    const options=[...templates.keys()].map(id=>`<option ${o.template===id?'selected':''} value="${esc(id)}">${esc(id)}</option>`).join('');
    const d=dimensions(o.template);
    root.innerHTML=`<label class="full">Objekt-ID<input data-key="id" type="text" maxlength="64" value="${esc(o.id)}"></label>
       <label class="full">Vorlage<select data-key="template">${options}</select></label>
       <label>Position X<input data-key="x" type="number" min="-10000" max="10000" value="${o.x}"></label>
       <label>Position Y<input data-key="y" type="number" min="-10000" max="10000" value="${o.y}"></label>
       <label class="full">Verhalten<select data-key="mode"><option value="static" ${o.mode==='static'?'selected':''}>Statisch – sofort sichtbar</option>
       <option value="dynamic" ${o.mode==='dynamic'?'selected':''}>Dynamisch – vom Spiel erzeugt</option></select></label>
       <p class="notice">Vorlagengröße: ${d.w} × ${d.h} px${d.hit?` · Kollision: ${d.hit.w} × ${d.hit.h} px`:''}</p>`;
  }
  function renderField(){
    const zoom=Number($('zoom').value);
    stage.style.width=`${Math.round(scene.width*zoom)}px`;
    stage.style.height=`${Math.round(scene.height*zoom)}px`;
    field.style.width=scene.width+'px';field.style.height=scene.height+'px';
    field.style.transformOrigin='top left';field.style.transform=`scale(${zoom})`;
    field.style.background=scene.background;
    field.innerHTML=originalHtml+'\n'+exportHtml;
    // Vorlagen im DOM belassen, sichtbare Instanzen darunter hängen.
    for (const o of scene.objects){
      const t=field.querySelector(`template[id="${CSS.escape(o.template)}"]`);
      if(!t?.content.firstElementChild)continue;
      const item=t.content.firstElementChild.cloneNode(true);
      item.id=o.id;item.dataset.sceneId=o.id;
      item.classList.add('game-object');
      if(o.mode==='dynamic')item.classList.add('sw-scene-dynamic');
      item.style.transform=`translate3d(${o.x}px,${o.y}px,0)`;
      item.style.opacity=o.mode==='dynamic'?'0.7':'';
      field.appendChild(item);
    }
    if($('show-grid').checked){
      const grid=document.createElement('div');grid.className='sw-scene-grid';
      const step=Number($('grid-size').value);
      grid.style.backgroundImage='linear-gradient(#addfff28 1px,transparent 1px),linear-gradient(90deg,#addfff28 1px,transparent 1px)';
      grid.style.backgroundSize=`${step}px ${step}px`;field.appendChild(grid);
    }
    const chosen=current();if(chosen){
      const s=dimensions(chosen.template),box=document.createElement('div');
      box.className='sw-scene-selection';
      Object.assign(box.style,{left:chosen.x+'px',top:chosen.y+'px',width:s.w+'px',height:s.h+'px'});
      field.appendChild(box);
      if(s.hit){const hit=document.createElement('div');hit.className='sw-scene-hitbox';
        Object.assign(hit.style,{left:(chosen.x+s.hit.x)+'px',top:(chosen.y+s.hit.y)+'px',
          width:s.hit.w+'px',height:s.hit.h+'px'});field.appendChild(hit);}
    }
  }
  function updateSnippet(){
    const generator=window.SpielwerkCodegen?.get($('snippet-language').value);
    $('snippet-code').textContent=generator?.generateScene?.({scene:structuredClone(scene)}) ?? '// Keine Codevorlage für diese Sprache';
  }
  function render(){
    $('scene-title').textContent=`Spielfeld · ${scene.width} × ${scene.height} px`;
    $('scene-width').value=scene.width;$('scene-height').value=scene.height;$('background').value=scene.background;
    listObjects();form();renderField();updateSnippet();
  }
  function add(template){
    const d=dimensions(template);
    const o={id:Model.nextId(scene.objects),template,x:snap((scene.width-d.w)/2),y:snap((scene.height-d.h)/2),mode:'dynamic'};
    scene.objects.push(o);selected=o.id;mark();render();
  }
  function pointerDown(e){
    const el=e.target.closest('[data-scene-id]');if(!el)return;
    const id=el.dataset.sceneId;const item=scene.objects.find(o=>o.id===id);if(!item)return;
    selected=id;drag={id,startX:e.clientX,startY:e.clientY,x:item.x,y:item.y,pointer:e.pointerId};
    field.setPointerCapture(e.pointerId);render();e.preventDefault();
  }
  function pointerMove(e){
    if(!drag || drag.pointer!==e.pointerId)return;
    const item=scene.objects.find(o=>o.id===drag.id);if(!item)return;
    const zoom=Number($('zoom').value);
    item.x=snap(drag.x+(e.clientX-drag.startX)/zoom);item.y=snap(drag.y+(e.clientY-drag.startY)/zoom);
    mark();renderField();form();updateSnippet();
  }
  function pointerUp(e){
    if(!drag || drag.pointer!==e.pointerId)return;
    drag=null;render();
  }
  function edit(e){
    const key=e.target.dataset.key,o=current();if(!o||!key)return;
    let val=(key==='x'||key==='y')?Math.round(Number(e.target.value)):e.target.value;
    if(key==='x'||key==='y')val=Math.max(-10000,Math.min(10000,val));
    if(key==='id' && (val!==o.id) && scene.objects.some(other=>other.id===val)){toast('Diese Objekt-ID gibt es bereits.');return;}
    if(key==='template'&&!templates.has(val))return;
    o[key]=val;
    if(key==='id')selected=val;
    mark();renderField();updateSnippet();listObjects();
  }
  async function save(){
    try{
      Model.validate(scene);
      for(const o of scene.objects) if(!templates.has(o.template))
        throw Error('Vorlage nicht vorhanden: '+o.template+'. Bitte Objektvorlage korrigieren.');
      const reserved=new Set([...field.querySelectorAll('[id]')]
        .filter(el=>!el.hasAttribute('data-scene-id')).map(el=>el.id));
      for(const o of scene.objects) if(reserved.has(o.id))
        throw Error('Objekt-ID bereits in der Szene vergeben: '+o.id);
      const data=JSON.stringify(scene,null,2)+'\n';
      $('save-scene').disabled=true;$('save-state').textContent='Speichere …';
      const r=await fetch('/editor/api/scene/save',{method:'POST',headers:{'Content-Type':'application/json; charset=utf-8','X-Spielwerk-Editor':'save'},body:data});
      if(!r.ok)throw Error((await r.text()).slice(0,200));
      dirty=false;$('save-state').className='';$('save-state').textContent='Gespeichert';
      toast('Szene gespeichert. Spielansicht neu laden, um die Anordnung zu sehen.');
    }catch(e){$('save-state').textContent='Fehler';toast(e.message);}finally{$('save-scene').disabled=false;}
  }
  async function load(){
    const [state,src,generated,figures]=await Promise.all([
      fetch('/editor/api/scene',{cache:'no-store'}),
      fetchOptional('/game/scene.html'),fetchOptional('/game/spielwerk/scene.html'),
      fetch('/editor/api/design',{cache:'no-store'})]);
    if(!state.ok)throw Error('Szenendaten konnten nicht geladen werden.');
    scene=Model.validate(await state.json());
    originalHtml=src;exportHtml=generated;
    if(figures.ok){design=await figures.json();}
    field.innerHTML=originalHtml+'\n'+exportHtml;
    discover();buildPalette();render();
    $('save-state').textContent='Bereit';
  }
  const languages=window.SpielwerkCodegen?.list()||[];
  const languageSelect=$('snippet-language');languageSelect.replaceChildren();
  for(const entry of languages){if(!window.SpielwerkCodegen.get(entry.id)?.generateScene)continue;
    const opt=document.createElement('option');opt.value=entry.id;opt.textContent=entry.label;languageSelect.appendChild(opt);}
  $('save-scene').onclick=save;
  $('object-form').addEventListener('change',e=>{edit(e);render();});
  $('object-form').addEventListener('input',e=>{if(e.target.dataset.key==='x'||e.target.dataset.key==='y')edit(e);});
  $('background').oninput=e=>{scene.background=e.target.value;mark();renderField();};
  $('delete-object').onclick=()=>{if(!current())return;scene.objects=scene.objects.filter(o=>o.id!==selected);selected=null;mark();render();};
  $('duplicate-object').onclick=()=>{const o=current();if(!o)return;
    const clone={...o,id:Model.nextId(scene.objects),x:o.x+20,y:o.y+20};scene.objects.push(clone);selected=clone.id;mark();render();};
  $('center-object').onclick=()=>{const o=current();if(!o)return;const d=dimensions(o.template);
    o.x=snap((scene.width-d.w)/2);o.y=snap((scene.height-d.h)/2);mark();render();};
  $('zoom').onchange=renderField;$('show-grid').onchange=renderField;$('grid-size').onchange=renderField;
  $('snippet-language').onchange=updateSnippet;
  $('copy-code').onclick=async()=>{try{await navigator.clipboard.writeText($('snippet-code').textContent);toast('Code kopiert. Keine Quelldatei verändert.');}catch{toast('Code im Textfeld markieren und kopieren.');}};
  window.addEventListener('keydown',e=>{
    if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key) || !current() ||
       e.target.closest('input,select,textarea,button') || e.ctrlKey || e.metaKey || e.altKey)return;
    const o=current(),n=e.shiftKey?10:1;
    o.x+=e.key==='ArrowLeft'?-n:e.key==='ArrowRight'?n:0;
    o.y+=e.key==='ArrowUp'?-n:e.key==='ArrowDown'?n:0;
    mark();render();e.preventDefault();
  });
  window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
  prepareStage();
  load().catch(e=>toast('Szeneneditor: '+e.message));
})();
