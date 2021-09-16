import sys
from zhconv import convert
import pypinyin
from pychai import Schema


class File:

    # 进行初始化定义，初始化全局变量
    def __init__(self):
        self.total = 0  # 总共的敏感词数目
        self.result = []  # 存放结果
        self.original_sensi_word = []  # 原文的敏感词库
        self.no_processed_sensi_word = []  # 去除掉换行符的敏感词数组
        self.sensi_word_pinyin = []  # 对敏感词进行拼音转换
        self.trans_sensi_words = {}  # 存放敏感词的所有变形形式，包括敏感词的谐音、拆部首等
        self.head_alphabet = {}  # 存放头部字母
        self.split_word = Schema('wubi98')  # 引入pychai，使用五笔98版
        self.split_word.run()
        self.al_occurred = {}  # 用来标记敏感词文本的行号和敏感词词头位置
        self.pass_list = {}
        self.pass_list_another = {}

    # 获取敏感词文件内容
    def get_sensi_word(self, filename):
        with open(filename, "r", encoding='utf-8') as file:
            self.original_sensi_word = file.readlines()
        for line in self.original_sensi_word:
            line = line.replace('\n', '').replace('\r', '')
            self.no_processed_sensi_word.append(line)
        self.sensi_word_pinyin = self.transform_to_pinyin()
        self.sensi_word_trie_tree = self.build_sensi_word_trie_tree(
            self.sensi_word_pinyin)

    # 将敏感词进行拼音转化，部首拆解，找出敏感词组合【构建敏感词库】
    def transform_to_pinyin(self):
        sensi_word_pinyin = []
        for single_sensi_word in self.no_processed_sensi_word:    # 增加汉字组合 去除某些不需要的组合
            sensi_word_pinyin.append(single_sensi_word.lower())
            pinyin_result = ""
            if '\u4e00' <= single_sensi_word[0] <= '\u9fff':
                for single_word in single_sensi_word:
                    if single_word in self.split_word.tree:
                        split_tree = self.split_word.tree[single_word]
                        head = split_tree.first
                        head_son = split_tree.second
                        while head.structure == 'h':
                            if head.first is None:
                                break
                            head = head.first
                        while head_son.structure == 'h':
                            if head_son.second is None:
                                break
                            head_son = head_son.second
                        pinyin_result += head.name[0]
                        pinyin_result += head_son.name
                        # 将偏旁进行拆分，就可以跳过拼音
                        self.pass_list[head.name[0]] = 1
                        self.pass_list[head_son.name] = 1
                        # 将汉字拆成部首和另外的部分，分别用两个数组来存
                        self.pass_list_another[head.name[0]] = head_son.name
                    else:
                        pinyin_result += single_word
                sensi_word_pinyin.append(pinyin_result)
            self.trans_sensi_words[single_sensi_word.lower()
                                   ] = single_sensi_word
            self.trans_sensi_words[pinyin_result] = single_sensi_word
        sensi_word_pinyin = list(set(sensi_word_pinyin))

        # 获取汉字的拼音
        # 需要将sensi_word_pinyin进行copy再操作
        for pinyin_result in sensi_word_pinyin.copy():
            if '\u4e00' <= pinyin_result[0] <= '\u9fff':
                pinyin = pypinyin.lazy_pinyin(pinyin_result)
                temp_word_list = []
                for k in range(len(pinyin_result)):
                    temp_word_list.append(pinyin_result[k])
                all_combine_result = self.combine_function(
                    len(pinyin_result))
                pass_flag = False
                for k in all_combine_result:
                    count = 0
                    result_word = ""  # 存放最终的组合结果
                    for i in range(len(k)):
                        if k[i] == 0:
                            if temp_word_list[count] in self.pass_list:
                                pass_flag = True
                            result_word += pinyin[count]
                        if k[i] == 1:
                            result_word += temp_word_list[count]
                            if temp_word_list[count] in self.pass_list_another:
                                result_word += self.pass_list_another[temp_word_list[count]]
                        if k[i] == 2:
                            if temp_word_list[count] in self.pass_list:
                                pass_flag = True
                            result_word += pinyin[count][0]
                            self.head_alphabet[pinyin[count][0]] = 1
                        count += 1
                    if not pass_flag:
                        sensi_word_pinyin.append(result_word)
                    if result_word not in self.trans_sensi_words:
                        self.trans_sensi_words[result_word] = pinyin_result
            else:
                self.trans_sensi_words[pinyin_result] = pinyin_result
        sensi_word_pinyin = list(set(sensi_word_pinyin))
        return sensi_word_pinyin

    # 构造敏感词的trie树
    def build_sensi_word_trie_tree(self, sensitive_word_list):
        sensi_word_trie_tree = {}
        for single_word in sensitive_word_list:
            now_point = sensi_word_trie_tree
            for k in range(len(single_word)):
                main_word = single_word[k]
                words_list = now_point.get(main_word)
                if words_list:
                    now_point = words_list
                    if main_word in self.head_alphabet:
                        now_point["More"] = 1
                else:
                    next_point = {"End_flag": 0}
                    now_point[main_word] = next_point
                    now_point = next_point
                    if main_word in self.head_alphabet:
                        now_point["More"] = 1

                if k == len(single_word) - 1:
                    now_point["End_flag"] = 1
                    now_point["sensi_word"] = single_word
                if k == 0:
                    now_point["Start_flag"] = 1
        return sensi_word_trie_tree

    # 对单行字符串进行检验，找出敏感词位置，并返回结果
    def get_single_line_sensi_word(self, words, lines_count):
        search_chinese = -1  # 使用1和-1进行识别遍历，1表示汉字
        start_position = -1  # 表示敏感词在该行的位置
        issensi_pages_len = -1  # 表示敏感词文本的长度
        result_position_list = []  # 存放遍历结果的敏感词数组
        now_point = self.sensi_word_trie_tree
        words_position = 0
        cur_list = {}
        skip_position = -1
        while words_position < len(words):
            cur_word = words[words_position]
            # 如果当前字段为汉字，则将其转换为简体汉字
            if '\u4e00' <= cur_word <= '\u9fff':
                cur_word = convert(cur_word, 'zh-hans')

            # 如果当前字段为字母，则将其转换为小写字母
            if cur_word.isalpha():
                cur_word = cur_word.lower()

            # 如果当前字段非字母或者汉字，跳过，即跳过特殊符号，以实现跳词
            if not cur_word.isalpha() and not ('\u4e00' <= cur_word <= '\u9fff'):
                issensi_pages_len += 1
                words_position += 1
                continue

            # 判断当前字段是否在敏感词trie树中
            search_flag = cur_word in now_point
            if search_flag:
                now_point = now_point.get(cur_word)
                if now_point.get("End_flag") == 1:
                    if not cur_list and now_point.get("More"):
                        if words_position == len(words) - 2:
                            if str(lines_count) + str(start_position) not in self.al_occurred.keys():
                                result_position_list.append(
                                    (start_position, issensi_pages_len, self.trans_sensi_words[now_point.get("sensi_word")]))
                            self.al_occurred[str(
                                lines_count) + str(start_position)] = 1
                            now_point = self.sensi_word_trie_tree  # 查询结束将指针指向根节点
                            issensi_pages_len = -1
                            start_position = -1
                            search_chinese = -1
                            self.total += 1
                            words_position += 1
                            cur_list = {}
                            continue
                        cur_list = now_point
                        skip_position += 1
                        words_position += 1
                        issensi_pages_len += 1
                        continue
                    else:
                        if str(lines_count) + str(start_position) not in self.al_occurred.keys():
                            result_position_list.append(
                                (start_position, issensi_pages_len, self.trans_sensi_words[now_point.get("sensi_word")]))
                        self.al_occurred[str(lines_count) +
                                         str(start_position)] = 1
                        now_point = self.sensi_word_trie_tree   # 查询结束将指针指向根节点
                        self.total += 1
                        cur_list = {}
                        issensi_pages_len = -1
                        search_chinese = -1
                        words_position += 1
                        start_position = -1
                        continue
                if (now_point.get("Start_flag") == 1) & (start_position == -1):
                    if search_chinese == -1 and ('\u4e00' <= cur_word <= '\u9fff'):
                        search_chinese = 1
                    start_position = words_position
                    issensi_pages_len = 1
                issensi_pages_len += 1
                words_position += 1
            else:
                if cur_list:
                    if str(lines_count) + str(start_position) not in self.al_occurred.keys():
                        result_position_list.append(
                            (start_position, issensi_pages_len - 1, self.trans_sensi_words[cur_list.get("sensi_word")]))
                    self.al_occurred[str(lines_count) +
                                     str(start_position)] = 1
                    now_point = self.sensi_word_trie_tree   # 查询结束将指针指向根节点
                    issensi_pages_len = -1
                    start_position = -1
                    words_position -= skip_position
                    search_chinese = -1
                    self.total += 1
                    cur_list = {}
                    continue
                if search_chinese == 1:
                    # 字段为字母或十进制字符
                    if cur_word.isalpha() or cur_word.isdecimal():
                        if not ('\u4e00' <= cur_word <= '\u9fff'):
                            issensi_pages_len += 1
                            words_position += 1
                            continue
                if '\u4e00' <= cur_word <= '\u9fff':
                    flag = True
                    now_position = words_position
                    pinyin = pypinyin.lazy_pinyin(cur_word)[0]
                    for i in pinyin:
                        flag_find_pinyin = i in now_point
                        if flag_find_pinyin:
                            if (now_point.get("Start_flag") == 1) & (start_position == -1):
                                if search_chinese == -1 and ('\u4e00' <= cur_word <= '\u9fff'):
                                    search_chinese = 1
                                issensi_pages_len = 1
                                start_position = now_position
                            now_point = now_point.get(i)
                        else:
                            flag = False
                            break
                    if flag:
                        issensi_pages_len += 1
                        if now_point.get("End_flag") == 1:
                            issensi_pages_len -= 1
                            if str(lines_count) + str(start_position) not in self.al_occurred.keys():
                                result_position_list.append(
                                    (start_position, issensi_pages_len, self.trans_sensi_words[now_point.get("sensi_word")]))
                            self.al_occurred[str(
                                lines_count) + str(start_position)] = 1
                            now_point = self.sensi_word_trie_tree
                            issensi_pages_len = -1
                            start_position = -1
                            search_chinese = -1
                            self.total += 1
                            words_position += 1
                            cur_list = {}
                            continue
                        words_position += 1
                        continue
                now_point = self.sensi_word_trie_tree
                start_position = -1
                issensi_pages_len = -1
                words_position += 1
        return result_position_list

    # 获取检测文本，并对读取单行文本内容，对单行文本进行检测，在结果数组中存入结果
    def get_single_line_result(self, filename):
        lines_page = []
        lines_count = 0
        with open(filename, "r+", encoding="utf-8") as file:
            lines_page = file.readlines()
        for lines in lines_page:
            if not lines:
                break
            lines_count += 1
            single_line_result = []
            single_line_result.extend(
                self.get_single_line_sensi_word(lines, lines_count))

            for res in single_line_result:
                self.result.append("Line" + str(lines_count) + ": <" +
                                   res[2] + "> " + lines[res[0]:res[0] + res[1]] + "\n")

    # 输出的文本函数
    def print_out(self, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("Total: " + str(self.total) + '\n')
            for k in self.result:
                file.write(k)

    # 将所有的结果组合在一起，返回数字的形式
    def combine_function(self, numbers):
        combine_result = []
        temp = []
        self.DFS(numbers, temp, combine_result)
        return combine_result

    # 使用深度优先搜索算法，便利所有节点，找出所有可能的组合，用数字表示
    def DFS(self, numbers, temp, result):
        temp_1 = temp.copy()
        if len(temp) >= numbers:
            result.append(temp_1)
            return
        # 用0表示拼音，用1表示拆部首，用2表示拼音首字母
        for k in range(3):
            temp.append(k)
            self.DFS(numbers, temp, result)
            temp.pop()
        return


if __name__ == '__main__':

    words_txt = sys.argv[1]
    org_txt = sys.argv[2]
    ans_txt = sys.argv[3]
    # words_txt = 'words.txt'
    # org_txt = 'org.txt'
    # ans_txt = 'ans.txt'
    f = File()
    f.get_sensi_word(words_txt)
    f.get_single_line_result(org_txt)
    f.print_out(ans_txt)
