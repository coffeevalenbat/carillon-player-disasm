# Interesting findings
This document is just for me to mention some interesting and funny things I noticed in Carillon Player's code and structure.

# Sample playback support
Not much of a surprise but still interesting - unlike GHX, another binary-shipped driver of the era, Carillon seems to have had no build flags that heavily modified the code, including for sample playback. What this means is that besides the sample info table contained in a Carillon bank to inform on a sample's address and length, all Carillon blobs out there are sample compatible.

# Unused sample panning
Carillon contains a 64-byte array defining the initial panning of every instrument and every instrument type: Pulse instruments, Wave instruments and Noise instruments. The fourth entry into this array is for... Samples! And indeed it gets accessed when triggering samples, but AFAIK no version of Carillon Editor or the Carillon Editor Utility ever made these options available to the user.

# Unused effect slots
While Carillon Editor v1.2 only ever documented 7 effect types for patterns, the driver technically can index up to 16 (0 meaning no effect, so 15)! There is a 32-byte table that's used to jump to the according effect's code, but only indexes 1-7 are ever used, the other 9 just point to a `ret` instruction, possibly for forwards compatibility. Weirdly enough there's a slot for effect 0, which never gets read because the code returns early if an effect code of 0 is read, this is probably a leftover before the code was changed to save cycles on empty effects.

# Uneven vibrato
Carillon's Vibrato table is... weird. Each index of the vibrato is just a simple sine wave amplified at a different multiplier, but not only is the amplitude of each index non-linear (Sequence is 2, 3, 6, 10, 15 and 20) but the second half of the sine is amplified by the multiplier... plus one? What this means is that every vibrato amplitude skews *just a bit* more into negative values than positive values.

The code for the vibrato table in this dissasembly is just my attempt at making a formula that spits out a matching table, but it's possible that it's not exactly how Aleksi did it.

# Repeated notes
For some strange reason, Carillon's note table stores the first and last octave twice:
```
	;   C-x   C#x   D-x   D#x   E-x   F-x   F#x   G-x   G#x   A-x   A#x   B-x
	dw $02C, $09D, $107, $16B, $1C9, $223, $277, $2C7, $312, $358, $39B, $3DA ; Octave 1
	dw $02C, $09D, $107, $16B, $1C9, $223, $277, $2C7, $312, $358, $39B, $3DA ; Octave 1... again?
	dw $416, $44E, $483, $4B5, $4E5, $511, $53B, $563, $589, $5AC, $5CE, $5ED ; Octave 2
	dw $60B, $627, $642, $65B, $672, $689, $69E, $6B2, $6C4, $6D6, $6E7, $6F7 ; Octave 3
	dw $706, $714, $721, $72D, $739, $744, $74F, $759, $762, $76B, $773, $77B ; Octave 4
	dw $783, $78A, $790, $797, $79D, $7A2, $7A7, $7AC, $7B1, $7B6, $7BA, $7BE ; Octave 5
	dw $7C1, $7C5, $7C8, $7CB, $7CE, $7D1, $7D4, $7D6, $7D9, $7DB, $7DD, $7DF ; Octave 6
	dw $7C1, $7C5, $7C8, $7CB, $7CE, $7D1, $7D4, $7D6, $7D9, $7DB, $7DD, $7DF ; Octave 6... again??
```
While I can't say for certain, My guess is that Aleksi did this to pad the already page-aligned table and also to add a safeguard in case subpatterns tried going off range.