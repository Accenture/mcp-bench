"""Tests for the links module."""

import json
import os
from typing import Any

import pytest

from biomcp.variants.links import inject_links


@pytest.fixture
def braf_variants() -> list[dict[str, Any]]:
    """Load BRAF V600 test data."""
    test_data_path = os.path.join(
        os.path.dirname(__file__),
        "../../data/myvariant/variants_part_braf_v600_multiple.json",
    )
    with open(test_data_path) as f:
        return json.load(f)


def test_inject_links_braf_variants(braf_variants):
    """Test URL injection for BRAF variants data."""
    result = inject_links(braf_variants)

    # Test first variant (no CIViC)
    variant0 = result[0]
    assert (
        variant0["dbsnp"]["url"]
        == f"https://www.ncbi.nlm.nih.gov/snp/{variant0['dbsnp']['rsid']}"
    )
    assert (
        variant0["clinvar"]["url"]
        == f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variant0['clinvar']['variant_id']}/"
    )
    assert (
        variant0["cosmic"]["url"]
        == f"https://cancer.sanger.ac.uk/cosmic/mutation/overview?id={variant0['cosmic']['cosmic_id']}"
    )
    assert "civic" not in variant0 or "url" not in variant0["civic"]
    assert (
        variant0["url"]["ensembl"]
        == f"https://ensembl.org/Homo_sapiens/Variation/Explore?v={variant0['dbsnp']['rsid']}"
    )
    assert variant0["url"]["ucsc_genome_browser"].startswith(
        "https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr7:"
    )
    assert (
        variant0["url"]["hgnc"]
        == "https://www.genenames.org/data/gene-symbol-report/#!/symbol/BRAF"
    )

    # Test second variant (with CIViC)
    variant1 = result[1]
    assert (
        variant1["civic"]["url"]
        == f"https://civicdb.org/variants/{variant1['civic']['id']}/summary"
    )

    # Test empty list
    assert inject_links([]) == []

    # Test insertion (no REF)
    insertion = {
        "chrom": "7",
        "vcf": {"position": "123", "alt": "A"},
        "dbnsfp": {"genename": "GENE1"},
    }
    result = inject_links([insertion])[0]
    assert (
        result["url"]["ucsc_genome_browser"]
        == "https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr7:123-124"
    )

    # Test deletion (no ALT)
    deletion = {
        "chrom": "7",
        "vcf": {"position": "123", "ref": "AAA"},
        "dbnsfp": {"genename": "GENE1"},
    }
    result = inject_links([deletion])[0]
    assert (
        result["url"]["ucsc_genome_browser"]
        == "https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr7:123-126"
    )
