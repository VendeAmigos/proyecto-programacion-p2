import os
import sqlite3

# 1. Rename files
img_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
for filename in os.listdir(img_dir):
    if ' ' in filename:
        new_filename = filename.replace(' ', '_')
        old_path = os.path.join(img_dir, filename)
        new_path = os.path.join(img_dir, new_filename)
        os.rename(old_path, new_path)
        print(f"Renamed: '{filename}' to '{new_filename}'")

# 2. Update Database
db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
con = sqlite3.connect(db_path)
cur = con.cursor()

# Get all products
cur.execute("SELECT id, imagen FROM productos")
productos = cur.fetchall()

for prod_id, imagen in productos:
    if imagen and ' ' in imagen:
        nueva_imagen = imagen.replace(' ', '_')
        cur.execute("UPDATE productos SET imagen = ? WHERE id = ?", (nueva_imagen, prod_id))
        print(f"Updated DB para ID {prod_id}: {nueva_imagen}")

con.commit()
con.close()
