import time,json,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from config.settings_loader import load_settings
from planner.keeper import Keeper
from prices.store import CandleStore
from tests.planner_helpers import Over, section
UTC=timezone.utc
base=load_settings().for_pair("GBPUSD")
d=Path(tempfile.mkdtemp())
s=Over(base, planner=section(base.planner, folder=d, historical_daily_swing_lookback_weeks=0))
store=CandleStore(Path("/opt/autobot/data/research/stp_validation_store/GBPUSD"),base.candles.compress_after_days)
import sys; t=datetime.fromisoformat(sys.argv[1]).replace(tzinfo=UTC); END=datetime.fromisoformat(sys.argv[2]).replace(tzinfo=UTC); t0=time.time()
while t<END:
    k=Keeper(s,store); k.run(t)
    st=k.state
    t+=timedelta(minutes=5)
print("secs",time.time()-t0)
print(json.dumps(st.get("last_ended"),default=str)[:600])
import glob,gzip
for f in sorted(glob.glob(str(d)+"/**/*",recursive=True)): print(f)

for l in open(d/"GBPUSD"/"recommendations.jsonl"):
    r=json.loads(l); print({k:(str(v)[:110]) for k,v in r.items() if k not in ("plan",)})
