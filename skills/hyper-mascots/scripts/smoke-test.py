#!/usr/bin/env python3
"""Offline regression checks for mascot export; GenMedia is mocked, no API calls.
Requires ffmpeg, pillow, numpy and scipy; HEVC is tested on macOS.
"""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,tempfile
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from matte import matte
spec=importlib.util.spec_from_file_location('normalize_frames',HERE/'normalize-frames.py')
normalizer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)


def ff(args):
    subprocess.run(['ffmpeg','-v','error','-y']+args,check=True)


def decode(path,size):
    data=subprocess.check_output(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgba','-'])
    return np.frombuffer(data,dtype=np.uint8).reshape(size,size,4)


def run():
    with tempfile.TemporaryDirectory(prefix='mascot-smoke-') as td:
        task=Path(td);binpath=task/'bin';binpath.mkdir()
        for name,width,x in [('source',128,32),('wide',192,64)]:
            ff(['-f','lavfi','-i',f'color=c=black:s={width}x128:r=24:d=0.5','-vf',f'drawbox=x={x}:y=32:w=64:h=64:color=orange:t=fill,drawbox=x={x+28}:y=60:w=12:h=12:color=black:t=fill','-c:v','libx264','-pix_fmt','yuv420p',str(task/f'{name}.mp4')])
            ff(['-f','lavfi','-i',f'color=c=black:s={width}x128:r=24:d=0.5','-vf',f'drawbox=x={x}:y=32:w=64:h=64:color=white:t=fill','-c:v','libx264','-pix_fmt','yuv420p',str(task/f'{name}-mask.mp4')])
        ff(['-f','lavfi','-i','sine=frequency=440:duration=0.5','-ar','44100',str(task/'raw.mp3')])
        fake=binpath/'genmedia'
        fake.write_text(chr(10).join([
            '#!/usr/bin/env python3','import json,os,sys','from pathlib import Path',
            "a=sys.argv[1:]; assert '--json' in a,a",
            "root=Path(os.environ['MASCOT_SMOKE_ROOT'])",
            "if os.environ.get('FORBID_GENMEDIA')=='1': raise SystemExit(97)",
            "with (root/'calls.jsonl').open('a') as log: print(json.dumps(a),file=log)",
            "if a[0]=='upload': print(json.dumps({'cdn_url':'https://example.invalid/'+Path(a[1]).stem}))",
            "elif a[0]=='run':",
            " assert '--download' in a,a",
            " if a[1]=='fal-ai/birefnet/v2/video':",
            "  field='mask_video'; stem=a[a.index('--video_url')+1].rsplit('/',1)[1]; path=root/(stem+'-mask.mp4')",
            " elif a[1]=='elevenlabs/tts/eleven-v4': field='audio'; path=root/'raw.mp3'",
            " else: raise SystemExit('Unexpected model request')",
            " url='https://example.invalid/'+path.name",
            " print(json.dumps({'request_id':'mock-mask-request','result':{field:{'url':url}},'downloaded_files':[{'url':url,'path':str(path)}]}))",
            "else: raise SystemExit('Unexpected GenMedia action')",
        ])+chr(10));fake.chmod(0o755)
        env=dict(os.environ,PATH=str(binpath)+os.pathsep+os.environ['PATH'],ORBIE_PYTHON=sys.executable,MASCOT_CROP='crop=iw:ih:0:0',MASCOT_SMOKE_ROOT=str(task),MASCOT_VOICE='Jessica')
        for key in ['MASCOT_STYLE','MASCOT_MASK','MASCOT_CACHE_DIR','MASCOT_REFERENCE_MASK','MASCOT_SCALE','ORBIE_STYLE','ORBIE_MASK','ORBIE_CACHE_DIR','ORBIE_REFERENCE_MASK','ORBIE_SCALE']:env.pop(key,None)
        def export(name,source,out,extra=None):
            subprocess.run(['sh',str(HERE/'alpha-clip.sh'),name,str(source),str(out),'160'],env=dict(env,**(extra or {})),check=True,stdout=subprocess.PIPE)
        export('first',task/'source.mp4',task/'web')
        rgba=decode(task/'web/first.webm',160)
        assert rgba[0,0,3]<=2,'Background is opaque'
        assert rgba[80,80,3]>240 and max(rgba[80,80,:3])<45,'Dark eye became a mask hole'
        manifest=json.loads((task/'web/first.json').read_text())
        assert manifest['finish']=='outline' and manifest['mask_origin']=='fetched'
        assert manifest['matte']['frames']==12 and manifest['mask_request_id']=='mock-mask-request'
        if sys.platform=='darwin':assert (task/'web/first.mov').stat().st_size>0
        subprocess.run(['sh',str(HERE/'voice-line.sh'),str(task/'voice/nested/test.mp3'),'Test line'],env=env,check=True,stdout=subprocess.PIPE)
        assert (task/'voice/nested/test.mp3').stat().st_size>0
        export('cached',task/'source.mp4',task/'other-web',{'FORBID_GENMEDIA':'1','ORBIE_STYLE':'glow','ORBIE_KEEP':'all'})
        cached=json.loads((task/'other-web/cached.json').read_text())
        assert cached['mask_origin']=='cache' and cached['keep_mode']=='all'
        export('override',task/'source.mp4',task/'web',{'FORBID_GENMEDIA':'1','ORBIE_MASK':str(task/'source-mask.mp4')})
        overridden=json.loads((task/'web/override.json').read_text())
        assert overridden['mask_origin']=='override' and overridden['mask_request_id'] is None
        assert overridden['mask_sha256']==hashlib.sha256((task/'source-mask.mp4').read_bytes()).hexdigest()
        export('wide',task/'wide.mp4',task/'web')
        alpha=decode(task/'web/wide.webm',160)[:,:,3]>200
        yy,xx=np.where(alpha);assert abs((xx.max()-xx.min())-(yy.max()-yy.min()))<=2,'Non-square crop distorted a square body'
        # Caption filtering is explicit: an idle's distant/bottom props must survive all mode.
        rgb=np.zeros((100,100,3),np.uint8);mask=np.zeros((100,100),np.uint8)
        mask[25:65,25:65]=255;mask[4:9,3:8]=255;mask[90:95,40:55]=255
        rgb[mask>0]=[240,120,10]
        report={};all_frame=matte(rgb,mask,'outline','all',report)
        assert all_frame[92,45,3]==255 and all_frame[6,5,3]==255 and report['dropped_pixels']==0
        report={};caption_frame=matte(rgb,mask,'outline','captions',report)
        assert caption_frame[92,45,3]<3 and report['bottom_rule_pixels']>0 and report['distance_rule_pixels']>0
        glow_caption=matte(rgb,mask,'glow','captions')
        assert glow_caption[92,45,3]<3,'Glow resurrected a filtered caption/prop'
        # Scale is sqrt(area ratio), after keep filtering, multiplied by the manual factor.
        raw=task/'norm/raw';masks=task/'norm/masks';raw.mkdir(parents=True);masks.mkdir()
        current=np.zeros((100,100),np.uint8);current[20:70,20:70]=255;current[92:95,30:50]=255
        reference=np.zeros((100,100),np.uint8);reference[30:70,30:70]=255
        Image.fromarray(np.repeat(current[:,:,None],3,axis=2)).save(raw/'f_0001.png')
        Image.fromarray(current).save(masks/'f_0001.png');Image.fromarray(reference).save(task/'reference.png')
        result=normalizer.normalize(str(raw),str(masks),str(task/'reference.png'),'1.1','captions')
        assert abs(result['reference_scale']-.8)<1e-9 and abs(result['manual_scale']-1.1)<1e-9
        assert abs(result['scale']-.88)<1e-9 and result['source_frame0_foreground_pixels']==2500
        assert result['centroid_offset']=={'x':5.,'y':5.}
        print('Offline mascot smoke passed: alpha/eyes, HEVC+WebM, voice, zero-network cached rerender, override provenance, aspect ratio, keep modes and fixed scale.',flush=True)


if __name__=='__main__':run()
