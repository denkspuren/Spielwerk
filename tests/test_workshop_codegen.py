"""Browserunabhängige JavaScript-Formtests und Sprachgeneratoren."""
import shutil
import subprocess
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('node'), 'Node fehlt')
class WorkshopCodegenTests(unittest.TestCase):
    def test_shapes_and_language_generators(self):
        result = subprocess.run(['node', 'tests/test_workshop_codegen.js'], cwd=ROOT,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('OK:', result.stdout)
    def test_python_code_is_valid(self):
        subprocess.run(['node', 'tests/test_workshop_codegen.js'], cwd=ROOT,
                       capture_output=True, check=True, timeout=10)
        src=Path('/tmp/spielwerk-python-schnipsel.py').read_text()
        compile(src, '<spielwerk Python>', 'exec')
    @unittest.skipUnless(shutil.which('javac'), 'JDK-Compiler fehlt')
    def test_java_snippet_compiles(self):
        subprocess.run(['node', 'tests/test_workshop_codegen.js'], cwd=ROOT,
                       capture_output=True, check=True, timeout=10)
        snippet=Path('/tmp/spielwerk-java-schnipsel.txt').read_text()
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'SnippetTest.java'
            src.write_text('public class SnippetTest {\n'+snippet+'\n'
                           'public static void main(String[] args) { test_figur_anlegen(); }\n}\n')
            compile_result=subprocess.run(['javac',str(src)],capture_output=True,text=True,timeout=15)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr)
            result=subprocess.run(['java','-cp',tmp,'SnippetTest'],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('CREATE held sw-test-figur',result.stdout)
    def test_backend_routes_are_editor_only(self):
        java=(ROOT/'server-java/EditorModule.java').read_text()
        python=(ROOT/'editor_module.py').read_text()
        self.assertIn('/editor/codegen/',java)
        self.assertIn('/editor/codegen/',python)
        self.assertNotIn('GameModule', ''.join((ROOT/'web/editor/codegen'/n).read_text()
                        for n in ('registry.js','java.js','python.js')))

if __name__=='__main__':unittest.main()
