#!/usr/bin/env python3
# Parse Carillon editor savefile into readable data
import argparse
from sys import exit
from os.path import splitext
parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument('-s', '--sav', help="Read data from Carillon Editor .sav file", type=str)
parser.add_argument('-b', '--bin', help="Read data from .bin/.sam files, if no SAM file path is passed, \
	it's assumed that no samples are used, but a warning will be displayed if the music data asks for a sample.", type=str, nargs='+')
parser.add_argument('--rom', help="Read data from offsets at Game Boy ROM file. If no offset is defined for SAM data, \
	it's assumed that no samples are used, but a warning will be displayed if the music data asks for a sample.", type=str, nargs='+')
parser.add_argument('-o', '--output', help="Output path for music data, if not defined, it's derived from input filename", type=str)

args = parser.parse_args()

NOTE_TABLE = [
	"C_0", "C#0", "D_0", "D#0", "E_0", "F_0", "F#0", "G_0", "G#0", "A_0", "A#0", "B_0",
	"C_1", "C#1", "D_1", "D#1", "E_1", "F_1", "F#1", "G_1", "G#1", "A_1", "A#1", "B_1",
	"C_2", "C#2", "D_2", "D#2", "E_2", "F_2", "F#2", "G_2", "G#2", "A_2", "A#2", "B_2",
	"C_3", "C#3", "D_3", "D#3", "E_3", "F_3", "F#3", "G_3", "G#3", "A_3", "A#3", "B_3",
	"C_4", "C#4", "D_4", "D#4", "E_4", "F_4", "F#4", "G_4", "G#4", "A_4", "A#4", "B_4",
	"C_5", "C#5", "D_5", "D#5", "E_5", "F_5", "F#5", "G_5", "G#5", "A_5", "A#5", "B_5"
]

FX_TABLE = ["__", "MO", "SL", "VW", "VR", "UP", "DN", "TM", "BR"]

INST_TYPEOF_DUTY	= 0
INST_TYPEOF_WAVE	= 1
INST_TYPEOF_NOISE	= 2

MUSBANK_SAMPLE_INFO		= 0x46C0 - 0x4000

MUSBANK_PANTABLE		= 0x47C0 - 0x4000

MUSBANK_PULSE_VOLLEN	= 0x4800 - 0x4000
MUSBANK_PULSE_NOTEDUTY	= 0x4900 - 0x4000

MUSBANK_WAVE_INDEXLEN	= 0x4A00 - 0x4000
MUSBANK_WAVE_NOTEVOL	= 0x4B00 - 0x4000
MUSBANK_WAVETABLE		= 0x4C00 - 0x4000

MUSBANK_NOISE_VOLLEN	= 0x4D00 - 0x4000
MUSBANK_NOISE_FREQ		= 0x4E00 - 0x4000

MUSBANK_ORDER_TABLE		= 0x4F00 - 0x4000

ORDER_END_CMD			= 0x0100
ORDER_LOOP_CMD			= 0x0200
ORDER_EMPTY_CMD			= 0x0400

def dumpBin(data, bytesPerLine, newLineStart = "db"):
	o = ""
	wLineByte = 0
	for i in range(len(data)):
		if wLineByte == 0:
			o += newLineStart
		o += f" ${data[i]:02X},"
		wLineByte += 1
		if wLineByte >= bytesPerLine:
			wLineByte = 0
			# Raplce comma with newline
			o = o[:-1] + "\n"
	return o

class instrument:
	def __init__(self, typeof):
		self.used = True
		self.typeof = typeof
		self.panning = 0xFF
		self.subpattern = []

class spRow:
	def __init__(self, typeof):
		self.typeof = typeof
		self.note = 0x00
		self.volume = 0x0
		self.shape = 0x00
		self.loop = None

class pattern:
	def __init__(self):
		self.used = False
		self.rows = []

class row:
	def __init__(self):
		self.ch1Note = None
		self.ch1Inst = None
		self.ch1Tied = False

		self.ch2Note = None
		self.ch2Inst = None
		self.ch2Tied = False

		self.ch3Note = None
		self.ch3Inst = None
		self.ch3Tied = False
		self.sample = None

		self.ch4Inst = None

		self.fxComm = None
		self.fxArg	= None


if __name__=='__main__':
	# Get input data
	if args.sav:
		inputName = args.sav
		with open(args.sav, "rb") as inFile:
			musicBank = bytearray(inFile.read(0x4000))
			samBank	= bytearray(inFile.read(0x4000))
	elif args.bin:
		inputName = args.bin[0]
		with open(args.bin[0], "rb") as inFile:
			musicBank = bytearray(inFile.read(0x4000))
		if len(args.bin) > 1:
			with open(args.bin[1], "rb") as inFile:
				samBank = bytearray(inFile.read(0x4000))
	elif args.rom:
		inputName = args.rom[0]
		with open(args.rom[0], "rb") as inFile:
			inFile.seek(eval(args.rom[1]))
			musicBank = bytearray(inFile.read(0x4000))
			if len(args.rom) > 2:
				inFile.seek(eval(args.rom[2]))
				samBank = bytearray(bytearray(inFile.read(0x4000)))

	if not 'musicBank' in vars():
		print("ERROR: No music source loaded!")
		exit(1)

	# Read instruments
	wInstruments = []
	for wInstType in range(3):
		wInstArray = []
		for wInstIndex in range(16):
			wInst = instrument(wInstType)
			wInst.panning = musicBank[MUSBANK_PANTABLE + (wInstType * 16) + wInstIndex]
			wInst.panning |= (wInst.panning << 1) | (wInst.panning << 2) | (wInst.panning << 3)
			for wRowIndex in range(16):
				wRow = spRow(wInstType)
				if wInstType == INST_TYPEOF_DUTY:
					wRow.length = musicBank[MUSBANK_PULSE_VOLLEN + (wInstIndex * 16) + wRowIndex] & 0x0F
					if wRow.length == 0x00:
						wRow.loop = musicBank[MUSBANK_PULSE_NOTEDUTY + (wInstIndex * 16) + wRowIndex]
					wRow.volume = musicBank[MUSBANK_PULSE_VOLLEN + (wInstIndex * 16) + wRowIndex] >> 4
					wRow.shape = musicBank[MUSBANK_PULSE_NOTEDUTY + (wInstIndex * 16) + wRowIndex] & 0b11
					wRow.note = musicBank[MUSBANK_PULSE_NOTEDUTY + (wInstIndex * 16) + wRowIndex] >> 2
					if wRow.note >= 0x20:
						wRow.note -= 0x40
				
				elif wInstType == INST_TYPEOF_WAVE:
					wRow.length = musicBank[MUSBANK_WAVE_INDEXLEN + (wInstIndex * 16) + wRowIndex] & 0x0F
					if wRow.length == 0x00:
						wRow.loop = musicBank[MUSBANK_WAVE_NOTEVOL + (wInstIndex * 16) + wRowIndex]
					wRow.shape = musicBank[MUSBANK_WAVE_INDEXLEN + (wInstIndex * 16) + wRowIndex] >> 4
					wRow.volume = [0b00, 0b11, 0b10, 0b01][musicBank[MUSBANK_WAVE_NOTEVOL + (wInstIndex * 16) + wRowIndex] & 0b11]
					wRow.note = musicBank[MUSBANK_WAVE_NOTEVOL + (wInstIndex * 16) + wRowIndex] >> 2
					if wRow.note >= 0x20:
						wRow.note -= 0x40

				elif wInstType == INST_TYPEOF_NOISE:
					wRow.length = musicBank[MUSBANK_NOISE_VOLLEN + (wInstIndex * 16) + wRowIndex] & 0x0F
					if wRow.length == 0x00:
						wRow.loop = musicBank[MUSBANK_NOISE_FREQ + (wInstIndex * 16) + wRowIndex]
					wRow.volume = musicBank[MUSBANK_NOISE_VOLLEN + (wInstIndex * 16) + wRowIndex] >> 4
					wRow.shape = musicBank[MUSBANK_NOISE_FREQ + (wInstIndex * 16) + wRowIndex]

				# add
				wInst.subpattern.append(wRow)
			wInstArray.append(wInst)
		wInstruments.append(wInstArray)

	wWaveforms = []
	for wWaveIndex in range(16):
		wWave = bytearray([])
		for i in range(16):
			wWave.append(musicBank[MUSBANK_WAVETABLE + ((wWaveIndex << 4) + i)])
		wWaveforms.append(wWave)
	
	# Read order
	wOrderTable = []
	wOrderIndex = 0x00
	while wOrderIndex < 255:
		wOrder = musicBank[MUSBANK_ORDER_TABLE + wOrderIndex]
		if wOrder == 0x00:
			# Next order might be loop/end or null
			wJump = musicBank[MUSBANK_ORDER_TABLE + wOrderIndex + 1]
			if wJump == 0xFF:
				# Store end
				wOrder = ORDER_END_CMD
			elif wJump == 0x00:
				# Empty row
				wOrder = ORDER_EMPTY_CMD
			else:
				wOrder = ORDER_LOOP_CMD | wJump
			wOrderTable.append(wOrder)
			# To keep table aligned and avoid issues with jumps
			wOrderTable.append(0x0000)
			wOrderIndex += 2
		else:
			wOrder = wOrder - 0x50
			wOrderTable.append(wOrder)
			wOrderIndex += 1

	# Read patterns
	wUsingSamples = False
	wPatterns = []
	wReferencedSamples = [False] * 16
	wMaxUsedSample = -1
	for wPatternIndex in range(0x30):
		wPatternPtr = 0x1000 + (wPatternIndex * 0x100)
		wPattern = pattern()
		wPattern.used = True # Placeholder
		for wRowIndex in range(0x20):
			wRow = row()

			# CH1
			wRow.ch1Note = musicBank[wPatternPtr] >> 1
			if wRow.ch1Note == 0x00:
				wRow.ch1Note = None
			else:
				wRow.ch1Note -= 12
				wRow.ch1Tied = bool(musicBank[wPatternPtr] & 1)
			wPatternPtr += 1
			if wRow.ch1Tied == False and (wRow.ch1Note != None):
				wRow.ch1Inst = musicBank[wPatternPtr] >> 4
			wPatternPtr += 1

			# CH2
			wRow.ch2Note = musicBank[wPatternPtr] >> 1
			if wRow.ch2Note == 0x00:
				wRow.ch2Note = None
			else:
				wRow.ch2Note -= 12
				wRow.ch2Tied = bool(musicBank[wPatternPtr] & 1)
			wPatternPtr += 1
			if wRow.ch2Tied == False and (wRow.ch2Note != None):
				wRow.ch2Inst = musicBank[wPatternPtr] >> 4
			wPatternPtr += 1

			# CH3
			if musicBank[wPatternPtr] == 0xFF:
				wPatternPtr += 1
				wRow.sample = musicBank[wPatternPtr]
				wPatternPtr += 1
				wReferencedSamples[wRow.sample] = True
				wMaxUsedSample = max(wRow.sample, wMaxUsedSample)
			else:
				wRow.ch3Note = musicBank[wPatternPtr] >> 1
				if wRow.ch3Note == 0x00:
					wRow.ch3Note = None
				else:
					wRow.ch3Note -= 12
					wRow.ch3Tied = bool(musicBank[wPatternPtr] & 1)
				wPatternPtr += 1
				if wRow.ch3Tied == False and (wRow.ch3Note != None):
					wRow.ch3Inst = musicBank[wPatternPtr] >> 4
				wPatternPtr += 1

			# CH4
			if musicBank[wPatternPtr] != 0x00:
				wRow.ch4Inst = musicBank[wPatternPtr] >> 4
			wPatternPtr += 1

			# Effect
			if musicBank[wPatternPtr] != 0x00:
				wRow.fxComm = musicBank[wPatternPtr] >> 4
				wRow.fxArg = musicBank[wPatternPtr] & 0x0F

			wPatternPtr += 1

			wPattern.rows.append(wRow)
		wPatterns.append(wPattern)

	# If available, load sample data
	wSamplePanning = [0xFF] * 16
	wSamples = [None] * 16
	if 'samBank' in vars():
		# Read sample info from table
		for wSampleIndex in range(16):
			wSampleAddr = (musicBank[MUSBANK_SAMPLE_INFO + (wSampleIndex * 2)] << 8) - 0x4000
			wSampleLen 	= musicBank[MUSBANK_SAMPLE_INFO + (wSampleIndex * 2) + 1] * 16
			# If empty...
			if wSampleAddr < 0x0000:
				# If sample index is referenced in music data
				if wReferencedSamples[wSampleIndex] != False:
					print(f"WARNING! Sample #{wSampleIndex:01X} is referenced in music data, but index sample contains invalid/null data!")
				continue
			# Read panning
			wSamplePanning[wSampleIndex] = musicBank[MUSBANK_PANTABLE + (3 * 16) + wSampleIndex]
			wSamplePanning[wSampleIndex] |= (wSamplePanning[wSampleIndex] << 1) | (wSamplePanning[wSampleIndex] << 2) | (wSamplePanning[wSampleIndex] << 3)
			wSampleData = bytearray([])
			for i in range(wSampleLen):
				if wSampleAddr >= len(samBank):
					print(f"WARNING! Sample #{wSampleIndex:01X} is longer than sample bank! Cut short!")
					break
				wSampleData.append(samBank[wSampleAddr])
				wSampleAddr += 1

			wSamples[wSampleIndex] = bytearray(wSampleData)
	else:
		i = 0
		for wSampleIndex in wReferencedSamples:
			if wSampleIndex != False:
				print(f"WARNING! Sample #{i:01X} is referenced in music data, but no sample bank was passed!")
			i += 1

	# Output
	outText = "; Carillon Music data generated with Caroline.py by Coffee 'Valen' Bat\n"

	## Sample info
	outText += "\nIF DEF(loadSampleInfo)\nPURGE loadSampleInfo\nENDC\n"
	outText += "\nMACRO loadSampleInfo\n"
	for wSampleIndex in range(16):
		if wSamples[wSampleIndex] == None:
			outText += f"; Sample #{wSampleIndex} (Null pointer)\n"
			outText += "\tdb HIGH(NULL)\n"
			outText += "\tdb $01\n"
		else:
			outText += f"; Sample #{wSampleIndex}\n"
			outText += f"\tdb HIGH(sample{wSampleIndex}Data)\n"
			outText += f"\tdb (sample{wSampleIndex}Data.end - sample{wSampleIndex}Data) >> 4\n"
	outText += "ENDM\n"

	## Generate panning info
	outText += "\nIF DEF(loadPanTable)\nPURGE loadPanTable\nENDC\n"
	outText += "\nMACRO loadPanTable\n"
	panningLabels = [
		".pulse:\n", 
		".wave:\n", 
		".noise:\n",
		".smp:\n"
	]
	for wInstType in range(3):
		wPanning = bytearray([])
		for wInst in wInstruments[wInstType]:
			wPanning.append(wInst.panning & 0x11)
		outText += panningLabels[wInstType]
		outText += dumpBin(wPanning, 16, "\tdb")

	# Sample panning (used but never edited by user)
	outText += panningLabels[3]
	wPanning = bytearray([])
	for i in wSamplePanning:
		wPanning.append(i & 0x11)
	outText += dumpBin(wPanning, 16, "\tdb")

	outText += "ENDM\n"

	## Pulse instrument Volume & Length
	outText += "\nIF DEF(loadPulseVolLen)\nPURGE loadPulseVolLen\nENDC\n"
	outText += "\nMACRO loadPulseVolLen"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_DUTY]:
		# Get volume and tick length of every instrument
		outText += f"\n; PULSE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				outText += "\tdpVolLen DN_JUMP\n"
			else:
				outText += f"\tdpVolLen ${wRow.volume:01X}, ${wRow.length:01X}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Pulse instrument Note & Duty
	outText += "\nIF DEF(loadPulseNoteDuty)\nPURGE loadPulseNoteDuty\nENDC\n"
	outText += "\nMACRO loadPulseNoteDuty"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_DUTY]:
		# Get volume and tick length of every instrument
		outText += f"\n; PULSE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				if wRow.loop == 0xFF:
					wRow.loop = "DN_END"
				else:
					wRow.loop = f"${wRow.loop:02X}"
				outText += f"\tdpNoteDuty {wRow.loop}\n"
			else:
				outText += f"\tdpNoteDuty {NOTE_TABLE[wRow.note + 36]}, {wRow.shape}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Wave instrument Index & Length
	outText += "\nIF DEF(loadWaveIndexLen)\nPURGE loadWaveIndexLen\nENDC\n"
	outText += "\nMACRO loadWaveIndexLen"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_WAVE]:
		# Get volume and tick length of every instrument
		outText += f"\n; WAVE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				outText += "\tdwIndexLen DN_JUMP\n"
			else:
				outText += f"\tdwIndexLen ${wRow.shape:01X}, ${wRow.length:01X}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Wave instrument Volume & Length
	outText += "\nIF DEF(loadWaveNoteVol)\nPURGE loadWaveNoteVol\nENDC\n"
	outText += "\nMACRO loadWaveNoteVol"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_WAVE]:
		# Get volume and tick length of every instrument
		outText += f"\n; WAVE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				if wRow.loop == 0xFF:
					wRow.loop = "DN_END"
				else:
					wRow.loop = f"${wRow.loop:02X}"
				outText += f"\tdwNoteVol {wRow.loop}\n"
			else:
				outText += f"\tdwNoteVol {NOTE_TABLE[wRow.note + 36]}, {wRow.volume:01X}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Waveforms
	outText += "\nIF DEF(loadWaveTable)\nPURGE loadWaveTable\nENDC\n"
	outText += "\nMACRO loadWaveTable\n"
	for wWave in wWaveforms:
		outText += "\twavetable "
		for b in wWave:
			outText += f"{b:02X}"
		outText += "\n"
	outText += "ENDM\n"

	## Noise instrument Volume & Length
	outText += "\nIF DEF(loadNoiseVolLen)\nPURGE loadNoiseVolLen\nENDC\n"
	outText += "\nMACRO loadNoiseVolLen"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_NOISE]:
		# Get volume and tick length of every instrument
		outText += f"\n; NOISE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				outText += "\tdnVolLen DN_JUMP\n"
			else:
				outText += f"\tdnVolLen ${wRow.volume:01X}, ${wRow.length:01X}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Noise instrument Freq
	outText += "\nIF DEF(loadNoiseFreq)\nPURGE loadNoiseFreq\nENDC\n"
	outText += "\nMACRO loadNoiseFreq"
	wInstIndex = 0
	for wInst in wInstruments[INST_TYPEOF_NOISE]:
		# Get volume and tick length of every instrument
		outText += f"\n; NOISE #{wInstIndex}\n"
		for wRow in wInst.subpattern:
			if wRow.loop != None:
				if wRow.loop == 0xFF:
					wRow.loop = "DN_END"
				else:
					wRow.loop = f"${wRow.loop:02X}"
				outText += f"\tdnPolyFreq {wRow.loop}\n"
			else:
				outText += f"\tdnPolyFreq ${wRow.shape:02X}\n"
		wInstIndex += 1
	outText += "ENDM\n"

	## Order table
	outText += "\nIF DEF(loadOrderTable)\nPURGE loadOrderTable\nENDC\n"
	outText += "\nMACRO loadOrderTable\n"
	wOrderIndex = 0
	while wOrderIndex < len(wOrderTable):
		if wOrderTable[wOrderIndex] == ORDER_EMPTY_CMD:
			outText += "\tdb $00 ; Empty\n"
			wOrderIndex += 1
		elif wOrderTable[wOrderIndex] == ORDER_END_CMD:
			outText += "\tdb $00, $FF ; End of song section\n"
			wOrderIndex += 1
		elif wOrderTable[wOrderIndex] & 0xFF00 == ORDER_LOOP_CMD:
			outText += f"\tdb $00, ${(wOrderTable[wOrderIndex] & 0xFF):02X} ; Loop command\n"
			wOrderIndex += 1
		else:
			outText += f"\tdb HIGH(pattern{wOrderTable[wOrderIndex]}Data)\n"
		wOrderIndex += 1
	outText += "ENDM\n"

	## Finally... patterns
	outText += "\nIF DEF(loadPatternData)\nPURGE loadPatternData\nENDC\n"
	outText += "\nMACRO loadPatternData"
	wPatternIndex = 0
	for wPattern in wPatterns:
		if wPattern.used == True:
			outText += f"\nds align[8]\npattern{wPatternIndex}Data:\n"
			for wRow in wPattern.rows:
				outText += f"\tdn "
				
				# CH1 Note
				if wRow.ch1Note == None:
					outText += "___, "
				else:
					outText += f"{NOTE_TABLE[wRow.ch1Note]}, "

				# Tied flag/Inst
				if wRow.ch1Tied == True:
					outText += "TI, "
				elif wRow.ch1Inst == None:
					outText += "__, "
				else:
					outText += f"${wRow.ch1Inst:01X}, "

				# CH2 Note
				if wRow.ch2Note == None:
					outText += "___, "
				else:
					outText += f"{NOTE_TABLE[wRow.ch2Note]}, "

				# Tied flag/Inst
				if wRow.ch2Tied == True:
					outText += "TI, "
				elif wRow.ch2Inst == None:
					outText += "__, "
				else:
					outText += f"${wRow.ch2Inst:01X}, "

				# CH3 Note
				if wRow.sample != None:
					outText += "SMP, "
				elif wRow.ch3Note == None:
					outText += "___, "
				else:
					outText += f"{NOTE_TABLE[wRow.ch3Note]}, "

				# Tied flag/Inst
				if wRow.sample != None:
					outText += f"${wRow.sample:01X}, "
				elif wRow.ch3Tied == True:
					outText += "TI, "
				elif wRow.ch3Inst == None:
					outText += "__, "
				else:
					outText += f"${wRow.ch3Inst:01X}, "

				# CH4 Inst
				if wRow.ch4Inst != None:
					outText += f"${wRow.ch4Inst:01X}, "
				else:
					outText += "__, "

				# Effect and arg
				if wRow.fxArg != None:
					outText += f"{FX_TABLE[wRow.fxComm]}, ${wRow.fxArg:01X}"
				else:
					outText += "__, __"

				outText += "\n"
		wPatternIndex += 1

	outText += "ENDM\n"

	## Sample data
	outText += "\nIF DEF(loadSampleData)\nPURGE loadSampleData\nENDC\n"
	outText += "\nMACRO loadSampleData\n"
	for wSampleIndex in range(len(wSamples)):
		if wSamples[wSampleIndex] != None:
			outText += "ds align[8]\n"
			outText += f"sample{wSampleIndex}Data:\n"
			outText += dumpBin(wSamples[wSampleIndex], 16, "\tdb")
			outText += ".end:\n"
	outText += "ENDM\n"


	## Done! Output file
	if args.output != None:
		outName = args.output
	else:
		outName = splitext(inputName)[0] + ".crlmod"

	with open(outName, "w") as outFile:
		outFile.write(outText)