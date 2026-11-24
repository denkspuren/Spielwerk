"""Szeneneditor: sprachneutral, unabhängig vom Spielprozess und dem Figureneditor."""
import json
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]


def unused_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


class SceneValidationTests(unittest.TestCase):
    def test_normalize_and_reject_unsafe_data(self):
        from scene_module import checked
        scene={'version':1,'width':640,'height':480,'background':'#112233',
               'objects':[{'id':'spieler','template':'sw-roboter','mode':'dynamic','x':20,'y':30}]}
        self.assertEqual(checked(scene),scene)
        for broken in ({**scene,'width':False}, {**scene,'objects':[scene['objects'][0]]*2},
                       {**scene,'objects':[{**scene['objects'][0],'id':'../evil'}]},
                       {**scene,'objects':[{**scene['objects'][0],'mode':'script'}]},
                       {**scene,'background':'red'}):
            with self.subTest(broken=broken),self.assertRaises(ValueError): checked(broken)

    @unittest.skipUnless(shutil.which('node'),'Node nicht verfügbar')
    def test_model_and_codegen(self):
        # Testet Sprachgeneratoren ohne Browser – diese dürfen die Daten nicht ändern.
        script=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const model=require('./web/editor/scene/scene-model.js');
const ctx={window:{}};vm.createContext(ctx);
for(const path of ['web/editor/codegen/registry.js','web/editor/codegen/java.js','web/editor/codegen/python.js'])
  vm.runInContext(fs.readFileSync(path,'utf8'),ctx);
const scene=model.fresh(600,380);
scene.objects.push({id:'spieler',template:'sw-roboter',x:44,y:90,mode:'dynamic'});
scene.objects.push({id:'wand1',template:'wall',x:20,y:30,mode:'static'});
const before=JSON.stringify(scene);
assert.strictEqual(model.validate(scene),scene);
for(const lang of ['java','python']){
  const generator=ctx.window.SpielwerkCodegen.get(lang);
  const result=generator.generateScene({scene:structuredClone(scene)});
  assert(result.includes('CREATE spieler sw-roboter'));
  assert(result.includes('MOVE spieler 44 90'));
  assert(!result.includes('CREATE wand1 wall'));
  assert.strictEqual(JSON.stringify(scene),before);
}
assert.strictEqual(model.nextId(scene.objects,'spieler'),'spieler1');
assert.throws(()=>model.validate({...scene,width:0}));
console.log('scene model + both code generators OK');
'''
        proc=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)


@unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK fehlt')
class SceneHttpTests(unittest.TestCase):
    def test_scene_independent_on_both_servers(self):
        for lang in ('java','python'):
            with self.subTest(server=lang), tempfile.TemporaryDirectory() as tmp:
                game=Path(tmp)/'sample'
                shutil.copytree(ROOT/'games'/'werkstatt_demo',game)
                layout=game/'spielwerk/layout.json'
                layout.unlink() # Default-Layout aus game.ini muss 600x380 übernehmen.
                originals={name:(game/name).read_bytes() for name in
                           ['SpielwerkDemo.java','scene.html','style.css','game.ini']}
                editor_originals={name:(game/'spielwerk'/name).read_bytes() for name in
                                  ['design.json','scene.html','style.css']}
                port=unused_port();base=f'http://127.0.0.1:{port}'
                cmd=(['java','server-java/ArcadeServer.java'] if lang=='java' else ['python3','server.py'])
                cmd += [str(game/'SpielwerkDemo.java'),'--port',str(port)]
                with tempfile.TemporaryFile() as logfile:
                    proc=subprocess.Popen(cmd,cwd=ROOT,stdout=logfile,stderr=subprocess.STDOUT)
                    try:
                        for _ in range(160):
                            try:
                                with urlopen(base+'/health',timeout=.4) as r:
                                    if r.status==200:break
                            except (OSError, URLError):
                                if proc.poll() is not None:break
                                time.sleep(.1)
                        else:self.fail('Server startete nicht')
                        self.assertIsNone(proc.poll())
                        for route,expected in [('/editor/scene',b'Szeneneditor'),
                                               ('/editor/scene/scene.js',b'/editor/api/scene/save'),
                                               ('/editor/scene/scene-model.js',b'SpielwerkSceneModel'),
                                               ('/editor/scene/scene.css',b'#scene-workarea')]:
                            with urlopen(base+route,timeout=5) as resp:
                                self.assertIn(expected,resp.read())
                        with urlopen(base+'/editor/api/scene',timeout=5) as resp:
                            current=json.load(resp)
                        self.assertEqual((current['width'],current['height']),(600,380))
                        current['objects']=[{'id':'wand1','template':'sw-formen','x':50,'y':80,'mode':'static'},
                                            {'id':'spieler','template':'sw-roboter','x':200,'y':140,'mode':'dynamic'}]
                        body=json.dumps(current).encode()
                        request=lambda data,headers=None:Request(base+'/editor/api/scene/save',data=data,
                            method='POST',headers=headers or {})
                        with self.assertRaises(HTTPError) as err:
                            urlopen(request(body),timeout=5)
                        self.assertEqual(err.exception.code,403)
                        with self.assertRaises(HTTPError) as err:
                            urlopen(request(body,{'X-Spielwerk-Editor':'save','Origin':'https://example.org'}),timeout=5)
                        self.assertEqual(err.exception.code,403)
                        with self.assertRaises(HTTPError) as err:
                            urlopen(request(b'{bad',{'X-Spielwerk-Editor':'save'}),timeout=5)
                        self.assertEqual(err.exception.code,400)
                        with urlopen(request(body,{'X-Spielwerk-Editor':'save'}),timeout=5) as resp:
                            self.assertEqual(resp.status,200)
                        with urlopen(base+'/game/spielwerk/layout.json',timeout=5) as resp:
                            saved=json.load(resp)
                        self.assertEqual(saved['objects'],current['objects'])
                        self.assertEqual(json.loads(layout.read_text())['objects'],current['objects'])
                        for name in ['SpielwerkDemo.java','scene.html','style.css','game.ini']:
                            self.assertEqual((game/name).read_bytes(),originals[name])
                        for name in ['design.json','scene.html','style.css']:
                            self.assertEqual((game/'spielwerk'/name).read_bytes(),editor_originals[name])
                        with urlopen(Request(base+'/input',data=b'KEYDOWN ArrowLeft',method='POST'),timeout=5) as resp:
                            self.assertEqual(resp.status,200)
                        with urlopen(Request(base+'/shutdown',data=b'',method='POST',headers={'X-Arcade-Action':'shutdown'}),timeout=5):pass
                        proc.wait(timeout=12);self.assertEqual(proc.returncode,0)
                    finally:
                        if proc.poll() is None:
                            proc.terminate()
                            try:proc.wait(timeout=5)
                            except subprocess.TimeoutExpired:proc.kill()

if __name__=='__main__': unittest.main()
