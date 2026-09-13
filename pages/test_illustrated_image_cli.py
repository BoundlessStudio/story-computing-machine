"""Exercise the installed bundled image CLI against a local fake Image API."""
import base64
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image

CLI=Path(os.environ.get('IMAGE_GEN',Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'skills/.system/imagegen/scripts/image_gen.py'))


@unittest.skipUnless(os.environ.get('ILLUSTRATED_IMAGE_CLI_TESTS')=='1' and CLI.is_file(),'Enable local fake-API test with installed imagegen skill')
class BundledImageCLITests(unittest.TestCase):
    def test_reference_conditioned_edit_uses_requested_model_and_real_input_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);source=directory/'reference.png';output=directory/'output.png'
            Image.new('RGB',(1024,1024),(32,64,96)).save(source)
            buffer=io.BytesIO();Image.new('RGB',(1024,1536),(120,90,60)).save(buffer,format='PNG')
            encoded=base64.b64encode(buffer.getvalue()).decode()
            requests=[]
            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    data=self.rfile.read(int(self.headers['Content-Length']))
                    requests.append((self.path,data))
                    response=('{"created":0,"data":[{"b64_json":"'+encoded+'"}]}').encode()
                    self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)
                def log_message(self,*args): pass
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                env=os.environ | {'OPENAI_API_KEY':'local-fixture-key','OPENAI_BASE_URL':f'http://127.0.0.1:{server.server_port}/v1','NO_PROXY':'127.0.0.1,localhost'}
                command=[sys.executable,str(CLI),'edit','--model','gpt-image-2.5-sunburst-2026-09-08','--quality','high','--size','1024x1536','--output-format','png','--n','1','--no-augment','--prompt','A synthetic test fixture; preserve the reference.','--image',str(source),'--out',str(output)]
                subprocess.run(command,env=env,check=True,capture_output=True,text=True,timeout=30)
                self.assertEqual(len(requests),1)
                path,data=requests[0]
                self.assertEqual(path,'/v1/images/edits')
                for expected in [b'gpt-image-2.5-sunburst-2026-09-08',b'high',b'1024x1536',source.read_bytes()]: self.assertIn(expected,data)
                with Image.open(output) as image:self.assertEqual(image.size,(1024,1536))
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)

if __name__=='__main__':unittest.main()
