#!/usr/bin/env python3
"""Graft a lip-synced face onto a moving clip of the same drawing.

  mouth-graft.py <still.png> <body_frames_dir> <talk_frames_dir> <out_dir>
                 <eyeL_x,eyeL_y> <eyeR_x,eyeR_y> <mouth_x,mouth_y>

The lip-sync model only animates the mouth and keeps everything else still,
and the tested video lip-sync models failed on this cartoon face. So: generate the
motion (a driving loop, say) from the still with a video model, generate the
talking with the lip-sync model from the same still, then graft the mouth
from the talking frames onto the moving frames. Both clips are tracked
against the still by the eyes, so the mouth lands on the face wherever the
body has bounced to. Frames must be the same size and frame rate.

Needs: pip install pillow numpy scipy
"""
import glob, os, sys
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
from scipy import ndimage as ndi

still, bdir, tdir, odir = sys.argv[1:5]
eL = tuple(int(v) for v in sys.argv[5].split(',')); eR = tuple(int(v) for v in sys.argv[6].split(',')); mo = tuple(int(v) for v in sys.argv[7].split(','))
os.makedirs(odir, exist_ok=True)
S = np.asarray(Image.open(still).convert('L')).astype(np.float32) / 255
H, W = S.shape
sp = eR[0] - eL[0]                                   # eye spacing sets every size
# eyes template (not the mouth, which changes shape while talking)
ty0, ty1 = int(eL[1] - .45 * sp), int(eL[1] + .45 * sp)
tx0, tx1 = int(eL[0] - .5 * sp), int(eR[0] + .5 * sp)
T = S[ty0:ty1, tx0:tx1]; T = T - T.mean()
# search in a window around the still's position
pad = int(.9 * sp)
wy0, wy1, wx0, wx1 = max(0, ty0 - pad), min(H, ty1 + pad), max(0, tx0 - pad), min(W, tx1 + pad)

def track(img):
    win = img[wy0:wy1, wx0:wx1]
    c = fftconvolve(win - win.mean(), T[::-1, ::-1], mode='valid')
    k = np.unravel_index(np.argmax(c), c.shape)
    return int(k[0] + wy0 - ty0), int(k[1] + wx0 - tx0)       # (dy, dx) from the still

# the whole face comes across, eyes and mouth together, so they always agree
# (a squint from one clip under an open mouth from the other looks wrong):
# a feathered ellipse from above the eyes to below an open "ah"
yy, xx = np.mgrid[0:H, 0:W]
cy, cx = (eL[1] + mo[1]) / 2 + .1 * sp, (eL[0] + eR[0]) / 2
ry, rx = (mo[1] - eL[1]) / 2 + .62 * sp, 1.05 * sp
d = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2
M = np.clip((1.15 - d) / .3, 0, 1).astype(np.float32)
M = ndi.gaussian_filter(M, sp * .03)

bf = sorted(glob.glob(os.path.join(bdir, '*.png'))); tf = sorted(glob.glob(os.path.join(tdir, '*.png')))
n = min(len(bf), len(tf)); offs = []
for i in range(n):
    B = np.asarray(Image.open(bf[i]).convert('RGB')).astype(np.float32)
    Tk = np.asarray(Image.open(tf[i]).convert('RGB')).astype(np.float32)
    bdy, bdx = track(B.mean(2) / 255); tdy, tdx = track(Tk.mean(2) / 255)
    offs.append((bdy, bdx, tdy, tdx))
    # talk pixels where the still's mouth is (+ talk offset), placed where the body's face is (+ body offset)
    src = ndi.shift(Tk, (bdy - tdy, bdx - tdx, 0), order=1, mode='nearest')
    m = ndi.shift(M, (bdy, bdx), order=1, mode='constant')[..., None]
    out = B * (1 - m) + src * m
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(os.path.join(odir, os.path.basename(bf[i])))
o = np.array(offs)
print('frames', n, '| body offset y %d..%d x %d..%d | talk offset y %d..%d x %d..%d' % (o[:,0].min(), o[:,0].max(), o[:,1].min(), o[:,1].max(), o[:,2].min(), o[:,2].max(), o[:,3].min(), o[:,3].max()))
