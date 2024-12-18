-- Создание или замена функции для обработки отзывов
CREATE OR REPLACE FUNCTION public.stage_object_otziv_perv_obr()
    RETURNS int
    LANGUAGE plpgsql
    VOLATILE
AS $

DECLARE
    id_ INT;  -- Переменная для хранения идентификатора
    id_max_ INT;  -- Максимальный идентификатор
    id_object_main_ INT;  -- Идентификатор основного объекта
    i_ INT;  -- Индекс для циклов
    rubrics_ VARCHAR(4000);  -- Переменная для хранения рубрик
    s1_ VARCHAR(100);  -- Временная строка для обработки
    arr_rubric_ VARCHAR(100)[] := ARRAY[]::VARCHAR[];  -- Массив для хранения рубрик

BEGIN
    -- Удаление временной таблицы, если она существует
    DROP TABLE IF EXISTS tmp_object_otziv;
    -- Создание временной таблицы для хранения отзывов
    CREATE TABLE tmp_object_otziv (
        id SERIAL4 NOT NULL,
        id_stage_object_otziv INT NOT NULL,
        address VARCHAR(200) NULL,
        name_ru VARCHAR(300) NULL,
        id_object_main INT,
        rating VARCHAR(4) NULL,
        rating_int INT,
        rubrics VARCHAR(4000) NULL,
        id_rubrics INT NULL,
        id_spr_rubrics INT NULL,
        text VARCHAR(21000) NULL,
        id_otziv INT NULL,
        CONSTRAINT tmp_object_otziv_pkey PRIMARY KEY (id)
    );

    -- Удаление временной таблицы для рубрик, если она существует
    DROP TABLE IF EXISTS tmp_rubrics;
    -- Создание временной таблицы для хранения рубрик
    CREATE TABLE tmp_rubrics (
        id SERIAL4 NOT NULL,
        id_object_main INT,
        rubrica VARCHAR(100) NULL,
        id_rubrics INT NULL,
        id_spr_rubrics INT NULL,
        CONSTRAINT tmp_rubrics_pkey PRIMARY KEY (id)
    );

    -- Вставка данных в временную таблицу отзывов
    INSERT INTO tmp_object_otziv (id_stage_object_otziv, address, name_ru, rating, rubrics, text)
    SELECT id, address, name_ru, rating, rubrics, text
    FROM stage_object_otziv;

    -- Обновление адресов: приведение к верхнему регистру и корректировка символов
    UPDATE tmp_object_otziv tu
    SET address = UPPER(return_correct_print_simvol(address, 2));

    -- Установка значения '-' для пустых адресов
    UPDATE tmp_object_otziv tu
    SET address = '-'
    WHERE address IS NULL;

    -- Обновление названий: приведение к верхнему регистру и корректировка символов
    UPDATE tmp_object_otziv tu
    SET name_ru = UPPER(return_correct_print_simvol(name_ru));

    -- Установка значения '-' для пустых названий
    UPDATE tmp_object_otziv tu
    SET name_ru = '-'
    WHERE name_ru IS NULL;

    -- Обновление рубрик: приведение к верхнему регистру и корректировка символов
    UPDATE tmp_object_otziv tu
    SET rubrics = UPPER(return_correct_print_simvol(rubrics));

    -- Корректировка текста: применение функции для корректировки символов
    UPDATE tmp_object_otziv tu
    SET text = return_correct_print_simvol(text);

    -- Установка пустой строки для пустых текстов
    UPDATE tmp_object_otziv tu
    SET text = ''
    WHERE text IS NULL;

    -- Удаление нецифровых символов из рейтинга
    UPDATE tmp_object_otziv tu
    SET rating = REGEXP_REPLACE(rating, '[^0-9]', '', 'g');

    -- Преобразование рейтинга в целое число
    UPDATE tmp_object_otziv tu
    SET rating_int = rating::INT
    WHERE rating <> '';

    -- Обновление идентификатора основного объекта
    UPDATE tmp_object_otziv tu
    SET id_object_main = t_o.id
    FROM object_main t_o
    WHERE t_o.address = tu.address AND 
          t_o.name_ru = tu.name_ru;

    -- Вставка новых объектов в основную таблицу объектов
    INSERT INTO object_main (address, name_ru)
    SELECT DISTINCT address, name_ru
    FROM tmp_object_otziv 
    WHERE id_object_main IS NULL;

    -- Повторное обновление идентификатора основного объекта
    UPDATE tmp_object_otziv tu
    SET id_object_main = t_o.id
    FROM object_main t_o
    WHERE tu.id_object_main IS NULL AND 
          t_o.address = tu.address AND 
          t_o.name_ru = tu.name_ru;

    -- Обработка рубрик
    id_max_ := (SELECT MAX(id) FROM tmp_object_otziv);
    FOR id_ IN 1..id_max_ LOOP
        arr_rubric_ := NULL;  -- Обнуляем массив рубрик
        s1_ = '';  -- Обнуляем временную строку
        
        -- Извлечение идентификатора основного объекта и рубрик
        SELECT id_object_main, rubrics
        INTO id_object_main_, rubrics_
        FROM tmp_object_otziv
        WHERE id = id_;

        -- Разделение рубрик и их добавление в массив
        FOR i_ IN 1..LENGTH(rubrics_) LOOP
            IF SUBSTRING(rubrics_, i_, 1) = ';' OR i_ = LENGTH(rubrics_) THEN
                IF i_ = LENGTH(rubrics_) AND SUBSTRING(rubrics_, i_, 1) <> ';' THEN 
                    s1_ = s1_ || SUBSTRING(rubrics_, i_, 1);
                END IF;
                s1_ = TRIM(s1_);
                IF s1_ <> '' THEN
                    arr_rubric_ := ARRAY_APPEND(arr_rubric_, s1_);
                END IF;
                s1_ = '';  -- Обнуляем временную строку
            ELSE
                s1_ = s1_ || SUBSTRING(rubrics_, i_, 1);  -- Накопление символов
            END IF;
        END LOOP;

        -- Вставка рубрик в временную таблицу
        INSERT INTO tmp_rubrics(id_object_main, rubrica)
        SELECT id_object_main_, t1
        FROM UNNEST(arr_rubric_) t1;

        -- Вывод информации о текущем прогрессе
        IF CEIL(id_ / 10000.0) = id_ / 10000.0 THEN
            RAISE NOTICE 'Обработано % из %', id_, id_max_;
        END IF;
    END LOOP;

    -- Обновление идентификаторов справочных рубрик
    UPDATE tmp_rubrics tu
    SET id_spr_rubrics = spr_rubrics.id
    FROM spr_rubrics
    WHERE spr_rubrics.rubrica = tu.rubrica;

    -- Добавление новых рубрик в справочник
    INSERT INTO spr_rubrics(rubrica)
    SELECT DISTINCT rubrica
    FROM tmp_rubrics
    WHERE id_spr_rubrics IS NULL AND 
          COALESCE(rubrica, '') <> '';

    -- Повторное обновление идентификаторов справочных рубрик
    UPDATE tmp_rubrics tu
    SET id_spr_rubrics = spr_rubrics.id
    FROM spr_rubrics
    WHERE tu.id_spr_rubrics IS NULL AND 
          spr_rubrics.rubrica = tu.rubrica;

    -- Обновление идентификаторов рубрик
    UPDATE tmp_rubrics tu
    SET id_rubrics = rubrics.id
    FROM rubrics
    WHERE rubrics.id_object_main = tu.id_object_main AND 
          rubrics.id_spr_rubrics = tu.id_spr_rubrics;

    -- Добавление новых рубрик в основную таблицу
    INSERT INTO rubrics(id_object_main, id_spr_rubrics)
    SELECT DISTINCT id_object_main, id_spr_rubrics
    FROM tmp_rubrics
    WHERE id_rubrics IS NULL AND 
          id_object_main IS NOT NULL AND 
          id_spr_rubrics IS NOT NULL;

    -- Повторное обновление идентификаторов рубрик
    UPDATE tmp_rubrics tu
    SET id_rubrics = rubrics.id
    FROM rubrics
    WHERE tu.id_rubrics IS NULL AND 
          rubrics.id_object_main = tu.id_object_main AND 
          rubrics.id_spr_rubrics = tu.id_spr_rubrics;

    -- Вставка отзывов в основную таблицу
    INSERT INTO otziv (id_object_main, id_stage_object_otziv, rating, text)
    SELECT id_object_main, id, rating_int, text 
    FROM tmp_object_otziv;

    -- Обновление статистики по отзывам
    UPDATE object_main tu
    SET cnt_otziv = cnt, rating_average = t1.average
    FROM (
        SELECT tc.id_object_main, COUNT(tc.rating) cnt, AVG(tc.rating) average
        FROM otziv tc
        GROUP BY tc.id_object_main
    ) t1
    WHERE tu.id = t1.id_object_main;

    -- Подсчет количества обработанных строк
    id_ = (SELECT COUNT(*) FROM tmp_object_otziv);
    
    -- Удаление временных таблиц
    DROP TABLE IF EXISTS tmp_object_otziv;
    DROP TABLE IF EXISTS tmp_rubrics;

    RETURN id_;  -- Возвращаем количество обработанных строк
END; $$
