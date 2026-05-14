## Recomendador de juegos de Steam según precio y género

Este proyecto limpia el dataset crudo de Steam y genera un archivo procesado en data/processed para luego consultar recomendaciones por presupuesto y género.

### Archivos generados

- data/processed/games_clean.csv
- data/processed/genres.json

### Datos

El archivo `data/raw/games.json` (766 MB) es demasiado grande para GitHub y se encuentra en `.gitignore`. 

**Opciones para obtenerlo:**
1. Descargar desde la URL original mencionada en el commit
2. Contactar con el desarrollador para acceder al archivo
3. El archivo será descargado automáticamente en futuras versiones

### Cómo ejecutar el pipeline

1. Asegúrate de tener el archivo crudo en `data/raw/games.json`
2. Ejecuta:

	python limpiadorDatos.py

### Cómo abrir la app

1. Ejecuta:

	python app.py

2. Ingresa el precio máximo y selecciona un género.
3. La pantalla mostrará los juegos ordenados por mejor valoración dentro de esos filtros.

### Criterio de ordenamiento

La valoración se calcula con la proporción de reseñas positivas de Steam. Si un juego no tiene reseñas, se usa la puntuación de Metacritic cuando está disponible.
