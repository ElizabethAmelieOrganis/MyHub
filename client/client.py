#!/usr/bin/env python3
import cmd
import os
import sys
import shutil
from typing import Any, Dict, List, Optional, Union

import click
import pyfiglet
import requests
from colorama import Fore, Style, init
from dotenv import load_dotenv

# ==========配置文件==========
load_dotenv()
config: dict = {
    "title": os.getenv("title", ""),
    "version": os.getenv("version", ""),
    "upload_day": os.getenv("upload_day"),
    "run_env": os.getenv("run_env"),
    "server_url": os.getenv("server_url"),
    "server_port": os.getenv("server_port"),
}
SERVER_ADDRESS: str = f"http://{config['server_url']}:{config['server_port']}"
init(autoreset=True)
user_list: List[str] = ["HY", "LCY"]
user_map: Dict[str, str] = {"HY": "HY-token", "LCY": "LCY-token"}


# ==========类型定义==========
RequestBody = Optional[Union[Dict[str, Any], str]]
FilesType = Optional[Dict[str, Any]]


# ==========辅助函数==========
def show_welcome() -> None:
    """欢迎内容"""
    text = pyfiglet.figlet_format("MyHub", font="block")
    print(Fore.BLUE + Style.BRIGHT + text)
    print(f"Welcome to {config['title']} v{config['version']} ({config['run_env']})")


def login() -> str:
    """简单用户登录"""
    while True:
        user = str(input("请输入用户名:"))
        if user not in user_list:
            click.echo("用户不存在")
            continue
        click.echo(f"登录成功，欢迎{user}")
        break
    return user


def check_server() -> bool:
    """检查服务器连接"""
    click.echo(f"正在尝试连接{SERVER_ADDRESS}...")
    try:
        r = requests.get(SERVER_ADDRESS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            click.echo(
                Fore.GREEN
                + f"√ 成功与服务器建立连接,当前服务版本v{data.get('version', '')}"
            )
            return True
    except requests.exceptions.ConnectionError:
        click.echo(Fore.RED + "✗ 连接失败,请检查:")
        click.echo(Fore.RED + "   1.服务器地址")
        click.echo(Fore.RED + "   2.网络连接")
        click.echo(Fore.RED + "   1.服务运行情况")
    except Exception as e:
        click.echo(Fore.RED + f"✗ 其他错误:{e}")
    return False


class UserStore(object):
    """用户状态管理"""

    # 登录状态
    def __init__(self, auth_user: str, auth_token: str):
        self.auth_user = auth_user
        self.auth_token = auth_token

    # 封装post请求，自动添加请求头
    def post(
        self, url: str, data: RequestBody = None, files: FilesType = None, **kwargs
    ):
        headers = {"token": self.auth_token}
        try:
            if files:
                # 上传文件时，data作为form data传递
                r = requests.post(
                    f"{SERVER_ADDRESS}{url}",
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=30,
                )
            else:
                # 普通请求，data作为json传递
                r = requests.post(
                    f"{SERVER_ADDRESS}{url}",
                    json=data,
                    files=files,
                    headers=headers,
                    timeout=30,
                )
            return r.json()
        except Exception as e:
            click.echo(f"请求错误:{e}")
            return e

    def upload_file(self, file_path: str, stored_name: str = None):
        if not os.path.exists(file_path):
             return {"detail": f"文件不存在: {file_path}"}
             
        try:
            # 必须用rb模式打开
            with open(file_path, "rb") as f:
                # files字典: {'参数名': (文件名, 文件对象, 类型)}
                # 这里简单传递: {'file': 文件对象}，requests会自动获取文件名
                files = {"file": f}
                data = {}
                if stored_name:
                    data["stored_name"] = stored_name
                
                # 注意：这里直接调用修改后的post方法
                response = self.post(url="/file/upload", data=data, files=files)
                return response
        except Exception as e:
            return {"detail": f"上传异常: {str(e)}"}

    def list_files(self):
        return self.post(url="/file/list")

    def get_file_detail(self, file_id: int):
        data = {"file_id": file_id}
        return self.post(url="/file/detail", data=data)

    def create_msg(self, msg: str, file_id: int = None):
        data: dict = {"data": msg}
        if file_id:
            data["file_id"] = file_id
        response = self.post(url="/msg/create", data=data)
        return response

    def list_msgs(self, limit: int = 4, file_id: int = None):
        data = {"limit": limit}
        if file_id:
            data["file_id"] = file_id
        response = self.post(url="/msg/list", data=data)
        return response
# ==========主菜单==========
class HubShell(cmd.Cmd):
    """主菜单"""

    prompt = "hub>"

    # 初始化时传入UserStore对象
    def __init__(self, user: UserStore):
        super().__init__()
        self.user = user

    def do_exit(self, arg) -> None:
        """退出: exit"""
        click.echo("👋 再见!")
        sys.exit(1)

    def do_clear(self, arg):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")
        show_welcome()

    def do_config(self, arg):
        """查看当前配置信息"""
        click.echo("当前系统配置信息:")
        click.echo(f"  服务器地址:{SERVER_ADDRESS}")
        click.echo(f"  运行系统:{config['run_env']}")
        click.echo(f"  版本号:{config['version']}")

    def do_help(self, arg: str) -> bool | None:
        if arg:
            # 显示具体命令的帮助
            super().do_help(arg)
            return
        click.echo("命令文档,可使用 help <cmd> 查看具体帮助")
        click.echo("=" * 50)
        click.echo("主菜单命令:")
        click.echo("    clear           清屏")
        click.echo("    help <cmd>      命令详情")
        click.echo("    config          查看配置信息")
        click.echo("    messages        进入留言系统")
        click.echo("    exit            退出")

    def do_messages(self, arg):
        """进入留言系统: messages"""
        click.echo("💬进入留言系统...")
        MessagesShell(self.user).cmdloop()

    def do_files(self, arg):
        """进入文件系统: files"""
        click.echo("📁进入文件系统...")
        FilesShell(self.user).cmdloop()


# ==========留言系统==========
class MessagesShell(cmd.Cmd):
    """留言系统"""

    def __init__(self, user: UserStore):
        super().__init__()
        self.user = user

    prompt = Fore.MAGENTA + "hub:messages> " + Style.RESET_ALL

    def do_msg(self, arg):
        """新建全局留言 msg <content>"""
        if not arg:
            click.echo("✗ 留言内容不能为空: msg '<content>'")
            return
            
        content = arg.strip()
        
        # 检查是否用英文单引号包裹
        if not (content.startswith("'") and content.endswith("'")):
             click.echo("✗ 留言内容必须使用英文单引号包裹: msg '<content>'")
             return
             
        # 去除引号
        content = content[1:-1]
        
        if not content:
            click.echo("✗ 留言内容不能为空: msg '<content>'")
            return
            
        # 发送消息
        response= self.user.create_msg(content)
        message=response.get("message", "")
        click.echo(message)

    def do_list(self, arg):
        """查看留言列表: list [-n <number>|--all]"""
        os.system("cls" if os.name == "nt" else "clear")
        
        limit = 4
        args = arg.split()
        
        if "--all" in args:
            limit = 0
        elif "-n" in args:
            try:
                idx = args.index("-n")
                if idx + 1 < len(args):
                    val = args[idx+1]
                    if val == "--all":
                        limit = 0
                    else:
                        limit = int(val)
                else:
                    click.echo("参数错误: -n 后需要跟数字")
                    return
            except ValueError:
                click.echo("参数错误: -n 后需要跟数字")
                return

        response = self.user.list_msgs(limit)
        messages = response if isinstance(response, list) else response.get("messages", [])
        
        if not messages:
            click.echo("暂无留言")
            return
            
        # 获取终端宽度
        width = shutil.get_terminal_size((80, 20)).columns
        width = min(width, 100)
        
        click.echo("-" * width + Style.RESET_ALL)
        
        for msg in messages:
            author = msg.get('author', 'Unknown')
            content = msg.get('content', '')
            created_at = msg.get('created_at', '')
            
            # 格式化时间: 2023-01-01T12:00:00.000000 -> 2023-01-01 12:00:00
            if 'T' in created_at:
                created_at = created_at.replace('T', ' ')
                if '.' in created_at:
                    created_at = created_at.split('.')[0]
            
            # 内容左对齐显示
            click.echo(f"\n{content}")
            
            # 用户和时间右对齐显示
            meta_info = f"-- {author} @ {created_at}"
            click.echo(Fore.WHITE + Style.DIM + f"{meta_info:>{width}}" + Style.RESET_ALL)
            
            # 分隔线
            click.echo("-" * width + Style.RESET_ALL)

    def do_back(self, arg):
        """返回主菜单: back"""
        click.echo("←返回主菜单")
        return True

    def do_clear(self, arg):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")
        show_welcome()

    def do_exit(self, arg) -> None:
        """退出: exit"""
        click.echo("👋 再见!")
        sys.exit(1)


# ==========文件内容浏览==========
class FileContentShell(cmd.Cmd):
    """文件内容浏览"""

    def __init__(self, user: UserStore, file_info: dict):
        super().__init__()
        self.user = user
        self.file_info = file_info
        self.file_id = file_info['id']
        self.prompt = Fore.YELLOW + f"hub:files:{self.file_id}> " + Style.RESET_ALL
        
        # 显示文件详情
        self.do_clear(None)

    def do_clear(self, arg):
        """清屏并显示详情"""
        os.system("cls" if os.name == "nt" else "clear")
        self.show_info()

    def show_info(self):
        f = self.file_info
        width = shutil.get_terminal_size((80, 20)).columns
        width = min(width, 100)
        
        click.echo("-" * width)
        click.echo(f"ID: {f['id']}")
        click.echo(f"原始名称: {f['original_name']}")
        click.echo(f"存储名称: {f['stored_name']}")
        
        size = f['size']
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.2f} KB"
        else:
            size_str = f"{size/(1024*1024):.2f} MB"
        click.echo(f"文件大小: {size_str}")
        
        click.echo(f"上传用户: {f['uploader']}")
        
        upload_time = f['upload_time']
        if 'T' in upload_time:
            upload_time = upload_time.replace('T', ' ')
            if '.' in upload_time:
                upload_time = upload_time.split('.')[0]
        click.echo(f"上传时间: {upload_time}")
        
        if f.get('tags'):
            click.echo(f"标签: {f['tags']}")
            
        click.echo("-" * width)
        click.echo("可用命令: msg 'content', list, back, exit")

    def do_msg(self, arg):
        """为当前文件留言: msg <content>"""
        if not arg:
            click.echo("✗ 留言内容不能为空: msg '<content>'")
            return
            
        content = arg.strip()
        
        # 检查是否用英文单引号包裹
        if not (content.startswith("'") and content.endswith("'")):
             click.echo("✗ 留言内容必须使用英文单引号包裹: msg '<content>'")
             return
             
        content = content[1:-1]
        
        if not content:
            click.echo("✗ 留言内容不能为空: msg '<content>'")
            return
            
        # 发送消息
        response = self.user.create_msg(content, self.file_id)
        message = response.get("message", "")
        click.echo(message)

    def do_list(self, arg):
        """查看当前文件的留言: list [-n <number>|--all]"""
        limit = 4
        args = arg.split()
        
        if "--all" in args:
            limit = 0
        elif "-n" in args:
            try:
                idx = args.index("-n")
                if idx + 1 < len(args):
                    val = args[idx+1]
                    if val == "--all":
                        limit = 0
                    else:
                        limit = int(val)
                else:
                    click.echo("参数错误: -n 后需要跟数字")
                    return
            except ValueError:
                click.echo("参数错误: -n 后需要跟数字")
                return

        response = self.user.list_msgs(limit, self.file_id)
        messages = response if isinstance(response, list) else response.get("messages", [])
        
        if not messages:
            click.echo("暂无留言")
            return
            
        width = shutil.get_terminal_size((80, 20)).columns
        width = min(width, 100)
        
        click.echo("-" * width)
        for msg in messages:
            author = msg.get('author', 'Unknown')
            content = msg.get('content', '')
            created_at = msg.get('created_at', '')
            
            if 'T' in created_at:
                created_at = created_at.replace('T', ' ')
                if '.' in created_at:
                    created_at = created_at.split('.')[0]
            
            click.echo(f"\n{content}")
            meta_info = f"-- {author} @ {created_at}"
            click.echo(Fore.WHITE + Style.DIM + f"{meta_info:>{width}}" + Style.RESET_ALL)
            click.echo("-" * width)

    def do_back(self, arg):
        """返回上一级"""
        click.echo("←返回文件列表")
        return True

    def do_exit(self, arg):
        """退出"""
        click.echo("👋 再见!")
        sys.exit(1)


# ==========文件系统==========
class FilesShell(cmd.Cmd):
    """文件系统"""

    def __init__(self, user: UserStore):
        super().__init__()
        self.user = user

    prompt = Fore.CYAN + "hub:files> " + Style.RESET_ALL

    def do_upload(self, arg):
        """上传文件: upload <filepath> [stored_name]"""
        if not arg:
            click.echo("✗ 请指定要上传的文件: upload <filepath> [stored_name]")
            return

        args = arg.split()
        file_path = args[0]
        stored_name = args[1] if len(args) > 1 else None

        # 检查并补全后缀
        if stored_name:
            _, ext = os.path.splitext(file_path)
            if not os.path.splitext(stored_name)[1]:
                 stored_name += ext

        click.echo(f"正在上传 {file_path} ...")
        response = self.user.upload_file(file_path, stored_name)

        if isinstance(response, dict):
            if "message" in response:
                click.echo(Fore.GREEN + f"√ {response['message']}")
                if "stored_name" in response:
                    click.echo(f"  存储名称: {response['stored_name']}")
            elif "detail" in response:
                click.echo(Fore.RED + f"✗ 上传失败: {response['detail']}")
            else:
                click.echo(Fore.RED + f"✗ 上传失败: 未知响应 {response}")
        else:
            click.echo(Fore.RED + f"✗ 上传失败: {response}")

    def do_list(self, arg):
        """查看文件列表: list"""
        os.system("cls" if os.name == "nt" else "clear")
        response = self.user.list_files()

        if isinstance(response, list):
            files = response
        elif isinstance(response, dict) and "detail" in response:
            click.echo(Fore.RED + f"✗ 获取列表失败: {response['detail']}")
            return
        else:
            click.echo(Fore.RED + f"✗ 获取列表失败: {response}")
            return

        if not files:
            click.echo("暂无文件")
            return

        # 获取终端宽度
        width = shutil.get_terminal_size((80, 20)).columns
        width = min(width, 100)

        click.echo("-" * width)

        for file in files:
            fid = file.get('id', '')
            original_name = file.get('original_name', 'Unknown')
            stored_name = file.get('stored_name', 'Unknown')
            size = file.get('size', 0)
            uploader = file.get('uploader', 'Unknown')
            upload_time = file.get('upload_time', '')

            # Format time
            if 'T' in upload_time:
                upload_time = upload_time.replace('T', ' ')
                if '.' in upload_time:
                    upload_time = upload_time.split('.')[0]

            # Format size (KB/MB)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            else:
                size_str = f"{size/(1024*1024):.2f} MB"

            click.echo(f"\nID: {fid} | {original_name} ({size_str})")
            if stored_name != original_name:
                click.echo(f"Stored as: {stored_name}")

            meta = f"-- {uploader} @ {upload_time}"
            click.echo(Fore.WHITE + Style.DIM + f"{meta:>{width}}" + Style.RESET_ALL)
            click.echo("-" * width)

    def do_look(self, arg):
        """查看文件详情: look -id <file_id>"""
        if not arg:
            click.echo("✗ 请指定文件ID: look -id <file_id>")
            return
            
        args = arg.split()
        if "-id" not in args:
            click.echo("✗ 请使用 -id 参数指定文件ID")
            return
            
        try:
            idx = args.index("-id")
            if idx + 1 >= len(args):
                click.echo("✗ 请指定文件ID")
                return
            file_id = int(args[idx+1])
        except ValueError:
            click.echo("✗ 文件ID必须是数字")
            return
            
        response = self.user.get_file_detail(file_id)
        if "detail" in response:
            click.echo(Fore.RED + f"✗ 获取文件详情失败: {response['detail']}")
            return
            
        # 进入文件内容Shell
        FileContentShell(self.user, response).cmdloop()

    def do_back(self, arg):
        """返回主菜单: back"""
        click.echo("←返回主菜单")
        return True

    def do_clear(self, arg):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")

    def do_exit(self, arg):
        """退出"""
        click.echo("👋 再见!")
        sys.exit(1)


if __name__ == "__main__":
    user = login()
    useUserStore = UserStore(user, user_map[user])
    show_welcome()
    if not check_server():
        sys.exit(1)
    click.echo("使用 'help' 获得帮助 , 'exit'退出 ")
    try:
        HubShell(useUserStore).cmdloop()
    except KeyboardInterrupt:
        click.echo("\n👋 再见!")
