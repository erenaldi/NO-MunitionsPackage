cd "C:/Users/erena/Desktop/Nuclear Option Munitions Package/cad/phantom_visual_reboot"
PY="C:/Users/erena/.config/opencode/cadgen-venv/Scripts/python.exe"
for c in check_ramp_intake_r3 check_aft_exhaust_r1 check_tail_fin_r4 check_interleaved_a5; do
  "$PY" src/$c.py > tmp/reg_$c.log 2>&1
  echo "$c exit $?" >> tmp/reg_summary.txt
done
"$PY" checks/check_agm1_reference_fit.py > tmp/reg_agm1.log 2>&1
echo "check_agm1_reference_fit exit $? (nonzero expected by design)" >> tmp/reg_summary.txt
echo finished >> tmp/reg_summary.txt
