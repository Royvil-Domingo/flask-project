from datetime import date, datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import update
from ..extensions import db
from ..models.borrowing import Borrowing
from ..models.equipment import Equipment
from ..models.borrower import Borrower
from ..utils.decorators import admin_required

borrowings = Blueprint('borrowings', __name__, url_prefix='/borrowings')


# ---- Admin: full history, search, and status filters ----
@borrowings.route('/')
@login_required
@admin_required
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
    elif status_filter in ('pending', 'borrowed', 'rejected', 'returned'):
        borrowings_query = borrowings_query.filter(Borrowing.status == status_filter)

    items = borrowings_query.order_by(Borrowing.id.desc()).all()
    return render_template(
        'borrowings/list.html', items=items, query=query, status_filter=status_filter
    )


# ---- Admin: pending-request queue ----
@borrowings.route('/requests')
@login_required
@admin_required
def pending_requests():
    items = Borrowing.query.filter_by(status='pending').order_by(Borrowing.id.asc()).all()
    return render_template('borrowings/requests.html', items=items)


# ---- Borrower: submit a request (does not touch inventory) ----
@borrowings.route('/request', methods=['GET', 'POST'])
@login_required
def submit_borrowing():
    if current_user.is_admin:
        flash('Admin accounts cannot submit borrowing requests.', category='error')
        return redirect(url_for('main.dashboard'))

    borrower_profile = current_user.borrower_profile
    if borrower_profile is None:
        flash('Your account has no borrower profile. Please contact an administrator.', category='error')
        return redirect(url_for('main.dashboard'))

    equipment_list = Equipment.query.filter(Equipment.available_quantity > 0).order_by(Equipment.name.asc()).all()

    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id', '')
        quantity = request.form.get('quantity', '').strip()
        due_on = request.form.get('due_on', '').strip()

        equipment_item = Equipment.query.get(int(equipment_id)) if equipment_id.isdigit() else None

        if not equipment_item:
            flash('Please select a valid piece of equipment.', category='error')
        elif not quantity.isdigit() or int(quantity) < 1:
            flash('Quantity must be a positive whole number.', category='error')
        elif not due_on:
            flash('Please provide a due date.', category='error')
        else:
            try:
                due_date = datetime.strptime(due_on, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format.', category='error')
                return render_template('borrowings/new.html', equipment_list=equipment_list)

            qty = int(quantity)
            today = date.today()

            if due_date < today:
                flash('Due date cannot be in the past.', category='error')
            elif qty > equipment_item.available_quantity:
                flash(
                    f'Only {equipment_item.available_quantity} unit(s) of "{equipment_item.name}" are currently available.',
                    category='error'
                )
            else:
                try:
                    # Pending requests never touch available_quantity.
                    new_record = Borrowing(
                        equipment_id=equipment_item.id,
                        borrower_id=borrower_profile.id,
                        quantity=qty,
                        requested_on=today,
                        due_on=due_date,
                        status='pending'
                    )
                    db.session.add(new_record)
                    db.session.commit()
                    flash(
                        f'Request submitted: {qty} x "{equipment_item.name}", pending admin approval.',
                        category='success'
                    )
                    return redirect(url_for('borrowings.my_borrowings'))
                except Exception:
                    db.session.rollback()
                    flash('An error occurred while submitting your request. Please try again.', category='error')

    return render_template('borrowings/new.html', equipment_list=equipment_list)


# ---- Borrower: their own requests/history only ----
@borrowings.route('/mine')
@login_required
def my_borrowings():
    borrower_profile = current_user.borrower_profile
    if borrower_profile is None:
        flash('Your account has no borrower profile.', category='error')
        return redirect(url_for('main.dashboard'))

    status_filter = request.args.get('status', '').strip()

    # Scoped to the authenticated user's own profile — never trusts any
    # borrower id supplied by the client.
    items_query = Borrowing.query.filter_by(borrower_id=borrower_profile.id)

    if status_filter == 'overdue':
        items_query = items_query.filter(Borrowing.status == 'borrowed', Borrowing.due_on < date.today())
    elif status_filter in ('pending', 'borrowed', 'rejected', 'returned'):
        items_query = items_query.filter(Borrowing.status == status_filter)

    items = items_query.order_by(Borrowing.id.desc()).all()
    return render_template('borrowings/my.html', items=items, status_filter=status_filter)


# ---- Admin: approve (atomic, race-condition safe) ----
@borrowings.route('/<int:borrowing_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_borrowing(borrowing_id):
    record = Borrowing.query.get_or_404(borrowing_id)

    if record.status != 'pending':
        flash('This request has already been reviewed.', category='error')
        return redirect(url_for('borrowings.pending_requests'))

    try:
        # Claim the request atomically — only succeeds if it is still
        # 'pending'. Guards against double-clicking Approve twice.
        claim = db.session.execute(
            update(Borrowing)
            .where(Borrowing.id == record.id, Borrowing.status == 'pending')
            .values(status='borrowed', borrowed_on=date.today(), processed_by_id=current_user.id)
        )

        if claim.rowcount == 0:
            db.session.rollback()
            flash('This request has already been reviewed.', category='error')
            return redirect(url_for('borrowings.pending_requests'))

        # Deduct stock atomically — only succeeds if enough is still
        # available at the moment of approval, not just at request time.
        deduction = db.session.execute(
            update(Equipment)
            .where(Equipment.id == record.equipment_id, Equipment.available_quantity >= record.quantity)
            .values(available_quantity=Equipment.available_quantity - record.quantity)
        )

        if deduction.rowcount == 0:
            db.session.rollback()
            flash(
                f'Not enough stock remains to approve this request for "{record.equipment.name}".',
                category='error'
            )
            return redirect(url_for('borrowings.pending_requests'))

        db.session.commit()
        flash(
            f'Approved: {record.borrower.name} may now borrow {record.quantity} x "{record.equipment.name}".',
            category='success'
        )
    except Exception:
        db.session.rollback()
        flash('An error occurred while approving this request. Please try again.', category='error')

    return redirect(url_for('borrowings.pending_requests'))


# ---- Admin: reject ----
@borrowings.route('/<int:borrowing_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_borrowing(borrowing_id):
    record = Borrowing.query.get_or_404(borrowing_id)
    reason = request.form.get('reason', '').strip()

    try:
        claim = db.session.execute(
            update(Borrowing)
            .where(Borrowing.id == record.id, Borrowing.status == 'pending')
            .values(status='rejected', rejection_reason=reason or None, processed_by_id=current_user.id)
        )

        if claim.rowcount == 0:
            db.session.rollback()
            flash('This request has already been reviewed.', category='error')
        else:
            db.session.commit()
            flash(f'Rejected the request from {record.borrower.name} for "{record.equipment.name}".', category='success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while rejecting this request. Please try again.', category='error')

    return redirect(url_for('borrowings.pending_requests'))


# ---- Admin: process a return (atomic, race-condition safe) ----
@borrowings.route('/return/<int:borrowing_id>', methods=['POST'])
@login_required
@admin_required
def return_borrowing(borrowing_id):
    record = Borrowing.query.get_or_404(borrowing_id)

    try:
        claim = db.session.execute(
            update(Borrowing)
            .where(Borrowing.id == record.id, Borrowing.status == 'borrowed')
            .values(status='returned', returned_on=date.today())
        )

        if claim.rowcount == 0:
            db.session.rollback()
            flash('This borrowing has already been returned.', category='error')
            return redirect(url_for('borrowings.list_borrowings'))

        db.session.execute(
            update(Equipment)
            .where(Equipment.id == record.equipment_id)
            .values(available_quantity=Equipment.available_quantity + record.quantity)
        )

        db.session.commit()
        flash(
            f'Return processed: {record.borrower.name} returned {record.quantity} x "{record.equipment.name}".',
            category='success'
        )
    except Exception:
        db.session.rollback()
        flash('An error occurred while processing the return. Please try again.', category='error')

    return redirect(url_for('borrowings.list_borrowings'))