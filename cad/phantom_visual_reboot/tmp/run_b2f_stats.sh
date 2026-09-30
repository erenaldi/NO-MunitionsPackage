cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot/src"
"C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe" -c "
import json, engine_bay_cosmetic as c
out={}
for st in ('Deployed','Stowed'):
    c.full(st); out[st]=c.full.stats
open('../reviews/engine_bay_b2f_engraving.json','w').write(json.dumps(out,indent=1)); print(json.dumps(out))
" > ../tmp/b2f_stats.log 2>&1
echo finished > ../tmp/b2f_stats_done.txt
