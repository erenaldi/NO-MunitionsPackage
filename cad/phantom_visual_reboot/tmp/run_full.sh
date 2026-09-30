cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot/src"
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe" -c "
import engine_bay_b2d as d
d.deployed_full(); d.stowed_full()" > ../tmp/full_build.log 2>&1
echo finished > ../tmp/full_done.txt
