from app import app, db

def init_database():
    # Create tables
    with app.app_context():
        db.create_all()
        print("Tables created.")

if __name__ == "__main__":
    init_database()
