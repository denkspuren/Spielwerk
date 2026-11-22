/* Unabhängiger Test der Sprachadapter und CSS-Formen ohne Browser oder Server. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
const window={};const context={window};vm.createContext(context);
for(const file of ['registry.js','java.js','python.js']) {
  vm.runInContext(fs.readFileSync(path.join(root,'web/editor/codegen',file),'utf8'),context,{filename:file});
}
const registry=window.SpielwerkCodegen;
assert.deepStrictEqual(Array.from(registry.list(),x=>x.id),['java','python']);
const original={id:'sw-test-figur',w:80,h:70,hit:{x:5,y:6,w:60,h:55},layers:[]};
for(const language of ['java','python']) {
  const template=JSON.parse(JSON.stringify(original));
  const code=registry.get(language).generate({template,designVersion:1});
  assert(code.includes('TEST_FIGUR_BREITE')&&code.includes('80'));
  assert(code.includes('CREATE held')&&code.includes('MOVE held 100 100'));
  assert(code.includes('KOLLISION_Y')&&code.includes('6'));
  assert.deepStrictEqual(template,original,'Sprachgenerator darf Design nicht ändern');
  if(language==='python') {
    assert(code.includes('flush=True'));
    fs.writeFileSync('/tmp/spielwerk-python-schnipsel.py',code);
  } else {
    assert(code.includes('static final int'));
    fs.writeFileSync('/tmp/spielwerk-java-schnipsel.txt',code);
  }
}
const source=fs.readFileSync(path.join(root,'web/editor/editor.js'),'utf8');
const part=source.slice(source.indexOf('  function shapeStyle('),source.indexOf('  function applyStyle('));
vm.runInContext('const fileName=()=>true; '+part+'\nthis.shapeStyle=shapeStyle;',context);
const base={x:0,y:0,w:60,h:60,color:'#51AADD',color2:'#003366',gradient:false,border:0,borderColor:'#fff',radius:0,shadow:0,opacity:100,fontSize:12};
const triangle=context.shapeStyle({...base,type:'triangle',direction:'down'});
assert(triangle.clipPath.includes('polygon(0% 0%, 100% 0%, 50% 100%)'));
const rotated=context.shapeStyle({...base,type:'triangle',direction:'up',rotation:90,flipX:true,flipY:false});
assert(rotated.transform==='rotate(90deg) scale(-1, 1)', 'Drehen und Spiegeln auch in exportiertem CSS');
const mirrored=context.shapeStyle({...base,type:'rect',rotation:-30,flipY:true});
assert(mirrored.transform==='rotate(-30deg) scale(1, -1)');
const arc=context.shapeStyle({...base,type:'arc',arcStart:45,arcSweep:220,arcThickness:9});
assert(arc.background.includes('conic-gradient(from 45deg'));
assert(arc.background.includes('220deg'));
assert(arc.maskImage.includes('9px'));
assert(arc.WebkitMaskImage===arc.maskImage);
const editorHtml=fs.readFileSync(path.join(root,'web/editor/index.html'),'utf8');
for(const control of ['show-guides','snap-grid','grid-size','center-layer'])assert(editorHtml.includes(`id="${control}"`));
console.log('OK: Grafik, Drehung, Spiegelung, Rasterhilfen, Java/Python-Generatoren');
