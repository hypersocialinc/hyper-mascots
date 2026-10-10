#!/usr/bin/env python3
"""Apply one reference scale and one manual scale to an aligned clip.

normalize-frames.py <raw_dir> <mask_dir> <reference_mask|-> <auto|manual_scale> [captions|all]
Compare the clip with its OWN source pose/props after the same crop/padding.
This measures silhouette area, not semantic body area across different roles.
"""
import glob,json,math,os,sys
import numpy as np
from PIL import Image
from matte import prepare_mask


def normalize(raw,masks,reference,requested,keep_mode='captions'):
    files=sorted(glob.glob(os.path.join(raw,'*.png')))
    if not files: raise ValueError('No raw frames to normalize')
    mask_files=[os.path.join(masks,os.path.basename(path)) for path in files]
    prepared=[prepare_mask(np.asarray(Image.open(path).convert('L')),keep_mode)[0]>.4 for path in mask_files]
    areas=np.array([int(mask.sum()) for mask in prepared])
    current=int(areas[0])
    if not current: raise ValueError('Frame-0 foreground mask is empty')
    reference_area=None; reference_scale=1.; centroid_offset=None
    if reference!='-':
        ref=prepare_mask(np.asarray(Image.open(reference).convert('L')),'all')[0]>.4
        if ref.shape!=prepared[0].shape: raise ValueError('Reference and clip must share crop/padding/dimensions')
        reference_area=int(ref.sum())
        if not reference_area: raise ValueError('Reference mask is empty')
        reference_scale=math.sqrt(reference_area/current)
        if abs(reference_area/current-1)<=.03: reference_scale=1.
        ry,rx=np.argwhere(ref).mean(axis=0);cy,cx=np.argwhere(prepared[0]).mean(axis=0)
        centroid_offset={'x':float(rx-cx),'y':float(ry-cy)}
    elif requested=='auto': raise ValueError('Auto normalization requires a reference mask')
    manual_scale=1. if requested=='auto' else float(requested)
    factor=reference_scale*manual_scale
    if not math.isfinite(factor) or not .25<=factor<=4:
        raise ValueError('Combined scale must be finite and within 0.25..4; check reference/manual scale')
    ratios=areas/current
    if abs(float(np.median(ratios))-1)>.03:
        print('WARNING: median mask area differs from frame 0 by more than 3%; inspect motion/size drift',file=sys.stderr)
    largest=(0,'none');edge_frames=0
    for path,mask_path in zip(files,mask_files):
        name=os.path.basename(path)
        for image_path,mode in [(path,'RGB'),(mask_path,'L')]:
            source=Image.open(image_path).convert(mode)
            if factor==1.: canvas=source
            else:
                width,height=source.size
                enlarged=source.resize((max(1,round(width*factor)),max(1,round(height*factor))),Image.Resampling.LANCZOS)
                canvas=Image.new(mode,(width,height),0)
                canvas.paste(enlarged,((width-enlarged.width)//2,(height-enlarged.height)//2))
                if mode=='L':
                    lost=max(0,int(np.count_nonzero(np.asarray(enlarged)>128))-int(np.count_nonzero(np.asarray(canvas)>128)))
                    if lost>largest[0]: largest=(lost,name)
                canvas.save(image_path)
            if mode=='L':
                foreground=prepare_mask(np.asarray(canvas),keep_mode)[0]>.4
                if any(np.any(edge) for edge in [foreground[0],foreground[-1],foreground[:,0],foreground[:,-1]]):edge_frames+=1
    result={'scale':factor,'reference_scale':reference_scale,'manual_scale':manual_scale,
            'reference_foreground_pixels':reference_area,'source_frame0_foreground_pixels':current,
            'frame_area_ratio':{'min':float(ratios.min()),'median':float(np.median(ratios)),'max':float(ratios.max())},
            'centroid_offset':centroid_offset,'max_clipped_mask_pixels':largest[0],
            'clipped_frame':largest[1],'foreground_edge_frames':edge_frames}
    if largest[0] or edge_frames:print(f'WARNING: {edge_frames} frames touch the edge; max clipped mask pixels={largest[0]} at {largest[1]}',file=sys.stderr)
    return result


if __name__=='__main__':
    if len(sys.argv) not in (5,6):raise SystemExit('usage: normalize-frames.py <raw_dir> <mask_dir> <reference|-> <auto|manual_scale> [captions|all]')
    try:print(json.dumps(normalize(*sys.argv[1:])))
    except (ValueError,OSError) as error:raise SystemExit(str(error))
