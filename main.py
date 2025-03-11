import sys
import argparse
import os
import tomli
import spacy
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QLabel, QTabWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QCheckBox, QFileDialog, QMessageBox,
                             QToolButton, QSizePolicy, QMenu, QMenuBar, QRadioButton,
                             QStackedWidget, QScrollArea, QFrame, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from ideadensity.idea_density_rater import rate_text
from ideadensity import depid
from ideadensity.utils.export_utils import export_cpidr_to_csv, export_depid_to_csv, export_cpidr_to_txt, export_cpidr_multiple_files_to_txt
from ideadensity.utils.version_utils import get_spacy_version_info


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


def cli_main(text, speech_mode, csv_output=None, txt_output=None, filename=None):
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
            export_cpidr_to_txt(word_list, text, word_count, proposition_count, density, txt_output, filename)
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
        self.file_word_lists = []  # Store per-file CPIDR analysis results
        self.file_dependencies = []  # Store per-file DEPID analysis results
        self.file_names = []  # Store names of processed files
        self.selected_files = []  # Store selected file paths
        self.input_mode = "text"  # Default input mode: "text" or "file"
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Menu bar
        menu_bar = QMenuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
        main_layout.setMenuBar(menu_bar)
        
        # Input mode selection
        input_mode_layout = QHBoxLayout()
        input_mode_layout.addWidget(QLabel("Input Mode:"))
        
        self.text_mode_radio = QRadioButton("Text")
        self.text_mode_radio.setChecked(True)
        self.text_mode_radio.toggled.connect(self.toggle_input_mode)
        
        self.file_mode_radio = QRadioButton("File")
        self.file_mode_radio.toggled.connect(self.toggle_input_mode)
        
        input_mode_layout.addWidget(self.text_mode_radio)
        input_mode_layout.addWidget(self.file_mode_radio)
        input_mode_layout.addStretch()
        
        main_layout.addLayout(input_mode_layout)
        
        # Input stacked widget (contains both text and file input)
        self.input_stack = QStackedWidget()
        main_layout.addWidget(self.input_stack)
        
        # Text input widget
        text_input_widget = QWidget()
        text_input_layout = QVBoxLayout(text_input_widget)
        text_input_layout.addWidget(QLabel("Input Text:"))
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to analyze...")
        text_input_layout.addWidget(self.text_input)
        
        self.input_stack.addWidget(text_input_widget)
        
        # File input widget
        file_input_widget = QWidget()
        file_input_layout = QVBoxLayout(file_input_widget)
        
        file_header_layout = QHBoxLayout()
        file_header_layout.addWidget(QLabel("Input Files:"))
        
        self.select_file_button = QPushButton("Select Files")
        self.select_file_button.clicked.connect(self.select_files)
        file_header_layout.addWidget(self.select_file_button)
        
        clear_files_button = QPushButton("Clear Files")
        clear_files_button.clicked.connect(self.clear_files)
        file_header_layout.addWidget(clear_files_button)
        
        file_header_layout.addStretch()
        file_input_layout.addLayout(file_header_layout)
        
        # Scroll area for file list
        file_scroll = QScrollArea()
        file_scroll.setWidgetResizable(True)
        file_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.file_list_widget = QWidget()
        self.file_list_layout = QGridLayout(self.file_list_widget)
        self.file_list_layout.setColumnMinimumWidth(0, 150)  # Fixed width for each column
        self.file_list_layout.setColumnMinimumWidth(1, 150)
        self.file_list_layout.setColumnMinimumWidth(2, 150)
        self.file_list_layout.setColumnMinimumWidth(3, 150)
        self.file_list_layout.setColumnMinimumWidth(4, 150)
        self.file_list_layout.setHorizontalSpacing(10)
        self.file_list_layout.setVerticalSpacing(10)
        self.file_list_layout.setContentsMargins(10, 10, 10, 10)
        self.file_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        file_scroll.setWidget(self.file_list_widget)
        
        file_input_layout.addWidget(file_scroll)
        
        self.input_stack.addWidget(file_input_widget)
        
        # Set default to text input
        self.input_stack.setCurrentIndex(0)
        
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
        
        # File filter combobox
        self.cpidr_file_combo = self.setup_file_filter(cpidr_layout)
        
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
        
        # Add file indication label to show which file's tokens are displayed
        self.token_file_label = QLabel("")
        self.token_file_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        header_layout.addWidget(self.token_file_label)
        
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
        
        # File filter combobox
        self.depid_file_combo = self.setup_file_filter(depid_layout)
        
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
        
        # Add file indication label for dependencies
        self.dependency_file_label = QLabel("")
        self.dependency_file_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        header_layout.addWidget(self.dependency_file_label)
        
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
        text, file_info = self.get_input_text()
        if not text:
            error_msg = "Please enter some text to analyze." if self.input_mode == "text" else "Please select files to analyze."
            self.cpidr_results.setText(error_msg)
            return
        
        # Show processing indicator for large files
        if len(text) > 10000:
            self.cpidr_results.setText("Processing text, please wait...")
            QApplication.processEvents()  # Update UI

        speech_mode = self.speech_mode_checkbox.isChecked()
        word_count, proposition_count, density, word_list = rate_text(text, speech_mode=speech_mode)
        
        # Display summary results
        result_text = (f"<b>CPIDR Analysis</b><br>"
                       f"Word count: {word_count}<br>"
                       f"Proposition count: {proposition_count}<br>"
                       f"Idea density: {density:.3f}")
        
        # Reset file data
        self.file_word_lists = []
        self.file_names = []
        
        # Update file filter dropdown
        self.cpidr_file_combo.clear()
        self.cpidr_file_combo.addItem("All files (combined)")
        
        # Add per-file breakdown if in file mode
        if self.input_mode == "file" and file_info:
            result_text += "<br><br><b>Per-file breakdown:</b>"
            
            # Process each file separately
            for file_data in file_info:
                file_path = file_data["path"]
                file_text = file_data["text"]
                file_name = os.path.basename(file_path)
                
                # Process this individual file
                file_word_count, file_prop_count, file_density, file_word_list = rate_text(
                    file_text, speech_mode=speech_mode
                )
                
                # Store file results for table filtering
                self.file_word_lists.append(file_word_list)
                self.file_names.append(file_name)
                
                # Add to dropdown
                self.cpidr_file_combo.addItem(file_name)
                
                # Add to summary text
                result_text += f"<br><br><b>{file_name}</b><br>"
                result_text += f"Word count: {file_word_count}<br>"
                result_text += f"Proposition count: {file_prop_count}<br>"
                result_text += f"Idea density: {file_density:.3f}"
            
            # Enable file filter only if we have multiple files
            self.cpidr_file_combo.setEnabled(len(file_info) > 0)
        else:
            # Disable file filter for text mode
            self.cpidr_file_combo.setEnabled(False)
        
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
        """Update the token table based on current filters and file selection"""
        if not self.current_word_list and not self.file_word_lists:
            return
            
        self.word_table.setRowCount(0)
        row = 0
        
        # Determine which word list to display
        selected_index = self.cpidr_file_combo.currentIndex()
        
        # If "All files (combined)" or in text mode
        if selected_index == 0 or not self.file_word_lists:
            word_list = self.current_word_list
            self.token_file_label.setText("Showing: All files (combined)")
        else:
            # Adjust for 0-based index and the "All files" item
            file_index = selected_index - 1
            if file_index < len(self.file_word_lists):
                word_list = self.file_word_lists[file_index]
                self.token_file_label.setText(f"Showing: {self.file_names[file_index]}")
            else:
                word_list = self.current_word_list
                self.token_file_label.setText("Showing: All files (combined)")
        
        if not word_list:
            return
            
        # Update table with selected word list
        for word in word_list.items:
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
        text, file_info = self.get_input_text()
        if not text:
            error_msg = "Please enter some text to analyze." if self.input_mode == "text" else "Please select files to analyze."
            self.depid_results.setText(error_msg)
            return
        
        # Show processing indicator for large files
        if len(text) > 10000:
            self.depid_results.setText("Processing text, please wait...")
            QApplication.processEvents()  # Update UI
        
        is_depid_r = self.depid_r_checkbox.isChecked()
        density, word_count, dependencies = depid(text, is_depid_r=is_depid_r)
        
        # Display summary results
        method_name = "DEPID-R" if is_depid_r else "DEPID"
        result_text = (f"<b>{method_name} Analysis</b><br>"
                       f"Word count: {word_count}<br>"
                       f"Dependency count: {len(dependencies)}<br>"
                       f"Idea density: {density:.3f}")
        
        # Reset file data
        self.file_dependencies = []
        if not hasattr(self, 'file_names') or self.input_mode == "file":
            self.file_names = []
        
        # Update file filter dropdown
        self.depid_file_combo.clear()
        self.depid_file_combo.addItem("All files (combined)")
        
        # Add per-file breakdown if in file mode
        if self.input_mode == "file" and file_info:
            result_text += "<br><br><b>Per-file breakdown:</b>"
            
            # Process each file separately
            for file_data in file_info:
                file_path = file_data["path"]
                file_text = file_data["text"]
                file_name = os.path.basename(file_path)
                
                # Process this individual file
                file_density, file_word_count, file_dependencies = depid(file_text, is_depid_r=is_depid_r)
                
                # Store file results for table filtering
                self.file_dependencies.append(file_dependencies)
                if not self.file_names or len(self.file_names) <= len(self.file_dependencies) - 1:
                    self.file_names.append(file_name)
                
                # Add to dropdown
                self.depid_file_combo.addItem(file_name)
                
                # Add to summary text
                result_text += f"<br><br><b>{file_name}</b><br>"
                result_text += f"Word count: {file_word_count}<br>"
                result_text += f"Dependency count: {len(file_dependencies)}<br>"
                result_text += f"Idea density: {file_density:.3f}"
            
            # Enable file filter only if we have multiple files
            self.depid_file_combo.setEnabled(len(file_info) > 0)
        else:
            # Disable file filter for text mode
            self.depid_file_combo.setEnabled(False)
        
        self.depid_results.setText(result_text)
        
        # Display dependency details in table
        self.current_dependencies = dependencies
        self.update_dependency_table()
        
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
        text, file_info = self.get_input_text()
        
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save TXT File", os.path.expanduser("~/cpidr_results.txt"), 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                # Check if we're in file mode and have multiple files
                if (self.input_mode == "file" and file_info and 
                    len(self.file_names) > 0 and len(self.file_word_lists) > 0):
                    
                    # All files combined mode (index 0)
                    if self.cpidr_file_combo.currentIndex() == 0:
                        # Export all files separately in one document
                        export_cpidr_multiple_files_to_txt(
                            self.file_word_lists, 
                            self.file_names, 
                            file_path
                        )
                    else:
                        # Individual file selected
                        selected_index = self.cpidr_file_combo.currentIndex() - 1  # -1 to account for "All files" item
                        if 0 <= selected_index < len(self.file_names):
                            word_list = self.file_word_lists[selected_index]
                            filename = self.file_names[selected_index]
                            
                            # Calculate stats for the selected file
                            word_count = sum(1 for item in word_list.items if item.is_word)
                            proposition_count = sum(1 for item in word_list.items if item.is_proposition)
                            density = 0.0
                            if word_count > 0:
                                density = proposition_count / word_count
                                
                            # Export the selected file
                            export_cpidr_to_txt(
                                word_list,
                                "",  # Text is not needed since we have the filename
                                word_count,
                                proposition_count, 
                                density, 
                                file_path, 
                                filename
                            )
                else:
                    # Text mode or single file analysis (use current_word_list)
                    # Get the analysis results
                    word_count = sum(1 for item in self.current_word_list.items if item.is_word)
                    proposition_count = sum(1 for item in self.current_word_list.items if item.is_proposition)
                    
                    # Calculate density
                    density = 0.0
                    if word_count > 0:
                        density = proposition_count / word_count
                        
                    # For text mode, we don't have a filename
                    filename = None
                    
                    export_cpidr_to_txt(
                        self.current_word_list, 
                        text, 
                        word_count, 
                        proposition_count, 
                        density, 
                        file_path, 
                        filename
                    )
                
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
                
    def toggle_input_mode(self, checked):
        """Toggle between text and file input modes"""
        if not checked:  # Only respond to the radio button that was checked
            return
            
        if self.sender() == self.text_mode_radio:
            self.input_mode = "text"
            self.input_stack.setCurrentIndex(0)
        else:  # File mode
            self.input_mode = "file"
            self.input_stack.setCurrentIndex(1)
    
    def select_files(self):
        """Open file dialog to select input files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Text Files", os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not files:
            return
            
        # Add files to the list
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                
        # Update file display
        self.update_file_display()
    
    def clear_files(self):
        """Clear all selected files"""
        self.selected_files = []
        self.update_file_display()
    
    def update_file_display(self):
        """Update the file list display"""
        # Clear current display
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add files to grid layout
        for i, file_path in enumerate(self.selected_files):
            row, col = divmod(i, 5)  # 5 files per row
            
            # Create file item widget with fixed size
            file_item = QWidget()
            file_item.setFixedWidth(130)  # Fixed width for each file item
            
            # Use absolute positioning for the removal button
            file_item.setLayout(QVBoxLayout())
            file_item.layout().setContentsMargins(3, 3, 3, 3)
            file_item.layout().setSpacing(3)  # Reduce space between elements
            
            # Create a container widget for icon and X button
            icon_container = QWidget()
            icon_container.setFixedHeight(40)  # Height for icon area
            icon_container_layout = QHBoxLayout(icon_container)
            icon_container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Icon frame to position the icon and the X button
            icon_frame = QFrame()
            icon_frame.setLayout(QGridLayout())
            icon_frame.layout().setContentsMargins(0, 0, 0, 0)
            icon_frame.layout().setSpacing(0)
            
            # File icon or placeholder
            icon_label = QLabel()
            # Try to use system icon for text files
            if QIcon.hasThemeIcon("text-x-generic"):
                pixmap = QIcon.fromTheme("text-x-generic").pixmap(32, 32)
                icon_label.setPixmap(pixmap)
            else:
                # Simple placeholder if no system icon
                icon_label.setText("📄")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet("font-size: 20px;")
            
            # Add icon to the frame
            icon_frame.layout().addWidget(icon_label, 0, 0, Qt.AlignmentFlag.AlignCenter)
            
            # Remove button - in the upper right corner
            remove_btn = QPushButton("×")
            remove_btn.setToolTip("Remove file")
            remove_btn.setProperty("file_index", i)
            remove_btn.clicked.connect(self.remove_file)
            remove_btn.setFixedWidth(18)
            remove_btn.setFixedHeight(18)
            remove_btn.setStyleSheet("""
                QPushButton {
                    border-radius: 9px;
                    background-color: #ff6b6b;
                    color: white;
                    font-weight: bold;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #ff4757;
                }
            """)
            
            # Position the X button in the upper right of the icon
            icon_frame.layout().addWidget(remove_btn, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            
            # Add the frame to the container
            icon_container_layout.addWidget(icon_frame)
            
            # Add the container to the item
            file_item.layout().addWidget(icon_container)
            
            # File name (basename only) - truncated if too long
            file_name = os.path.basename(file_path)
            if len(file_name) > 20:
                display_name = file_name[:17] + "..."
            else:
                display_name = file_name
                
            name_label = QLabel(display_name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setToolTip(file_path)  # Full path on hover
            file_item.layout().addWidget(name_label)
            
            # Add to grid with alignment
            self.file_list_layout.addWidget(file_item, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    
    def remove_file(self):
        """Remove a file from the list"""
        btn = self.sender()
        index = btn.property("file_index")
        
        if 0 <= index < len(self.selected_files):
            del self.selected_files[index]
            self.update_file_display()
    
    def setup_file_filter(self, layout, wrapper_layout=None):
        """Create and add file filter dropdown for either CPIDR or DEPID"""
        file_filter_layout = QHBoxLayout()
        file_filter_layout.addWidget(QLabel("Show data for:"))
        
        self.file_filter_combo = QComboBox()
        self.file_filter_combo.addItem("All files (combined)")
        self.file_filter_combo.setEnabled(False)  # Disabled until multiple files analyzed
        self.file_filter_combo.currentIndexChanged.connect(self.file_filter_changed)
        
        file_filter_layout.addWidget(self.file_filter_combo)
        file_filter_layout.addStretch()
        
        if wrapper_layout:
            wrapper_layout.addLayout(file_filter_layout)
        else:
            layout.addLayout(file_filter_layout)
            
        return self.file_filter_combo
    
    def file_filter_changed(self):
        """Handler for when file filter is changed"""
        # Update displays based on selected file
        self.update_token_table()
        self.update_dependency_table()
        
    def update_dependency_table(self):
        """Update the dependency table based on file selection"""
        if not self.current_dependencies and not self.file_dependencies:
            return
            
        self.dependency_table.setRowCount(0)
        
        # Determine which dependencies to display
        selected_index = self.depid_file_combo.currentIndex()
        
        # If "All files (combined)" or in text mode
        if selected_index == 0 or not self.file_dependencies:
            dependencies = self.current_dependencies
            self.dependency_file_label.setText("Showing: All files (combined)")
        else:
            # Adjust for 0-based index and the "All files" item
            file_index = selected_index - 1
            if file_index < len(self.file_dependencies):
                dependencies = self.file_dependencies[file_index]
                self.dependency_file_label.setText(f"Showing: {self.file_names[file_index]}")
            else:
                dependencies = self.current_dependencies
                self.dependency_file_label.setText("Showing: All files (combined)")
        
        if not dependencies:
            return
            
        # Update table with selected dependencies
        for i, dep in enumerate(dependencies):
            self.dependency_table.insertRow(i)
            self.dependency_table.setItem(i, 0, QTableWidgetItem(str(dep[0])))
            self.dependency_table.setItem(i, 1, QTableWidgetItem(str(dep[1])))
            self.dependency_table.setItem(i, 2, QTableWidgetItem(str(dep[2])))
    
    def get_input_text(self):
        """Get input text based on current mode"""
        if self.input_mode == "text":
            return self.text_input.toPlainText(), None
        else:  # File mode
            if not self.selected_files:
                return "", None
                
            # Store file texts and paths separately
            file_texts = []
            valid_file_paths = []
            
            for file_path in self.selected_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_text = f.read()
                        file_texts.append(file_text)
                        valid_file_paths.append(file_path)
                except Exception as e:
                    QMessageBox.warning(
                        self, "File Error", 
                        f"Error reading file {os.path.basename(file_path)}: {str(e)}"
                    )
            
            if not file_texts:
                return "", None
                
            # Return combined text and list of file paths with corresponding texts
            file_info = []
            for path, text in zip(valid_file_paths, file_texts):
                file_info.append({"path": path, "text": text})
                
            return "\n\n".join(file_texts), file_info
            
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

        filename = None
        if args.text:
            text = " ".join(args.text)
        else:  # args.file is set
            try:
                text = read_text_from_file(args.file)
                filename = os.path.basename(args.file)
            except (FileNotFoundError, IOError) as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
                
        cli_main(text, args.speech_mode, args.csv, args.txt, filename)
    else:
        # Start GUI
        app = QApplication(sys.argv)
        window = IdeaDensityApp()
        window.show()
        sys.exit(app.exec())
