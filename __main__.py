import sys

from .entrypoint import main as cli_main

if __name__ == "__main__":
    # If called with arguments, go to CLI handler
    if len(sys.argv) > 1:
        cli_main()
    else:
        try:
            from .testing_gui import OpenAITestGUI
            import tkinter as tk

            root = tk.Tk()
            app = OpenAITestGUI(root)
            root.mainloop()
        except Exception as e:
            import traceback
            print("\n=== GUI LAUNCH FAILED ===")
            print(traceback.format_exc())
