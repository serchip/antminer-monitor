from app import db


class MinerСontainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return "MinerСontainer(description='{}')".format(self.model, self.chips, self.description)
