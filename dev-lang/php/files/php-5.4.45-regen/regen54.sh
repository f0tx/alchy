#!/bin/bash
# пересадка набора патчей 5.6->5.4.45: последовательно, с фаззингом, с регенерацией и сбором реджектов
set -u
SER=/tmp/p54/ref/patches
PRI=/tmp/p54/pristine/php-5.4.45
R=/tmp/p54/reg; OUT=/tmp/p54/newpatches; REJ=/tmp/p54/rejstore
rm -rf $R $OUT $REJ; mkdir -p $R/b $OUT $REJ
tar xjf /var/cache/distfiles/php-5.4.45.tar.bz2 -C $R/b --strip-components=1
for p in "$SER"/[0-9]*.patch; do
  nm=$(basename "$p")
  rm -rf $R/a; cp -a $R/b $R/a
  (cd $R/b && patch -p1 -f --fuzz=5 --no-backup-if-mismatch < "$p" > /tmp/p54/apply_"$nm".log 2>&1) || echo "PARTFAIL $nm"
  if find $R/b -name '*.rej' | grep -q .; then
    echo "REJ $nm: $(find $R/b -name '*.rej' | sed "s|$R/b/||" | tr '\n' ' ')"
    mkdir -p $REJ/$nm
    for r in $(find $R/b -name '*.rej'); do cp "$r" $REJ/$nm/$(echo "$r" | sed "s|$R/b/||;s|/|__|g"); done
  fi
  find $R/b -name '*.rej' -delete; find $R/b -name '*.orig' -delete
  if [ -f /tmp/p54/fixpayload54.py ]; then
    python3 /tmp/p54/fixpayload54.py "$nm" "$R/b" >/dev/null 2>/tmp/p54/fixerr.tmp || { echo "FIXFAIL $nm"; cat /tmp/p54/fixerr.tmp; }
  fi
  (cd $R && diff -urN a b > /tmp/p54/newdiff.tmp) || true
  if [ -s /tmp/p54/newdiff.tmp ]; then
    python3 - "$p" /tmp/p54/newdiff.tmp "$OUT/$nm" <<'PY'
import sys
orig, difff, out = sys.argv[1], sys.argv[2], sys.argv[3]
o = open(orig, errors='replace').read()
d = open(difff, errors='replace').read()
hdr = []
for ln in o.split('\n'):
    if ln.startswith('diff ') or ln.startswith('--- '):
        break
    hdr.append(ln)
h = '\n'.join(hdr).rstrip('\n')
open(out, 'w').write((h + '\n' if h.strip() else '') + d)
PY
    echo "PATCH $nm -> $(wc -l < $OUT/$nm) строк"
  else
    : > "$OUT/$nm"; echo "PATCH $nm -> ПУСТО"
  fi
done
echo "=== контроль: последовательное применение на pristine:"
CHK=/tmp/p54/check; rm -rf $CHK; mkdir -p $CHK
tar xjf /var/cache/distfiles/php-5.4.45.tar.bz2 -C $CHK --strip-components=1
cd $CHK
fail=0
for p in $OUT/*.patch; do
  [ -s "$p" ] || continue
  if patch -p1 -f -g0 --no-backup-if-mismatch < "$p" > /tmp/p54/chk.log 2>&1; then
    echo "OK   $(basename $p)"
  else
    fail=1; echo "FAIL $(basename $p)"; grep -m3 "FAILED\|can't find" /tmp/p54/chk.log
  fi
done
find $CHK -name '*.rej' -delete; find $CHK -name '*.orig' -delete
echo "fail=$fail"
echo "=== сверка дерева:"; diff -r --brief $CHK /tmp/p54/reg/b | head; echo "(пусто = идентично)"