from datetime import date, datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..extensions import db
from ..models.borrowing import Borrowing
from ..models.equipment import Equipment
from ..models.borrower import Borrower

borrowings = Blueprint('borrowings', __name__, url_prefix='/borrowings')


@borrowings.route('/')
@login_required
def list_borrowings():
    query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    borrowings_query = Borrowing.query.join(Equipment).join(Borrower)

    if query:
        borrowings_query = borrowings_query.filter(
            (Equipment.name.ilike(f'%{query}%')) | (Borrower.name.ilike(f'%{query}%'))
        )

    if status_filter == 'overdue':
        borrowings_query = borrowings_query.filter(
            Borrowing.status == 'borrowed', Borrowing.due_on < date.today()
        )
    elif status_filter in ('borrowed', 'returned'):
        borrowings_query = borrowings_query.filter(Borrowing.status == status_filter)

    items = borrowings_query.order_by(Borrowing.id.desc()).all()
    return render_template(
        'borrowings/list.html', items=items, query=query, status_filter=status_filter
    )


@borrowings.route('/new', methods=['GET', 'POST'])
@login_required
def new_borrowing():
    equipment_list = Equipment.query.filter(Equipment.available_quantity > 0).order_by(Equipment.name.asc()).all()
    borrower_list = Borrower.query.order_by(Borrower.name.asc()).all()

    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id', '')
        borrower_id = request.form.get('borrower_id', '')
        quantity = request.form.get('quantity', '').strip()
        due_on = request.form.get('due_on', '').strip()

        equipment_item = Equipment.query.get(int(equipment_id)) if equipment_id.isdigit() else None
        borrower_item = Borrower.query.get(int(borrower_id)) if borrower_id.isdigit() else None

        if not equipment_item:
            flash('Please select a valid piece of equipment.', category='error')
        elif not borrower_item:
            flash('Please select a valid borrower.', category='error')
        elif not quantity.isdigit() or int(quantity) < 1:
            flash('Quantity must be a positive whole number.', category='error')
        elif not due_on:
            flash('Please provide a due date.', category='error')
        else:
            try:
                due_date = datetime.strptime(due_on, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format.', category='error')
                return render_template(
                    'borrowings/new.html', equipment_list=equipment_list, borrower_list=borrower_list
                )

            qty = int(quantity)
            today = date.today()

            if due_date < today:
                flash('Due date cannot be in the past.', category='error')
            elif qty > equipment_item.available_quantity:
                flash(
                    f'Only {equipment_item.available_quantity} unit(s) of "{equipment_item.name}" are available.',
                    category='error'
                )
            else:
                try:
                    equipment_item.available_quantity -= qty
                    new_record = Borrowing(
                        equipment_id=equipment_item.id,
                        borrower_id=borrower_item.id,
                        processed_by_id=current_user.id,
                        quantity=qty,
                        borrowed_on=today,
                        due_on=due_date,
                        status='borrowed'
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    flash(
                        f'Borrowing recorded: {borrower_item.name} borrowed {qty} x "{equipment_item.name}".',
                        category='success'
                    )
                    return redirect(url_for('borrowings.list_borrowings'))
                except Exception:
                    db.session.rollback()
                    flash('An error occurred while processing the borrowing. Please try again.', category='error')

    return render_template(
        'borrowings/new.html', equipment_list=equipment_list, borrower_list=borrower_list
    )


@borrowings.route('/return/<int:borrowing_id>', methods=['POST'])
@login_required
def return_borrowing(borrowing_id):
    record = Borrowing.query.get_or_404(borrowing_id)

    if record.status != 'borrowed':
        flash('This borrowing has already been returned.', category='error')
        return redirect(url_for('borrowings.list_borrowings'))

    try:
        record.equipment.available_quantity += record.quantity
        record.status = 'returned'
        record.returned_on = date.today()
        db.session.commit()
        flash(
            f'Return processed: {record.borrower.name} returned {record.quantity} x "{record.equipment.name}".',
            category='success'
        )
    except Exception:
        db.session.rollback()
        flash('An error occurred while processing the return. Please try again.', category='error')

    return redirect(url_for('borrowings.list_borrowings'))