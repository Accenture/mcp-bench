Feature: Autocomplete

  Scenario Outline: Valid autocomplete concept and query
    Given I have a valid concept "<concept>" and a valid query "<query>"
    When I call the Pubtator Autocomplete API
    Then the response entity_id should be "<expected_id>"
    And the response concept should be "<concept>"

    Examples:
      | concept  | query               | expected_id                     |
      | gene     | her2                | @GENE_ERBB2                     |
      | variant  | BRAF V600E          | @VARIANT_p.V600E_BRAF_human     |
      | disease  | lung adenocarcinoma | @DISEASE_Adenocarcinoma_of_Lung |
      | chemical | Caffeine            | @CHEMICAL_Caffeine              |

  Scenario Outline: Invalid autocomplete query
    Given I have a valid concept "<concept>" and an invalid query "<query>"
    When I call the Pubtator Autocomplete API
    Then the response should be empty

    Examples:
      | concept  | query  |
      | gene     | iPhone |
      | variant  | iPhone |
      | disease  | iPhone |
      | chemical | iPhone |
