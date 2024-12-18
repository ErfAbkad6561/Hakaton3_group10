-- Удаление функции, если она существует
-- DROP FUNCTION public.return_correct_print_simvol(varchar, int4);

CREATE OR REPLACE FUNCTION public.return_correct_print_simvol(str_in character varying, i_kateg integer DEFAULT 0)
 RETURNS character varying
 LANGUAGE plpgsql
AS $function$

DECLARE
    simvol VARCHAR(2);  -- Переменная для текущего символа
    simvol_2 VARCHAR(2);  -- Переменная для заменяемого символа
    simvol_dbl VARCHAR(2);  -- Переменная для задвоенного символа
    -- Массивы для замены символов
    corr_symv_zamena_1 VARCHAR(2)[] := ARRAY['#', '*', '?', '\n'];
    corr_symv_zamena_2 VARCHAR(2)[] := ARRAY['-', 'x', '-', ' '];
    corr_symv_zamena_name_org_1 VARCHAR(1)[] := ARRAY['<', '>'];
    corr_symv_zamena_name_org_2 VARCHAR(1)[] := ARRAY['', ''];
    corr_symv_dubl VARCHAR(1)[] := ARRAY[' ', '*', '(', ')', '{', '}', '[', ']', '#', '№', '+', '-', '/', '\', '!', '@', '#', ',', '%', '^', '"'];
    del_symv_left VARCHAR(1)[] := ARRAY[' ', '*', '(', ')', '{', '}', '[', ']', '#', '№', '+', '-', '/', '\', '!', '@', '#', ',', '%', '^', '"', '?', ',', '.', '*'];
    del_symv_right VARCHAR(1)[] := ARRAY[' ', '*', '(', '{', '[', '#', '№', '+', '-', '/', '\', '!', '@', '#', ',', '%', '^', '"', ',', '.', '*'];
    del_symv_left_adres VARCHAR(1)[] := ARRAY[' ', '.', ','];
    del_symv_right_adres VARCHAR(1)[] := ARRAY[' ', '.', ','];
BEGIN
    -- Проверка на NULL входной строки
    IF str_in IS NULL THEN
        RETURN NULL;
    END IF;

    -- Замена символов
    str_in = REPLACE(str_in, '''', ' ');
    str_in = REPLACE(str_in, '"', ' ');
    str_in = REPLACE(str_in, E'\n', ' ');
    str_in = REPLACE(str_in, CHR(13), '');
    str_in = REPLACE(str_in, CHR(10), '');
    str_in = REGEXP_REPLACE(str_in, E'[^[:alnum:][:space:][:punct:]]', ' ', 'g');
    str_in = REGEXP_REPLACE(str_in, '[^A-Za-zА-Яа-я0-9*(){}\\[\\]#№+-/\\!@#$%^,;.!"]', ' ', 'g');

    -- Удаление задвоенных символов
    FOR i IN 1..ARRAY_LENGTH(corr_symv_dubl, 1) LOOP
        simvol = corr_symv_dubl[i];
        simvol_dbl = simvol || simvol;  -- Создание задвоенного символа
        LOOP
            str_in = REPLACE(str_in, simvol_dbl, simvol);
            EXIT WHEN POSITION(simvol_dbl IN str_in) = 0;  -- Выход из цикла, если задвоенные символы больше не найдены
        END LOOP;
    END LOOP;

    -- Удаление символов слева
    LOOP
        IF LEFT(str_in, 1) IN (SELECT UNNEST(del_symv_left)) THEN
            str_in := RIGHT(str_in, LENGTH(str_in) - 1);  -- Удаление первого символа
        ELSE
            EXIT;
        END IF;
    END LOOP;

    -- Удаление символов справа
    LOOP
        IF RIGHT(str_in, 1) IN (SELECT UNNEST(del_symv_right)) THEN
            str_in := LEFT(str_in, LENGTH(str_in) - 1);  -- Удаление последнего символа
        ELSE
            EXIT;
        END IF;
    END LOOP;

    -- Замены символов
    FOR i IN 1..ARRAY_LENGTH(corr_symv_zamena_1, 1) LOOP
        simvol = corr_symv_zamena_1[i];
        simvol_2 = corr_symv_zamena_2[i];
        str_in = REPLACE(str_in, simvol, simvol_2);
    END LOOP;

    -- Замены для наименования
    IF i_kateg = 1 THEN
        FOR i IN 1..ARRAY_LENGTH(corr_symv_zamena_name_org_1, 1) LOOP
            simvol = corr_symv_zamena_name_org_1[i];
            simvol_2 = corr_symv_zamena_name_org_2[i];
            str_in = REPLACE(str_in, simvol, simvol_2);
        END LOOP;
    END IF;

    -- Удаление задвоенных символов повторно
    FOR i IN 1..ARRAY_LENGTH(corr_symv_dubl, 1) LOOP
        simvol = corr_symv_dubl[i];
        simvol_dbl = simvol || simvol;  -- Создание задвоенного символа
        LOOP
            str_in = REPLACE(str_in, simvol_dbl, simvol);
            EXIT WHEN POSITION(simvol_dbl IN str_in) = 0;  -- Выход из цикла, если задвоенные символы больше не найдены
        END LOOP;
    END LOOP;

    -- Обработка адреса
    IF i_kateg = 2 THEN
        -- Удаление символов слева
        LOOP
            IF LEFT(str_in, 1) IN (SELECT UNNEST(del_symv_left_adres)) THEN
                str_in := RIGHT(str_in, LENGTH(str_in) - 1);  -- Удаление первого символа
            ELSE
                EXIT;
            END IF;
        END LOOP;

        -- Удаление символов справа
        LOOP
            IF RIGHT(str_in, 1) IN (SELECT UNNEST(del_symv_right_adres)) THEN
                str_in := LEFT(str_in, LENGTH(str_in) - 1);  -- Удаление последнего символа
            ELSE
                EXIT;
            END IF;
        END LOOP;
    END IF;

    -- Проверка на пустую строку
    IF str_in IS NULL OR str_in = '' THEN
        str_in = NULL;
    END IF;

    RETURN str_in;  -- Возврат очищенной строки
END; $function$
;