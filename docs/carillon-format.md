
# Carillon Player music format

## Data types and terms used in this document
- `Bank` is a Game Boy cartridge ROM bank, usually 16KiB big.
- `byte` is a single-byte/8-bit entry, unsigned unless mentioned otherwise.
- `word` is a 2-byte/16-bit entry, unsigned unless mentioned otherwise.
- `char` is a UTF-8 character.
- `C?` is an array of `char`s.
- `B?` is an array of `byte`s.
- `W?` is an array of `word`s.

Size for arrays is described under the value's description. All values are little-endian unless mentioned otherwise.

## Index
<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Carillon Player music format](#carillon-player-music-format)
   * [Data types and terms used in this document](#data-types-and-terms-used-in-this-document)
   * [Index](#index)
   * [Tracker Structure Concepts](#tracker-structure-concepts)
   * [Order table](#order-table)
   * [Song Pattern](#song-pattern)
   * [Instruments](#instruments)
      + [Panning](#panning)
      + [Pulse Instrument Volume & Length](#pulse-instrument-volume-length)
      + [Pulse Instrument Note & Duty](#pulse-instrument-note-duty)
      + [Wave Instrument Wave Index & Length](#wave-instrument-wave-index-length)
      + [Wave Instrument Note & Volume](#wave-instrument-note-volume)
      + [Waveform table](#waveform-table)
      + [Noise Instrument Volume & Length](#noise-instrument-volume-length)
      + [Noise Instrument Polynomic Counter](#noise-instrument-polynomic-counter)
   * [Samples](#samples)
   * [Finding a Carillon Player bank in ROM](#finding-a-carillon-player-bank-in-rom)
   * [Finding sample bank in ROM](#finding-sample-bank-in-rom)

<!-- TOC end -->

## Tracker Structure Concepts
Carillon Player is a music playback routine created by Aleksi Eeben in 2000. Aleksi released Carillon Player alongside Carillon Editor, a toolset that runs directly on the Game Boy for editing save data with music. 
These muisc save files then get INCBINd into a game ROM for playback, meaning the save file not only contains the music data, but also the playback routine, located at the start of the save data and weighting around a Kilobyte, leaving 15KiB for music data.

Carillon shares many concepts with other tracker routines such as MOD:

- Patterns
An array (in this case with a size of 32 entries) of rows, each containing note and instrument data for all 4 channels, plus a single effect column, allowing for manipulation of the music speed or pitch of a channel.

- Song Order
An array defining the order in which patterns will be played, allowing for repeating patterns without duplication, looping, etc.

- Instruments
A macro-like set of notes, volume values and duty/wave data for each channel that allows shaping the sound in a more detailed form.

- Samples
A stream of audio samples played back using Channel 3, similar to sample-based module formats but without pitching or volume control.

Due to the structure of the format, Carillon allows to store multiple songs inside a single music bank, but all official Carillon releases hardcode the start of all 8 song indexes to specific indexes of the song order. Due to this and the small number of patterns per bank, it is more common to see multiple Carillon banks inside a game ROM than it is with other drivers of the era, such as GHX.

This document focuses on the format used in Carillon Player v1.0, the only officially released version. This document doesn't dive into propietary Carillon modifications, such as Mackarel Interactive's "Makrillon" driver, or the driver implementation inside Carillon Editor.

Unless mentioned otherwise, all data offsets refer to the offset inside a Carillon Editor-formatted .SAV file.

## Order table
The order table is located at `$0F00` and is 256 bytes long. It consists of 255 pattern entries that store the high byte of the requested pattern, it's assumed that the low byte is `$00`, meaning pattern data must be aligned to the lower 8 bits. If a jump is requested, it's encoded as two bytes, hence why Carillon Editor only exposes 255 entries of the order table. 
For a jump to be taken, the first byte of the entry must be `$00`, then the next byte must be **the bitwise NOT** of the order table index to jump to (`LOW(~indexToJumpTo)`).

## Song Pattern
Normal Carillon Player banks store 48 patterns starting at `$1000` and finishing at `$3FFF`, each being 256 bytes aligned to the lowest 8 bits.
Each row contains the same format and is always 8 bytes.

```
 type | description
-----------------------------------
 byte | Note index for Channel 1 and tied flag
      | - Bits 7-1:	Note index
      | - Bit 0:	Tied flag
 byte | Instrument Pointer for Channel 1
      | - Bits 7-4:	Instrument to use
      | - Bits 3-0:	Row of subpattern to start at
      |
 byte | Note index for Channel 2 and tied flag
      | - Bits 7-1:	Note index
      | - Bit 0:	Tied flag
 byte | Instrument Pointer for Channel 2
      | - Bits 7-4:	Instrument to use
      | - Bits 3-0:	Row of subpattern to start at
      |
 byte | Note index for Channel 3 and tied flag
      | - Bits 7-1:	Note index
      | - Bit 0:	Tied flag
      | If byte is $FF, CH3 requests a sample to be played
 byte | Instrument Pointer for Channel 3 (or Sample index)
      | - If sample was requested:
      |		- Bits 7-0: Sample index
      | - Else:
      | 	- Bits 7-4:	Instrument to use
      | 	- Bits 3-0:	Row of subpattern to start at
      |
 byte | Instrument Pointer for Channel 4
      | - Bits 7-4:	Instrument to use
      | - Bits 3-1:	Row of subpattern to start at (X2)
      | - Bit 0:	Always 1, to prevent zero-check from passing incorrectly
      |
 byte | Effect command and parameter
      | - Bits 7-4:	Command to call:
      |		- 0: ---
      |		- 1: Mxx
      |		- 2: SLx
      |		- 3: VWx
      |		- 4: VRx
      |		- 5: UPx
      |		- 6: DNx
      |		- 7: TMx
      |		- 8: BRx
      |		For better documentation on each effect, check the Carillon manual.
      | - Bits 3-0:	Command parameter
```
The "Tied flag" refers to changing the channel's current note without triggering a new instrument, similar to a legato. If the note index byte for a channel is `$00`, it's intepreted as no note present.

## Instruments
Unlike patterns, instrument data is organized by each data's attributes rather than by it's instrument. That is, there is an array for every type of data in an instrument, all of which get indexed based on the instrument index and the current step inside it's subpattern. This allows for very fast data indexing at the cost of readability.

### Panning
Each instrument can be panned Left, Center or Right, this is achieved with a 16x4 array at `$07C0`, where each column is an instrument type (Pulse, Wave, Noise) and each 16 byte row stores the panning for the Nth instrument of that type. The 4th row of this array stores the panning of Samples 0-F, which while correctly processed by the player code is never exposed for user manipulation by Carillon Editor. Each panning value is in [rAUDTERM]() format, where bit 4 represents enabling the left channel output and bit 0 represents the right channel output.

The following info will be broken down in per-type form, due to the different packing of each instrument type.

### Pulse Instrument Volume & Length
Each subpattern step's volume and tick length for pulse instruments is stored in a 256-byte table at `$0800`, where each row represents the Nth step's data and each column represents the Nth instrument's data.
```
 type | description
-----------------------------------
 byte | Pulse instrument Volume & Length
      | Bits 7-4: Volume (0-F)
      | Bits 3-0: Length in ticks (1-F)
```
If tick length (and volume) is zero, there is a check for whether to do a jump to a different subpattern row or finish reading the subpattern (and mute the channel). TO determine what to do and where to jump, the Note & Duty table is tested, see below.

### Pulse Instrument Note & Duty
Located at `$0900`, this table uses the same arrangement as the previous table, but this one stores the subpattern row's note index and pulse duty, or the jump data if it was requested by the Vol & Len table.
```
 type | description
-----------------------------------
 byte | Pulse instrument Note & Duty
      | If Loop/Jump requested:
      | 	Bits 7-0: Loop point / Command
      | Else:
      | 	Bits 7-2: Signed Note offset (-32 to 31)
      | 	Bits 1-0: Pulse duty (0-3)
```
If the Loop Command is `$FF`, It finishes the channel's playback and mutes it. Otherwise, subpattern execution continues at the Nth row of the subpattern (That is, for loop values `$00`-`$0F`).

### Wave Instrument Wave Index & Length
This array, located at `$0A00` works the exact same as the Pulse Instrument Volume & Length array, but instead of storing a row's length and the row's volume, it stores the tick length and waveform index.
```
 type | description
-----------------------------------
 byte | Pulse instrument Volume & Length
      | Bits 7-4: Waveform index (0-F)
      | Bits 3-0: Length in ticks (1-F)
```

### Wave Instrument Note & Volume
This array located at `$0B00` works exactly like the Pulse Instrument Note & Duty array, except that instead of storing the channel pulse duty, it stores the channel volume in rNR32/rAUD3LEVEL format, meaning 0% Volume is `$00`, 50% volume is `$02`, 25% volume is `$03` and 100% volume is `%01`.
```
 type | description
-----------------------------------
 byte | Pulse instrument Note & Duty
      | If Loop/Jump requested:
      |   Bits 7-0: Loop point / Command
      | Else:
      |   Bits 7-2: Signed Note offset (-32 to 31)
      |   Bits 1-0: Channel Volume (rAUD3LEVEL/rNR32 format)
```

### Waveform table
Located at `$0C00`, this is a 16 * 16 table containing the [WAVERAM]() data for all 16 usable waveforms.
```
 type | description
-----------------------------------
 B16  | Waveform index
```

### Noise Instrument Volume & Length
Located at `$0D00`, this array works exactly like Pulse Instrument Volume & Length. See that table for format.

### Noise Instrument Polynomic Counter
Located at `$0E00`, this array is similar to Pulse Instrument Note & Duty, but only stores the value written to rAUD4POLY/rNR43.
```
 type | description
-----------------------------------
 byte | Pulse instrument Note & Duty
      | If Loop/Jump requested:
      |   Bits 7-0: Loop point / Command
      | Else:
      |   Bits 7-0: rAUD4POLY/rNR43 value
```

## Samples
Sample data is stored on a separate bank to Carillon Player, this extra bank contains a small code stub at the start that plays back the data at a desired rate of ~7645Hz (or 4 update calls per frame roughly). To play back samples, Channel 3's WAVERAM is rewritten constantly, which allows for 4-Bit sample playback. When a sample trigger is requested by the song, a 2 * 16 Look-Up-Table located at `$06C0` in the player bank is read to write the correct info into WRAM for the sample player. The data is then stored in the sample bank (On a SAV file this bank starts at `$4000`) as multiple 16-byte chunks in [WAVERAM]() format.
```
 type | description
-----------------------------------
 byte | High byte of sample data in sample bank (HIGH(sampleXData))
 byte | Length of sample data in 16-byte chunks ((sampleXData.end - sampleXData) / 16)
```
This means sample data must be aligned in such a way that the data starts at an address where the lower 8 bits are all zero. The length counter also means a sample can only be about ~1.06 Seconds long.

## Finding a Carillon Player bank in ROM
Luckily all Carillon Player banks contain a small stub of text at the start:
```
CARILLON PLAYER Version 1.0 (c)2000 Aleksi Eeben (email:aleksi@cncd.fi)
```
So finding a carillon bank should be as easy as searching for this string in the ROM.

### Info sources used
- [format.md](https://github.com/tildearrow/furnace/blob/master/papers/format.md), Furnace tracker's format description written by Tildearrow, from where I took the syntax used in this document.