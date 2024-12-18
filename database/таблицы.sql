-- Удаление таблицы stage_object_otziv, если она существует
-- DROP TABLE IF EXISTS stage_object_otziv;

-- Создание таблицы для хранения этапов объектов с отзывами
CREATE TABLE stage_object_otziv (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    address VARCHAR(200),  -- Адрес объекта
    name_ru VARCHAR(300),  -- Наименование на русском языке
    rating VARCHAR(150),  -- Рейтинг объекта
    rubrics VARCHAR(4000),  -- Рубрики, к которым относится объект
    text VARCHAR(21000),  -- Текст отзыва

    CONSTRAINT stage_object_otziv_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Удаление таблицы object_main, если она существует
-- DROP TABLE IF EXISTS object_main;

-- Создание основной таблицы объектов (адрес + наименование)
CREATE TABLE object_main (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    address VARCHAR(200),  -- Адрес объекта
    name_ru VARCHAR(300),  -- Наименование на русском языке
    cnt_otziv INT,  -- Количество отзывов
    rating_average NUMERIC(5, 2),  -- Средний рейтинг

    CONSTRAINT object_main_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Удаление таблицы spr_rubrics, если она существует
-- DROP TABLE IF EXISTS spr_rubrics;

-- Создание справочника рубрик
CREATE TABLE spr_rubrics (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    rubrica VARCHAR(100),  -- Наименование рубрики

    CONSTRAINT spr_rubrics_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Удаление таблицы rubrics, если она существует
-- DROP TABLE IF EXISTS rubrics;

-- Создание таблицы для хранения рубрик объектов
CREATE TABLE rubrics (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    id_object_main INT NULL,  -- Идентификатор основного объекта
    id_spr_rubrics INT,  -- Идентификатор справочной рубрики

    CONSTRAINT rubrics_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Установка внешнего ключа для связи с основной таблицей объектов
ALTER TABLE public.rubrics 
ADD CONSTRAINT rubrics_id_object_main FOREIGN KEY (id_object_main) 
REFERENCES public.object_main(id) ON DELETE CASCADE;

-- Создание индекса для повышения производительности запросов по id_object_main
CREATE INDEX idx_rubrics_id_object_main ON rubrics (id_object_main);

-- Удаление таблицы otziv, если она существует
-- DROP TABLE IF EXISTS otziv;

-- Создание таблицы для хранения отзывов
CREATE TABLE otziv (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    id_object_main INT,  -- Идентификатор основного объекта
    id_stage_object_otziv INT,  -- Идентификатор этапа объекта с отзывом
    rating INT,  -- Рейтинг отзыва
    text VARCHAR(21000),  -- Текст отзыва

    CONSTRAINT otziv_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Установка внешнего ключа для связи с основной таблицей объектов
ALTER TABLE public.otziv 
ADD CONSTRAINT otziv_id_object_main FOREIGN KEY (id_object_main) 
REFERENCES public.object_main(id) ON DELETE CASCADE;

-- Создание индекса для повышения производительности запросов по id_object_main
CREATE INDEX idx_otziv_id_object_main ON otziv (id_object_main);

-- Удаление таблицы zayavka_main_summarise, если она существует
-- DROP TABLE IF EXISTS zayavka_main_summarise;

-- Создание таблицы для суммаризации заявок
CREATE TABLE zayavka_main_summarise (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    usl_cod_model VARCHAR(10),  -- Код модели услуги
    dolya_usech INT,  -- Доля усечений
    dt_load TIMESTAMP,  -- Дата загрузки
    dt_run TIMESTAMP,  -- Дата выполнения
    dt_out TIMESTAMP,  -- Дата выхода
    id_object_main INT,  -- Идентификатор основного объекта

    CONSTRAINT zayavka_main_summarise_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Удаление таблицы zayavka_main_summarise_detal, если она существует
-- DROP TABLE IF EXISTS zayavka_main_summarise_detal;

-- Создание таблицы для детализации суммаризации заявок
CREATE TABLE zayavka_main_summarise_detal (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    id_zayavka_main_summarise INT,  -- Идентификатор суммаризации заявки
    id_otziv INT,  -- Идентификатор отзыва

    CONSTRAINT zayavka_main_summarise_detal_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Установка внешнего ключа для связи с таблицей суммаризации заявок
ALTER TABLE public.zayavka_main_summarise_detal 
ADD CONSTRAINT zayavka_main_summarise_detal_id_zayavka_main_summarise FOREIGN KEY (id_zayavka_main_summarise) 
REFERENCES public.zayavka_main_summarise(id) ON DELETE CASCADE;

-- Создание индекса для повышения производительности запросов по id_zayavka_main_summarise
CREATE INDEX idx_zayavka_main_summarise_detal_id_zayavka_main_summarise ON zayavka_main_summarise_detal (id_zayavka_main_summarise);

-- Удаление таблицы zayavka_main_summarise_result, если она существует
-- DROP TABLE IF EXISTS zayavka_main_summarise_result;

-- Создание таблицы для хранения результатов суммаризации заявок
CREATE TABLE zayavka_main_summarise_result (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    id_zayavka_main_summarise INT,  -- Идентификатор суммаризации заявки
    result TEXT,  -- Результат суммаризации

    CONSTRAINT zayavka_main_summarise_result_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);

-- Установка внешнего ключа для связи с таблицей суммаризации заявок
ALTER TABLE public.zayavka_main_summarise_result 
ADD CONSTRAINT zayavka_main_summarise_result_id_zayavka_main_summarise FOREIGN KEY (id_zayavka_main_summarise) 
REFERENCES public.zayavka_main_summarise(id) ON DELETE CASCADE;

-- Создание индекса для повышения производительности запросов по id_zayavka_main_summarise
CREATE INDEX idx_zayavka_main_summarise_result_id_zayavka_main_summarise ON zayavka_main_summarise_result (id_zayavka_main_summarise);

-- Удаление таблицы zayavka_main_summarise_test, если она существует
-- DROP TABLE IF EXISTS zayavka_main_summarise_test;

-- Создание таблицы для тестирования суммаризации заявок
CREATE TABLE zayavka_main_summarise_test (
    id SERIAL NOT NULL,  -- Уникальный идентификатор
    id_object_main INT,  -- Идентификатор основного объекта
    usl_cod_model VARCHAR(10),  -- Код модели услуги
    dolya_usech INT,  -- Доля усечений
    text_otl_in TEXT,  -- Текст положительного отзыва (вход)
    text_neitral_in TEXT,  -- Текст нейтрального отзыва (вход)
    text_bad_in TEXT,  -- Текст отрицательного отзыва (вход)
    text_otl_out TEXT,  -- Текст положительного отзыва (выход)
    text_neitral_out TEXT,  -- Текст нейтрального отзыва (выход)
    text_bad_out TEXT,  -- Текст отрицательного отзыва (выход)
    b_calc_metrika BOOL,  -- Флаг расчета метрики
    metrika_otl_detal TEXT,  -- Детали метрики положительного отзыва
    metrika_otl NUMERIC(5, 2),  -- Метрика положительного отзыва
    metrika_neitral_detal TEXT,  -- Детали метрики нейтрального отзыва
    metrika_neitral NUMERIC(5, 2),  -- Метрика нейтрального отзыва
    metrika_bad_detal TEXT,  -- Детали метрики отрицательного отзыва
    metrika_bad NUMERIC(5, 2),  -- Метрика отрицательного отзыва

    CONSTRAINT zayavka_main_summarise_test_pkey PRIMARY KEY (id)  -- Установка первичного ключа
);