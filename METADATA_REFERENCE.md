# Metadata JSON Reference

Quick reference for accessing product metadata fields in BigQuery queries.

## JSON Paths for Common Fields

### Basic Product Information

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| Product Name | `$.productDisplayName` | "Blue Floral Dress" |
| Product ID | Direct column | "10000" |
| Brand | `$.brandName` | "Brand Name" |
| Description | `$.productDescriptors.description.value` | "A beautiful summer dress..." |

### Pricing

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| MRP/Price | `$.price.mrp` | 199.99 |
| Currency | `$.price.currency` | "INR" or "USD" |

### Categorization

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| Category/Type | `$.articleType.typeName` | "Dress" |
| Subcategory | `$.subCategory` | "Casual Dresses" |
| Master Category | `$.masterCategory.typeName` | "Apparel" |
| Base Color | `$.baseColour` | "Blue" |

### Attributes

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| Gender | `$.gender` | "Women", "Men", "Unisex" |
| Season | `$.season` | "Summer", "Winter", "Fall", "Spring" |
| Usage | `$.usage` | "Casual", "Formal", "Sports" |
| Display Categories | `$.displayCategories` | "Dresses" |

## BigQuery Query Examples

### Extract Basic Fields

```sql
SELECT
  product_id,
  JSON_VALUE(metadata, '$.productDisplayName') as name,
  JSON_VALUE(metadata, '$.brandName') as brand,
  CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) as price,
  JSON_VALUE(metadata, '$.baseColour') as color,
  JSON_VALUE(metadata, '$.articleType.typeName') as category
FROM `your_dataset.product_embeddings`
LIMIT 10;
```

### Filter by Price Range

```sql
SELECT *
FROM `your_dataset.product_embeddings`
WHERE CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) BETWEEN 100 AND 500;
```

### Filter by Color

```sql
SELECT *
FROM `your_dataset.product_embeddings`
WHERE LOWER(JSON_VALUE(metadata, '$.baseColour')) IN ('blue', 'green', 'red');
```

### Filter by Category and Gender

```sql
SELECT *
FROM `your_dataset.product_embeddings`
WHERE LOWER(JSON_VALUE(metadata, '$.articleType.typeName')) LIKE '%dress%'
  AND LOWER(JSON_VALUE(metadata, '$.gender')) = 'women';
```

### Filter by Season

```sql
SELECT *
FROM `your_dataset.product_embeddings`
WHERE LOWER(JSON_VALUE(metadata, '$.season')) LIKE '%summer%';
```

### Complex Multi-Attribute Filter

```sql
SELECT
  product_id,
  JSON_VALUE(metadata, '$.productDisplayName') as name,
  CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) as price,
  JSON_VALUE(metadata, '$.baseColour') as color
FROM `your_dataset.product_embeddings`
WHERE CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) < 200
  AND LOWER(JSON_VALUE(metadata, '$.baseColour')) IN ('blue', 'green', 'mint', 'sage')
  AND LOWER(JSON_VALUE(metadata, '$.articleType.typeName')) LIKE '%dress%'
  AND LOWER(JSON_VALUE(metadata, '$.gender')) = 'women'
  AND LOWER(JSON_VALUE(metadata, '$.season')) LIKE '%summer%'
ORDER BY price ASC
LIMIT 20;
```

## Python Access Patterns

### Parsing Metadata in Python

```python
import json

# If metadata is a string
metadata = json.loads(row.get("metadata"))

# If metadata is already a dict
metadata = row.get("metadata", {})

# Access fields
name = metadata.get("productDisplayName", "Unknown")
brand = metadata.get("brandName", "")
price = metadata.get("price", {}).get("mrp", 0)
color = metadata.get("baseColour", "")
category = metadata.get("articleType", {}).get("typeName", "")
description = metadata.get("productDescriptors", {}).get("description", {}).get("value", "")
gender = metadata.get("gender", "")
season = metadata.get("season", "")
```

### Safe Nested Access

```python
def safe_get(data, *keys, default=None):
    """Safely access nested dictionary keys."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
    return data if data is not None else default

# Usage
price = safe_get(metadata, "price", "mrp", default=0)
description = safe_get(metadata, "productDescriptors", "description", "value", default="")
category = safe_get(metadata, "articleType", "typeName", default="Unknown")
```

## Common Metadata Patterns

### Full Product Object

```json
{
  "id": 10000,
  "productDisplayName": "Elegant Blue Dress",
  "brandName": "Fashion Brand",
  "price": {
    "mrp": 1999.0,
    "currency": "INR"
  },
  "baseColour": "Blue",
  "gender": "Women",
  "season": "Summer",
  "articleType": {
    "id": 123,
    "typeName": "Dress"
  },
  "masterCategory": {
    "typeName": "Apparel"
  },
  "subCategory": "Dresses",
  "usage": "Casual",
  "displayCategories": "Dresses",
  "productDescriptors": {
    "description": {
      "value": "A beautiful flowing dress perfect for summer occasions..."
    }
  },
  "variantName": "Midi Length",
  "styleImages": {
    "default": {
      "imageURL": "http://..."
    }
  }
}
```

## Troubleshooting

### Issue: NULL values when extracting JSON

**Cause**: Path doesn't exist or is spelled incorrectly

**Solution**: Check exact field names (case-sensitive)
```sql
-- Inspect full metadata structure
SELECT metadata
FROM `your_dataset.product_embeddings`
LIMIT 1;
```

### Issue: Type casting errors

**Cause**: JSON values are strings, need explicit casting

**Solution**: Always cast numeric values
```sql
-- Correct
CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64)

-- Incorrect (may cause errors in comparisons)
JSON_VALUE(metadata, '$.price.mrp')
```

### Issue: LIKE queries not matching

**Cause**: Case sensitivity

**Solution**: Use LOWER() for case-insensitive matching
```sql
WHERE LOWER(JSON_VALUE(metadata, '$.baseColour')) LIKE '%blue%'
```

## Performance Tips

1. **Index Frequently Queried Fields**: Consider creating computed columns for heavily queried JSON fields
2. **Avoid SELECT ***: Explicitly select only needed fields
3. **Filter Before Similarity**: Apply WHERE clauses before vector similarity calculations
4. **Cache Parsed JSON**: In Python, cache parsed metadata objects to avoid repeated JSON parsing

## Adding New Metadata Fields

If your metadata schema evolves:

1. Update `services/product_search_service.py` result parsing
2. Add new JSON_VALUE() extractions in SQL queries
3. Update the Product model in `main.py` if needed
4. Test with sample queries to ensure fields are accessible
