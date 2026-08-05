# Analitica-Educativa
Proyecto enfocado en entregar un análisis FODA para docentes universitarios, apoyar con criterios de rotación de un profesor de una materia a otra de la misma área en la universidad, y anticipar la deserción para una clase especifica.

La parte explorativa se encuentra en el directorio **exploracion** e incluye todo lo relacionado al analisis FODA en el subdirectorio **Procesamiento del Lenguaje Natural**, incluyendo cómo hacer fine-tuning y críterios de elección de modelos.

La metodología tentativa para los modelos de machine learning clásicos para rotación de asignaturas y deserción estudiantes se encuentran en el notebook **Consultas Estructuradas Con Metricas.ipynb**, capitulo 4.

Así mismo se evidencia el código fuente del backend, el cual entre otras cosas carga un modelo de sentimientos al cual se le hizo fine-tuning, principalmente en el archivo **src/app.py**.

Para pruebas locales del backend en FastAPI, los modelos resultantes del fine-tuning se deben a una ruta acorde al sistema operativo:
- Mac: ~/Public/ml_models
- Linux: $XDG_PUBLICSHARE_DIR/ml_models (por default es ~/Public/ml_models)
- Windows: %PUBLIC%\ml_models (por default es C:\Users\Public\ml_models) 

El código fuente del frontend se encuentra en el siguiente repositorio:
[Dashboard en PowerBI](https://github.com/Capstone-Tech-Tailors/entregable-visual)

Para efectos de demostración el backend se desplegó en Azure, y el portal de Swagger se encuentra en el siguiente recurso:
[Swagger](https://analitica-educativa.nicecoast-a9c3f8c2.eastus2.azurecontainerapps.io/docs)

Así mismo la demostración del Dashboard se encuentra en el siguiente recurso:
[Demo Dashboard en PowerBI](https://app.powerbi.com/view?r=eyJrIjoiMGY0ZWIwOGQtYmZkMC00NDE1LTgxNmEtNzczY2YyOWNhMGM0IiwidCI6ImJhNWIwYTRkLTZjNjgtNGFjMy05ZDZlLWM1YjVhMTJhOWQ2OSIsImMiOjR9)
