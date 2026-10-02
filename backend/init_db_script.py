import pymysql
from sqlalchemy.engine import make_url
from app import app, db, ensure_default_templates

def init_database():
    # Connect to MySQL server to create DB if not exists
    try:
        url = make_url(app.config['SQLALCHEMY_DATABASE_URI'])
        conn = pymysql.connect(
            host=url.host,
            user=url.username,
            password=url.password,
            port=url.port or 3306
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{url.database}`")
        cursor.close()
        conn.close()
        print(f"Database '{url.database}' structure ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    # Create tables
    with app.app_context():
        db.create_all()
        ensure_default_templates()
        print("Tables created.")

if __name__ == "__main__":
    init_database()
