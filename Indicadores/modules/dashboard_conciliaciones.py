import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_dashboard_conciliaciones(data):

    conciliaciones = data["conciliaciones"].copy()

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
    # FUNCIONES AUXILIARES
    # =====================================

    def formatear_moneda(valor):
        if valor >= 1_000_000_000_000:
            return f"{valor/1_000_000_000_000:,.2f} Billones"
        elif valor >= 1_000_000_000:
            return f"{valor/1_000_000_000:,.2f} Mil M"
        elif valor >= 1_000_000:
            return f"{valor/1_000_000:,.2f} M"
        return f"${valor:,.0f}"

    # =====================================
    # PREPARACIÓN DE DATOS
    # =====================================

    conciliaciones[
        "Fecha de Solicitud (Radicado) (Radicado)"
    ] = pd.to_datetime(
        conciliaciones["Fecha de Solicitud (Radicado) (Radicado)"],
        errors="coerce"
    )

    conciliaciones["Año"] = conciliaciones[
        "Fecha de Solicitud (Radicado) (Radicado)"
    ].dt.year

    conciliaciones["Mes"] = conciliaciones[
        "Fecha de Solicitud (Radicado) (Radicado)"
    ].dt.month

    # =====================================
    # 1. CONTENEDOR FIJO DE FILTROS (STICKY TOP 0)
    # =====================================

    with st.container():
        st.markdown('<div class="filtro-tarjeta-fija"></div>', unsafe_allow_html=True)

        with st.expander("🔎 Filtros Conciliaciones", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                año = st.multiselect(
                    "Año",
                    sorted(
                        conciliaciones["Año"]
                        .dropna()
                        .astype(int)
                        .unique()
                        .tolist()
                    ),
                    key="conc_anio"
                )

                etapa = st.multiselect(
                    "Etapa",
                    sorted(
                        conciliaciones["Etapa"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="conc_etapa"
                )

            with col_f2:
                abogado = st.multiselect(
                    "Abogado",
                    sorted(
                        conciliaciones["Abogado Asignado"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="conc_abogado"
                )

                proyecto = st.multiselect(
                    "Proyecto",
                    sorted(
                        conciliaciones["Proyecto"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="conc_proyecto"
                )

            with col_f3:
                empresa = st.multiselect(
                    "Empresa / Filial ",
                    sorted(
                        conciliaciones["Empresa / Filial "]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="conc_empresa"
                )

                tema = st.multiselect(
                    "Tema / Subtemas",
                    sorted(
                        conciliaciones["Tema / Subtemas"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    ),
                    key="conc_tema"
                )

    # =====================================
    # LÓGICA DE FILTRADO
    # =====================================

    df = conciliaciones.copy()

    if año:
        df = df[df["Año"].isin(año)]

    if abogado:
        df = df[df["Abogado Asignado"].isin(abogado)]

    if empresa:
        df = df[df["Empresa / Filial "].isin(empresa)]

    if etapa:
        df = df[df["Etapa"].isin(etapa)]

    if proyecto:
        df = df[df["Proyecto"].isin(proyecto)]

    if tema:
        df = df[df["Tema / Subtemas"].isin(tema)]

    # =====================================
    # 2. TÍTULO DEL DASHBOARD
    # =====================================

    st.subheader("🤝 Dashboard de Conciliaciones")

    # =====================================
    # 3. METRICAS Y KPIs
    # =====================================

    total_conciliaciones = len(df)

    total_pretensiones = (
        pd.to_numeric(
            df["Valor Total Pretensiones"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    total_abogados = df["Abogado Asignado"].nunique()
    total_empresas = df["Empresa / Filial "].nunique()
    total_temas = df["Tema / Subtemas"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🤝 Conciliaciones", f"{total_conciliaciones:,}")

    with col2:
        st.metric("💰 Pretensiones", formatear_moneda(total_pretensiones))

    with col3:
        st.metric("👨‍⚖️ Abogados", total_abogados)

    with col4:
        st.metric("🏢 Empresas", total_empresas)

    with col5:
        st.metric("📄 Temas", total_temas)

    st.divider()

    # =====================================
    # GRÁFICOS INTERACTIVOS (FILAS 1 A 5)
    # =====================================

    col1, col2 = st.columns(2)

    with col1:
        abogado_df = (
            df["Abogado Asignado"]
            .fillna("Sin Asignar")
            .value_counts()
            .head(15)
            .reset_index()
        )
        abogado_df.columns = ["Abogado", "Cantidad"]
        fig = px.bar(
            abogado_df,
            x="Cantidad",
            y="Abogado",
            orientation="h",
            title="Conciliaciones por Abogado"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        empresa_df = (
            df["Empresa / Filial "]
            .fillna("Sin Empresa")
            .value_counts()
            .reset_index()
        )
        empresa_df.columns = ["Empresa", "Cantidad"]
        fig = px.bar(
            empresa_df,
            x="Empresa",
            y="Cantidad",
            title="Conciliaciones por Empresa"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        proyecto_df = (
            df["Proyecto"]
            .fillna("Sin Proyecto")
            .value_counts()
            .head(15)
            .reset_index()
        )
        proyecto_df.columns = ["Proyecto", "Cantidad"]
        fig = px.bar(
            proyecto_df,
            x="Cantidad",
            y="Proyecto",
            orientation="h",
            title="Conciliaciones por Proyecto"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        etapa_df = (
            df["Etapa"]
            .fillna("Sin Etapa")
            .value_counts()
            .reset_index()
        )
        etapa_df.columns = ["Etapa", "Cantidad"]
        fig = px.pie(
            etapa_df,
            names="Etapa",
            values="Cantidad",
            title="Conciliaciones por Etapa",
            hole=0.5
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col5, col6 = st.columns(2)

    with col5:
        tema_df = (
            df["Tema / Subtemas"]
            .fillna("Sin Tema")
            .value_counts()
            .head(15)
            .reset_index()
        )
        tema_df.columns = ["Tema", "Cantidad"]
        fig = px.bar(
            tema_df,
            x="Cantidad",
            y="Tema",
            orientation="h",
            title="Conciliaciones por Tema/Subtemas"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        pret_tema = (
            df.groupby("Tema / Subtemas")["Valor Total Pretensiones"]
            .sum()
            .reset_index()
            .sort_values("Valor Total Pretensiones", ascending=False)
            .head(15)
        )
        fig = px.bar(
            pret_tema,
            x="Valor Total Pretensiones",
            y="Tema / Subtemas",
            orientation="h",
            title="Pretensiones por Tema/Subtemas"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col7, col8 = st.columns(2)

    with col7:
        anio_df = (
            df["Año"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        anio_df.columns = ["Año", "Cantidad"]
        fig = px.line(
            anio_df,
            x="Año",
            y="Cantidad",
            markers=True,
            title="Conciliaciones por Año"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col8:
        mes_df = (
            df["Mes"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        mes_df.columns = ["Mes", "Cantidad"]
        fig = px.bar(
            mes_df,
            x="Mes",
            y="Cantidad",
            title="Conciliaciones por Mes"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col9, col10 = st.columns(2)

    with col9:
        pret_empresa = (
            df.groupby("Empresa / Filial ")["Valor Total Pretensiones"]
            .sum()
            .reset_index()
            .sort_values("Valor Total Pretensiones", ascending=False)
        )
        fig = px.bar(
            pret_empresa,
            x="Empresa / Filial ",
            y="Valor Total Pretensiones",
            title="Pretensiones por Empresa"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col10:
        pret_abogado = (
            df.groupby("Abogado Asignado")["Valor Total Pretensiones"]
            .sum()
            .reset_index()
            .sort_values("Valor Total Pretensiones", ascending=False)
            .head(15)
        )
        fig = px.bar(
            pret_abogado,
            x="Valor Total Pretensiones",
            y="Abogado Asignado",
            orientation="h",
            title="Pretensiones por Abogado"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📋 Consulta de Conciliaciones")
    st.dataframe(df, use_container_width=True, height=650)
