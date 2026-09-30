cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot"
PY="C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe"
(cd src && "$PY" engine_bay_cosmetic.py) > tmp/b2f_build.log 2>&1
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/cadgen.exe" step snapshot --job review_engine_bay_b2f.json > tmp/b2f_snap.log 2>&1
echo finished > tmp/b2f_done.txt
