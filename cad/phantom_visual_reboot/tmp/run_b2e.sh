cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot"
PY="C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe"
(cd src && "$PY" engine_bay_b2e.py) > tmp/b2e_build.log 2>&1
"$PY" checks/check_engine_bay_b2e.py > tmp/b2e_check.log 2>&1
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/cadgen.exe" step snapshot --job review_engine_bay_b2e.json > tmp/b2e_snap.log 2>&1
echo finished > tmp/b2e_done.txt
