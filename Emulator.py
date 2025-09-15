import tkinter as tk
from tkinter import scrolledtext
import re
from datetime import datetime
import os
class TerminalEmulator:
    def __init__(self, root, script_path=None):
        self.root = root
        self.vfs_path = os.getcwd()
        self.root.title("VFS")
        self.script_path = script_path
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_area = scrolledtext.ScrolledText(main_frame)
        self.output_area.pack(fill=tk.BOTH, expand=True)
        self.output_area.config(state=tk.DISABLED)
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 0))

        prompt_label = tk.Label(
            input_frame, 
            text= self.parse_env_var("$HOME")+">"
        )
        os.environ["DATE"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.environ["PWD"]=self.vfs_path
        os.environ["USER"]=os.getlogin()
        prompt_label.pack(side=tk.LEFT)
        self.startup_script()
        self.input_field = tk.Entry(input_frame, relief=tk.FLAT)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_field.focus()
        self.print_debug_info()
        self.input_field.bind('<Return>', self.process_command)


    def print_debug_info(self):
        self.print_output("TERMINAL DEBUG INFO")
        self.print_output(f"VFS Path: {self.parse_env_var("$HOME")}")
        self.print_output(f"Prompt: '{self.parse_env_var("$HOME")}>'")
        self.print_output(f"Script: {self.script_path}")
        self.print_output("")
        
    def repl(self, match):
        name = match.group(1)
        return os.environ.get(name, '')
            
    def parse_env_var(self, command):
        pattern = r'\$(\w+)'
        return re.sub(pattern, self.repl, command)
    
    def print_output(self, text):
        self.output_area.config(state = tk.NORMAL)
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.config(state= tk.DISABLED)
        self.output_area.see(tk.END)

    def startup_script(self):
        if not os.path.exists(self.script_path):
            self.print_output(f"Ошибка: скрипт '{self.script_path}' не найден")
            return
        self.print_output(f"Выполнение скрипта'{self.script_path}'")
        self.print_output("")
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    line  = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self.print_output(f"{self.parse_env_var("$HOME")}> {line}")
                    try:
                        self.command_reader(line)
                    except Exception as e:
                        self.print_output(f"Строка {line_num}: ошибка - {str(e)}")
                        continue

        except Exception as e:
            self.print_output(f'Ошибка чтения скрипта: {str(e)}')
        self.print_output("")
        
    def cmd_ls(self, args):
        self.print_output(f"ls {args}")
        
    def cmd_cd(self, args):
        self.print_output(f"cd {args}")
        
    def cmd_pwd(self):
        self.print_output(f"{self.vfs_path}")
        
    def command_reader(self, command):
         parsed = self.parse_env_var(command)
         cmd_parts = parsed.split()
         if not cmd_parts:
             return
         cmd =  cmd_parts[0]
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
         else:
             self.print_output(f"Ошибка: неизвестная команда '{cmd}'")
             
    def process_command(self, event):
       command = self.input_field.get().strip()
       self.input_field.delete(0, tk.END)
       if not command:
           return
       self.print_output(f"{command}")
       try:
          self.command_reader(command)
       except Exception as e:
            self.print_output(f"Error: {str(e)}")

root = tk.Tk()
script = "script_2.0.txt"
terminal = TerminalEmulator(root, script)
root.mainloop()

