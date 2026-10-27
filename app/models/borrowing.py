from datetime import date, datetime
from ..extensions import db


class Borrowing(db.Model):
    __tablename__ = 'borrowings'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    quantity = db.Column(db.Integer, nullable=False)
    borrowed_on = db.Column(db.Date, nullable=False, default=date.today)
    due_on = db.Column(db.Date, nullable=False)
    returned_on = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='borrowed')  # borrowed, returned

    equipment = db.relationship('Equipment', back_populates='borrowings')
    borrower = db.relationship('Borrower', back_populates='borrowings')
    processed_by = db.relationship('User', back_populates='processed_borrowings')

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='chk_quantity_positive'),
    )

    @property
    def is_overdue(self):
        return self.status == 'borrowed' and self.due_on < date.today()

    def __repr__(self):
        return f'<Borrowing {self.id} - {self.status}>'