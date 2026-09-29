import re

def is_contains_chinese(strs):
    for char in strs:
        if '一' <= char <= '龥':
            return True
    return False

def is_english_and_digit(s):
    return bool(re.fullmatch('(?=.*[A-Za-z])(?=.*\\d)[A-Za-z0-9]+', s))

def has_special_char(s):
    return bool(re.search('[^A-Za-z0-9]', s))
