from contextwalker import *


class CommentDeleter(ContextWalker):

    def __init__(self, string: str):
        super().__init__(string)
        self.in_comment = False
        self.debug = True
        self.comment_depth = 0
        self.commend_error = False

    def deal(self, ctx: Context) -> str | None | int | tuple[str, int]:
        if "double_device" in ctx.event_result:print(ctx.event_result["double_device"])
        if self.in_comment:
            return ""
        elif self.comment_depth:
            return ""
        else:
            return 0

    @str_event("//")
    def double_device(self, ctx):
        if not self.comment_depth:
            self.in_comment = True

    @str_event("\n", "\r")
    def new_line(self, ctx):
        if not self.comment_depth:
            self.in_comment = False

    @str_event("/*")
    def enter(self, ctx):
        if not self.in_comment:
            self.comment_depth += 1

    @str_event("*/",offset=-2)
    def exit(self, ctx):
        if not self.in_comment:
            if self.comment_depth:
                self.comment_depth -= 1
            else:
                self.commend_error = True

    def eventual(self, ctx) -> str|None|int|tuple[str,int]:
        if self.comment_depth:
            print("注释未闭合")
        if self.commend_error:
            print("多行注释外出现注释结束符号")


a = CommentDeleter("""
int a;
void func(int b){//114514 1919810
    printf('6');/*666
114514 // 
float abc;/*  */
hehehe // kaka */
static inline void opq();
}""")


print(a.walk())