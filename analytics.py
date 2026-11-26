def dashboard(connection):
    monthly = connection.execute("""
        SELECT to_char(date_trunc('month', sold_on), 'YYYY-MM') AS month,
               count(DISTINCT sales.id) AS transactions,
               sum(quantity) AS units, sum(quantity::bigint * unit_price_cop) AS revenue
        FROM sales JOIN sale_items ON sale_id = sales.id
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    categories = connection.execute("""
        SELECT c.name, coalesce(sum(d.quantity::bigint * d.unit_price_cop), 0) AS revenue
        FROM categories c LEFT JOIN products p ON c.id = p.category_id
        LEFT JOIN sale_items d ON d.product_id = p.id
        GROUP BY c.id ORDER BY revenue DESC, c.name
    """).fetchall()
    products = connection.execute("""
        SELECT p.name, i.stock, i.minimum, coalesce(sum(d.quantity), 0) AS units,
               coalesce(sum(d.quantity) FILTER (
                   WHERE s.sold_on >= date_trunc('month', latest.sold_on)
               ), 0) AS latest_units
        FROM products p JOIN inventory i ON p.id = i.product_id
        CROSS JOIN (SELECT max(sold_on) AS sold_on FROM sales) latest
        LEFT JOIN sale_items d ON p.id = d.product_id
        LEFT JOIN sales s ON s.id = d.sale_id
        GROUP BY p.id, i.stock, i.minimum ORDER BY units DESC, p.name
    """).fetchall()
    for row in monthly + categories:
        row["revenue"] = int(row["revenue"])

    alerts = [product for product in products if product["stock"] < product["minimum"]]
    priority = [product for product in alerts if product["latest_units"] >= 30]
    last_three = monthly[-3:]
    declining = False
    if len(last_three) == 3:
        first, second, third = last_three
        month_numbers = [int(row["month"][:4]) * 12 + int(row["month"][5:])
                         for row in last_three]
        declining = (month_numbers[2] - month_numbers[0] == 2
                     and first["revenue"] > second["revenue"] > third["revenue"])

    return dict(monthly=monthly, categories=categories, products=products,
                alerts=alerts, priority=priority, declining=declining,
                revenue=sum(row["revenue"] for row in monthly),
                transactions=sum(row["transactions"] for row in monthly),
                units=sum(row["units"] for row in monthly))
