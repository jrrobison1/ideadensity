import sys
import argparse
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QTabWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox
from PyQt6.QtCore import Qt
from ideadensity.idea_density_rater import rate_text
from ideadensity import depid


def cli_main(text, speech_mode):
    _, _, density, word_list = rate_text(text, speech_mode=speech_mode)

    print(f"Density: {density}")
    print("Word list:")
    for word in word_list.items:
        print(
            f"Token: [{word.token}], tag: [{word.tag}], is_word: [{word.is_word}], is_prop: [{word.is_proposition}], rule_number: [{word.rule_number}]"
        )


class IdeaDensityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Idea Density Analyzer")
        self.resize(1000, 700)
        self.current_word_list = None
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Input area
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to analyze...")
        main_layout.addWidget(QLabel("Input Text:"))
        main_layout.addWidget(self.text_input)
        
        # Tabs for CPIDR and DEPID
        tab_widget = QTabWidget()
        cpidr_tab = QWidget()
        depid_tab = QWidget()
        
        tab_widget.addTab(cpidr_tab, "CPIDR")
        tab_widget.addTab(depid_tab, "DEPID")
        
        # CPIDR Tab
        cpidr_layout = QVBoxLayout()
        
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout()
        self.speech_mode_checkbox = QCheckBox("Speech Mode (filter fillers)")
        options_layout.addWidget(self.speech_mode_checkbox)
        options_group.setLayout(options_layout)
        cpidr_layout.addWidget(options_group)
        
        self.cpidr_analyze_btn = QPushButton("Analyze with CPIDR")
        self.cpidr_analyze_btn.clicked.connect(self.analyze_cpidr)
        cpidr_layout.addWidget(self.cpidr_analyze_btn)
        
        results_layout = QHBoxLayout()
        
        # Results section
        cpidr_results_group = QGroupBox("Summary")
        cpidr_results_layout = QVBoxLayout()
        self.cpidr_results = QLabel("Results will appear here")
        self.cpidr_results.setAlignment(Qt.AlignmentFlag.AlignTop)
        cpidr_results_layout.addWidget(self.cpidr_results)
        cpidr_results_group.setLayout(cpidr_results_layout)
        results_layout.addWidget(cpidr_results_group, 1)
        
        # Token details table with filters
        word_details_group = QGroupBox("Token Details")
        word_details_layout = QVBoxLayout()
        
        # Filter options
        filter_layout = QHBoxLayout()
        self.show_all_tokens_checkbox = QCheckBox("Show All Tokens")
        self.show_all_tokens_checkbox.setChecked(True)
        self.show_all_tokens_checkbox.stateChanged.connect(self.update_token_filters)
        
        self.show_only_words_checkbox = QCheckBox("Only Words")
        self.show_only_words_checkbox.stateChanged.connect(self.update_token_filters)
        
        self.show_only_props_checkbox = QCheckBox("Only Propositions")
        self.show_only_props_checkbox.stateChanged.connect(self.update_token_filters)
        
        filter_layout.addWidget(self.show_all_tokens_checkbox)
        filter_layout.addWidget(self.show_only_words_checkbox)
        filter_layout.addWidget(self.show_only_props_checkbox)
        filter_layout.addStretch()
        
        word_details_layout.addLayout(filter_layout)
        
        # Token table
        self.word_table = QTableWidget(0, 4)
        self.word_table.setHorizontalHeaderLabels(["Token", "POS Tag", "Is Proposition", "Rule"])
        self.word_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        word_details_layout.addWidget(self.word_table)
        
        word_details_group.setLayout(word_details_layout)
        results_layout.addWidget(word_details_group, 2)
        
        cpidr_layout.addLayout(results_layout)
        cpidr_tab.setLayout(cpidr_layout)
        
        # DEPID Tab
        depid_layout = QVBoxLayout()
        
        depid_options_group = QGroupBox("Options")
        depid_options_layout = QHBoxLayout()
        self.depid_r_checkbox = QCheckBox("Use DEPID-R (count distinct dependencies)")
        depid_options_layout.addWidget(self.depid_r_checkbox)
        depid_options_group.setLayout(depid_options_layout)
        depid_layout.addWidget(depid_options_group)
        
        self.depid_analyze_btn = QPushButton("Analyze with DEPID")
        self.depid_analyze_btn.clicked.connect(self.analyze_depid)
        depid_layout.addWidget(self.depid_analyze_btn)
        
        depid_results_layout = QHBoxLayout()
        
        # DEPID Results
        depid_results_group = QGroupBox("Summary")
        depid_summary_layout = QVBoxLayout()
        self.depid_results = QLabel("Results will appear here")
        self.depid_results.setAlignment(Qt.AlignmentFlag.AlignTop)
        depid_summary_layout.addWidget(self.depid_results)
        depid_results_group.setLayout(depid_summary_layout)
        depid_results_layout.addWidget(depid_results_group, 1)
        
        # Dependency details
        dependency_group = QGroupBox("Dependencies")
        dependency_layout = QVBoxLayout()
        self.dependency_table = QTableWidget(0, 3)
        self.dependency_table.setHorizontalHeaderLabels(["Token", "Dependency", "Head"])
        self.dependency_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        dependency_layout.addWidget(self.dependency_table)
        dependency_group.setLayout(dependency_layout)
        depid_results_layout.addWidget(dependency_group, 2)
        
        depid_layout.addLayout(depid_results_layout)
        depid_tab.setLayout(depid_layout)
        
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        
    def analyze_cpidr(self):
        text = self.text_input.toPlainText()
        if not text:
            self.cpidr_results.setText("Please enter some text to analyze.")
            return
        
        speech_mode = self.speech_mode_checkbox.isChecked()
        word_count, proposition_count, density, word_list = rate_text(text, speech_mode=speech_mode)
        
        # Display summary results
        result_text = (f"<b>CPIDR Analysis</b><br>"
                       f"Word count: {word_count}<br>"
                       f"Proposition count: {proposition_count}<br>"
                       f"Idea density: {density:.3f}")
        self.cpidr_results.setText(result_text)
        
        # Save word list for filtering
        self.current_word_list = word_list
        self.update_token_table()
        
    def update_token_filters(self):
        """Update token table based on filter checkboxes"""
        # Ensure mutual exclusivity between filter options
        if self.sender() == self.show_all_tokens_checkbox and self.show_all_tokens_checkbox.isChecked():
            self.show_only_words_checkbox.setChecked(False)
            self.show_only_props_checkbox.setChecked(False)
        elif self.sender() in [self.show_only_words_checkbox, self.show_only_props_checkbox]:
            if self.sender().isChecked():
                self.show_all_tokens_checkbox.setChecked(False)
                
        # If nothing is checked, default to "Show All"
        if not any([self.show_all_tokens_checkbox.isChecked(), 
                   self.show_only_words_checkbox.isChecked(), 
                   self.show_only_props_checkbox.isChecked()]):
            self.show_all_tokens_checkbox.setChecked(True)
            
        self.update_token_table()
        
    def update_token_table(self):
        """Update the token table based on current filters"""
        if not self.current_word_list:
            return
            
        self.word_table.setRowCount(0)
        row = 0
        
        for word in self.current_word_list.items:
            if not word.token:  # Skip empty tokens
                continue
                
            # Apply filters
            if self.show_all_tokens_checkbox.isChecked():
                show_token = True
            else:
                show_word = self.show_only_words_checkbox.isChecked() and word.is_word
                show_prop = self.show_only_props_checkbox.isChecked() and word.is_proposition
                show_token = show_word or show_prop
                
            if show_token:
                self.word_table.insertRow(row)
                self.word_table.setItem(row, 0, QTableWidgetItem(word.token))
                self.word_table.setItem(row, 1, QTableWidgetItem(word.tag))
                self.word_table.setItem(row, 2, QTableWidgetItem("Yes" if word.is_proposition else "No"))
                self.word_table.setItem(row, 3, QTableWidgetItem(str(word.rule_number) if word.rule_number is not None else ""))
                row += 1
                
    def analyze_depid(self):
        text = self.text_input.toPlainText()
        if not text:
            self.depid_results.setText("Please enter some text to analyze.")
            return
        
        is_depid_r = self.depid_r_checkbox.isChecked()
        density, word_count, dependencies = depid(text, is_depid_r=is_depid_r)
        
        # Display summary results
        method_name = "DEPID-R" if is_depid_r else "DEPID"
        result_text = (f"<b>{method_name} Analysis</b><br>"
                       f"Word count: {word_count}<br>"
                       f"Dependency count: {len(dependencies)}<br>"
                       f"Idea density: {density:.3f}")
        self.depid_results.setText(result_text)
        
        # Display dependency details in table
        self.dependency_table.setRowCount(0)
        for i, dep in enumerate(dependencies):
            self.dependency_table.insertRow(i)
            self.dependency_table.setItem(i, 0, QTableWidgetItem(str(dep[0])))
            self.dependency_table.setItem(i, 1, QTableWidgetItem(str(dep[1])))
            self.dependency_table.setItem(i, 2, QTableWidgetItem(str(dep[2])))


if __name__ == "__main__":
    # Check if running in CLI mode
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description="Calculate idea density of a given text."
        )
        parser.add_argument("text", nargs="+", help="The text to analyze")
        parser.add_argument("--speech-mode", action="store_true", help="Enable speech mode")
        args = parser.parse_args()

        text = " ".join(args.text)
        cli_main(text, args.speech_mode)
    else:
        # Start GUI
        app = QApplication(sys.argv)
        window = IdeaDensityApp()
        window.show()
        sys.exit(app.exec())
