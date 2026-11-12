#!/usr/bin/env python3
"""Convert ELF64 shared object to UEFI PE32+ EFI application image."""
import struct
import sys


def read_elf_sections(data):
    assert data[:4] == b'\x7fELF', "Not an ELF file"
    assert data[4] == 2, "Only 64-bit ELF"
    assert data[5] == 1, "Only little-endian"

    e_entry = struct.unpack_from('<Q', data, 24)[0]
    e_shoff = struct.unpack_from('<Q', data, 40)[0]
    e_shentsize = struct.unpack_from('<H', data, 58)[0]
    e_shnum = struct.unpack_from('<H', data, 60)[0]
    e_shstrndx = struct.unpack_from('<H', data, 62)[0]

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name = struct.unpack_from('<I', data, off)[0]
        sh_addr = struct.unpack_from('<Q', data, off + 16)[0]
        sh_offset = struct.unpack_from('<Q', data, off + 24)[0]
        sh_size = struct.unpack_from('<Q', data, off + 32)[0]
        sections.append({
            'name_off': sh_name, 'addr': sh_addr,
            'offset': sh_offset, 'size': sh_size,
        })

    shstr_off = sections[e_shstrndx]['offset']

    def get_name(idx):
        end = data.index(b'\x00', shstr_off + idx)
        return data[shstr_off + idx:end].decode()

    result = {}
    for s in sections:
        name = get_name(s['name_off'])
        if s['size'] > 0 and name in ('.text', '.data', '.rodata', '.sdata',
                                        '.dynamic', '.dynsym', '.dynstr',
                                        '.got.plt', '.data.rel.ro'):
            result[name] = {
                'addr': s['addr'],
                'size': s['size'],
                'data': data[s['offset']:s['offset'] + s['size']],
            }
    return e_entry, result


def align_up(val, align):
    return (val + align - 1) & ~(align - 1)


def build_pe32_efi(entry_rva, sections):
    FILE_ALIGN = 512
    SECTION_ALIGN = 0x1000
    IMAGE_BASE = 0

    sec_list = []
    for name, s in sections.items():
        sec_list.append((name, s['addr'], s['size'], s['data']))
    sec_list.sort(key=lambda x: x[1])

    num_sec = len(sec_list)

    dos_size = 64
    nt_sig_size = 4
    coff_size = 20
    opt_size = 240
    sec_table_size = num_sec * 40

    headers_size = align_up(dos_size + nt_sig_size + coff_size + opt_size + sec_table_size, FILE_ALIGN)

    sec_infos = []
    cur_r = headers_size
    max_vaddr = 0
    for name, addr, size, data in sec_list:
        vsize = align_up(size, SECTION_ALIGN)
        rsize = align_up(size, FILE_ALIGN)
        vaddr = align_up(addr, SECTION_ALIGN)
        sec_infos.append({
            'name': name, 'vaddr': vaddr, 'vsize': vsize,
            'raw_addr': cur_r, 'raw_size': rsize, 'data': data,
        })
        cur_r += rsize
        max_vaddr = max(max_vaddr, vaddr + vsize)

    size_of_image = max(align_up(cur_r, SECTION_ALIGN), max_vaddr)

    buf = bytearray(headers_size + size_of_image)

    # === DOS Header ===
    struct.pack_into('<H', buf, 0, 0x5A4D)
    struct.pack_into('<I', buf, 60, dos_size)  # e_lfanew

    # === NT Signature ===
    struct.pack_into('<I', buf, dos_size, 0x00004550)

    off = dos_size + nt_sig_size  # 68

    # === COFF File Header ===
    struct.pack_into('<H', buf, off, 0x8664); off += 2
    struct.pack_into('<H', buf, off, num_sec); off += 2
    struct.pack_into('<I', buf, off, 0); off += 4
    struct.pack_into('<I', buf, off, 0); off += 4
    struct.pack_into('<I', buf, off, 0); off += 4
    struct.pack_into('<H', buf, off, opt_size); off += 2
    struct.pack_into('<H', buf, off, 0x0002 | 0x0020 | 0x2000); off += 2

    # === PE32+ Optional Header ===
    opt_start = off
    struct.pack_into('<H', buf, opt_start, 0x20B); opt_start += 2
    struct.pack_into('<BB', buf, opt_start, 0, 0); opt_start += 2
    struct.pack_into('<I', buf, opt_start, sum(align_up(s[2], SECTION_ALIGN) for s in sec_list if s[0] == '.text')); opt_start += 4
    struct.pack_into('<I', buf, opt_start, sum(align_up(s[2], FILE_ALIGN) for s in sec_list if s[0] != '.text')); opt_start += 4
    struct.pack_into('<I', buf, opt_start, 0); opt_start += 4
    struct.pack_into('<I', buf, opt_start, entry_rva); opt_start += 4
    struct.pack_into('<I', buf, opt_start, sec_list[0][1] if sec_list else 0); opt_start += 4
    struct.pack_into('<Q', buf, opt_start, IMAGE_BASE); opt_start += 8
    struct.pack_into('<I', buf, opt_start, SECTION_ALIGN); opt_start += 4
    struct.pack_into('<I', buf, opt_start, FILE_ALIGN); opt_start += 4
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0); opt_start += 2
    struct.pack_into('<I', buf, opt_start, 0); opt_start += 4
    struct.pack_into('<I', buf, opt_start, size_of_image); opt_start += 4
    struct.pack_into('<I', buf, opt_start, headers_size); opt_start += 4
    struct.pack_into('<I', buf, opt_start, 0); opt_start += 4
    struct.pack_into('<H', buf, opt_start, 10); opt_start += 2
    struct.pack_into('<H', buf, opt_start, 0x0100); opt_start += 2
    struct.pack_into('<Q', buf, opt_start, 0x100000); opt_start += 8
    struct.pack_into('<Q', buf, opt_start, 0x1000); opt_start += 8
    struct.pack_into('<Q', buf, opt_start, 0x100000); opt_start += 8
    struct.pack_into('<Q', buf, opt_start, 0x1000); opt_start += 8
    struct.pack_into('<I', buf, opt_start, 0); opt_start += 4
    struct.pack_into('<I', buf, opt_start, 16); opt_start += 4
    for _ in range(16):
        struct.pack_into('<II', buf, opt_start, 0, 0); opt_start += 8

    # Move off to start of section table
    off = opt_start

    # === Section Table ===
    for s in sec_infos:
        buf[off:off+8] = s['name'].encode()[:8].ljust(8, b'\x00'); off += 8
        chars = 0x60000020 if s['name'] == '.text' else 0x60000040
        struct.pack_into('<I', buf, off, s['vsize']); off += 4
        struct.pack_into('<I', buf, off, s['vaddr']); off += 4
        struct.pack_into('<I', buf, off, s['raw_size']); off += 4
        struct.pack_into('<I', buf, off, s['raw_addr']); off += 4
        struct.pack_into('<II', buf, off, 0, 0); off += 8
        struct.pack_into('<HH', buf, off, 0, 0); off += 4
        struct.pack_into('<I', buf, off, chars); off += 4

    # === Section Data ===
    for s in sec_infos:
        buf[s['raw_addr']:s['raw_addr'] + len(s['data'])] = s['data']

    return bytes(buf)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.so output.efi", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        data = f.read()

    entry, sections = read_elf_sections(data)
    buf = build_pe32_efi(entry, sections)

    with open(sys.argv[2], 'wb') as f:
        f.write(buf)

    print(f"Wrote {sys.argv[2]} ({len(buf)} bytes), entry=0x{entry:08X}")


if __name__ == '__main__':
    main()
