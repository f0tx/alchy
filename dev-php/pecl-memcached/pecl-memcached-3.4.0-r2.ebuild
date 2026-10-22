# Copyright 1999-2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
#
# Локальная копия dev-php/pecl-memcached-3.4.0-r1 из ::gentoo, пересобранная
# под PHP 7.4: штатный ebuild собирает только php8-x (USE_PHP), здесь слот 7.4.

EAPI=8
PHP_EXT_NAME="memcached"
DOCS=( ChangeLog README.markdown )

USE_PHP="php7-4"
PHP_EXT_NEEDED_USE="json(+)?,session(-)?"
MY_P="${PN/pecl-/}-${PV/_rc/RC}"
PHP_EXT_PECL_FILENAME="${MY_P}.tgz"

inherit php-ext-pecl-r3

DESCRIPTION="Interface PHP with memcached via libmemcached library"
LICENSE="PHP-3.01"
SLOT="7.4"
KEYWORDS="~amd64"
IUSE="igbinary json sasl +session"

IGBINARY_DEPEND=""
for slot in ${USE_PHP} ; do
	IGBINARY_DEPEND+="dev-php/igbinary[php_targets_${slot}(-)?] "
done

COMMON_DEPEND="|| ( dev-libs/libmemcached-awesome[sasl(-)?] >=dev-libs/libmemcached-1.0.14[sasl(-)?] )
	virtual/zlib:=
	igbinary? ( ${IGBINARY_DEPEND} )
"
DEPEND="${COMMON_DEPEND}"
RDEPEND="${COMMON_DEPEND}"
BDEPEND="${COMMON_DEPEND}"

src_configure() {
	local PHP_EXT_ECONF_ARGS="--enable-memcached
		$(use_enable session memcached-session)
		$(use_enable sasl memcached-sasl)
		$(use_enable json memcached-json)
		$(use_enable igbinary memcached-igbinary)"

	php-ext-source-r3_src_configure
}