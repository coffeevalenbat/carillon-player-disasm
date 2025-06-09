;; Macro pack for more easily using debugfiles in RGBDS projects.
;; Being placed in the public domain, it is free to use, modify, and redistribute without any constraints...
;; ...but "WITHOUT ANY WARRANTIES (etc.)", as well. Enjoy!
;;
;; New versions, usage instructions, tips, etc. can be found at https://github.com/ISSOtm/debugfile.inc

IF __RGBDS_MAJOR__ == 0 && __RGBDS_MINOR__ < 9
    FAIL "This version of 'debugfile.inc' requires RGBDS version 0.9.0 or later."
ENDC

; If all of these have already been defined, don't do it again.

IF !DEF(DEBUGFILE_INC)
def DEBUGFILE_INC EQU 1

; Usage: require_debugfile_inc_v <min_ver>
; Examples: require_debugfile_inc_v 4.1.2
;           require_debugfile_inc_v 4.1 (equivalent to 4.1.0)
;           require_debugfile_inc_v 4 (equivalent to 4.0.0)
MACRO require_debugfile_inc_v
    def CUR_VER equs "1,0,0"    ; ** UPDATE THIS LINE WHEN CHANGING THE REVISION NUMBER **

    def MIN_VER equs STRRPL("\1", ".", ",")
    def INTERNAL_CHK equs """MACRO ___internal
    IF \\1 != \\4 || \\2 < \\5 || (\\2 == \\5 && \\3 < \\6)
    	FAIL "Version \\1.\\2.\\3 of 'debugfile.inc' is incompatible with requested version \\4.\\5.\\6"
    ENDC
\nENDM"""
    INTERNAL_CHK
    ___internal {CUR_VER}, {MIN_VER},0,0
    purge CUR_VER, MIN_VER, INTERNAL_CHK, ___internal
ENDM


IF DEF(PRINT_DEBUGFILE)
	println "@debugfile 1.0.0"

	MACRO dbg_var ; <name>, <default value>
	    def DEFAULT_VALUE equs "0"
	    IF _NARG > 1
	        redef DEFAULT_VALUE equs "\2"
	    ENDC
	    println "@var \1 {DEFAULT_VALUE}"
	    purge DEFAULT_VALUE
	ENDM

	MACRO dbg_action ; <action:str> [, <condition:dbg_expr>]
		def OFS_FROM_BASE equ @ - {.}
		def ACTION_COND equs ""
		IF _NARG > 1
			redef ACTION_COND equs "\2"
		ENDC
		println "{.}+{d:OFS_FROM_BASE} x {ACTION_COND}: ", \1
		purge OFS_FROM_BASE, ACTION_COND
	ENDM

	MACRO dbg_group ; <id:dbg_ident> [, <display name:str>]
		IF _NARG > 1
			println "@group \1 \2"
		ELSE
			println "@group \1"
		ENDC
	ENDM
	MACRO end_dbg_group
		println "@endgroup"
	ENDM

ELSE
  ; If not printing debugfiles to stdout, define the "core" macros as do-nothing, but still
  ; as macros and not `EQUS ";"`, because line continuations are *not* processed within comments.
	MACRO dbg_var
	ENDM
	MACRO dbg_action
	ENDM
	MACRO dbg_group
	ENDM
	MACRO end_dbg_group
	ENDM
ENDC

MACRO dbg_log ; <message:dbg_str> [, <condition:dbg_expr>]
	def MSG equs \1
	shift
	dbg_action "message \"{MSG}\"", \#
	purge MSG
ENDM

MACRO runtime_assert ; <condition:dbg_expr> [, <message:dbg_str>]
	def MSG equs "assert failure"
	IF _NARG > 1
		redef MSG equs \2
	ENDC
	dbg_action "alert \"{MSG}\"", !(\1)
	purge MSG
ENDM

MACRO unreachable ; [<message:dbg_str>]
	def MSG equs "unreachable code reached!"
	IF _NARG > 0
		redef MSG equs \1
	ENDC
	dbg_action "alert \"In {.}: {MSG}\""
	purge MSG
ENDM


ENDC
