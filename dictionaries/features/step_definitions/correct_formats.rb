#!/usr/bin/env ruby
# encoding: utf-8
#
# Copyright:: (c) 2011 Zedge Inc.
# Author:: Knut O. Hellan
#          (khellan@zedge.net)

require "rspec/expectations"
require "json"

$: << File.expand_path("../..", File.dirname(__FILE__)) unless $:.include?(File.expand_path("../..", File.dirname(__FILE__)))

Given /^the bad term list$/ do
  @filename = "#{File.dirname(__FILE__)}/../../bad_terms.json"
end

Given /^the bad category hash$/ do
  @filename = "#{File.dirname(__FILE__)}/../../bad_categories.json"
end

Then /^parsing it should not cause an exception$/ do
  JSON.parse(open(@filename).read)
end