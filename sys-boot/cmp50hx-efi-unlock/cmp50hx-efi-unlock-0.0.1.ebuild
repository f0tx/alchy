# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

inherit toolchain-funcs

DESCRIPTION="UEFI compute unlock application for NVIDIA CMP 50HX (TU102)"
HOMEPAGE="https://github.com/xrip/cmp50hx-unlock"
SRC_URI="https://github.com/xrip/cmp50hx-unlock/archive/refs/heads/master.tar.gz -> ${P}.tar.gz"

LICENSE="copyleft-next-0.3.1"
SLOT="0"
KEYWORDS="~amd64"
IUSE=""

DEPEND="sys-boot/gnu-efi"
RDEPEND=""

PATCHES=( "${FILESDIR}/cmp50hx-efi-unlock-fix.patch" )

S="${WORKDIR}/cmp50hx-unlock-master"

src_prepare() {
    default
}

src_configure() {
    :
}

src_compile() {
    local efi_inc="/usr/include/efi"
    local efi_lib="/usr/lib64"

    if [[ ! -d "${efi_inc}" ]]; then
        die "gnu-efi headers not found at ${efi_inc}"
    fi

    cd "${S}/efi-unlock" || die

    emake CC="$(tc-getCC)" \
        EFI_INC="${efi_inc}" \
        EFI_LIB="${efi_lib}" \
        SCRIPT_DIR="${FILESDIR}" \
        -f "${FILESDIR}/build-efi.mk"
}

src_install() {
    insinto /usr/lib/cmp50hx-efi-unlock
    doins "${S}/efi-unlock/50HXUNLK.EFI"

    dodoc "${S}/README.md" "${S}/README.RU.md" "${S}/findings.md" "${S}/efi-unlock/README.md"
    newdoc "${S}/efi-unlock/runs/20260910-ab-stock-vs-efi.md" results-ab-stock-vs-efi.md
}

pkg_postinst() {
    elog "CMP 50HX EFI unlock application installed."
    elog ""
    elog "To deploy to the ESP:"
    elog "  1. Mount your EFI System Partition (e.g., /boot/efi)"
    elog "  2. Create directory: backslash-EFI-backslash-50HX-backslash"
    elog "  3. Copy: /usr/lib/cmp50hx-efi-unlock/50HXUNLK.EFI -> /boot/efi/EFI/50HX/50HXUNLK.EFI"
    elog "  4. Add boot entry: efibootmgr -c -d /dev/nvme0n1 -p 1 -l 'backslash-EFI-backslash-50HX-backslash-50HXUNLK.EFI' -L 'CMP 50HX Unlock'"
    elog "  5. Set BootNext to the unlock entry before rebooting"
    elog ""
    elog "WARNING: This is experimental firmware-level code. It modifies GPU state"
    elog "pre-OS. Ensure you have a way to recover before deploying."
    elog "The unlock is volatile and does not persist across reboots."
    elog ""
    elog "Tested hardware: CMP 50HX (10de:1e09) with subsystem 10de:1554 or 1462:371f."
    elog "Your card may have a different subsystem - proceed with caution."
}
