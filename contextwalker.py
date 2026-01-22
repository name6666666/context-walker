"""context walker是一个文本处理框架，以缓冲区为基本逻辑，相比正则表达式，它基于继承ContextWalker类定制\"上下文遍历器\"来工作。
此模块中约有5%的实现依靠AI，已用左括号加AI加右括号的固定形式的注释标出，其余均人工实现"""

from abc import ABC
from abc import abstractmethod
from typing import final, Callable
from colorama import init, Fore, Back, Style

init()

class ContextWalkerError(Exception):
    pass

def _merge_ranges(*args, merge_adjacent=True):
    """合并重叠的索引范围，支持列表切片语义（AI）"""
    if not args:
        return []
    # 转换为列表并按起始位置排序
    ranges = sorted([list(r) for r in args], key=lambda x: x[0])
    merged = [ranges[0]]
    for current in ranges[1:]:
        last = merged[-1]
        # 确定是否应该合并
        # 对于列表切片，相邻范围(1,3)和(3,5)不重叠
        # 如果要合并相邻范围，需要特殊处理
        should_merge = current[0] <= last[1] if not merge_adjacent else current[0] <= last[1] + 1
        if should_merge:
            # 扩展范围到最右边界
            last[1] = max(last[1], current[1])
        else:
            # 无重叠，添加新区间
            merged.append(current)
    # 转回元组
    return [tuple(r) for r in merged]

def _sum(*args, if_void=None):
    lst = [*args]
    if lst:
        result = lst[0]
        for i in lst[1:]:
            result += i
        return result
    else:
        return if_void

def _style_str(string: str, *color):
    return _sum(*color) + repr(string)[1:-1] + Style.RESET_ALL

def _get_all_methods(cls):
    """获取一个类的MRO规则下的所有方法（AI）"""
    methods = {}
    for base in cls.__mro__[:-1]:
        for name, obj in base.__dict__.items():
            if callable(obj) and name not in methods:
                methods[name] = obj
    return methods

def match_beginning(string: str, *targets: str) -> bool:
    """返回一个字符串开头是否是要匹配的目标，可以有多个目标"""
    strs = [*targets]
    if not all(type(i) == str for i in strs):
        raise Exception("Unexpected type. *targets expected strings.")
    return any(string[0:len(i)] == i for i in strs)

class Context:
    def __init__(self, buffer, dealt, residue, index, result, event_result):
        self.event_result: dict = event_result
        self.buffer: str = buffer
        self.result: str = result
        self.dealt: str = dealt
        self.residue: str = residue
        self.index: int = index

class ContextWalker(ABC):
    _str_events: list[Callable] = []

    def __init_subclass__(cls, **kwargs):
        cls._str_events: list[Callable] = [method for _,method in _get_all_methods(cls).items() if hasattr(method,"_is_str_event")]

    def __init__(self, string: str):
        self._string: str = string
        self.debug = False

        self._result: str = ""
        self._buffer: str = ""

    @final
    def walk(self) -> str:
        """开始遍历"""

        self._result = ""
        self._buffer = ""

        i = 0
        while i < len(self._string):
            debug_event = []
            debug_index = i
            debug_buffer = None
            debug_result1 = self._result
            debug_result2 = None

            self._buffer += self._string[i]

            event_result = {}
            for func in self.__class__._str_events:
                if match_beginning(self._string[i + func.offset:], *func.string):
                    debug_event.append(func)
                    result = func.__get__(self, self.__class__)(Context(self._buffer, self._string[0:i], self._string[i:], i, self._result, event_result.copy()))#对于这一行的__get__，（AI）
                    event_result[func.__name__] = result

            debug_buffer = self._buffer
            deal = self.deal(Context(self._buffer, self._string[0:i], self._string[i:], i, self._result, event_result))

            if deal is not None:
                if type(deal) == str:
                    self._result += deal
                    self._buffer = ""
                elif type(deal) == int:
                    if deal < 0: raise ContextWalkerError("Should be a positive number.")
                    self._result += self._buffer + self._string[i + 1:i + deal + 1]
                    self._buffer = ""
                    i += deal
                elif type(deal) == tuple:
                    if not type(deal[0]) == str and type(deal[1]) == int: raise ContextWalkerError("Unexpected type. Expected str or NoneType or int or tuple[str,int].")
                    if deal[1] < 0: raise ContextWalkerError("Should be a positive number.")
                    self._result += deal[0] + self._string[i + 1:i + deal[1] + 1]
                    self._buffer = ""
                    i += deal[1]
                else:
                    raise ContextWalkerError("Unexpected type. Expected str or NoneType or int or tuple[str,int].")
            i += 1

            debug_result2 = self._result
            if self.debug: self._debug(debug_event, debug_index, debug_buffer, debug_result1, debug_result2)

        deal = self.eventual(Context(self._buffer, self._string[0:i], self._string[i:], i, self._result, {}))

        if deal is not None:
            if type(deal) == str:
                self._result += deal
                self._buffer = ""
            elif type(deal) == int:
                if deal < 0: raise ContextWalkerError("Should be a positive number.")
                self._result += self._buffer + self._string[i + 1:i + deal + 1]
                self._buffer = ""
                i += deal
            elif type(deal) == tuple:
                if not type(deal[0]) == str and type(deal[1]) == int: raise ContextWalkerError(
                    "Unexpected type. Expected str or NoneType or int or tuple[str,int].")
                if deal[1] < 0: raise ContextWalkerError("Should be a positive number.")
                self._result += deal[0] + self._string[i + 1:i + deal[1] + 1]
                self._buffer = ""
                i += deal[1]
            else:
                raise ContextWalkerError("Unexpected type. Expected str or NoneType or int or tuple[str,int].")

        return self._result

    @abstractmethod
    def deal(self, context: Context) -> str | None | int | tuple[str,int]:
        """定义每次遍历对缓冲区的处理，其四种不同类型的返回值代表不同的操作"""
        pass

    def eventual(self, context: Context) -> str | None | int | tuple[str,int]:
        """结束遍历时调用"""
        pass

    @final
    def _debug(self, event, index, buffer, result1, result2):
        where_to_color = set()
        for i in event:
            for j in i.string:
                where_to_color.add((index + i.offset, index + i.offset + len(j)))
        where_to_color = _merge_ranges(*where_to_color)

        device_point = [0]
        for i,j in where_to_color:
            device_point += [i, j]
        device_point.append(len(self._string))

        colored_str = []
        case = 0
        for i,j in zip(device_point, device_point[1:]):
            if case % 2 == 0:
                if i <= index < j:
                    colored_str.append(_style_str(self._string[i:index], Back.GREEN, Fore.BLACK)+
                                       _style_str(self._string[index], Back.LIGHTGREEN_EX, Fore.BLACK)+
                                       _style_str(self._string[index+1:j], Back.GREEN, Fore.BLACK))
                else:
                    colored_str.append(_style_str(self._string[i:j], Back.GREEN, Fore.BLACK))
            else:
                if i <= index < j:
                    colored_str.append(_style_str(self._string[i:index], Back.MAGENTA, Fore.BLACK) +
                                       _style_str(self._string[index], Back.LIGHTMAGENTA_EX, Fore.BLACK) +
                                       _style_str(self._string[index + 1:j], Back.MAGENTA, Fore.BLACK))
                else:
                    colored_str.append(_style_str(self._string[i:j], Back.RED, Fore.BLACK))
            case += 1
        colored_str = _sum(*colored_str)

        line1 = colored_str
        line2 = _style_str(result1, Back.BLUE, Fore.BLACK) + _style_str(buffer, Back.YELLOW, Fore.BLACK)
        line3 = _style_str(result2, Back.BLUE, Fore.BLACK)

        self.debug_info(line1, line2, line3, index)

    def debug_info(self, event_and_index: str, buffer: str, result: str, index: int):
        print(event_and_index + "\n" + buffer + "\n" + result + "\n")

def str_event(*string: str, offset: int = 0):
    """将实例方法注册为字符串事件方法的装饰器工厂，遍历到正后方有目标字符串时自动触发，常用来实现状态机，与python的MRO系统融合良好，
    在模块的内部实现中自动注册所有被MRO命中的字符串事件方法。事件方法触发顺序遵循从先定义到后定义、从子类到父类。"""
    def decorator(func):
        func.string = [*string]
        func.offset = offset
        func._is_str_event = None
        return func
    return decorator
