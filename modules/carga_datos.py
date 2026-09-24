import streamlit as st
import pandas as pd


def mostrar_carga_datos():

    st.sidebar.title("📂 Carga de Archivos")

    archivos = st.sidebar.file_uploader(
        "Seleccione los archivos Excel",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if archivos:

        data = {}

        for archivo in archivos:

            nombre = archivo.name.lower()

            try:

                if "equipo" in nombre:
                    data["equipo"] = pd.read_excel(archivo)

                elif "reclam" in nombre:
                    data["reclamaciones"] = pd.read_excel(archivo)

                elif "concil" in nombre:
                    data["conciliaciones"] = pd.read_excel(archivo)

                elif "tutela" in nombre:
                    data["tutelas"] = pd.read_excel(archivo)

                elif "proceso" in nombre:
                    data["procesos"] = pd.read_excel(archivo)

                elif "sentencia" in nombre:
                    data["sentencias"] = pd.read_excel(archivo)

            except Exception as e:
                st.sidebar.error(
                    f"Error leyendo {archivo.name}"
                )

        requeridos = [
            "equipo",
            "reclamaciones",
            "conciliaciones",
            "tutelas",
            "procesos",
            "sentencias"
        ]

        if all(k in data for k in requeridos):

            st.session_state["data"] = data

            st.sidebar.success(
                "✅ Archivos cargados correctamente"
            )

            if st.sidebar.button(
                "🔄 Nuevo Corte",
                use_container_width=True
            ):
                st.session_state.clear()
                st.rerun()

        else:

            faltantes = [
                k for k in requeridos
                if k not in data
            ]

            st.sidebar.warning(
                f"Faltan archivos: {', '.join(faltantes)}"
            )