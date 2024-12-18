import time
import psycopg2
import nltk
from summarizer import Summarizer
from transformers import AutoModel, AutoTokenizer, AutoConfig
import eda
import re

# Глобальный флаг для загрузки пакетов NLTK
punkt_downloaded = False

def is_integer(value):
    if value is None:
        return False
    pattern = r'^-?\d+$'
    return bool(re.match(pattern, value))

def run_process():
    conn = psycopg2.connect(
        host="194.87.215.7",
        database="hakaton3",
        user="gen_user",
        password="9!pL>B\\jAQF0\\J",
        port='5432'
    )
    
    cur = conn.cursor()
    sql = '''
        DO $ 
        DECLARE 
            id_ INT;
            usl_cod_model_ VARCHAR(10);
            dolya_usech_ INT;
            id_object_main_ INT;
        BEGIN
            id_ = 0;
            usl_cod_model_ = '';
            dolya_usech_ = 0;
            id_object_main_ = 0;
            
            SELECT id, usl_cod_model, dolya_usech, id_object_main
            INTO id_, usl_cod_model_, dolya_usech_, id_object_main_
            FROM zayavka_main_summarise 
            WHERE dt_run IS NULL AND dt_out IS NULL 
            ORDER BY CASE WHEN id_object_main IS NULL THEN 0 ELSE 1 END ASC
            LIMIT 1; 
            
            UPDATE zayavka_main_summarise SET dt_run = NOW() WHERE id = id_;
            
            RAISE INFO 'id_zayavka_main_summarise_%', id_;
            RAISE INFO 'usl_cod_model_%', usl_cod_model_;
            RAISE INFO 'dolya_usech_%', dolya_usech_;
            RAISE INFO 'id_object_main_%', id_object_main_;
        END; 
        $ 
    '''
    
    conn.notices = []
    cur.execute(sql)
    conn.commit()
    
    # Инициализация переменных
    id_zayavka_main_summarise = 0
    id_object_main = 0
    usl_cod_model = ''
    dolya_usech = 0

    # Обработка уведомлений
    for notice in conn.notices:
        if 'id_zayavka_main_summarise' in notice:
            id_zayavka_main_summarise = extract_integer(notice, 'id_zayavka_main_summarise')
        if 'usl_cod_model' in notice:
            usl_cod_model = extract_value(notice, 'usl_cod_model')
        if 'dolya_usech' in notice:
            dolya_usech = extract_integer(notice, 'dolya_usech')
        if 'id_object_main' in notice:
            id_object_main = extract_integer(notice, 'id_object_main')

    if id_zayavka_main_summarise == 0:
        cur.close()
        conn.close()
        return

    # Инициализация текстов
    text_otl, text_neitral, text_bad = [], [], []
    text_otl_in, text_neitral_in, text_bad_in = '', '', ''
    
    # Получение отзывов
    if id_object_main != 0:  # тестовый режим
        sql = f'SELECT rating, text FROM otziv WHERE id_object_main = {id_object_main};'
    else:
        sql = f'''
            SELECT rating, text
            FROM zayavka_main_summarise_detal t1
            LEFT JOIN otziv t2 ON t2.id = t1.id_otziv
            WHERE t1.id_zayavka_main_summarise = {id_zayavka_main_summarise};
        '''
    
    cur.execute(sql)
    rows = cur.fetchall()
    
    # Обработка отзывов
    for row in rows:
        rating = row[0]
        text = row[1]
        if rating == 5:
            text_otl.append(text)
        elif rating == 4:
            text_neitral.append(text)
        else:
            text_bad.append(text)

    # Формирование входных текстов
    text_otl_in = '\n'.join(text_otl) if text_otl else 'отсутствуют'
    text_neitral_in = '\n'.join(text_neitral) if text_neitral else 'отсутствуют'
    text_bad_in = '\n'.join(text_bad) if text_bad else 'отсутствуют'

    # Расчет метрик
    metrika_otl, metrika_otl_detal = calculate_metrics(text_otl_in, usl_cod_model, dolya_usech)
    metrika_neitral, metrika_neitral_detal = calculate_metrics(text_neitral_in, usl_cod_model, dolya_usech)
    metrika_bad, metrika_bad_detal = calculate_metrics(text_bad_in, usl_cod_model, dolya_usech)

    # Экранирование текста
    text_otl_in, text_neitral_in, text_bad_in = map(escape_single_quotes, [text_otl_in, text_neitral_in, text_bad_in])
    metrika_otl_detal, metrika_neitral_detal, metrika_bad_detal = map(escape_single_quotes, [metrika_otl_detal, metrika_neitral_detal, metrika_bad_detal])

    # SQL для вставки/обновления
    if id_object_main != 0:  # тестовый режим
        sql = f'''
            DO $ 
            BEGIN
                INSERT INTO zayavka_main_summarise_test 
                    (id_object_main, usl_cod_model, dolya_usech, text_otl_in, text_neitral_in, text_bad_in,
                     text_otl_out, text_neitral_out, text_bad_out, b_calc_metrika,
                     metrika_otl_detal, metrika_otl, metrika_neitral_detal, metrika_neitral,
                     metrika_bad_detal, metrika_bad)
                VALUES ({id_object_main}, '{usl_cod_model}', {dolya_usech},
                        '{text_otl_in}', '{text_neitral_in}', '{text_bad_in}',
                        '{text_otl_out}', '{text_neitral_out}', '{text_bad_out}',
                        TRUE, '{metrika_otl_detal}', {metrika_otl},
                        '{metrika_neitral_detal}', {metrika_neitral},
                        '{metrika_bad_detal}', {metrika_bad});
                DELETE FROM zayavka_main_summarise WHERE id = {id_zayavka_main_summarise};
            END; 
            $ 
        '''
    else:        
        s_out = f'''Статистика по отзывам: 
   - положительные (5): {len(text_otl)} 
   - нейтральные (4, не указан): {len(text_neitral)} 
   - отрицательные (1, 2, 3): {len(text_bad)} 

Положительные (метрика {metrika_otl}):
{text_otl_out}

Нейтральные (метрика {metrika_neitral}):
{text_neitral_out}

Отрицательные (метрика {metrika_bad}):
{text_bad_out}'''
    
        sql = f'''
            INSERT INTO zayavka_main_summarise_result (id_zayavka_main_summarise, result)
            VALUES ({id_zayavka_main_summarise}, '{s_out}');
            UPDATE zayavka_main_summarise SET dt_out = NOW() WHERE id = {id_zayavka_main_summarise}; 
        '''
    
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def extract_integer(notice, key):
    value = notice[notice.find(key) + len(key) + 1:].strip()
    return int(value) if is_integer(value) else 0

def extract_value(notice, key):
    return notice[notice.find(key) + len(key) + 1:].strip()

def escape_single_quotes(text):
    return text.replace("'", "''")

def calculate_metrics(text_in, usl_cod_model, dolya_usech):
    if text_in != 'отсутствуют':
        text_out = get_summ_text(usl_cod_model, dolya_usech, text_in)
        return eda.text_sopost(text_in, text_out)
    return 0, ''

def get_summ_text(usl_cod_model, dolya_usech, text_in):
    if len(text_in) > 1000000:
        return f'На вход подана строка {len(text_in)} символов. Ограничение модели - 1 млн. символов.'
    
    global punkt_downloaded
    if not punkt_downloaded:
        nltk.download('punkt')
        punkt_downloaded = True
        
    n = int(len(nltk.sent_tokenize(text_in)))
    size1 = int(round(n * (float(dolya_usech) / 100)) + 1)
    size = int((n - size1) + 1)
    
    model_map = {
        'gpt': 'sberbank-ai/rugpt3small_based_on_gpt2',
        'bert': 'bert-base-multilingual-cased',
        'rubert': 'DeepPavlov/rubert-base-cased'
    }
    
    name_model = model_map.get(usl_cod_model, 'gpt')  # По умолчанию 'gpt'
    
    config = AutoConfig.from_pretrained(name_model, output_hidden_states=True)
    custom_tokenizer = AutoTokenizer.from_pretrained(name_model)
    custom_model = AutoModel.from_pretrained(name_model, config=config)
    model = Summarizer(custom_model=custom_model, custom_tokenizer=custom_tokenizer)
    
    result = model(body=text_in, num_sentences=size)
    return ''.join(result)

def main():    
    while True:
        run_process()
        time.sleep(1)

if __name__ == "__main__":
    main()
