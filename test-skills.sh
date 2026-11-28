#!/usr/bin/env bash
# test-skills.sh — kiểm cấu trúc mọi skill trong skills/: name khớp thư mục, có description, có dòng NOTICE, SHA256SUMS khớp.
cd "$(dirname "$0")" || exit 1
T=0; F=0
ok(){ T=$((T+1)); printf '  \033[1;32mok\033[0m  %s\n' "$1"; }
bad(){ T=$((T+1)); F=$((F+1)); printf '  \033[1;31mFAIL\033[0m %s\n' "$1"; }
fm(){ awk 'NR==1&&$0!="---"{exit} NR>1&&$0=="---"{exit} NR>1{print}' "$1"; }
for d in skills/*/; do
  n=$(basename "$d"); f="$d/SKILL.md"
  [ -f "$f" ] || { bad "$n: thiếu SKILL.md"; continue; }
  name=$(fm "$f" | sed -n 's/^name:[[:space:]]*//p' | head -1 | tr -d '"'"'")
  [ "$name" = "$n" ] && ok "$n: name khớp thư mục" || bad "$n: name='$name' ≠ thư mục"
  fm "$f" | grep -q '^description:' && ok "$n: có description" || bad "$n: thiếu description"
  grep -q "\`$n\`" skills/NOTICE.md && ok "$n: có trong NOTICE.md" || bad "$n: thiếu trong NOTICE.md (nguồn/giấy phép)"
done
( cd skills && shasum -a 256 -c SHA256SUMS >/dev/null 2>&1 ) && ok "SHA256SUMS khớp" || bad "SHA256SUMS lệch (chạy lại lệnh sinh trong README)"
echo; printf 'TỔNG: %d test · %d PASS · %d FAIL\n' "$T" "$((T-F))" "$F"
[ "$F" = 0 ]
