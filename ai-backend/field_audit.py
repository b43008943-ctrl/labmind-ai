"""Field consistency audit — compares pipeline stages between fields"""
import json, os, sys, cv2, numpy as np, torch, torchvision
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

def field_audit(image_path, label):
    p = V1Provider()
    img = cv2.imread(image_path)
    if img is None: return None
    h, w = img.shape[:2]
    q = p.quality_check(img)

    # Stage 1: YOLO detection
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

    # Stage 2: NMS
    vb,vc,vs = [],[],[]
    if gboxes:
        keep = torchvision.ops.batched_nms(torch.tensor(gboxes,dtype=torch.float32),torch.tensor(gscores,dtype=torch.float32),torch.tensor(gclasses,dtype=torch.int64),0.35)
        for idx in keep:
            i=idx.item(); vb.append(gboxes[i]); vc.append(gclasses[i]); vs.append(gscores[i])

    # Stage 3: Median + watershed
    ra = []; rw2 = []; rh2 = []
    for i,b in enumerate(vb):
        cn=YOLO_CLASS_MAP.get(vc[i],"?")
        if cn in("rbc","sickle"): ra.append((b[2]-b[0])*(b[3]-b[1])); rw2.append(b[2]-b[0]); rh2.append(b[3]-b[1])
    med_a = float(np.median(ra)) if ra else 0
    med_w = float(np.median(rw2)) if rw2 else 0
    med_h = float(np.median(rh2)) if rh2 else 0

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

    # Stage 4: Classification with gate tracking
    ok=0; none_cnt=0; exc_cnt=0
    detected=[]
    # Track gate rejections
    cnn_sickle_total = 0  # CNN said sickle (regardless of gates)
    gate_morph_veto = 0    # blocked by morphology_veto
    gate_border = 0        # blocked by border
    gate_dual_fail = 0     # CNN sickle but morphology_abnormal=False and light_ar<1.10
    gate_cnn_low = 0       # CNN sickle prob < 0.55
    gate_passed = 0        # classified as sickle

    rbc_candidates = 0
    for i,b in enumerate(db):
        cn=YOLO_CLASS_MAP.get(dc[i],"?"); conf=ds[i]
        if cn in("rbc","sickle"):
            rbc_candidates += 1
            try:
                cd=p._classify_rbc(img,b,dc[i],conf,med_a,w,h)
                if cd:
                    ok+=1; detected.append(cd)
                    # Track CNN classification
                    cnn_prob = cd.get("cnn_class_probabilities",{}).get("sickle",0)
                    if cnn_prob >= 0.50:
                        cnn_sickle_total += 1
                    if cd.get("class_name") == "sickle":
                        gate_passed += 1
                    elif cnn_prob >= 0.55:
                        # CNN said sickle but was blocked — why?
                        ar = cd.get("aspect_ratio",0)
                        circ = cd.get("circularity",0)
                        sol = cd.get("solidity",0)
                        if ar > 0 and ar < 1.15 and circ > 0.80 and sol > 0.90:
                            gate_morph_veto += 1
                        elif cd.get("x1",99) <= 3 or cd.get("y1",99) <= 3:
                            gate_border += 1
                        else:
                            gate_dual_fail += 1
                    elif 0.50 <= cnn_prob < 0.55:
                        gate_cnn_low += 1
                else:
                    none_cnt+=1
            except:
                exc_cnt+=1
        else:
            ok+=1; detected.append({"class_name":cn,"x1":int(b[0]),"y1":int(b[1]),"x2":int(b[2]),"y2":int(b[3])})

    # Stage 5: Dedup
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

    # Morphology distribution of sickle detections
    sick_morphs = []
    for c in final:
        if c.get("class_name")=="sickle":
            sick_morphs.append({"conf":round(c.get("confidence",0),3),"cnn":round(c.get("cnn_probability",0),3),
                "ar":round(c.get("aspect_ratio",0),2),"circ":round(c.get("circularity",0),2),
                "sol":round(c.get("solidity",0),2)})

    # Morphology distribution of normal RBCs (sample)
    norm_morphs = []
    for c in final[:20]:
        if c.get("class_name")=="rbc" and c.get("aspect_ratio",0) > 0:
            norm_morphs.append({"ar":round(c.get("aspect_ratio",0),2),"circ":round(c.get("circularity",0),2),
                "sol":round(c.get("solidity",0),2),"cnn_sick":round(c.get("cnn_class_probabilities",{}).get("sickle",0),3)})

    return {
        "label": label,
        "img_size": [w, h],
        "quality": q["quality_score"],
        "stage1_raw": raw,
        "stage1_edge_rej": edge_rej,
        "stage2_after_nms": len(vb),
        "stage3_after_ws": len(db),
        "stage3_ws_split": ws,
        "stage4_rbc_candidates": rbc_candidates,
        "stage4_classify_ok": ok,
        "stage4_classify_none": none_cnt,
        "stage4_classify_exc": exc_cnt,
        "stage5_dedup_removed": dd,
        "final_total": len(final),
        "final_sickle": fs,
        "final_rbc": fr,
        "median_area": round(med_a, 1),
        "gates": {
            "cnn_sickle_candidates": cnn_sickle_total,
            "gate_morph_veto": gate_morph_veto,
            "gate_border": gate_border,
            "gate_dual_fail": gate_dual_fail,
            "gate_cnn_low": gate_cnn_low,
            "gate_passed": gate_passed
        },
        "sickle_morphs": sick_morphs[:5],
        "normal_sample_morphs": norm_morphs[:5]
    }

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
        print(f"Auditing {lbl}...", flush=True)
        r=field_audit(path,lbl)
        if r: results.append(r)
    with open("field_audit_results.json","w") as f: json.dump(results,f,indent=2)
    print("Done. Results in field_audit_results.json")
