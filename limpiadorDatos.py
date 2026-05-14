"""Pipeline de limpieza para juegos de Steam.

Lee el archivo crudo data/raw/games.json, normaliza la información relevante
para recomendación por precio y género, y guarda los resultados en
data/processed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "games.json"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DATA_PATH = PROCESSED_DIR / "games_clean.csv"
GENRES_PATH = PROCESSED_DIR / "genres.json"

GENRE_SEPARATOR = " | "


def _safe_float(value: Any, default: float = 0.0) -> float:
	try:
		if value is None or value == "":
			return default
		return float(value)
	except (TypeError, ValueError):
		return default


def _safe_int(value: Any, default: int = 0) -> int:
	try:
		if value is None or value == "":
			return default
		return int(float(value))
	except (TypeError, ValueError):
		return default


def _normalize_text(value: Any) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _normalize_list(value: Any) -> list[str]:
	if not isinstance(value, list):
		return []

	cleaned: list[str] = []
	for item in value:
		text = _normalize_text(item)
		if text and text not in cleaned:
			cleaned.append(text)
	return cleaned


def _compute_rating_score(game: dict[str, Any]) -> tuple[float, int, str]:
	positive = _safe_int(game.get("positive"))
	negative = _safe_int(game.get("negative"))
	review_count = positive + negative

	if review_count > 0:
		return round((positive / review_count) * 100, 2), review_count, "steam_reviews"

	metacritic = _safe_float(game.get("metacritic_score"))
	if metacritic > 0:
		return round(metacritic, 2), 0, "metacritic"

	return 0.0, 0, "unknown"


def load_raw_dataset(raw_path: Path = RAW_DATA_PATH) -> dict[str, dict[str, Any]]:
	if not raw_path.exists():
		raise FileNotFoundError(
			f"No se encontró el archivo crudo en {raw_path}. Coloca games.json en data/raw/."
		)

	with raw_path.open("r", encoding="utf-8") as fin:
		return json.load(fin)


def clean_dataset(dataset: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
	cleaned_rows: list[dict[str, Any]] = []
	seen_genres: set[str] = set()

	for app_id, game in dataset.items():
		name = _normalize_text(game.get("name"))
		genres = _normalize_list(game.get("genres"))

		if not name or not genres:
			continue

		price = _safe_float(game.get("price"))
		rating_score, review_count, rating_source = _compute_rating_score(game)

		row = {
			"app_id": str(app_id),
			"name": name,
			"genres": GENRE_SEPARATOR.join(genres),
			"price": round(price, 2),
			"rating_score": rating_score,
			"review_count": review_count,
			"positive": _safe_int(game.get("positive")),
			"negative": _safe_int(game.get("negative")),
			"release_date": _normalize_text(game.get("release_date")),
			"developers": GENRE_SEPARATOR.join(_normalize_list(game.get("developers"))),
			"publishers": GENRE_SEPARATOR.join(_normalize_list(game.get("publishers"))),
			"short_description": _normalize_text(game.get("short_description")),
			"rating_source": rating_source,
		}
		cleaned_rows.append(row)

		for genre in genres:
			seen_genres.add(genre)

	cleaned_rows.sort(
		key=lambda row: (
			-float(row["rating_score"]),
			-int(row["review_count"]),
			float(row["price"]),
			row["name"].lower(),
		)
	)

	return cleaned_rows, sorted(seen_genres)


def save_processed_data(
	cleaned_rows: list[dict[str, Any]],
	genres: Iterable[str],
	processed_dir: Path = PROCESSED_DIR,
	processed_data_path: Path = PROCESSED_DATA_PATH,
	genres_path: Path = GENRES_PATH,
) -> None:
	processed_dir.mkdir(parents=True, exist_ok=True)

	fieldnames = [
		"app_id",
		"name",
		"genres",
		"price",
		"rating_score",
		"review_count",
		"positive",
		"negative",
		"release_date",
		"developers",
		"publishers",
		"short_description",
		"rating_source",
	]

	with processed_data_path.open("w", encoding="utf-8", newline="") as fout:
		writer = csv.DictWriter(fout, fieldnames=fieldnames)
		writer.writeheader()
		for row in cleaned_rows:
			writer.writerow(row)

	with genres_path.open("w", encoding="utf-8") as fout:
		json.dump(list(genres), fout, ensure_ascii=False, indent=2)


def build_pipeline() -> tuple[Path, Path]:
	dataset = load_raw_dataset()
	cleaned_rows, genres = clean_dataset(dataset)
	save_processed_data(cleaned_rows, genres)
	return PROCESSED_DATA_PATH, GENRES_PATH


def ensure_processed_data() -> tuple[Path, Path]:
	if PROCESSED_DATA_PATH.exists() and GENRES_PATH.exists():
		raw_mtime = RAW_DATA_PATH.stat().st_mtime if RAW_DATA_PATH.exists() else 0
		processed_mtime = min(PROCESSED_DATA_PATH.stat().st_mtime, GENRES_PATH.stat().st_mtime)
		if processed_mtime >= raw_mtime:
			return PROCESSED_DATA_PATH, GENRES_PATH

	return build_pipeline()


GENRE_ALIASES: dict[str, list[str]] = {
	"Todos": [],
	"Acción": ["Action"],
	"Aventura": ["Adventure"],
	"Casual": ["Casual"],
	"Indie": ["Indie"],
	"Rol / RPG": ["RPG"],
	"Simulación": ["Simulation"],
	"Estrategia": ["Strategy"],
	"Deportes": ["Sports"],
	"Carreras": ["Racing"],
	"Multijugador masivo": ["Massively Multiplayer"],
	"F2P": ["Free To Play"],
	"Acceso anticipado": ["Early Access"],
}


def available_genre_labels() -> list[str]:
	ensure_processed_data()
	with GENRES_PATH.open("r", encoding="utf-8") as fin:
		genres = json.load(fin)

	labels = ["Todos"]
	for label, steam_genres in GENRE_ALIASES.items():
		if label == "Todos":
			continue
		if any(genre in genres for genre in steam_genres):
			labels.append(label)

	# Agrega los géneros restantes que no tengan una etiqueta en español.
	used_steam_genres = {steam_genre for values in GENRE_ALIASES.values() for steam_genre in values}
	for genre in genres:
		if genre not in used_steam_genres:
			labels.append(genre)

	return labels


def genre_label_to_steam_genres(label: str) -> list[str]:
	return GENRE_ALIASES.get(label, [label] if label and label != "Todos" else [])


def recommend_games(max_price: float, genre_label: str = "Todos", limit: int = 20) -> list[dict[str, Any]]:
	ensure_processed_data()
	allowed_genres = set(genre_label_to_steam_genres(genre_label))

	matches: list[dict[str, Any]] = []
	with PROCESSED_DATA_PATH.open("r", encoding="utf-8", newline="") as fin:
		reader = csv.DictReader(fin)
		for row in reader:
			price = _safe_float(row.get("price"))
			if price > max_price:
				continue

			if allowed_genres:
				row_genres = set(_normalize_list(row.get("genres", "").split(GENRE_SEPARATOR)))
				if not row_genres.intersection(allowed_genres):
					continue

			matches.append(
				{
					"app_id": row.get("app_id", ""),
					"name": row.get("name", ""),
					"genres": row.get("genres", ""),
					"price": price,
					"rating_score": _safe_float(row.get("rating_score")),
					"review_count": _safe_int(row.get("review_count")),
					"release_date": row.get("release_date", ""),
					"short_description": row.get("short_description", ""),
				}
			)

	matches.sort(
		key=lambda row: (
			-float(row["rating_score"]),
			-int(row["review_count"]),
			float(row["price"]),
			row["name"].lower(),
		)
	)
	return matches[:limit]


def main() -> None:
	processed_data_path, genres_path = build_pipeline()
	print(f"Datos limpios guardados en: {processed_data_path}")
	print(f"Catálogo de géneros guardado en: {genres_path}")


if __name__ == "__main__":
	main()
