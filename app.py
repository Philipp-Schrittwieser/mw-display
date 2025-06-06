import streamlit as st
import json
import pandas as pd
import plotly.express as px
import numpy as np

# App-Stil
st.set_page_config(page_title="marswalk Video Performance Analysis", layout="wide")


st.markdown("""
<style>
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  [data-testid=stDecoration] {display: none;}
  .stAppToolbar {display: none;}
""", unsafe_allow_html=True)




# Funktion zum Laden der Daten
def load_data(file_name):
    with open(file_name, "r") as f:
        data = json.load(f)
    return data

# Auswahl der JSON-Datei
# st.sidebar.title("🪐 marswalk")
st.sidebar.image("logo.png", width=250)
file_option = st.sidebar.selectbox("Datenquelle:", ["mit_views.json", "ohne_views.json"])

# Daten laden
data = load_data(file_option)

# Dashboard Header
st.title("Video Performance Analysis")

# Daten in DataFrame umwandeln
df = pd.DataFrame([{
    "tiktok_user": item.get("tiktok_user", "Unbekannt"),
    "description": item.get("title", "")[:80],
    "video_url": item.get("item_url", item.get("video_url", "")),
    "likes": int(item.get("likes", 0)) if isinstance(item.get("likes"), (int, float)) or (isinstance(item.get("likes"), str) and item.get("likes").isdigit()) else 0,
    "shares": int(item.get("shares", 0)) if isinstance(item.get("shares"), (int, float)) or (isinstance(item.get("shares"), str) and item.get("shares").isdigit()) else 0,
    "bookmarks": int(item.get("bookmarks", 0)) if isinstance(item.get("bookmarks"), (int, float)) or (isinstance(item.get("bookmarks"), str) and item.get("bookmarks").isdigit()) else 0,
    "comments": int(item.get("comments", 0)) if isinstance(item.get("comments"), (int, float)) or (isinstance(item.get("comments"), str) and item.get("comments").isdigit()) else 0,
    "song_title": item.get("song_title", ""),
    "views": int(item.get("statsV2", {}).get("playCount", 0) if item.get("statsV2") is not None else 0)
} for item in data])

# Success Score berechnen
st.sidebar.header("Success Score Formel")
st.sidebar.write("Stelle die Gewichtung für den Score ein:")

# Gewichtungen per Slider einstellbar
likes_weight = st.sidebar.slider("Likes Gewichtung", 0.1, 5.0, 1.0, 0.1)
shares_weight = st.sidebar.slider("Shares Gewichtung", 0.1, 5.0, 2.0, 0.1)
bookmarks_weight = st.sidebar.slider("Bookmarks Gewichtung", 0.1, 5.0, 1.5, 0.1)
comments_weight = st.sidebar.slider("Comments Gewichtung", 0.1, 5.0, 1.0, 0.1)
views_weight = st.sidebar.slider("Views Gewichtung", 0.0, 5.0, 0.5, 0.1)

normalize = st.sidebar.checkbox("Werte normalisieren (empfohlen)", True)

st.sidebar.info("Die Formel berücksichtigt alle Metriken mit deinen Gewichtungen")

# Success Score berechnen
if normalize:
    # Normalisieren der Werte (0-1 Skala)
    df["likes_norm"] = df["likes"] / df["likes"].max() if df["likes"].max() > 0 else 0
    df["shares_norm"] = df["shares"] / df["shares"].max() if df["shares"].max() > 0 else 0
    df["bookmarks_norm"] = df["bookmarks"] / df["bookmarks"].max() if df["bookmarks"].max() > 0 else 0
    df["comments_norm"] = df["comments"] / df["comments"].max() if df["comments"].max() > 0 else 0
    df["views_norm"] = df["views"] / df["views"].max() if df["views"].max() > 0 else 0
    
    # Gewichteter Score (0-100)
    df["success_score"] = (
        df["likes_norm"] * likes_weight +
        df["shares_norm"] * shares_weight +
        df["bookmarks_norm"] * bookmarks_weight +
        df["comments_norm"] * comments_weight +
        df["views_norm"] * views_weight
    ) * 100 / (likes_weight + shares_weight + bookmarks_weight + comments_weight + views_weight)
else:
    # Direkter gewichteter Score
    df["success_score"] = (
        df["likes"] * likes_weight +
        df["shares"] * shares_weight * 100 +  # Weil Shares typischerweise deutlich niedriger sind
        df["bookmarks"] * bookmarks_weight * 10 +
        df["comments"] * comments_weight * 10 +
        df["views"] * views_weight * 0.01
    ) / (likes_weight + shares_weight + bookmarks_weight + comments_weight + views_weight)

# Tabs für verschiedene Ansichten
tab1, tab2 = st.tabs(["📊 Video Ranking", "📈 Top-Videos Analyse"])

# Tab 1: Video Ranking nach Score
with tab1:
    # Filter-Optionen
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        search_term = st.text_input("Suche nach Video-Beschreibung:")
    
    with col2:
        creators = sorted(df['tiktok_user'].unique())
        selected_creators = st.multiselect("Filter nach Creator:", creators)
    
    with col3:
        min_score = st.number_input("Min. Success Score:", 0.0, 100.0, 0.0, 5.0)
    
    # Daten filtern
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False)]
    
    if selected_creators:
        filtered_df = filtered_df[filtered_df['tiktok_user'].isin(selected_creators)]
    
    if min_score > 0:
        filtered_df = filtered_df[filtered_df['success_score'] >= min_score]
    
    # Nach Success Score sortieren
    sorted_df = filtered_df.sort_values(by="success_score", ascending=False).reset_index(drop=True)
    
    # Anzeige der gefilterten Videos
    st.subheader(f"Video-Ranking nach Success Score ({len(sorted_df)} Videos)")
    
   

    # Container für die Box
    with st.container(border=True):
        show_table = st.checkbox(":red[**Als Tabelle anzeigen**]", True)
    
    st.write("")

    if show_table:
        # Als Tabelle formatieren
        display_df = sorted_df[['tiktok_user', 'description', 'video_url', 'likes', 'shares', 
                               'bookmarks', 'comments', 'views', 'success_score']].copy()
        display_df.columns = ['Creator', 'Beschreibung', 'Video Link', 'Likes', 'Shares', 'Bookmarks', 
                             'Comments', 'Views', 'Success Score']
        display_df['Success Score'] = display_df['Success Score'].round(1)
        
        st.dataframe(
            display_df,
            column_config={
                "Success Score": st.column_config.ProgressColumn(
                    "Success Score",
                    format="%f",
                    min_value=0,
                    max_value=100,
                ),
                "Beschreibung": st.column_config.TextColumn(
                    "Beschreibung",
                    width="medium",
                ),
                "Video Link": st.column_config.LinkColumn(
                    "Video Link",
                    display_text="Link"
                ),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        # Als detaillierte Liste anzeigen
        for i, row in enumerate(sorted_df.itertuples(), 1):
            score_color = "green" if row.success_score > 70 else "orange" if row.success_score > 40 else "red"
            
            with st.container():
                left_col, right_col = st.columns([3, 1])
                
                with left_col:
                    st.markdown(f"#### #{i}: {row.description}")
                    st.markdown(f"**Creator:** @{row.tiktok_user} | **Score:** "
                              f"<span style='color:{score_color};font-weight:bold;'>{row.success_score:.1f}</span>/100", 
                              unsafe_allow_html=True)
                    
                    metric_cols = st.columns(5)
                    metric_cols[0].metric("❤️ Likes", f"{row.likes:,}")
                    metric_cols[1].metric("↗️ Shares", f"{row.shares:,}")
                    metric_cols[2].metric("🔖 Bookmarks", f"{row.bookmarks:,}")
                    metric_cols[3].metric("💬 Comments", f"{row.comments:,}")
                    metric_cols[4].metric("👁️ Views", f"{row.views:,}")
                    
                    st.markdown(f"[Video auf TikTok ansehen]({row.video_url})")
                
                with right_col:
                    # Success Score als Donut-Chart
                    progress_html = f"""
                    <div style="position: relative; width: 100px; height: 100px; border-radius: 50%; 
                                background: conic-gradient({score_color} {row.success_score}%, #f0f0f0 0); 
                                margin: 0 auto;">
                        <div style="position: absolute; top: 10px; left: 10px; width: 80px; height: 80px; 
                                    border-radius: 50%; background-color: white; display: flex; 
                                    align-items: center; justify-content: center; font-weight: bold; 
                                    font-size: 20px; color: {score_color};">
                            {row.success_score:.0f}
                        </div>
                    </div>
                    """
                    st.markdown(progress_html, unsafe_allow_html=True)
                
                st.markdown("---")

# Tab 2: Top-Videos Analyse
with tab2:
    st.subheader("Success Faktoren Analyse")
    
    # Top 20 Videos nach Score
    top_videos = df.sort_values(by="success_score", ascending=False).head(20)
    
    # Balkendiagramm der Success Scores
    fig1 = px.bar(
        top_videos,
        x="success_score",
        y="description",
        orientation='h',
        color="success_score",
        color_continuous_scale="viridis",
        title="Top 20 Videos nach Success Score",
        labels={"success_score": "Success Score", "description": "Video"},
        text="tiktok_user"
    )
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)
    
    # Metriken-Aufschlüsselung für Top 10
    st.subheader("Metriken der Top 10 Videos")
    
    top10 = top_videos.head(10).copy()
    top10["video_id"] = range(1, 11)
    top10["video_name"] = top10["video_id"].astype(str) + ". @" + top10["tiktok_user"]
    
    # Normalisierte Werte für bessere Darstellung
    metrics_df = pd.DataFrame({
        "Video": np.repeat(top10["video_name"].tolist(), 5),  # 5 statt 4
        "Metrik": ["Likes", "Shares", "Bookmarks", "Comments", "Views"] * 10,
        "Wert": np.concatenate([
            top10["likes_norm"].values, 
            top10["shares_norm"].values,
            top10["bookmarks_norm"].values,
            top10["comments_norm"].values,
            top10["views_norm"].values
        ]),
        "Gewicht": np.concatenate([
            [likes_weight] * 10,
            [shares_weight] * 10,
            [bookmarks_weight] * 10,
            [comments_weight] * 10,
            [views_weight] * 10
        ])
    })
    
    fig2 = px.bar(
        metrics_df,
        x="Video",
        y="Wert",
        color="Metrik",
        barmode="group",
        title="Normalisierte Metriken der Top 10 Videos",
        labels={"Wert": "Normalisierter Wert (0-1)"},
        hover_data=["Gewicht"]
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Korrelation zwischen Metriken und Score
    st.subheader("Was trägt am meisten zum Success Score bei?")
    
    corr_df = pd.DataFrame({
        "Metrik": ["Likes", "Shares", "Bookmarks", "Comments", "Views"],
        "Korrelation mit Score": [
            df["likes"].corr(df["success_score"]),
            df["shares"].corr(df["success_score"]),
            df["bookmarks"].corr(df["success_score"]),
            df["comments"].corr(df["success_score"]),
            df["views"].corr(df["success_score"])
        ]
    })
    
    fig3 = px.bar(
        corr_df,
        x="Metrik",
        y="Korrelation mit Score",
        color="Korrelation mit Score",
        color_continuous_scale="RdBu",
        title="Korrelation zwischen Metriken und Success Score",
        text_auto='.2f'
    )
    st.plotly_chart(fig3, use_container_width=True)

# Footer mit Erklärung
with st.expander("ℹ️ Wie wird der Success Score berechnet?"):
    st.markdown("""
    ### Success Score Berechnung
    
    Der Success Score ist ein gewichteter Wert zwischen 0-100, der die Performance eines Videos bewertet:
    
    1. **Normalisierung**: Alle Metriken werden auf eine Skala von 0-1 normalisiert
    2. **Gewichtung**: Die normalisierten Werte werden mit deinen Gewichtungen multipliziert
    3. **Kombinierung**: Der gewichtete Durchschnitt wird auf eine 0-100 Skala umgerechnet
    
    **Formel**:
    ```
    Success Score = (likes_norm * likes_weight + shares_norm * shares_weight + 
                    bookmarks_norm * bookmarks_weight + comments_norm * comments_weight +
                    views_norm * views_weight) * 100 / 
                    (likes_weight + shares_weight + bookmarks_weight + comments_weight + views_weight)
    ```
    
    Passe die Gewichtungen in der Seitenleiste an, um verschiedene Bewertungsmodelle zu testen!
    """)

# Neues Feld mit allen Beschreibungen als nummerierte Liste
with st.expander("📋 Alle Video-Beschreibungen"):
    # Erstelle eine nummerierte Liste aller Beschreibungen als String
    descriptions_list = ""
    for i, desc in enumerate(df['description'], 1):
        descriptions_list += f"{i}. {desc}\n"
    
    # Zeige die Liste an
    st.text_area("Liste aller Videos:", descriptions_list, height=300)

# Gemini-Analyse in einem eigenen Expander, der standardmäßig geöffnet ist
with st.expander("🧠 KI-Trend-Analyse", expanded=True):
    # Zusätzliche Informationen für den Prompt
    additional_info = st.text_area(
        "Zusätzliche Informationen für die Analyse (z.B. Zielgruppe, Produkt, spezifische Anforderungen):",
        placeholder="Beispiel: Mein Kunde ist Coca Cola und sucht nach Ideen für erfrischende Sommer-Content..."
    )
    
    # Zeile mit Buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        analyze_button = st.button("🔍 Call Gemini für Trend-Analyse", use_container_width=True)
    with col2:
        regenerate_button = st.button("🔄 Neu generieren", use_container_width=True)
    with col3:
        reset_button = st.button("❌ Reset", use_container_width=True)
    
    # Wenn Reset geklickt wird, Session State zurücksetzen
    if reset_button:
        if 'gemini_response' in st.session_state:
            del st.session_state['gemini_response']
        st.rerun()
    
    # Wenn Analyse-Button oder Regenerate-Button geklickt wird oder bereits eine Antwort im Session State ist
    if analyze_button or regenerate_button or 'gemini_response' in st.session_state:
        # Nur API aufrufen, wenn der Button geklickt wurde oder neu generieren
        if analyze_button or regenerate_button:
            # Loading-Spinner während der Analyse
            with st.spinner("Gemini analysiert die Video-Beschreibungen..."):
                try:
                    # Gemini API direkt einbinden
                    import google.generativeai as genai
                    
                    # API-Key aus Streamlit Secrets oder als Input
                    api_key = st.secrets.get("GEMINI_API_KEY", None)
                    
                    if not api_key:
                        api_key = st.text_input("Bitte Gemini API-Key eingeben:", type="password")
                        if not api_key:
                            st.warning("API-Key wird benötigt, um Gemini zu nutzen.")
                            st.stop()
                    
                    # Gemini konfigurieren
                    genai.configure(api_key=api_key)
                    
                    # Modell initialisieren
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    # Erstelle die Liste der Beschreibungen, falls sie noch nicht existiert
                    if 'descriptions_list' not in locals():
                        descriptions_list = ""
                        for i, desc in enumerate(df['description'], 1):
                            descriptions_list += f"{i}. {desc}\n"
                    
                    # Zusätzliche Informationen in den Prompt einbauen
                    additional_context = ""
                    if additional_info:
                        additional_context = f"""
                        Zusätzliche Informationen:
                        {additional_info}
                        
                        Berücksichtige diese Informationen besonders in deiner Analyse und den Empfehlungen.
                        """
                    
                    # Prompt erstellen
                    prompt = f"""
                    Du bist eine TikTok-Agentur und versuchst aus folgenden Bildbeschreibungen Anzeichen für Trends zu sammeln, 
                    um weiteren Content zu generieren. Analysiere diese Beschreibungen und identifiziere:
                    
                    1. Häufige Themen und Muster
                    2. Erfolgreiche Hashtags
                    3. Content-Formate die gut funktionieren
                    4. Empfehlungen für neue Content-Ideen (Gib hier konkrete Beispiele für Video Ideen)

                    ENDE, höre nach 4. auf und gebe keine weiteren Informationen.
                    
                    {additional_context}
                    
                    Beschreibungen:
                    {descriptions_list}
                    
                    Antworte auf Deutsch und formatiere deine Antwort mit Markdown.
                    """
                    
                    # Antwort generieren
                    response = model.generate_content(prompt)
                    
                    # Antwort im Session State speichern
                    st.session_state['gemini_response'] = response.text
                    
                except Exception as e:
                    st.error(f"Fehler bei der Gemini-API: {str(e)}")
                    st.info("Tipp: Stelle sicher, dass du einen gültigen API-Key hast und die Google Generative AI Bibliothek installiert ist (pip install google-generativeai)")
        
        # Antwort anzeigen (entweder neu generiert oder aus dem Session State)
        if 'gemini_response' in st.session_state:
            st.success("Trend-Analyse abgeschlossen!")
            st.markdown(st.session_state['gemini_response'])
            
            # Download-Button für die Analyse
            st.download_button(
                label="Analyse als Text herunterladen",
                data=st.session_state['gemini_response'],
                file_name="tiktok_trend_analyse.txt",
                mime="text/plain"
            ) 