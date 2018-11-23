# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 12:09:54 2018

@author: anhol
"""

#Test File Expectations
from __future__ import division
import great_expectations as ge
import pytest



def test_expect_file_line_regex_match_count_to_be_between():
    
    
    #####Invlaid File Path######
    joke_file_path="joke.txt"
    joke_dat=ge.dataset.FileDataset(joke_file_path)
    
    with pytest.raises(IOError):
        joke_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                                  expected_min_count=0,
                                                                  expected_max_count=4,
                                                                  skip=1)
    
    
    
    complete_file_path='./tests/test_sets/toy_data_complete.csv'
    
    file_dat=ge.dataset.FileDataset(complete_file_path)
    
    
    #Invalid Skip Parameter
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                            expected_min_count=0, 
                                                            expected_max_count=4,
                                                            skip=2.4) 

    #Invalid Regex
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=2,
                                                            expected_min_count=1, 
                                                            expected_max_count=8,
                                                            skip=2) 
    
        
    
    #Non-integer min value
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                            expected_min_count=1.3, 
                                                            expected_max_count=8,
                                                            skip=1) 

    
    #Negative min value
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                                     expected_min_count=-2,
                                                                     expected_max_count=8,
                                                                     skip=1)



    #Non-integer max value
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                            expected_min_count=0,
                                                            expected_max_count="foo",
                                                            skip=1) 
        
    #Negative max value
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                            expected_min_count=0,
                                                            expected_max_count=-1,
                                                            skip=1) 

    
    #Min count more than max count
    
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                            expected_min_count=4,
                                                            expected_max_count=3,
                                                            skip=1) 

    #Count does not fall in range
    fail_trial=file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                                         expected_min_count=9,
                                                                         expected_max_count=12,
                                                                         skip=1)
    
    assert (not fail_trial["success"])
    assert fail_trial['result']['unexpected_percent']==1
    assert fail_trial['result']['missing_percent']==0
    
    #Count does fall in range
    success_trial=file_dat.expect_file_line_regex_match_count_to_be_between(regex=",\S",
                                                                        expected_min_count=0,
                                                                        expected_max_count=4,
                                                                        skip=1)
    assert success_trial["success"]
    assert success_trial['result']['unexpected_percent']==0
    assert success_trial['result']['missing_percent']==0
    
    
    
    
    
  
    
def test_expect_file_line_regex_match_count_to_equal():
    
    complete_file_path='./tests/test_sets/toy_data_complete.csv'
    incomplete_file_path='./tests/test_sets/toy_data_incomplete.csv'
    
    file_dat=ge.dataset.FileDataset(complete_file_path)
    file_incomplete_dat=ge.dataset.FileDataset(incomplete_file_path)
    
    #Invalid Regex Value
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_equal(regex=True,
                                                            expected_count=3,
                                                            skip=1) 
    
    
    #Non-integer expected_count
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_equal(regex=",\S",
                                                            expected_count=6.3,
                                                            skip=1) 

    
    #Negative expected_count
    with pytest.raises(ValueError):
        file_dat.expect_file_line_regex_match_count_to_equal(regex=",\S",
                                                                   expected_count=-6,
                                                                   skip=1)
        
    

    #Count does not equal expected count
    fail_trial=file_incomplete_dat.expect_file_line_regex_match_count_to_equal(regex=",\S",
                                                                    expected_count=3,
                                                                    skip=1)
    
    assert (not fail_trial["success"])
    assert fail_trial['result']['unexpected_percent']==3/9
    assert fail_trial['result']['missing_percent']==2/9
    assert fail_trial['result']['unexpected_percent_nonmissing']==3/7
    
    
    #Mostly success
    mostly_trial=file_incomplete_dat.expect_file_line_regex_match_count_to_equal(regex=",\S",
                                                                    expected_count=3,
                                                                    skip=1,
                                                                    mostly=0.57)
    
    assert mostly_trial["success"]
    
    
    #Count does fall in range
    success_trial=file_dat.expect_file_line_regex_match_count_to_equal(regex=",\S",
                                                                            expected_count=3,
                                                                            skip=1)
    assert success_trial["success"]
    assert success_trial['result']['unexpected_percent']==0
    assert success_trial['result']['unexpected_percent_nonmissing']==0
    assert success_trial['result']['missing_percent']==0
    
    
    
def test_expect_file_hash_to_equal():
    # Test for non-existent file
    fake_file=ge.dataset.FileDataset(file_path="abc")
    
    with pytest.raises(IOError):
        fake_file.expect_file_hash_to_equal(value='abc')

        
    # Test for non-existent hash algorithm
    titanic_path = './tests/test_sets/Titanic.csv'
    titanic_file=ge.dataset.FileDataset(titanic_path)
    
    with pytest.raises(ValueError):
        titanic_file.expect_file_hash_to_equal(hash_alg='md51',
                                         value='abc')
        
    # Test non-matching hash value
    
    fake_hash_value=titanic_file.expect_file_hash_to_equal(value="abc")
    
    assert (not fake_hash_value["success"])
    
    # Test matching hash value with default algorithm
    hash_value='63188432302f3a6e8c9e9c500ff27c8a'
    good_hash_default_alg=titanic_file.expect_file_hash_to_equal(value=hash_value)
    assert good_hash_default_alg["success"]
    
    # Test matching hash value with specified algorithm
    hash_value='f89f46423b017a1fc6a4059d81bddb3ff64891e3c81250fafad6f3b3113ecc9b'
    good_hash_new_alg=titanic_file.expect_file_hash_to_equal(value=hash_value,
                                                     hash_alg='sha256')
    assert good_hash_new_alg["success"]
    
    


    
    


