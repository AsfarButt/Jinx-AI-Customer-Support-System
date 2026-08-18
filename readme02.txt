customers.csv — the customer table: ID, name, email, region.
customers_dirty_index.csv — ground truth flagging which customer rows are deliberately messy (dupes, casing issues, near-duplicates) and their linked counterpart.
orders.csv.gz — the core transactional table: order ID, customer, product, warehouse, date, status, tracking ID.
tracking.csv.gz — one row per order: carrier, status history, last updated.
returns.csv — return records: which order, which customer/product, reason, refund status.
returns_outside_window_index.csv — ground truth flagging which returns are deliberate "outside normal window" exceptions (goodwill/defective-item cases), not bugs.
products.csv — the product catalog: ID, name, category, price, region availability.
warehouses.csv — reference table of warehouses (region, country, capacity tier).
shipping_partners.csv — reference table of contracted logistics partners (distinct from carriers).
carriers.csv — reference table of the 5 last-mile delivery carriers and which regions each serves.
tickets.jsonl.gz — the labeled support-email archive: sender, subject, body, category, resolved customer/order (or unresolved, ~15% of the time).