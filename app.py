import streamlit as st
import pandas as pd
import soccerdata as sd

st.set_page_config(page_title="Pro Football Scout", layout="wide")
st.title("⚽ Профессиональный скаут-инструмент")

# --- ФУНКЦИЯ ЗАГРУЗКИ СПИСКА ИГРОКОВ ---
@st.cache_data(ttl=86400) # Кэшируем список на 24 часа
def load_player_list():
    try:
        fb = sd.FBref()
        # Получаем статистику, чтобы вытащить из неё имена и ID
        # Для скорости берем только одну лигу для инициализации, 
        # но поиск будет работать по тем, кто загружен.
        df = fb.read_player_season_stats(stat_type="standard")
        df_flat = df.reset_index()
        
        # Создаем словарь: "Имя (Команда)" -> ID
        df_flat['display_name'] = df_flat['player'] + " (" + df_flat['Squad'] + ")"
        player_dict = pd.Series(df_flat.player_id.values, index=df_flat.display_name).to_dict()
        return player_dict
    except:
        # Резервный список, если FBref недоступен
        return {"Lionel Messi": "d70ce98e", "Kylian Mbappé": "42fd4c3c"}

# Загружаем базу
with st.spinner("Загрузка базы игроков..."):
    PLAYER_DB = load_player_list()
    player_names = sorted(list(PLAYER_DB.keys()))

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("Поиск")

# Поиск с автодополнением (работает при вводе 3+ букв)
p1_select = st.sidebar.selectbox("Игрок №1:", player_names, index=0 if len(player_names) > 0 else 0)
p2_select = st.sidebar.selectbox("Игрок №2:", player_names, index=1 if len(player_names) > 1 else 0)

p1_id = PLAYER_DB[p1_select]
p2_id = PLAYER_DB[p2_select]

st.sidebar.markdown("---")
mode = st.sidebar.radio("Режим:", ["Весь сезон", "Последние 5 матчей"])

# --- ПОЛУЧЕНИЕ ДАННЫХ ---
@st.cache_data(ttl=3600)
def get_stats(p_id, match_logs=False):
    fb = sd.FBref()
    try:
        if match_logs:
            df = fb.read_player_match_logs(stat_type="summary")
            return df.xs(p_id, level='player').tail(5)
        else:
            df = fb.read_player_season_stats(stat_type="standard")
            return df.xs(p_id, level='player').iloc[-1]
    except:
        return None

# --- ВЫВОД ---
if st.sidebar.button("Сравнить"):
    if mode == "Весь сезон":
        d1 = get_stats(p1_id)
        d2 = get_stats(p2_id)
        if d1 is not None and d2 is not None:
            st.subheader("📊 Итоги сезона")
            res = pd.DataFrame({
                "Метрика": ["Команда", "Матчи", "Голы", "xG"],
                p1_select: [d1['Squad'], d1['MP'], d1['Gls'], d1['xG']],
                p2_select: [d2['Squad'], d2['MP'], d2['Gls'], d2['xG']]
            })
            st.table(res)
    
    elif mode == "Последние 5 матчей":
        l1 = get_stats(p1_id, True)
        l2 = get_stats(p2_id, True)
        
        col1, col2 = st.columns(2)
        for col, logs, name in zip([col1, col2], [l1, l2], [p1_select, p2_select]):
            with col:
                st.subheader(name)
                if logs is not None:
                    st.dataframe(logs.reset_index()[['Date', 'Opponent', 'Gls', 'xG']])
                else:
                    st.error("Нет данных")
