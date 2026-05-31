insert into products (id, title, category, base_price, inventory_count) values
  ('p_1001', 'Smart Running Shoes', 'sports', 89, 48),
  ('p_1002', 'Premium Leather Bag', 'fashion', 220, 15),
  ('p_1003', 'Noise Canceling Headphones', 'electronics', 179, 32),
  ('p_1004', 'Daily Essentials Bundle', 'grocery', 39, 64),
  ('p_1005', 'Designer Sunglasses', 'fashion', 140, 19),
  ('p_1006', 'Wireless Charger', 'electronics', 35, 70)
on conflict (id) do update
set
  title = excluded.title,
  category = excluded.category,
  base_price = excluded.base_price,
  inventory_count = excluded.inventory_count;
