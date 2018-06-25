#-*- coding:utf-8 -*-
from app.models import Miner, MinerModel, Settings, MinerСontainer
from app import db
from lib.pycgminer import (get_summary,
                               get_pools,
                               get_stats,
                               )
from sqlalchemy import update
import json



print("[INFO] Starting DB update...")


for miner in Miner.query.all():
    try:
        miner_stats = get_stats(miner.ip)
        miner_stats = json.dumps(miner_stats)
        miner_pools = get_pools(miner.ip)
        miner_pools = json.dumps(miner_pools)
        miner.stats = miner_stats
        miner.pools = miner_pools
        db.session.commit()
    except TypeError:
        pass

db.session.commit()
    
print("[INFO] Updating DB successfully finished")