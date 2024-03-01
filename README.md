Skrypty projektu Kryptoznaczek

# kz_market_count.py

Skrypt oblicza sumę kwot Zico na giełdzie KZ dla każdego użytkownika.

Skrypt korzysta z Polygonscan API i potrzebuje wygenerowanego api key ([instrukcja](https://docs.polygonscan.com/getting-started/viewing-api-usage-statistics)). Api key należy podmienić w kodzie skryptu.

Przykład użycia w celu obliczenia sumy kwot w lutym i marcu 2024:

```python kz_market_count.py 2024-02-01 2024-04-01```

Skrypt przyjmuje 2 parametry:
- pierwszy parametr określa początkową datę okresu, dla którego ma być liczona suma
- drugi parametr określa końcową datę okresu (północ), dla którego ma być liczona suma