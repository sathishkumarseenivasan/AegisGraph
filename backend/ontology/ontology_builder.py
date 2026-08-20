"""
Ontology Builder Module.

Provides lightweight ontology inference from CSV uploads:
- Infers candidate entity types
- Suggests relationships
- Recommends schema mappings
"""
import csv
import io
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime
import hashlib


class OntologyBuilder:
    """Builds candidate ontologies from CSV data."""
    
    # Common patterns for type inference
    TYPE_PATTERNS = {
        'person': [r'name', r'person', r'user', r'employee', r'customer', r'contact'],
        'organization': [r'company', r'org', r'organization', r'department', r'agency'],
        'location': [r'address', r'city', r'country', r'location', r'place', r'state', r'zip'],
        'event': [r'date', r'time', r'event', r'incident', r'meeting', r'occurrence'],
        'product': [r'product', r'item', r'sku', r'inventory', r'goods'],
        'financial': [r'amount', r'price', r'cost', r'revenue', r'payment', r'transaction'],
        'identifier': [r'id', r'code', r'number', r'key', r'uuid', r'guid'],
        'timestamp': [r'timestamp', r'created', r'updated', r'date_time', r'datetime'],
        'coordinate': [r'lat', r'lon', r'longitude', r'latitude', r'coord'],
    }
    
    # Common relationship indicators
    RELATIONSHIP_PATTERNS = {
        'belongs_to': [r'belongs', r'owned by', r'part of', r'member of'],
        'located_at': [r'located at', r'situated in', r'based in', r'headquartered'],
        'employed_by': [r'works for', r'employed by', r'employee of'],
        'connected_to': [r'connected to', r'linked with', r'associated with'],
        'interacted_with': [r'interacted', r'contacted', r'met with', 'communicated'],
        'transaction_with': [r'purchased from', r'sold to', r'paid to', r'received from'],
    }
    
    def __init__(self):
        self.inferred_types: Dict[str, str] = {}
        self.suggested_relationships: List[Dict[str, Any]] = []
        self.schema_mappings: Dict[str, Dict[str, Any]] = {}
        self.column_stats: Dict[str, Dict[str, Any]] = {}
    
    def analyze_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Analyze CSV content and infer ontology elements.
        
        Args:
            csv_content: Raw CSV string content
            
        Returns:
            Dictionary containing inferred types, relationships, and mappings
        """
        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)
            
            if not rows:
                return {
                    'success': False,
                    'error': 'Empty CSV file',
                    'inferred_types': {},
                    'suggested_relationships': [],
                    'schema_mappings': {}
                }
            
            # Analyze columns
            headers = list(rows[0].keys())
            self._analyze_columns(headers, rows)
            
            # Infer entity types
            self._infer_entity_types(headers)
            
            # Suggest relationships
            self._suggest_relationships(headers, rows)
            
            # Generate schema mappings
            self._generate_schema_mappings(headers)
            
            return {
                'success': True,
                'row_count': len(rows),
                'column_count': len(headers),
                'headers': headers,
                'inferred_types': self.inferred_types,
                'suggested_relationships': self.suggested_relationships,
                'schema_mappings': self.schema_mappings,
                'column_stats': self.column_stats,
                'sample_rows': rows[:3]  # Include first 3 rows as samples
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'inferred_types': {},
                'suggested_relationships': [],
                'schema_mappings': {}
            }
    
    def _analyze_columns(self, headers: List[str], rows: List[Dict]) -> None:
        """Analyze column characteristics."""
        self.column_stats = {}
        
        for header in headers:
            values = [row.get(header, '') for row in rows if row.get(header)]
            
            stats = {
                'name': header,
                'non_empty_count': len(values),
                'empty_count': len(rows) - len(values),
                'unique_count': len(set(values)),
                'sample_values': list(set(values))[:5],
                'data_type': self._infer_data_type(values),
                'pattern_matches': self._match_patterns(header)
            }
            
            # Additional analysis for numeric values
            if stats['data_type'] == 'numeric':
                try:
                    numeric_values = [float(v) for v in values if v]
                    stats['min_value'] = min(numeric_values)
                    stats['max_value'] = max(numeric_values)
                    stats['avg_value'] = sum(numeric_values) / len(numeric_values)
                except (ValueError, TypeError):
                    pass
            
            self.column_stats[header] = stats
    
    def _infer_data_type(self, values: List[str]) -> str:
        """Infer the data type of a column."""
        if not values:
            return 'unknown'
        
        # Check for boolean
        bool_values = {'true', 'false', 'yes', 'no', '1', '0'}
        if all(v.lower() in bool_values for v in values[:10]):
            return 'boolean'
        
        # Check for numeric
        try:
            [float(v) for v in values[:10] if v]
            return 'numeric'
        except ValueError:
            pass
        
        # Check for date/timestamp
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{4}/\d{2}/\d{2}'
        ]
        for pattern in date_patterns:
            if all(re.search(pattern, v) for v in values[:5] if v):
                return 'datetime'
        
        # Check for email
        if all(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v) for v in values[:5] if v):
            return 'email'
        
        # Check for URL
        if all(v.startswith(('http://', 'https://')) for v in values[:5] if v):
            return 'url'
        
        return 'text'
    
    def _match_patterns(self, column_name: str) -> List[str]:
        """Match column name against known patterns."""
        matches = []
        column_lower = column_name.lower()
        
        for type_name, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, column_lower):
                    matches.append(type_name)
                    break
        
        return list(set(matches))
    
    def _infer_entity_types(self, headers: List[str]) -> None:
        """Infer entity types from column names and statistics."""
        self.inferred_types = {}
        
        for header in headers:
            stats = self.column_stats.get(header, {})
            pattern_matches = stats.get('pattern_matches', [])
            
            # Determine most likely type
            if pattern_matches:
                # Use the most specific match (first in priority order)
                for type_name in ['person', 'organization', 'location', 'event', 'product']:
                    if type_name in pattern_matches:
                        self.inferred_types[header] = {
                            'type': type_name,
                            'confidence': 0.8,
                            'reasoning': f"Column name matches '{type_name}' pattern"
                        }
                        break
                else:
                    # Use first match if no high-priority type found
                    primary_type = pattern_matches[0]
                    self.inferred_types[header] = {
                        'type': primary_type,
                        'confidence': 0.6,
                        'reasoning': f"Column name matches '{primary_type}' pattern"
                    }
            elif stats.get('data_type') == 'text' and stats.get('unique_count', 0) > len(stats.get('sample_values', [])):
                # High cardinality text field might be an identifier
                if 'id' in header.lower() or 'code' in header.lower():
                    self.inferred_types[header] = {
                        'type': 'identifier',
                        'confidence': 0.9,
                        'reasoning': "High cardinality text field with ID-like naming"
                    }
                else:
                    self.inferred_types[header] = {
                        'type': 'attribute',
                        'confidence': 0.5,
                        'reasoning': "Text field with moderate uniqueness"
                    }
            else:
                self.inferred_types[header] = {
                    'type': 'attribute',
                    'confidence': 0.4,
                    'reasoning': "Default classification as attribute"
                }
    
    def _suggest_relationships(self, headers: List[str], rows: List[Dict]) -> None:
        """Suggest potential relationships between columns."""
        self.suggested_relationships = []
        
        # Look for foreign key patterns
        id_columns = [h for h in headers if 'id' in h.lower() or 'code' in h.lower()]
        ref_columns = [h for h in headers if any(pattern in h.lower() 
                          for pattern in ['_id', '_code', 'ref_', 'parent_', 'source_'])]
        
        # Suggest relationships based on naming conventions
        for header in headers:
            for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, header.lower()):
                        # Try to find target column
                        target_candidates = [h for h in headers 
                                           if h != header and 
                                           ('id' in h.lower() or 'name' in h.lower())]
                        
                        if target_candidates:
                            self.suggested_relationships.append({
                                'source_column': header,
                                'relationship_type': rel_type,
                                'target_column': target_candidates[0],
                                'confidence': 0.7,
                                'reasoning': f"Column name suggests '{rel_type}' relationship"
                            })
        
        # Suggest hierarchical relationships based on ID patterns
        for id_col in id_columns:
            base_name = id_col.replace('_id', '').replace('_code', '')
            potential_refs = [h for h in headers 
                             if h != id_col and 
                             (h.endswith(f'_{base_name}') or 
                              h.startswith(f'{base_name}_'))]
            
            for ref_col in potential_refs:
                self.suggested_relationships.append({
                    'source_column': ref_col,
                    'relationship_type': 'references',
                    'target_column': id_col,
                    'confidence': 0.85,
                    'reasoning': "Naming convention suggests foreign key relationship"
                })
    
    def _generate_schema_mappings(self, headers: List[str]) -> None:
        """Generate suggested schema mappings."""
        self.schema_mappings = {}
        
        for header in headers:
            stats = self.column_stats.get(header, {})
            type_info = self.inferred_types.get(header, {})
            
            mapping = {
                'source_column': header,
                'suggested_target_type': type_info.get('type', 'attribute'),
                'data_type': stats.get('data_type', 'text'),
                'nullable': stats.get('empty_count', 0) > 0,
                'unique': stats.get('unique_count', 0) == stats.get('non_empty_count', 0),
                'suggested_constraints': [],
                'transformation_rules': []
            }
            
            # Add constraints based on analysis
            if mapping['unique']:
                mapping['suggested_constraints'].append('UNIQUE')
            
            if stats.get('data_type') == 'email':
                mapping['suggested_constraints'].append('EMAIL_FORMAT')
            
            if stats.get('data_type') == 'numeric':
                if stats.get('min_value', 0) >= 0:
                    mapping['suggested_constraints'].append('NON_NEGATIVE')
            
            # Add transformation rules
            if stats.get('data_type') == 'datetime':
                mapping['transformation_rules'].append('PARSE_DATETIME')
            
            if stats.get('data_type') == 'text':
                mapping['transformation_rules'].append('TRIM_WHITESPACE')
            
            self.schema_mappings[header] = mapping
    
    def export_ontology(self, format: str = 'json') -> str:
        """Export the inferred ontology in specified format."""
        if format == 'json':
            import json
            return json.dumps({
                'inferred_types': self.inferred_types,
                'suggested_relationships': self.suggested_relationships,
                'schema_mappings': self.schema_mappings,
                'generated_at': datetime.now().isoformat()
            }, indent=2)
        elif format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write types
            writer.writerow(['Column', 'Inferred Type', 'Confidence', 'Reasoning'])
            for col, info in self.inferred_types.items():
                writer.writerow([col, info['type'], info['confidence'], info['reasoning']])
            
            writer.writerow([])
            
            # Write relationships
            writer.writerow(['Source', 'Relationship', 'Target', 'Confidence', 'Reasoning'])
            for rel in self.suggested_relationships:
                writer.writerow([
                    rel['source_column'],
                    rel['relationship_type'],
                    rel['target_column'],
                    rel['confidence'],
                    rel['reasoning']
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
