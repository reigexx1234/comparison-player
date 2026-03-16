import streamlit as st
import pandas as pd
import soccerdata as sd

# Настройка внешнего вида
st.set_page_config(page_title="Football Scout Pro", layout="wide")

# --- ФУНКЦИЯ ЗАГРУЗКИ ВСЕХ ИГРОКОВ (Кэш на 24 часа) ---
@st.cache_data(ttl=86400)
def load_all_players():
    try:
        fb = sd.FBref()
        # Качаем общую статистику для создания списка поиска
        df = fb.read_player_season_stats(stat_type="standard")
        df = df.reset_index()
        
        # Создаем имя для поиска: "Имя (Команда)"
        df['display_name'] = df['player'] + " (" + df['Squad'].astype(str) + ")"
        
        # Убираем дубликаты и создаем словарь {Имя: ID}
        player_dict = pd.Series(df.player_id.values, index=df.display_name).to_dict()
        return player_dict
    except:
        return {"Lionel Messi (Inter Miami)": "d70ce98e", "Kylian Mbappé (Real Madrid)": "42fd4c3c"}

# --- ФУНКЦИЯ ПОЛУЧЕНИЯ СТАТИСТИКИ (Кэш на 1 час) ---
@st.cache_data(ttl=3600)
def get_player_stats(p_id, mode="Season"):
    fb = sd.FBref()
    try:
        if mode == "Matches":
            df = fb.read_player_match_logs(stat_type="summary")
            df = df.reset_index()
            return df[df['player_id'] == p_id].tail(5)
        else:
            df = fb.read_player_season_stats(stat_type="standard")
            df = df.reset_index()
            # Берем самую свежую строку данных этого игрока
            return df[df['player_id'] == p_id].iloc[-1]
    except:
        return None

# --- ИНТЕРФЕЙС ---
st.title("⚽ Football Scout Professional")
st.markdown("Инструмент для глубокого анализа и сравнения футболистов на базе данных **FBref**.")

# Загружаем базу имен
with st.spinner("Синхронизация базы игроков..."):
    PLAYER_DB = load_all_players()
    player_names = sorted(list(PLAYER_DB.keys()))

# Боковая панель
st.sidebar.header("Параметры поиска")
p1_name = st.sidebar.selectbox("Игрок №1:", player_names, index=0)
p2_name = st.sidebar.selectbox("Игрок №2:", player_names, index=min(1, len(player_names)-1))

# Достаем ID по выбранным именам
id1 = PLAYER_DB[p1_name]
id2 = PLAYER_DB[p2_name]

st.sidebar.markdown("---")
analysis_mode = st.sidebar.radio("Тип данных:", ["Итоги сезона", "Последние 5 игр (Форма)"])

# Кнопка запуска
if st.sidebar.button("Провести анализ"):
    if analysis_mode == "Итоги сезона":
        data1 = get_player_stats(id1, "Season")
        data2 = get_player_stats(id2, "Season")
        
        if data1 is not None and data2 is not None:
            st.subheader("📊 Сравнение за сезон")
            
            # Создаем красивую таблицу сравнения
            metrics = {
                "Показатель": ["Команда", "Лига", "Матчи", "Минуты", "Голы", "Ассисты", "xG (Ожидаемые)"],
                p1_name: [data1['Squad'], data1['Comp'], data1['MP'], data1['Min'], data1['Gls'], data1['Ast'], data1['xG']],
                p2_name: [data2['Squad'], data2['Comp'], data2['MP'], data2['Min'], data2['Gls'], data2['Ast'], data2['xG']]
            }
            df_compare = pd.DataFrame(metrics)
            st.table(df_compare)
            
            # Визуальный индикатор (метрики)
            c1, c2 = st.columns(2)
            c1.metric(f"Голы {data1['player']}", int(data1['Gls']))
            c2.metric(f"Голы {data2['player']}", int(data2['Gls']))
        else:
            st.error("Не удалось подгрузить сезонную статистику.")

    else:
        log1 = get_player_stats(id1, "Matches")
        log2 = get_player_stats(id2, "Matches")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Форма: {p1_name}")
            if log1 is not None and not log1.empty:
                st.dataframe(log1[['Date', 'Opponent', 'Gls', 'Ast', 'xG']], hide_index=True)
            else: st.warning("Нет данных о матчах")
            
        with col2:
            st.subheader(f"Форма: {p2_name}")
            if log2 is not None and not log2.empty:
                st.dataframe(log2[['Date', 'Opponent', 'Gls', 'Ast', 'xG']], hide_index=True)
            else: st.warning("Нет данных о матчах")

# Инфо-блок
st.sidebar.markdown("---")
st.sidebar.info("Данные обновляются автоматически раз в сутки. Поиск работает по английским именам игроков.")
