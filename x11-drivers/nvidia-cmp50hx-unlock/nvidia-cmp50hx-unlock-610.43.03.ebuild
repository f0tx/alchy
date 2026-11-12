# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

inherit linux-mod-r1

DESCRIPTION="NVIDIA Open GPU kernel modules 610.43.03 with CMP 50HX unlock patches"
HOMEPAGE="https://github.com/xrip/cmp50hx-unlock https://github.com/NVIDIA/open-gpu-kernel-modules"

# NVIDIA Open GPU kernel modules source
SRC_URI="https://github.com/NVIDIA/open-gpu-kernel-modules/archive/refs/tags/${PV}.tar.gz -> ${P}-nvidia-src.tar.gz"

LICENSE="MIT NVIDIA"
SLOT="0/${PV}"
KEYWORDS="~amd64"
IUSE=""

# Dependencies for building
DEPEND="sys-devel/gcc
        sys-devel/binutils"
RDEPEND=""

# The source directory inside the tarball
S="${WORKDIR}/open-gpu-kernel-modules-${PV}"

# Patches from xrip/cmp50hx-unlock repo
PATCHES=(
    "${FILESDIR}/common/01-nvidia-kernel-string-api.patch"
    "${FILESDIR}/cmp50hx/01-cmp50-stockflow.patch"
    "${FILESDIR}/cmp50hx/02-cmp50-rt-core-count.patch"
    "${FILESDIR}/cmp50hx/03-cmp50-rebar.patch"
    "${FILESDIR}/cmp50hx/04-cmp50-pcie-gen2.patch"
    "${FILESDIR}/cmp50hx/05-rtx2080ti-rebar.patch"
    "${FILESDIR}/cmp50hx/06-aikitoria-p2p.patch"
    "${FILESDIR}/cmp50hx/07-turing-p2p.patch"
    "${FILESDIR}/cmp50hx/08-cmp50-driver-profiling.patch"
    "${FILESDIR}/cmp50hx/09-cmp50-mailbox-high-address.patch"
)

# NOTE: 05-cmp50-auto-pstate.patch is deliberately NOT applied.
# It pins the card at P8 even at 100% load and breaks the idle governor.

# Kernel module targets to build
MODULES_TARGETS="nvidia nvidia-uvm nvidia-modeset nvidia-drm nvidia-peermem"

src_configure() {
    : # No configure step needed for NVIDIA kernel modules
}

src_compile() {
    if [[ ! -d "${KV_DIR}" ]]; then
        die "Kernel headers not found at ${KV_DIR}"
    fi

    # Gentoo's default LDFLAGS includes -Wl,-O1 which binutils 2.47
    # does not support. Override with empty LDFLAGS.
    # NVIDIA Makefile expects ARCH=x86_64, not amd64.
    emake \
        KERNEL_UNAME="${KV_FULL}" \
        ARCH=x86_64 \
        LDFLAGS="" \
        modules \
        -j"${JOBS}"
}

src_install() {
    local mod
    for mod in ${MODULES_TARGETS}; do
        if [[ -f "kernel-open/${mod}.ko" ]]; then
            insinto "/lib/modules/${KV_FULL}/updates"
            doins "kernel-open/${mod}.ko"
        fi
    done

    # Install build script and patches for reference
    insinto "/usr/share/doc/${PF}"
    doins "${FILESDIR}/build.sh"
    newdoc "${FILESDIR}/cmp50hx/01-cmp50-stockflow.patch" 01-cmp50-stockflow.patch
    newdoc "${FILESDIR}/cmp50hx/02-cmp50-rt-core-count.patch" 02-cmp50-rt-core-count.patch
    newdoc "${FILESDIR}/cmp50hx/03-cmp50-rebar.patch" 03-cmp50-rebar.patch
    newdoc "${FILESDIR}/cmp50hx/04-cmp50-pcie-gen2.patch" 04-cmp50-pcie-gen2.patch
}

pkg_postinst() {
    elog "NVIDIA CMP 50HX unlock modules installed."
    elog ""
    elog "To load the patched modules:"
    elog "  1. Unload stock modules: modprobe -r nvidia-drm nvidia-modeset nvidia-uvm nvidia"
    elog "  2. Load patched modules: modprobe nvidia"
    elog "  3. Verify: nvidia-smi"
    elog ""
    elog "To make permanent at boot, ensure /lib/modules/${KV_FULL}/updates/nvidia.ko"
    elog "is loaded instead of the stock module."
    elog ""
    elog "WARNING: This is experimental firmware-level code. The unlock modifies"
    elog "GPU compute state. Ensure you have a way to recover (serial console,"
    elog "second GPU, etc.) before deploying."
    elog ""
    elog "Tested hardware: CMP 50HX (10de:1e09). Your card's subsystem ID may"
    elog "vary - proceed with caution."
}
