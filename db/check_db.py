import os
import sqlite3

print("Current working directory:", os.getcwd())
print("Absolute DB path:", os.path.abspath("db\\northwind.db"))
print("Exists:", os.path.exists("db\\northwind.db"))
print("Size:", os.path.getsize("db\\northwind.db"))

conn = sqlite3.connect("db\\northwind.db")
cur = conn.cursor()

cur.execute("PRAGMA database_list;")
print("Database list:", cur.fetchall())

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()

print("Tables:", tables)

conn.close()