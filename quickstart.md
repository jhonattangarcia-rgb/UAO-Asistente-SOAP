Quickstart — Desarrollo local

1. Crear entorno virtual e instalar dependencias

```powershell
python -m venv .venv
. .venv\Scripts\activate
pip install -e .
```

2. Copiar el archivo de ejemplo .env

```powershell
copy .env.example .env
# Edita .env y coloca tu OPENROUTER_API_KEY
```

3. Ejecutar la app

```powershell
streamlit run app.py
```

Notas:
- En producción (Docker), siempre pasa las variables de entorno al contenedor en tiempo de ejecución. El archivo .env local no será usado por contenedores si defines variables en la línea de `docker run -e` o en tu orquestador.
- No comites tu .env. El repositorio incluye .env.example como referencia.
