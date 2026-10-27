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


if __name__ == '__main__':
    app.run(debug=True)