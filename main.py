import sys
import argparse
import os
import tomli
import spacy
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QLabel, QTabWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QCheckBox, QFileDialog, QMessageBox,
                             QToolButton, QSizePolicy, QMenu, QMenuBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from ideadensity.idea_density_rater import rate_text
from ideadensity import depid
from ideadensity.utils.word_search_utils import export_cpidr_to_csv, export_depid_to_csv, export_cpidr_to_txt


def get_version():
    """Get version from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        if not pyproject_path.exists():
            # Try one directory up (for running from the repo root)
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
        return pyproject_data["tool"]["poetry"]["version"]
    except (FileNotFoundError, KeyError, tomli.TOMLDecodeError):
        return "0.3.1"  # Fallback to hardcoded version


def cli_main(text, speech_mode, csv_output=None, txt_output=None):
    word_count, proposition_count, density, word_list = rate_text(text, speech_mode=speech_mode)

    print(f"Density: {density}")
    print(f"Word count: {word_count}")
    print(f"Proposition count: {proposition_count}")
    print("Word list:")
    for word in word_list.items:
        if word.token:  # Skip empty tokens
            print(
                f"Token: [{word.token}], tag: [{word.tag}], is_word: [{word.is_word}], is_prop: [{word.is_proposition}], rule_number: [{word.rule_number}]"
            )
    
    # Export to CSV if requested
    if csv_output:
        try:
            export_cpidr_to_csv(word_list, csv_output)
            print(f"Token details exported to {csv_output}")
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            
    # Export to TXT if requested
    if txt_output:
        try:
            export_cpidr_to_txt(word_list, text, word_count, proposition_count, density, txt_output)
            print(f"Results exported to {txt_output} in CPIDR format")
        except Exception as e:
            print(f"Error exporting to TXT: {str(e)}")


class IdeaDensityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Idea Density Analyzer")
        self.resize(1000, 700)
        self.current_word_list = None  # Store CPIDR analysis results
        self.current_dependencies = None  # Store DEPID analysis results
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Menu bar
        menu_bar = QMenuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
        main_layout.setMenuBar(menu_bar)
        
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
        
        # Analyze button
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
        
        # Header with filters and export button
        header_layout = QHBoxLayout()
        
        # Filter options layout
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
        
        # Add filters to header
        header_layout.addLayout(filter_layout)
        
        # Export button with menu for different formats
        self.cpidr_export_btn = QToolButton()
        self.cpidr_export_btn.setToolTip("Export Results")
        self.cpidr_export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Set an icon (try system theme first, then fall back)
        icon_set = False
        
        # Try system theme icon
        if QIcon.hasThemeIcon("document-save-as") and not icon_set:
            self.cpidr_export_btn.setIcon(QIcon.fromTheme("document-save-as"))
            icon_set = True
        elif QIcon.hasThemeIcon("document-save") and not icon_set:
            self.cpidr_export_btn.setIcon(QIcon.fromTheme("document-save"))
            icon_set = True
            
        # If no system icon, use a text alternative with styling
        if not icon_set:
            self.cpidr_export_btn.setText("Export")
            self.cpidr_export_btn.setStyleSheet("""
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """)
        
        self.cpidr_export_btn.setIconSize(QSize(16, 16))
        
        # Create menu for export options
        export_menu = QMenu(self)
        export_csv_action = export_menu.addAction("Export CSV")
        export_txt_action = export_menu.addAction("Export TXT (CPIDR format)")
        
        # Connect actions to handlers
        export_csv_action.triggered.connect(self.export_cpidr_csv)
        export_txt_action.triggered.connect(self.export_cpidr_txt)
        
        # Set the menu on the button
        self.cpidr_export_btn.setMenu(export_menu)
        self.cpidr_export_btn.setEnabled(False)  # Disabled until analysis is run
        self.cpidr_export_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(self.cpidr_export_btn)
        
        # Add header to layout
        word_details_layout.addLayout(header_layout)
        
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
        
        # Analyze button
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
        
        # Header for export button
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        # Export CSV button (as an icon if possible, otherwise text)
        self.depid_export_btn = QToolButton()
        self.depid_export_btn.setToolTip("Export CSV")
        
        # Set an icon (try system theme first, then fall back)
        icon_set = False
        
        # Try system theme icon
        if QIcon.hasThemeIcon("document-save-as") and not icon_set:
            self.depid_export_btn.setIcon(QIcon.fromTheme("document-save-as"))
            icon_set = True
        elif QIcon.hasThemeIcon("document-save") and not icon_set:
            self.depid_export_btn.setIcon(QIcon.fromTheme("document-save"))
            icon_set = True
            
        # If no system icon, use a text alternative with styling
        if not icon_set:
            self.depid_export_btn.setText("CSV")
            self.depid_export_btn.setStyleSheet("""
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """)
        
        self.depid_export_btn.setIconSize(QSize(16, 16))
        
        self.depid_export_btn.clicked.connect(self.export_depid_csv)
        self.depid_export_btn.setEnabled(False)  # Disabled until analysis is run
        self.depid_export_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(self.depid_export_btn)
        
        dependency_layout.addLayout(header_layout)
        
        # Table
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
        
        # Enable export button
        self.cpidr_export_btn.setEnabled(True)
        
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
            
        # Save dependencies for CSV export
        self.current_dependencies = dependencies
        
        # Enable export button
        self.depid_export_btn.setEnabled(True)
    
    def export_cpidr_csv(self):
        """Export CPIDR token details to a CSV file"""
        if not self.current_word_list:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return
            
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", os.path.expanduser("~/cpidr_tokens.csv"), 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                export_cpidr_to_csv(self.current_word_list, file_path)
                QMessageBox.information(
                    self, "Export Successful", f"Token details exported to {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting token details: {str(e)}"
                )
    
    def export_cpidr_txt(self):
        """Export CPIDR results to a TXT file in CPIDR format"""
        if not self.current_word_list:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return
            
        # Get the original text
        text = self.text_input.toPlainText()
        
        # Get the analysis results
        word_count = sum(1 for item in self.current_word_list.items if item.is_word)
        proposition_count = sum(1 for item in self.current_word_list.items if item.is_proposition)
        
        # Calculate density
        density = 0.0
        if word_count > 0:
            density = proposition_count / word_count
            
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save TXT File", os.path.expanduser("~/cpidr_results.txt"), 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                export_cpidr_to_txt(self.current_word_list, text, word_count, 
                                    proposition_count, density, file_path)
                QMessageBox.information(
                    self, "Export Successful", f"Results exported to {file_path} in CPIDR format"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting results: {str(e)}"
                )
    
    def export_depid_csv(self):
        """Export DEPID dependency details to a CSV file"""
        if not self.current_dependencies:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return
            
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", os.path.expanduser("~/depid_dependencies.csv"), 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                export_depid_to_csv(self.current_dependencies, file_path)
                QMessageBox.information(
                    self, "Export Successful", f"Dependency details exported to {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting dependency details: {str(e)}"
                )
                
    def show_about(self):
        """Show about dialog with version information"""
        app_version = get_version()
        spacy_version = spacy.__version__
        try:
            nlp = spacy.load("en_core_web_sm")
            model_name = "en_core_web_sm"
            model_version = nlp.meta["version"]
        except:
            model_name = "en_core_web_sm"
            model_version = "not loaded"
        
        message = f"""<h3>Idea Density Analyzer</h3>
<p>Version: {app_version}</p>
<p>A tool for computing propositional idea density.</p>
<p>Using:</p>
<ul>
    <li>spaCy version: {spacy_version}</li>
    <li>Model: {model_name} (v{model_version})</li>
</ul>
<p>Homepage: <a href="https://github.com/jrrobison1/PyCPIDR">https://github.com/jrrobison1/PyCPIDR</a></p>
"""
        QMessageBox.about(self, "About Idea Density Analyzer", message)


def read_text_from_file(file_path):
    """Read text from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The contents of the file as a string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If there is an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")

if __name__ == "__main__":
    # Check if running in CLI mode
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description="Calculate idea density of a given text."
        )
        
        # Create version action
        class VersionAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                app_version = get_version()
                spacy_version = spacy.__version__
                try:
                    nlp = spacy.load("en_core_web_sm")
                    model_name = "en_core_web_sm"
                    model_version = nlp.meta["version"]
                except:
                    model_name = "en_core_web_sm"
                    model_version = "not loaded"
                
                print(f"Idea Density Analyzer v{app_version}")
                print(f"spaCy v{spacy_version}")
                print(f"Model: {model_name} v{model_version}")
                sys.exit(0)
        
        parser.add_argument("--version", action=VersionAction, nargs=0, 
                            help="Show version information and exit")
        
        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument("--text", nargs="+", help="The text to analyze")
        input_group.add_argument("--file", type=str, help="Path to a file containing text to analyze")
        parser.add_argument("--speech-mode", action="store_true", help="Enable speech mode")
        parser.add_argument("--csv", type=str, help="Export token details to a CSV file at the specified path")
        parser.add_argument("--txt", type=str, help="Export results to a TXT file in CPIDR format at the specified path")
        args = parser.parse_args()

        if args.text:
            text = " ".join(args.text)
        else:  # args.file is set
            try:
                text = read_text_from_file(args.file)
            except (FileNotFoundError, IOError) as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
                
        cli_main(text, args.speech_mode, args.csv, args.txt)
    else:
        # Start GUI
        app = QApplication(sys.argv)
        window = IdeaDensityApp()
        window.show()
        sys.exit(app.exec())
