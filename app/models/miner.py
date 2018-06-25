from app import db
import json

class Miner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('miner_model.id'), nullable=False)
    model = db.relationship("MinerModel", backref="miners")
    container_id = db.Column(db.Integer, db.ForeignKey('minerСontainer.id'), nullable=False)
    container = db.relationship('MinerСontainer', backref='miners')
    remarks = db.Column(db.String(255), nullable=True)
    stats = db.Column(db.Text(), nullable=True)
    pools = db.Column(db.Text(), nullable=True)

    def get_stats(self):
        if self.stats:
            return json.loads(self.stats)
        return {}

    def get_pools(self):
        if self.pools:
            return json.loads(self.pools)
        return {}

    def check_stats(self):
        from lib.pycgminer import (get_pools,
                                   get_stats,
                                   )
        import json
        try:
            miner_stats = get_stats(self.ip)
            miner_stats = json.dumps(miner_stats)
        except TypeError:
            miner_stats = None
        try:
            miner_pools = get_pools(self.ip)
            miner_pools = json.dumps(miner_pools)
        except TypeError:
            miner_pools = None
        self.stats = miner_stats
        self.pools = miner_pools
        db.session.commit()

    def __repr__(self):
        return "Miner(ip='{}', model='{}', remarks='{}')".format(self.ip, self.model, self.remarks)
