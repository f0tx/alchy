import sys, os, re, shutil
name = sys.argv[1]; B = sys.argv[2]
PRI = '/tmp/pristine'

def path(rel): return os.path.join(B, rel)
def once(s, needle, label=""):
    assert s.count(needle) == 1, (label or needle[:50], s.count(needle))

FIX = {}
def fix(pname):
    def deco(f): FIX[pname] = f; return f
    return deco

@fix('00040_intl-detect-icu-via-pkg-config.patch')
def _f(b):
    shutil.copy(PRI + '/ext/intl/config.m4', path('ext/intl/config.m4'))

@fix('00060_intl-icu-memory-corruption.patch')
def _f(b):
    shutil.copy(PRI + '/ext/intl/msgformat/msgformat_helpers.cpp',
                path('ext/intl/msgformat/msgformat_helpers.cpp'))
    t = path('ext/intl/tests/bug74484_MessageFormatter.phpt')
    if os.path.exists(t): return
    rej = open('/tmp/fz72/ext/intl/tests/bug74484_MessageFormatter.phpt.rej').read()
    body = [l[1:] for l in rej.split('\n') if l.startswith('+')][1:]
    open(t, 'w').write('\n'.join(body) + '\n')

@fix('00130_icu-boolean-fix.patch')
def _f(b):
    p = path('ext/intl/config.m4'); s = open(p).read()
    if '-DU_DEFINE_FALSE_AND_TRUE=1' in s: return
    old = 'INTL_COMMON_FLAGS="$ICU_INCS -Wno-write-strings -D__STDC_LIMIT_MACROS -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1"'
    once(s, old, 'INTL_COMMON_FLAGS')
    open(p, 'w').write(s.replace(old, old[:-1] + ' -DU_DEFINE_FALSE_AND_TRUE=1"'))

@fix('00140_icu-cxx17.patch')
def _f(b):
    p = path('ext/intl/config.m4'); s = open(p).read()
    m = re.search(r'\n  AC_MSG_CHECKING\(\[if intl requires -std=gnu\+\+17\]\).*?\n  \]\)\n', s, re.S)
    if m:
        block = s[m.start():m.end()]
        s = s[:m.start()] + '\n' + s[m.end():]
    else:
        block = ('\n  AC_MSG_CHECKING([if intl requires -std=gnu++17])\n'
                 '  AS_IF([test "$PKG_CONFIG icu-uc --atleast-version=74"], [\n'
                 '    AC_MSG_RESULT([yes])\n'
                 '    PHP_INTL_CPP_FLAGS="$PHP_INTL_CPP_FLAGS -std=gnu++17"\n'
                 '  ], [\n'
                 '    AC_MSG_RESULT([no])\n'
                 '    PHP_INTL_CPP_FLAGS="$PHP_INTL_CPP_FLAGS -std=gnu++11"\n'
                 '  ])\n')
    block = block.replace('PHP_INTL_CPP_FLAGS', 'PHP_INTL_CXX_FLAGS')
    anchor = 'PHP_INTL_CXX_FLAGS="$INTL_COMMON_FLAGS $ICU_CXXFLAGS"\n'
    once(s, anchor, 'CXX_FLAGS anchor')
    s = s.replace(anchor, anchor.rstrip('\n') + '\n' + block)
    open(p, 'w').write(s)

@fix('00150_libxml2-2.12.patch')
def _f(b):
    p = path('ext/libxml/libxml.c'); s = open(p).read()
    if 'int compression ZEND_ATTRIBUTE_UNUSED)' in s: return
    old = 'int compression ATTRIBUTE_UNUSED)'
    once(s, old, 'ATTRIBUTE_UNUSED')
    open(p, 'w').write(s.replace(old, 'int compression ZEND_ATTRIBUTE_UNUSED)'))

@fix('00170_gcc14.patch')
def _f(b):
    p = path('acinclude.m4'); s = open(p).read()
    if 'PHP_READDIR_R_TYPE' in s:
        i = s.index('\ndnl\ndnl PHP_READDIR_R_TYPE')
        j = s.index('\ndnl\ndnl PHP_TM_GMTOFF')
        assert 0 < i < j and 'AC_DEFUN([PHP_READDIR_R_TYPE]' in s[i:j]
        s = s[:i] + s[j:]
    subs = [
        ('dnl even newer glibcs have a different seeker definition...',
         'dnl Even newer glibcs have a different seeker definition.'),
        ('AC_TRY_RUN([\n#define _GNU_SOURCE\n#include <stdio.h>\n\nstruct cookiedata {',
         'AC_RUN_IFELSE([AC_LANG_SOURCE([[\n#define _GNU_SOURCE\n#include <stdio.h>\n\nstruct cookiedata {'),
        ('  __off64_t pos;', '  off64_t pos;'),
        ('__ssize_t reader(', 'ssize_t reader('),
        ('__ssize_t writer(', 'ssize_t writer('),
        ('int seeker(void *cookie, __off64_t *position, int whence)',
         'int seeker(void *cookie, off64_t *position, int whence)'),
        ('cookie_io_functions_t funcs = {reader, writer, seeker, closer};\n\nmain() {',
         'cookie_io_functions_t funcs = {reader, writer, seeker, closer};\n\nint main() {'),
        ('== 8192)\n    exit(0);\n  exit(1);', '== 8192)\n    return 0;\n  return 1;'),
        ('}\n\n], [\n  cookie_io_functions_use_off64_t=yes',
         '}\n\n]])], [\n  cookie_io_functions_use_off64_t=yes'),
        ('])\n    \n\n    else', '])\n\n\n    else'),
        ('dnl older glibc versions (up to 2.1.2 ?)\ndnl call it _IO_cookie_io_functions_t\nAC_TRY_COMPILE([',
         'dnl Older glibc versions (up to 2.1.2?) call it _IO_cookie_io_functions_t.\nAC_COMPILE_IFELSE([AC_LANG_PROGRAM([['),
        ('], [ _IO_cookie_io_functions_t cookie; ], [have_IO_cookie_io_functions_t=yes], [])',
         ']], [[_IO_cookie_io_functions_t cookie;]])], [have_IO_cookie_io_functions_t=yes], [])'),
    ]
    for old, new in subs:
        if old in s and new not in s:
            s = s.replace(old, new)
    open(p, 'w').write(s)
    p = path('configure.ac'); s = open(p).read()
    if 'PHP_READDIR_R_TYPE\n' in s:
        once(s, 'PHP_READDIR_R_TYPE\n', 'configure.ac')
        open(p, 'w').write(s.replace('PHP_READDIR_R_TYPE\n', '', 1))
    p = path('Zend/zend_language_parser.y'); s = open(p).read()
    if not s.startswith('%require'):
        s = '%require "3.0"\n' + s
    if '%pure-parser\n' in s:
        s = s.replace('%pure-parser\n', '%define api.pure full\n%define parse.error verbose\n', 1)
    elif '%define api.pure' not in s:
        raise AssertionError('parser.y unknown state')
    open(p, 'w').write(s)
    p = path('ext/mbstring/libmbfl/filters/mbfilter_utf8_mobile.c'); s = open(p).read()
    dbl = ('int mbfl_filt_put_invalid_char(int c, mbfl_convert_filter *filter);\n'
           'int mbfl_filt_put_invalid_char(int c, mbfl_convert_filter *filter);\n')
    if dbl in s:
        open(p, 'w').write(s.replace(dbl, dbl.split('\n')[0] + '\n'))
    # funcs.c: убрать кривую вставку protected int, поставить его перед file_replace
    p = path('ext/fileinfo/libmagic/funcs.c'); s = open(p).read()
    s = s.replace('\tsize_t len;\n\n\nprotected int\n\tif (level', '\tsize_t len;\n\n\tif (level')
    if 'protected int\nfile_replace(' not in s:
        s = s.replace('\nfile_replace(struct magic_set *ms, const char *pat, const char *rep)',
                      '\nprotected int\nfile_replace(struct magic_set *ms, const char *pat, const char *rep)')
    open(p, 'w').write(s)
    # acinclude: __ssize_t -> ssize_t
    p = path('acinclude.m4'); s = open(p).read()
    s = s.replace('__ssize_t reader(', 'ssize_t reader(').replace('__ssize_t writer(', 'ssize_t writer(')
    open(p, 'w').write(s)

@fix('00180_gcc14_2.patch')
def _f(b):
    p = path('TSRM/TSRM.h'); s = open(p).read()
    ext = 'extern __thread void ***tsrm_ls;'
    # убрать из C++-ветки, если попал туда
    bad = '#if defined(__cplusplus) && __cplusplus > 199711L\n' + ext + '\n\n# define TSRM_TLS thread_local'
    if bad in s:
        s = s.replace(bad, '#if defined(__cplusplus) && __cplusplus > 199711L\n# define TSRM_TLS thread_local')
    if ext not in s:
        anchor = '#define TSRM_UNSHUFFLE_RSRC_ID(rsrc_id)\t\t((rsrc_id)-1)\n'
        once(s, anchor, 'UNSHUFFLE')
        s = s.replace(anchor, anchor + '\n' + ext + '\n')
    open(p, 'w').write(s)

if name in FIX:
    FIX[name](B)
print("fix: %s ok" % name)
