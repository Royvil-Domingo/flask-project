from datetime import datetime
from ..extensions import db


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.String(500))
    total_quantity = db.Column(db.Integer, nullable=False, default=0)
    available_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrowings = db.relationship('Borrowing', back_populates='equipment', lazy=True)

    __table_args__ = (
        db.CheckConstraint('total_quantity >= 0', name='chk_total_quantity_non_negative'),
        db.CheckConstraint('available_quantity >= 0', name='chk_available_quantity_non_negative'),
        db.CheckConstraint('available_quantity <= total_quantity', name='chk_available_lte_total'),
    )

    @property
    def borrowed_quantity(self):
        return self.total_quantity - self.available_quantity

    def __repr__(self):
        return f'<Equipment {self.name}>'