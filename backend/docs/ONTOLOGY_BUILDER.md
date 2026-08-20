# Ontology Builder Feature

## Overview

The Ontology Builder is a lightweight feature that allows users to upload CSV files and automatically infer:
- **Entity Types**: Candidate classifications for columns (person, organization, location, event, etc.)
- **Relationships**: Suggested connections between columns based on naming patterns
- **Schema Mappings**: Recommended data types, constraints, and transformation rules

## Architecture

```
backend/ontology/
├── ontology_builder.py    # Core inference engine
└── __init__.py           # Module exports

backend/api/
└── ontology_routes.py    # REST API endpoints

backend/tests/
└── test_ontology_builder.py  # Comprehensive test suite

backend/synthetic/
└── sample_ontology.csv   # Sample data for testing
```

## Features

### Type Inference

The system uses pattern matching on column names to infer entity types:

| Type | Patterns Detected |
|------|------------------|
| person | name, person, user, employee, customer, contact |
| organization | company, org, organization, department, agency |
| location | address, city, country, location, place, state, zip |
| event | date, time, event, incident, meeting, occurrence |
| product | product, item, sku, inventory, goods |
| financial | amount, price, cost, revenue, payment, transaction |
| identifier | id, code, number, key, uuid, guid |
| timestamp | timestamp, created, updated, date_time, datetime |
| coordinate | lat, lon, longitude, latitude, coord |

### Data Type Detection

Automatically detects column data types:
- **Boolean**: true/false, yes/no, 1/0 values
- **Numeric**: Integer and floating-point numbers
- **DateTime**: Various date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **Email**: Valid email address patterns
- **URL**: HTTP/HTTPS URLs
- **Text**: Default for other string values

### Relationship Suggestions

Identifies potential relationships using:
- Foreign key naming conventions (`_id`, `_code`, `ref_`, `parent_`)
- Semantic relationship indicators (belongs_to, located_at, employed_by, etc.)
- Hierarchical patterns in column names

### Schema Mappings

Generates recommended schema elements:
- Target entity types
- Data types with nullable flags
- Constraints (UNIQUE, EMAIL_FORMAT, NON_NEGATIVE)
- Transformation rules (PARSE_DATETIME, TRIM_WHITESPACE)

## API Endpoints

### POST /api/ontology/analyze

Upload a CSV file for analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ontology/analyze" \
  -F "file=@data.csv" \
  -F "include_samples=true"
```

**Response:**
```json
{
  "success": true,
  "row_count": 100,
  "column_count": 10,
  "headers": ["id", "name", "email", ...],
  "inferred_types": {
    "name": {"type": "person", "confidence": 0.8, "reasoning": "..."},
    "email": {"type": "attribute", "confidence": 0.4, "reasoning": "..."}
  },
  "suggested_relationships": [
    {"source_column": "company_id", "relationship_type": "references", "target_column": "id", "confidence": 0.85}
  ],
  "schema_mappings": {...},
  "column_stats": {...},
  "sample_rows": [...]
}
```

### POST /api/ontology/analyze-text

Analyze CSV content provided as text.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ontology/analyze-text" \
  -F "csv_content=id,name,email\n1,John,john@example.com" \
  -F "include_samples=true"
```

### POST /api/ontology/export

Export inferred ontology in JSON or CSV format.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ontology/export" \
  -F "csv_content=id,name\n1,John" \
  -F "format=json"
```

### GET /api/ontology/patterns

Get all patterns used for type inference.

**Request:**
```bash
curl "http://localhost:8000/api/ontology/patterns"
```

## Usage Examples

### Python SDK Example

```python
from backend.ontology.ontology_builder import OntologyBuilder

# Initialize builder
builder = OntologyBuilder()

# Read CSV
with open('data.csv', 'r') as f:
    csv_content = f.read()

# Analyze
result = builder.analyze_csv(csv_content)

if result['success']:
    print(f"Found {result['row_count']} rows")
    print(f"Inferred {len(result['inferred_types'])} types")
    print(f"Suggested {len(result['suggested_relationships'])} relationships")
    
    # Export results
    json_output = builder.export_ontology(format='json')
    csv_output = builder.export_ontology(format='csv')
```

### Frontend Integration Example

```typescript
// Upload CSV for analysis
async function analyzeCSV(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('include_samples', 'true');
  
  const response = await fetch('/api/ontology/analyze', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Display results
const result = await analyzeCSV(myFile);
console.log('Inferred types:', result.inferred_types);
console.log('Relationships:', result.suggested_relationships);
```

## Testing

Run the test suite:

```bash
cd /workspace
python -m pytest backend/tests/test_ontology_builder.py -v
```

All 20 tests should pass, covering:
- Basic CSV analysis
- Type inference
- Relationship suggestions
- Schema mappings
- Column statistics
- Complex data types
- Export functionality
- Edge cases (empty files, special characters, Unicode, etc.)

## Sample Data

A sample CSV file is provided at `backend/synthetic/sample_ontology.csv` containing:
- 10 employee records
- 11 columns with various data types
- Mixed entity types (persons, organizations, locations)
- Boolean, numeric, datetime, and email fields

## Confidence Scoring

All inferences include confidence scores:
- **0.8-0.9**: High confidence (strong pattern match)
- **0.6-0.7**: Medium confidence (partial pattern match)
- **0.4-0.5**: Low confidence (default/heuristic-based)

## Limitations

- Pattern-based inference may not catch domain-specific terminology
- Relationship detection relies on naming conventions
- No cross-file ontology building (single CSV only)
- Statistical analysis uses basic methods (not ML-based)

## Future Enhancements

Potential improvements:
- Machine learning-based type inference
- Cross-reference multiple CSV files
- Custom pattern configuration
- Ontology validation and refinement UI
- Graph database export
- Schema evolution tracking
