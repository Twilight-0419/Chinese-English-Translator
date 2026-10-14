from src.translator import translate

def main():
    while True:
        zh_sentence = input("请输入中文句子: ")
        translation = translate(zh_sentence)
        print("翻译结果:", translation)
        break_prompt = input("是否继续翻译？(y/n): ")
        if break_prompt.lower() != 'y':
            break

if __name__ == "__main__":
    main()
