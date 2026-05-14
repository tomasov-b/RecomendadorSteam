"""Interfaz gráfica para recomendar juegos de Steam por precio y género."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from limpiadorDatos import available_genre_labels, recommend_games


class SteamRecommenderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Recomendador de juegos de Steam")
        self.root.geometry("1050x700")
        self.root.minsize(950, 620)
        self.current_matches: list[dict[str, object]] = []
        self.price_sort_desc = True

        self._build_styles()
        self._build_layout()

    def _build_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Recomendador de juegos de Steam",
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Filtra por presupuesto y género. La lista se ordena por mejor valoración.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        filters = ttk.LabelFrame(container, text="Filtros", padding=14)
        filters.pack(fill="x", pady=(16, 12))

        ttk.Label(filters, text="Presupuesto máximo (USD):").grid(row=0, column=0, sticky="w")
        self.price_var = tk.StringVar(value="20")
        price_entry = ttk.Entry(filters, textvariable=self.price_var, width=18)
        price_entry.grid(row=0, column=1, sticky="w", padx=(10, 24))

        ttk.Label(filters, text="Género: ").grid(row=0, column=2, sticky="w")
        self.genre_var = tk.StringVar(value="Todos")
        self.genre_combo = ttk.Combobox(
            filters,
            textvariable=self.genre_var,
            values=available_genre_labels(),
            state="readonly",
            width=26,
        )
        self.genre_combo.grid(row=0, column=3, sticky="w", padx=(10, 24))

        search_button = ttk.Button(filters, text="Buscar recomendados", style="Action.TButton", command=self.search)
        search_button.grid(row=0, column=4, sticky="w")

        filters.columnconfigure(5, weight=1)

        self.results_info = ttk.Label(container, text="Listo para buscar.")
        self.results_info.pack(anchor="w", pady=(0, 8))

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "genres", "price", "rating", "reviews", "release")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        headings = {
            "name": "Juego",
            "genres": "Géneros",
            "price": "Precio",
            "rating": "Valoración",
            "reviews": "Reseñas",
            "release": "Lanzamiento",
        }
        widths = {
            "name": 280,
            "genres": 240,
            "price": 90,
            "rating": 100,
            "reviews": 100,
            "release": 120,
        }
        for column in columns:
            if column == "price":
                self.tree.heading(column, text=headings[column], command=self.sort_by_price)
            else:
                self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w", stretch=(column in {"name", "genres"}))

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self._load_initial_results()

    def _load_initial_results(self) -> None:
        self.search()

    def _clear_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _display_matches(self, matches: list[dict[str, object]]) -> None:
        self._clear_tree()
        for game in matches:
            self.tree.insert(
                "",
                "end",
                values=(
                    game["name"],
                    game["genres"],
                    f"${float(game['price']):.2f}",
                    f"{float(game['rating_score']):.2f}",
                    int(game["review_count"]),
                    game["release_date"],
                ),
            )

    def sort_by_price(self) -> None:
        if not self.current_matches:
            return

        self.current_matches.sort(key=lambda game: float(game["price"]), reverse=self.price_sort_desc)
        self.price_sort_desc = not self.price_sort_desc
        self._display_matches(self.current_matches)

    def search(self) -> None:
        try:
            max_price = float(self.price_var.get())
            if max_price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Presupuesto inválido", "Ingresa un precio válido mayor o igual a 0.")
            return

        genre = self.genre_var.get().strip() or "Todos"
        matches = recommend_games(max_price=max_price, genre_label=genre, limit=50)
        self.current_matches = list(matches)
        self.price_sort_desc = True
        self._display_matches(self.current_matches)

        self.results_info.config(
            text=f"Se encontraron {len(matches)} juegos para presupuesto ≤ ${max_price:.2f} y género '{genre}'."
        )


def main() -> None:
    root = tk.Tk()
    app = SteamRecommenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()