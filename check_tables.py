
from app.database import engine, Base
import app.models

print("Registered tables:")
print(list(Base.metadata.tables.keys()))

try:
    Base.metadata.create_all(bind=engine)
    print("\nTables created or already exist!")
except Exception as e:
    print("\nDatabase error:", e)
