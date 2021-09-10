import pypinyin
import os
import re


def GetSensitiveWord(file_name):
    col = []
    with open(file_name, "r", encoding="utf-8") as f:
        data = f.readlines()
    for k in data:
        k = k.strip("\n")
        col.append(k)
    return col


def translate_to_pinyin(words):
    results = pypinyin.pinyin(words, style=pypinyin.NORMAL)
    return results


def GetPages(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        pages = f.readlines()
    return pages


if __name__ == "__main__":
    sensi_words = GetSensitiveWord("words.txt")
    print(sensi_words)
    sensi_words_pinyin = []
    Test_pages = []
    Test_pages_1 = []
    for k in sensi_words:
        k = translate_to_pinyin(k)
        sensi_words_pinyin.append(k)
    print(sensi_words_pinyin)
    Test_pages = GetPages("org1.txt")
    print(Test_pages)
    
    for k in Test_pages:
        a = re.findall('[\u4e00-\u9fa5a-zA-Z]+', k, re.S)  # 只要字符串中的中文，字母，数字
        Test_pages_1.append(a)

    for k in Test_pages_1:
        print(k)
        
    Test_pages_pinyin = []
    for k in Test_pages_1:
        k = translate_to_pinyin(k)
        Test_pages_pinyin.append(k)
    print(Test_pages_pinyin)
