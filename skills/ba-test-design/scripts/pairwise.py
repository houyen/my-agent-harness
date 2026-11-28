#!/usr/bin/env python3
"""Sinh bộ test tổ hợp tối thiểu (pairwise hoặc t-way) từ một model JSON. Chỉ dùng thư viện chuẩn, không mạng.

  pairwise.py model.json [--strength 2] [--format json|md]

model.json:
  {"parameters": {"Đăng nhập": ["đúng", "sai"], "2FA": ["bật", "tắt"]},
   "forbidden": [{"Đăng nhập": "sai", "2FA": "bật"}]}      # tuỳ chọn: tổ hợp KHÔNG được xuất hiện cùng nhau

Thuật toán tham lam, kết quả tất định (cùng model → cùng bộ test). Không đảm bảo số dòng nhỏ nhất tuyệt đối.
"""
import argparse
import itertools
import json
import sys


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            model = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"không đọc được model {path}: {e}")
    params = model.get("parameters")
    if not isinstance(params, dict) or not params:
        sys.exit("model thiếu 'parameters'")
    for name, vals in params.items():
        if not isinstance(vals, list) or not vals or len(set(map(str, vals))) != len(vals):
            sys.exit(f"tham số {name}: cần danh sách giá trị không rỗng, không trùng")
    forbidden = model.get("forbidden", [])
    for f in forbidden:
        for k, v in f.items():
            if k not in params or v not in params[k]:
                sys.exit(f"forbidden nhắc tới giá trị không có trong model: {k}={v}")
    return params, forbidden


def violates(assign, forbidden):
    return any(all(assign.get(k) == v for k, v in f.items()) for f in forbidden)


def generate(params, forbidden, strength=2):
    names = list(params)
    if not 1 <= strength <= len(names):
        raise ValueError("strength phải trong khoảng 1..số tham số")
    uncovered = set()
    for cols in itertools.combinations(names, strength):
        for vals in itertools.product(*(params[c] for c in cols)):
            combo = tuple(zip(cols, vals))
            if not violates(dict(combo), forbidden):
                uncovered.add(combo)
    total = len(uncovered)
    rows, skipped = [], 0
    order = sorted(uncovered, key=lambda c: [(n, str(v)) for n, v in c])
    while uncovered:
        seed = next(c for c in order if c in uncovered)
        row = dict(seed)
        ok = True
        for name in names:
            if name in row:
                continue
            best, best_gain = None, -1
            for v in params[name]:
                trial = dict(row)
                trial[name] = v
                if violates(trial, forbidden):
                    continue
                gain = sum(1 for c in uncovered if all(trial.get(k) == x for k, x in c) and name in dict(c))
                if gain > best_gain:
                    best, best_gain = v, gain
            if best is None:
                ok = False
                break
            row[name] = best
        if not ok or violates(row, forbidden):
            # tham lam bí đường: thử vét cạn phần còn lại trước khi coi tổ hợp là không đạt được
            rest = [n for n in names if n not in dict(seed)]
            row = None
            for vals in itertools.product(*(params[n] for n in rest)):
                cand = {**dict(seed), **dict(zip(rest, vals))}
                if not violates(cand, forbidden):
                    row = cand
                    break
            if row is None:
                uncovered.discard(seed)
                skipped += 1
                continue
        rows.append({n: row[n] for n in names})
        uncovered -= {c for c in uncovered if all(row[k] == x for k, x in c)}
    return rows, total, skipped


def feasible(combo, params, forbidden):
    """Có ít nhất một dòng đầy đủ chứa combo mà không vi phạm forbidden không."""
    fixed = dict(combo)
    rest = [n for n in params if n not in fixed]
    return any(not violates({**fixed, **dict(zip(rest, vals))}, forbidden)
               for vals in itertools.product(*(params[n] for n in rest)))


def covers(rows, params, forbidden, strength=2):
    """Kiểm độc lập: mọi tổ hợp đạt được đều xuất hiện trong ít nhất một dòng, và không dòng nào vi phạm."""
    names = list(params)
    seen = {tuple(zip(cols, (r[c] for c in cols))) for r in rows for cols in itertools.combinations(names, strength)}
    for cols in itertools.combinations(names, strength):
        for vals in itertools.product(*(params[c] for c in cols)):
            combo = tuple(zip(cols, vals))
            if combo not in seen and feasible(combo, params, forbidden):
                return False
    return not any(violates(r, forbidden) for r in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model")
    ap.add_argument("--strength", type=int, default=2)
    ap.add_argument("--format", choices=["json", "md"], default="json")
    args = ap.parse_args()
    params, forbidden = load(args.model)
    try:
        rows, total, skipped = generate(params, forbidden, args.strength)
    except ValueError as e:
        sys.exit(str(e))
    stats = {"parameters": len(params), "strength": args.strength, "combinations_to_cover": total,
             "tests": len(rows), "full_cartesian": _product(params), "unreachable_combinations": skipped}
    if args.format == "json":
        print(json.dumps({"stats": stats, "tests": rows}, ensure_ascii=False, indent=2))
    else:
        names = list(params)
        print("| # | " + " | ".join(names) + " |")
        print("|---|" + "---|" * len(names))
        for i, r in enumerate(rows, 1):
            print(f"| {i} | " + " | ".join(str(r[n]) for n in names) + " |")
        print(f"\n{len(rows)} test thay cho {stats['full_cartesian']} tổ hợp đầy đủ ({total} cặp cần phủ, bỏ qua {skipped} không đạt được).")


def _product(params):
    n = 1
    for v in params.values():
        n *= len(v)
    return n


if __name__ == "__main__":
    main()
