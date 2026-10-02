#!/usr/bin/env python3
"""Plan or create code+real-video ZIP; never fabricate a recording or overwrite one.

By default this only lists the curated tracked files. --create requires a real
H.264 video, ffprobe validation and a human --confirm-face attestation. Re-run
after committing presentation changes so tracked contents are complete.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VIDEO_NAME='Milestone2 48287045.mp4'
ZIP_NAME='Milestone2 48287045.zip'
LIMIT=100_000_000
ALLOWED={'src','tests','scripts','docs','results','presentation'}
FORBIDDEN={'.pdf','.mp4','.zip','.exe','.o','.ncu-rep','.nsys-rep','.sqlite','.prof','.pyc'}

def tracked_files():
    raw=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8')
    selected=[]
    for name in raw.split('\0'):
        if not name: continue
        path=Path(name)
        if path.parts[0] not in ALLOWED and name not in ('README.md','Makefile','.gitattributes'): continue
        if path.suffix.lower() in FORBIDDEN or path.name=='.gitkeep': continue
        if any(p in ('.git','build','work','outputs','__pycache__') for p in path.parts): continue
        absolute=ROOT/path
        if absolute.is_symlink() or not absolute.is_file(): raise ValueError('missing/unsafe tracked file '+name)
        selected.append((name,absolute))
    for name in ['Makefile','README.md','src/life.cpp','src/life_cuda.cu','tests/test_cuda.cpp','presentation/narration.md','presentation/final-results.md']:
        if name not in {n for n,_ in selected}: raise ValueError('required file not tracked: '+name)
    return sorted(selected)

def video_metadata(path,ffprobe):
    if path.name!=VIDEO_NAME: raise ValueError('video must be named '+VIDEO_NAME)
    if not path.is_file() or path.stat().st_size<=0 or path.stat().st_size>=LIMIT:
        raise ValueError('video must exist and be strictly smaller than 100 MB')
    executable=shutil.which(ffprobe) or (ffprobe if Path(ffprobe).is_file() else None)
    if not executable: raise ValueError('ffprobe unavailable: supply --ffprobe absolute/path/to/ffprobe')
    result=subprocess.run([executable,'-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=20,check=True)
    meta=json.loads(result.stdout)
    streams=[s for s in meta.get('streams',[]) if s.get('codec_type')=='video']
    if not streams or any(s.get('codec_name')!='h264' for s in streams): raise ValueError('H.264 video required')
    duration=float(meta['format']['duration'])
    if not 0<duration<600: raise ValueError('video must be strictly under 600 seconds for this packaging gate')
    if 'mp4' not in meta['format'].get('format_name','').split(','): raise ValueError('MP4 container required')
    return {'name':path.name,'bytes':path.stat().st_size,'duration_seconds':duration,'codec':'h264','face_visibility':'human confirmation required'}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--video',type=Path)
    parser.add_argument('--create',action='store_true'); parser.add_argument('--confirm-face',action='store_true')
    parser.add_argument('--ffprobe',default='ffprobe'); parser.add_argument('--output-dir',type=Path,default=ROOT/'outputs')
    args=parser.parse_args(); files=tracked_files()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,text=True).strip():
        raise ValueError('commit or resolve workspace changes before planning/creating a reproducible package')
    report={'source_revision':revision,'video':None,'code_files':[n for n,_ in files],
            'code_bytes':sum(p.stat().st_size for _,p in files),'zip_name':ZIP_NAME,
            'structure':{'root_video':VIDEO_NAME,'code_directory':'code/','metadata':'code/SUBMISSION_SOURCE.json'}}
    if args.video: report['video']=video_metadata(args.video.resolve(),args.ffprobe)
    if not args.create:
        print(json.dumps(report,indent=2)); return
    if not args.video or not args.confirm_face: raise ValueError('creation requires real --video and human --confirm-face')
    if report['code_bytes']+report['video']['bytes']>LIMIT-1_000_000:
        raise ValueError('leave at least 1 MB headroom for archive metadata/upload limit; re-export a smaller video')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    target=args.output_dir/ZIP_NAME; pending=args.output_dir/(ZIP_NAME+'.partial')
    if target.exists() or pending.exists(): raise ValueError('refusing to overwrite existing archive; choose another --output-dir')
    metadata={'repository':'https://github.com/z23blhx/cosc7502-milestone2','revision':revision,
              'video_checks':report['video'],'human_face_attestation':True,
              'files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files}}
    with zipfile.ZipFile(pending,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,path in files: archive.write(path,'code/'+name)
        archive.writestr('code/SUBMISSION_SOURCE.json',json.dumps(metadata,indent=2)+'\n')
        archive.write(args.video,VIDEO_NAME,compress_type=zipfile.ZIP_STORED)
    with zipfile.ZipFile(pending) as archive:
        if archive.testzip() is not None: raise ValueError('archive CRC validation failed; partial archive retained')
        if VIDEO_NAME not in archive.namelist(): raise ValueError('archive lacks recording')
    if pending.stat().st_size>=LIMIT: raise ValueError('combined ZIP exceeds conservative upload limit; partial archive retained')
    pending.rename(target)
    print('Created checked archive: {} ({} bytes)'.format(target,target.stat().st_size))

if __name__=='__main__': main()
