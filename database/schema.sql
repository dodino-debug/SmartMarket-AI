CREATE TABLE IF NOT EXISTS categories (
    id integer PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id integer PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id integer PRIMARY KEY,
    name text NOT NULL UNIQUE,
    category_id integer NOT NULL REFERENCES categories,
    supplier_id integer NOT NULL REFERENCES suppliers,
    price_cop integer NOT NULL CHECK (price_cop > 0)
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id integer PRIMARY KEY REFERENCES products,
    stock integer NOT NULL CHECK (stock >= 0),
    minimum integer NOT NULL CHECK (minimum > 0)
);

CREATE TABLE IF NOT EXISTS sales (
    id integer PRIMARY KEY,
    sold_on date NOT NULL
);

CREATE TABLE IF NOT EXISTS sale_items (
    sale_id integer REFERENCES sales,
    product_id integer REFERENCES products,
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price_cop integer NOT NULL CHECK (unit_price_cop > 0),
    PRIMARY KEY (sale_id, product_id)
);

CREATE INDEX IF NOT EXISTS sales_sold_on_idx ON sales (sold_on);
CREATE INDEX IF NOT EXISTS sale_items_product_idx ON sale_items (product_id);
