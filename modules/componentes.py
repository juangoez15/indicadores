import streamlit as st

def mostrar_filtros_superiores_fijos(df):
    # 1. CSS para congelar el contenedor en la parte superior (Sticky)
    st.markdown("""
        <style>
        /* Fija el contenedor superior */
        div[data-testid="stVerticalBlock"] > div:has(div.sticky-filters) {
            position: sticky;
            top: 2.8rem; /* Distancia desde el borde superior del viewport */
            z-index: 999;
            background-color: var(--background-color, #ffffff);
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. Contenedor de Filtros con la clase identificadora
    with st.container():
        # HTML invisible para marcar cuál contenedor debe fijarse
        st.markdown('<div class="sticky-filters"></div>', unsafe_allow_html=True)
        
        with st.expander("🔎 Filtros de Búsqueda", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                f_anio = st.multiselect("Año", sorted(df["Año"].dropna().unique()))
                f_dep = st.multiselect("Dependencia", sorted(df["Dependencia"].dropna().unique()))
            with col2:
                f_solicitud = st.multiselect("Tipo Solicitud", sorted(df["Tipo Solicitud"].dropna().unique()))
                f_abogado = st.multiselect("Abogado", sorted(df["Abogado"].dropna().unique()))
            with col3:
                f_etapa = st.multiselect("Etapa", sorted(df["Etapa"].dropna().unique()))
                f_estado = st.multiselect("Razón Estado", sorted(df["Razón Estado"].dropna().unique()))
            with col4:
                f_accion = st.multiselect("Acción", sorted(df["Acción"].dropna().unique()))
                f_empresa = st.multiselect("Empresa", sorted(df["Empresa"].dropna().unique()))

    return f_anio, f_solicitud, f_etapa, f_accion, f_dep, f_abogado, f_estado, f_empresa