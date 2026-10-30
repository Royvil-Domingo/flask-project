from datetime import datetime
from ..extensions import db


class Borrower(db.Model):
    __tablename__ = 'borrowers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    contact = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='borrower_profile')
    borrowings = db.relationship('Borrowing', back_populates='borrower', lazy=True)

    def __repr__(self):
        return f'<Borrower {self.name}>'