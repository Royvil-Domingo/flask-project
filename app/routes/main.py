from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date
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

    overdue_borrowings = Borrowing.query.filter(
        Borrowing.status == 'borrowed',
        Borrowing.due_on < date.today()
    ).count()

    recent_borrowings = Borrowing.query.order_by(Borrowing.id.desc()).limit(5).all()

    return render_template(
        'main/dashboard.html',
        total_equipment_types=total_equipment_types,
        total_units=total_units,
        available_units=available_units,
        borrowed_units=borrowed_units,
        overdue_borrowings=overdue_borrowings,
        recent_borrowings=recent_borrowings
    )