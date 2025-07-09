from enum import Enum, auto

class State(Enum):
    free = auto()  # 文本
    list = auto()  # 列表
    code = auto()  # 代码块
    table = auto()  # 表格
    quote = auto()  # 引用

class InlineType(Enum):
    label = auto()
    end = auto()


class Type(Enum):
    heading = auto()
    list = auto()
    code = auto()
    table = auto()
    quote = auto()
    inline = auto()
    paragraph = auto()
doc = '''这是[underline;color(red,green):一个]简单的[bold:行内[color('red'):标[text:记]]]'''
class TokenParser():
    def __init__(self):
        self.token = []  # 最终结果
        self.temp_token = []  # 构造区 token模型:(标签,[参1,参2,...],*文本)
        self.state = State.free
        self.global_align = "left"

        self.temp_slice = None  # 开始

    def inline_parser(self, line:str):  # note:1最简单的[:]完成 2.[:][:]完成 3.[:[:]]完成
        temp = []
        state = "text"  # 初始化
        marked_index = 0 # 初始化
        current_index = 0 # 初始化
        label_num = []
        line_length = len(line)
        while line_length > current_index:
            char = line[current_index]
            if char == '[':
                if state == "text":  # 标记标签开始
                    state = '['
                    text = line[marked_index:current_index]
                    temp.append(text)
                    marked_index = current_index + 1
                elif state == ':':
                    state = '['
                    text = line[marked_index:current_index]
                    temp.append(text)
                    marked_index = current_index + 1
            elif char == ':':
                if state == '[':  # 标记标签结束
                    state = ':'
                    labels = line[marked_index:current_index].split(';')
                    temp.extend((InlineType.label,i) for i in labels)
                    label_num.append(len(labels))# 记录labeltype数量,便于后期闭合
                    marked_index = current_index + 1
            elif char == ']':
                if state == ':':  # 标记一个行内标记结束
                    state = "text"
                    text = line[marked_index:current_index]
                    temp.append(text)
                    temp.extend((InlineType.end,) * label_num.pop()) # 闭合label,需配合labeltype数量
                    marked_index = current_index + 1
                elif state == "text":
                    text = line[marked_index:current_index]
                    temp.append(text)
                    temp.extend((InlineType.end,) * label_num.pop()) # 闭合label,需配合labeltype数量
                    marked_index = current_index + 1

            current_index += 1
        return temp
    
    def tokenize(self, texts:str):
        """
        按行分割,逐行解析
        """
        lines = texts.split("\n")
        lines_len = len(lines)
        line_index = 0
        while lines_len > line_index:
            line = lines[line_index]  # 遍历每行
            if self.state == State.free:
                # 块结构处理
                if line.startswith("[heading") and line[-1] == "]":
                    # [heading4<:xxx] (Type,[align,size],text)
                    align = {"<":"left",">":"right","^":"center"}.get(line[9])
                    size = line[8]
                    text = line[10 if align else 9:-1]
                    self.token.append((Type.heading,[align,size],self.inline_parser(text)))
                elif line.startswith("[paragraph") and line[-1] == "]":
                    # [paragraph<]
                    self.global_align = {"<":"left",">":"right","^":"center"}.get(line[10])
                elif line in (mapping := {"[list]":State.list,"[code]":State.code,"[table]":State.table,"[quote]":State.quote}):
                    # ("[list]","[code]","[table]","[quote]")
                    self.state = mapping[line]
                    self.temp_token.extend((Type(self.state.value),[]))  # hack:能运行,且结果正确,但不知道原理(冒汗)
                # 行结构
                elif '[' in line and ':' in line and ']' in line:
                    self.token.append((Type.inline,[self.global_align],self.inline_parser(line)))
                else:
                    self.token.append((Type.paragraph,[self.global_align],line))
            # 状态机
            elif line == "[end]":
                # 释放状态
                self.state = State.free
                self.token.append(tuple(self.temp_token))
                self.temp_token = []
            elif self.state in (State.list, State.code, State.table, State.quote):
                # 多行缓存
                self.temp_token.append(line)


            line_index += 1

tokenparser = TokenParser()
tokenparser.tokenize(doc)
token_list = tokenparser.token
print(token_list,sep='\n')