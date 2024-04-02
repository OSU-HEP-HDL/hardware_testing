import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGroupBox, QRadioButton, QPushButton, QLabel


class YesNoQuestionWidget(QWidget):
    def __init__(self, question_text):
        super().__init__()

        self.question_text = question_text

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Question label
        question_label = QLabel(self.question_text)
        layout.addWidget(question_label)

        # Radio buttons
        self.yes_button = QRadioButton("Yes")
        self.no_button = QRadioButton("No")

        self.yes_button.setChecked(False)
        self.no_button.setChecked(False)

        layout.addWidget(self.yes_button)
        layout.addWidget(self.no_button)

        # Add layout to group box
        group_box = QGroupBox()
        group_box.setLayout(layout)

        # Add group box to main layout
        self.setLayout(layout)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Yes/No Questions")

        # Layout
        layout = QVBoxLayout()

        # Add yes/no question widgets
        self.question1 = YesNoQuestionWidget("Do you like Python?")
        self.question2 = YesNoQuestionWidget("Is the sky blue?")
        self.question3 = YesNoQuestionWidget("Have you ever been to space?")

        layout.addWidget(self.question1)
        layout.addWidget(self.question2)
        layout.addWidget(self.question3)

        # Submit button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_answers)
        layout.addWidget(submit_button)

        # Set the main layout of the window
        self.setLayout(layout)

    def submit_answers(self):
        # Example function to get the answers from the radio buttons
        answer1 = "Yes" if self.question1.yes_button.isChecked() else "No"
        answer2 = "Yes" if self.question2.yes_button.isChecked() else "No"
        answer3 = "Yes" if self.question3.yes_button.isChecked() else "No"

        print("Answer 1:", answer1)
        print("Answer 2:", answer2)
        print("Answer 3:", answer3)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
