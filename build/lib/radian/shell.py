from __future__ import unicode_literals
import sys
import os
import shlex
import subprocess


def run_command(command):
    if not command:
        sys.stdout.write("\n")
        return

    try:
        if sys.platform.startswith('win'):
            cmd_list = command.strip().split(" ", 1)
        else:
            cmd_list = shlex.split(command)
    except Exception as e:
        print(e)
        return

    if cmd_list[0] == "cd":
        if len(cmd_list) != 2:
            sys.stdout.write("cd method takes one argument\n\n")
            return
        try:
            path = cmd_list[1].strip()
            if path == "-":
                oldpwd = os.environ["OLDPWD"] if "OLDPWD" in os.environ else os.getcwd()
                os.environ["OLDPWD"] = os.getcwd()
                os.chdir(oldpwd)
            else:
                if sys.platform.startswith('win'):
                    path = path.replace("\\", "/")
                    if path.startswith('"') and path.endswith('"'):
                        path = path[1:-1]

                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                os.environ["OLDPWD"] = os.getcwd()
                os.chdir(path)

            sys.stdout.write(os.getcwd())
            sys.stdout.write("\n")
        except Exception as e:
            print(e)
            return

    else:
        if sys.platform.startswith('win'):
            p = subprocess.Popen(command, shell=True, stdin=sys.stdin, stdout=sys.stdout)
        else:
            shell = os.path.basename(os.environ.get("SHELL", "/bin/sh"))
            p = subprocess.Popen([shell, "-c", command], stdin=sys.stdin, stdout=sys.stdout)

        p.wait()
