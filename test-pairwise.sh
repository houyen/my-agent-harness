#!/usr/bin/env bash
# Test skills/ba-test-design/scripts/pairwise.py: phủ đủ cặp (kiểm độc lập), tôn trọng forbidden,
# tất định, strength 3, và từ chối model hỏng.
set -uo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pairwise-test.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  ok  $1"; else FAIL=$((FAIL+1)); echo "  NO  $1"; fi; }
S=skills/ba-test-design/scripts/pairwise.py
cat > "$TMP/m.json" <<'J'
{"parameters": {"Credentials": ["valid","invalid"], "TwoFA": ["on","off"], "Remember": ["yes","no"], "Failures": [0,1,2,3,4]},
 "forbidden": [{"Credentials":"invalid","Remember":"yes"}, {"Failures":4,"Credentials":"valid"}]}
J
python3 -I "$S" "$TMP/m.json" > "$TMP/o1.json"; ok "chạy được, rc 0" '[ $? -eq 0 ]'
python3 -I "$S" "$TMP/m.json" > "$TMP/o2.json"; ok "tất định" 'cmp -s "$TMP/o1.json" "$TMP/o2.json"'
ok "độc lập: phủ mọi cặp hợp lệ, không vi phạm forbidden" 'python3 -I - "$TMP/m.json" "$TMP/o1.json" <<PY
import json,sys,importlib.util
s=importlib.util.spec_from_file_location("pw","skills/ba-test-design/scripts/pairwise.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
model=json.load(open(sys.argv[1])); out=json.load(open(sys.argv[2]))
sys.exit(0 if m.covers(out["tests"],model["parameters"],model.get("forbidden",[])) else 1)
PY'
ok "ít dòng hơn tích Descartes" 'python3 -c "import json;d=json.load(open(\"$TMP/o1.json\"));assert d[\"stats\"][\"tests\"]<d[\"stats\"][\"full_cartesian\"]"'
python3 -I "$S" "$TMP/m.json" --strength 3 > "$TMP/o3.json"
ok "strength 3 phủ 3-way" 'python3 -I - "$TMP/m.json" "$TMP/o3.json" <<PY
import json,sys,importlib.util
s=importlib.util.spec_from_file_location("pw","skills/ba-test-design/scripts/pairwise.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
model=json.load(open(sys.argv[1])); out=json.load(open(sys.argv[2]))
sys.exit(0 if m.covers(out["tests"],model["parameters"],model.get("forbidden",[]),3) else 1)
PY'
ok "--format md ra bảng" '[[ "$(python3 -I "$S" "$TMP/m.json" --format md)" == "| # | Credentials"* ]]'
echo '{"parameters": {"A": []}}' > "$TMP/bad1.json"; python3 -I "$S" "$TMP/bad1.json" >/dev/null 2>&1; ok "từ chối tham số rỗng" '[ $? -ne 0 ]'
echo '{"parameters": {"A": [1,2]}, "forbidden": [{"A": 9}]}' > "$TMP/bad2.json"; python3 -I "$S" "$TMP/bad2.json" >/dev/null 2>&1; ok "từ chối forbidden lạ" '[ $? -ne 0 ]'
echo 'khong phai json' > "$TMP/bad3.json"; python3 -I "$S" "$TMP/bad3.json" >/dev/null 2>&1; ok "từ chối JSON hỏng" '[ $? -ne 0 ]'
python3 -I "$S" "$TMP/m.json" --strength 9 >/dev/null 2>&1; ok "từ chối strength vượt số tham số" '[ $? -ne 0 ]'
echo '{"parameters": {"A": ["x","y"], "B": ["p","q"]}, "forbidden": [{"A":"x","B":"p"}]}' > "$TMP/u.json"
o="$(python3 -I "$S" "$TMP/u.json")"; ok "tổ hợp bị cấm không xuất hiện" '! grep -q "\"A\": \"x\",\s*\"B\": \"p\"" <<<"$(tr -d "\n " <<<"$o" | sed "s/},{/}\n{/g")" || ! python3 -c "import json,sys;d=json.loads(sys.argv[1]);assert not any(r[\"A\"]==\"x\" and r[\"B\"]==\"p\" for r in d[\"tests\"])" "$o"'
ok "ngẫu nhiên 150 model (có forbidden, strength 2 và 3): luôn phủ đủ" 'python3 -I - <<PY
import random,importlib.util,sys
s=importlib.util.spec_from_file_location("pw","skills/ba-test-design/scripts/pairwise.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rnd=random.Random(7)
for i in range(150):
    n=rnd.randint(3,5)
    params={f"P{j}":[f"v{k}" for k in range(rnd.randint(2,4))] for j in range(n)}
    forb=[]
    for _ in range(rnd.randint(0,3)):
        cols=rnd.sample(list(params),rnd.randint(1,2))
        forb.append({c:rnd.choice(params[c]) for c in cols})
    for st in (2,3):
        if st>n: continue
        rows,_,_=m.generate(params,forb,st)
        if not m.covers(rows,params,forb,st):
            print("FAIL",i,st,params,forb); sys.exit(1)
PY'
echo; echo "TỔNG: $((PASS+FAIL)) test · $PASS PASS · $FAIL FAIL"
[ "$FAIL" -eq 0 ]
