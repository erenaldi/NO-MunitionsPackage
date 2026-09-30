cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot"
PY="C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe"
(cd src && "$PY" engine_bay_b2h.py) > tmp/b2h_build.log 2>&1
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/cadgen.exe" step snapshot --job review_engine_bay_b2h.json > tmp/b2h_snap.log 2>&1
echo finished > tmp/b2h_done.txt
