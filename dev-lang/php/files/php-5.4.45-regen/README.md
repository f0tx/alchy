# php-5.4.45 — происхождение и регенерация патчей

Пакет `dev-lang/php-5.4.45` в оверлее `::alchy`. Ebuild: `php-5.4.45.ebuild`,
патчи: `files/php-5.4.45/*.patch` (18 шт, включая 00165).

## Происхождение

- Исходник: официальный `php-5.4.45.tar.bz2` (www.php.net/distributions, sha256 `4e0d28b1…`).
  Backports-ветка 5.4 отсутствует, поэтому берётся релизный тарбол.
- База патчей: `php-5.6.40-patches-4.tar.xz` → пересадка на 5.4 через `regen54.sh`
  (последовательное применение с fuzz=5, сбор реджектов, автоправки fixpayload, регенерация diff).
- Патч `00165_threads-m4-autoconf273.patch` создан вручную: заменяет блок
  `PTHREADS_CHECK_COMPILE/PTHREADS_CHECK` в `TSRM/threads.m4` версией из 5.6-дерева.

## Зачем 00165 (главная грабля)

autoconf 2.73 (на guard) генерирует из 5.4-версии `TSRM/threads.m4` синтаксически битый
`configure`: в m4-теле AC_CACHE_CHECK(pthreads_cflags) был лишний `fi`, а `AC_TRY_RUN`
старого образца. autoconf 2.69 (из тарбола) это прощал, 2.73 — нет (`bash -n` падает,
configure рушится «unexpected end of file»). Патч переносит исправленные макросы из 5.6.

## Прочие ручные фиксы при пересадке (fixpayload54.py)

- `00010` — whitelist bison продлён до 3.10 (в 5.4 список обрывался на 2.6.4).
- `00040` — `PHP_SETUP_ICU` переписан на `PKG_CHECK_MODULES([ICU],[icu-io >= 50.1])`.
- `00130`/`00140` — ICU boolean/C++17-совместимость.
- `00170` — минус дубль `protected int` перед `file_replace` в `ext/fileinfo/libmagic/funcs.c`
  (в 5.4 строка уже присутствует, патч 5.6 вставлял вторую).
- `00180` — правки под `wddx.c`.
- `00200` — сигнатуры/вызовы в `ext/gd/gd_ctx.c`, `ext/gd/gd.c` (+ отдельный блок правок для `_php_image_create_from`).
- `00200`, адаптация под bundled libgd 5.4 (у 5.6-патча расчёт на libgd 5.6): вырезана старая
  WEBP-ветка, ioctx-путь и вызовы `func_p`/`ioctx_func_p` переведены на единые 5/7-арг формы,
  call-sites `imagecreatefromwebp`/`imagecreatefromgd2part` — на обёртки; в обёртках
  `JpegEx`→`Jpeg` (в libgd 5.4 нет `*Ex`-вариантов) и `JpegCtx(io_ctx, INI_INT(...))`
  (в 5.4 у неё 2 аргумента). Симптом ошибки до правки: `too few arguments to function
  'ioctx_func_p'/'func_p'` при сборке с USE=gd. Проверено: jpg/png/gif/gd2/gd2part/
  imagecreatefromstring/wbmp/exif — работают.
- Остальные патчи применяются к 5.4 как есть (после fuzz).

Все правки валидируются через `once()` — при несоответствии числа совпадений fixpayload падает,
это и есть страховка от молчаливых регрессий.

## Компилятор

GCC 16 на guard использует `-std=gnu23` по умолчанию; 5.4-код старше. В ebuild добавлено:

    append-cflags -std=gnu17 -Wno-error=incompatible-pointer-types \
        -Wno-error=implicit-function-declaration -Wno-error=implicit-int -Wno-error=int-conversion
    append-cxxflags -std=gnu++17 -Wno-error=incompatible-pointer-types

(тот же приём, что в рабочем php-7.2.34.)

## Регенерация набора

    # на guard, от root:
    mkdir -p /tmp/p54 && cd /tmp/p54
    # pristine-дерево:
    mkdir -p pristine && tar xjf /var/cache/distfiles/php-5.4.45.tar.bz2 -C pristine --strip-components=1
    # reference-набор патчей 5.6.40 (patches-4) c добавленным 00165:
    mkdir -p ref/patches && tar xJf /var/cache/distfiles/php-5.6.40-patches-4.tar.xz -C ref --strip-components=1
    cp .../00165_threads-m4-autoconf273.patch ref/patches/
    cp fixpayload54.py /tmp/p54/
    bash regen54.sh          # генерирует /tmp/p54/newpatches/*.patch + контрольное применение

Результат копируется в `files/php-5.4.45/`, затем:

    ebuild php-5.4.45.ebuild manifest

## Проверка (smoke)

Собранный интерпретатор: `/usr/lib64/php5.4/bin/php`. Проверено: json, iconv, fileinfo,
dom, dba(gdbm), zip, bz2, mbstring, mcrypt, phar, gmp, hash — работают.

## Известное

- USE-строка в `/etc/portage/package.use/php` для 5.4.45 не содержит `cgi`/`fpm`
  (и содержит опечатку `-gmm`) — собирается cli-вариант (по желанию править там).
- Сборка идёт только с тарболом в distfiles: php.net с guard недоступен (CDN), качать на newton.

## Файлы в этой папке

- `fixpayload54.py` — автоправки по патчам (см. список выше).
- `regen54.sh` — полный цикл пересадки/регенерации/контроля.
- `00165_threads-m4-autoconf273.patch` — исходник для ref-набора (в files/php-5.4.45/ не нужен,
  там уже лежит).