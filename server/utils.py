# 服务端统一输出工具
from colorama import Fore, Style, init

init(autoreset=True)


# 输出成功信息
def println_success(text: str):
    print(Fore.GREEN + Style.BRIGHT + text)


# 输出失败信息
def println_failed(text: str):
    print(Fore.RED + Style.BRIGHT + text)
