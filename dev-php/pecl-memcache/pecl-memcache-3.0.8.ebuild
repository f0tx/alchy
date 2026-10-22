# Copyright 1999-2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
#
# Локальный ebuild dev-php/pecl-memcache под PHP 5.4 (в ::gentoo пакета нет).
# Старое расширение memcache: даёт обработчик сессий "memcache"; memcached 2.2.0
# под этот слот не нужен.

EAPI=8
PHP_EXT_NAME="memcache"
DOCS=( README )

USE_PHP="php5-4"
PHP_EXT_NEEDED_USE="session(-)?"

inherit flag-o-matic php-ext-pecl-r3

DESCRIPTION="Memcached extension for PHP (legacy memcache API)"
LICENSE="PHP-3.01"
SLOT="5.4"
KEYWORDS="~amd64"
IUSE="+session"

RDEPEND="virtual/zlib:="
DEPEND="${RDEPEND}"

src_configure() {
	# gnu89 обязателен: mmc_queue_remove объявлена как `inline` в заголовке и
	# определена в .c — по C99/GNU17 такой символ не экспортируется, и .so не грузится
	# с "undefined symbol: mmc_queue_remove".
	append-cflags -std=gnu89 -Wno-error=implicit-function-declaration \
		-Wno-error=implicit-int -Wno-error=int-conversion \
		-Wno-error=incompatible-pointer-types

	local PHP_EXT_ECONF_ARGS="--enable-memcache
		$(use_enable session memcache-session)
		--with-zlib-dir"

	php-ext-source-r3_src_configure
}
