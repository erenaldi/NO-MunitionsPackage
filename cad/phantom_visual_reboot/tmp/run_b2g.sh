cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot"
PY="C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe"
(cd src && "$PY" -c "
import engine_bay_b2g as g
g.nozzle_section(); g.deployed_full(); g.stowed_full()") > tmp/b2g_build.log 2>&1
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/cadgen.exe" step snapshot --job review_engine_bay_b2g.json > tmp/b2g_snap.log 2>&1
echo finished > tmp/b2g_done.txt
