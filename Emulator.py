import tkinter as tk
from tkinter import scrolledtext
import re
import os
class TerminalEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title("VFS")
        
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
        prompt_label.pack(side=tk.LEFT)
        
        self.input_field = tk.Entry(input_frame)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_field.focus()

        self.input_field.bind('<Return>', self.process_command)
        
    def repl(self, match):
        name = match.group(1)
        return os.environ.get(name, '')      
    def parse_env_var(self, command):
        pattern = r'\$(\w+)'
        return re.sub(pattern, self.repl, command)
    def print_output(self, text):
        self.output_area.config(state = tk.NORMAL)
        self.output_area.insert(tk.END, self.parse_env_var("$HOME")+" "+text + "\n")
        self.output_area.config(state= tk.DISABLED)
        self.output_area.see(tk.END)


    def cmd_ls(self, args):
        self.print_output(f"ls {args}")
        
    def cmd_cd(self, args):
        self.print_output(f"cd {args}")
            
    def process_command(self, event):
       command = self.input_field.get().strip()
       self.input_field.delete(0, tk.END)
       if not command:
           return
       self.print_output(f"{command}")
       try:
           parsed = self.parse_env_var(command)
           cmd_parts = parsed.split()
           if not cmd_parts:
               return
           cmd =  cmd_parts[0]
           args = cmd_parts[1:]
           if cmd == "exit":
               self.root.quit()
           #elif command[0] == '$':
               #self.print_output(parsed)
           elif cmd == "ls":
               self.cmd_ls(args)
           elif cmd == "cd":
               self.cmd_cd(args)
           else:
               self.print_output(f"Error: Unknown command '{cmd}'")
       except Exception as e:
            self.print_output(f"Error: {str(e)}")
root = tk.Tk()
terminal = TerminalEmulator(root)
root.mainloop()

