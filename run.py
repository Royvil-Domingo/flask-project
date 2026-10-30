import click
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()


@app.cli.command('seed-admin')
@click.option('--email', prompt=True)
@click.option('--first-name', prompt='First name')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def seed_admin(email, first_name, password):
    """Create an initial administrator account."""
    email = email.strip().lower()
    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f'A user with email {email} already exists.')
        return

    admin = User(email=email, first_name=first_name, role='admin')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f'Admin account created for {email}.')


@app.cli.command('migrate-data')
def migrate_data():
    """One-time data fixup for the borrower workflow. Converts any remaining
    'staff' users to 'borrower', and creates a linked Borrower profile for any
    borrower-role user who doesn't already have one. Safe to run more than once."""
    from app.models.borrower import Borrower

    staff_users = User.query.filter_by(role='staff').all()
    for user in staff_users:
        user.role = 'borrower'
        click.echo(f'Migrated {user.email} from staff to borrower.')

    borrower_role_users = User.query.filter_by(role='borrower').all()
    for user in borrower_role_users:
        if user.borrower_profile is None:
            profile = Borrower(user_id=user.id, name=user.first_name, contact=user.email)
            db.session.add(profile)
            click.echo(
                f'Created a borrower profile for {user.email} '
                f'(contact defaulted to their email — update it from the Borrowers page if you have a real phone number on file).'
            )

    db.session.commit()
    click.echo('Data migration complete.')


if __name__ == '__main__':
    app.run(debug=True)