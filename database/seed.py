import random
from datetime import date


CATALOG = {
    "Despensa": ("Arroz", "Fríjoles", "Lentejas", "Pasta", "Harina", "Aceite"),
    "Bebidas": ("Agua", "Café", "Jugo de mango", "Té", "Gaseosa", "Avena líquida"),
    "Refrigerados": ("Leche", "Yogur", "Queso", "Mantequilla", "Crema", "Kumis"),
    "Aseo": ("Jabón", "Detergente", "Champú", "Desinfectante", "Cloro", "Suavizante"),
    "Hogar": ("Servilletas", "Esponja", "Papel aluminio", "Bolsas", "Velas", "Paños"),
}
SUPPLIERS = ("Abastos Andinos", "Bebidas del Valle", "Lácteos Sabana",
             "Aseo Central", "Hogar del Norte")
MONTHLY_VOLUME = (18, 24, 30, 26, 32, 34, 38, 36, 42, 50, 39, 25)


def seed(connection):
    rng = random.Random(1729)
    products = []
    for category_id, (category, names) in enumerate(CATALOG.items(), 1):
        for name in names:
            products.append((len(products) + 1, name, category_id, category_id,
                             rng.randrange(25, 160) * 100))

    sales, items = [], []
    for month, volume in enumerate(MONTHLY_VOLUME, 1):
        for day in range(volume):
            sale_id = len(sales) + 1
            sales.append((sale_id, date(2025, month, day % 28 + 1)))
            product_id = day % len(products) + 1
            _, _, _, _, price = products[product_id - 1]
            items.append((sale_id, product_id, rng.randint(1, 3), price))
            if product_id != 1:
                items.append((sale_id, 1, 2, products[0][-1]))

    with connection.cursor() as cursor:
        cursor.executemany("INSERT INTO categories VALUES (%s, %s) ON CONFLICT DO NOTHING",
                           enumerate(CATALOG, 1))
        cursor.executemany("INSERT INTO suppliers VALUES (%s, %s) ON CONFLICT DO NOTHING",
                           enumerate(SUPPLIERS, 1))
        cursor.executemany("INSERT INTO products VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                           products)
        inventory = [(product_id, 2 if product_id in {1, 9, 19} else rng.randint(6, 40), 6)
                     for product_id, *_ in products]
        cursor.executemany("INSERT INTO inventory VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                           inventory)
        cursor.executemany("INSERT INTO sales VALUES (%s, %s) ON CONFLICT DO NOTHING", sales)
        cursor.executemany("INSERT INTO sale_items VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                           items)
