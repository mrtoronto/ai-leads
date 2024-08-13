from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.get(1)
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {user.username} (ID: 1) has been granted admin permissions.")
    else:
        print("User with ID 1 not found.")