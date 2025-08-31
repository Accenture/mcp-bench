Feature: Search for genetic variants via CLI
  As a researcher
  I want to search for genetic variants using various criteria
  So that I can find relevant variants for my research

  Scenario: Search for variants by gene symbol
    When I run "biomcp variant search --gene BRCA1"
    Then each variant should have gene that is equal to BRCA1

  Scenario: Filter variants by clinical significance (Pathogenic)
    When I run "biomcp variant search --gene BRAF --significance Pathogenic"
    Then each variant should have gene that is equal to BRAF
    Then each variant should have significance that contains Pathogenic

  Scenario: Filter variants by clinical significance (Likely Benign)
    When I run "biomcp variant search --gene TP53 --significance "likely benign" --size 5"
    Then each variant should have gene that is equal to TP53
    Then each variant should have significance that is equal to Likely benign
    Then the number of variants is less than or equal to 5

  Scenario: Filter variants by allele frequency (Range)
    When I run "biomcp variant search --gene TP53 --min-frequency 0.0002 --max-frequency 0.0003"
    Then each variant should have gene that is equal to TP53
    Then each variant should have frequency that is greater than or equal to 0.0002
    Then each variant should have frequency that is less than or equal to 0.0003

  Scenario: Filter variants by allele frequency (Minimum only)
    When I run "biomcp variant search --gene APOE --min-frequency 0.4 --size 3"
    Then each variant should have gene that is equal to APOE
    Then each variant should have frequency that is greater than or equal to 0.4
    Then the number of variants is less than 3

  Scenario: Filter variants by allele frequency (Maximum only)
    When I run "biomcp variant search --gene TP53 --max-frequency 0.00001 --size 5"
    Then each variant should have gene that is equal to TP53
    Then each variant should have frequency that is less than or equal to 0.00001
    Then the number of variants is less than or equal to 5

  Scenario: Search for variants by rsID
    When I run "biomcp variant search --rsid rs1799966"
    Then each variant should have rsid that is equal to rs1799966

  Scenario: Search for variants by protein notation
    When I run "biomcp variant search --hgvsp p.Val600Glu"
    Then each variant should have hgvsp that is equal to p.Val600Glu

  Scenario: Search for variants by cDNA notation
    When I run "biomcp variant search --hgvsc c.1799T>A"
    Then each variant should have hgvsc that is equal to c.1799T>A

  Scenario: Search for variants by genomic region
    When I run "biomcp variant search --region chr7:140453130-140453140"
    Then each variant should have chromosome that is equal to 7
    And each variant should have position that is greater than or equal to 140453130
    And each variant should have position that is less than or equal to 140453140

  Scenario: Filter variants by CADD score
    When I run "biomcp variant search --gene BRCA1 --cadd 20"
    Then each variant should have gene that is equal to BRCA1
    Then each variant should have cadd that is greater than or equal to 20

  Scenario: Filter variants by PolyPhen prediction (Possibly Damaging)
    When I run "biomcp variant search --gene BRCA1 --polyphen P"
    Then each variant should have gene that is equal to BRCA1
    Then each variant should have polyphen that contains P

  Scenario: Filter variants by PolyPhen prediction (Benign)
    When I run "biomcp variant search --gene CFTR --polyphen B --size 3"
    Then each variant should have gene that is equal to CFTR
    Then each variant should have polyphen that contains B
    Then the number of variants is less than or equal to 3

  Scenario: Filter variants by SIFT prediction (Deleterious)
    When I run "biomcp variant search --gene BRCA1 --sift D"
    Then each variant should have gene that is equal to BRCA1
    Then each variant should have sift that contains D

  Scenario: Filter variants by SIFT prediction (Tolerated)
    When I run "biomcp variant search --gene MTHFR --sift T --size 3"
    Then each variant should have gene that is equal to MTHFR
    Then each variant should have sift that contains T
    Then the number of variants is less than or equal to 3

  Scenario: Search with multiple filters combined
    When I run "biomcp variant search --gene BRCA1 --significance Pathogenic --cadd 20 --max-frequency 0.01"
    Then each variant should have gene that is equal to BRCA1
    Then each variant should have significance that contains Pathogenic
    Then each variant should have cadd that is greater than or equal to 20
    Then each variant should have frequency that is less than or equal to 0.01

  Scenario: Limit number of search results (size=5)
    When I run "biomcp variant search --gene TP53 --size 5"
    Then each variant should have gene that is equal to TP53
    Then the number of variants is less than or equal to 5

  Scenario: Limit number of search results (size=1)
    When I run "biomcp variant search --gene TP53 --size 1"
    Then each variant should have gene that is equal to TP53
    Then the number of variants is equal to 1
#
  Scenario: Select different sources
    When I run "biomcp variant search --rsid 'chr17:g.7574024G>A' --sources mutdb"
    Then each variant should have uniprot_id that contains VAR_018629

  Scenario: Search expected to yield no results
    When I run "biomcp variant search --gene XYZABC123 --rsid rs9999999999"
    Then the number of variants is equal to 0
