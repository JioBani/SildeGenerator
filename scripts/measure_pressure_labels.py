"""Detect reviewed cream label ink bands, not OCR or clinical verification."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

source=Path(sys.argv[1]);output=Path(sys.argv[2])
if output.exists():raise ValueError('Preserve previous evidence')
data=json.loads(source.read_text(encoding='utf-8'));rows=[]
for frame in data['frames']:
    if not 136.3<=frame['source_second']<141:continue
    with Image.open(source.parent/'frames'/frame['file']) as im:a=np.asarray(im.convert('RGB'),dtype=float)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    cream=(r>170)&(g>120)&(b>90)&(g>r*.6)
    rows.append({'source_second':frame['source_second'],'heading_pixels':int(cream[145:171,180:450].sum()),
                 'number_pixels':int(cream[175:230,200:450].sum())})
heading=next(x['source_second'] for x in rows if x['heading_pixels']>25)
number=next(x['source_second'] for x in rows if x['number_pixels']>25)
output.write_text(json.dumps({'source_sha256':data['source_sha256'],'heading_first_detected':heading,
    'number_first_detected':number,'limitations':'Reviewed ROI ink onset; threshold and sampling uncertainty, not exact authored keyframe','rows':rows},indent=2),encoding='utf-8')
print(json.dumps({'heading_first_detected':heading,'number_first_detected':number}))
