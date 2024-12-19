from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, 
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QCursor
from PyQt5.QtCore import Qt
import psycopg2
import time

# Параметры подключения к базе данных
DB_CONFIG = {
    "host": "194.87.215.7",
    "database": "hakaton3",
    "user": "gen_user",
    "password": "9!pL>B\\jAQF0\\J",
    "port": "5432"
}

# Устанавливаем подключение к базе данных
conn = psycopg2.connect(**DB_CONFIG)

class DatabaseTableEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conn = conn
        self.cur = self.conn.cursor()  # Создаем курсор для выполнения запросов
        self.id_object_main = 0  # Идентификатор текущего объекта
        self.id_zayavka_main_summarise = 0  # Идентификатор заявки для суммаризации
        self.s_where = ''  # Условие фильтрации для основного запроса
        self.initUI()
        self.load_initial_data()

    def initUI(self):
        # Или просто используйте resize() для установки начального размера
        self.resize(1500, 950)  # Начальный размер окна
        self.setWindowTitle('Отзывы')

        # Создаем виджет таблицы для отображения объектов
        self.table_object_main = self.create_table_widget(320, 10, 870, 500)
        self.table_object_main.currentCellChanged.connect(self.table_object_main_cell_changed)

        self.create_filter_fields()  # Создаем элементы фильтров
        self.btn_filtr = self.create_button('Фильтр', 10, 235, self.loadTable_object_main)
        self.btn_filtr.setCursor(QCursor(Qt.PointingHandCursor))  # Установить курсор для кнопки

        self.create_summarization_fields()  # Создаем элементы интерфейса для суммаризации
        self.table_rubrics = self.create_table_widget(10, 520, 290, 500)  # Таблица рубрик
        self.table_otziv = self.create_table_widget(310, 520, 870, 500)  # Таблица отзывов

        self.status_label = QLabel(self)  # Метка для отображения статуса

    def create_table_widget(self, x, y, width, height):
        """
        Создает таблицу для отображения данных.
        """
        table = QTableWidget(self)
        table.setGeometry(x, y, width, height)
        return table

    def create_button(self, text, x, y, callback):
        """
        Создает кнопку с заданным текстом, координатами и обработчиком событий.
        """
        button = QPushButton(text, self)
        button.setGeometry(x, y, 290, 20)
        button.clicked.connect(callback)
        return button

    def create_filter_fields(self):
        """
        Создает элементы интерфейса для фильтрации данных.
        """
        self.label_filter = QLabel('Фильтры:', self)
        self.label_filter.setGeometry(10, 10, 290, 20)

        self.edit_address = self.create_line_edit(10, 60, 'Адрес (like):')  # Поле для ввода адреса
        self.edit_name_ru = self.create_line_edit(10, 110, 'Наименование (like):')  # Поле для ввода наименования
        self.edit_rubrica = self.create_line_edit(10, 160, 'Рубрика (like):')  # Поле для ввода рубрики

        self.label_raiting = QLabel('Средний рейтинг (от - до включительно):', self)
        self.label_raiting.setGeometry(10, 185, 290, 20)
        self.edit_raiting_min = self.create_line_edit(10, 210, '', width=50)  # Минимальный рейтинг
        self.edit_raiting_max = self.create_line_edit(70, 210, '', width=50)  # Максимальный рейтинг

        self.set_line_edit_validators()  # Устанавливаем валидаторы для ввода чисел

        # Установка стилей для текстовых полей
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;                /* Светлая рамка */
                border-radius: 5px;                    /* Округленные углы */
                padding: 5px;                           /* Отступ внутри поля */
                font-size: 12px;                        /* Размер шрифта */
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;              /* Цвет рамки при фокусе */
                background-color: #f9f9f9;              /* Фоновый цвет при фокусе */
            }
            QLabel {
                margin-bottom: 5px;                     /* Отступ снизу */
            }
        """)  # Установка стилей

    def create_line_edit(self, x, y, label_text, width=290):
        """
        Создает текстовое поле с меткой.
        """
        label = QLabel(label_text, self)
        label.setGeometry(x, y - 25, 290, 20)
        edit = QLineEdit(self)
        edit.setGeometry(x, y, width, 20)
        return edit

    def set_line_edit_validators(self):
        """
        Устанавливает ограничения на ввод для полей рейтинга.
        """
        validator = QDoubleValidator(0, 5, 2)  # Валидатор для вещественных чисел
        self.edit_raiting_min.setValidator(validator)
        self.edit_raiting_max.setValidator(validator)

    def create_summarization_fields(self):
        """
        Создает элементы интерфейса для выполнения суммаризации.
        """
        self.label_usl_cod_model = QLabel('Модель:', self)
        self.label_usl_cod_model.setGeometry(1200, 15, 140, 20)
        self.label_dolya_usech = QLabel('Сжатие (%):', self)
        self.label_dolya_usech.setGeometry(1350, 15, 140, 20)

        self.combo_box_usl_cod_model = QComboBox(self)  # Выпадающий список выбора модели
        self.combo_box_usl_cod_model.setGeometry(1200, 35, 140, 20)
        self.combo_box_usl_cod_model.addItems(["gpt", "bert", "rubert"])

        self.edit_dolya_usech = self.create_line_edit(1350, 35, '', width=140)  # Поле для ввода процента сжатия
        self.edit_dolya_usech.setText('50')  # Значение по умолчанию
        self.edit_dolya_usech.setValidator(QIntValidator(0, 100))  # Валидатор для целых чисел

        self.btn_summarization = self.create_button('Суммаризация', 1200, 60, self.get_summarization_result)
        self.btn_summarization.setCursor(QCursor(Qt.PointingHandCursor))  # Установить курсор для кнопки

        self.edit_summarization_result = QTextEdit(self)  # Поле для вывода результата суммаризации
        self.edit_summarization_result.setGeometry(1200, 85, 290, 425)

        # Устанавливаем стили для QTextEdit
        self.edit_summarization_result.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ccc;                /* Светлая рамка */
                border-radius: 10px;                   /* Округленные углы */
                padding: 0px;                          /* Отступ внутри поля */
                font-size: 12px;                       /* Размер шрифта */
                background-color: #f9f9f9;             /* Светлый фон */
            }
            QTextEdit:focus {
                border: 2px solid #4CAF50;              /* Цвет рамки при фокусе */
            }
        """)

        # Установка стилей для остальных полей
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;                /* Светлая рамка */
                border-radius: 5px;                    /* Округленные углы */
                padding: 1px;                           /* Отступ внутри поля */
                font-size: 12px;                        /* Размер шрифта */
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;              /* Цвет рамки при фокусе */
                background-color: #f9f9f9;              /* Фоновый цвет при фокусе */
            }
            QLabel {
                margin-bottom: 5px;                     /* Отступ снизу */
            }
            QComboBox {
                border: 2px solid #ccc;                 /* Светлая рамка для комбобокса */
                border-radius: 5px;                     /* Округленные углы */
                padding: 0px 5px;                       /* Отступ внутри */
                font-size: 12px;                        /* Размер шрифта */
            }
            QComboBox:focus {
                border: 2px solid #4CAF50;              /* Цвет рамки при фокусе */
            }
            QPushButton { /* Стили для кнопки */
            background-color: white; /* Зеленый цвет фона */
            color: black;              /* Белый цвет текста */
            border: 2px solid #ccc;     /* Светлая рамка */
            border-radius: 5px;         /* Округленные углы */
            padding: -5px 10px;         /* Отступы внутри кнопки */
            font-size: 12px;            /* Размер шрифта */
            font-weight: none;          /* Жирный шрифт */
            }
            QPushButton:hover { /* Стили при наведении курсора */
                background-color: #45a049; /* Темнее зеленый цвет при наведении */
            }
            QPushButton:pressed { /* Стили при нажатии */
                background-color: #3e8e41; /* Еще темнее зеленый цвет при нажатии */
            }
        """)  # Установка стилей

    def load_initial_data(self):
        """
        Загружает начальные данные в таблицы.
        """
        self.loadTable_object_main()  # Основная таблица
        self.loadTable_otziv()  # Отзывы
        self.loadTable_rubrics()  # Рубрики

    def loadTable_object_main(self):
        """
        Загружает данные в таблицу объектов с учетом фильтров.
        """
        self.loadTable_object_main_where()  # Генерация условия WHERE
        sql = f'''
            SELECT tm.id, tm.address, tm.name_ru, tm.cnt_otziv, tm.rating_average
            FROM object_main tm
            {self.s_where}
            ORDER BY tm.cnt_otziv DESC
            LIMIT 100
        '''
        self.cur.execute(sql)  # Выполнение SQL-запроса
        rows = self.cur.fetchall()
        self.populate_table(self.table_object_main, rows, ['УН', 'Адрес', 'Наименование', 'Кол-во отзывов', 'Средний балл'])

        # Установка ширины столбцов
        self.table_object_main.setColumnWidth(0, 50)   # УН
        self.table_object_main.setColumnWidth(1, 350)  # Адрес
        self.table_object_main.setColumnWidth(2, 200)  # Наименование
        self.table_object_main.setColumnWidth(3, 100)  # Кол-во отзывов
        self.table_object_main.setColumnWidth(4, 100)  # Средний балл

        if rows:
            self.table_object_main.setCurrentCell(0, 0)
        
        # Установка стилей с округлением углов и жирной рамкой
        self.table_object_main.setStyleSheet("""
            QHeaderView::section {
                background-color: #4CAF50;   /* Цвет фона заголовка */
                color: white;                 /* Цвет текста заголовка */
                font-weight: bold;            /* Жирный шрифт заголовка */
            }
            QTableWidget {
                font-size: 14px;              /* Размер шрифта */
                border: 2px solid #4CAF50;    /* Жирная рамка темно-красного цвета */
                border-radius: 10px;          /* Округленные углы */
                padding: 5px;                 /* Отступ внутри таблицы */
            }
            QTableWidget QTableCornerButton {
                background-color: #4CAF50;    /* Цвет угла таблицы */
            }
        """)  # Установка стилей с округлением углов и рамкой
        
    def loadTable_object_main_where(self):
        """
        Формирует SQL-условие WHERE на основе введенных фильтров.
        """
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

        self.s_where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''

    def populate_table(self, table, rows, headers):
        """
        Заполняет таблицу данными.
        """
        table.setRowCount(len(rows))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                table.setItem(i, j, item)
        table.resizeRowsToContents()

    def loadTable_otziv(self):
        """
        Загружает отзывы для текущего объекта.
        """
        if not self.id_object_main:
            return
        sql = f'''
            SELECT rating, text 
            FROM otziv 
            WHERE id_object_main = {self.id_object_main} 
            ORDER BY rating DESC
        '''
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        self.populate_table(self.table_otziv, rows, ['Рейтинг', 'Отзыв'])
        # Установка ширины столбцов
        self.table_otziv.setColumnWidth(0, 70)  # Рейтинг
        self.table_otziv.setColumnWidth(1, 1000)  # Отзыв

        self.table_otziv.setFixedSize(1180, 400)  # Устанавливаем ширину таблицы

        # Дополнительные визуальные настройки
        self.table_otziv.setAlternatingRowColors(True)  # Чередующиеся цвета строк

        # Применение стилей
        self.table_otziv.setStyleSheet("""
            QHeaderView::section {
                background-color: #4CAF50;  /* Цвет фона заголовка */
                color: white;                /* Цвет текста заголовка */
                font-weight: bold;           /* Жирный шрифт заголовка */
            }
            QTableWidget {
                font-size: 14px;            /* Размер шрифта */
                border: none;               /* Убираем рамку */
                selection-background-color: #A5D6A7; /* Цвет фона при выборе строк */
                border: 2px solid #4CAF50;    /* Жирная рамка темно-красного цвета */
                border-radius: 10px;          /* Округленные углы */
                padding: 5px;                 /* Отступ внутри таблицы */
            }
            QTableWidget QTableCornerButton {
                background-color: #4CAF50;  /* Цвет угла таблицы */
            }
        """)
        if rows:
            self.table_otziv.setCurrentCell(0, 0)

    def loadTable_rubrics(self):
        """
        Загружает рубрики для текущего объекта.
        """
        if not self.id_object_main:
            return
        sql = f'''
            SELECT rubrica
            FROM rubrics
            LEFT JOIN spr_rubrics ON spr_rubrics.id = rubrics.id_spr_rubrics
            WHERE id_object_main = {self.id_object_main}
            ORDER BY rubrica
        '''
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        self.populate_table(self.table_rubrics, rows, ['Рубрика'])
        self.table_rubrics.setColumnWidth(0, 250)  # Устанавливаем ширину 

        # Устанавливаем высоту таблицы
        self.table_rubrics.setFixedHeight(400)  # Установить фиксированную высоту таблицы

        # Применение стилей для красного цвета текста
        self.table_rubrics.setStyleSheet("""
            QTableWidget {
                color: black;                /* Установка красного цвета текста */
                font-size: 14px;          /* Размер шрифта */
                border: 2px solid red;    /* Жирная рамка темно-красного цвета */
                border-radius: 10px;          /* Округленные углы */
                padding: 5px;                 /* Отступ внутри таблицы */
            }
            QHeaderView::section {
                background-color: red; /* Цвет фона заголовка при необходимости */
                color: white;               /* Цвет текста заголовка */
                font-weight: bold;          /* Жирный шрифт для заголовка */
            }
        """)
    def table_object_main_cell_changed(self, currentRow, currentColumn):
        """
        Обрабатывает изменение текущей ячейки в таблице объектов.
        """
        if currentRow is not None:
            self.id_object_main = int(self.table_object_main.item(currentRow, 0).text())
            self.loadTable_otziv()  # Обновляем отзывы
            self.loadTable_rubrics()  # Обновляем рубрики

    def get_summarization_result(self):
        """
        Отправляет запрос на выполнение суммаризации.
        """
        if not self.id_object_main:
            return
        self.edit_summarization_result.setText('Запрос направлен...')
        # Логика суммаризации будет добавлена позже


def main():
    """
    Основная точка входа в приложение.
    """
    app = QApplication([])
    win = DatabaseTableEditor()
    win.show()
    app.exec()


if __name__ == '__main__':
    main()