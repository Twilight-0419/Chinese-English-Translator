from src.translator import translate

def main():
    zh_sentence = input("请输入中文句子: ")
    top_k = int(input("请输入top_k值: "))
    translation = translate(zh_sentence, top_k)
    print("翻译结果:", translation)

if __name__ == "__main__":
    main()