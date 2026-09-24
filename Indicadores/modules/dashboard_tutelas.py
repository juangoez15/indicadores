import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_dashboard_tutelas(data):
    """
    Renders the Legal Writs / Protection Actions (Tutelas) Dashboard in Streamlit.
    Processes the 'tutelas' dataset and visualizes KPIs, constitutional rights violated,
    assigned lawyers, corporate entities, projects, requested claims, and yearly trends.
    """

    # Safely retrieve tutelas dataframe
    tutelas_raw = data.get("tutelas", pd.DataFrame())

    if tutelas_raw is None or tutelas_raw.empty:
        st.warning("⚠️ No se encontraron datos para el módulo de Tutelas.")
        return

    tutelas = tutelas_raw.copy()

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
            font-size: 1.4rem !important;
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

    # Mapeo y verificación de columnas
    col_fecha = "Fecha de Solicitud (Radicado) (Radicado)" if "Fecha de Solicitud (Radicado) (Radicado)" in tutelas.columns else "Fecha de Solicitud"
    col_pretensiones = "Valor Total Pretensiones" if "Valor Total Pretensiones" in tutelas.columns else "Valor Pretensiones"
    col_abogado = "Abogado asignado" if "Abogado asignado" in tutelas.columns else None
    col_accion = "Acción" if "Acción" in tutelas.columns else None
    col_derecho = "Derecho Vulnerado" if "Derecho Vulnerado" in tutelas.columns else None
    col_empresa = "Empresa / Filial" if "Empresa / Filial" in tutelas.columns else None
    col_proyecto = "Proyecto" if "Proyecto" in tutelas.columns else None
    col_tema = "Tema / Subtemas" if "Tema / Subtemas" in tutelas.columns else None
    col_tipo = "Tipo de Solicitud" if "Tipo de Solicitud" in tutelas.columns else None

    # Normalización de fechas y años
    if col_fecha and col_fecha in tutelas.columns:
        tutelas["Fecha_dt"] = pd.to_datetime(tutelas[col_fecha], errors="coerce")
        tutelas["Año"] = tutelas["Fecha_dt"].dt.year
    else:
        tutelas["Año"] = pd.NA

    # Normalización de pretensiones monetarias
    if col_pretensiones and col_pretensiones in tutelas.columns:
        tutelas["Pretensiones_Num"] = pd.to_numeric(tutelas[col_pretensiones], errors="coerce").fillna(0)
    else:
        tutelas["Pretensiones_Num"] = 0.0

    # =====================================
    # FILTROS DINÁMICOS Y EN CASCADA (SIDEBAR)
    # =====================================

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Filtros Tutelas")

    df_temp = tutelas.copy()

    # 1. Filtro Año
    anios_disponibles = sorted(df_temp["Año"].dropna().astype(int).unique().tolist(), reverse=True)
    
    opcion_anio = st.sidebar.radio(
        "Modo de selección de Año:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_anio"
    )
    
    if opcion_anio == "Seleccionar varios" and anios_disponibles:
        anios_seleccionados = st.sidebar.multiselect(
            "Seleccione los Años:",
            options=anios_disponibles,
            default=anios_disponibles,
            key="tut_anio_multi"
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
        key="tut_modo_abogado"
    )

    if opcion_abogado == "Seleccionar varios" and abogados_disp:
        abogados_seleccionados = st.sidebar.multiselect(
            "Seleccione Abogados:",
            options=abogados_disp,
            default=abogados_disp,
            key="tut_abogado_multi"
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
        key="tut_modo_accion"
    )

    if opcion_accion == "Seleccionar varios" and acciones_disp:
        acciones_seleccionadas = st.sidebar.multiselect(
            "Seleccione Acciones:",
            options=acciones_disp,
            default=acciones_disp,
            key="tut_accion_multi"
        )
    else:
        acciones_seleccionadas = acciones_disp

    if col_accion and col_accion in df_temp.columns and acciones_seleccionadas:
        df_temp = df_temp[df_temp[col_accion].astype(str).isin(acciones_seleccionadas)]

    # 4. Filtro Derecho Vulnerado
    derechos_disp = (
        sorted(df_temp[col_derecho].dropna().astype(str).unique().tolist())
        if col_derecho and col_derecho in df_temp.columns
        else []
    )

    opcion_derecho = st.sidebar.radio(
        "Modo de selección de Derecho Vulnerado:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_derecho"
    )

    if opcion_derecho == "Seleccionar varios" and derechos_disp:
        derechos_seleccionados = st.sidebar.multiselect(
            "Seleccione Derechos Vulnerados:",
            options=derechos_disp,
            default=derechos_disp,
            key="tut_derecho_multi"
        )
    else:
        derechos_seleccionados = derechos_disp

    if col_derecho and col_derecho in df_temp.columns and derechos_seleccionados:
        df_temp = df_temp[df_temp[col_derecho].astype(str).isin(derechos_seleccionados)]

    # 5. Filtro Empresa / Filial
    empresas_disp = (
        sorted(df_temp[col_empresa].dropna().astype(str).unique().tolist())
        if col_empresa and col_empresa in df_temp.columns
        else []
    )

    opcion_empresa = st.sidebar.radio(
        "Modo de selección de Empresa / Filial:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_empresa"
    )

    if opcion_empresa == "Seleccionar varios" and empresas_disp:
        empresas_seleccionadas = st.sidebar.multiselect(
            "Seleccione Empresas / Filiales:",
            options=empresas_disp,
            default=empresas_disp,
            key="tut_empresa_multi"
        )
    else:
        empresas_seleccionadas = empresas_disp

    if col_empresa and col_empresa in df_temp.columns and empresas_seleccionadas:
        df_temp = df_temp[df_temp[col_empresa].astype(str).isin(empresas_seleccionadas)]

    # 6. Filtro Proyecto
    proyectos_disp = (
        sorted(df_temp[col_proyecto].dropna().astype(str).unique().tolist())
        if col_proyecto and col_proyecto in df_temp.columns
        else []
    )

    opcion_proyecto = st.sidebar.radio(
        "Modo de selección de Proyecto:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_proyecto"
    )

    if opcion_proyecto == "Seleccionar varios" and proyectos_disp:
        proyectos_seleccionados = st.sidebar.multiselect(
            "Seleccione Proyectos:",
            options=proyectos_disp,
            default=proyectos_disp,
            key="tut_proyecto_multi"
        )
    else:
        proyectos_seleccionados = proyectos_disp

    if col_proyecto and col_proyecto in df_temp.columns and proyectos_seleccionados:
        df_temp = df_temp[df_temp[col_proyecto].astype(str).isin(proyectos_seleccionados)]

    # 7. Filtro Tema / Subtemas
    temas_disp = (
        sorted(df_temp[col_tema].dropna().astype(str).unique().tolist())
        if col_tema and col_tema in df_temp.columns
        else []
    )

    opcion_tema = st.sidebar.radio(
        "Modo de selección de Tema / Subtemas:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_tema"
    )

    if opcion_tema == "Seleccionar varios" and temas_disp:
        temas_seleccionados = st.sidebar.multiselect(
            "Seleccione Temas / Subtemas:",
            options=temas_disp,
            default=temas_disp,
            key="tut_tema_multi"
        )
    else:
        temas_seleccionados = temas_disp

    if col_tema and col_tema in df_temp.columns and temas_seleccionados:
        df_temp = df_temp[df_temp[col_tema].astype(str).isin(temas_seleccionados)]

    # 8. Filtro Tipo de Solicitud
    tipos_disp = (
        sorted(df_temp[col_tipo].dropna().astype(str).unique().tolist())
        if col_tipo and col_tipo in df_temp.columns
        else []
    )

    opcion_tipo = st.sidebar.radio(
        "Modo de selección de Tipo de Solicitud:",
        ["Todos", "Seleccionar varios"],
        key="tut_modo_tipo"
    )

    if opcion_tipo == "Seleccionar varios" and tipos_disp:
        tipos_seleccionados = st.sidebar.multiselect(
            "Seleccione Tipos de Solicitud:",
            options=tipos_disp,
            default=tipos_disp,
            key="tut_tipo_multi"
        )
    else:
        tipos_seleccionados = tipos_disp

    if col_tipo and col_tipo in df_temp.columns and tipos_seleccionados:
        df_temp = df_temp[df_temp[col_tipo].astype(str).isin(tipos_seleccionados)]

    # DataFrame filtrado final
    df = df_temp.copy()

    # =====================================
    # CABECERA Y KPIS
    # =====================================

    st.subheader("⚖️ Dashboard de Tutelas")

    if df.empty:
        st.info("No hay información que coincida con los filtros seleccionados.")
        return

    total_tutelas = len(df)
    total_pretensiones = df["Pretensiones_Num"].sum() if not df.empty else 0
    total_abogados = df[col_abogado].nunique() if col_abogado and not df.empty else 0
    total_empresas = df[col_empresa].nunique() if col_empresa and not df.empty else 0
    total_derechos = df[col_derecho].nunique() if col_derecho and not df.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("⚖️ Tutelas", f"{total_tutelas:,}".replace(",", "."))
    c2.metric("💰 Pretensiones", formatear_moneda(total_pretensiones))
    c3.metric("👨‍⚖️ Abogados", f"{total_abogados:,}".replace(",", "."))
    c4.metric("🏢 Empresas", f"{total_empresas:,}".replace(",", "."))
    c5.metric("📄 Derechos", f"{total_derechos:,}".replace(",", "."))

    st.divider()

    # Función auxiliar reutilizable para gráficos horizontales
    def crear_barras_h(dataframe, x_col, y_col, titulo, limit=15):
        conteo = (
            dataframe[y_col]
            .fillna("Sin Definir")
            .value_counts()
            .head(limit)
            .reset_index()
        )
        conteo.columns = [y_col, x_col]
        conteo = conteo.sort_values(x_col, ascending=True)

        fig = px.bar(
            conteo,
            x=x_col,
            y=y_col,
            orientation="h",
            title=titulo,
            text=x_col,
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title="",
            margin=dict(l=20, r=60, t=50, b=30),
        )
        return fig

    # =====================================
    # FILA 1: ACCIÓN Y DERECHO
    # =====================================

    col1, col2 = st.columns(2)
    with col1:
        if col_accion and not df.empty:
            st.plotly_chart(
                crear_barras_h(df, "Cantidad", col_accion, "Tutelas por Acción"),
                use_container_width=True,
            )
        else:
            st.info("Información de Acción no disponible.")

    with col2:
        if col_derecho and not df.empty:
            st.plotly_chart(
                crear_barras_h(
                    df, "Cantidad", col_derecho, "Derechos Vulnerados (Top 15)"
                ),
                use_container_width=True,
            )
        else:
            st.info("Información de Derecho Vulnerado no disponible.")

    st.divider()

    # =====================================
    # FILA 2: ABOGADO Y EMPRESA
    # =====================================

    col3, col4 = st.columns(2)
    with col3:
        if col_abogado and not df.empty:
            st.plotly_chart(
                crear_barras_h(
                    df, "Cantidad", col_abogado, "Tutelas por Abogado (Top 15)"
                ),
                use_container_width=True,
            )
        else:
            st.info("Información de Abogado Asignado no disponible.")

    with col4:
        if col_empresa and not df.empty:
            emp_df = (
                df[col_empresa]
                .fillna("Sin Empresa")
                .value_counts()
                .head(15)
                .reset_index()
            )
            emp_df.columns = ["Empresa", "Cantidad"]
            emp_df = emp_df.sort_values("Cantidad", ascending=True)

            fig_emp = px.bar(
                emp_df,
                x="Cantidad",
                y="Empresa",
                orientation="h",
                text="Cantidad",
                title="Tutelas por Empresa / Filial",
            )
            fig_emp.update_traces(textposition="outside", cliponaxis=False)
            fig_emp.update_layout(
                xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=60, t=50, b=30)
            )
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.info("Información de Empresa / Filial no disponible.")

    st.divider()

    # =====================================
    # FILA 3: PROYECTO Y TEMA
    # =====================================

    col5, col6 = st.columns(2)
    with col5:
        if col_proyecto and not df.empty:
            st.plotly_chart(
                crear_barras_h(
                    df, "Cantidad", col_proyecto, "Tutelas por Proyecto (Top 15)"
                ),
                use_container_width=True,
            )
        else:
            st.info("Información de Proyecto no disponible.")

    with col6:
        if col_tema and not df.empty:
            st.plotly_chart(
                crear_barras_h(
                    df, "Cantidad", col_tema, "Tutelas por Tema/Subtemas (Top 15)"
                ),
                use_container_width=True,
            )
        else:
            st.info("Información de Tema / Subtemas no disponible.")

    st.divider()

    # =====================================
    # FILA 4: TIPO SOLICITUD Y AÑO
    # =====================================

    col7, col8 = st.columns(2)
    with col7:
        if col_tipo and not df.empty:
            tipo_df = (
                df[col_tipo]
                .fillna("Sin Tipo")
                .value_counts()
                .reset_index()
            )
            tipo_df.columns = ["Tipo", "Cantidad"]

            fig_pie = px.pie(
                tipo_df,
                names="Tipo",
                values="Cantidad",
                title="Tutelas por Tipo de Solicitud",
                hole=0.4,
            )
            fig_pie.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Información de Tipo de Solicitud no disponible.")

    with col8:
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

            fig_line = px.line(
                anio_df,
                x="Año",
                y="Cantidad",
                markers=True,
                title="Evolución de Tutelas por Año",
            )
            fig_line.update_xaxes(type="category")
            fig_line.update_layout(hovermode="x unified", yaxis_title="Cantidad de Tutelas")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Evolución temporal no disponible (faltan fechas válidas).")

    st.divider()

    # =====================================
    # FILA 5: PRETENSIONES
    # =====================================

    col9, col10 = st.columns(2)
    with col9:
        if col_empresa and not df.empty:
            p_emp = (
                df.groupby(col_empresa)["Pretensiones_Num"]
                .sum()
                .reset_index()
                .sort_values("Pretensiones_Num", ascending=False)
                .head(15)
                .sort_values("Pretensiones_Num", ascending=True)
            )
            p_emp["Texto"] = p_emp["Pretensiones_Num"].apply(formatear_moneda)

            fig_pe = px.bar(
                p_emp,
                x="Pretensiones_Num",
                y=col_empresa,
                orientation="h",
                text="Texto",
                title="Pretensiones por Empresa",
            )
            fig_pe.update_traces(textposition="outside", cliponaxis=False)
            fig_pe.update_layout(
                xaxis_title="Valor Pretensiones", yaxis_title="", margin=dict(l=20, r=100, t=50, b=30)
            )
            st.plotly_chart(fig_pe, use_container_width=True)

    with col10:
        if col_abogado and not df.empty:
            p_abog = (
                df.groupby(col_abogado)["Pretensiones_Num"]
                .sum()
                .reset_index()
                .sort_values("Pretensiones_Num", ascending=False)
                .head(15)
                .sort_values("Pretensiones_Num", ascending=True)
            )
            p_abog["Texto"] = p_abog["Pretensiones_Num"].apply(formatear_moneda)

            fig_pa = px.bar(
                p_abog,
                x="Pretensiones_Num",
                y=col_abogado,
                orientation="h",
                text="Texto",
                title="Pretensiones por Abogado (Top 15)",
            )
            fig_pa.update_traces(textposition="outside", cliponaxis=False)
            fig_pa.update_layout(
                xaxis_title="Valor Pretensiones", yaxis_title="", margin=dict(l=20, r=100, t=50, b=30)
            )
            st.plotly_chart(fig_pa, use_container_width=True)

    st.divider()

    # =====================================
    # TABLA FINAL DE DETALLE
    # =====================================

    st.subheader("📋 Consulta General de Tutelas")

    columnas_mostrar = [
        c
        for c in [
            col_fecha,
            col_accion,
            col_derecho,
            col_abogado,
            col_empresa,
            col_proyecto,
            col_tema,
            col_tipo,
            col_pretensiones,
        ]
        if c and c in df.columns
    ]

    df_display = df[columnas_mostrar].copy() if columnas_mostrar else df.copy()

    if col_pretensiones and col_pretensiones in df_display.columns:
        df_display[col_pretensiones] = df_display[col_pretensiones].apply(formatear_cop_exacto)

    st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)