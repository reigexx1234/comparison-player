import streamlit as st
import pandas as pd
import soccerdata as sd

st.set_page_config(page_title="Pro Football Scout", layout="wide")
st.title("⚽ Детальное сравнение игроков")

# --- БОКОВАЯ ПАНЕЛЬ: ВВОД ДАННЫХ ---
st.sidebar.header("Настройки поиска")
p1_id = st.sidebar.text_input("ID Игрока №1", value="819b6927") # Салах
p2_id = st.sidebar.text_input("ID Игрока №2", value="b8e7402a") # Холанд

# --- БОКОВАЯ ПАНЕЛЬ: ФИЛЬТРЫ ---
st.sidebar.markdown("---")
st.sidebar.header("Фильтры турниров и матчей")

# Выбор режима работы
mode = st.sidebar.radio(
    "Выберите режим сравнения:",
    ["Весь сезон (Суммарно)", "Конкретный турнир", "Последние 5 матчей"]
)

# Если выбран конкретный турнир, даем возможность вписать его название
# (В идеале здесь должен быть выпадающий список, но для простоты начнем с ввода)
selected_comp = None
if mode == "Конкретный турнир":
    selected_comp = st.sidebar.selectbox(
        "Выберите турнир:", 
        ["Premier League", "Champions Lg", "La Liga", "Serie A", "Bundesliga"]
    )

# --- ФУНКЦИИ ПОЛУЧЕНИЯ ДАННЫХ ---
@st.cache_data(ttl=3600)
def get_season_data(p_id, comp_filter=None):
    """Получает статистику за сезон (с фильтром по турниру или без)"""
    try:
        fb = sd.FBref()
        df = fb.read_player_season_stats(stat_type="standard")
        player_df = df.xs(p_id, level='player')
        
        if comp_filter:
            # Ищем строки, где в названии турнира есть выбранный (например, Premier League)
            player_df = player_df[player_df.index.get_level_values('Comp').str.contains(comp_filter, na=False)]
            if player_df.empty:
                return None
            return player_df.iloc[-1] # Берем последний сезон в этом турнире
        else:
            # Если фильтра нет, берем строку, где турнир указан как комбинированный, 
            # либо просто самую свежую общую строку
            return player_df.iloc[-1] 
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def get_match_logs(p_id):
    """Получает статистику по отдельным матчам"""
    try:
        fb = sd.FBref()
        # Загружаем логи матчей за текущий сезон
        df = fb.read_player_match_logs(stat_type="summary")
        player_logs = df.xs(p_id, level='player')
        return player_logs.tail(5) # Возвращаем 5 последних матчей
    except Exception as e:
        return None

# --- ОСНОВНОЙ ЭКРАН: ВЫВОД РЕЗУЛЬТАТОВ ---
if st.sidebar.button("Сравнить"):
    with st.spinner("Загрузка данных с FBref (может занять до минуты)..."):
        
        # ЛОГИКА ДЛЯ СЕЗОНА И ТУРНИРОВ
        if mode in ["Весь сезон (Суммарно)", "Конкретный турнир"]:
            comp_to_search = selected_comp if mode == "Конкретный турнир" else None
            
            data1 = get_season_data(p1_id, comp_to_search)
            data2 = get_season_data(p2_id, comp_to_search)
            
            if data1 is not None and data2 is not None:
                st.subheader(f"📊 Сравнение: {mode}")
                if comp_to_search:
                    st.caption(f"Турнир: {comp_to_search}")

                res = pd.DataFrame({
                    "Метрика": ["Сыграно матчей (MP)", "Голы (Gls)", "Ассисты (Ast)", "xG", "Желтые карточки (CrdY)"],
                    "Игрок 1": [data1.get('MP', 0), data1.get('Gls', 0), data1.get('Ast', 0), data1.get('xG', 0), data1.get('CrdY', 0)],
                    "Игрок 2": [data2.get('MP', 0), data2.get('Gls', 0), data2.get('Ast', 0), data2.get('xG', 0), data2.get('CrdY', 0)]
                })
                
                # Подсвечиваем лучшие результаты (для карточек лучше меньше, но для простоты подсветим максимум)
                st.table(res.style.highlight_max(subset=['Игрок 1', 'Игрок 2'], color='#90EE90', axis=1))
            else:
                st.error("Данные не найдены. Возможно, игрок не участвовал в этом турнире.")

        # ЛОГИКА ДЛЯ ОТДЕЛЬНЫХ МАТЧЕЙ
        elif mode == "Последние 5 матчей":
            logs1 = get_match_logs(p1_id)
            logs2 = get_match_logs(p2_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Игрок 1: Форма")
                if logs1 is not None and not logs1.empty:
                    # Выбираем только самые интересные колонки для отображения
                    display_logs = logs1[['Date', 'Comp', 'Opponent', 'Min', 'Gls', 'Ast', 'xG']]
                    st.dataframe(display_logs)
                else:
                    st.warning("Нет данных о матчах.")
                    
            with col2:
                st.subheader("Игрок 2: Форма")
                if logs2 is not None and not logs2.empty:
                    display_logs = logs2[['Date', 'Comp', 'Opponent', 'Min', 'Gls', 'Ast', 'xG']]
                    st.dataframe(display_logs)
                else:
                    st.warning("Нет данных о матчах.")
