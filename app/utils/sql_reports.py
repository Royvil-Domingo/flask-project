"""Hand-written SQL reports.

Each query is plain SQL run through SQLAlchemy's text() with bound
parameters (:today), so user/request data is never concatenated into the
statement. The SQL strings are also shown on the Reports page.
"""
from datetime import date
from sqlalchemy import text, Integer, String, Date
from ..extensions import db

OVERDUE_SQL = """
SELECT b.id         AS borrowing_id,
       e.name       AS equipment,
       br.name      AS borrower,
       br.contact   AS contact,
       b.quantity   AS quantity,
       b.due_on     AS due_on
FROM borrowings AS b
JOIN equipment  AS e  ON e.id  = b.equipment_id
JOIN borrowers  AS br ON br.id = b.borrower_id
WHERE b.status = 'borrowed'
  AND b.due_on < :today
ORDER BY b.due_on ASC, b.id ASC
"""

AVAILABILITY_SQL = """
SELECT e.id                                   AS equipment_id,
       e.name                                 AS equipment,
       e.total_quantity                       AS total_quantity,
       e.available_quantity                   AS available_quantity,
       (e.total_quantity - e.available_quantity) AS borrowed_quantity,
       COALESCE(SUM(CASE WHEN b.status = 'pending' THEN b.quantity ELSE 0 END), 0)
                                              AS pending_quantity
FROM equipment AS e
LEFT JOIN borrowings AS b ON b.equipment_id = e.id
GROUP BY e.id, e.name, e.total_quantity, e.available_quantity
ORDER BY e.name ASC
"""

STATUS_SQL = """
SELECT status                    AS status,
       COUNT(*)                  AS total_records,
       COALESCE(SUM(quantity), 0) AS total_units
FROM borrowings
GROUP BY status
ORDER BY status ASC
"""


def get_overdue_report(today=None):
    today = today or date.today()
    stmt = text(OVERDUE_SQL).columns(
        borrowing_id=Integer, equipment=String, borrower=String,
        contact=String, quantity=Integer, due_on=Date,
    )
    rows = db.session.execute(stmt, {'today': today.isoformat()}).mappings().all()
    report = []
    for row in rows:
        item = dict(row)
        item['days_overdue'] = (today - item['due_on']).days
        report.append(item)
    return report


def get_availability_report():
    stmt = text(AVAILABILITY_SQL).columns(
        equipment_id=Integer, equipment=String, total_quantity=Integer,
        available_quantity=Integer, borrowed_quantity=Integer, pending_quantity=Integer,
    )
    return [dict(r) for r in db.session.execute(stmt).mappings().all()]


def get_status_summary():
    stmt = text(STATUS_SQL).columns(status=String, total_records=Integer, total_units=Integer)
    return [dict(r) for r in db.session.execute(stmt).mappings().all()]