import os
import sqlite3

def fix_all():
    targets = ['.html', '.py', '.css']
    replacements = {
        'ó': 'ó',
        'á': 'á',
        'é': 'é',
        'Ã\xad': 'í',  # í
        'ú': 'ú',
        'ñ': 'ñ',
        'Ñ': 'Ñ',
        '¿': '¿'
    }
    
    replaced_list = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if any(file.endswith(ext) for ext in targets):
                filepath = os.path.join(root, file)
                if 'venv' in filepath or '__pycache__' in filepath:
                    continue
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    new_content = content
                    for bad, good in replacements.items():
                        if bad in new_content:
                            new_content = new_content.replace(bad, good)
                            if f"{bad} -> {good}" not in replaced_list:
                                replaced_list.append(f"{bad} -> {good}")
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                except Exception as e:
                    pass

    return replaced_list

replaced = fix_all()
print('REPLACED_STRINGS:', replaced)

conn = sqlite3.connect('tienda.sqlite3')
cur = conn.cursor()
cur.execute('SELECT es_admin FROM usuarios WHERE username="admin"')
res = cur.fetchone()
if res:
    cur.execute('UPDATE usuarios SET es_admin=1 WHERE username="admin"')
    conn.commit()
    print('DB_UPDATE: User admin es_admin updated to 1')
else:
    # Need to create (assuming default hash or something if it doesnt exist, but we checked and it exists)
    print('DB_UPDATE: User admin not found')
conn.close()
