if __name__ == '__main__' and __package__ is None:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = 'OpenAI_API_Wrapper'

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import traceback
from .model_manager import get_available_models, update_model_config
from .openai_wrapper import call_openai_method
import openai

import os
import json

CONFIG_CACHE = "gui_test_config.json"

class OpenAITestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI API Tester")

        self.api_key = tk.StringVar()
        self.prompt = tk.StringVar()
        self.model = tk.StringVar()
        self.output_path = tk.StringVar()

        self.models = []
        self._load_config()

        self._build_ui()
        self._setup_autosave()

    def _build_ui(self):
        ttk.Label(self.root, text="API Key:").grid(row=0, column=0, sticky='w')
        ttk.Entry(self.root, textvariable=self.api_key, width=50).grid(row=0, column=1, sticky='ew')
        ttk.Button(self.root, text="Load Models", command=self._load_models).grid(row=0, column=2)

        ttk.Label(self.root, text="Model:").grid(row=1, column=0, sticky='w')
        self.model_combo = ttk.Combobox(self.root, values=self.models, textvariable=self.model)
        self.model_combo.grid(row=1, column=1, columnspan=2, sticky='ew')

        ttk.Label(self.root, text="Prompt:").grid(row=2, column=0, sticky='nw')
        self.prompt_entry = tk.Text(self.root, height=5, width=60)
        self.prompt_entry.grid(row=2, column=1, columnspan=2, sticky='ew')

        ttk.Label(self.root, text="Output File:").grid(row=3, column=0, sticky='w')
        ttk.Entry(self.root, textvariable=self.output_path, width=40).grid(row=3, column=1, sticky='ew')
        ttk.Button(self.root, text="Browse", command=self._browse_file).grid(row=3, column=2)

        ttk.Button(self.root, text="Run Test", command=self._run_test).grid(row=4, column=0, pady=5)
        ttk.Button(self.root, text="Clear All", command=self._clear_all).grid(row=4, column=1, pady=5)
        ttk.Label(self.root, text="").grid(row=4, column=2)

        self.log_box = tk.Text(self.root, height=15, width=100)
        self.log_box.grid(row=5, column=0, columnspan=3, sticky='nsew')

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(5, weight=1)

    def _browse_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            self.output_path.set(file_path)

    def _load_models(self):
        try:
            key = self.api_key.get().strip()
            self.models = get_available_models() if not key else update_model_config(api_key=key)
            self.model_combo['values'] = self.models
            self._log(f"Loaded {len(self.models)} models from config.")
        except Exception as e:
            self._log("\n=== ERROR LOADING MODELS ===\n" + traceback.format_exc())

    def _save_config(self):
        data = {
            "prompt": self.prompt_entry.get("1.0", tk.END).strip(),
            "model": self.model.get(),
            "output_path": self.output_path.get()
        }
        with open(CONFIG_CACHE, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def _load_config(self):
        if os.path.exists(CONFIG_CACHE):
            try:
                with open(CONFIG_CACHE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.prompt_entry.insert("1.0", data.get("prompt", ""))
                self.model.set(data.get("model", ""))
                self.output_path.set(data.get("output_path", ""))
            except Exception:
                pass

    def _clear_all(self):
        self.prompt_entry.delete("1.0", tk.END)
        self.model.set("")
        self.output_path.set("")
        self._save_config()

    def _run_test(self):
        threading.Thread(target=self._execute_test, daemon=True).start()

    def _execute_test(self):
        self.log_box.delete('1.0', tk.END)
        key = self.api_key.get().strip()
        model = self.model.get().strip()
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        output_path = self.output_path.get().strip()

        if not key or not model or not prompt:
            self._log("ERROR: Missing required fields.")
            return

        try:
            self._save_config()
            response = call_openai_method(
                "chat.completions.create",
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_key=key
            )
            content = response.choices[0].message.content
            self._log("\n=== MODEL RESPONSE ===\n" + content)

            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._log(f"\nSaved response to {output_path}")

        except Exception as e:
            err_trace = traceback.format_exc()
            self._log("\n=== ERROR ===\n" + err_trace)

    def _setup_autosave(self):
        self.prompt_entry.bind("<KeyRelease>", lambda e: self._save_config())
        self.model.trace_add("write", lambda *args: self._save_config())
        self.output_path.trace_add("write", lambda *args: self._save_config())

    def _log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


if __name__ == '__main__':
    root = tk.Tk()
    app = OpenAITestGUI(root)
    root.mainloop()
