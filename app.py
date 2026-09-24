import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Indicadores Jurídicos",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importación de módulos organizados
from modules.carga_datos import mostrar_carga_datos
from modules.dashboard_procesos import mostrar_dashboard_procesos
from modules.dashboard_reclamaciones import mostrar_dashboard_reclamaciones
from modules.dashboard_conciliaciones import mostrar_dashboard_conciliaciones
from modules.dashboard_tutelas import mostrar_dashboard_tutelas
from modules.dashboard_sentencias import mostrar_dashboard_sentencias
from modules.dashboard_equipo import mostrar_dashboard_equipo
from modules.dashboard_resumen import mostrar_dashboard_resumen


def main():
    # Carga de datos inicial (procesamiento o lectura de archivos)
    mostrar_carga_datos()

    # Verificación de datos en sesión antes de renderizar dashboards
    if "data" in st.session_state and st.session_state["data"]:
        
        st.sidebar.title("Navegación")
        
        # Mapeo de opciones a funciones correspondientes
        menu_opciones = {
            "📚 Procesos Vigentes": mostrar_dashboard_procesos,
            "📌 Reclamaciones": mostrar_dashboard_reclamaciones,
            "🤝 Conciliaciones": mostrar_dashboard_conciliaciones,
            "⚖️ Tutelas": mostrar_dashboard_tutelas,
            "🏆 Sentencias": mostrar_dashboard_sentencias,
            "👥 Equipo": mostrar_dashboard_equipo,
            "🏠 Resumen Ejecutivo": mostrar_dashboard_resumen
        }

        opcion = st.sidebar.radio(
            "📊 Seleccione un Dashboard:",
            options=list(menu_opciones.keys())
        )

        # Ejecución dinámica del dashboard seleccionado
        funcion_dashboard = menu_opciones[opcion]
        funcion_dashboard(st.session_state["data"])

    else:
        st.info("👆 Por favor, cargue los datos de entrada para habilitar las vistas del dashboard.")


if __name__ == "__main__":
    main()
