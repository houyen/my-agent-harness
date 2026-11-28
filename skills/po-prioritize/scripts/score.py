#!/usr/bin/env python3
"""Chấm điểm và xếp hạng backlog theo RICE hoặc WSJF. Chỉ dùng thư viện chuẩn, không mạng, không ghi file.

  score.py backlog.json [--format json|md] [--capacity N]

backlog.json:
  {"method": "rice",  "items": [{"id": "FR-1", "name": "...", "reach": 800, "impact": 2, "confidence": 0.8, "effort": 3}]}
  {"method": "wsjf",  "items": [{"id": "FR-2", "name": "...", "business_value": 8, "time_criticality": 5,
                                  "risk_reduction": 3, "job_size": 5}]}

RICE = reach * impact * confidence / effort.  WSJF = (business_value + time_criticality + risk_reduction) / job_size.
--capacity N: đi từ hạng 1 xuống, đánh dấu mục còn vừa tổng công sức (effort hoặc job_size) <= N.
Điểm chỉ phản ánh số bạn đưa vào: số ước lượng sai thì thứ hạng sai.
"""
import argparse
import json
import sys

FIELDS = {
    "rice": ("reach", "impact", "confidence", "effort"),
    "wsjf": ("business_value", "time_criticality", "risk_reduction", "job_size"),
}
RICE_IMPACT_SCALE = (0.25, 0.5, 1, 2, 3)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"không đọc được {path}: {e}")
    method = data.get("method")
    if method not in FIELDS:
        sys.exit("method phải là 'rice' hoặc 'wsjf'")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        sys.exit("thiếu danh sách 'items'")
    seen = set()
    for it in items:
        iid = it.get("id")
        if not iid or iid in seen:
            sys.exit(f"id thiếu hoặc trùng: {iid!r}")
        seen.add(iid)
        for f in FIELDS[method]:
            v = it.get(f)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                sys.exit(f"{iid}: '{f}' phải là số (đang là {v!r})")
            if v < 0:
                sys.exit(f"{iid}: '{f}' không được âm")
        size = it["effort" if method == "rice" else "job_size"]
        if size <= 0:
            sys.exit(f"{iid}: công sức/kích thước phải lớn hơn 0")
        if method == "rice" and not 0 <= it["confidence"] <= 1:
            sys.exit(f"{iid}: confidence phải nằm trong 0..1")
    return method, items


def score(method, it):
    if method == "rice":
        return it["reach"] * it["impact"] * it["confidence"] / it["effort"]
    return (it["business_value"] + it["time_criticality"] + it["risk_reduction"]) / it["job_size"]


def warnings(method, it, tied):
    out = []
    if method == "rice":
        if it["confidence"] < 0.5:
            out.append("độ tin cậy thấp (<0.5)")
        if it["impact"] not in RICE_IMPACT_SCALE:
            out.append("impact ngoài thang 0.25/0.5/1/2/3")
        if it["reach"] == 0:
            out.append("reach bằng 0")
    if tied:
        out.append("hoà điểm với mục khác")
    return out


def rank(method, items, capacity=None):
    scored = [(score(method, it), it) for it in items]
    scored.sort(key=lambda p: (-p[0], str(p[1]["id"])))
    counts = {}
    for s, _ in scored:
        counts[round(s, 9)] = counts.get(round(s, 9), 0) + 1
    rows, used = [], 0.0
    key = "effort" if method == "rice" else "job_size"
    for pos, (s, it) in enumerate(scored, 1):
        row = {"rank": pos, "id": it["id"], "name": it.get("name", ""), "score": round(s, 2),
               "warnings": warnings(method, it, counts[round(s, 9)] > 1)}
        if capacity is not None:
            if used + it[key] <= capacity:
                used += it[key]
                row["fits_capacity"] = True
            else:
                row["fits_capacity"] = False
        rows.append(row)
    return rows, used


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("backlog")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--capacity", type=float)
    args = ap.parse_args()
    if args.capacity is not None and args.capacity < 0:
        sys.exit("--capacity không được âm")
    method, items = load(args.backlog)
    rows, used = rank(method, items, args.capacity)
    if args.format == "json":
        print(json.dumps({"method": method, "capacity_used": used if args.capacity is not None else None, "ranked": rows},
                         ensure_ascii=False, indent=2))
        return
    cap = args.capacity is not None
    print("| Hạng | Mã | Tên | Điểm | " + ("Vừa sức chứa | " if cap else "") + "Lưu ý |")
    print("|---|---|---|---|" + ("---|" if cap else "") + "---|")
    for r in rows:
        fit = (("có" if r["fits_capacity"] else "không") + " | ") if cap else ""
        print(f"| {r['rank']} | {r['id']} | {r['name']} | {r['score']} | {fit}{'; '.join(r['warnings'])} |")
    if cap:
        print(f"\nĐã dùng {used:g} / {args.capacity:g}.")


if __name__ == "__main__":
    main()
