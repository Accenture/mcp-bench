Feature: Perform Search

  Scenario Outline: Search PubMed using entity and keywords
    Given I build a query for "<gene>" "<disease>" "<variant>"
    When I perform a search with that query
    Then the response should contain the article "<pmid>"
    And the article "<pmid>" abstract should contain "<phrase>"

    Examples:
    | gene | disease  | variant    | pmid     | phrase                                             |
    | BRAF | Melanoma | BRAF V600E | 21717063 | melanomas presenting with the BRAF(V600E) mutation |
