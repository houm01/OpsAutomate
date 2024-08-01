#!/usr/bin/env python3

import re
import sys
import subprocess
from nb_log import get_logger


log = get_logger('exec')

version = sys.argv[1]

log.info(f'输入的版本号为: {version}')


def update_version(filename):
    # 读取文件内容
    with open(filename, 'r') as file:
        content = file.read()
        print(content)
    # 使用正则表达式查找版本号
    match = re.search(r"VERSION\s*=\s*'(\d+)\.(\d+)\.(\d+)'", content)
    
    print(match)
    
    if match:
        major, minor, patch = match.groups()
        new_patch = str(int(patch) + 1)
        
        # 构建新的版本号
        new_version = f"{major}.{minor}.{new_patch.zfill(1)}"
        
        # 替换旧版本号为新版本号
        new_content = content.replace(match.group(0), f"VERSION = '{version}'")
        
        # 写入更新后的内容到文件
        with open(filename, 'w') as file:
            file.write(new_content)
        
        log.info(f"版本号已更新为 {version}")
# 调用函数
update_version('setup.py')


def run_shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    if result.stdout:
        log.debug(result.stdout)
    if result.stderr:
        log.error(result.stderr)

run_shell_cmd(cmd='git add .')
run_shell_cmd(cmd=f"""git commit -m "Released v{version}""")
run_shell_cmd(cmd=f'git tag -a v{version} -m v{version}')
run_shell_cmd(cmd='git push --tag')
run_shell_cmd(cmd='git push')


