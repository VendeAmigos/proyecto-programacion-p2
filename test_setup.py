#!/usr/bin/env python3
# test_setup.py - Test database initialization

import sys
sys.path.insert(0, '/c/Users/angel/OneDrive/Escritorio/practica1')

from tienda_db import BaseDatosTienda

print("=" * 60)
print("Testing Database Setup")
print("=" * 60)

try:
    # Initialize database
    db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")
    print("✓ Database connection established")
    
    # Create admin user
    db.semilla_admin()
    print("✓ Admin user created/verified")
    
    # Load products
    db.semilla_productos()
    print("✓ Products loaded")
    
    # Test data retrieval
    productos = db.listar_productos()
    print(f"✓ Found {len(productos)} products")
    
    for p in productos:
        print(f"  - {p['nombre']}: ${p['precio']}")
    
    # Test admin user
    admin = db.obtener_usuario_por_email("admin@smartwatches.com")
    if admin:
        print(f"✓ Admin user verified: {admin['nombre']} ({admin['rol']})")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nThe application is ready to run.")
    print("Admin credentials:")
    print("  Email: admin@smartwatches.com")
    print("  Password: admin123")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
