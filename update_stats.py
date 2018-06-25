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
        miner.check_stats()
    except TypeError:
        pass

print("[INFO] Updating DB successfully finished")