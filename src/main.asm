; Boilerplate Carillon player
include "hardware.inc"

rev_Check_hardware_inc 4.11.0

; Include main music module
include "src/carillon/carillon_stub.gbz80"

; RGB555 format color written to BGPD to display busy time
DEF CGB_BUSY_COLOR	EQU $7FFF
; Default palette
DEF CGB_CLEAR_COLOR	EQU $0000
; Value written to rBGP to display busy time on DMG
DEF DMG_BUSY_COLOR	EQU %00_01_11_11
; Default palette
DEF DMG_CLEAR_COLOR	EQU %00_01_11_00

; A couple of helpers...

;; Waits until rLY == C
; @param c: Scanline to wait for
; @destroy af
MACRO waitLY
	:ldh a, [rLY]
	cp c
	jr nz, :-
ENDM

;; Wait for VRAM to become available
; @destroy af
MACRO waitVRAM
	:ldh a, [rSTAT]
	and STATF_BUSY
	jr nz, :-
ENDM

; Used WRAM variables
SECTION "Variables", WRAM0
wConsoleType: db

; All interrupt handlers/RSTs are just RETI
; ...Just gonna fill that with a loop!
FOR RST_ADDR, $0000, $0068, $08
SECTION "RST ${x:RST_ADDR}", ROM0[RST_ADDR]
	reti
ENDR

SECTION "Entry point", ROM0[$0100]
	nop
	jp entryPoint
	ds $150 - @, $00 ; Header ($0104 - $014FF) filled with $00s for RGBFIX to populate

entryPoint:
	di
	ld sp, $FFFE
	; Since MGB is still DMG but with a different boot value.. still weird
	cp BOOTUP_A_MGB
	jr nz, :+
		ld a, BOOTUP_A_DMG
:
	dec a
	ld [wConsoleType], a
	call turnLCDOff
	; If on DMG, skip color and 2X CPU related code
	ld a, [wConsoleType]
	or a
	jr z, .isDMG
.isCGB:
	ld hl, rSPD
	bit SPDB_DBLSPEED, [hl]
	jr nz, .alreadyDoubleSpeed
		set SPDB_PREPARE, [hl]
		xor a
		ldh [rIF], a
		ldh [rIE], a
		ld a, JOYP_GET_NONE
		ldh [rJOYP], a
		; According to this graphic, in this case STOP is a two-byte instruction:
		; https://gbdev.io/pandocs/Reducing_Power_Consumption.html#using-the-stop-instruction
		stop $00
.alreadyDoubleSpeed:
	ld hl, fontPal
	ld a, BGPIF_AUTOINC
	ldh [rBGPI], a
	ld bc, (fontPal.end - fontPal) << 8 | LOW(rBGPD)
.bgPaletteLoop:
	ld a, [hli]
	ldh [c], a
	dec b
	jr nz, .bgPaletteLoop
	
	; Clear attribute map
	ld a, VBK_BANK
	ldh [rVBK], a
	ld hl, _SCRN0
	ld bc, SCRN_VX_B * SCRN_VY_B
	xor a
	call memFill
	xor a
	ldh [rVBK], a
.isDMG:
	ld a, DMG_CLEAR_COLOR
	ldh [rBGP], a
	
	; Copy font with ascii offset
	ld hl, fontTiles
	ld de, _VRAM + $300
	ld bc, fontTiles.end - fontTiles
	call memCopy
	
	; Copy map
	ld hl, screenText
	ld de, _SCRN0
	ld bc, SCRN_VX_B * SCRN_Y_B
	call memCopy

	; If system is DMG, patch map with DMG message
	ld a, [wConsoleType]
	or a
	jr nz, .skipDMGPatch
		ld hl, screenText.ifDMG
		ld de, _SCRN0 + (screenText.patchSys - screenText)
		ld bc, screenText.ifDMGEnd - screenText.ifDMG
		call memCopy
.skipDMGPatch
	ld a, BANK(Player_Initialize)
	ld [rROMB0], a
	; Initialize music player RAM
	call Player_Initialize
	; Play music, by default plays track #0
	call Player_MusicStart
	ld a, LCDCF_ON | LCDCF_BG8000 | LCDCF_BGON
	ldh [rLCDC], a
IF DEF(_CARILLON_SAMPLE_PLAYBACK)
mainLoop:
	; Somewhat accurate scanline waits for sample playback
	; Due to VBlank's speed not 100% aligning with the APU, getting an exact refresh rate is impossible
	ld c, 16
	call tickMusicAndSamples
	ld c, 54
	call tickSamples
	ld c, 93
	call tickSamples
	ld c, 131
	call tickSamples
	jr mainLoop

;; Set BG color #0 back to default color to display non-busy CPU time
; @destroy af c
clearBG:
	ld a, DMG_CLEAR_COLOR
	ldh [rBGP], a
	; I guess Aleksi didn't know BGPD isn't VRAM attached :P
	waitVRAM
	ld a, BGPIF_AUTOINC
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	waitVRAM
	assert CGB_CLEAR_COLOR == $0000
	xor a
	ldh [c], a
	ldh [c], a
	ret

;; Set BG color #0 to BUSY color to display busy CPU time
; @destroy af c
busyBG:
	waitVRAM
	ld a, BGPIF_AUTOINC
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	waitVRAM
	ld a, LOW(CGB_BUSY_COLOR)
	ldh [c], a
	ld a, HIGH(CGB_BUSY_COLOR)
	ldh [c], a
	ld a, DMG_BUSY_COLOR
	ldh [rBGP], a
	ret

;; Waits until scanline and updates sample player
; @param c: Scanline to wait for
; @destroy af bc de hl
tickSamples:
	waitLY
	inc c
	waitLY
	call busyBG
	call Player_SampleUpdate
	jr clearBG

;; Waits until scanline and updates music player, followed by the sample player
; @param c: Scanline to wait for
; @destroy af bc de hl
tickMusicAndSamples:
	waitLY
	ld a, BANK(Player_MusicUpdate)
	ld [rROMB0], a
	inc c
	waitLY
	call busyBG
	call Player_MusicUpdate
	ld a, BANK(Player_SampleUpdate)
	ld [rROMB0], a
	call Player_SampleUpdate
	jr clearBG
ELSE
mainLoop:
	; Ticks music engine once line 54 has been reached
	ld c, 84
	waitLY
	inc c
	waitLY
	; Set BG color to busy
	waitVRAM
	ld a, BGPIF_AUTOINC
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	waitVRAM
	ld a, LOW(CGB_BUSY_COLOR)
	ldh [c], a
	ld a, HIGH(CGB_BUSY_COLOR)
	ldh [c], a
	ld a, DMG_BUSY_COLOR
	ldh [rBGP], a
	
	; Call player, already technically in bank since this is a 32KiB ROM, so no banking needed
	call Player_MusicUpdate

	; Set BG color back to default
	ld a, DMG_CLEAR_COLOR
	ldh [rBGP], a
	waitVRAM
	ld a, BGPIF_AUTOINC
	ldh [rBGPI], a
	ld c, LOW(rBGPD)
	waitVRAM
	assert CGB_CLEAR_COLOR == $0000
	xor a
	ldh [c], a
	ldh [c], a
	jr mainLoop
ENDC

;; Fills memory section with byte value
; @param hl: address to fill
; @param bc: length of fill
; @param a: value to fill with
; @destroy f bc hl
memFill:
	inc b
	inc c
	jr :+
.loop:
	ld [hli], a
:
	dec c
	jr nz, .loop
	dec b
	jr nz, .loop
	ret

;; Copies memory sections
; @param hl: source address
; @param de: destination address
; @param bc: length of copy
; @destroy af bc de hl
memCopy:
	inc b
	inc c
	jr :+
.loop:
	ld a, [hli]
	ld [de], a
	inc de
:
	dec c
	jr nz, .loop
	dec b
	jr nz, .loop
	ret

;; Safely disables LCD
; @destroy af hl
turnLCDOff:
	ld hl, rLCDC
	bit LCDCB_ON, [hl]
	ret z
.waitVBlank:
	ldh a, [rLY]
	cp SCRN_Y + 1
	jr nz, .waitVBlank
	res LCDCB_ON, [hl]
	ret

fontTiles:
	INCBIN "assets/gfx/font.2bpp"
.end

NEWCHARMAP screenTextCharMap
DEF CHARS EQUS "0123456789.,©:@/ ABCDEFGHIJKLMNOPQRSTUVWXYZÄÁÖ'-"
FOR CHAR, STRLEN(#CHARS)
	charmap STRSUB(#CHARS, CHAR + 1, 1), CHAR + $30
ENDR

;; Macro to make the map below less ugly to define
; Stores string and pads it to tilemap width with $00
MACRO dtxt
	db \1
	ds SCRN_VX_B - STRLEN(\1), $00
ENDM

screenText:
	dtxt "                    "
	dtxt "CARILLON PLAYER V1.0"
	dtxt "                    "
	dtxt " ©2000 ALEKSI EEBEN "
	dtxt "                    "
	dtxt "   ALEKSI@CNCD.FI   "
	dtxt " WWW.CNCD.FI/AEEBEN "
	dtxt "                    "
	dtxt "    FREE FOR ALL    "
	dtxt " NON-COMMERCIAL USE "
	dtxt "                    "
	dtxt "                    "
	dtxt " TEST CODE VERSION: "
IF DEF(_CARILLON_SAMPLE_PLAYBACK)
	dtxt "7645HZ SAMPLE PLAYER"
ELSE
	dtxt "  NO SAMPLE PLAYER  "
ENDC
	dtxt "                    "
	dtxt " CURRENT CPU CLOCK: "
.patchSys:
	dtxt "  CGB DOUBLE SPEED  "
	dtxt "                    "
.ifDMG:
	dtxt "  DMG NORMAL SPEED  "
.ifDMGEnd:

fontPal:
	INCBIN "assets/gfx/font.pal"
.end