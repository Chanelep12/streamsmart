# ============================================================
# STREAMSMART - Dashboard Plotly Dash
# KPIs + Graphiques + Filtres interactifs
# ============================================================

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import warnings
warnings.filterwarnings("ignore")

DB_PATH = "streamsmart.db"

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

def load_rfm():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM rfm_segments", conn)
    conn.close()
    return df

def load_listens():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT l.user_id, l.listened_at, l.completed,
               t.title, t.artist, t.genre, t.duration_s
        FROM listens l
        JOIN tracks t ON l.track_id = t.track_id
    """, conn)
    conn.close()
    df["listened_at"] = pd.to_datetime(df["listened_at"])
    df["month"] = df["listened_at"].dt.to_period("M").astype(str)
    return df

def load_tracks():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT t.title, t.artist, t.genre,
               COUNT(l.listen_id) AS nb_ecoutes
        FROM tracks t
        LEFT JOIN listens l ON t.track_id = l.track_id
        GROUP BY t.track_id
        ORDER BY nb_ecoutes DESC
    """, conn)
    conn.close()
    return df

df_rfm     = load_rfm()
df_listens = load_listens()
df_tracks  = load_tracks()

# ============================================================
# COULEURS SEGMENTS
# ============================================================

SEGMENT_COLORS = {
    "Champion":  "#6C63FF",
    "Loyal":     "#3ECFCF",
    "Potentiel": "#F59E0B",
    "À risque":  "#F97316",
    "Inactif":   "#EF4444",
}

# ============================================================
# APP DASH
# ============================================================

app = Dash(__name__)
app.title = "StreamSmart Dashboard"

# ============================================================
# LAYOUT
# ============================================================

app.layout = html.Div(style={"fontFamily": "Segoe UI, sans-serif", "backgroundColor": "#0F0F1A", "minHeight": "100vh", "padding": "24px"}, children=[

    # ── Header ──────────────────────────────────────────────
    html.Div(style={"marginBottom": "28px"}, children=[
        html.H1("🎵 StreamSmart", style={"color": "#FFFFFF", "fontSize": "28px", "margin": 0}),
        html.P("Dashboard Marketing & Analyse RFM", style={"color": "#9CA3AF", "margin": "4px 0 0 0"}),
    ]),

    # ── Filtres ──────────────────────────────────────────────
    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}, children=[

        html.Div([
            html.Label("Segment RFM", style={"color": "#9CA3AF", "fontSize": "12px", "marginBottom": "4px", "display": "block"}),
            dcc.Dropdown(
                id="filter-segment",
                options=[{"label": "Tous", "value": "Tous"}] + [{"label": s, "value": s} for s in sorted(df_rfm["segment"].unique())],
                value="Tous",
                clearable=False,
                style={"width": "200px", "backgroundColor": "#1E1E2E", "color": "#000"},
            )
        ]),

        html.Div([
            html.Label("Plan d'abonnement", style={"color": "#9CA3AF", "fontSize": "12px", "marginBottom": "4px", "display": "block"}),
            dcc.Dropdown(
                id="filter-plan",
                options=[{"label": "Tous", "value": "Tous"}] + [{"label": p.capitalize(), "value": p} for p in sorted(df_rfm["plan"].dropna().unique())],
                value="Tous",
                clearable=False,
                style={"width": "200px", "backgroundColor": "#1E1E2E", "color": "#000"},
            )
        ]),

        html.Div([
            html.Label("Pays", style={"color": "#9CA3AF", "fontSize": "12px", "marginBottom": "4px", "display": "block"}),
            dcc.Dropdown(
                id="filter-country",
                options=[{"label": "Tous", "value": "Tous"}] + [{"label": c, "value": c} for c in sorted(df_rfm["country"].unique())],
                value="Tous",
                clearable=False,
                style={"width": "200px", "backgroundColor": "#1E1E2E", "color": "#000"},
            )
        ]),
    ]),

    # ── KPIs ─────────────────────────────────────────────────
    html.Div(id="kpi-cards", style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),

    # ── Graphiques ligne 1 ───────────────────────────────────
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px"}, children=[
            dcc.Graph(id="graph-segments", config={"displayModeBar": False})
        ]),
        html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px"}, children=[
            dcc.Graph(id="graph-rfm-scatter", config={"displayModeBar": False})
        ]),
    ]),

    # ── Graphiques ligne 2 ───────────────────────────────────
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginBottom": "16px"}, children=[
        html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px"}, children=[
            dcc.Graph(id="graph-top-tracks", config={"displayModeBar": False})
        ]),
        html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px"}, children=[
            dcc.Graph(id="graph-genres", config={"displayModeBar": False})
        ]),
    ]),

    # ── Graphique ligne 3 ────────────────────────────────────
    html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px", "marginBottom": "16px"}, children=[
        dcc.Graph(id="graph-ecoutes-temps", config={"displayModeBar": False})
    ]),

    # ── Table utilisateurs ───────────────────────────────────
    html.Div(style={"backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px"}, children=[
        html.H3("👥 Détail utilisateurs", style={"color": "#FFFFFF", "fontSize": "16px", "marginTop": 0}),
        html.Div(id="user-table")
    ]),
])


# ============================================================
# CALLBACKS
# ============================================================

def filter_df(segment, plan, country):
    """Applique les filtres sur df_rfm"""
    df = df_rfm.copy()
    if segment != "Tous":
        df = df[df["segment"] == segment]
    if plan != "Tous":
        df = df[df["plan"] == plan]
    if country != "Tous":
        df = df[df["country"] == country]
    return df


@app.callback(
    Output("kpi-cards", "children"),
    Output("graph-segments", "figure"),
    Output("graph-rfm-scatter", "figure"),
    Output("graph-top-tracks", "figure"),
    Output("graph-genres", "figure"),
    Output("graph-ecoutes-temps", "figure"),
    Output("user-table", "children"),
    Input("filter-segment", "value"),
    Input("filter-plan", "value"),
    Input("filter-country", "value"),
)
def update_dashboard(segment, plan, country):
    df = filter_df(segment, plan, country)

    # ── KPIs ─────────────────────────────────────────────────
    nb_users     = len(df)
    avg_recency  = int(df["recency"].mean()) if nb_users > 0 else 0
    avg_freq     = round(df["frequency"].mean(), 1) if nb_users > 0 else 0
    total_rev    = round(df["monetary"].sum(), 0) if nb_users > 0 else 0
    nb_champions = len(df[df["segment"] == "Champion"])

    def kpi_card(title, value, icon, color):
        return html.Div(style={
            "backgroundColor": "#1E1E2E", "borderRadius": "12px", "padding": "16px 20px",
            "borderLeft": f"4px solid {color}", "flex": "1", "minWidth": "160px"
        }, children=[
            html.P(f"{icon} {title}", style={"color": "#9CA3AF", "fontSize": "12px", "margin": "0 0 4px 0"}),
            html.H2(str(value), style={"color": "#FFFFFF", "margin": 0, "fontSize": "28px"}),
        ])

    kpis = [
        kpi_card("Utilisateurs", nb_users, "👥", "#6C63FF"),
        kpi_card("Champions RFM", nb_champions, "🏆", "#F59E0B"),
        kpi_card("Récence moy. (j)", avg_recency, "📅", "#3ECFCF"),
        kpi_card("Écoutes moy.", avg_freq, "🎵", "#F97316"),
        kpi_card("Revenus (€)", f"{total_rev:,.0f}", "💰", "#10B981"),
    ]

    # ── Graphique 1 : Répartition segments ──────────────────
    seg_counts = df["segment"].value_counts().reset_index()
    seg_counts.columns = ["segment", "count"]
    fig_seg = px.pie(
        seg_counts, names="segment", values="count",
        color="segment", color_discrete_map=SEGMENT_COLORS,
        title="Répartition des segments RFM",
        hole=0.5,
    )
    fig_seg.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF", title_font_size=14,
        legend=dict(font=dict(color="#9CA3AF")),
        margin=dict(t=40, b=10, l=10, r=10),
    )

    # ── Graphique 2 : Scatter Recency vs Frequency ──────────
    fig_scatter = px.scatter(
        df, x="recency", y="frequency",
        color="segment", color_discrete_map=SEGMENT_COLORS,
        size="monetary", size_max=25,
        hover_data=["full_name", "plan", "monetary"],
        title="Recency vs Frequency (taille = Monetary)",
        labels={"recency": "Recency (jours)", "frequency": "Frequency (écoutes)"},
    )
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF", title_font_size=14,
        xaxis=dict(gridcolor="#2D2D3F"), yaxis=dict(gridcolor="#2D2D3F"),
        legend=dict(font=dict(color="#9CA3AF")),
        margin=dict(t=40, b=10, l=10, r=10),
    )

    # ── Graphique 3 : Top 10 tracks ─────────────────────────
    top10 = df_tracks.head(10).sort_values("nb_ecoutes")
    fig_tracks = px.bar(
        top10, x="nb_ecoutes", y="title",
        orientation="h", color="genre",
        title="Top 10 tracks les plus écoutées",
        labels={"nb_ecoutes": "Écoutes", "title": ""},
    )
    fig_tracks.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF", title_font_size=14,
        xaxis=dict(gridcolor="#2D2D3F"), yaxis=dict(gridcolor="#2D2D3F"),
        showlegend=False,
        margin=dict(t=40, b=10, l=10, r=10),
    )

    # ── Graphique 4 : Genres enrichis Last.fm ───────────────
    genre_counts = df["genre_enrichi"].value_counts().reset_index()
    genre_counts.columns = ["genre", "count"]
    fig_genres = px.bar(
        genre_counts.head(8), x="genre", y="count",
        color="count", color_continuous_scale="Viridis",
        title="Genres préférés (enrichis via Last.fm)",
        labels={"genre": "Genre", "count": "Utilisateurs"},
    )
    fig_genres.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF", title_font_size=14,
        xaxis=dict(gridcolor="#2D2D3F"), yaxis=dict(gridcolor="#2D2D3F"),
        coloraxis_showscale=False,
        margin=dict(t=40, b=10, l=10, r=10),
    )

    # ── Graphique 5 : Écoutes dans le temps ─────────────────
    ecoutes_time = df_listens.groupby("month").size().reset_index(name="nb_ecoutes")
    fig_time = px.line(
        ecoutes_time, x="month", y="nb_ecoutes",
        title="Évolution des écoutes dans le temps",
        labels={"month": "Mois", "nb_ecoutes": "Écoutes"},
        markers=True,
    )
    fig_time.update_traces(line_color="#6C63FF", marker_color="#6C63FF")
    fig_time.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF", title_font_size=14,
        xaxis=dict(gridcolor="#2D2D3F"), yaxis=dict(gridcolor="#2D2D3F"),
        margin=dict(t=40, b=10, l=10, r=10),
    )

    # ── Table utilisateurs ───────────────────────────────────
    cols = ["full_name", "country", "plan", "segment", "recency", "frequency", "monetary", "genre_enrichi"]
    table = dash_table.DataTable(
        data=df[cols].to_dict("records"),
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in cols],
        style_table={"overflowX": "auto"},
        style_cell={"backgroundColor": "#1E1E2E", "color": "#FFFFFF", "border": "1px solid #2D2D3F", "padding": "8px", "fontSize": "13px"},
        style_header={"backgroundColor": "#2D2D3F", "color": "#9CA3AF", "fontWeight": "bold", "border": "1px solid #3D3D4F"},
        style_data_conditional=[
            {"if": {"filter_query": '{segment} = "Champion"'}, "color": "#6C63FF", "fontWeight": "bold"},
            {"if": {"filter_query": '{segment} = "Loyal"'}, "color": "#3ECFCF"},
            {"if": {"filter_query": '{segment} = "À risque"'}, "color": "#F97316"},
            {"if": {"filter_query": '{segment} = "Inactif"'}, "color": "#EF4444"},
        ],
        page_size=10,
        sort_action="native",
    )

    return kpis, fig_seg, fig_scatter, fig_tracks, fig_genres, fig_time, table


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    print("🚀 Dashboard disponible sur http://127.0.0.1:8050")
    app.run(debug=True)
    