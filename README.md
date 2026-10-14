# 汉英翻译器

一个中文到英文的神经机器翻译项目。GRU 编码器-解码器 + 加性注意力，从零训练，
语料 138 万句对。

```
我爱你。              i love you .
你叫什么名字？         what 's your name ?
我是一名警察。         i 'm a cop .
他在哪里？            where 's he ?
我不知道该怎么办。      i don 't know what to do .
```

## 目录结构

```
data/       平行语料及其说明
models/     词表和模型权重，不在 git 里 —— 见「模型」一节
notebook/   模型定义、训练循环和损失曲线
src/        命令行翻译程序
```

## 数据

`data/zh-en.txt` 包含 1,381,995 条简体中文到英文的句对，每行一句，中英之间用制表符
分隔。语料来自 OPUS 的七个数据集，覆盖网页文本、影视字幕、维基百科、演讲和新闻。

具体来源、筛选规则、各语料的产出量、词表阈值和已知缺陷，见
[data/README.md](data/README.md)。

## 模型

模型权重放在 GitHub Release 里，而不是提交进 git —— 它们是约 100 MB 的二进制文件，
git 无法做增量压缩，进了历史就永远留着。

| 版本 | 说明 |
|---|---|
| **[v0.2](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.2)** | 当前版本，138 万句对，2,539 万参数 |
| [v0.1](https://github.com/Twilight-0419/Chinese-English-Translator/releases/tag/v0.1) | 第一次训练，49.3 万句对，4,440 万参数 |

每个 Release 带三个必须配套使用的文件：

| 文件 | v0.2 大小 |
|---|---:|
| `encoder.pt` | 37.9 MB |
| `decoder.pt` | 63.7 MB |
| `word2index_and_word_count.pt` | 1.3 MB |

词表必须和权重一起分发，因为两者是绑定的：索引 7 在这份词表里是 "is"，
换一份词表就变成别的词了。

```bash
mkdir -p models && cd models
base=https://github.com/Twilight-0419/Chinese-English-Translator/releases/download/v0.2
for f in encoder.pt decoder.pt word2index_and_word_count.pt; do curl -L -O "$base/$f"; done
```

## 使用

在项目根目录执行：

```bash
python -m src.main
```

```
请输入中文句子: 我爱你。
翻译结果: i love you .
是否继续翻译？(y/n):
```

必须写成 `python -m src.main`，不能写 `python src/main.py`。直接运行脚本时，
Python 会把 `src/` 而不是项目根目录放进搜索路径，`from src.translator import
translate` 就找不到这个包了。

`src/translator.py` 里是模型定义、权重加载和 `translate(sentence)` 函数。

## 训练

`notebook/C2E_Translator.ipynb` 包含完整流程：语料加载、词表构建、模型定义、
训练循环和损失曲线。从上往下依次运行即可。

v0.2 的训练参数：batch size 256，Adam 学习率 1e-4，梯度裁剪 max_norm 20，
teacher forcing 从 0.5 开始、每轮衰减 0.95，共 30 轮。

## 实现要点

**编码器** —— GRU 读取中文句子。padding 不会传进解码器：最终隐状态取每句话
真实最后一个词的位置，注意力分数也做了 mask，补齐位置的权重精确为 0。

**解码器** —— 每一步把上一步的隐状态和上一个词的 embedding 拼起来，
对编码器输出做注意力，再输出一个覆盖英文词表的概率分布。

**贪心解码** —— 每步直接取分数最高的词，所以同样的输入永远得到同样的输出。

**重复惩罚 2.0** —— 已经出现过的词，分数除以 2。不加这个惩罚，模型会输出
`i love love . .` 这种；加上之后，测试句的重复率从 72% 降到 0。

## 已知局限

- **只能处理短句**：语料筛选时限制在 6-19 个汉字，长句或复杂句属于训练分布之外，
  翻译质量很差。
- **语料本身有噪声**：混合了影视字幕和网页爬取，大约每 6～8 句里有 1 句对齐松散
  或错误。纯文本规则清不掉这类问题。
- **模型很小**：2,539 万参数，没有 beam search、没有子词切分，词表是 3.4 万 / 3.0 万。
  把它当作一条能跑通的完整流水线，而不是可用的翻译工具。
- **输出空格是字面的**：分词后直接用空格拼接，所以缩写和标点会变成
  `i 'm a cop .` 而不是 `I'm a cop.`
