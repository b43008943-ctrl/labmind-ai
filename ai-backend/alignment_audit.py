"""Alignment diagnostic — measures contour refinement box shift vs YOLO original"""
import json, os, sys, cv2, numpy as np, torch, torchvision
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

def alignment_audit(image_path, label):
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

    # Classify and measure shift
    shift_sickle = []
    shift_normal = []
    gate_rejects = {"fg_ratio": 0, "fill_ratio": 0, "centrality": 0, "contour_ar": 0, "area": 0, "blur": 0, "size": 0, "merge": 0, "no_contour": 0}

    for i,b in enumerate(db):
        cn=YOLO_CLASS_MAP.get(dc[i],"?"); conf=ds[i]
        if cn in("rbc","sickle"):
            orig_cx = (b[0]+b[2])/2; orig_cy = (b[1]+b[3])/2
            orig_w = b[2]-b[0]; orig_h = b[3]-b[1]

            # Manually do contour refinement to measure shift
            pad = 15
            rx1,ry1 = max(0,b[0]-pad), max(0,b[1]-pad)
            rx2,ry2 = min(w,b[2]+pad), min(h,b[3]+pad)
            roi = img[ry1:ry2,rx1:rx2]
            if roi.size == 0: continue
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                gate_rejects["no_contour"] += 1; continue

            # Nearest-center contour
            yolo_cx_local = orig_cx - rx1; yolo_cy_local = orig_cy - ry1
            best_contour = None; best_dist = float('inf')
            for cnt in contours:
                ca = cv2.contourArea(cnt)
                if ca < 100: continue
                M = cv2.moments(cnt)
                if M["m00"]==0: continue
                ccx = M["m10"]/M["m00"]; ccy = M["m01"]/M["m00"]
                d = np.sqrt((ccx-yolo_cx_local)**2 + (ccy-yolo_cy_local)**2)
                if d < best_dist: best_dist = d; best_contour = cnt
            if best_contour is None:
                best_contour = max(contours, key=cv2.contourArea)

            cx2, cy2, cw2, ch2 = cv2.boundingRect(best_contour)
            ref_x1 = rx1+cx2; ref_y1 = ry1+cy2
            ref_x2 = ref_x1+cw2; ref_y2 = ref_y1+ch2
            ref_cx = (ref_x1+ref_x2)/2; ref_cy = (ref_y1+ref_y2)/2

            shift_px = np.sqrt((ref_cx-orig_cx)**2 + (ref_cy-orig_cy)**2)
            shift_pct = shift_px / max(orig_w, 1) * 100

            # Run actual classification
            cd = p._classify_rbc(img,b,dc[i],conf,med_a,w,h)
            if cd:
                final = cd.get("class_name")
                entry = {"shift_px": round(shift_px,1), "shift_pct": round(shift_pct,1),
                         "cnn": round(cd.get("cnn_class_probabilities",{}).get("sickle",0),3),
                         "morph": round(cd.get("morph_score",0),3),
                         "l_ar": round(cd.get("light_ar",0),2), "l_circ": round(cd.get("light_circ",0),2)}
                if final == "sickle": shift_sickle.append(entry)
                else: shift_normal.append(entry)

    shift_sickle.sort(key=lambda x: x["shift_pct"], reverse=True)
    shift_normal.sort(key=lambda x: x["morph"], reverse=True)

    return {
        "label": label, "total_candidates": len(db),
        "sickle_count": len(shift_sickle), "normal_count": len(shift_normal),
        "avg_sickle_shift": round(np.mean([s["shift_pct"] for s in shift_sickle]),1) if shift_sickle else 0,
        "avg_normal_shift": round(np.mean([s["shift_pct"] for s in shift_normal]),1) if shift_normal else 0,
        "top5_sickle_shift": shift_sickle[:5],
        "top5_normal_high_morph": [s for s in shift_normal if s["morph"]>0.40][:5],
    }

if __name__=="__main__":
    tests=[]
    sd="validation_smears/sickle"
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd))[:1]: tests.append((os.path.join(sd,f),"SICKLE_"+f))
    m="test_images/Sickle_Cell_Blood_Smear.jpg"
    if os.path.isfile(m): tests.append((m,"SICKLE_MAIN"))
    for path,lbl in tests:
        print(f"Alignment audit: {lbl}...", flush=True)
        r=alignment_audit(path,lbl)
        if r:
            print(json.dumps(r, indent=2))
