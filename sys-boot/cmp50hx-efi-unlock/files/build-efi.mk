# Makefile for building CMP 50HX EFI unlock application
# Used by cmp50hx-efi-unlock ebuild

EFI_INC ?= /usr/include/efi
EFI_LIB ?= /usr/lib64
CC ?= gcc
OBJCOPY ?= objcopy

SRC = unlock50x_v1.c
OBJ = unlock50x_v1.o
SO = unlock50x_v1.so
EFI = 50HXUNLK.EFI

BLOBS = v67_payload_bin booter_ucode_dbg booter_ucode_prod \
        gsp_rm_boot_dbg fwsec_50hx_prod_bin fwsec_50hx_dbg_bin \
        sec2_ucode_vbios_49 sec2_ucode_vbios_89 gsp_bl_tu102

BLOB_OBJS = $(foreach b,$(BLOBS),$(b).o)

CFLAGS = -O2 -fno-stack-protector -fpic -ffreestanding \
         -fno-asynchronous-unwind-tables -fno-unwind-tables \
         -fshort-wchar -mno-red-zone -maccumulate-outgoing-args \
         -fno-builtin -fno-strict-aliasing -Wno-unused-function \
         -I $(EFI_INC) -I $(EFI_INC)/x86_64 \
         -DGNU_EFI_USE_MS_ABI -DDIRECT_SEC2 -DRELEASE_BUILD -DVBIOS_DUMP

all: $(EFI)

$(OBJ): $(SRC)
	$(CC) -c $(CFLAGS) -o $@ $<

define embed_rule
$(1).o: blobs/$(1).bin
	cd blobs && objcopy --input-target binary --output-target elf64-x86-64 \
		--binary-architecture i386:x86-64 \
		--redefine-sym _binary_$(*F)_start=$$(@F:.o=) \
		--redefine-sym _binary_$(*F)_end=$$(@F:.o=)_end \
		--redefine-sym _binary_$(*F)_size=$$(@F:.o=)_size \
		$$< ../$$@
endef

$(foreach b,$(BLOBS),$(eval $(call embed_rule,$(b))))

$(SO): $(OBJ) $(BLOB_OBJS)
	ld -nostdlib -znocombreloc -T $(EFI_LIB)/elf_x86_64_efi.lds -shared -Bsymbolic \
	    $(EFI_LIB)/crt0-efi-x86_64.o $^ \
	    -L$(EFI_LIB) -lgnuefi -lefi -o $$@ 2>&1 | tail -5

$(EFI): $(SO)
	python3 $(CURDIR)/../../files/elf_to_efi.py $$< $$@

clean:
	rm -f $(OBJ) $(SO) $(EFI) $(BLOB_OBJS)

.PHONY: all clean
