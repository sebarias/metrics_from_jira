### Métricas para Jira

JIRA v7 server + Python 3.7 + DASH + Plotly + FIREBASE

Este proyecto tiene por objetivo obtener datos de Jira usando su API REST, para luego almacenarlos en una Base de datos No Sql en Firebase.
De esta manera se evita sobrecargar Jira con peticiones al servidor.
Con la data obtenida, se grafican en dos scatter plot, para Cycle Time y Lead Time y un Histograma para visualizar el Througput del proyecto analizado.

Archivos de configuración necesarios:

- jira_creds.json : Archivo json que contiene las credenciales de JIRA en los siguientes atributos
      - user
      - password
   `{
            "user":"XXXX",
            "password":"XXXX"
    }`

- firebase_config.json: contiene dos atributos
      - file_path = path de json que contiene las credenciales de Firebase
      - databaseURL = url de la base de datos de Firebase
      
- Archivo json de credenciales de Firebase : Este archivo es generado por Firebase cuando se habilitan las crendenciales de acceso a los proyectos de la plataforma.
