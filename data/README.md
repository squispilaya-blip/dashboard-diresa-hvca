# data/ — fuente permanente del dashboard

Los Excel de esta carpeta son **la única copia que sobrevive**: al arrancar,
`app.py::_auto_load_from_data_dir()` los lee y con eso llena el dashboard.

Lo que se sube desde el panel de administrador vive solo en la memoria del
servidor (`st.cache_resource`) y **se pierde cuando Streamlit Cloud duerme o
reinicia la app** — entonces el dashboard vuelve al mes que esté aquí.

## Actualizar un mes (lo que hay que hacer el 15 de cada mes)

1. Descargar las 16 fichas del portal MINSA (`Ficha_NN_DL1153_AAAAMM_*.xlsx`).
   Los reportes son **acumulados**: el de agosto trae enero–agosto.
2. Borrar los Excel viejos de esta carpeta y copiar los nuevos.
3. `git add data/ && git commit -m "data: indicadores hasta AAAA-MM" && git push`
4. Streamlit Cloud redespliega solo; el banner debe decir el periodo nuevo.

Indicadores esperados (16): 01 02 03 04 05 06 10 11 12 13 15 16 17 19 25 32.
