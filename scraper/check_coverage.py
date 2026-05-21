import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT u.source_key, COUNT(c.id) FROM universities u LEFT JOIN courses c ON c.university_id=u.id GROUP BY u.source_key ORDER BY COUNT(c.id) DESC')
targets = {'nptel':3200,'mit_ocw':2573,'harvard':142,'berkeley':300,'stanford':130,'oxford':100,'cambridge':60,'gatech':80,'cmu':60,'princeton':50,'yale':42}
print(f'{"Source":<15} {"DB":>6} {"Target":>8} {"Pct":>7}')
print('-'*40)
for r in cur.fetchall():
    sk = r[0]; cnt = r[1]
    if sk in targets:
        pct = cnt/targets[sk]*100
        flag = " OK" if pct >= 90 else " NEED"
        print(f'{sk:<15} {cnt:>6} {targets[sk]:>8} {pct:>6.1f}%{flag}')
conn.close()
