import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_dashboard_equipo(data):

    equipo_raw = data["equipo"].copy()

    # =====================================
    # ESTILOS CSS - FILTROS FIJOS + MANTENIMIENTO DE LOS 3 PUNTOS (⋮)
    # =====================================

    st.markdown("""
    <style>

    /* 1. MANTENER VISIBLES Y ACCESIBLES LOS 3 PUNTOS Y EL MENÚ SUPERIOR */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 100000 !important;
        pointer-events: none !important; /* Permite hacer clic en los filtros debajo */
    }

    /* Activar eventos de clic únicamente para los 3 puntos y botones nativos */
    header[data-testid="stHeader"] * {
        pointer-events: auto !important;
    }

    /* 2. Margen superior mínimo del lienzo principal */
    [data-testid="stMainBlockContainer"] {
        padding-top: 0.5rem !important;
    }

    /* 3. Estilos y alineación centrada para métricas */
    div[data-testid="metric-container"] {
        text-align: center;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        justify-content: center;
    }

    div[data-testid="stMetricLabel"] {
        justify-content: center;
    }

    /* 4. REGLA STICKY PRINCIPAL: Mantiene la tarjeta de filtros fija arriba al 100% */
    div[data-testid="stVerticalBlock"] > div:has(div.filtro-tarjeta-fija) {
        position: sticky !important;
        top: 0px !important;
        z-index: 99999 !important;
        background-color: var(--background-color, #ffffff) !important;
        padding: 0px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
        margin-top: 0px !important;
    }

    /* Expander adaptativo (Soporta Light Mode y Dark Mode) */
    div[data-testid="stVerticalBlock"] > div:has(div.filtro-tarjeta-fija) [data-testid="stExpander"] {
        background-color: var(--secondary-background-color) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.08) !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # =====================================
    # NORMALIZAR EQUIPO
    # =====================================

    registros = []

    # DIRECCIÓN
    for i in range(1, len(equipo_raw)):
        nombre = equipo_raw.iloc[i, 0]
        cargo = equipo_raw.iloc[i, 1]
        vinculacion = equipo_raw.iloc[i, 2]

        if pd.notna(nombre):
            registros.append({
                "Área": "Dirección",
                "Nombre": nombre,
                "Cargo": cargo,
                "Vinculación": vinculacion
            })

    # DEFENSA ADMINISTRATIVA
    for i in range(1, len(equipo_raw)):
        nombre = equipo_raw.iloc[i, 3]
        cargo = equipo_raw.iloc[i, 4]
        vinculacion = equipo_raw.iloc[i, 5]

        if pd.notna(nombre):
            registros.append({
                "Área": "Defensa Administrativa",
                "Nombre": nombre,
                "Cargo": cargo,
                "Vinculación": vinculacion
            })

    # PREDIAL Y RESPONSABILIDAD
    for i in range(1, len(equipo_raw)):
        nombre = equipo_raw.iloc[i, 6]
        cargo = equipo_raw.iloc[i, 7]
        vinculacion = equipo_raw.iloc[i, 8]

        if pd.notna(nombre):
            registros.append({
                "Área": "Predial y Responsabilidad",
                "Nombre": nombre,
                "Cargo": cargo,
                "Vinculación": vinculacion
            })

    # CONTRATISTAS
    for i in range(1, len(equipo_raw)):
        nombre = equipo_raw.iloc[i, 9]
        vinculacion = equipo_raw.iloc[i, 10]

        if pd.notna(nombre):
            registros.append({
                "Área": "Contratistas",
                "Nombre": nombre,
                "Cargo": "Contratista",
                "Vinculación": vinculacion
            })

    df = pd.DataFrame(registros)

    # =====================================
    # 1. CONTENEDOR FIJO DE FILTROS (STICKY TOP 0)
    # =====================================

    with st.container():
        st.markdown('<div class="filtro-tarjeta-fija"></div>', unsafe_allow_html=True)

        with st.expander("🔎 Filtros Equipo", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                area = st.multiselect(
                    "Área",
                    sorted(
                        df["Área"]
                        .dropna()
                        .unique()
                        .tolist()
                    ),
                    key="eq_area"
                )

            with col_f2:
                cargo = st.multiselect(
                    "Cargo",
                    sorted(
                        df["Cargo"]
                        .astype(str)
                        .dropna()
                        .unique()
                        .tolist()
                    ),
                    key="eq_cargo"
                )

            with col_f3:
                vinculacion = st.multiselect(
                    "Vinculación",
                    sorted(
                        df["Vinculación"]
                        .astype(str)
                        .dropna()
                        .unique()
                        .tolist()
                    ),
                    key="eq_vinc"
                )

    # =====================================
    # FILTRADO
    # =====================================

    if area:
        df = df[df["Área"].isin(area)]

    if cargo:
        df = df[df["Cargo"].isin(cargo)]

    if vinculacion:
        df = df[df["Vinculación"].isin(vinculacion)]

    # =====================================
    # 2. TÍTULO DEL DASHBOARD
    # =====================================

    st.subheader("👥 Equipo de Trabajo")

    # =====================================
    # 3. METRICAS Y KPIs
    # =====================================

    total_personas = len(df)

    profesionales = df[
        df["Cargo"]
        .astype(str)
        .str.contains(
            "Profesional",
            case=False,
            na=False
        )
    ].shape[0]

    tecnologos = df[
        df["Cargo"]
        .astype(str)
        .str.contains(
            "Tecnólogo|Tecnico|Técnico",
            case=False,
            na=False
        )
    ].shape[0]

    aprendices = df[
        df["Cargo"]
        .astype(str)
        .str.contains(
            "Aprendiz",
            case=False,
            na=False
        )
    ].shape[0]

    contratistas = df[
        df["Área"] == "Contratistas"
    ].shape[0]

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "👥 Integrantes",
            total_personas
        )

    with col2:
        st.metric(
            "👔 Profesionales",
            profesionales
        )

    with col3:
        st.metric(
            "⚙️ Tecnólogos",
            tecnologos
        )

    with col4:
        st.metric(
            "🎓 Aprendices",
            aprendices
        )

    with col5:
        st.metric(
            "📑 Contratistas",
            contratistas
        )

    st.divider()

    # =====================================
    # PERSONAL POR ÁREA Y CARGO
    # =====================================

    col1, col2 = st.columns(2)

    with col1:
        area_df = (
            df["Área"]
            .value_counts()
            .reset_index()
        )
        area_df.columns = ["Área", "Cantidad"]

        fig = px.bar(
            area_df,
            x="Área",
            y="Cantidad",
            text="Cantidad",
            title="Personal por Área"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cargo_df = (
            df["Cargo"]
            .value_counts()
            .reset_index()
        )
        cargo_df.columns = ["Cargo", "Cantidad"]

        fig = px.bar(
            cargo_df,
            x="Cantidad",
            y="Cargo",
            orientation="h",
            title="Personal por Cargo"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =====================================
    # VINCULACIÓN
    # =====================================

    col3, col4 = st.columns(2)

    with col3:
        vinc_df = (
            df["Vinculación"]
            .value_counts()
            .reset_index()
        )
        vinc_df.columns = ["Vinculación", "Cantidad"]

        fig = px.pie(
            vinc_df,
            names="Vinculación",
            values="Cantidad",
            hole=0.5,
            title="Tipo de Vinculación"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        area_cargo = (
            df.groupby(["Área", "Cargo"])
            .size()
            .reset_index(name="Cantidad")
        )

        fig = px.bar(
            area_cargo,
            x="Área",
            y="Cantidad",
            color="Cargo",
            barmode="stack",
            title="Área vs Cargo"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =====================================
    # ÁREA VS VINCULACIÓN
    # =====================================

    col5, col6 = st.columns(2)

    with col5:
        area_vinc = (
            df.groupby(["Área", "Vinculación"])
            .size()
            .reset_index(name="Cantidad")
        )

        fig = px.bar(
            area_vinc,
            x="Área",
            y="Cantidad",
            color="Vinculación",
            title="Área vs Vinculación"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        fig = px.sunburst(
            df,
            path=["Área", "Cargo"],
            title="Composición del Equipo"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📋 Consulta Equipo")

    st.dataframe(
        df,
        use_container_width=True,
        height=650
    )