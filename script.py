# script_temporal.py
from core.database import db

with db.get_connection() as conn:
    conn.execute('''
        UPDATE settings 
        SET insta_user = 'ldownloader8@gmail.com',
            insta_pass = '26718867Luis',
            groq_key = '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'
    ''')
    conn.commit()
print("Datos cargados.")