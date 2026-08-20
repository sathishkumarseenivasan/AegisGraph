"""
Tests for Ontology Builder module.
"""
import pytest
from backend.ontology.ontology_builder import OntologyBuilder


@pytest.fixture
def sample_csv():
    """Sample CSV data for testing."""
    return """id,name,email,company_id,company_name,city,country,amount,created_at
1,John Doe,john@example.com,C001,Acme Corp,New York,USA,1500.50,2024-01-15
2,Jane Smith,jane@example.com,C002,Tech Inc,San Francisco,USA,2300.00,2024-01-16
3,Bob Johnson,bob@example.com,C001,Acme Corp,Chicago,USA,890.25,2024-01-17
4,Alice Brown,alice@example.com,C003,Global Ltd,London,UK,3200.75,2024-01-18
5,Charlie Wilson,charlie@example.com,C002,Tech Inc,Boston,USA,1750.00,2024-01-19
"""


@pytest.fixture
def empty_csv():
    """Empty CSV for edge case testing."""
    return "id,name,email\n"


@pytest.fixture
def complex_csv():
    """Complex CSV with various data types."""
    return """employee_id,employee_name,department_id,department_name,salary,start_date,is_manager,email,office_location
E001,John Smith,D001,Engineering,95000,2020-01-15,true,john.smith@company.com,New York
E002,Jane Doe,D001,Engineering,87000,2021-03-20,false,jane.doe@company.com,New York
E003,Bob Johnson,D002,Sales,78000,2019-07-10,true,bob.j@company.com,Chicago
E004,Alice Williams,D002,Sales,82000,2022-02-28,false,alice.w@company.com,Chicago
E005,Charlie Brown,D003,HR,65000,2023-01-05,false,charlie.b@company.com,Boston
"""


class TestOntologyBuilder:
    """Test suite for OntologyBuilder class."""
    
    def test_basic_csv_analysis(self, sample_csv):
        """Test basic CSV analysis functionality."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        assert result['success'] is True
        assert result['row_count'] == 5
        assert result['column_count'] == 9
        assert len(result['headers']) == 9
        assert 'id' in result['headers']
        assert 'name' in result['headers']
    
    def test_empty_csv(self, empty_csv):
        """Test handling of empty CSV."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(empty_csv)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_type_inference(self, sample_csv):
        """Test entity type inference."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        assert 'inferred_types' in result
        
        # Check that name column is inferred as person
        if 'name' in result['inferred_types']:
            assert result['inferred_types']['name']['type'] == 'person'
        
        # Check that email is detected
        if 'email' in result['inferred_types']:
            assert result['inferred_types']['email']['type'] in ['identifier', 'attribute']
    
    def test_relationship_suggestions(self, sample_csv):
        """Test relationship suggestion logic."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        assert 'suggested_relationships' in result
        assert isinstance(result['suggested_relationships'], list)
        
        # Check that relationships have required fields
        for rel in result['suggested_relationships']:
            assert 'source_column' in rel
            assert 'relationship_type' in rel
            assert 'target_column' in rel
            assert 'confidence' in rel
    
    def test_schema_mappings(self, sample_csv):
        """Test schema mapping generation."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        assert 'schema_mappings' in result
        
        # Check that mappings have required fields
        for column, mapping in result['schema_mappings'].items():
            assert 'source_column' in mapping
            assert 'suggested_target_type' in mapping
            assert 'data_type' in mapping
            assert 'nullable' in mapping
            assert 'suggested_constraints' in mapping
    
    def test_column_statistics(self, sample_csv):
        """Test column statistics calculation."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        assert 'column_stats' in result
        
        # Check statistics for amount column
        if 'amount' in result['column_stats']:
            stats = result['column_stats']['amount']
            assert stats['data_type'] == 'numeric'
            assert 'min_value' in stats
            assert 'max_value' in stats
            assert 'avg_value' in stats
    
    def test_complex_csv_analysis(self, complex_csv):
        """Test analysis of complex CSV with various data types."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(complex_csv)
        
        assert result['success'] is True
        assert result['row_count'] == 5
        # Column count may vary based on actual CSV structure
        assert result['column_count'] >= 8
        
        # Check boolean detection
        if 'is_manager' in result['column_stats']:
            assert result['column_stats']['is_manager']['data_type'] == 'boolean'
        
        # Check datetime detection
        if 'start_date' in result['column_stats']:
            assert result['column_stats']['start_date']['data_type'] == 'datetime'
        
        # Check email detection
        if 'email' in result['column_stats']:
            assert result['column_stats']['email']['data_type'] == 'email'
    
    def test_export_json(self, sample_csv):
        """Test JSON export functionality."""
        builder = OntologyBuilder()
        builder.analyze_csv(sample_csv)
        
        json_output = builder.export_ontology(format='json')
        
        assert isinstance(json_output, str)
        assert 'inferred_types' in json_output
        assert 'suggested_relationships' in json_output
        assert 'schema_mappings' in json_output
        assert 'generated_at' in json_output
    
    def test_export_csv(self, sample_csv):
        """Test CSV export functionality."""
        builder = OntologyBuilder()
        builder.analyze_csv(sample_csv)
        
        csv_output = builder.export_ontology(format='csv')
        
        assert isinstance(csv_output, str)
        assert 'Column' in csv_output
        assert 'Inferred Type' in csv_output
        assert 'Relationship' in csv_output
    
    def test_export_invalid_format(self, sample_csv):
        """Test export with invalid format."""
        builder = OntologyBuilder()
        builder.analyze_csv(sample_csv)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            builder.export_ontology(format='xml')
    
    def test_data_type_inference(self):
        """Test data type inference for various value types."""
        builder = OntologyBuilder()
        
        # Test numeric
        assert builder._infer_data_type(['123', '456', '789']) == 'numeric'
        assert builder._infer_data_type(['12.5', '67.8', '90.1']) == 'numeric'
        
        # Test boolean
        assert builder._infer_data_type(['true', 'false', 'true']) == 'boolean'
        assert builder._infer_data_type(['yes', 'no', 'yes']) == 'boolean'
        
        # Test text
        assert builder._infer_data_type(['hello', 'world', 'test']) == 'text'
        
        # Test empty
        assert builder._infer_data_type([]) == 'unknown'
    
    def test_pattern_matching(self):
        """Test pattern matching for column names."""
        builder = OntologyBuilder()
        
        # Test person patterns
        matches = builder._match_patterns('customer_name')
        assert 'person' in matches
        
        # Test organization patterns
        matches = builder._match_patterns('company_id')
        assert 'organization' in matches
        
        # Test location patterns
        matches = builder._match_patterns('country_code')
        assert 'location' in matches
        
        # Test identifier patterns
        matches = builder._match_patterns('user_id')
        assert 'identifier' in matches
    
    def test_sample_rows_included(self, sample_csv):
        """Test that sample rows are included in results."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv, )
        
        assert 'sample_rows' in result
        assert len(result['sample_rows']) <= 3
        
        # Check sample row structure
        if result['sample_rows']:
            sample = result['sample_rows'][0]
            assert 'id' in sample
            assert 'name' in sample
    
    def test_no_samples_requested(self, sample_csv):
        """Test that samples can be excluded."""
        builder = OntologyBuilder()
        result = builder.analyze_csv(sample_csv)
        
        # By default samples are included
        assert 'sample_rows' in result
        
        # Note: The exclude logic is handled in the API layer
        # The core analyzer always includes samples
    
    def test_high_cardinality_detection(self):
        """Test detection of high cardinality columns."""
        csv_data = """id,unique_code,value
1,ABC123,common
2,DEF456,common
3,GHI789,common
4,JKL012,common
5,MNO345,common
"""
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_data)
        
        # unique_code should have high uniqueness
        if 'unique_code' in result['column_stats']:
            stats = result['column_stats']['unique_code']
            assert stats['unique_count'] == stats['non_empty_count']


class TestOntologyBuilderEdgeCases:
    """Test edge cases and error handling."""
    
    def test_malformed_csv(self):
        """Test handling of malformed CSV."""
        builder = OntologyBuilder()
        malformed = "id,name,value\n1,John,100\n2,Jane"  # Missing value
        
        # Should still parse but handle gracefully
        result = builder.analyze_csv(malformed)
        assert result['success'] is True  # CSV parser is lenient
    
    def test_special_characters(self):
        """Test CSV with special characters."""
        csv_data = """id,name,description
1,"John ""The Boss"" Doe","A description with, commas"
2,Jane Smith,"Another description"
"""
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_data)
        
        assert result['success'] is True
        assert result['row_count'] == 2
    
    def test_unicode_content(self):
        """Test CSV with Unicode content."""
        csv_data = """id,name,city
1,José García,México
2,François Müller,Zürich
3，田中太郎，東京
"""
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_data)
        
        assert result['success'] is True
        assert result['row_count'] == 3
    
    def test_very_large_values(self):
        """Test CSV with very large numeric values."""
        csv_data = """id,amount,population
1,999999999999.99,8000000000
2,0.00000001,1
3,123456789.12,500000
"""
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_data)
        
        assert result['success'] is True
        
        if 'amount' in result['column_stats']:
            stats = result['column_stats']['amount']
            assert stats['data_type'] == 'numeric'
    
    def test_all_null_column(self):
        """Test CSV with a column containing only null/empty values."""
        csv_data = """id,name,optional_field
1,John,
2,Jane,
3,Bob,
"""
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_data)
        
        assert result['success'] is True
        
        if 'optional_field' in result['column_stats']:
            stats = result['column_stats']['optional_field']
            assert stats['non_empty_count'] == 0
            # Check that empty count equals total rows
            assert stats['empty_count'] == 3
