from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords
from pymystem3 import Mystem

# Глобальный флаг для загрузки стоп-слов
punkt_downloaded = False

def text_sopost(original_text, summary_text):
    m = Mystem()
    
    # Лемматизация текста
    original_text = ' '.join(m.lemmatize(original_text)).strip()
    summary_text = ' '.join(m.lemmatize(summary_text)).strip()
    
    global punkt_downloaded
    if not punkt_downloaded:
        nltk.download('stopwords')
        punkt_downloaded = True

    # Получение списка стоп-слов
    stop_words = stopwords.words('russian')
    vectorizer = CountVectorizer(stop_words=stop_words)

    # Считаем частоты слов
    original_freq = vectorizer.fit_transform([original_text]).toarray()[0]
    summary_freq = vectorizer.transform([summary_text]).toarray()[0]
    vocab = vectorizer.get_feature_names_out()

    # Сортируем частоты слов оригинала
    sorted_indices = original_freq.argsort()[::-1]
    
    # Выбираем первые 10 слов с наибольшими частотами
    arr_result = []
    for i in sorted_indices[:10]:
        arr_result.append([vocab[i], original_freq[i], summary_freq[i]])

    # Формирование выходной строки
    s_out = '\n'.join(f"{row[0]}\t{row[1]}\t{row[2]}" for row in arr_result if row[2] > 0)
    cnt = sum(1 for row in arr_result if row[2] > 0)

    # Расчет b_out
    b_out = cnt / len(arr_result) if arr_result else 0
    
    return b_out, s_out

# Пример использования:
# b_out, s_out = text_sopost(original_text, summary_text)
# print(b_out, '\n', s_out)

