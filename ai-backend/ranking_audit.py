"""Ranking audit v2 — uses actual pipeline light-pass values from _classify_rbc output"""
import json, os, sys, cv2, numpy as np, torch, torchvision
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

def ranking_audit(image_path, label):
    p = V1Provider()
    img = cv2.imread(image_path)
    if img is None: return None
    h, w = img.shape[:2]

    tile_size = 640; overlap = int(tile_size*0.25); step = tile_size - overlap
    gboxes, gscores, gclasses = [], [], []
    for y in range(0, h, step):
        for x in range(0, w, step):
            ye, xe = min(y+tile_size,h), min(x+tile_size,w)
            tile = img[y:ye,x:xe]
            if tile.shape[0]<100 or tile.shape[1]<100: continue
            for r in p._yolo_model(tile, conf=0.05, imgsz=tile_size, verbose=False):
                bx = r.boxes.xyxy.cpu().numpy(); sc = r.boxes.conf.cpu().numpy(); cl = r.boxes.cls.cpu().numpy()
                for i in range(len(bx)):
                    tx1,ty1,tx2,ty2 = map(int,bx[i])
                    if tx1<=5 or ty1<=5 or tx2>=tile.shape[1]-5 or ty2>=tile.shape[0]-5: continue
                    gboxes.append([x+tx1,y+ty1,x+tx2,y+ty2]); gscores.append(float(sc[i])); gclasses.append(int(cl[i]))

    vb,vc,vs = [],[],[]
    if gboxes:
        keep = torchvision.ops.batched_nms(torch.tensor(gboxes,dtype=torch.float32),torch.tensor(gscores,dtype=torch.float32),torch.tensor(gclasses,dtype=torch.int64),0.35)
        for idx in keep:
            i=idx.item(); vb.append(gboxes[i]); vc.append(gclasses[i]); vs.append(gscores[i])

    ra = []; rw2 = []; rh2 = []
    for i,b in enumerate(vb):
        cn=YOLO_CLASS_MAP.get(vc[i],"?")
        if cn in("rbc","sickle"): ra.append((b[2]-b[0])*(b[3]-b[1])); rw2.append(b[2]-b[0]); rh2.append(b[3]-b[1])
    med_a = float(np.median(ra)) if ra else 0
    med_w = float(np.median(rw2)) if rw2 else 0
    med_h = float(np.median(rh2)) if rh2 else 0

    db,dc,ds = [],[],[]
    for i,b in enumerate(vb):
        cn=YOLO_CLASS_MAP.get(vc[i],"?")
        if cn in("rbc","sickle") and med_w>0:
            bw,bh=b[2]-b[0],b[3]-b[1]
            if bw>1.5*med_w or bh>1.5*med_h:
                for sc in p._watershed_decluster(img,b,med_a,w,h):
                    db.append(sc); dc.append(vc[i]); ds.append(vs[i])
                continue
        db.append(b); dc.append(vc[i]); ds.append(vs[i])

    all_cells = []
    for i,b in enumerate(db):
        cn=YOLO_CLASS_MAP.get(dc[i],"?"); conf=ds[i]
        if cn in("rbc","sickle"):
            try:
                cd = p._classify_rbc(img,b,dc[i],conf,med_a,w,h)
                if cd:
                    cnn_sick = cd.get("cnn_class_probabilities", {}).get("sickle", 0)
                    all_cells.append({
                        "final": cd.get("class_name"),
                        "conf": round(cd.get("confidence", 0), 3),
                        "cnn_sick": round(cnn_sick, 3),
                        "l_ar": round(cd.get("light_ar", 0), 2),
                        "l_circ": round(cd.get("light_circ", 0), 2),
                        "l_sol": round(cd.get("light_sol", 0), 2),
                        "h_ar": round(cd.get("aspect_ratio", 0), 2),
                        "h_circ": round(cd.get("circularity", 0), 2),
                        "h_sol": round(cd.get("solidity", 0), 2),
                        "morph_score": round(cd.get("morph_score", 0), 3),
                        "composite": round(cd.get("composite_score", 0), 3),
                        "box": [b[0],b[1],b[2],b[3]]
                    })
            except:
                pass

    all_cells.sort(key=lambda x: x["composite"], reverse=True)
    sickle_cells = [c for c in all_cells if c["final"] == "sickle"]
    if sickle_cells:
        median_sm = sorted([c["morph_score"] for c in sickle_cells])[len(sickle_cells)//2]
    else:
        median_sm = 0
    missed = [c for c in all_cells if c["final"] == "rbc" and c["morph_score"] > median_sm]

    return {
        "label": label, "total": len(all_cells), "sickle_count": len(sickle_cells),
        "median_sickle_morph": median_sm, "missed_count": len(missed),
        "top5_sickle": sickle_cells[:5], "bottom5_sickle": sickle_cells[-5:] if len(sickle_cells)>5 else sickle_cells,
        "top5_missed": missed[:5]
    }

if __name__=="__main__":
    tests=[]
    nd="validation_smears/normal"
    if os.path.isdir(nd):
        for f in sorted(os.listdir(nd))[:1]: tests.append((os.path.join(nd,f),"NORMAL_"+f))
    sd="validation_smears/sickle"
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd))[:2]: tests.append((os.path.join(sd,f),"SICKLE_"+f))
    m="test_images/Sickle_Cell_Blood_Smear.jpg"
    if os.path.isfile(m): tests.append((m,"SICKLE_MAIN"))
    results=[]
    for path,lbl in tests:
        print(f"Audit: {lbl}...", flush=True)
        r=ranking_audit(path,lbl)
        if r: results.append(r)
    with open("ranking_audit_results.json","w") as f: json.dump(results,f,indent=2)
    print("Done.")
