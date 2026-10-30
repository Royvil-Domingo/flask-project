from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models.equipment import Equipment
from ..models.borrowing import Borrowing

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    equipment_items = Equipment.query.all()
    total_equipment_types = len(equipment_items)
    total_units = sum(e.total_quantity for e in equipment_items)
    available_units = sum(e.available_quantity for e in equipment_items)
    borrowed_units = total_units - available_units

    if current_user.is_admin:
        pending_count = Borrowing.query.filter_by(status='pending').count()
        overdue_borrowings = Borrowing.query.filter(
            Borrowing.status == 'borrowed',
            Borrowing.due_on < date.today()
        ).count()
        recent_borrowings = Borrowing.query.order_by(Borrowing.id.desc()).limit(5).all()

        return render_template(
            'main/dashboard.html',
            total_equipment_types=total_equipment_types,
            available_units=available_units,
            borrowed_units=borrowed_units,
            pending_count=pending_count,
            overdue_borrowings=overdue_borrowings,
            recent_borrowings=recent_borrowings
        )

    borrower_profile = current_user.borrower_profile
    my_pending = my_active = my_overdue = 0
    my_recent = []
    if borrower_profile is not None:
        my_pending = Borrowing.query.filter_by(borrower_id=borrower_profile.id, status='pending').count()
        my_active = Borrowing.query.filter_by(borrower_id=borrower_profile.id, status='borrowed').count()
        my_overdue = Borrowing.query.filter(
            Borrowing.borrower_id == borrower_profile.id,
            Borrowing.status == 'borrowed',
            Borrowing.due_on < date.today()
        ).count()
        my_recent = Borrowing.query.filter_by(borrower_id=borrower_profile.id).order_by(Borrowing.id.desc()).limit(5).all()

    return render_template(
        'main/dashboard.html',
        total_equipment_types=total_equipment_types,
        available_units=available_units,
        my_pending=my_pending,
        my_active=my_active,
        my_overdue=my_overdue,
        my_recent=my_recent
    )