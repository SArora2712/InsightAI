"""
InsightAI - Human-readable schema metadata for the Northwind database.
This is the source of truth consumed by the schema-linking retriever (Step 2)
and, downstream, injected into the NL->SQL prompt (Step 3).

Excludes:
- CustomerCustomerDemo, CustomerDemographics (empty, 0 rows in this build)
- sqlite_sequence (internal SQLite bookkeeping table)
"""

# Tables with a space in their name need quoting in generated SQL.
# We track this explicitly so the SQL-generation prompt can warn the LLM.
QUOTED_TABLES = {"Order Details"}


SCHEMA_METADATA = {
    "Customers": {
        "description": "Customer companies who place orders. One row per customer account.",
        "columns": {
            "CustomerID": "Unique customer identifier (text code, e.g. 'ALFKI')",
            "CompanyName": "Customer's company name",
            "ContactName": "Primary contact person at the customer",
            "ContactTitle": "Job title of the contact person",
            "City": "Customer's city",
            "Region": "Customer's state/region (may be blank for non-US)",
            "Country": "Customer's country",
        },
        "primary_key": "CustomerID",
        "foreign_keys": {},
    },
    "Employees": {
        "description": "Sales employees who take and process orders.",
        "columns": {
            "EmployeeID": "Unique employee identifier",
            "LastName": "Employee last name",
            "FirstName": "Employee first name",
            "Title": "Job title (e.g. 'Sales Representative')",
            "City": "Employee's city",
            "Country": "Employee's country",
            "ReportsTo": "EmployeeID of this employee's manager (self-referencing)",
        },
        "primary_key": "EmployeeID",
        "foreign_keys": {"ReportsTo": "Employees.EmployeeID"},
    },
    "Orders": {
        "description": (
            "Orders placed by customers. One row per order; does not contain "
            "line-item detail or revenue amounts directly - join to 'Order Details' for that."
        ),
        "columns": {
            "OrderID": "Unique order identifier",
            "CustomerID": "Which customer placed the order",
            "EmployeeID": "Which employee processed the order",
            "OrderDate": "Date the order was placed",
            "RequiredDate": "Date the order was due to ship",
            "ShippedDate": "Date the order actually shipped (NULL if not yet shipped)",
            "ShipVia": "Shipper used (foreign key to Shippers)",
            "Freight": "Shipping cost charged",
            "ShipCountry": "Country the order was shipped to",
        },
        "primary_key": "OrderID",
        "foreign_keys": {
            "CustomerID": "Customers.CustomerID",
            "EmployeeID": "Employees.EmployeeID",
            "ShipVia": "Shippers.ShipperID",
        },
    },
    "Order Details": {
        "description": (
            "Line items within an order - THIS is where revenue/quantity/pricing lives. "
            "To compute revenue: SUM(UnitPrice * Quantity * (1 - Discount)). "
            "IMPORTANT: table name has a space, must be quoted as \"Order Details\" in SQL."
        ),
        "columns": {
            "OrderID": "Which order this line item belongs to",
            "ProductID": "Which product was sold",
            "UnitPrice": "Price per unit at time of sale",
            "Quantity": "Number of units sold",
            "Discount": "Discount applied, as a decimal fraction (e.g. 0.15 = 15% off)",
        },
        "primary_key": "OrderID, ProductID",
        "foreign_keys": {
            "OrderID": "Orders.OrderID",
            "ProductID": "Products.ProductID",
        },
    },
    "Products": {
        "description": "Product catalog.",
        "columns": {
            "ProductID": "Unique product identifier",
            "ProductName": "Product name",
            "SupplierID": "Which supplier provides this product",
            "CategoryID": "Which category this product belongs to",
            "UnitPrice": "Current list price per unit",
            "UnitsInStock": "Current inventory count",
            "Discontinued": "1 if the product is discontinued, 0 otherwise",
        },
        "primary_key": "ProductID",
        "foreign_keys": {
            "SupplierID": "Suppliers.SupplierID",
            "CategoryID": "Categories.CategoryID",
        },
    },
    "Categories": {
        "description": "Product categories (e.g. Beverages, Condiments, Seafood).",
        "columns": {
            "CategoryID": "Unique category identifier",
            "CategoryName": "Category name",
            "Description": "Category description text",
        },
        "primary_key": "CategoryID",
        "foreign_keys": {},
    },
    "Suppliers": {
        "description": "Companies that supply products.",
        "columns": {
            "SupplierID": "Unique supplier identifier",
            "CompanyName": "Supplier company name",
            "City": "Supplier's city",
            "Country": "Supplier's country",
        },
        "primary_key": "SupplierID",
        "foreign_keys": {},
    },
    "Shippers": {
        "description": "Shipping companies used to deliver orders.",
        "columns": {
            "ShipperID": "Unique shipper identifier",
            "CompanyName": "Shipping company name",
            "Phone": "Shipper phone number",
        },
        "primary_key": "ShipperID",
        "foreign_keys": {},
    },
    "Territories": {
        "description": "Sales territories, grouped into regions.",
        "columns": {
            "TerritoryID": "Unique territory identifier",
            "TerritoryDescription": "Territory name",
            "RegionID": "Which region this territory belongs to",
        },
        "primary_key": "TerritoryID",
        "foreign_keys": {"RegionID": "Regions.RegionID"},
    },
    "Regions": {
        "description": "Top-level geographic sales regions.",
        "columns": {
            "RegionID": "Unique region identifier",
            "RegionDescription": "Region name",
        },
        "primary_key": "RegionID",
        "foreign_keys": {},
    },
    "EmployeeTerritories": {
        "description": "Junction table linking employees to the territories they cover.",
        "columns": {
            "EmployeeID": "Employee assigned to the territory",
            "TerritoryID": "Territory the employee covers",
        },
        "primary_key": "EmployeeID, TerritoryID",
        "foreign_keys": {
            "EmployeeID": "Employees.EmployeeID",
            "TerritoryID": "Territories.TerritoryID",
        },
    },
}
# Add an "aliases" list to each table entry to capture common phrasings
# that don't lexically match the table/column names, e.g. "shipping companies" -> Shippers.
SCHEMA_ALIASES = {
    "Customers": ["clients", "accounts", "buyers"],
    "Employees": ["staff", "sales reps", "salespeople", "workers"],
    "Orders": ["purchases", "transactions", "sales orders"],
    "Order Details": ["order line items", "order lines", "revenue", "sales amount", "line items"],
    "Products": ["items", "inventory", "catalog", "merchandise"],
    "Categories": ["product types", "product groups"],
    "Suppliers": ["vendors", "manufacturers"],
    "Shippers": ["shipping companies", "carriers", "freight companies", "delivery companies"],
    "Territories": ["sales areas", "sales zones"],
    "Regions": ["geographic regions", "areas"],
    
    "EmployeeTerritories": ["employee coverage", "rep assignments"],
}

def table_to_document(table_name: str) -> str:
    """
    Flatten a table's metadata into a single text blob for embedding.
    Used by the schema linker to build its searchable index.
    """
    meta = SCHEMA_METADATA[table_name]
    col_lines = [f"{col}: {desc}" for col, desc in meta["columns"].items()]
    fk_lines = [f"{col} references {ref}" for col, ref in meta["foreign_keys"].items()]

    parts = [
        f"Table: {table_name}",
        f"Description: {meta['description']}",
        "Columns: " + "; ".join(col_lines),
    ]
    if fk_lines:
        parts.append("Relationships: " + "; ".join(fk_lines))

    aliases = SCHEMA_ALIASES.get(table_name, [])
    if aliases:
        parts.append("Also known as: " + ", ".join(aliases))

    return "\n".join(parts)


def format_table_for_prompt(table_name: str) -> str:
    """
    Format a table's schema for injection into the SQL-generation prompt.
    More compact than table_to_document - optimized for LLM consumption, not embedding.
    """
    meta = SCHEMA_METADATA[table_name]
    quoted = f'"{table_name}"' if table_name in QUOTED_TABLES else table_name
    cols = ", ".join(meta["columns"].keys())
    lines = [f"- {quoted} ({meta['description']})", f"  Columns: {cols}"]
    if meta["foreign_keys"]:
        fks = "; ".join(f"{c} -> {r}" for c, r in meta["foreign_keys"].items())
        lines.append(f"  Foreign keys: {fks}")
    return "\n".join(lines)


ALL_TABLES = list(SCHEMA_METADATA.keys())