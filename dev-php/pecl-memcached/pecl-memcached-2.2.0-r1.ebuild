# Copyright 1999-2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
#
# Локальная сборка dev-php/pecl-memcached 2.2.0 под PHP 5.6 (штатный ebuild
# собирает только php8-x). memcached 2.2.0 — последняя ветка с поддержкой PHP 5.x.

EAPI=8
PHP_EXT_NAME="memcached"
DOCS=( ChangeLog README.markdown )

USE_PHP="php5-6"
PHP_EXT_NEEDED_USE="json(+)?,session(-)?"

inherit php-ext-pecl-r3

DESCRIPTION="Interface PHP with memcached via libmemcached library"
LICENSE="PHP-3.01"
SLOT="5.6"
KEYWORDS="~amd64"
IUSE="igbinary json sasl +session"

COMMON_DEPEND="|| ( dev-libs/libmemcached-awesome[sasl(-)?] >=dev-libs/libmemcached-1.0.14[sasl(-)?] )
	virtual/zlib:=
	igbinary? ( dev-php/igbinary[php_targets_php5-6(-)?] )
"
DEPEND="${COMMON_DEPEND}"
RDEPEND="${COMMON_DEPEND}"
BDEPEND="${COMMON_DEPEND}"

src_configure() {
	append-cflags -std=gnu17 -Wno-error=incompatible-pointer-types \
		-Wno-error=implicit-function-declaration -Wno-error=implicit-int \
		-Wno-error=int-conversion

	local PHP_EXT_ECONF_ARGS="--enable-memcached
		$(use_enable session memcached-session)
		$(use_enable sasl memcached-sasl)
		$(use_enable json memcached-json)
		$(use_enable igbinary memcached-igbinary)"

	php-ext-source-r3_src_configure
}
