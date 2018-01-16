Feature: Correct format in the dictionaries

  Scenario: Term list has correct format
    Given the bad term list
    Then parsing it should not cause an exception

  Scenario: Category hash has correct format
    Given the bad category hash
    Then parsing it should not cause an exception
