import unittest

from main import File

class MyTestCase(unittest.TestCase):

    def test_1(self):
        f = File()
        test_number = 2
        test_result = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
        all_combine_result = f.combine_function(test_number)
        self.assertEqual(all_combine_result,test_result)

    def test_2(self):
        lines = []
        try:
            with open("words.txt","r+",encoding="utf-8") as file:
                lines = file.readlines()
        except IOError:
            print("读写文件异常")
        else:
            print("get words!")
        print(lines)

if __name__ == '__main__':
    unittest.main()
