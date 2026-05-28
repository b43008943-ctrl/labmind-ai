"""Minimal recall counter — writes JSON output"""
import json, os, sys, cv2, numpy as np, torch, torchvision
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

def audit(image_path, label):
    p = V1Provider()
    img = cv2.imread(image_path)
    if img is None: return None
    h, w = img.shape[:2]
    q = p.quality_check(img)
    if q["quality_status"] == "rejected": return {"rejected": True}

    tile_size = 640; overlap = int(tile_size*0.25); step = tile_size - overlap
    gboxes, gscores, gclasses = [], [], []
    raw = 0; edge_rej = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            ye, xe = min(y+tile_size,h), min(x+tile_size,w)
            tile = img[y:ye,x:xe]
            if tile.shape[0]<100 or tile.shape[1]<100: continue
            for r in p._yolo_model(tile, conf=0.05, imgsz=tile_size, verbose=False):
                bx = r.boxes.xyxy.cpu().numpy(); sc = r.boxes.conf.cpu().numpy(); cl = r.boxes.cls.cpu().numpy()
                for i in range(len(bx)):
                    raw += 1
                    tx1,ty1,tx2,ty2 = map(int,bx[i])
                    if tx1<=5 or ty1<=5 or tx2>=tile.shape[1]-5 or ty2>=tile.shape[0]-5:
                        edge_rej += 1; continue
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
    med_a = float(np.median(ra)) if ra else 0; med_w = float(np.median(rw2)) if rw2 else 0; med_h = float(np.median(rh2)) if rh2 else 0

    db,dc,ds = [],[],[]
    ws=0
    for i,b in enumerate(vb):
        cn=YOLO_CLASS_MAP.get(vc[i],"?")
        if cn in("rbc","sickle") and med_w>0:
            bw,bh=b[2]-b[0],b[3]-b[1]
            if bw>1.5*med_w or bh>1.5*med_h:
                ws+=1
                for sc in p._watershed_decluster(img,b,med_a,w,h):
                    db.append(sc); dc.append(vc[i]); ds.append(vs[i])
                continue
        db.append(b); dc.append(vc[i]); ds.append(vs[i])

    ok=0; none_cnt=0; exc_cnt=0; sickle_dets=[]
    detected=[]
    for i,b in enumerate(db):
        cn=YOLO_CLASS_MAP.get(dc[i],"?"); conf=ds[i]
        if cn in("rbc","sickle"):
            try:
                cd=p._classify_rbc(img,b,dc[i],conf,med_a,w,h)
                if cd: ok+=1; detected.append(cd)
                else: none_cnt+=1
            except: exc_cnt+=1
        else:
            ok+=1; detected.append({"class_name":cn,"x1":int(b[0]),"y1":int(b[1]),"x2":int(b[2]),"y2":int(b[3])})

    # dedup
    final=[]; dd=0
    for c in detected:
        cx2=(c["x1"]+c["x2"])/2; cy2=(c["y1"]+c["y2"])/2; dup=False
        for f in final:
            if f["class_name"]!=c["class_name"]: continue
            if np.sqrt((cx2-(f["x1"]+f["x2"])/2)**2+(cy2-(f["y1"]+f["y2"])/2)**2)<15: dup=True; break
        if not dup: final.append(c)
        else: dd+=1

    fs=sum(1 for c in final if c.get("class_name")=="sickle")
    fr=sum(1 for c in final if c.get("class_name")=="rbc")

    sick_info = []
    for s in [c for c in final if c.get("class_name")=="sickle"]:
        sick_info.append({"box":[s["x1"],s["y1"],s["x2"],s["y2"]],"conf":s.get("confidence",0),"cnn":s.get("cnn_probability",0),
            "ar":s.get("aspect_ratio",0),"circ":s.get("circularity",0),"sol":s.get("solidity",0),
            "border": s["x1"]<=3 or s["y1"]<=3 or s["x2"]>=w-3 or s["y2"]>=h-3})

    return {"label":label,"raw":raw,"edge_rej":edge_rej,"after_edge":len(gboxes),"after_nms":len(vb),
            "after_ws":len(db),"ws_split":ws,"classify_ok":ok,"classify_none":none_cnt,"classify_exc":exc_cnt,
            "dedup_removed":dd,"final":len(final),"sickle":fs,"rbc":fr,"median_area":med_a,"sickle_details":sick_info}

if __name__=="__main__":
    tests=[]
    nd="validation_smears/normal"
    if os.path.isdir(nd):
        for f in sorted(os.listdir(nd))[:2]: tests.append((os.path.join(nd,f),"NORMAL_"+f))
    sd="validation_smears/sickle"
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd))[:2]: tests.append((os.path.join(sd,f),"SICKLE_"+f))
    m="test_images/Sickle_Cell_Blood_Smear.jpg"
    if os.path.isfile(m): tests.append((m,"SICKLE_MAIN"))
    results=[]
    for path,lbl in tests:
        r=audit(path,lbl)
        if r: results.append(r)
    with open("recall_results.json","w") as f: json.dump(results,f,indent=2)
    print("Done. Results in recall_results.json")
