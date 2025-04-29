from app import app, db
from app import User, Portfolio  # Import the models

with app.app_context():
    # Drop all tables first to ensure a clean slate
    db.drop_all()
    print("Dropped all existing tables")
    
    # Create all tables
    db.create_all()
    print("Created all tables")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("\nCreated tables:")
    for table in tables:
        print(f"- {table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  - {column['name']}: {column['type']}") 