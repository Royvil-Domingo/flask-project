from datetime import date, datetime
from ..extensions import db


class Borrowing(db.Model):
    __tablename__ = 'borrowings'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False)

    # The admin who approved or rejected this request. Null while pending.
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    quantity = db.Column(db.Integer, nullable=False)
    requested_on = db.Column(db.Date, nullable=False, default=date.today)
    borrowed_on = db.Column(db.Date, nullable=True)
    due_on = db.Column(db.Date, nullable=False)
    returned_on = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, borrowed, rejected, returned
    rejection_reason = db.Column(db.String(255), nullable=True)

    equipment = db.relationship('Equipment', back_populates='borrowings')
    borrower = db.relationship('Borrower', back_populates='borrowings')
    processed_by = db.relationship('User', back_populates='processed_borrowings')

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='chk_quantity_positive'),
    )

    @property
    def is_overdue(self):
        return self.status == 'borrowed' and self.due_on < date.today()

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_rejected(self):
        return self.status == 'rejected'

    def __repr__(self):
        return f'<Borrowing {self.id} - {self.status}>'