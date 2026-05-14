## Recomendador de juegos de Steam según precio y género

Este proyecto limpia el dataset crudo de Steam y genera un archivo procesado en data/processed para luego consultar recomendaciones por presupuesto y género.

### Archivos generados

- data/processed/games_clean.csv
- data/processed/genres.json

### Cómo ejecutar el pipeline

1. Asegúrate de tener el archivo crudo en data/raw/games.json.
2. Ejecuta:

	python limpiadorDatos.py

### Cómo abrir la app

1. Ejecuta:

	python app.py

2. Ingresa el precio máximo y selecciona un género.
3. La pantalla mostrará los juegos ordenados por mejor valoración dentro de esos filtros.

### Criterio de ordenamiento

La valoración se calcula con la proporción de reseñas positivas de Steam. Si un juego no tiene reseñas, se usa la puntuación de Metacritic cuando está disponible.
