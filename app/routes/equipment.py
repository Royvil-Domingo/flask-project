from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..extensions import db
from ..models.equipment import Equipment
from ..models.borrowing import Borrowing
from ..utils.decorators import admin_required

equipment = Blueprint('equipment', __name__, url_prefix='/equipment')


@equipment.route('/')
@login_required
def list_equipment():
    query = request.args.get('q', '').strip()
    equipment_query = Equipment.query
    if query:
        equipment_query = equipment_query.filter(Equipment.name.ilike(f'%{query}%'))
    items = equipment_query.order_by(Equipment.name.asc()).all()
    return render_template('equipment/list.html', items=items, query=query)


@equipment.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_equipment():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        total_quantity = request.form.get('total_quantity', '').strip()

        if len(name) < 2:
            flash('Equipment name must be at least 2 characters.', category='error')
        elif not total_quantity.isdigit() or int(total_quantity) < 1:
            flash('Total quantity must be a positive whole number.', category='error')
        elif Equipment.query.filter_by(name=name).first():
            flash('Equipment with that name already exists.', category='error')
        else:
            qty = int(total_quantity)
            new_item = Equipment(
                name=name,
                description=description,
                total_quantity=qty,
                available_quantity=qty
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Equipment registered successfully!', category='success')
            return redirect(url_for('equipment.list_equipment'))

    return render_template('equipment/form.html', item=None)


@equipment.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_equipment(item_id):
    item = Equipment.query.get_or_404(item_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        total_quantity = request.form.get('total_quantity', '').strip()

        borrowed_quantity = item.borrowed_quantity

        if len(name) < 2:
            flash('Equipment name must be at least 2 characters.', category='error')
        elif not total_quantity.isdigit() or int(total_quantity) < 1:
            flash('Total quantity must be a positive whole number.', category='error')
        elif int(total_quantity) < borrowed_quantity:
            flash(f'Total quantity cannot be less than currently borrowed units ({borrowed_quantity}).', category='error')
        else:
            new_total = int(total_quantity)
            item.name = name
            item.description = description
            item.available_quantity = new_total - borrowed_quantity
            item.total_quantity = new_total
            db.session.commit()
            flash('Equipment updated successfully!', category='success')
            return redirect(url_for('equipment.list_equipment'))

    return render_template('equipment/form.html', item=item)


@equipment.route('/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_equipment(item_id):
    item = Equipment.query.get_or_404(item_id)

    active_borrowings = Borrowing.query.filter_by(equipment_id=item.id, status='borrowed').count()
    if active_borrowings > 0:
        flash('Cannot delete equipment with active borrowings.', category='error')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('Equipment deleted.', category='success')

    return redirect(url_for('equipment.list_equipment'))