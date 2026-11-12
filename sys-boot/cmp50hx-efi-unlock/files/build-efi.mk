# Makefile for building CMP 50HX EFI unlock application
# Used by cmp50hx-efi-unlock ebuild

EFI_INC ?= /usr/include/efi
EFI_LIB ?= /usr/lib64
CC ?= gcc
OBJCOPY ?= objcopy
SCRIPT_DIR ?= .

SRC = unlock50x_v1.c
OBJ = unlock50x_v1.o
SO = unlock50x_v1.so
EFI = 50HXUNLK.EFI

# Each blob: symbol_name source_filename_in_blobs_dir
BLOB_RULES = \
  v67_payload_bin:v67_payload.bin \
  booter_ucode_dbg:booter_ucode_dbg.bin \
  booter_ucode_prod:booter_ucode_prod.bin \
  gsp_rm_boot_dbg:gsp_rm_boot_dbg.bin \
  fwsec_50hx_prod_bin:fwsec_50hx_prod.bin \
  fwsec_50hx_dbg_bin:fwsec_50hx_dbg.bin \
  sec2_ucode_vbios_49:sec2_ucode_vbios_49.bin \
  sec2_ucode_vbios_89:sec2_ucode_vbios_89.bin \
  gsp_bl_tu102:bl_gsp_tu102.bin

BLOB_OBJS = $(foreach pair,$(BLOB_RULES),$(word 1,$(subst :, ,$(pair))).o)

CFLAGS = -O2 -fno-stack-protector -fpic -ffreestanding \
         -fno-asynchronous-unwind-tables -fno-unwind-tables \
         -fshort-wchar -mno-red-zone -maccumulate-outgoing-args \
         -fno-builtin -fno-strict-aliasing -Wno-unused-function \
         -I $(EFI_INC) -I $(EFI_INC)/x86_64 \
         -DGNU_EFI_USE_MS_ABI -DDIRECT_SEC2 -DRELEASE_BUILD -DVBIOS_DUMP

all: $(EFI)

$(OBJ): $(SRC)
	$(CC) -c $(CFLAGS) -o $@ $<

# Generate a compile rule for each blob
define BLOB_RULE
$(1).o: blobs/$(2)
	cd blobs && objcopy --input-target binary --output-target elf64-x86-64 \
		--binary-architecture i386:x86-64 \
		--redefine-sym _binary_$(1)_start=$(1) \
		--redefine-sym _binary_$(1)_end=$(1)_end \
		--redefine-sym _binary_$(1)_size=$(1)_size \
		$(2) ../$$(@)
endef

$(foreach pair,$(BLOB_RULES),$(eval $(call BLOB_RULE,$(word 1,$(subst :, ,$(pair))),$(word 2,$(subst :, ,$(pair))))))

$(SO): $(OBJ) $(BLOB_OBJS)
	ld -nostdlib -znocombreloc -T $(EFI_LIB)/elf_x86_64_efi.lds -shared -Bsymbolic \
	    $(EFI_LIB)/crt0-efi-x86_64.o $^ \
	    -L$(EFI_LIB) -lgnuefi -lefi -o $@

$(EFI): $(SO)
	python3 $(SCRIPT_DIR)/elf_to_efi.py $< $@

clean:
	rm -f $(OBJ) $(SO) $(EFI) $(BLOB_OBJS)

.PHONY: all clean
