# Carillon Player
This is a dissasembly of [Aleksi Eeben](https://aleksieeben.wordpress.com/)'s Carillon Player, a Game Boy music engine focused on speed (0-3 Scanlines on CGB max). This dissasembly is based on what I believe is the latest version of Carillon Player, using a mix of the included example ROMs and the playback code present in Carillon Editor v1.2.

This repository is supposed to work less as a 100% matching dissasembly of Carillon and more as a documentation of the format and an easy to use/understand version of the source code, hopefully allowing for easier implementation in Homebrew.

**Right now this repository is still very WIP!**

# Format
For info on the Carillon Player format, see inside [docs](docs/carillon-format.md).

# Compiling
Simply open you favorite command prompt / terminal, place yourself in this directory (the one the Makefile is located in), and run the command `make`.
This should create a bunch of things, including the output in the `bin` directory. 

To change the module to build, simply change `CARILLON_MODULE` in `project.mk` to target your desired file. Right now, the repository contains all the original example Carillon modules as .SAV files for playback. To enable/disable the sample player, simply comment out the line below it. Music that uses samples will work without it but will lack sample playback.

Pass the `-s` flag to `make` if it spews too much input for your tastes.
Päss the `-j <N>` flag to `make` to build more things in parallel, replacing `<N>` with however many things you want to build in parallel; your number of (logical) CPU cores is often a good pick (so, `-j 8` for me), run the command `nproc` to obtain it.

If you get errors that you don't understand, try running `make clean`.
If that gives the same error, try deleting the `assets` directory.
If that still doesn't work, try deleting the `bin` and `obj` directories as well.
If that still doesn't work, feel free to ask for help.

# External Usage
Right now the code is still early on enough that external implementation is not 100% done yet, but for the brave...

To add a Carillon music/sample bank to your program, simply `include` the `carillon_stub.gbz80` file in your RGBDS project, and don't forget to pass the variable `_CARILLON_MODULE` with the path to your project file. This repository contains an example ROM that loads a module from a SAV file. If you're using a build system like Make, make (hehe) sure that none of the files inside the `carillon` folder get picked up as a source, this can be achieved through different ways, but this repo achieves it by using the `.asm` extension for source assembly files and the `.gbz80` extension for files that should be scanned.

Right now due to the structure of the driver, it's not possible to embed multiple copies of Carillon+Music+Samples on a single project. This is something I wanna support in the future but I need a proper structure that doesn't create colliding labels. Any ideas are welcome!

The driver also utilizes [Debugfiles](https://github.com/ISSOtm/debugfile.inc/wiki) to allow for clearer debugging of the driver. To enable extensive logging, define `_CARILLON_LOG`. These debug info and assertions are currently supported by [Emulicious](https://emulicious.net/).

# TODO
- Port documentation from Carillon's release from HTML to MD
- Modern alternative of Carillon Editor Utility?
- New example ROM?
- ROM0+ROMX version (Allowing for proper GBDK support)?

# Credits
- [Aleksi Eeben](https://aleksieeben.wordpress.com/): Original author of Carillon Player
- [Coffee 'Valen' Bat](https://x.com/Cofebbat): Tools and Dissasembly
- [ISSOtm](https://eldred.fr/): Author of gb-boilerplate, used as a template for this repo, and [debugfile.inc](https://github.com/ISSOtm/debugfile.inc), used for versatile debugging.

This project uses the [gb-boilerplate](https://github.com/ISSOtm/gb-boilerplate) template by ISSOtm, under the zlib license.