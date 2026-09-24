import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_dashboard_sentencias(data):
    """
    Renders the Legal Sentences Dashboard in Streamlit.
    Processes the 'sentencias' dataset and visualizes KPIs, decision outcomes,
    actions, assigned lawyers, amounts (cuantía), and yearly trends.
    """

    # Safely retrieve sentencias dataframe
    sentencias_raw = data.get("sentencias", pd.DataFrame())

    if sentencias_raw is None or sentencias_raw.empty:
        st.warning("⚠️ No hay datos disponibles para el módulo de Sentencias.")
        return

    sentencias = sentencias_raw.copy()

    # =====================================
    # ESTILOS METRICAS
    # =====================================

    st.markdown(
        """
        <style>
        div[data-testid="metric-container"] {
            text-align: center;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            justify-content: center;
        }
        div[data-testid="stMetricLabel"] {
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =====================================
    # FUNCIONES AUXILIARES DE FORMATO
    # =====================================

    def formatear_moneda(valor):
        if pd.isna(valor) or valor == 0:
            return "$0"
        if valor >= 1_000_000_000_000:
            return f"${valor / 1_000_000_000_000:,.2f} Billones"
        elif valor >= 1_000_000_000:
            return f"${valor / 1_000_000_000:,.2f} Mil M"
        elif valor >= 1_000_000:
            return f"${valor / 1_000_000:,.2f} M"
        return f"${valor:,.0f}"

    def formatear_cop_exacto(val):
        """Formatea dinero estilo COP con separadores habituales."""
        if pd.isna(val) or val == 0:
            return "$ 0,00"
        return f"$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # =====================================
    # PREPARACIÓN Y LIMPIEZA DE DATOS
    # =====================================

    # Normalización de nombres de columnas frecuentes
    col_fecha = "Fecha Providencia" if "Fecha Providencia" in sentencias.columns else None
    col_cuantia = "Cuantía" if "Cuantía" in sentencias.columns else "Valor Pretensiones"
    col_abogado = (
        "Abogado asignado (Radicado) (Radicado)"
        if "Abogado asignado (Radicado) (Radicado)" in sentencias.columns
        else ("Abogado asignado" if "Abogado asignado" in sentencias.columns else None)
    )
    col_accion = (
        "Acción (Demanda) (Demanda)"
        if "Acción (Demanda) (Demanda)" in sentencias.columns
        else ("Acción" if "Acción" in sentencias.columns else None)
    )
    col_despacho = (
        "Despacho Judicial (Demanda) (Demanda)"
        if "Despacho Judicial (Demanda) (Demanda)" in sentencias.columns
        else ("Despacho Judicial" if "Despacho Judicial" in sentencias.columns else None)
    )
    col_instancia = "Instancia" if "Instancia" in sentencias.columns else None
    col_decision = "Sentido de la Decisión" if "Sentido de la Decisión" in sentencias.columns else None
    col_providencia = "Providencia" if "Providencia" in sentencias.columns else None

    # Procesar Fecha y Año
    if col_fecha and col_fecha in sentencias.columns:
        sentencias["Fecha_dt"] = pd.to_datetime(sentencias[col_fecha], errors="coerce")
        sentencias["Año"] = sentencias["Fecha_dt"].dt.year
    else:
        sentencias["Año"] = pd.NA

    # Procesar Cuantía
    if col_cuantia and col_cuantia in sentencias.columns:
        sentencias["Cuantía_Num"] = pd.to_numeric(sentencias[col_cuantia], errors="coerce").fillna(0)
    else:
        sentencias["Cuantía_Num"] = 0.0

    # =====================================
    # FILTROS DINÁMICOS Y EN CASCADA (SIDEBAR)
    # =====================================

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Filtros Sentencias")

    df_temp = sentencias.copy()

    # 1. Filtro Año
    anios_disponibles = sorted(df_temp["Año"].dropna().astype(int).unique().tolist(), reverse=True)
    
    opcion_anio = st.sidebar.radio(
        "Modo de selección de Año:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_anio"
    )
    
    if opcion_anio == "Seleccionar varios" and anios_disponibles:
        anios_seleccionados = st.sidebar.multiselect(
            "Seleccione los Años:",
            options=anios_disponibles,
            default=anios_disponibles,
            key="sen_anio_multi"
        )
    else:
        anios_seleccionados = anios_disponibles

    if "Año" in df_temp.columns and anios_seleccionados:
        df_temp = df_temp[df_temp["Año"].isin(anios_seleccionados)]

    # 2. Filtro Abogado
    abogados_disp = (
        sorted(df_temp[col_abogado].dropna().astype(str).unique().tolist())
        if col_abogado and col_abogado in df_temp.columns
        else []
    )
    
    opcion_abogado = st.sidebar.radio(
        "Modo de selección de Abogado:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_abogado"
    )

    if opcion_abogado == "Seleccionar varios" and abogados_disp:
        abogados_seleccionados = st.sidebar.multiselect(
            "Seleccione Abogados:",
            options=abogados_disp,
            default=abogados_disp,
            key="sen_abogado_multi"
        )
    else:
        abogados_seleccionados = abogados_disp

    if col_abogado and col_abogado in df_temp.columns and abogados_seleccionados:
        df_temp = df_temp[df_temp[col_abogado].astype(str).isin(abogados_seleccionados)]

    # 3. Filtro Acción
    acciones_disp = (
        sorted(df_temp[col_accion].dropna().astype(str).unique().tolist())
        if col_accion and col_accion in df_temp.columns
        else []
    )

    opcion_accion = st.sidebar.radio(
        "Modo de selección de Acción:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_accion"
    )

    if opcion_accion == "Seleccionar varios" and acciones_disp:
        acciones_seleccionadas = st.sidebar.multiselect(
            "Seleccione Acciones:",
            options=acciones_disp,
            default=acciones_disp,
            key="sen_accion_multi"
        )
    else:
        acciones_seleccionadas = acciones_disp

    if col_accion and col_accion in df_temp.columns and acciones_seleccionadas:
        df_temp = df_temp[df_temp[col_accion].astype(str).isin(acciones_seleccionadas)]

    # 4. Filtro Despacho Judicial
    despachos_disp = (
        sorted(df_temp[col_despacho].dropna().astype(str).unique().tolist())
        if col_despacho and col_despacho in df_temp.columns
        else []
    )

    opcion_despacho = st.sidebar.radio(
        "Modo de selección de Despacho:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_despacho"
    )

    if opcion_despacho == "Seleccionar varios" and despachos_disp:
        despachos_seleccionados = st.sidebar.multiselect(
            "Seleccione Despachos:",
            options=despachos_disp,
            default=despachos_disp,
            key="sen_despacho_multi"
        )
    else:
        despachos_seleccionados = despachos_disp

    if col_despacho and col_despacho in df_temp.columns and despachos_seleccionados:
        df_temp = df_temp[df_temp[col_despacho].astype(str).isin(despachos_seleccionados)]

    # 5. Filtro Instancia
    instancias_disp = (
        sorted(df_temp[col_instancia].dropna().astype(str).unique().tolist())
        if col_instancia and col_instancia in df_temp.columns
        else []
    )

    opcion_instancia = st.sidebar.radio(
        "Modo de selección de Instancia:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_instancia"
    )

    if opcion_instancia == "Seleccionar varios" and instancias_disp:
        instancias_seleccionadas = st.sidebar.multiselect(
            "Seleccione Instancias:",
            options=instancias_disp,
            default=instancias_disp,
            key="sen_instancia_multi"
        )
    else:
        instancias_seleccionadas = instancias_disp

    if col_instancia and col_instancia in df_temp.columns and instancias_seleccionadas:
        df_temp = df_temp[df_temp[col_instancia].astype(str).isin(instancias_seleccionadas)]

    # 6. Filtro Sentido de la Decisión
    decisiones_disp = (
        sorted(df_temp[col_decision].dropna().astype(str).unique().tolist())
        if col_decision and col_decision in df_temp.columns
        else []
    )

    opcion_decision = st.sidebar.radio(
        "Modo de selección de Sentido de Decisión:",
        ["Todos", "Seleccionar varios"],
        key="sen_modo_decision"
    )

    if opcion_decision == "Seleccionar varios" and decisiones_disp:
        decisiones_seleccionadas = st.sidebar.multiselect(
            "Seleccione Decisiones:",
            options=decisiones_disp,
            default=decisiones_disp,
            key="sen_decision_multi"
        )
    else:
        decisiones_seleccionadas = decisiones_disp

    if col_decision and col_decision in df_temp.columns and decisiones_seleccionadas:
        df_temp = df_temp[df_temp[col_decision].astype(str).isin(decisiones_seleccionadas)]

    # DataFrame final completamente filtrado
    df = df_temp.copy()

    # =====================================
    # CABECERA Y KPIS
    # =====================================

    st.subheader("🏆 Dashboard de Sentencias")

    total_sentencias = len(df)
    total_cuantia = df["Cuantía_Num"].sum() if not df.empty else 0
    total_abogados = df[col_abogado].nunique() if col_abogado and not df.empty else 0
    total_acciones = df[col_accion].nunique() if col_accion and not df.empty else 0
    total_decisiones = df[col_decision].nunique() if col_decision and not df.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🏆 Total Sentencias", f"{total_sentencias:,}".replace(",", "."))

    with col2:
        st.metric("💰 Cuantía Total", formatear_moneda(total_cuantia))

    with col3:
        st.metric("👨‍⚖️ Abogados", f"{total_abogados:,}".replace(",", "."))

    with col4:
        st.metric("⚖️ Acciones", f"{total_acciones:,}".replace(",", "."))

    with col5:
        st.metric("📄 Decisiones", f"{total_decisiones:,}".replace(",", "."))

    st.divider()

    # =====================================
    # FILA 1: DECISIÓN Y ACCIÓN
    # =====================================

    col1, col2 = st.columns(2)

    with col1:
        if col_decision and not df.empty:
            decision_df = (
                df[col_decision]
                .fillna("Sin Clasificar")
                .value_counts()
                .reset_index()
            )
            decision_df.columns = ["Decision", "Cantidad"]
            decision_df = decision_df.sort_values("Cantidad", ascending=True)

            fig = px.bar(
                decision_df,
                x="Cantidad",
                y="Decision",
                orientation="h",
                text="Cantidad",
                title="Sentencias por Sentido de Decisión",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Información de Sentido de Decisión no disponible.")

    with col2:
        if col_accion and not df.empty:
            accion_df = (
                df[col_accion]
                .fillna("Sin Acción")
                .value_counts()
                .head(15)
                .reset_index()
            )
            accion_df.columns = ["Acción", "Cantidad"]
            accion_df = accion_df.sort_values("Cantidad", ascending=True)

            fig = px.bar(
                accion_df,
                x="Cantidad",
                y="Acción",
                orientation="h",
                text="Cantidad",
                title="Top 15 Sentencias por Acción",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Información de Acción / Medio de Control no disponible.")

    st.divider()

    # =====================================
    # FILA 2: ABOGADO Y DESPACHO
    # =====================================

    col3, col4 = st.columns(2)

    with col3:
        if col_abogado and not df.empty:
            abogado_df = (
                df[col_abogado]
                .fillna("Sin Asignar")
                .value_counts()
                .head(15)
                .reset_index()
            )
            abogado_df.columns = ["Abogado", "Cantidad"]
            abogado_df = abogado_df.sort_values("Cantidad", ascending=True)

            fig = px.bar(
                abogado_df,
                x="Cantidad",
                y="Abogado",
                orientation="h",
                text="Cantidad",
                title="Top 15 Sentencias por Abogado",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Información de Abogado Asignado no disponible.")

    with col4:
        if col_despacho and not df.empty:
            despacho_df = (
                df[col_despacho]
                .fillna("Sin Despacho")
                .value_counts()
                .head(15)
                .reset_index()
            )
            despacho_df.columns = ["Despacho", "Cantidad"]
            despacho_df = despacho_df.sort_values("Cantidad", ascending=True)

            fig = px.bar(
                despacho_df,
                x="Cantidad",
                y="Despacho",
                orientation="h",
                text="Cantidad",
                title="Top 15 Sentencias por Despacho Judicial",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Información de Despacho Judicial no disponible.")

    st.divider()

    # =====================================
    # FILA 3: INSTANCIA Y EVOLUCIÓN TEMPORAL
    # =====================================

    col5, col6 = st.columns(2)

    with col5:
        if col_instancia and not df.empty:
            instancia_df = (
                df[col_instancia]
                .fillna("Sin Clasificar")
                .value_counts()
                .reset_index()
            )
            instancia_df.columns = ["Instancia", "Cantidad"]

            fig = px.pie(
                instancia_df,
                names="Instancia",
                values="Cantidad",
                title="Distribución por Instancia",
                hole=0.45,
            )
            fig.update_traces(textinfo="percent+value")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Información de Instancia no disponible.")

    with col6:
        if "Año" in df.columns and df["Año"].notna().any():
            anio_df = (
                df["Año"]
                .dropna()
                .astype(int)
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
                title="Evolución de Sentencias por Año",
            )
            fig.update_xaxes(type="category")
            fig.update_layout(hovermode="x unified", yaxis_title="Cantidad de Sentencias")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Evolución temporal no disponible (faltan fechas válidas).")

    st.divider()

    # =====================================
    # FILA 4: CUANTÍAS
    # =====================================

    col7, col8 = st.columns(2)

    with col7:
        if col_accion and not df.empty:
            cuantia_accion = (
                df.groupby(col_accion)["Cuantía_Num"]
                .sum()
                .reset_index()
                .sort_values("Cuantía_Num", ascending=False)
                .head(15)
                .sort_values("Cuantía_Num", ascending=True)
            )
            cuantia_accion["Formato_Texto"] = cuantia_accion["Cuantía_Num"].apply(formatear_moneda)

            fig = px.bar(
                cuantia_accion,
                x="Cuantía_Num",
                y=col_accion,
                orientation="h",
                text="Formato_Texto",
                title="Top 15 Cuantías por Acción",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Valor Cuantía", yaxis_title="", margin=dict(l=20, r=100, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col8:
        if col_abogado and not df.empty:
            cuantia_abogado = (
                df.groupby(col_abogado)["Cuantía_Num"]
                .sum()
                .reset_index()
                .sort_values("Cuantía_Num", ascending=False)
                .head(15)
                .sort_values("Cuantía_Num", ascending=True)
            )
            cuantia_abogado["Formato_Texto"] = cuantia_abogado["Cuantía_Num"].apply(formatear_moneda)

            fig = px.bar(
                cuantia_abogado,
                x="Cuantía_Num",
                y=col_abogado,
                orientation="h",
                text="Formato_Texto",
                title="Top 15 Cuantías por Abogado",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Valor Cuantía", yaxis_title="", margin=dict(l=20, r=100, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =====================================
    # FILA 5: PROVIDENCIA Y CONSULTA FINAL
    # =====================================

    col9, col10 = st.columns(2)

    with col9:
        if col_providencia and not df.empty:
            providencia_df = (
                df[col_providencia]
                .fillna("Sin Providencia")
                .value_counts()
                .head(15)
                .reset_index()
            )
            providencia_df.columns = ["Providencia", "Cantidad"]
            providencia_df = providencia_df.sort_values("Cantidad", ascending=True)

            fig = px.bar(
                providencia_df,
                x="Cantidad",
                y="Providencia",
                orientation="h",
                text="Cantidad",
                title="Top Tipos de Providencia",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col10:
        if col_decision and not df.empty:
            decision_pie = (
                df[col_decision]
                .fillna("Sin Clasificar")
                .value_counts()
                .reset_index()
            )
            decision_pie.columns = ["Decision", "Cantidad"]

            fig = px.pie(
                decision_pie,
                names="Decision",
                values="Cantidad",
                title="Proporción General de Decisiones",
                hole=0.4,
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =====================================
    # TABLA FINAL DE DETALLE
    # =====================================

    st.subheader("📋 Consulta General de Sentencias")

    columnas_mostrar = [
        c
        for c in [
            col_fecha,
            col_decision,
            col_accion,
            col_abogado,
            col_despacho,
            col_instancia,
            col_cuantia,
        ]
        if c and c in df.columns
    ]

    df_display = df[columnas_mostrar].copy() if columnas_mostrar else df.copy()

    if col_cuantia and col_cuantia in df_display.columns:
        df_display[col_cuantia] = df_display[col_cuantia].apply(formatear_cop_exacto)

    st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)