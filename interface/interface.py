from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import psycopg2
import time

# Подключение к базе данных
conn = psycopg2.connect(
    host="194.87.215.7",
    database="hakaton3",
    user="gen_user",
    password="9!pL>B\\jAQF0\\J",
    port='5432'
)

class DatabaseTableEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.conn = conn  # Сохраняем соединение с базой данных
        self.cur = None  # Курсор для выполнения SQL-запросов
        self.id_object_main = 0  # ID выбранного объекта
        self.id_zayavka_main_summarise = 0  # ID заявки на суммаризацию
        self.s_where = ''  # Условия для SQL-запросов
        
        self.initUI()  # Инициализация пользовательского интерфейса
        self.load_initial_data()  # Загрузка начальных данных

    def initUI(self):
        self.setFixedSize(1500, 1060)  # Установка фиксированного размера окна
        self.cur = self.conn.cursor()  # Создание курсора для работы с базой данных
        
        # Основная таблица для отображения объектов
        self.table_object_main = self.create_table_widget(10 + 300, 10, 1500 - 300 - 300 - 10 - 10, 500)
        self.table_object_main.currentCellChanged.connect(self.table_object_main_cell_changed)  # Подключение сигнала изменения ячейки

        # Создание полей для фильтров
        self.create_filter_fields()
        
        # Кнопка для применения фильтров
        self.btn_filtr = self.create_button('Фильтр', 10, 235, self.loadTable_object_main)

        # Создание полей для суммаризации
        self.create_summarization_fields()
        
        # Таблицы для отображения отзывов и рубрик
        self.table_rubrics = self.create_table_widget(10, 10 + 500 + 10, 290, 500)
        self.table_otziv = self.create_table_widget(310, 10 + 500 + 10, 1500 - 310 - 10, 500)

        # Статус bar
        self.status_label = QLabel(self)
        self.setWindowTitle('Отзывы')  # Установка заголовка окна

    def create_table_widget(self, x, y, width, height):
        """Создание виджета таблицы."""
        table = QTableWidget(self)
        table.setGeometry(x, y, width, height)
        return table

    def create_button(self, text, x, y, callback):
        """Создание кнопки."""
        button = QPushButton(text, self)
        button.setGeometry(x, y, 290, 20)
        button.clicked.connect(callback)  # Подключение сигнала нажатия кнопки к функции
        return button

    def create_filter_fields(self):
        """Создание полей для фильтров."""
        self.label_filter = QLabel('Фильтры:', self)
        self.label_filter.setGeometry(10, 10, 290, 20)

        # Поля для ввода фильтров
        self.edit_address = self.create_line_edit(10, 60, 'Адрес (like):')
        self.edit_name_ru = self.create_line_edit(10, 110, 'Наименование (like):')
        self.edit_rubrica = self.create_line_edit(10, 160, 'Рубрика (like):')
        
        # Поля для ввода диапазона рейтинга
        self.label_raiting = QLabel('Средний рейтинг (от - до включительно):', self)
        self.label_raiting.setGeometry(10, 185, 290, 20)
        self.edit_raiting_min = self.create_line_edit(10, 210, '', width=50)
        self.edit_raiting_max = self.create_line_edit(70, 210, '', width=50)
        
        self.set_line_edit_validators()  # Установка валидаторов для полей ввода

    def create_line_edit(self, x, y, label_text, width=290):
        """Создание поля для ввода текста с соответствующей меткой."""
        label = QLabel(label_text, self)
        label.setGeometry(x, y - 25, 290, 20)
        edit = QLineEdit(self)
        edit.setGeometry(x, y, width, 20)
        return edit

    def set_line_edit_validators(self):
        """Установка валидаторов для полей ввода рейтинга."""
        self.edit_raiting_min.setValidator(QDoubleValidator(0, 5, 2, self.edit_raiting_min))
        self.edit_raiting_max.setValidator(QDoubleValidator(0, 5, 2, self.edit_raiting_max))

    def create_summarization_fields(self):
        """Создание полей для суммаризации."""
        self.label_usl_cod_model = QLabel('Модель:', self)
        self.label_usl_cod_model.setGeometry(1200, 10, 140, 20)
        self.label_dolya_usech = QLabel('Сжатие (%):', self)
        self.label_dolya_usech.setGeometry(1350, 10, 140, 20)

        # Комбобокс для выбора модели
        self.combo_box_usl_cod_model = QComboBox(self)
        self.combo_box_usl_cod_model.setGeometry(1200, 35, 140, 20)
        self.combo_box_usl_cod_model.addItems(["gpt", "bert", "rubert"])

        # Поле для ввода доли сжатия
        self.edit_dolya_usech = self.create_line_edit(1350, 35, '', width=140)
        self.edit_dolya_usech.setText('50')  # Установка значения по умолчанию
        self.edit_dolya_usech.setValidator(QIntValidator(0, 100, self.edit_dolya_usech))  # Установка валидатора

        # Кнопка для запуска суммаризации
        self.btn_summarization = self.create_button('Суммаризация', 1200, 60, self.get_summarization_result)

        # Поле для отображения результата суммаризации
        self.edit_summarization_result = QTextEdit(self)
        self.edit_summarization_result.setGeometry(1200, 85, 290, 425)

    def load_initial_data(self):
        """Загрузка начальных данных в таблицы."""
        self.loadTable_object_main()
        self.loadTable_otziv()
        self.loadTable_rubrics()

    def loadTable_object_main(self):
        """Загрузка данных основной таблицы объектов с учетом фильтров."""
        self.loadTable_object_main_where()  # Формирование условий для выборки
        sql = f'''
            SELECT tm.id, tm.address, tm.name_ru, tm.cnt_otziv, tm.rating_average
            FROM object_main tm
            {self.s_where}
            ORDER BY tm.cnt_otziv DESC
            LIMIT 100
        '''
        self.cur.execute(sql)  # Выполнение SQL-запроса
        rows = self.cur.fetchall()  # Получение результатов
        
        # Заполнение таблицы данными
        self.populate_table(self.table_object_main, rows, ['УН', 'Адрес', 'Наименование', 'кол-во отзывов', 'средний балл'])
        
        # Если есть результаты, выбираем первую строку и загружаем отзывы и рубрики
        if self.table_object_main.rowCount() > 0:
            self.table_object_main.setCurrentCell(0, 0)
            self.loadTable_otziv()
            self.loadTable_rubrics()

    def loadTable_object_main_where(self):
        """Формирование условий для SQL-запроса основной таблицы объектов на основе фильтров."""
        conditions = []
        if self.edit_address.text():
            conditions.append(f"tm.address LIKE '%{self.edit_address.text().upper()}%'")
        if self.edit_name_ru.text():
            conditions.append(f"tm.name_ru LIKE '%{self.edit_name_ru.text().upper()}%'")
        if self.edit_rubrica.text():
            conditions.append(f"tm.id IN (SELECT tc.id_object_main FROM rubrics tc LEFT JOIN spr_rubrics tc2 ON tc2.id = tc.id_spr_rubrics WHERE tc2.rubrica LIKE '%{self.edit_rubrica.text().upper()}%')")
        if self.edit_raiting_min.text():
            conditions.append(f"tm.rating_average >= {self.edit_raiting_min.text().replace(',', '.')}")
        if self.edit_raiting_max.text():
            conditions.append(f"tm.rating_average <= {self.edit_raiting_max.text().replace(',', '.')}")

        # Формируем строку условий для SQL-запроса
        self.s_where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''

    def populate_table(self, table, rows, headers):
        """Заполнение таблицы данными."""
        table.setRowCount(len(rows))  # Установка количества строк
        table.setColumnCount(len(headers))  # Установка количества столбцов
        table.setHorizontalHeaderLabels(headers)  # Установка заголовков столбцов
        
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))  # Создание элемента таблицы
                if i == 0 and j == 0:
                    self.id_object_main = int(value)  # Сохранение ID выбранного объекта
                    self.statusBar().showMessage(str(value))  # Обновление статусной строки
                table.setItem(i, j, item)  # Установка элемента в таблицу

        table.resizeRowsToContents()  # Автоматическая подстройка высоты строк
        for j in range(len(headers)):
            table.setColumnWidth(j, [50, 350, 200, 100, 100][j])  # Установка ширины столбцов

    def loadTable_otziv(self):
        """Загрузка отзывов для выбранного объекта."""
        if self.id_object_main == 0:
            return  # Если не выбран объект, выходим из функции
        
        sql = f'''
            SELECT rating, text 
            FROM otziv 
            WHERE id_object_main = {self.id_object_main} 
            ORDER BY rating DESC
        '''
        self.cur.execute(sql)  # Выполнение SQL-запроса
        rows = self.cur.fetchall()  # Получение результатов
        self.populate_table(self.table_otziv, rows, ['УН', 'Отзыв'])  # Заполнение таблицы отзывов

    def loadTable_rubrics(self):
        """Загрузка рубрик для выбранного объекта."""
        if self.id_object_main == 0:
            return  # Если не выбран объект, выходим из функции
        
        sql = f'''
            SELECT rubrica
            FROM rubrics
            LEFT JOIN spr_rubrics ON spr_rubrics.id = rubrics.id_spr_rubrics
            WHERE id_object_main = {self.id_object_main}
            ORDER BY rubrica
        '''
        self.cur.execute(sql)  # Выполнение SQL-запроса
        rows = self.cur.fetchall()  # Получение результатов
        self.populate_table(self.table_rubrics, rows, ['Рубрика'])  # Заполнение таблицы рубрик

    def table_object_main_cell_changed(self, currentRow, currentColumn):
        """Обработчик изменения ячейки в основной таблице объектов."""
        if currentRow is not None:
            self.id_object_main = int(self.table_object_main.item(currentRow, 0).text())  # Получение ID объекта
            self.statusBar().showMessage(str(self.id_object_main))  # Обновление статусной строки
            self.loadTable_otziv()  # Загрузка отзывов для выбранного объекта
            self.loadTable_rubrics()  # Загрузка рубрик для выбранного объекта

    def get_summarization_result(self):
        """Запрос на суммаризацию данных и получение результата."""
        if self.id_object_main == 0:
            return  # Если не выбран объект, выходим из функции

        self.edit_summarization_result.setText('запрос направлен ...')  # Уведомление о начале запроса
        cur = self.conn.cursor()  # Создание курсора для выполнения SQL-запросов

        sdolya_usech = self.edit_dolya_usech.text() or '50'  # Получение значения доли сжатия
        ldolya_usech = int(sdolya_usech)

        # SQL-запрос для вставки заявки на суммаризацию
        sql = f'''
            DO $$
            DECLARE
                id_zayavka_main_summarise_ int;
            BEGIN  
                INSERT INTO zayavka_main_summarise(dt_load, usl_cod_model, dolya_usech)
                VALUES (now(), '{self.combo_box_usl_cod_model.currentText()}', {ldolya_usech})
                RETURNING id INTO id_zayavka_main_summarise_;
                RAISE INFO 'id_zayavka_main_summarise_%', id_zayavka_main_summarise_;
            END; $$
        '''
        
        self.conn.notices = []  # Очистка уведомлений
        cur.execute(sql)  # Выполнение SQL-запроса
        conn.commit()  # Подтверждение транзакции

        # Получение ID заявки из уведомлений
        for notice in conn.notices:
            if 'id_zayavka_main_summarise' in notice:
                self.id_zayavka_main_summarise = int(notice.split()[-1])
                break

        # SQL-запрос для вставки деталей заявки
        sql = f'''
            INSERT INTO zayavka_main_summarise_detal (id_zayavka_main_summarise, id_otziv)
            SELECT {self.id_zayavka_main_summarise}, id
            FROM otziv
            WHERE id_object_main = {self.id_object_main}
        '''
        cur.execute(sql)  # Выполнение SQL-запроса
        conn.commit()  # Подтверждение транзакции

        # Ожидание обобщенного комментария от сервера
        while True:
            time.sleep(1)  # Пауза между запросами
            sql = f'SELECT id FROM zayavka_main_summarise WHERE id = {self.id_zayavka_main_summarise} AND dt_out IS NOT NULL'
            cur.execute(sql)  # Выполнение SQL-запроса
            rows = cur.fetchall()  # Получение результатов
            if rows and rows[0][0] is not None:
                sql = f'SELECT result FROM zayavka_main_summarise_result WHERE id_zayavka_main_summarise = {self.id_zayavka_main_summarise}'
                cur.execute(sql)  # Выполнение SQL-запроса
                result_rows = cur.fetchall()  # Получение результатов
                if result_rows and result_rows[0][0] is not None:
                    self.edit_summarization_result.setText(result_rows[0][0])  # Отображение результата
                cur.execute(f'DELETE FROM zayavka_main_summarise WHERE id = {self.id_zayavka_main_summarise}')  # Удаление заявки
                break  # Выход из цикла

        self.id_zayavka_main_summarise = 0  # Сброс ID заявки
        cur.close()  # Закрытие курсора
        conn.commit()  # Подтверждение транзакции

def main():
    """Основная функция для запуска приложения."""
    app = QApplication([])  # Создание экземпляра приложения
    win = DatabaseTableEditor()  # Создание основного окна
    win.show()  # Отображение окна
    app.exec()  # Запуск основного цикла приложения

if __name__ == '__main__':
    main()  
