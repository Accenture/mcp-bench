"""Functions for adding database links to variant data."""

from typing import Any


def _calculate_vcf_end(variant: dict[str, Any]) -> int:
    """Calculate the end position for UCSC Genome Browser link."""
    if "vcf" not in variant:
        return 0

    vcf = variant["vcf"]
    pos = int(vcf.get("position", 0))
    ref = vcf.get("ref", "")
    alt = vcf.get("alt", "")

    # For insertions/deletions, handle special cases
    if not ref and alt:  # insertion
        return pos + 1
    elif ref and not alt:  # deletion
        return pos + len(ref)
    else:  # substitution
        return pos + max(0, ((len(alt) + 1) - len(ref)))


def _get_first_value(data: Any) -> Any:
    """Get the first value from a list or return the value itself."""
    if isinstance(data, list) and data:
        return data[0]
    return data


def _ensure_url_section(variant: dict[str, Any]) -> None:
    """Ensure the URL section exists in the variant."""
    if "url" not in variant:
        variant["url"] = {}


def _add_dbsnp_links(variant: dict[str, Any]) -> None:
    """Add dbSNP and Ensembl links if rsid is present."""
    if "dbsnp" in variant and variant["dbsnp"].get("rsid"):
        variant["dbsnp"]["url"] = (
            f"https://www.ncbi.nlm.nih.gov/snp/{variant['dbsnp']['rsid']}"
        )
        _ensure_url_section(variant)
        variant["url"]["ensembl"] = (
            f"https://ensembl.org/Homo_sapiens/Variation/Explore?v={variant['dbsnp']['rsid']}"
        )


def _add_clinvar_link(variant: dict[str, Any]) -> None:
    """Add ClinVar link if variant_id is present."""
    if "clinvar" in variant and variant["clinvar"].get("variant_id"):
        variant["clinvar"]["url"] = (
            f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variant['clinvar']['variant_id']}/"
        )


def _add_cosmic_link(variant: dict[str, Any]) -> None:
    """Add COSMIC link if cosmic_id is present."""
    if "cosmic" in variant and variant["cosmic"].get("cosmic_id"):
        variant["cosmic"]["url"] = (
            f"https://cancer.sanger.ac.uk/cosmic/mutation/overview?id={variant['cosmic']['cosmic_id']}"
        )


def _add_civic_link(variant: dict[str, Any]) -> None:
    """Add CIViC link if id is present."""
    if "civic" in variant and variant["civic"].get("id"):
        variant["civic"]["url"] = (
            f"https://civicdb.org/variants/{variant['civic']['id']}/summary"
        )


def _add_ucsc_link(variant: dict[str, Any]) -> None:
    """Add UCSC Genome Browser link if chromosome and position are present."""
    if (
        "chrom" in variant
        and "vcf" in variant
        and variant["vcf"].get("position")
    ):
        vcf_end = _calculate_vcf_end(variant)
        _ensure_url_section(variant)
        variant["url"]["ucsc_genome_browser"] = (
            f"https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&"
            f"position=chr{variant['chrom']}:{variant['vcf']['position']}-{vcf_end}"
        )


def _add_hgnc_link(variant: dict[str, Any]) -> None:
    """Add HGNC link if gene name is present."""
    if "dbnsfp" in variant and variant["dbnsfp"].get("genename"):
        gene = _get_first_value(variant["dbnsfp"]["genename"])
        if gene:
            _ensure_url_section(variant)
            variant["url"]["hgnc"] = (
                f"https://www.genenames.org/data/gene-symbol-report/#!/symbol/{gene}"
            )


def inject_links(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Inject database links into variant data.

    Args:
        variants: List of variant dictionaries from MyVariant.info API

    Returns:
        List of variant dictionaries with added URL links in appropriate sections
    """
    for variant in variants:
        _add_dbsnp_links(variant)
        _add_clinvar_link(variant)
        _add_cosmic_link(variant)
        _add_civic_link(variant)
        _add_ucsc_link(variant)
        _add_hgnc_link(variant)

    return variants
