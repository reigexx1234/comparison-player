import streamlit as st
import pandas as pd
import soccerdata as sd
import matplotlib.pyplot as plt

# Настройка страницы
st.set_page_config(page_title="Football Player Compare", layout="wide")

st.title("⚽ Сравнение футболистов по данным FBref")

# Инструкция для пользователя
st.info("Введите ID игроков из URL FBref (например, 819b6927 для Салаха)")

# Боковая панель
st.sidebar.header("Настройки")
p1_id = st.sidebar.text_input("ID Игрока №1", value="819b6927")
p2_id = st.sidebar.text_input("ID Игрока №2", value="b8e7402a")

# Метрики для сравнения (можно менять)
metrics = {
    "Голы": ("shooting", "Gls"),
    "xG (Ожидаемые голы)": ("shooting", "xG"),
    "Удары в створ %": ("shooting", "SoT%"),
    "Передачи в штрафную": ("passing", "PPA"),
    "Прогрессивные передачи": ("passing", "PrgP")
}

@st.cache_data(ttl=3600)
def get_data(p_id):
    try:
        fb = sd.FBref()
        # Загружаем базовую статистику ударов
        df = fb.read_player_season_stats(stat_type="shooting")
        # Выбираем последнюю строку для этого игрока
        return df.xs(p_id, level='player').iloc[-1]
    except Exception as e:
        return None

if st.sidebar.button("Запустить сравнение"):
    with st.spinner("Загружаем данные..."):
        data1 = get_data(p1_id)
        data2 = get_data(p2_id)
        
        if data1 is not None and data2 is not None:
            # Создаем простую таблицу сравнения
            res = pd.DataFrame({
                "Параметр": ["Голы", "xG", "Удары в створ %"],
                "Игрок 1": [data1['Gls'], data1['xG'], data1['SoT%']],
                "Игрок 2": [data2['Gls'], data2['xG'], data2['SoT%']]
            })
            
            # Функция подсветки
            def highlight_max(s):
                is_max = s == s.max()
                return ['background-color: #90EE90' if v else '' for v in is_max]

            st.subheader("Результаты анализа")
            st.table(res.style.apply(highlight_max, subset=['Игрок 1', 'Игрок 2'], axis=1))
        else:
            st.error("Ошибка: Проверьте правильность ID игроков!")
