import time
import psycopg2
import eda  # для расчёта метрик EDA

def run_process(conn):
    cur = conn.cursor()
    sql = '''
        SELECT id, 
               text_otl_in, text_neitral_in, text_bad_in, 
               text_otl_out, text_neitral_out, text_bad_out
        FROM zayavka_main_summarise_test
        WHERE b_calc_metrika IS NULL
        LIMIT 1;
    '''
    cur.execute(sql)
    rows = cur.fetchall()

    # Если записей нет - выходим
    if not rows:
        cur.close()
        conn.close()
        return 0

    # Извлечение данных из первой строки
    id_zayavka_main_summarise_test = rows[0][0]
    texts_in = rows[0][1:4]  # text_otl_in, text_neitral_in, text_bad_in
    texts_out = rows[0][4:7]  # text_otl_out, text_neitral_out, text_bad_out

    metrics = {}
    for text_in, text_out, key in zip(texts_in, texts_out, ['metrika_otl', 'metrika_neitral', 'metrika_bad']):
        if text_in != 'отсутствуют' and text_out:
            metrics[key], metrics[f'{key}_detal'] = eda.text_sopost(text_in, text_out)
        else:
            metrics[key] = -1
            metrics[f'{key}_detal'] = ''

    # Формирование SQL для обновления
    sql_update = f'''
        UPDATE zayavka_main_summarise_test
        SET b_calc_metrika = true,
            metrika_otl = CASE WHEN {metrics['metrika_otl']} = -1 THEN NULL ELSE {metrics['metrika_otl']} END,
            metrika_otl_detal = '{metrics['metrika_otl_detal']}',
            metrika_neitral = CASE WHEN {metrics['metrika_neitral']} = -1 THEN NULL ELSE {metrics['metrika_neitral']} END,
            metrika_neitral_detal = '{metrics['metrika_neitral_detal']}',
            metrika_bad = CASE WHEN {metrics['metrika_bad']} = -1 THEN NULL ELSE {metrics['metrika_bad']} END,
            metrika_bad_detal = '{metrics['metrika_bad_detal']}'
        WHERE id = {id_zayavka_main_summarise_test}
    '''
    cur.execute(sql_update)
    conn.commit()
    
    return 1

def main():
    conn = psycopg2.connect(
        host="194.87.215.7",
        database="hakaton3",
        user="gen_user",
        password="9!pL>B\\jAQF0\\J",
        port='5432'
    )
    
    while run_process(conn) == 1:
        pass
    
    conn.close()
    time.sleep(60)

if __name__ == "__main__":
    main()
