
.SUFFIXES: # Suppress a lot of useless default rules, which also provides a nice speedup.

# Recursive `wildcard` function.
rwildcard = $(foreach d,$(wildcard $(1:=/*)),$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))

# Program constants.
# POSIX OSes (the sane default).
RM_RF := rm -rf
MKDIR_P := mkdir -p
ifeq ($(strip $(shell which rm)),)
	# Windows *really* tries its hardest to be Special™!
	RM_RF := -rmdir /s /q
	MKDIR_P := -mkdir
endif

RGBDS   ?= # Shortcut if you want to use a local copy of RGBDS.
RGBASM  := ${RGBDS}rgbasm
RGBLINK := ${RGBDS}rgblink
RGBFIX  := ${RGBDS}rgbfix
RGBGFX  := ${RGBDS}rgbgfx

ROM = bin/${ROMNAME}.${ROMEXT}

# Argument constants
INCDIRS  = src/ include/
WARNINGS = all extra
ASFLAGS  = -p ${PADVALUE} $(addprefix -I,${INCDIRS}) $(addprefix -W,${WARNINGS}) -D_CARILLON_MODULE=${CARILLON_MODULE}
LDFLAGS  = -p ${PADVALUE}
FIXFLAGS = -p ${PADVALUE} -i "${GAMEID}" -k "${LICENSEE}" -l ${OLDLIC} -m ${MBC} -n ${VERSION} -r ${SRAMSIZE} -t ${TITLE}

# The list of ASM files that RGBASM will be invoked on.
SRCS = $(call rwildcard,src,*.asm)

## Project-specific configuration
# Use this to override the above
include project.mk

# `all` (Default target): build the ROM
all: ${ROM}
.PHONY: all

# `clean`: Clean temp and bin files
clean:
	${RM_RF} bin obj assets dbg
.PHONY: clean

# `rebuild`: Build everything from scratch
# It's important to do these two in order if we're using more than one job
rebuild:
	${MAKE} clean
	${MAKE} all
.PHONY: rebuild

# By default, asset recipes convert files in `assets/` into other files in `assets/`.
# This line causes assets not found in `assets/` to be also looked for in `src/assets/`.
# "Source" assets can thus be safely stored there without `make clean` removing them!
VPATH := src

# To catch bad flags
%.flags:
	@${MKDIR_P} "${@D}"
	touch $@

# Tile graphics
assets/%.2bpp: assets/%.flags assets/%.png
	@${MKDIR_P} "${@D}"
	${RGBGFX} -o $@ @$^

assets/%.pal: assets/%.flags assets/%.png
	@${MKDIR_P} "${@D}"
	${RGBGFX} -p $@ @$^

# Define how to parse Carillon Save files.
assets/%.carillon: assets/%.sav
	@${MKDIR_P} "${@D}"
	src/tools/caroline.py --sav $^ -o $@

# How to build a ROM.
# Notice that the build date is always refreshed.
bin/%.${ROMEXT}: $(patsubst src/%.asm,obj/%.o,${SRCS})
	@${MKDIR_P} "${@D}"
	${RGBASM} ${ASFLAGS} -o obj/lib/build_date.o src/lib/build_date.asm
	${RGBLINK} ${LDFLAGS} -m bin/$*.map -n bin/$*.sym -o $@ $^ \
	&& ${RGBFIX} -v ${FIXFLAGS} $@
	@# Create master DBG file that includes all files
	echo "@debugfile 1.0.0\n" > bin/$*.dbg
	@for debugfile in $(patsubst src/%.asm,dbg/%.dbg,${SRCS}) ; do \
		echo "; $$debugfile" >> bin/$*.dbg ; \
		cat $$debugfile >> bin/$*.dbg ; \
	done

# `.mk` files are auto-generated dependency lists of the source ASM files, to save a lot of hassle.
# Also add all obj dependencies to the dep file too, so Make knows to remake it.
# Caution: some of these flags were added in RGBDS 0.4.0, using an earlier version WILL NOT WORK
# (and produce weird errors).
obj/%.mk: src/%.asm
	@${MKDIR_P} "${@D}"
	@# First build DBG file
	@${MKDIR_P} $(dir $(patsubst obj/%,dbg/%,$@))
	@${RGBASM} ${ASFLAGS} -DPRINT_DEBUGFILE -M $@ -MG -MP -MQ ${@:.mk=.o} -MQ $@ -o ${@:.mk=.o} $< > dbg/$*.dbg
	@# Now actual ASM file
	${RGBASM} ${ASFLAGS} -M $@ -MG -MP -MQ ${@:.mk=.o} -MQ $@ -o ${@:.mk=.o} $<
# DO NOT merge this with the rule above, otherwise Make will assume that the `.o` file is generated,
# even when it isn't!
# This causes weird issues that depend, among other things, on the version of Make.
obj/%.o: obj/%.mk
	@touch $@

ifeq ($(filter clean,${MAKECMDGOALS}),)
include $(patsubst src/%.asm,obj/%.mk,${SRCS})
endif
