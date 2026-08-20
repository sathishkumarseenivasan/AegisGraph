"""
Ontology API Routes.

Endpoints for CSV upload and ontology inference.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import io

from backend.ontology.ontology_builder import OntologyBuilder

router = APIRouter(prefix="/ontology", tags=["ontology"])


@router.post("/analyze")
async def analyze_csv(
    file: UploadFile = File(..., description="CSV file to analyze"),
    include_samples: bool = Form(default=True, description="Include sample rows in response")
):
    """
    Upload a CSV file and get inferred ontology information.
    
    Analyzes the CSV to infer:
    - Entity types for columns
    - Potential relationships between columns
    - Schema mappings and constraints
    - Data type detection
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_content)
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to analyze CSV')
            )
        
        # Remove sample rows if not requested
        if not include_samples and 'sample_rows' in result:
            del result['sample_rows']
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded CSV"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing CSV: {str(e)}"
        )


@router.post("/analyze-text")
async def analyze_csv_text(
    csv_content: str = Form(..., description="Raw CSV content as text"),
    include_samples: bool = Form(default=True, description="Include sample rows in response")
):
    """
    Analyze CSV content provided as text.
    
    Useful for testing or when CSV is already loaded in memory.
    """
    try:
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_content)
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to analyze CSV')
            )
        
        # Remove sample rows if not requested
        if not include_samples and 'sample_rows' in result:
            del result['sample_rows']
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing CSV: {str(e)}"
        )


@router.post("/export")
async def export_ontology(
    csv_content: str = Form(..., description="Raw CSV content"),
    format: str = Form(default="json", description="Export format (json or csv)")
):
    """
    Export inferred ontology in specified format.
    
    Returns the complete ontology inference results in JSON or CSV format.
    """
    try:
        builder = OntologyBuilder()
        result = builder.analyze_csv(csv_content)
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to analyze CSV')
            )
        
        export_content = builder.export_ontology(format=format)
        
        media_type = "application/json" if format == "json" else "text/csv"
        
        from fastapi.responses import Response
        return Response(
            content=export_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=ontology.{format}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting ontology: {str(e)}"
        )


@router.get("/patterns")
async def get_patterns():
    """
    Get the list of patterns used for type inference.
    
    Returns all the regex patterns and relationship indicators
    used by the ontology builder.
    """
    builder = OntologyBuilder()
    
    return {
        "type_patterns": {
            type_name: patterns 
            for type_name, patterns in builder.TYPE_PATTERNS.items()
        },
        "relationship_patterns": {
            rel_type: patterns 
            for rel_type, patterns in builder.RELATIONSHIP_PATTERNS.items()
        }
    }
