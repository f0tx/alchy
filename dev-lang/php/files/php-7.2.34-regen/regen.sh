set -u
SER=/var/db/repos/alchy/dev-lang/php/files/php-7.2.34
R=/tmp/reg4; OUT=/tmp/newpatches
rm -rf $R $OUT; mkdir -p $R/b $OUT
tar xf /var/cache/distfiles/php-7.2.34.tar.xz -C $R/b --strip-components=1
for p in "$SER"/[0-9]*.patch; do
  nm=$(basename "$p")
  rm -rf $R/a; cp -a $R/b $R/a
  (cd $R/b && patch -p1 -f --fuzz=5 --no-backup-if-mismatch < "$p" > /tmp/apply.log 2>&1) || true
  python3 /tmp/fixpayload.py "$nm" "$R/b" >/dev/null || echo "FIXFAIL $nm"
  find $R/b -name '*.rej' -delete; find $R/b -name '*.orig' -delete
  (cd $R && diff -urN a b > /tmp/newdiff.tmp) || true
  if [ -s /tmp/newdiff.tmp ]; then
    python3 - "$p" /tmp/newdiff.tmp "$OUT/$nm" <<'PY'
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
CHK=/tmp/check2; rm -rf $CHK; mkdir -p $CHK
tar xf /var/cache/distfiles/php-7.2.34.tar.xz -C $CHK --strip-components=1
cd $CHK
fail=0
for p in $OUT/*.patch; do
  [ -s "$p" ] || { echo "SKIP $nm"; continue; }
  if patch -p1 -f -g0 --no-backup-if-mismatch < "$p" > /tmp/chk.log 2>&1; then
    echo "OK   $(basename $p)"
  else
    fail=1; echo "FAIL $(basename $p)"; grep -m3 "FAILED\|can't find" /tmp/chk.log
    patch -p1 -f -g0 --no-backup-if-mismatch < "$p" >/dev/null 2>&1
  fi
done
echo "fail=$fail"
find $CHK -name '*.rej' -delete; find $CHK -name '*.orig' -delete
echo "=== сверка дерева:"
diff -r --brief $CHK /tmp/reg4/b | head; echo "(пусто = идентично)"
