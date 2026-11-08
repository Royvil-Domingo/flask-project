from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask import current_app
from ..models.user import User
from flask_login import login_required
from ..extensions import db
from ..models.borrower import Borrower
from ..models.borrowing import Borrowing
from ..utils.decorators import admin_required

borrowers = Blueprint('borrowers', __name__, url_prefix='/borrowers')


@borrowers.route('/')
@login_required
@admin_required
def list_borrowers():
    query = request.args.get('q', '').strip()
    borrowers_query = Borrower.query
    if query:
        borrowers_query = borrowers_query.filter(
            (Borrower.name.ilike(f'%{query}%')) | (Borrower.contact.ilike(f'%{query}%'))
        )
    items = borrowers_query.order_by(Borrower.name.asc()).all()
    return render_template('borrowers/list.html', items=items, query=query)


@borrowers.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_borrower():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()

        if len(name) < 2:
            flash('Borrower name must be at least 2 characters.', category='error')
        elif len(contact) < 5:
            flash('Please provide a valid contact number or email.', category='error')
        else:
            new_borrower = Borrower(name=name, contact=contact)
            db.session.add(new_borrower)
            db.session.commit()
            flash('Borrower registered successfully!', category='success')
            return redirect(url_for('borrowers.list_borrowers'))

    return render_template('borrowers/form.html', item=None)


@borrowers.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_borrower(item_id):
    item = Borrower.query.get_or_404(item_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()

        if len(name) < 2:
            flash('Borrower name must be at least 2 characters.', category='error')
        elif len(contact) < 5:
            flash('Please provide a valid contact number or email.', category='error')
        else:
            item.name = name
            item.contact = contact
            db.session.commit()
            flash('Borrower updated successfully!', category='success')
            return redirect(url_for('borrowers.list_borrowers'))

    return render_template('borrowers/form.html', item=item)


@borrowers.route('/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_borrower(item_id):
    item = Borrower.query.get_or_404(item_id)

    history_count = Borrowing.query.filter_by(borrower_id=item.id).count()
    if history_count > 0:
        flash(
            f'Cannot delete "{item.name}": they have {history_count} borrowing record(s) '
            'in the history. Records are kept for the audit trail.',
            category='error'
        )
        return redirect(url_for('borrowers.list_borrowers'))

    linked_user = item.user

    try:
        if linked_user:
            # Legacy records may reference this account as the processing user.
            Borrowing.query.filter_by(processed_by_id=linked_user.id).update(
                {Borrowing.processed_by_id: None}, synchronize_session=False
            )

        db.session.delete(item)
        db.session.flush()

        # Remove the linked normal login account too (never an admin).
        if linked_user and linked_user.role != 'admin':
            db.session.delete(linked_user)

        db.session.commit()
        flash('Borrower deleted.', category='success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete borrower ID %s", item_id)
        flash('Unable to delete borrower. Please try again.', category='error')

    return redirect(url_for('borrowers.list_borrowers'))