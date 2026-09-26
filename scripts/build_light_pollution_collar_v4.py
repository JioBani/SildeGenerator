"""Collar occlusion revision; keep the approved C performance and media intact."""
from __future__ import annotations

import json
import shutil
import cv2
import numpy as np

from build_light_pollution_story_ab import ASSETS, EXPERIMENT, GSAP, render, sha256
from actor_assembly_gate import occlusion_findings


NECK = "person-neck-overlap-v4b.png"


def registration() -> dict:
    moving = cv2.imread(str(ASSETS / NECK), cv2.IMREAD_GRAYSCALE)
    target = cv2.imread(str(ASSETS / "person-head-neutral.png"), cv2.IMREAD_GRAYSCALE)
    if moving is None or target is None:
        raise ValueError("Neck registration images missing")
    detector = cv2.SIFT_create()
    masks = [np.zeros_like(moving), np.zeros_like(target)]
    masks[0][:780] = 255
    masks[1][:840] = 255
    ka, da = detector.detectAndCompute(moving,masks[0])
    kb, db = detector.detectAndCompute(target,masks[1])
    matches = [a for a,b in cv2.BFMatcher().knnMatch(da,db,k=2) if a.distance < .7*b.distance]
    src = np.float32([ka[m.queryIdx].pt for m in matches])
    dst = np.float32([kb[m.trainIdx].pt for m in matches])
    matrix, inliers = cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=3)
    if matrix is None or inliers is None or int(inliers.sum()) < 20:
        raise ValueError("Neck registration insufficient")
    rms = float(np.sqrt(np.mean(np.sum((src @ matrix[:,:2].T + matrix[:,2] - dst)[inliers[:,0]>0]**2,axis=1))))
    if rms > 2:
        raise ValueError("Neck registration exceeds source-pixel tolerance")
    return {"native_affine":matrix.tolist(), "source_size":[moving.shape[1],moving.shape[0]],
            "matches":len(matches), "inliers":int(inliers.sum()), "rms_source_pixels":rms,
            "method":"SIFT/RANSAC on upper head only; not anatomical approval"}


def page(reg: dict) -> str:
    source = (EXPERIMENT / "C/project/index.html").read_text(encoding="utf-8")
    html = source.replace("story-c", "story-d")
    old_patch = '<svg class="neck-underlay" viewBox="0 0 1920 1080"><path d="M1435 635 L1578 650 L1545 772 L1460 770 L1425 685Z" fill="#b17a55"/></svg>'
    if old_patch not in html:
        raise ValueError("Reviewed C program changed; rebase the revision explicitly")
    html = html.replace(old_patch, '')
    html = html.replace(".head,.torso,.neck-underlay", ".head,.torso")
    html = html.replace('<div class="head">', f'''<div class="head"><div class="neck-surface"><img class="neck-extension" src="assets/{NECK}" alt=""></div>''')
    html = html.replace('</div></div></main>', '''</div><div class="torso collar-front"></div></div></main>''')
    html = html.replace('</style>', '''
    .head{z-index:20}
    .head .neutral{mask-image:linear-gradient(to bottom,#000 0px,#000 333px,transparent 350px)}
    .neck-surface{position:absolute;left:0;top:0;width:420px;height:505px;clip-path:polygon(40% 64%,76% 64%,88% 100%,38% 100%)}
    .head .neck-extension{transform-origin:0 0}
    .face-light{clip-path:polygon(0 0,100% 0,100% 75%,0 75%)}
    .collar-front{z-index:30;background:url(assets/person-body.png) 0 0/630px 840px no-repeat;clip-path:polygon(280px 390px,510px 390px,510px 610px,280px 610px)}
    </style>''')
    m = reg["native_affine"]
    scale = 420 / 1238
    width, height = reg["source_size"]
    html = html.replace('</style>', f'''.head .neck-extension{{width:{width*scale}px;height:{height*scale}px;transform:matrix({m[0][0]},{m[1][0]},{m[0][1]},{m[1][1]},{m[0][2]*scale},{m[1][2]*scale})}}</style>''')
    return html


def build():
    draw_order = ["torso","head_and_neck","collar-front"]
    if occlusion_findings(draw_order,"head_and_neck","collar-front"):
        raise ValueError("Collar must cover neck before rendering")
    approval = json.loads((EXPERIMENT / "C/human-review-lighting-acting.json").read_text(encoding="utf-8"))
    if sha256(EXPERIMENT / "C/comparison.mp4") != approval["video_sha256"]:
        raise ValueError("Approved performance artifact changed")
    root = EXPERIMENT / "D"
    target = root / "project/assets"
    target.mkdir(parents=True, exist_ok=True)
    for asset in (EXPERIMENT / "C/project/assets").glob("*.png"):
        shutil.copy2(asset,target / asset.name)
    shutil.copy2(ASSETS / NECK,target / NECK)
    shutil.copy2(GSAP,target / GSAP.name)
    reg = registration()
    (root / "project/index.html").write_text(page(reg),encoding="utf-8")
    meta = json.loads((EXPERIMENT / "C/project/meta.json").read_text())
    meta["name"] = "story-d"
    (root / "project/meta.json").write_text(json.dumps(meta),encoding="utf-8")
    render("D")
    receipt = {"version":"collar-occlusion-0.1", "production_ready":False,"human_review":"PENDING",
        "source_performance_sha256":approval["video_sha256"],
        "video_sha256":sha256(root / "comparison.mp4"),
        "neck_asset_sha256":sha256(target / NECK),
        "program_sha256":sha256(root / "project/index.html"),
        "motion_parent":"head", "occluder":"collar-front", "draw_order":draw_order,
        "join":{"covered_layer":"head_and_neck","line_owner":"collar-front",
            "overlap_extent":"Authored broad neck tail below the original visible collar; limited to the approved 0 to 1.8 degree head rotation",
            "occluder_scene_bounds":[1430,625,230,220]},
        "registration":reg,
        "paid_api_calls":0,"builtin_image_edits":2,
        "limits":["Small approved head motion only", "Authored masked neck surface; not a general deformable rig", "Landmark fit is not anatomical approval"]}
    (root / "receipt.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    from verify_light_pollution_collar import verify
    if verify()["findings"]:
        raise ValueError("Rendered collar checks require revision; see D/verification.json")


if __name__ == "__main__":
    build()
