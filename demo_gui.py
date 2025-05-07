import sys
from PyQt5 import QtWidgets

class AIToolboxApp(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Toolbox — GPT / DALL·E / Whisper")

        self.gpt_tab = self.init_gpt_tab()
        self.dalle_tab = self.init_dalle_tab()
        self.whisper_tab = self.init_whisper_tab()

        self.addTab(self.gpt_tab, "GPT")
        self.addTab(self.dalle_tab, "DALL·E")
        self.addTab(self.whisper_tab, "Whisper")

    def init_gpt_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.gpt_input = QtWidgets.QTextEdit()
        self.gpt_output = QtWidgets.QTextEdit()
        self.gpt_output.setReadOnly(True)
        gpt_submit = QtWidgets.QPushButton("Send to GPT")
        gpt_export = QtWidgets.QPushButton("Export Response")

        gpt_submit.clicked.connect(self.fake_gpt_call)
        gpt_export.clicked.connect(lambda: self.export_text(self.gpt_output.toPlainText()))

        layout.addWidget(QtWidgets.QLabel("Prompt:"))
        layout.addWidget(self.gpt_input)
        layout.addWidget(gpt_submit)
        layout.addWidget(QtWidgets.QLabel("Response:"))
        layout.addWidget(self.gpt_output)
        layout.addWidget(gpt_export)

        tab.setLayout(layout)
        return tab

    def init_dalle_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.dalle_prompt = QtWidgets.QLineEdit()
        dalle_submit = QtWidgets.QPushButton("Generate Image")
        self.dalle_image_label = QtWidgets.QLabel("[Image will appear here]")
        dalle_export = QtWidgets.QPushButton("Export Image")

        dalle_submit.clicked.connect(lambda: self.dalle_image_label.setText("[Image generated]") )
        dalle_export.clicked.connect(lambda: print("Image export clicked"))

        layout.addWidget(QtWidgets.QLabel("Prompt:"))
        layout.addWidget(self.dalle_prompt)
        layout.addWidget(dalle_submit)
        layout.addWidget(self.dalle_image_label)
        layout.addWidget(dalle_export)

        tab.setLayout(layout)
        return tab

    def init_whisper_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.whisper_file_label = QtWidgets.QLabel("No file selected")
        whisper_upload = QtWidgets.QPushButton("Upload Audio")
        whisper_transcribe = QtWidgets.QPushButton("Transcribe")
        self.whisper_output = QtWidgets.QTextEdit()
        self.whisper_output.setReadOnly(True)
        whisper_export = QtWidgets.QPushButton("Export Transcript")

        whisper_upload.clicked.connect(lambda: self.whisper_file_label.setText("[Audio file uploaded]"))
        whisper_transcribe.clicked.connect(lambda: self.whisper_output.setText("[Transcribed text]"))
        whisper_export.clicked.connect(lambda: self.export_text(self.whisper_output.toPlainText()))

        layout.addWidget(self.whisper_file_label)
        layout.addWidget(whisper_upload)
        layout.addWidget(whisper_transcribe)
        layout.addWidget(self.whisper_output)
        layout.addWidget(whisper_export)

        tab.setLayout(layout)
        return tab

    def fake_gpt_call(self):
        prompt = self.gpt_input.toPlainText()
        self.gpt_output.setText(f"[Response to]:\n{prompt}")

    def export_text(self, content):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Output", "output.txt", "Text Files (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AIToolboxApp()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
