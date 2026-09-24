import streamlit as st
import pandas as pd
import plotly.express as px


def mostrar_dashboard_procesos(data):

    # Trabajar con la hoja correcta o el DataFrame de procesos
    if isinstance(data, dict):
        procesos = data.get("procesos", pd.DataFrame()).copy()
    else:
        procesos = data.copy()

    if procesos.empty:
        st.warning("No hay datos de procesos disponibles.")
        return

    # Limpiar espacios adicionales alrededor de las columnas
    procesos.columns = procesos.columns.astype(str).str.strip()

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

    def formatear_pretensiones(valor):
        if valor >= 1_000_000_000_000:
            return f"${valor / 1_000_000_000_000:,.2f} Billones"
        elif valor >= 1_000_000_000:
            return f"${valor / 1_000_000_000:,.2f} Mil M"
        elif valor >= 1_000_000:
            return f"${valor / 1_000_000:,.2f} M"
        return f"${valor:,.0f}"

    def formatear_moneda_tabla(valor):
        if pd.isna(valor) or valor == 0:
            return "$ -"
        return f"$ {valor:,.2f}"

    # ==========================
    # MANEJO SEGURO DE FECHA Y AÑO
    # ==========================
    col_fecha = None
    if "Fecha de Solicitud" in procesos.columns:
        col_fecha = "Fecha de Solicitud"
    elif "Fecha creación" in procesos.columns:
        col_fecha = "Fecha creación"

    if col_fecha:
        procesos[col_fecha] = pd.to_datetime(procesos[col_fecha], errors="coerce")
        procesos["Año"] = procesos[col_fecha].dt.year
    else:
        procesos["Año"] = None

    # =====================================
    # 1. CONTENEDOR FIJO DE FILTROS (STICKY TOP 0)
    # =====================================

    with st.container():
        st.markdown('<div class="filtro-tarjeta-fija"></div>', unsafe_allow_html=True)

        with st.expander("🔎 Filtros Procesos", expanded=True):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)

            with col_f1:
                años_disponibles = sorted(procesos["Año"].dropna().astype(int).unique().tolist()) if "Año" in procesos.columns and procesos["Año"].notna().any() else []
                año = st.multiselect("Año", años_disponibles, key="proc_anio")

                dependencia = st.multiselect(
                    "Dependencia",
                    sorted(procesos["Dependencia que Radica"].dropna().astype(str).unique().tolist())
                    if "Dependencia que Radica" in procesos.columns else [],
                    key="proc_dep"
                )

            with col_f2:
                tipo_solicitud = st.multiselect(
                    "Tipo Solicitud",
                    sorted(procesos["Tipo de Solicitud"].dropna().astype(str).unique().tolist())
                    if "Tipo de Solicitud" in procesos.columns else [],
                    key="proc_tipo_sol"
                )

                abogado = st.multiselect(
                    "Abogado",
                    sorted(procesos["Abogado asignado"].dropna().astype(str).unique().tolist())
                    if "Abogado asignado" in procesos.columns else [],
                    key="proc_abogado"
                )

            with col_f3:
                etapa = st.multiselect(
                    "Etapa",
                    sorted(procesos["Etapa"].dropna().astype(str).unique().tolist())
                    if "Etapa" in procesos.columns else [],
                    key="proc_etapa"
                )

                razon = st.multiselect(
                    "Razón Estado",
                    sorted(procesos["Razón para el estado"].dropna().astype(str).unique().tolist())
                    if "Razón para el estado" in procesos.columns else [],
                    key="proc_razon"
                )

            with col_f4:
                accion_filter = st.multiselect(
                    "Acción",
                    sorted(procesos["Acción"].dropna().astype(str).unique().tolist())
                    if "Acción" in procesos.columns else [],
                    key="proc_accion"
                )

                empresa = st.multiselect(
                    "Empresa",
                    sorted(procesos["Empresa o filial"].dropna().astype(str).unique().tolist())
                    if "Empresa o filial" in procesos.columns else [],
                    key="proc_empresa"
                )

    # ==========================
    # APLICACIÓN DE FILTROS
    # ==========================

    df = procesos.copy()

    if año and "Año" in df.columns:
        df = df[df["Año"].isin(año)]

    if dependencia and "Dependencia que Radica" in df.columns:
        df = df[df["Dependencia que Radica"].isin(dependencia)]

    if tipo_solicitud and "Tipo de Solicitud" in df.columns:
        df = df[df["Tipo de Solicitud"].isin(tipo_solicitud)]

    if abogado and "Abogado asignado" in df.columns:
        df = df[df["Abogado asignado"].isin(abogado)]

    if etapa and "Etapa" in df.columns:
        df = df[df["Etapa"].isin(etapa)]

    if razon and "Razón para el estado" in df.columns:
        df = df[df["Razón para el estado"].isin(razon)]

    if accion_filter and "Acción" in df.columns:
        df = df[df["Acción"].isin(accion_filter)]

    if empresa and "Empresa o filial" in df.columns:
        df = df[df["Empresa o filial"].isin(empresa)]

    # =====================================
    # 2. TÍTULO DEL DASHBOARD
    # =====================================

    st.subheader("📚 Procesos Judiciales")

    # ==========================
    # 3. ENCABEZADO Y KPIS
    # ==========================

    total_procesos = len(df)

    col_pretensiones = None
    for col in ["Valor Total Pretensiones", "Valor total pretensiones", "Pretensiones", "VALOR TOTAL PRETENSIONES"]:
        if col in df.columns:
            col_pretensiones = col
            break

    total_pretensiones = (
        pd.to_numeric(df[col_pretensiones], errors="coerce").fillna(0).sum()
        if col_pretensiones else 0
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("⚖️ Procesos", f"{total_procesos:,}")

    with col2:
        st.metric("💰 Pretensiones", formatear_pretensiones(total_pretensiones))

    with col3:
        st.metric("👨‍⚖️ Abogados", df["Abogado asignado"].nunique() if "Abogado asignado" in df.columns else 0)

    with col4:
        st.metric("🏢 Empresas", df["Empresa o filial"].nunique() if "Empresa o filial" in df.columns else 0)

    with col5:
        st.metric("📄 Acciones", df["Acción"].nunique() if "Acción" in df.columns else 0)

    st.divider()

    # ==========================
    # TABLA RESUMEN POR ACCIÓN Y ROL
    # ==========================
    st.subheader("📊 Consolidado de Procesos por Acción y Calidad de EPM")

    acciones_objetivo = [
        "Acción de cumplimiento", "Acciones de Grupo", "Acciones populares", 
        "Amparos Policivos", "Competencia desleal", "Contractual", 
        "Declaración de pertenencia", "Demanda arbitral", "Demanda de inconstitucionalidad", 
        "Denuncia Ley 600 del 2000", "Denuncia Ley 906 del 2004", "Deslinde y amojonamiento", 
        "Divisorios", "Ejecutivo", "Ejecutivo singular", "Expropiación", 
        "Extinción de dominio", "Imposición de servidumbre", "Impugnación de actos de asamblea", 
        "Nulidad", "Nulidad y restablecimiento del derecho", 
        "Nulidad y restablecimiento del derecho - Laboral", "Ordinario Laboral", 
        "Pago por consignación", "Proceso Verbal", "Protección del consumidor", 
        "Pruebas extraprocesales", "Querella Civil", "Querella Ley 906 del 2004", 
        "Recurso extraordinario de revisión", "Reivindicatorio", "Reparación directa", 
        "Repetición", "Responsabilidad Civil Extracontractual", "Responsabilidad Fiscal", 
        "Restitución de inmueble arrendado", "Restitución y formalización de tierras", 
        "Solicitud de insistencia", "Sucesión"
    ]

    df_tabla = df.copy()

    if col_pretensiones and col_pretensiones in df_tabla.columns:
        df_tabla["Valor Total Pretensiones"] = pd.to_numeric(df_tabla[col_pretensiones], errors="coerce").fillna(0)
    else:
        df_tabla["Valor Total Pretensiones"] = 0

    # Búsqueda dinámica de la columna de Rol Sujeto Principal
    col_rol = None
    posibles_cols_rol = ["Rol Sujeto Principal", "Rol sujeto principal", "ROL SUJETO PRINCIPAL", "Rol Sujeto", "Rol"]
    for col in posibles_cols_rol:
        if col in df_tabla.columns:
            col_rol = col
            break

    if col_rol is None:
        for col in df_tabla.columns:
            if "rol" in str(col).lower() and "sujeto" in str(col).lower():
                col_rol = col
                break

    if col_rol:
        df_tabla["Rol_Normalizado"] = df_tabla[col_rol].astype(str).str.strip().str.upper()
    else:
        df_tabla["Rol_Normalizado"] = ""

    filas = []

    for acc in acciones_objetivo:
        sub_df = df_tabla[df_tabla["Acción"].astype(str).str.strip() == acc] if "Acción" in df_tabla.columns else pd.DataFrame()
        
        # EPM Demandante -> Rol Sujeto Principal == DEMANDADO
        epm_demandante = sub_df[sub_df["Rol_Normalizado"] == "DEMANDADO"]
        no_demandante = len(epm_demandante)
        val_demandante = epm_demandante["Valor Total Pretensiones"].sum()

        # EPM Demandado -> Rol Sujeto Principal == DEMANDANTE
        epm_demandado = sub_df[sub_df["Rol_Normalizado"] == "DEMANDANTE"]
        no_demandado = len(epm_demandado)
        val_demandado = epm_demandado["Valor Total Pretensiones"].sum()

        no_total = no_demandante + no_demandado
        val_total = val_demandante + val_demandado

        filas.append({
            "Acción/Medio de control": acc,
            "EPM Demandante - No.": no_demandante,
            "EPM Demandante - Valor": val_demandante,
            "EPM Demandado - No.": no_demandado,
            "EPM Demandado - Valor": val_demandado,
            "No. total": no_total,
            "Valor total pretensiones": val_total
        })

    df_resumen = pd.DataFrame(filas)

    total_row = pd.Series({
        "Acción/Medio de control": "TOTAL",
        "EPM Demandante - No.": df_resumen["EPM Demandante - No."].sum(),
        "EPM Demandante - Valor": df_resumen["EPM Demandante - Valor"].sum(),
        "EPM Demandado - No.": df_resumen["EPM Demandado - No."].sum(),
        "EPM Demandado - Valor": df_resumen["EPM Demandado - Valor"].sum(),
        "No. total": df_resumen["No. total"].sum(),
        "Valor total pretensiones": df_resumen["Valor total pretensiones"].sum()
    })

    df_resumen_display = pd.concat([df_resumen, pd.DataFrame([total_row])], ignore_index=True)

    df_resumen_display["EPM Demandante - Valor"] = df_resumen_display["EPM Demandante - Valor"].apply(formatear_moneda_tabla)
    df_resumen_display["EPM Demandado - Valor"] = df_resumen_display["EPM Demandado - Valor"].apply(formatear_moneda_tabla)
    df_resumen_display["Valor total pretensiones"] = df_resumen_display["Valor total pretensiones"].apply(formatear_moneda_tabla)

    df_resumen_display.columns = pd.MultiIndex.from_tuples([
        ("", "Acción/Medio de control"),
        ("EPM/Filial Demandante", "No."),
        ("EPM/Filial Demandante", "Valor pretensiones"),
        ("EPM/filial Demandado", "No."),
        ("EPM/filial Demandado", "Valor pretensiones"),
        ("", "No. total"),
        ("", "Valor total pretensiones")
    ])

    st.dataframe(
        df_resumen_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================
    # GRÁFICOS INTERACTIVOS
    # ==========================
    col1, col2 = st.columns(2)

    with col1:
        if "Acción" in df.columns:
            acciones = df["Acción"].fillna("Sin Clasificar").value_counts().head(10).reset_index()
            acciones.columns = ["Acción", "Cantidad"]
            fig = px.bar(acciones, x="Cantidad", y="Acción", orientation="h", title="Top 10 Procesos por Acción")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "Etapa" in df.columns:
            etapas = df["Etapa"].fillna("Sin Clasificar").value_counts().reset_index()
            etapas.columns = ["Etapa", "Cantidad"]
            fig = px.pie(etapas, names="Etapa", values="Cantidad", title="Distribución por Etapa", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        if "Empresa o filial" in df.columns:
            empresas = df["Empresa o filial"].fillna("Sin Empresa").value_counts().reset_index()
            empresas.columns = ["Empresa", "Cantidad"]
            fig = px.bar(empresas, x="Empresa", y="Cantidad", title="Procesos por Empresa o Filial")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if "Abogado asignado" in df.columns:
            abogados = df["Abogado asignado"].fillna("Sin Asignar").value_counts().head(15).reset_index()
            abogados.columns = ["Abogado", "Cantidad"]
            fig = px.bar(abogados, x="Cantidad", y="Abogado", orientation="h", title="Top 15 Abogados con más Procesos")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==========================
    # DETALLE Y TABLA COMPLETA
    # ==========================
    st.subheader("📋 Detalle General de Procesos")
    st.dataframe(df, use_container_width=True, height=600)