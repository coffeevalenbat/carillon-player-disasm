# This file contains project-specific configuration.
# You can override variables set in the Makefile here.

CARILLON_MODULE := assets/modules/oldschool.carillon
# Enable sample playback
ASFLAGS += -D_CARILLON_SAMPLE_PLAYBACK
# Enable debug logging
ASFLAGS += -DCARILLON_LOG

# Value that the ROM will be filled with.
PADVALUE := 0xFF

## Header constants (passed to RGBFIX).

# ROM version (typically starting at 0 and incremented for each published version).
VERSION := 0

# 4-ASCII letter game ID.
GAMEID := 

# Game title, up to 11 ASCII chars.
TITLE := MUSIC

# New licensee, 2 ASCII chars.
# Homebrew games FTW!.
LICENSEE := 
# Old licensee, please set to 0x33 (required to get SGB compatibility).
OLDLIC := 0x33

# MBC type, tells which hardware is in the cart.
# You can get a list of valid values by running `rgbfix -m help`.
# See https://gbdev.io/pandocs/MBCs for more information, or consult any copy of Pan Docs.
# If using no MBC, consider enabling `-t` below.
MBC := MBC5

# ROM size is set automatically by RGBFIX.

# Size of the on-board SRAM; MBC type should indicate the presence of RAM.
# See https://gbdev.io/pandocs/The_Cartridge_Header#0149--ram-size or consult any copy of Pan Docs.
# Set this to 0 when using MBC2's built-in SRAM.
SRAMSIZE := 0x00

# ROM name.
ROMNAME := carillonPlayer
ROMEXT  := gbc


# Compilation parameters, uncomment to apply, comment to cancel.
# "Sensible defaults" are included.
# Please refer to RGBDS' documentation.
# For example, offline: `man 1 rgbasm`; online: https://rgbds.gbdev.io/docs/rgbasm.1

# Export all labels.
# This means they must all have unique names, but they will all show up in the .sym and .map files.
# ASFLAGS += -E

# Game Boy Color compatible.
FIXFLAGS += -c
# Game Boy Color required.
# FIXFLAGS += -C

# Super Game Boy compatible.
# FIXFLAGS += -s

# Game Boy mode.
# LDFLAGS += -d

# No banked WRAM mode.
# LDFLAGS += -w

# 32k mode.
# LDFLAGS += -t
