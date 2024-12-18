import psycopg2

def connect_to_db():
    """Устанавливает соединение с базой данных PostgreSQL."""
    return psycopg2.connect(
        host="194.87.215.7",
        database="hakaton3",
        user="gen_user",
        password="9!pL>B\\jAQF0\\J",
        port='5432'
    )

def extract_data_from_line(sline):
    """Извлекает данные из строки формата TSV, начиная с 'address='."""
    if not sline.startswith('address='):
        print('Ошибка переноса строки:', sline[1:len('address=')])
        return None

    data = {}
    keys = ['address', 'name_ru', 'rating', 'rubrics', 'text']
    
    # Извлекаем каждое поле из строки
    for key in keys:
        prefix = f"{key}="
        start_index = sline.find(prefix)
        if start_index != -1:
            end_index = len(sline)
            # Находим конец текущего поля
            for next_key in keys[keys.index(key) + 1:]:
                next_prefix = f"{next_key}="
                next_index = sline.find(next_prefix)
                if next_index != -1:
                    end_index = next_index
                    break
            data[key] = sline[start_index + len(prefix):end_index - 1]
    
    return data

def sanitize_string(s):
    """Заменяет одинарные кавычки в строке на двойные, чтобы избежать ошибок SQL."""
    return s.replace("'", "''")

def main():
    """Основная функция для обработки данных и вставки их в базу данных."""
    conn = connect_to_db()  # Устанавливаем соединение с базой данных
    cur = conn.cursor()  # Создаем курсор для выполнения SQL-запросов

    sql = ''
    # Открываем файл с данными
    with open('geo-reviews-dataset-2023.tskv', "r", encoding="utf-8") as f:
        for id, sline in enumerate(f, start=1):  # Итерируем по строкам файла
            if id % 1000 == 0:  # Каждые 1000 строк выводим номер строки
                print(id)

            data = extract_data_from_line(sline)  # Извлекаем данные из строки
            if data is None:  # Если произошла ошибка, выходим из цикла
                break

            # Санитизируем входные данные
            sanitized_data = {key: sanitize_string(value) for key, value in data.items()}

            # Формируем SQL-запрос для вставки данных
            s1 = f"""
                INSERT INTO stage_object_otziv(id, address, name_ru, rating, rubrics, text)
                VALUES ({id}, '{sanitized_data.get('address', '')}', '{sanitized_data.get('name_ru', '')}', 
                        '{sanitized_data.get('rating', '')}', '{sanitized_data.get('rubrics', '')}', 
                        '{sanitized_data.get('text', '')}');
            """

            # Проверяем длину запроса и выполняем его, если он слишком длинный
            if len(sql + s1) > 40000:
                cur.execute(sql)  # Выполняем накопленные запросы
                sql = s1  # Начинаем новый запрос
            else:
                sql += s1  # Добавляем запрос к текущему

    if sql:  # Если остались накопленные запросы, выполняем их
        cur.execute(sql)
    
    conn.commit()  # Подтверждаем изменения в базе данных
    
    # Выполняем хранимую процедуру для обработки данных
    cur.execute('SELECT * FROM public.stage_object_otziv_perv_obr()')
    
    conn.close()  # Закрываем соединение с базой данных

if __name__ == "__main__":
    main()  # Запускаем основную функцию