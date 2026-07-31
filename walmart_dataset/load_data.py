import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

# Database connection string
conn_string = os.environ["POSTGRES_CONNECTION_STRING"]

# CSV files mapping to tables
csv_files = {
    "customers.csv": "raw.customers",
    "stores.csv": "raw.stores",
    "products.csv": "raw.products",
    "employees.csv": "raw.employees",
    "orders.csv": "raw.orders",
    "order_items.csv": "raw.order_items",
}

data_dir = "data"

conn = psycopg.connect(conn_string)

try:
    with conn.cursor() as cursor:
        # Load each CSV file into its corresponding table
        for csv_file, table_name in csv_files.items():
            csv_path = os.path.join(data_dir, csv_file)

            if os.path.exists(csv_path):
                print(f"Loading {csv_file} into {table_name}...")

                with open(csv_path, "r") as f, cursor.copy(
                    f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
                ) as copy:
                    while data := f.read(8192):
                        copy.write(data)

                conn.commit()
                print(f"✓ Successfully loaded {csv_file}")
            else:
                print(f"✗ File not found: {csv_path}")

    print("\n✓ All data loaded successfully!")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
    raise

finally:
    conn.close()
