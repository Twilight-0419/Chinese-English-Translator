from src.translator import translate

def main():
    zh_sentence = input("请输入中文句子: ")
    translation = translate(zh_sentence)
    print("翻译结果:", translation)

if __name__ == "__main__":
    main()