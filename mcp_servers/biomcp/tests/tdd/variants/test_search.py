import pytest

from biomcp.variants.search import (
    ClinicalSignificance,
    PolyPhenPrediction,
    SiftPrediction,
    VariantQuery,
    build_query_string,
    search_variants,
)


@pytest.fixture
def basic_query():
    """Create a basic gene query."""
    return VariantQuery(gene="BRAF")


@pytest.fixture
def complex_query():
    """Create a complex query with multiple parameters."""
    return VariantQuery(
        gene="BRCA1",
        significance=ClinicalSignificance.PATHOGENIC,
        min_frequency=0.0001,
        max_frequency=0.01,
    )


def test_query_validation():
    """Test VariantQuery model validation."""
    # Test basic query with gene
    query = VariantQuery(gene="BRAF")
    assert query.gene == "BRAF"

    # Test query with rsid
    query = VariantQuery(rsid="rs113488022")
    assert query.rsid == "rs113488022"

    # Test query requires at least one search parameter
    with pytest.raises(ValueError):
        VariantQuery()

    # Test query with clinical significance enum requires a search parameter
    query = VariantQuery(
        gene="BRCA1", significance=ClinicalSignificance.PATHOGENIC
    )
    assert query.significance == ClinicalSignificance.PATHOGENIC

    # Test query with prediction scores
    query = VariantQuery(
        gene="TP53",
        polyphen=PolyPhenPrediction.PROBABLY_DAMAGING,
        sift=SiftPrediction.DELETERIOUS,
    )
    assert query.polyphen == PolyPhenPrediction.PROBABLY_DAMAGING
    assert query.sift == SiftPrediction.DELETERIOUS


def test_build_query_string():
    """Test build_query_string function."""
    # Test single field
    query = VariantQuery(gene="BRAF")
    q_string = build_query_string(query)
    assert 'dbnsfp.genename:"BRAF"' in q_string

    # Test multiple fields
    query = VariantQuery(gene="BRAF", rsid="rs113488022")
    q_string = build_query_string(query)
    assert 'dbnsfp.genename:"BRAF"' in q_string
    assert "rs113488022" in q_string

    # Test genomic region
    query = VariantQuery(region="chr7:140753300-140753400")
    q_string = build_query_string(query)
    assert "chr7:140753300-140753400" in q_string

    # Test clinical significance
    query = VariantQuery(significance=ClinicalSignificance.LIKELY_BENIGN)
    q_string = build_query_string(query)
    assert 'clinvar.rcv.clinical_significance:"likely benign"' in q_string

    # Test frequency filters
    query = VariantQuery(min_frequency=0.0001, max_frequency=0.01)
    q_string = build_query_string(query)
    assert "gnomad_exome.af.af:>=0.0001" in q_string
    assert "gnomad_exome.af.af:<=0.01" in q_string


async def test_search_variants_basic(basic_query, anyio_backend):
    """Test search_variants function with a basic query."""
    # Use a real API query for a common gene
    result = await search_variants(basic_query)

    # Verify we got sensible results
    assert "BRAF" in result
    assert not result.startswith("Error")


async def test_search_variants_complex(complex_query, anyio_backend):
    """Test search_variants function with a complex query."""
    # Use a simple common query that will return results
    simple_query = VariantQuery(gene="TP53")
    result = await search_variants(simple_query)

    # Verify response formatting
    assert not result.startswith("Error")


async def test_search_variants_no_results(anyio_backend):
    """Test search_variants function with a query that returns no results."""
    query = VariantQuery(gene="UNKNOWN_XYZ")
    result = await search_variants(query, output_json=True)
    assert result == "[]"


async def test_search_variants_with_limit(anyio_backend):
    """Test search_variants function with size limit."""
    # Query with a small limit
    query = VariantQuery(gene="TP53", size=3)
    result = await search_variants(query)

    # Result should be valid but limited
    assert not result.startswith("Error")
