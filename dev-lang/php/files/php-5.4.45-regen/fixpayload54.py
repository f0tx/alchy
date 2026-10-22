import sys, os, re, shutil
name = sys.argv[1]; B = sys.argv[2]
PRI = '/tmp/p54/pristine/php-5.4.45'

def path(rel): return os.path.join(B, rel)
def ppri(rel): return os.path.join(PRI, rel)
def once(s, needle, label=""):
    assert s.count(needle) == 1, (label or needle[:60], s.count(needle))

FIX = {}
def fix(pname):
    def deco(f): FIX[pname] = f; return f
    return deco

@fix('00010_no-bison-warnings.patch')
def _f(b):
    p = path('Zend/acinclude.m4'); s = open(p).read()
    old = '2.5 2.5.1 2.6 2.6.1 2.6.2 2.6.4"'
    once(s, old, 'bison list')
    s = s.replace(old, '2.5 2.5.1 2.6 2.6.1 2.6.2 2.6.4 2.7 2.8 3.0 3.1 3.2 3.3 3.4 3.5 3.6 3.7 3.8 3.9 3.10"')
    open(p, 'w').write(s)

@fix('00040_intl-detect-icu-via-pkg-config.patch')
def _f(b):
    # --- acinclude.m4: PHP_SETUP_ICU через pkg-config ---
    p = path('acinclude.m4'); s = open(p).read()
    i = s.index('AC_DEFUN([PHP_SETUP_ICU],[')
    j = s.index('\n])\n', i) + len('\n])\n')
    new = (
'\nAC_DEFUN([PHP_SETUP_ICU],[\n'
'  PKG_CHECK_MODULES([ICU], [icu-io >= 50.1])\n'
'\n'
'  PHP_EVAL_INCLINE($ICU_CFLAGS)\n'
'  PHP_EVAL_LIBLINE($ICU_LIBS, $1)\n'
'\n'
'  ICU_CFLAGS="$ICU_CFLAGS -DU_NO_DEFAULT_INCLUDE_UTF_HEADERS=1"\n'
'  ICU_CXXFLAGS="$ICU_CXXFLAGS -DUNISTR_FROM_CHAR_EXPLICIT=explicit -DUNISTR_FROM_STRING_EXPLICIT=explicit"\n'
'\n'
'  # provide icu_version for the spoofchecker check in ext/intl/config.m4\n'
'  icu_version_full=`$PKG_CONFIG icu-uc --modversion`\n'
'  ac_IFS=$IFS\n'
'  IFS="."\n'
'  set $icu_version_full\n'
'  IFS=$ac_IFS\n'
'  icu_version=`expr [$]1 \\* 1000 + [$]2`\n'
'\n'
'  ICU_INCS="$ICU_CFLAGS"\n'
'\n'
'  if test "$PKG_CONFIG icu-io --atleast-version=60"; then\n'
'    ICU_CFLAGS="$ICU_CFLAGS -DU_HIDE_OBSOLETE_UTF_OLD_H=1"\n'
'  fi\n'
'\n'
'])\n')
    s = s[:i] + new + s[j:]
    open(p, 'w').write(s)

    # --- ext/intl/config.m4: пересборка из pristine + правки ---
    t = open(ppri('ext/intl/config.m4')).read()
    once(t, '  PHP_REQUIRE_CXX()\n', 'cxx')
    t = t.replace('  PHP_REQUIRE_CXX()\n',
        '  PHP_REQUIRE_CXX()\n'
        '  INTL_COMMON_FLAGS="$ICU_CFLAGS -Wno-write-strings -D__STDC_LIMIT_MACROS -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1"\n', 1)
    once(t, '    msgformat/msgformat_helpers.cpp \\\n', 'cpp line')
    t = t.replace('    msgformat/msgformat_helpers.cpp \\\n', '', 1)
    once(t, '    $icu_spoof_src, $ext_shared,,$ICU_INCS)\n', 'tail')
    t = t.replace('    $icu_spoof_src, $ext_shared,,$ICU_INCS)\n',
                  '    $icu_spoof_src, $ext_shared,,$INTL_COMMON_FLAGS)\n', 1)
    anchor = '  PHP_ADD_BUILD_DIR($ext_builddir/collator)\n'
    once(t, anchor, 'anchor')
    block = (
'  PHP_INTL_CPP_SOURCES="msgformat/msgformat_helpers.cpp"\n'
'\n'
'  PHP_INTL_CPP_FLAGS="$ICU_CXXFLAGS -Wno-write-strings -D__STDC_LIMIT_MACROS -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1"\n'
'  if test "$ext_shared" = "no"; then\n'
'    PHP_ADD_SOURCES(PHP_EXT_DIR(intl), $PHP_INTL_CPP_SOURCES, $PHP_INTL_CPP_FLAGS)\n'
'  else\n'
'    PHP_ADD_SOURCES_X(PHP_EXT_DIR(intl), $PHP_INTL_CPP_SOURCES, $PHP_INTL_CPP_FLAGS, shared_objects_intl, yes)\n'
'  fi\n'
'\n')
    t = t.replace(anchor, block + anchor, 1)
    open(path('ext/intl/config.m4'), 'w').write(t)

@fix('00130_icu-boolean-fix.patch')
def _f(b):
    p = path('ext/intl/config.m4'); s = open(p).read()
    defflag = ' -DU_DEFINE_FALSE_AND_TRUE=1'
    lines = s.split('\n')
    for i, ln in enumerate(lines):
        if ('INTL_COMMON_FLAGS="' in ln or 'PHP_INTL_CPP_FLAGS="' in ln) and 'U_DEFINE_FALSE_AND_TRUE' not in ln and ln.endswith('"'):
            lines[i] = ln[:-1] + defflag + '"'
    s = '\n'.join(lines)
    assert s.count(defflag) == 2, s.count(defflag)
    open(p, 'w').write(s)

@fix('00140_icu-cxx17.patch')
def _f(b):
    p = path('ext/intl/config.m4'); s = open(p).read()
    # 1) вычистить любые ранее вставленные блоки cxx17 (могут стоять криво)
    lines = s.split('\n'); out = []; i = 0
    while i < len(lines):
        if 'if intl requires -std=gnu++17' in lines[i]:
            j = i
            while lines[j].strip() != '])':
                j += 1
            i = j + 1
            continue
        out.append(lines[i]); i += 1
    lines = out
    # 2) вставить канонический блок сразу после строки PHP_INTL_CPP_FLAGS
    idx = [i for i, ln in enumerate(lines) if ln.startswith('  PHP_INTL_CPP_FLAGS="')]
    assert len(idx) == 1, idx
    block = [
        '  AC_MSG_CHECKING([if intl requires -std=gnu++17])',
        '  AS_IF([$PKG_CONFIG icu-uc --atleast-version=74], [',
        '    AC_MSG_RESULT([yes])',
        '    PHP_INTL_CPP_FLAGS="$PHP_INTL_CPP_FLAGS -std=gnu++17"',
        '  ], [',
        '    AC_MSG_RESULT([no])',
        '    PHP_INTL_CPP_FLAGS="$PHP_INTL_CPP_FLAGS -std=gnu++11"',
        '  ])',
    ]
    lines[idx[0]+1:idx[0]+1] = block
    open(p, 'w').write('\n'.join(lines))

@fix('00170_gcc14.patch')
def _f(b):
    p = path('ext/fileinfo/libmagic/funcs.c'); s = open(p).read()
    old = 'protected int\n\nprotected int \nfile_replace('
    once(s, old, 'funcs dup protected')
    s = s.replace(old, 'protected int\nfile_replace(')
    open(p, 'w').write(s)

@fix('00180_gcc14_2.patch')
def _f(b):
    p = path('ext/wddx/wddx.c'); s = open(p).read()
    old = 'const char *class_name, *prop_name;'
    once(s, old, 'wddx decl')
    s = s.replace(old, 'const char *class_name;\n\t\t\t\tchar *prop_name;')
    old2 = 'zend_unmangle_property_name(key, key_len-1, &class_name, &prop_name);'
    once(s, old2, 'wddx call')
    s = s.replace(old2, 'zend_unmangle_property_name(key, key_len-1, &class_name, (const char **) &prop_name);')
    open(p, 'w').write(s)

GD_WRAPPERS = '''static void php_gd_output_xbm_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) filter;
\tgdImageXbmCtx(im, filename ? filename : "", quality, ctx);
}

static void php_gd_output_gif_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) quality;
\t(void) filter;
\t(void) filename;
\tgdImageGifCtx(im, ctx);
}

#ifdef HAVE_GD_PNG
static void php_gd_output_png_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) filename;
\tgdImagePngCtxEx(im, ctx, quality, filter);
}
#endif

#ifdef HAVE_GD_WEBP
static void php_gd_output_webp_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) filter;
\t(void) filename;
\tgdImageWebpCtx(im, ctx, quality);
}
#endif

#ifdef HAVE_GD_JPG
static void php_gd_output_jpeg_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) filter;
\t(void) filename;
\tgdImageJpegCtx(im, ctx, quality);
}
#endif

static void php_gd_output_wbmp_ctx(gdImagePtr im, gdIOCtx *ctx, int quality, int filter, char *filename)
{
\t(void) filter;
\t(void) filename;
\tgdImageWBMPCtx(im, quality, ctx);
}

static void php_gd_output_gd(gdImagePtr im, FILE *fp, int quality, int type)
{
\t(void) quality;
\t(void) type;
\tgdImageGd(im, fp);
}

static void php_gd_output_gd2(gdImagePtr im, FILE *fp, int quality, int type)
{
\tgdImageGd2(im, fp, quality, type);
}

static void php_gd_output_bw_convert(gdImagePtr im, FILE *fp, int quality, int type)
{
\tgdIOCtx *ctx;

\t(void) type;
\tctx = gdNewFileCtx(fp);
\tif (!ctx) {
\t\treturn;
\t}

\t_php_image_bw_convert(im, ctx, quality);
\tctx->gd_free(ctx);
}
'''

@fix('00200_gcc15.patch')
def _f(b):
    # --- gd.c ---
    p = path('ext/gd/gd.c'); s = open(p).read()
    old_sig = 'static void _php_image_output(INTERNAL_FUNCTION_PARAMETERS, int image_type, char *tn, void (*func_p)())'
    once(s, old_sig, 'gd output sig')
    s = s.replace(old_sig, 'static void _php_image_output(INTERNAL_FUNCTION_PARAMETERS, int image_type, char *tn, php_gd_image_output_func func_p)')
    anchor = '/* {{{ _php_image_output\n'
    once(s, anchor, 'gd output anchor')
    s = s.replace(anchor, GD_WRAPPERS + '\n' + anchor, 1)
    reps = [
        ('\t\t\t\tgdImageWBMP(im, q, fp);\n', '\t\t\t\t(*func_p)(im, fp, q, t);\n'),
        ('\t\t\t\t(*func_p)(im, fp, q);\n', '\t\t\t\t(*func_p)(im, fp, q, t);\n'),
        ('\t\t\t\t(*func_p)(im, i, fp);\n', '\t\t\t\t(*func_p)(im, fp, i, t);\n'),
        ('\t\t\t\t(*func_p)(im, fp);\n', '\t\t\t\t(*func_p)(im, fp, q, t);\n'),
        ('\t\t\t\tgdImageWBMP(im, q, tmp);\n', '\t\t\t\t(*func_p)(im, tmp, q, t);\n'),
        ('\t\t\t\t(*func_p)(im, tmp, q);\n', '\t\t\t\t(*func_p)(im, tmp, q, t);\n'),
    ]
    for old, new in reps:
        once(s, old, 'gd call %s' % old.strip()[:40])
        s = s.replace(old, new)
    open(p, 'w').write(s)
    # --- gd_ctx.c ---
    p = path('ext/gd/gd_ctx.c'); s = open(p).read()
    old1 = '\t\t\tif (image_type == PHP_GDIMG_TYPE_XBM) {\n\t\t\t\t(*func_p)(im, file, q, ctx);\n\t\t\t} else {\n\t\t\t\t(*func_p)(im, q, ctx);\n\t\t\t}\n'
    once(s, old1, 'gd_ctx xbm')
    s = s.replace(old1, '\t\t\t(*func_p)(im, ctx, q, f, file ? file : "");\n')
    old2 = '\t\tdefault:\n\t\t\t(*func_p)(im, ctx);\n'
    once(s, old2, 'gd_ctx default')
    s = s.replace(old2, '\t\tdefault:\n\t\t\t(*func_p)(im, ctx, q, f, file ? file : "");\n')
    open(p, 'w').write(s)

if name in FIX:
    FIX[name](B)
print("fix: %s ok" % name)