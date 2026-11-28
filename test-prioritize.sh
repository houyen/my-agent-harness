#!/usr/bin/env bash
# Test skills/po-prioritize/scripts/score.py: điểm RICE/WSJF đúng số tay, thứ hạng, hoà điểm, sức chứa, lỗi đầu vào.
set -uo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/prio-test.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  ok  $1"; else FAIL=$((FAIL+1)); echo "  NO  $1"; fi; }
S=skills/po-prioritize/scripts/score.py
cat > "$TMP/rice.json" <<'J'
{"method":"rice","items":[
 {"id":"A","name":"Hoàn tiền","reach":800,"impact":2,"confidence":0.8,"effort":4},
 {"id":"B","name":"Báo cáo","reach":300,"impact":1,"confidence":1,"effort":1},
 {"id":"C","name":"Dark mode","reach":1000,"impact":0.5,"confidence":0.4,"effort":2},
 {"id":"D","name":"Đổi hàng","reach":200,"impact":3,"confidence":0.5,"effort":6}]}
J
# tay: A=800*2*0.8/4=320  B=300*1*1/1=300  C=1000*0.5*0.4/2=100  D=200*3*0.5/6=50
o="$(python3 -I "$S" "$TMP/rice.json")"
ok "RICE: thứ tự A,B,C,D" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);assert [r[\"id\"] for r in d[\"ranked\"]]==[\"A\",\"B\",\"C\",\"D\"]" "$o"'
ok "RICE: điểm đúng số tay" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);s={r[\"id\"]:r[\"score\"] for r in d[\"ranked\"]};assert s==({\"A\":320.0,\"B\":300.0,\"C\":100.0,\"D\":50.0})" "$o"'
ok "cảnh báo độ tin cậy thấp (C)" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);c=[r for r in d[\"ranked\"] if r[\"id\"]==\"C\"][0];assert any(\"tin cậy\" in w for w in c[\"warnings\"])" "$o"'
ok "tất định" '[ "$(python3 -I "$S" "$TMP/rice.json")" = "$o" ]'
o2="$(python3 -I "$S" "$TMP/rice.json" --capacity 5)"
# A(4) vừa, B(1) vừa → 5; C(2) vượt; D(6) vượt
ok "capacity 5: A,B vừa; C,D không" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);f={r[\"id\"]:r[\"fits_capacity\"] for r in d[\"ranked\"]};assert f=={\"A\":True,\"B\":True,\"C\":False,\"D\":False} and d[\"capacity_used\"]==5" "$o2"'
cat > "$TMP/wsjf.json" <<'J'
{"method":"wsjf","items":[
 {"id":"X","name":"x","business_value":8,"time_criticality":5,"risk_reduction":3,"job_size":4},
 {"id":"Y","name":"y","business_value":3,"time_criticality":2,"risk_reduction":1,"job_size":1}]}
J
# X=16/4=4  Y=6/1=6
o3="$(python3 -I "$S" "$TMP/wsjf.json")"
ok "WSJF: Y trước X, điểm 6 và 4" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);r=d[\"ranked\"];assert [x[\"id\"] for x in r]==[\"Y\",\"X\"] and r[0][\"score\"]==6.0 and r[1][\"score\"]==4.0" "$o3"'
cat > "$TMP/tie.json" <<'J'
{"method":"wsjf","items":[
 {"id":"B","business_value":2,"time_criticality":2,"risk_reduction":2,"job_size":2},
 {"id":"A","business_value":3,"time_criticality":3,"risk_reduction":0,"job_size":2}]}
J
o4="$(python3 -I "$S" "$TMP/tie.json")"
ok "hoà điểm: xếp theo id, có cảnh báo" 'python3 -c "import json,sys;d=json.loads(sys.argv[1]);r=d[\"ranked\"];assert r[0][\"id\"]==\"A\" and any(\"hoà\" in w for w in r[0][\"warnings\"])" "$o4"'
ok "--format md ra bảng" '[[ "$(python3 -I "$S" "$TMP/rice.json" --format md --capacity 5)" == "| Hạng | Mã"* ]]'
bad(){ python3 -I "$S" "$1" >/dev/null 2>&1; [ $? -ne 0 ]; }
echo '{"method":"rice","items":[{"id":"A","reach":1,"impact":1,"confidence":1,"effort":0}]}' > "$TMP/b1.json"; ok "từ chối effort = 0" 'bad "$TMP/b1.json"'
echo '{"method":"rice","items":[{"id":"A","reach":1,"impact":1,"confidence":1.5,"effort":1}]}' > "$TMP/b2.json"; ok "từ chối confidence > 1" 'bad "$TMP/b2.json"'
echo '{"method":"rice","items":[{"id":"A","reach":"nhiều","impact":1,"confidence":1,"effort":1}]}' > "$TMP/b3.json"; ok "từ chối giá trị không phải số" 'bad "$TMP/b3.json"'
echo '{"method":"rice","items":[{"id":"A","reach":1,"impact":1,"confidence":1,"effort":1},{"id":"A","reach":1,"impact":1,"confidence":1,"effort":1}]}' > "$TMP/b4.json"; ok "từ chối id trùng" 'bad "$TMP/b4.json"'
echo '{"method":"moscow","items":[]}' > "$TMP/b5.json"; ok "từ chối method lạ" 'bad "$TMP/b5.json"'
echo 'khong phai json' > "$TMP/b6.json"; ok "từ chối JSON hỏng" 'bad "$TMP/b6.json"'
echo '{"method":"rice","items":[{"id":"A","reach":1,"impact":1,"confidence":true,"effort":1}]}' > "$TMP/b7.json"; ok "từ chối boolean thay số" 'bad "$TMP/b7.json"'
echo; echo "TỔNG: $((PASS+FAIL)) test · $PASS PASS · $FAIL FAIL"
[ "$FAIL" -eq 0 ]
