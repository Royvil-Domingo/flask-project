-- Equipment Borrowing and Return System: database schema (SQLite)
-- Reference copy of the tables the SQLAlchemy models create.
-- The app builds these tables automatically on startup.

PRAGMA foreign_keys = ON;

-- Accounts. role is 'admin' or 'borrower'.
CREATE TABLE users (
    id            INTEGER      PRIMARY KEY,
    email         VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,   -- hashed, never plain text
    first_name    VARCHAR(150) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'borrower',
    created_at    DATETIME
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE equipment (
    id                 INTEGER      PRIMARY KEY,
    name               VARCHAR(150) NOT NULL,
    description        VARCHAR(500),
    total_quantity     INTEGER      NOT NULL DEFAULT 0,
    available_quantity INTEGER      NOT NULL DEFAULT 0,
    created_at         DATETIME,
    CONSTRAINT chk_total_quantity_non_negative     CHECK (total_quantity >= 0),
    CONSTRAINT chk_available_quantity_non_negative CHECK (available_quantity >= 0),
    CONSTRAINT chk_available_lte_total             CHECK (available_quantity <= total_quantity)
);
CREATE INDEX ix_equipment_name ON equipment (name);

-- Borrower profile. user_id links to the login account; it is NULL for
-- borrowers an admin added by hand who have no account.
CREATE TABLE borrowers (
    id         INTEGER      PRIMARY KEY,
    user_id    INTEGER      UNIQUE,
    name       VARCHAR(150) NOT NULL,
    contact    VARCHAR(150) NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
CREATE INDEX ix_borrowers_name ON borrowers (name);

-- status: 'pending' -> 'borrowed' -> 'returned', or 'pending' -> 'rejected'.
-- "Overdue" is not stored; it is borrowed AND due_on < today.
CREATE TABLE borrowings (
    id               INTEGER     PRIMARY KEY,
    equipment_id     INTEGER     NOT NULL,
    borrower_id      INTEGER     NOT NULL,
    processed_by_id  INTEGER,                      -- admin who approved/rejected
    quantity         INTEGER     NOT NULL,
    requested_on     DATE        NOT NULL,
    borrowed_on      DATE,                         -- issue date, set on approval
    due_on           DATE        NOT NULL,
    returned_on      DATE,
    status           VARCHAR(20) NOT NULL DEFAULT 'pending',
    rejection_reason VARCHAR(255),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    FOREIGN KEY (equipment_id)    REFERENCES equipment (id),
    FOREIGN KEY (borrower_id)     REFERENCES borrowers (id),
    FOREIGN KEY (processed_by_id) REFERENCES users (id)
);

-- ---------------------------------------------------------------
-- Example queries (SQLite shell)
-- ---------------------------------------------------------------

-- Overdue items
SELECT b.id, e.name AS equipment, br.name AS borrower, b.quantity, b.due_on
FROM borrowings b
JOIN equipment e  ON e.id  = b.equipment_id
JOIN borrowers br ON br.id = b.borrower_id
WHERE b.status = 'borrowed' AND b.due_on < date('now')
ORDER BY b.due_on;

-- Available vs borrowed quantities
SELECT name, total_quantity, available_quantity,
       total_quantity - available_quantity AS borrowed_quantity
FROM equipment;