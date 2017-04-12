# I finally got Pygame to work on my Mac. But, possibly because I'm using 
# MacPorts, it requires pointing the compiler at an unusual place. This
# script represents what I'm doing whenever I discover yet another missing
# dependency for pygame. Just update the list of modules in the second line
# and re-run it. (Suck, suck, suck!)
pip uninstall pygame
for x in ttf image sound mixer gfx net ; do sudo port install libsdl_$x ; done
pip install --global-option=build_ext --global-option="--include-dirs=/opt/local/include" pygame
