# Caroline.py
To parse music and sample data, `caroline.py` is provided, which parses multiple Carillon formats (ROM Dump, SAV file, BIN/SAM) and spits an include-able file compatible with this dissasembly.

# Standard usage
Caroline's main goal is to read different formats for Carillon music data and output a readable RGBDS assembly file that this dissasembly can process without need of INCBINing the data. Currently it supports three input formats: A Carillon Editor save file in SRAM format (`--sav`), a BIN+SAM file combo outputted by Carillon Editor Utility (`--bin`) and a chunk from a Game Boy ROM file defining data offsets for both the Music and Sample banks (`--rom`), useful if you're importing data from a game using Carillon.

To use one of these, simply call `caroline.py` with the format's flag followed by the file input. For `--bin`, two filenames must be passed if the music data uses samples, Otherwise one is fine. In case that the parser finds that the music data references samples, a warning will be output. `--rom` works similarly, where an input filename must be given followed by the Music and Sample bank offsets in the file. If a second offset isn't given, it's assumed the music data doesn't use samples, and a warning will be given if the parser finds this to not be true.

# Limitations and innacuracies
Due to certain issues with how Carillon Editor works, Caroline has issues with creating 100% Matching music data. The two main issues are described below.

## Ghost Bytes
Carillon Editor's Block Editor has two ways to clear a note row, either by deleting it with `B + A` or by changing the note index with `Left/Right + A` until reaching one semitone under C-0. The former clears both the note index byte and the instrument index byte to `$00`, while the former only updates the note index, so if you clear a note row using the latter method, this leaves a "ghost byte" for the instrument index, which the driver never actually reads, as a note value of `$00` skips reading the instrument value. Because of this and the way Caroline reads data, it assumes the instrument index is `$00` if the note index is `$00`, thus these ghost bytes aren't recreated in the output data.

## Incorrect samples
For one reason or another, Carillon Editor (or it's accompanying Windows tool) sometimes stores sample data incorrectly. Samples sometimes are shortened to the max size (~1.07s) but *only in the sample info table*, meaning there's leftover data that never possibly gets read. Caroline isn't aware of this extra data and thus it can't import it. 
I've also found instances of sample info describing samples that go outside the sample bank, reaching into VRAM even. I haven't seen a song using these but they're described in the header, so Caroline will stop reading sample data once it goes outside the sample bank (And throw a warning about it).