import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import re


def mostrar_dashboard_resumen(data):
    """
    Renders the Executive Summary Dashboard in Streamlit.
    Processes legal datasets (procesos, reclamaciones, conciliaciones, tutelas, sentencias, equipo)
    and visualizes workload, pretension amounts, actions, and historical evolution.
    """

    # Safely retrieve dataframes with defaults
    procesos = data.get("procesos", pd.DataFrame())
    reclamaciones = data.get("reclamaciones", pd.DataFrame())
    conciliaciones = data.get("conciliaciones", pd.DataFrame())
    tutelas = data.get("tutelas", pd.DataFrame())
    sentencias = data.get("sentencias", pd.DataFrame())
    equipo = data.get("equipo", pd.DataFrame())

    # =====================================
    # FUNCIONES AUXILIARES Y FORMATO
    # =====================================

    def ultra_limpiar_nombre(texto):
        """
        Limpia texto a fondo: quita tildes, caracteres especiales, paréntesis,
        múltiples espacios y pasa a mayúsculas para un cruce impecable.
        """
        if pd.isna(texto):
            return ""
        st_text = str(texto).strip().upper()
        st_text = "".join(
            c for c in unicodedata.normalize("NFD", st_text)
            if unicodedata.category(c) != "Mn"
        )
        st_text = st_text.replace("Ñ", "N")
        st_text = re.sub(r"\(.*?\)", "", st_text)
        st_text = re.sub(r"[^A-Z\s]", "", st_text)
        return re.sub(r"\s+", " ", st_text).strip()

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
        """Formatea dinero estilo COP. Si es 0 o vacío, retorna texto vacío."""
        if pd.isna(val) or val == 0:
            return "$ 0,00"
        return f"$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def obtener_clave_corta(texto):
        """Genera clave basada en el primer nombre y el primer/último apellido."""
        partes = ultra_limpiar_nombre(texto).split()
        if len(partes) >= 2:
            return f"{partes[0]} {partes[-1]}"
        elif len(partes) == 1:
            return partes[0]
        return ""

    # =====================================
    # NORMALIZACIÓN DE TABLA DE EQUIPO
    # =====================================

    def normalizar_equipo(df_eq):
        if df_eq is None or df_eq.empty:
            return pd.DataFrame()

        df = df_eq.copy()
        df = df.loc[:, ~df.columns.duplicated()].dropna(how="all")
        cols_norm = [ultra_limpiar_nombre(c) for c in df.columns]

        if any("NOMBRE" in c for c in cols_norm):
            return df

        registros = []
        num_cols = df.shape[1]
        for i in range(0, num_cols, 3):
            if i + 2 < num_cols:
                sub_df = df.iloc[1:, [i, i+1, i+2]].dropna(how="all")
                for _, row in sub_df.iterrows():
                    nom_raw = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    if not nom_raw or nom_raw.lower() in ["nan", "none"]:
                        continue
                    
                    cargo = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "-"
                    tipo = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "-"
                    
                    encargo = "Sí" if ("ENCARGO" in nom_raw.upper() or "ENCARGADA" in nom_raw.upper()) else "No"
                    nom_limpio = re.sub(r"\s*\(.*?\)", "", nom_raw).strip()

                    if nom_limpio:
                        registros.append({
                            "Nombre": nom_limpio,
                            "Cargo inicial": cargo,
                            "Encargo": encargo,
                            "Tipo de contrato": tipo
                        })
        return pd.DataFrame(registros)

    # =====================================
    # FECHAS Y AÑOS
    # =====================================

    def extraer_anio(df, col_fecha):
        if df is not None and not df.empty and col_fecha in df.columns:
            df["Año"] = pd.to_datetime(df[col_fecha], errors="coerce").dt.year
        elif df is not None:
            df["Año"] = pd.NA

    extraer_anio(procesos, "Fecha de Solicitud")
    extraer_anio(reclamaciones, "Fecha de Solicitud (Radicado) (Radicado)")
    extraer_anio(conciliaciones, "Fecha de Solicitud (Radicado) (Radicado)")
    extraer_anio(tutelas, "Fecha de Solicitud (Radicado) (Radicado)")
    extraer_anio(sentencias, "Fecha Providencia")

    # =====================================
    # BARRA LATERAL: FILTROS DINÁMICOS ESTÁNDAR
    # =====================================

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Filtros Resumen Ejecutivo")

    # 1. Filtro de Año
    todos_anios_set = set()
    for df in [procesos, reclamaciones, conciliaciones, tutelas, sentencias]:
        if df is not None and "Año" in df.columns:
            valid_years = df["Año"].dropna().astype(int).tolist()
            todos_anios_set.update(valid_years)

    anios_disponibles = sorted(list(todos_anios_set), reverse=True)
    
    opcion_anio = st.sidebar.radio(
        "Modo de selección de Año:",
        ["Todos", "Seleccionar varios"],
        key="resumen_modo_anio"
    )
    
    if opcion_anio == "Seleccionar varios":
        anios_seleccionados = st.sidebar.multiselect(
            "Seleccione los Años:",
            options=anios_disponibles,
            default=anios_disponibles,
            key="resumen_anios_multi"
        )
    else:
        anios_seleccionados = anios_disponibles

    # Helper de filtrado primario por año
    def aplicar_filtro_anio(df):
        if df is None or df.empty:
            return pd.DataFrame()
        if "Año" in df.columns and anios_seleccionados:
            return df[df["Año"].isin(anios_seleccionados)].copy()
        return df.copy()

    proc_temp = aplicar_filtro_anio(procesos)

    # 2. Filtro Empresa o Filial
    empresas_disponibles = []
    if "Empresa o filial" in proc_temp.columns:
        empresas_disponibles = sorted(proc_temp["Empresa o filial"].dropna().astype(str).unique().tolist())

    opcion_empresa = st.sidebar.radio(
        "Modo de selección de Empresa / Filial:",
        ["Todos", "Seleccionar varios"],
        key="resumen_modo_empresa"
    )

    if opcion_empresa == "Seleccionar varios" and empresas_disponibles:
        empresas_seleccionadas = st.sidebar.multiselect(
            "Seleccione Empresas:",
            options=empresas_disponibles,
            default=empresas_disponibles,
            key="resumen_empresa_multi"
        )
    else:
        empresas_seleccionadas = empresas_disponibles

    if "Empresa o filial" in proc_temp.columns and empresas_seleccionadas:
        proc_temp = proc_temp[proc_temp["Empresa o filial"].astype(str).isin(empresas_seleccionadas)]

    # 3. Filtro Abogado Asignado
    abogados_disponibles = []
    if "Abogado asignado" in proc_temp.columns:
        abogados_disponibles = sorted(proc_temp["Abogado asignado"].dropna().astype(str).unique().tolist())

    opcion_abogado = st.sidebar.radio(
        "Modo de selección de Abogado:",
        ["Todos", "Seleccionar varios"],
        key="resumen_modo_abogado"
    )

    if opcion_abogado == "Seleccionar varios" and abogados_disponibles:
        abogados_seleccionados = st.sidebar.multiselect(
            "Seleccione Abogados:",
            options=abogados_disponibles,
            default=abogados_disponibles,
            key="resumen_abogado_multi"
        )
    else:
        abogados_seleccionados = abogados_disponibles

    if "Abogado asignado" in proc_temp.columns and abogados_seleccionados:
        proc_temp = proc_temp[proc_temp["Abogado asignado"].astype(str).isin(abogados_seleccionados)]

    # 4. Filtro Acción / Medio de Control
    acciones_disponibles = []
    if "Acción" in proc_temp.columns:
        acciones_disponibles = sorted(proc_temp["Acción"].dropna().astype(str).unique().tolist())

    opcion_accion = st.sidebar.radio(
        "Modo de selección de Acción / Medio de Control:",
        ["Todos", "Seleccionar varios"],
        key="resumen_modo_accion"
    )

    if opcion_accion == "Seleccionar varios" and acciones_disponibles:
        acciones_seleccionadas = st.sidebar.multiselect(
            "Seleccione Acciones:",
            options=acciones_disponibles,
            default=acciones_disponibles,
            key="resumen_accion_multi"
        )
    else:
        acciones_seleccionadas = acciones_disponibles

    # =====================================
    # APLICACIÓN FINAL DE FILTROS CRUZADOS
    # =====================================

    def filtrar_dataframe_completo(df):
        if df is None or df.empty:
            return pd.DataFrame()
        
        res_df = df.copy()

        # Filtro de Año
        if "Año" in res_df.columns and anios_seleccionados:
            res_df = res_df[res_df["Año"].isin(anios_seleccionados)]

        # Filtro de Empresa
        if "Empresa o filial" in res_df.columns and empresas_seleccionadas:
            res_df = res_df[res_df["Empresa o filial"].astype(str).isin(empresas_seleccionadas)]

        # Filtro de Abogado
        if "Abogado asignado" in res_df.columns and abogados_seleccionados:
            res_df = res_df[res_df["Abogado asignado"].astype(str).isin(abogados_seleccionados)]

        # Filtro de Acción
        if "Acción" in res_df.columns and acciones_seleccionadas:
            res_df = res_df[res_df["Acción"].astype(str).isin(acciones_seleccionadas)]

        return res_df

    procesos_f = filtrar_dataframe_completo(procesos)
    reclamaciones_f = filtrar_dataframe_completo(reclamaciones)
    conciliaciones_f = filtrar_dataframe_completo(conciliaciones)
    tutelas_f = filtrar_dataframe_completo(tutelas)
    sentencias_f = filtrar_dataframe_completo(sentencias)

    # =====================================
    # KPIS GENERALES
    # =====================================

    equipo_normalizado = normalizar_equipo(equipo)

    total_procesos = len(procesos_f)
    total_reclamaciones = len(reclamaciones_f)
    total_conciliaciones = len(conciliaciones_f)
    total_tutelas = len(tutelas_f)
    total_sentencias = len(sentencias_f)
    total_equipo = len(equipo_normalizado) if not equipo_normalizado.empty else 0

    st.subheader("🏠 Resumen Ejecutivo")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("⚖️ Procesos", f"{total_procesos:,}")
    with col2:
        st.metric("📌 Reclamaciones", f"{total_reclamaciones:,}")
    with col3:
        st.metric("🤝 Conciliaciones", f"{total_conciliaciones:,}")
    with col4:
        st.metric("⚖️ Tutelas", f"{total_tutelas:,}")
    with col5:
        st.metric("🏆 Sentencias", f"{total_sentencias:,}")
    with col6:
        st.metric("👥 Equipo (Tabla1)", total_equipo)

    st.divider()

    # =====================================
    # PRETENSIONES
    # =====================================

    def calcular_sumatoria_pretensiones(df):
        if df is None or df.empty or "Valor Total Pretensiones" not in df.columns:
            return 0.0
        return pd.to_numeric(df["Valor Total Pretensiones"], errors="coerce").fillna(0).sum()

    pret_procesos = calcular_sumatoria_pretensiones(procesos_f)
    pret_reclamaciones = calcular_sumatoria_pretensiones(reclamaciones_f)
    pret_conciliaciones = calcular_sumatoria_pretensiones(conciliaciones_f)
    pret_tutelas = calcular_sumatoria_pretensiones(tutelas_f)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Procesos", formatear_moneda(pret_procesos))
    with col2:
        st.metric("💰 Reclamaciones", formatear_moneda(pret_reclamaciones))
    with col3:
        st.metric("💰 Conciliaciones", formatear_moneda(pret_conciliaciones))
    with col4:
        st.metric("💰 Tutelas", formatear_moneda(pret_tutelas))

    st.divider()

    # =====================================
    # DISTRIBUCIÓN GENERAL
    # =====================================

    col1, col2 = st.columns(2)

    with col1:
        distribucion = pd.DataFrame({
            "Tipo": ["Procesos", "Reclamaciones", "Conciliaciones", "Tutelas", "Sentencias"],
            "Cantidad": [total_procesos, total_reclamaciones, total_conciliaciones, total_tutelas, total_sentencias]
        })

        fig = px.pie(
            distribucion,
            names="Tipo",
            values="Cantidad",
            hole=0.5,
            title="Distribución General"
        )
        fig.update_traces(textinfo="percent+value", textfont_size=12)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        total_asuntos = total_procesos + total_reclamaciones + total_conciliaciones + total_tutelas
        pret_total = pret_procesos + pret_reclamaciones + pret_conciliaciones + pret_tutelas
        
        if "Abogado asignado" in procesos_f.columns:
            total_abogados = len(set(procesos_f["Abogado asignado"].dropna().astype(str).tolist()))
        else:
            total_abogados = 0

        st.info(
            f"""
### 📋 Resumen Consolidado

**Total Asuntos:** {total_asuntos:,}

**Pretensiones Totales:**  
{formatear_moneda(pret_total)}

**Abogados en Procesos:** {total_abogados:,}

**Integrantes en Tabla1:** {total_equipo}
"""
        )

    # =====================================
    # CARGA LABORAL Y AGRUPACIÓN
    # =====================================

    if "Valor Total Pretensiones" in procesos_f.columns:
        procesos_f["Valor Total Pretensiones Num"] = pd.to_numeric(
            procesos_f["Valor Total Pretensiones"],
            errors="coerce"
        ).fillna(0)
    else:
        procesos_f["Valor Total Pretensiones Num"] = 0

    if "Abogado asignado" in procesos_f.columns and not procesos_f.empty:
        carga_abogados = (
            procesos_f.groupby("Abogado asignado")
            .agg(
                Cantidad=("Abogado asignado", "count"),
                Pretensiones=("Valor Total Pretensiones Num", "sum")
            )
            .reset_index()
        )

        carga_abogados = carga_abogados[
            carga_abogados["Abogado asignado"].notna()
            & (carga_abogados["Abogado asignado"].astype(str).str.strip() != "")
            & (carga_abogados["Cantidad"] > 0)
        ].copy()
    else:
        carga_abogados = pd.DataFrame(columns=["Abogado asignado", "Cantidad", "Pretensiones"])

    # =====================================
    # CRUCE CON TABLA DE EQUIPO
    # =====================================

    if not equipo_normalizado.empty and not carga_abogados.empty:
        eq_clean = equipo_normalizado.copy()

        col_nombre_eq = None
        for c in eq_clean.columns:
            if "NOMBRE" in ultra_limpiar_nombre(c):
                col_nombre_eq = c
                break

        if not col_nombre_eq:
            col_nombre_eq = eq_clean.columns[0]

        nuevas_cols = []
        for c in eq_clean.columns:
            cn = ultra_limpiar_nombre(c)
            if c == col_nombre_eq:
                nuevas_cols.append("Profesional en derecho")
            elif "CARGO" in cn:
                nuevas_cols.append("Cargo inicial")
            elif "ENCARGO" in cn:
                nuevas_cols.append("Encargo")
            elif "CONTRATO" in cn or "TIPO" in cn:
                nuevas_cols.append("Tipo de contrato")
            else:
                nuevas_cols.append(c)

        eq_clean.columns = nuevas_cols
        eq_clean = eq_clean.loc[:, ~eq_clean.columns.duplicated()].copy()

        carga_abogados["Key_Clean"] = carga_abogados["Abogado asignado"].apply(ultra_limpiar_nombre)
        carga_abogados["Key_Short"] = carga_abogados["Abogado asignado"].apply(obtener_clave_corta)

        eq_clean["Key_Clean"] = eq_clean["Profesional en derecho"].apply(ultra_limpiar_nombre)
        eq_clean["Key_Short"] = eq_clean["Profesional en derecho"].apply(obtener_clave_corta)

        df_merged = pd.merge(carga_abogados, eq_clean, on="Key_Clean", how="inner")

        sin_match_abogados = carga_abogados[~carga_abogados["Key_Clean"].isin(df_merged["Key_Clean"])].copy()

        if not sin_match_abogados.empty:
            recuperados = pd.merge(
                sin_match_abogados,
                eq_clean,
                on="Key_Short",
                how="inner",
                suffixes=("", "_eq")
            )

            if not recuperados.empty:
                cols_validas = [c for c in df_merged.columns if c in recuperados.columns]
                df_merged = pd.concat([df_merged[cols_validas], recuperados[cols_validas]], ignore_index=True)

        df_merged.drop_duplicates(subset=["Key_Clean"], inplace=True)

        cols_deseadas = [
            "Profesional en derecho",
            "Cargo inicial",
            "Encargo",
            "Tipo de contrato",
            "Cantidad",
            "Pretensiones"
        ]

        for c in cols_deseadas:
            if c not in df_merged.columns:
                df_merged[c] = "-"

        df_tabla_final = df_merged[cols_deseadas].copy()
        df_tabla_final.rename(columns={"Pretensiones": "Valor pretensiones"}, inplace=True)
        df_tabla_final = df_tabla_final[df_tabla_final["Cantidad"] > 0].copy()
        df_tabla_final.sort_values("Cantidad", ascending=False, inplace=True)

    else:
        if not carga_abogados.empty:
            df_tabla_final = (
                carga_abogados.sort_values("Cantidad", ascending=False)
                .rename(columns={"Abogado asignado": "Profesional en derecho", "Pretensiones": "Valor pretensiones"})
                [["Profesional en derecho", "Cantidad", "Valor pretensiones"]]
            )
        else:
            df_tabla_final = pd.DataFrame(columns=["Profesional en derecho", "Cantidad", "Valor pretensiones"])

    for c in ["Cargo inicial", "Encargo", "Tipo de contrato"]:
        if c in df_tabla_final.columns:
            df_tabla_final[c] = df_tabla_final[c].fillna("-").replace(["nan", "None", "", None], "-")

    # =====================================
    # GRÁFICO TOP 10 Y TABLA
    # =====================================

    if not df_tabla_final.empty:
        grafico_carga = df_tabla_final.sort_values("Cantidad", ascending=False).head(10).copy()
        grafico_carga["Nombre corto"] = grafico_carga["Profesional en derecho"].astype(str).apply(
            lambda nombre: " ".join(nombre.split()[:2])
        )

        for col in ["Cargo inicial", "Tipo de contrato"]:
            if col not in grafico_carga.columns:
                grafico_carga[col] = "-"

        fig_carga = px.bar(
            grafico_carga,
            x="Nombre corto",
            y="Cantidad",
            text="Cantidad",
            title="Top 10 Profesionales por Carga Laboral",
            custom_data=["Profesional en derecho", "Cargo inicial", "Tipo de contrato"]
        )

        fig_carga.update_traces(
            marker_color="#0078D4",
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=13),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Cargo: %{customdata[1]}<br>"
                "Contrato: %{customdata[2]}<br>"
                "Procesos: %{y:,.0f}"
                "<extra></extra>"
            )
        )

        fig_carga.update_layout(
            height=500,
            xaxis_title="",
            yaxis_title="Cantidad de procesos",
            showlegend=False,
            bargap=0.25,
            margin=dict(l=50, r=30, t=70, b=120)
        )

        fig_carga.update_xaxes(tickangle=-35, tickfont=dict(size=11))
        fig_carga.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", rangemode="tozero")

        st.plotly_chart(fig_carga, use_container_width=True)

    if "Valor pretensiones" in df_tabla_final.columns:
        df_tabla_final["Valor pretensiones"] = df_tabla_final["Valor pretensiones"].apply(formatear_cop_exacto)

    st.dataframe(df_tabla_final, use_container_width=True, height=380, hide_index=True)
    st.divider()

    # =====================================
    # EMPRESAS / FILIALES
    # =====================================

    st.subheader("🏢 Representación de Empresas y Filiales")

    if "Empresa o filial" in procesos_f.columns and not procesos_f.empty:
        empresa_df = procesos_f["Empresa o filial"].fillna("Sin Empresa").value_counts().reset_index()
        empresa_df.columns = ["Empresa", "Cantidad"]

        fig_empresa = px.bar(
            empresa_df,
            x="Empresa",
            y="Cantidad",
            text="Cantidad",
            title="Asuntos por Empresa / Filial"
        )
        st.plotly_chart(fig_empresa, use_container_width=True)
        st.dataframe(empresa_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay información disponible de Empresa o Filial para los filtros seleccionados.")

    st.divider()

    # =====================================
    # ACCIONES Y PRETENSIONES
    # =====================================

    st.subheader("⚖️ Acciones / Medios de Control")

    if "Acción" in procesos_f.columns and not procesos_f.empty:
        acciones_df = (
            procesos_f.groupby("Acción")
            .agg(
                Cantidad=("Acción", "count"),
                Pretensiones=("Valor Total Pretensiones Num", "sum")
            )
            .reset_index()
        )

        acciones_cantidad = (
            acciones_df.sort_values("Cantidad", ascending=False)
            .head(15)
            .sort_values("Cantidad", ascending=True)
        )

        acciones_pretensiones = (
            acciones_df.sort_values("Pretensiones", ascending=False)
            .head(15)
            .sort_values("Pretensiones", ascending=True)
        )

        def formato_corto(valor):
            if valor >= 1_000_000_000_000:
                return f"{valor / 1_000_000_000_000:,.2f} B"
            elif valor >= 1_000_000_000:
                return f"{valor / 1_000_000_000:,.2f} Mil M"
            elif valor >= 1_000_000:
                return f"{valor / 1_000_000:,.2f} M"
            return f"{valor:,.0f}"

        acciones_pretensiones["Valor mostrado"] = acciones_pretensiones["Pretensiones"].apply(formato_corto)

        col1, col2 = st.columns(2)

        with col1:
            fig_acciones = px.bar(
                acciones_cantidad,
                x="Cantidad",
                y="Acción",
                orientation="h",
                text="Cantidad",
                title="Cantidad de Procesos"
            )
            fig_acciones.update_traces(textposition="outside", cliponaxis=False)
            fig_acciones.update_layout(height=600, xaxis_title="Cantidad", yaxis_title="", margin=dict(l=20, r=80, t=60, b=40))
            st.plotly_chart(fig_acciones, use_container_width=True)

        with col2:
            fig_pretensiones = px.bar(
                acciones_pretensiones,
                x="Pretensiones",
                y="Acción",
                orientation="h",
                text="Valor mostrado",
                title="Pretensiones por Acción"
            )
            fig_pretensiones.update_traces(textposition="outside", cliponaxis=False)
            fig_pretensiones.update_layout(height=600, xaxis_title="Valor de Pretensiones", yaxis_title="", margin=dict(l=20, r=140, t=60, b=40))
            st.plotly_chart(fig_pretensiones, use_container_width=True)

        acciones_tabla = acciones_df.sort_values("Cantidad", ascending=False).copy()
        acciones_tabla["Cantidad"] = acciones_tabla["Cantidad"].apply(lambda x: f"{x:,}".replace(",", "."))
        acciones_tabla["Pretensiones"] = acciones_tabla["Pretensiones"].apply(formatear_cop_exacto)

        st.dataframe(acciones_tabla, use_container_width=True, height=400, hide_index=True)
    else:
        st.info("No hay información disponible sobre Acciones o Medios de Control para los filtros seleccionados.")

    st.divider()

    # =====================================
    # EVOLUCIÓN HISTÓRICA CONSOLIDADA
    # =====================================

    st.subheader("📈 Evolución Histórica Consolidada")

    if list(todos_anios_set):
        historico = pd.DataFrame({"Año": sorted(list(todos_anios_set))})
        
        for nombre_tipo, df_f in [
            ("Procesos", procesos_f),
            ("Reclamaciones", reclamaciones_f),
            ("Conciliaciones", conciliaciones_f),
            ("Tutelas", tutelas_f),
            ("Sentencias", sentencias_f)
        ]:
            if df_f is not None and not df_f.empty and "Año" in df_f.columns:
                historico[nombre_tipo] = historico["Año"].apply(lambda x: len(df_f[df_f["Año"] == x]))
            else:
                historico[nombre_tipo] = 0

        historico["Total_Anio"] = historico[["Procesos", "Reclamaciones", "Conciliaciones", "Tutelas", "Sentencias"]].sum(axis=1)
        historico = historico[historico["Total_Anio"] > 0].drop(columns=["Total_Anio"])

        if not historico.empty:
            historico_long = historico.melt(id_vars="Año", var_name="Tipo", value_name="Cantidad")

            fig_hist = px.line(
                historico_long,
                x="Año",
                y="Cantidad",
                color="Tipo",
                markers=True,
                title="Evolución Anual"
            )
            fig_hist.update_xaxes(type='category', title="Año")
            fig_hist.update_yaxes(title="Cantidad de Asuntos")
            fig_hist.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No hay suficiente información para trazar la evolución histórica con los filtros aplicados.")
    else:
        st.info("No hay fechas/años disponibles en los registros para generar la evolución histórica.")

    # =====================================
    # HALLAZGOS
    # =====================================

    accion_principal = (
        procesos_f["Acción"].value_counts().index[0]
        if ("Acción" in procesos_f.columns and len(procesos_f) > 0 and not procesos_f["Acción"].dropna().empty)
        else "N/D"
    )

    st.success(
        f"""
### 🎯 Hallazgos Relevantes

• Se administran actualmente **{total_asuntos:,} asuntos**.

• Las pretensiones consolidadas ascienden a **{formatear_moneda(pret_total)}**.

• Integrantes activos en Tabla1: **{total_equipo}**.

• La acción con mayor volumen corresponde a **{accion_principal}**.

• Se registran **{total_sentencias:,} sentencias** en el histórico cargado.
"""
    )