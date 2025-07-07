from enum import Enum, auto

class State(Enum):
    free = auto()  # 文本
    list = auto()  # 列表
    code = auto()  # 代码块
    table = auto()  # 表格
    quote = auto()  # 引用

class InlineState(Enum):
    wait = auto()
    label = auto()
    text = auto()

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

class TokenParser():
    def __init__(self):
        self.token = []  # 最终结果
        self.temp_token = []  # 构造区 token模型:(标签,[参1,参2,...],*文本)
        self.state = State.free
        self.global_align = "left"

        self.temp_slice = None  # 开始
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
                    self.token.append((Type.heading,[align,size],text))
                elif line.startswith("[paragraph") and line[-1] == "]":
                    # [paragraph<]
                    self.global_align = {"<":"left",">":"right","^":"center"}.get(line[10])
                elif line in (mapping := {"[list]":State.list,"[code]":State.code,"[table]":State.table,"[quote]":State.quote}):
                    # ("[list]","[code]","[table]","[quote]")
                    self.state = mapping[line]
                    self.temp_token.extend((Type(self.state.value),[]))
                # 行结构
                elif '[' in line and ':' in line and ']' in line:
                    # 初始化token
                    self.temp_token.extend((Type.inline,[self.global_align]))

                    row_index = 0
                    row_len = len(line)
                    while row_index < row_len:
                        char = line[row_index]  # 遍历每行
                        # free -> label -> wait -> text -> wait
                        if self.state == State.free:
                            if char == '[':
                                self.state = InlineState.label
                        elif self.state in (InlineState.label,InlineState.text):
                            self.state = InlineState.wait
                            self.temp_slice = row_index
                        elif self.state == InlineState.wait:
                            if char == ':':
                                self.state = InlineState.text
                                self.temp_token.append((InlineType.label,line[self.temp_slice:row_index]))
                            elif char == ']':
                                self.state = State.free
                                self.temp_token.extend((line[self.temp_slice:row_index],InlineType.end))
                                self.token.append(tuple(self.temp_token))
                        # todo:行内结构分析
                        row_index += 1
                    self.temp_token = []
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

doc = """[heading1:wosk]
[paragraph>]
线性模型没那本事
[paragraph<]
[test:测试]
[list]
-一级
    -二级
    -二级
-一级
[end]
"""
tokenparser = TokenParser()
tokenparser.tokenize(doc)
print(*tokenparser.token, sep="\n")
print(tokenparser.global_align)