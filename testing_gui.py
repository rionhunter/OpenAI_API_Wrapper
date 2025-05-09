import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import traceback
import json
from model_manager import get_available_models
from openai_wrapper import call_openai_method
import openai

class OpenAITestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI API Tester")

        self.api_key = tk.StringVar()
        self.prompt = tk.StringVar()
        self.model = tk.StringVar()
        self.output_path = tk.StringVar()

        self.models = []

        self._build_ui()

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

        ttk.Button(self.root, text="Run Test", command=self._run_test).grid(row=4, column=0, columnspan=3, pady=5)

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
            from model_manager import update_model_config
            key = self.api_key.get().strip()
            self.models = update_model_config(api_key=key)
            self.model_combo['values'] = self.models
            self._log(f"Loaded {len(self.models)} models from config.")
        except Exception as e:
            self._log("\n=== ERROR LOADING MODELS ===\n" + traceback.format_exc())

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

    def _log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


if __name__ == '__main__':
    root = tk.Tk()
    app = OpenAITestGUI(root)
    root.mainloop()
