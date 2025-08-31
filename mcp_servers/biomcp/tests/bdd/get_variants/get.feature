Feature: Retrieve Variant Details

  Scenario: Get variant details using HGVS ID
    Given I run "biomcp variant get chr7:g.140453136A>T --json"
    Then at least one variant should have field "_id" equal to "chr7:g.140453136A>T"
    And at least one variant should have field "mutdb.uniprot_id" equal to "VAR_018629"
    And at least one variant should have field "dbsnp.rsid" equal to "rs113488022"
    And at least one variant should have field "cadd.phred" equal to "32"

  Scenario: Get variant details using rsID
    Given I run "biomcp variant get rs113488022 --json"
    Then at least one variant should have field "_id" equal to "chr7:g.140453136A>T"
    And at least one variant should have field "mutdb.uniprot_id" equal to "VAR_018629"
    And at least one variant should have field "dbsnp.rsid" equal to "rs113488022"
    And at least one variant should have field "cadd.phred" equal to "32"
