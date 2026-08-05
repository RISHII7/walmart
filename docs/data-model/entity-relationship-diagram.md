# Entity-Relationship Diagrams

## Raw / Bronze — operational schema

This is the shape of the data as it exists at source, before any dbt transformation.

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    STORES ||--o{ ORDERS : fulfills
    STORES ||--o{ EMPLOYEES : employs
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : "sold as"

    CUSTOMERS {
        bigint customer_id PK
        string first_name
        string last_name
        string email
        string phone
        string city
        string province
        string country
        char is_active
    }
    STORES {
        bigint store_id PK
        string store_name
        string city
        string province
        string country
        char is_active
    }
    EMPLOYEES {
        bigint employee_id PK
        bigint store_id FK
        string first_name
        string last_name
        string job_title
        numeric salary
        char is_active
    }
    PRODUCTS {
        bigint product_id PK
        string product_name
        string category
        string brand
        numeric price
        char is_active
    }
    ORDERS {
        bigint order_id PK
        bigint customer_id FK
        bigint store_id FK
        timestamp order_timestamp
        string payment_method
        string order_status
        numeric total_amount
        char is_active
    }
    ORDER_ITEMS {
        bigint order_item_id PK
        bigint order_id FK
        bigint product_id FK
        int quantity
        numeric unit_price
        numeric line_amount
        char is_active
    }
```

## Gold — star schema

The conformed dimensional model that analytics actually queries: `fact_orders` at the
center, joined out to five SCD Type 2 dimension snapshots.

```mermaid
erDiagram
    FACT_ORDERS }o--|| DIM_CUSTOMERS : customer_id
    FACT_ORDERS }o--|| DIM_ORDERS : order_id
    FACT_ORDERS }o--|| DIM_PRODUCTS : product_id
    FACT_ORDERS }o--|| DIM_EMPLOYEES : employee_id
    FACT_ORDERS }o--|| DIM_STORES : store_id

    FACT_ORDERS {
        bigint order_id FK
        bigint order_item_id
        bigint product_id FK
        bigint store_id FK
        bigint employee_id FK
        bigint customer_id FK
        numeric total_amount
        int quantity
        numeric unit_price
        numeric line_amount
    }
    DIM_CUSTOMERS {
        bigint customer_id PK
        string customer_first_name
        string customer_last_name
        string customer_email
        string customer_city
        timestamp dbt_valid_from
        timestamp dbt_valid_to
    }
    DIM_ORDERS {
        bigint order_id PK
        bigint order_item_id
        string payment_method
        string order_status
        timestamp dbt_valid_from
        timestamp dbt_valid_to
    }
    DIM_PRODUCTS {
        bigint product_id PK
        string product_name
        string category
        string brand
        numeric price
        timestamp dbt_valid_from
        timestamp dbt_valid_to
    }
    DIM_EMPLOYEES {
        bigint employee_id PK
        string employee_first_name
        string job_title
        numeric salary
        timestamp dbt_valid_from
        timestamp dbt_valid_to
    }
    DIM_STORES {
        bigint store_id PK
        string store_name
        string store_city
        timestamp dbt_valid_from
        timestamp dbt_valid_to
    }
```

Note the fact table joins to dimensions by natural key (`customer_id`, `order_id`, etc.),
not by a surrogate snapshot key — point-in-time-correct joins are achieved by additionally
filtering the dimension snapshot on `dbt_valid_from <= <as-of-date> < dbt_valid_to`, not
by carrying `dbt_scd_id` on the fact row itself.

## Silver → Gold lineage (model level)

```mermaid
flowchart LR
    customers_t --> obt_b
    employees_t --> obt_b
    order_items_t --> obt_b
    orders_t --> obt_b
    products_t --> obt_b
    stores_t --> obt_b

    obt_b --> eph_customers --> dim_customers
    obt_b --> eph_employees --> dim_employees
    obt_b --> eph_orders --> dim_orders
    obt_b --> eph_products --> dim_products
    obt_b --> eph_stores --> dim_stores
    obt_b --> fact_orders
```
