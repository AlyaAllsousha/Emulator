import tkinter as tk
from tkinter import scrolledtext
import re
from datetime import datetime
import os
import zipfile
import argparse
from pathlib import Path
import base64

class VFS:
    def __init__(self, zip_path=None):
        self.filesystem = {}
        self.curr_dir = "/"
        if zip_path:
            self.load_from_zip(zip_path)
        else:
            self.create_default_vfs()
    
    def load_from_zip(self, zip_path):
        try:
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"ZIP-файл не найден: {zip_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        dir_path = file_info.filename
                        if not dir_path.endswith('/'):
                            dir_path += '/'
                        self.filesystem[dir_path] = None
                    else:
                        content = zip_ref.read(file_info.filename)
                        try:
                            content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            content = "base64:" + base64.b64encode(content).decode('utf-8')
                        self.filesystem[file_info.filename] = content
            
            print(f"VFS загружена из {zip_path}")
            
        except zipfile.BadZipFile:
            raise ValueError(f"Неверный формат ZIP-файла: {zip_path}")
        except Exception as e:
            raise Exception(f"Ошибка загрузки VFS: {str(e)}")
    
    
    def create_default_vfs(self):
        self.filesystem = {
            "/": None,
            "bin/": None,
            "bin/app.exe": "base64:ZXhlY3V0YWJsZSBiaW5hcnkgZGF0YQ==",
            "documents/": None,
            "documents/report.txt": "Отчет за 2025 год \nВсе работает отлично!",
            "documents/projects/": None,
            "documents/projects/project1.py": "print('Hello VFS!')\n# Python код",
            "documents/projects/project2.c": "// C код\n#include <stdio.h>\nint main() { return 0; }",
            "config/": None,
            "config/settings.ini": "[settings]\nlanguage = ru\ntheme = dark",
            "temp/": None
        }
     
    def normalize_path(self, path):
        if path == ".":
            return self.curr_dir
        if not path.startswith("/"):
            path = os.path.join(self.curr_dir, path).replace("\\", "/")

        parts = path.split('/')
        result_parts = []
        for part in parts:
            if part == "..":
                if result_parts:
                    result_parts.pop()
            elif part and part != ".":
                result_parts.append(part)
        
        result_path = "/".join(result_parts)
        if path.endswith("/") and not result_path.endswith("/"):
            result_path += "/"
        
        return result_path or "/"
    
    def list_dir(self, path="."):
        normalized_path = self.normalize_path(path)
        
        if normalized_path in self.filesystem and not normalized_path.endswith("/"):
            return [os.path.basename(normalized_path)]
        
        if not normalized_path.endswith("/") and normalized_path != "/":
            normalized_path += "/"
        
        items = set()
        
        for file_path in self.filesystem.keys():
            if normalized_path == "/":
                if file_path == "/":
                    continue
                if "/" in file_path:
                    first_item = file_path.split("/")[0]
                    if "/" in file_path[len(first_item):]:
                        items.add(first_item + "/")
                    else:
                        items.add(first_item)
                else:
                    items.add(file_path)
            else:
                if file_path.startswith(normalized_path):
                    rel_path = file_path[len(normalized_path):]
                    if not rel_path:
                        continue
                    
                    if "/" in rel_path:
                        first_part = rel_path.split("/")[0]
                        items.add(first_part + "/")
                    else:
                        items.add(rel_path)
        
        return sorted(list(items))
    def read_file(self, file_path):
        normalized_path = self.normalize_path(file_path)
        
        if normalized_path.endswith("/"):
            return None
        
        if normalized_path in self.filesystem:
            content = self.filesystem[normalized_path]
            if content and content.startswith("base64:"):
                return base64.b64decode(content[7:])
            return content
        return None
    
    
    def change_dir(self, new_dir):
        if new_dir == "/":
            self.curr_dir = "/"
            return True
        
        normalized_path = self.normalize_path(new_dir)
        
        dir_path = normalized_path + "/" if not normalized_path.endswith("/") else normalized_path
        
        if dir_path in self.filesystem:
            self.curr_dir = normalized_path
            return True
        
        for path in self.filesystem.keys():
            if path.startswith(normalized_path + "/") or path == normalized_path:
                self.curr_dir = normalized_path
                return True
        
        return False
    def get_curr_path(self):
        return self.curr_dir
    
    def get_file_content(self, file_path):
        normalized_path = self.normalize_path(file_path)
        
        if normalized_path in self.filesystem:
            content = self.filesystem[normalized_path]
            if content and content.startswith("base64:"):
                return base64.b64decode(content[7:]).decode('latin-1')
            return content
        return None
    
    def tree_traverse(self, path, prefix="", depth=-1, current_depth=1):
        if depth >= 0 and current_depth > depth:
            return []
        normalized_path = self.normalize_path(path)
        if not normalized_path.endswith("/"):
            normalized_path += "/"
        
        result = []
        items = self.list_dir(normalized_path)
        
        if not items and normalized_path != "/":
            return []
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            
            result.append(prefix + ("└── " if is_last else "├── ") + item)
            
            if item.endswith("/"): 
                next_prefix = prefix + ("    " if is_last else "│   ")
                result.extend(self.tree_traverse(
                    normalized_path + item, 
                    next_prefix, 
                    depth, 
                    current_depth + 1
                ))
        
        return result


class TerminalEmulator:
    def __init__(self, root, script_path=None, vfs_path=None):
        self.root = root
        self.vfs_path = vfs_path or os.getcwd()
        self.root.title("VFS Terminal Emulator")

        try:
            self.vfs = VFS(vfs_path)
        except Exception as e:
            self.print_output(f"Ошибка VFS: {str(e)}")
            self.root.quit()
            return 
        
        self.script_path = script_path
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_area = scrolledtext.ScrolledText(main_frame, height=20)
        self.output_area.pack(fill=tk.BOTH, expand=True)
        self.output_area.config(state=tk.DISABLED)
        
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))

        os.environ["DATE"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.environ["PWD"] = self.vfs.get_curr_path()
        os.environ["USER"] = os.getlogin() if hasattr(os, 'getlogin') else "user"
        os.environ["HOME"] = "/"
        
        self.prompt_text = self.parse_env_var("$USER@VFS")
        self.prompt_label = tk.Label(input_frame, text=self.prompt_text)
        self.prompt_label.pack(side=tk.LEFT)
        
        self.input_field = tk.Entry(input_frame, relief=tk.FLAT)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.input_field.focus()
        
        self.input_field.bind('<Return>', self.process_command)
       
        self.print_output("")
        
        if script_path:
            self.startup_script()
    
    
            
    def repl(self, match):
        name = match.group(1)
        return os.environ.get(name, '')
            
    def parse_env_var(self, command):
        pattern = r'\$(\w+)'
        return re.sub(pattern, self.repl, command)
    
    def print_output(self, text):
        self.output_area.config(state=tk.NORMAL)
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.config(state=tk.DISABLED)
        self.output_area.see(tk.END)
    
    def update_environment(self):
        os.environ["PWD"] = self.vfs.get_curr_path()

    def startup_script(self):
        if not self.script_path or not os.path.exists(self.script_path):
            self.print_output(f"Ошибка: скрипт '{self.script_path}' не найден")
            return
        
        self.print_output(f"Выполнение скрипта '{self.script_path}'")
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    self.print_output(f"{self.prompt_text}> {line}")
                    try:
                        self.command_reader(line)
                    except Exception as e:
                        self.print_output(f"Строка {line_num}: ошибка - {str(e)}")
                        continue

        except Exception as e:
            self.print_output(f'Ошибка чтения скрипта: {str(e)}')
        
        self.print_output("Завершение выполнения скрипта")
        self.print_output("")
    
    def cmd_ls(self, args):
        path = args[0] if args else "."
        
        try:
            items = self.vfs.list_dir(path)
            if not items:
                self.print_output("Директория пуста")
                return
            
            for item in items:
                self.print_output(item)
        except Exception as e:
            self.print_output(f"Ошибка ls: {str(e)}")
    
    def cmd_cd(self, args):
        if not args:
            target = "/"
        else:
            target = args[0]
        
        try:
            success = self.vfs.change_dir(target)
            if not success:
                self.print_output(f"cd: {target}: Нет такой директории")
            else:
                self.update_environment()
        except Exception as e:
            self.print_output(f"Ошибка cd: {str(e)}")
    
    def cmd_pwd(self):
        self.print_output(self.vfs.get_curr_path())
    
    def cmd_tree(self, args):
        path = args[0] if args else "."
        depth = -1
        
        if len(args) >= 2 and args[0] == "-L":
            try:
                depth = int(args[1])
                path = args[2] if len(args) > 2 else "."
            except ValueError:
                self.print_output("tree: неверный аргумент глубины")
                return
        
        try:
            tree_lines = self.vfs.tree_traverse(path, depth=depth)
            if not tree_lines:
                self.print_output(f"{path} [пустая директория]")
                return
            
            self.print_output(path)
            for line in tree_lines:
                self.print_output(line)
        except Exception as e:
            self.print_output(f"Ошибка tree: {str(e)}")
    
    def cmd_tac(self, args):
        if not args:
            self.print_output("tac: требуется указать файл")
            return
        
        file_path = args[0]
        try:
            content = self.vfs.get_file_content(file_path)
            if content is None:
                self.print_output(f"tac: {file_path}: Нет такого файла")
                return
            
            lines = content.split('\n')
            reversed_lines = reversed(lines)
            
            for line in reversed_lines:
                self.print_output(line)
        except Exception as e:
            self.print_output(f"Ошибка tac: {str(e)}")
    def cmd_script(self, args):
        if not args:
            self.print_output("Использование: script <путь_к_скрипту>")
            return
    
        script_path = args[0]
        if not os.path.exists(script_path):
            self.print_output(f"Ошибка: скрипт '{script_path}' не найден")
            return
    
        self.script_path = script_path
        self.startup_script()

    def cmd_vfs(self, args):
        if not args:
            self.print_output("Использование: vfs")
            return
    
        vfs_path = args[0]
        if not os.path.exists(vfs_path):
            self.print_output(f"Ошибка: арxив '{vfs_path}' не найден совсем")
            return
    
        try:
            self.vfs.load_from_zip(vfs_path)
            self.vfs_path = vfs_path
            self.update_environment()
            self.print_output(f"VFS успешно загружена из '{vfs_path}'")
            self.print_output(f"Текущая директория: {self.vfs.get_curr_path()}")
        except Exception as e:
            self.print_output(f"Ошибка загрузки VFS: {str(e)}")

    def command_reader(self, command):
        parsed = self.parse_env_var(command)
        cmd_parts = parsed.split()
        if not cmd_parts:
            return
        
        cmd = cmd_parts[0]
        args = cmd_parts[1:]
        
        if cmd == "exit":
            self.root.quit()
        elif cmd == "ls":
            self.cmd_ls(args)
        elif cmd == "cd":
            self.cmd_cd(args)
        elif cmd == "pwd":
            self.cmd_pwd()
        elif cmd == "echo":
            self.print_output(" ".join(args))
        elif cmd == "cls":
            self.output_area.config(state=tk.NORMAL)
            self.output_area.delete(1.0, tk.END)
            self.output_area.config(state=tk.DISABLED)
        elif cmd == "tree":
            self.cmd_tree(args)
        elif cmd == "tac":
            self.cmd_tac(args)
        elif cmd == "script":
            self.cmd_script(args)
        elif cmd == "vfs":
            self.cmd_vfs(args)
        else:
            self.print_output(f"Ошибка: неизвестная команда '{cmd}'")
    
    def process_command(self, event):
        command = self.input_field.get().strip()
        self.input_field.delete(0, tk.END)
        if not command:
            return
        
        self.print_output(f"{self.prompt_text} {command}")
        try:
            self.command_reader(command)
        except Exception as e:
            self.print_output(f"Ошибка: {str(e)}")
    
        
    
    

    
root = tk.Tk()
root.geometry("800x600") 

terminal = TerminalEmulator(root, "", "")
root.mainloop()                     
root = tk.Tk()
