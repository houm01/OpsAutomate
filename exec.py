#!/usr/bin/env python3

import sys
import subprocess
from nb_log import get_logger


log = get_logger('exec')

version = sys.argv[1]



# 读取文件内容
with open('setup.py', 'r') as file:
    content = file.read()

# 替换内容
new_content = content.replace('version_replace', version)

# 将更改后的内容写回文件
with open('setup.py', 'w') as file:
    file.write(new_content)


def run_shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    log.debug(result.stdout)
    log.error(result.stderr)

run_shell_cmd(cmd='git add .')
run_shell_cmd(cmd=f"""git commit -m "Released v{version}""")
run_shell_cmd(cmd=f'git tag -a v{version} -m v{version}')
run_shell_cmd(cmd='git push --tag')
run_shell_cmd(cmd='git push')


