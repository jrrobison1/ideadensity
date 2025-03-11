import sys
import argparse
import os
import tomli
import spacy
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QTabWidget,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QToolButton,
    QSizePolicy,
    QMenu,
    QMenuBar,
    QRadioButton,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QGridLayout,
    QComboBox,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from ideadensity.idea_density_rater import rate_text
from ideadensity import depid
from ideadensity.utils.export_utils import (
    export_cpidr_to_csv,
    export_depid_to_csv,
    export_cpidr_to_txt,
    export_cpidr_multiple_files_to_txt,
    export_summary_to_txt,
    export_summary_to_csv,
)
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
    word_count, proposition_count, density, word_list = rate_text(
        text, speech_mode=speech_mode
    )

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
            export_cpidr_to_txt(
                word_list,
                text,
                word_count,
                proposition_count,
                density,
                txt_output,
                filename,
            )
            print(f"Results exported to {txt_output} in CPIDR format")
        except Exception as e:
            print(f"Error exporting to TXT: {str(e)}")


class IdeaDensityApp(QWidget):
    def __init__(self):
        super().__init__()
        # Get version and set window title
        app_version = get_version()
        self.setWindowTitle(f"ideadensity {app_version}")
        self.resize(1000, 700)
        # Make the window start maximized
        self.setWindowState(Qt.WindowState.WindowMaximized)
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
        # Set maximum height to reduce the top section size by about 25%
        self.input_stack.setMaximumHeight(200)  # Limit the height of the input area
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

        self.select_file_button = QPushButton("Browse...")
        self.select_file_button.clicked.connect(self.select_files)
        file_header_layout.addWidget(self.select_file_button)

        clear_files_button = QToolButton()
        clear_files_button.setToolTip("Clear Files")
        clear_files_button.clicked.connect(self.clear_files)

        # Try to use system icon for clear/trash
        if QIcon.hasThemeIcon("edit-clear"):
            clear_files_button.setIcon(QIcon.fromTheme("edit-clear"))
        elif QIcon.hasThemeIcon("trash-empty"):
            clear_files_button.setIcon(QIcon.fromTheme("trash-empty"))
        else:
            # Simple text alternative if no system icon
            clear_files_button.setText("🗑️")
            clear_files_button.setStyleSheet("font-size: 16px;")
        file_header_layout.addWidget(clear_files_button)

        file_header_layout.addStretch()
        file_input_layout.addLayout(file_header_layout)

        # Scroll area for file list
        file_scroll = QScrollArea()
        file_scroll.setWidgetResizable(True)
        file_scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Create a table for file display
        self.file_list_widget = QTableWidget()
        self.file_list_widget.setColumnCount(4)
        self.file_list_widget.setHorizontalHeaderLabels(
            ["", "File Name", "Size", "Full Path"]
        )
        self.file_list_widget.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )  # Delete icon
        self.file_list_widget.setColumnWidth(0, 40)  # Fixed width for delete column
        self.file_list_widget.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )  # Stretch file name
        self.file_list_widget.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # Size
        self.file_list_widget.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )  # Full path
        self.file_list_widget.verticalHeader().setVisible(False)  # Hide row numbers
        self.file_list_widget.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
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

        # Button and options row
        button_options_layout = QHBoxLayout()

        # Analyze button
        self.cpidr_analyze_btn = QPushButton("Analyze with CPIDR")
        self.cpidr_analyze_btn.clicked.connect(self.analyze_cpidr)
        button_options_layout.addWidget(self.cpidr_analyze_btn)

        # Options directly in horizontal layout
        self.speech_mode_checkbox = QCheckBox("Speech Mode (filter fillers)")
        button_options_layout.addWidget(self.speech_mode_checkbox)

        # Add stretcher to push everything to the left
        button_options_layout.addStretch()

        cpidr_layout.addLayout(button_options_layout)

        # We'll move the file filter combobox to the token details section

        results_layout = QHBoxLayout()

        # Results section
        cpidr_results_group = QGroupBox("Summary")
        cpidr_results_layout = QVBoxLayout()

        # Header with title and download button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        # Add a label with content that will appear at the left
        header_label = QLabel("<b>CPIDR Analysis</b>")
        header_layout.addWidget(header_label)
        
        # Add stretch to push the button to the right
        header_layout.addStretch(1)

        # Download button with menu for different formats
        self.cpidr_summary_export_btn = QToolButton()
        self.cpidr_summary_export_btn.setToolTip("Download Summary")
        self.cpidr_summary_export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.cpidr_summary_export_btn.setEnabled(
            False
        )  # Disabled until analysis is run
        
        # Create menu for export options
        cpidr_summary_export_menu = QMenu(self)
        export_txt_action = cpidr_summary_export_menu.addAction("TXT")
        export_csv_action = cpidr_summary_export_menu.addAction("CSV")
        
        # Connect actions to handlers
        export_txt_action.triggered.connect(self.export_cpidr_summary_txt)
        export_csv_action.triggered.connect(self.export_cpidr_summary_csv)
        
        # Set the menu on the button
        self.cpidr_summary_export_btn.setMenu(cpidr_summary_export_menu)

        # Set an icon (try system theme first, then fall back)
        icon_set = False
        # Try system theme icon
        if QIcon.hasThemeIcon("document-save-as") and not icon_set:
            self.cpidr_summary_export_btn.setIcon(QIcon.fromTheme("document-save-as"))
            icon_set = True
        elif QIcon.hasThemeIcon("document-save") and not icon_set:
            self.cpidr_summary_export_btn.setIcon(QIcon.fromTheme("document-save"))
            icon_set = True

        # If no system icon, use a text alternative with styling
        if not icon_set:
            self.cpidr_summary_export_btn.setText("↓")
            self.cpidr_summary_export_btn.setStyleSheet(
                """
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """
            )

        self.cpidr_summary_export_btn.setIconSize(QSize(16, 16))
        header_layout.addWidget(self.cpidr_summary_export_btn)

        cpidr_results_layout.addLayout(header_layout)

        # Results content
        self.cpidr_results = QLabel("Results will appear here")
        self.cpidr_results.setAlignment(Qt.AlignmentFlag.AlignTop)
        cpidr_results_layout.addWidget(self.cpidr_results)

        cpidr_results_group.setLayout(cpidr_results_layout)
        results_layout.addWidget(cpidr_results_group, 1)  # Stretch factor 1

        # Token details table with filters
        word_details_group = QGroupBox("Token Details")
        word_details_layout = QVBoxLayout()

        # Header with filters and export button
        header_layout = QHBoxLayout()

        # Add file filter dropdown in place of the file indication label
        file_filter_layout = QHBoxLayout()
        file_filter_layout.addWidget(QLabel("Show data for:"))

        self.cpidr_file_combo = QComboBox()
        self.cpidr_file_combo.addItem("All files (combined)")
        self.cpidr_file_combo.setEnabled(
            False
        )  # Disabled until multiple files analyzed
        self.cpidr_file_combo.currentIndexChanged.connect(self.file_filter_changed)

        file_filter_layout.addWidget(self.cpidr_file_combo)
        header_layout.addLayout(file_filter_layout)

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
            self.cpidr_export_btn.setStyleSheet(
                """
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """
            )

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
        self.cpidr_export_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        header_layout.addWidget(self.cpidr_export_btn)

        # Add header to layout
        word_details_layout.addLayout(header_layout)

        # Token table
        self.word_table = QTableWidget(0, 4)
        self.word_table.setHorizontalHeaderLabels(
            ["Token", "POS Tag", "Is Proposition", "Rule"]
        )
        self.word_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        # Make the table expand to fill available space
        self.word_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        word_details_layout.addWidget(self.word_table)

        word_details_group.setLayout(word_details_layout)
        results_layout.addWidget(
            word_details_group, 3
        )  # Increased stretch factor from 2 to 3

        cpidr_layout.addLayout(results_layout)
        cpidr_tab.setLayout(cpidr_layout)

        # DEPID Tab
        depid_layout = QVBoxLayout()

        # Button and options row
        button_options_layout = QHBoxLayout()

        # Analyze button
        self.depid_analyze_btn = QPushButton("Analyze with DEPID")
        self.depid_analyze_btn.clicked.connect(self.analyze_depid)
        button_options_layout.addWidget(self.depid_analyze_btn)

        # Options directly in horizontal layout
        self.depid_r_checkbox = QCheckBox("Use DEPID-R (count distinct dependencies)")
        button_options_layout.addWidget(self.depid_r_checkbox)

        # Add stretcher to push everything to the left
        button_options_layout.addStretch()

        depid_layout.addLayout(button_options_layout)

        depid_results_layout = QHBoxLayout()

        # DEPID Results
        depid_results_group = QGroupBox("Summary")
        depid_summary_layout = QVBoxLayout()

        # Header with title and download button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        # Add a label with content that will appear at the left
        self.depid_header_label = QLabel("<b>DEPID Analysis</b>")
        header_layout.addWidget(self.depid_header_label)
        
        # Add stretch to push the button to the right
        header_layout.addStretch(1)

        # Download button with menu for different formats
        self.depid_summary_export_btn = QToolButton()
        self.depid_summary_export_btn.setToolTip("Download Summary") 
        self.depid_summary_export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.depid_summary_export_btn.setEnabled(
            False
        )  # Disabled until analysis is run
        
        # Create menu for export options
        depid_summary_export_menu = QMenu(self)
        export_txt_action = depid_summary_export_menu.addAction("TXT")
        export_csv_action = depid_summary_export_menu.addAction("CSV")
        
        # Connect actions to handlers
        export_txt_action.triggered.connect(self.export_depid_summary_txt)
        export_csv_action.triggered.connect(self.export_depid_summary_csv)
        
        # Set the menu on the button
        self.depid_summary_export_btn.setMenu(depid_summary_export_menu)

        # Set an icon (try system theme first, then fall back)
        icon_set = False
        # Try system theme icon
        if QIcon.hasThemeIcon("document-save-as") and not icon_set:
            self.depid_summary_export_btn.setIcon(QIcon.fromTheme("document-save-as"))
            icon_set = True
        elif QIcon.hasThemeIcon("document-save") and not icon_set:
            self.depid_summary_export_btn.setIcon(QIcon.fromTheme("document-save"))
            icon_set = True

        # If no system icon, use a text alternative with styling
        if not icon_set:
            self.depid_summary_export_btn.setText("↓")
            self.depid_summary_export_btn.setStyleSheet(
                """
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """
            )

        self.depid_summary_export_btn.setIconSize(QSize(16, 16))
        header_layout.addWidget(self.depid_summary_export_btn)

        depid_summary_layout.addLayout(header_layout)

        # Results content
        self.depid_results = QLabel("Results will appear here")
        self.depid_results.setAlignment(Qt.AlignmentFlag.AlignTop)
        depid_summary_layout.addWidget(self.depid_results)

        depid_results_group.setLayout(depid_summary_layout)
        depid_results_layout.addWidget(depid_results_group, 1)  # Stretch factor 1

        # Dependency details
        dependency_group = QGroupBox("Dependencies")
        dependency_layout = QVBoxLayout()

        # Header for export button
        header_layout = QHBoxLayout()

        # Add file filter dropdown in place of the file indication label
        file_filter_layout = QHBoxLayout()
        file_filter_layout.addWidget(QLabel("Show data for:"))

        self.depid_file_combo = QComboBox()
        self.depid_file_combo.addItem("All files (combined)")
        self.depid_file_combo.setEnabled(
            False
        )  # Disabled until multiple files analyzed
        self.depid_file_combo.currentIndexChanged.connect(self.file_filter_changed)

        file_filter_layout.addWidget(self.depid_file_combo)
        header_layout.addLayout(file_filter_layout)

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
            self.depid_export_btn.setStyleSheet(
                """
                QToolButton {
                    padding: 3px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                }
            """
            )

        self.depid_export_btn.setIconSize(QSize(16, 16))

        self.depid_export_btn.clicked.connect(self.export_depid_csv)
        self.depid_export_btn.setEnabled(False)  # Disabled until analysis is run
        self.depid_export_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        header_layout.addWidget(self.depid_export_btn)

        dependency_layout.addLayout(header_layout)

        # Table
        self.dependency_table = QTableWidget(0, 3)
        self.dependency_table.setHorizontalHeaderLabels(["Token", "Dependency", "Head"])
        self.dependency_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        # Make the table expand to fill available space
        self.dependency_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        dependency_layout.addWidget(self.dependency_table)

        dependency_group.setLayout(dependency_layout)
        depid_results_layout.addWidget(
            dependency_group, 3
        )  # Increased stretch factor from 2 to 3

        depid_layout.addLayout(depid_results_layout)
        depid_tab.setLayout(depid_layout)

        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)

    def analyze_cpidr(self):
        text, file_info = self.get_input_text()
        if not text:
            error_msg = (
                "Please enter some text to analyze."
                if self.input_mode == "text"
                else "Please select files to analyze."
            )
            self.cpidr_results.setText(error_msg)
            return

        # Show processing indicator for large files
        if len(text) > 10000:
            self.cpidr_results.setText("Processing text, please wait...")
            QApplication.processEvents()  # Update UI

        speech_mode = self.speech_mode_checkbox.isChecked()
        word_count, proposition_count, density, word_list = rate_text(
            text, speech_mode=speech_mode
        )

        # Display summary results
        result_text = (
            f"Word count: {word_count}<br>"
            f"Proposition count: {proposition_count}<br>"
            f"Idea density: {density:.3f}"
        )

        # Reset file data
        self.file_word_lists = []
        self.file_names = []

        # Store combined results for exporting - we will exclude these during export
        self.cpidr_combined_ideas_count = proposition_count
        self.cpidr_combined_word_count = word_count
        self.cpidr_combined_density = density

        # Initialize per-file results lists (without combined results)
        self.cpidr_ideas_counts = []
        self.cpidr_word_counts = []
        self.cpidr_densities = []

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
                file_word_count, file_prop_count, file_density, file_word_list = (
                    rate_text(file_text, speech_mode=speech_mode)
                )

                # Store file results for table filtering
                self.file_word_lists.append(file_word_list)
                self.file_names.append(file_name)

                # Store results for exporting
                self.cpidr_ideas_counts.append(file_prop_count)
                self.cpidr_word_counts.append(file_word_count)
                self.cpidr_densities.append(file_density)

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

            # For text mode, use placeholder filename
            if not self.file_names:
                self.file_names = ["input_text"]

        self.cpidr_results.setText(result_text)

        # Save word list for filtering
        self.current_word_list = word_list
        self.update_token_table()

        # Enable export buttons
        self.cpidr_export_btn.setEnabled(True)

        # Only enable summary export in file mode with multiple files
        self.cpidr_summary_export_btn.setEnabled(
            self.input_mode == "file" and len(self.file_names) > 0
        )

    def update_token_filters(self):
        """Update token table based on filter checkboxes"""
        # Ensure mutual exclusivity between filter options
        if (
            self.sender() == self.show_all_tokens_checkbox
            and self.show_all_tokens_checkbox.isChecked()
        ):
            self.show_only_words_checkbox.setChecked(False)
            self.show_only_props_checkbox.setChecked(False)
        elif self.sender() in [
            self.show_only_words_checkbox,
            self.show_only_props_checkbox,
        ]:
            if self.sender().isChecked():
                self.show_all_tokens_checkbox.setChecked(False)

        # If nothing is checked, default to "Show All"
        if not any(
            [
                self.show_all_tokens_checkbox.isChecked(),
                self.show_only_words_checkbox.isChecked(),
                self.show_only_props_checkbox.isChecked(),
            ]
        ):
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
        else:
            # Adjust for 0-based index and the "All files" item
            file_index = selected_index - 1
            if file_index < len(self.file_word_lists):
                word_list = self.file_word_lists[file_index]
            else:
                word_list = self.current_word_list

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
                show_prop = (
                    self.show_only_props_checkbox.isChecked() and word.is_proposition
                )
                show_token = show_word or show_prop

            if show_token:
                self.word_table.insertRow(row)
                self.word_table.setItem(row, 0, QTableWidgetItem(word.token))
                self.word_table.setItem(row, 1, QTableWidgetItem(word.tag))
                self.word_table.setItem(
                    row, 2, QTableWidgetItem("Yes" if word.is_proposition else "No")
                )
                self.word_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        str(word.rule_number) if word.rule_number is not None else ""
                    ),
                )
                row += 1

    def analyze_depid(self):
        text, file_info = self.get_input_text()
        if not text:
            error_msg = (
                "Please enter some text to analyze."
                if self.input_mode == "text"
                else "Please select files to analyze."
            )
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
        
        # Update the header label
        self.depid_header_label.setText(f"<b>{method_name} Analysis</b>")
        
        result_text = (
            f"Word count: {word_count}<br>"
            f"Dependency count: {len(dependencies)}<br>"
            f"Idea density: {density:.3f}"
        )

        # Reset file data
        self.file_dependencies = []
        self.file_names = []  # Always reset file names for consistency

        # Store combined results for exporting - we will exclude these during export
        self.depid_analyzer_type = method_name
        self.depid_combined_ideas_count = len(dependencies)
        self.depid_combined_word_count = word_count
        self.depid_combined_density = density

        # Initialize per-file results lists (without combined results)
        self.depid_ideas_counts = []
        self.depid_word_counts = []
        self.depid_densities = []

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
                file_density, file_word_count, file_dependencies = depid(
                    file_text, is_depid_r=is_depid_r
                )

                # Store file results for table filtering
                self.file_dependencies.append(file_dependencies)
                self.file_names.append(file_name)  # Always add the file name

                # Store results for exporting
                self.depid_ideas_counts.append(len(file_dependencies))
                self.depid_word_counts.append(file_word_count)
                self.depid_densities.append(file_density)

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

            # For text mode, use placeholder filename
            if not self.file_names:
                self.file_names = ["input_text"]

        self.depid_results.setText(result_text)

        # Display dependency details in table
        self.current_dependencies = dependencies
        self.update_dependency_table()

        # Enable export buttons
        self.depid_export_btn.setEnabled(True)

        # Only enable summary export in file mode with multiple files
        self.depid_summary_export_btn.setEnabled(
            self.input_mode == "file" and len(self.file_names) > 0
        )

    def export_cpidr_csv(self):
        """Export CPIDR token details to a CSV file"""
        if not self.current_word_list:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            os.path.expanduser("~/cpidr_tokens.csv"),
            "CSV Files (*.csv);;All Files (*)",
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
            self,
            "Save TXT File",
            os.path.expanduser("~/cpidr_results.txt"),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                # Check if we're in file mode and have multiple files
                if (
                    self.input_mode == "file"
                    and file_info
                    and len(self.file_names) > 0
                    and len(self.file_word_lists) > 0
                ):

                    # All files combined mode (index 0)
                    if self.cpidr_file_combo.currentIndex() == 0:
                        # Export all files separately in one document
                        export_cpidr_multiple_files_to_txt(
                            self.file_word_lists, self.file_names, file_path
                        )
                    else:
                        # Individual file selected
                        selected_index = (
                            self.cpidr_file_combo.currentIndex() - 1
                        )  # -1 to account for "All files" item
                        if 0 <= selected_index < len(self.file_names):
                            word_list = self.file_word_lists[selected_index]
                            filename = self.file_names[selected_index]

                            # Calculate stats for the selected file
                            word_count = sum(
                                1 for item in word_list.items if item.is_word
                            )
                            proposition_count = sum(
                                1 for item in word_list.items if item.is_proposition
                            )
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
                                filename,
                            )
                else:
                    # Text mode or single file analysis (use current_word_list)
                    # Get the analysis results
                    word_count = sum(
                        1 for item in self.current_word_list.items if item.is_word
                    )
                    proposition_count = sum(
                        1
                        for item in self.current_word_list.items
                        if item.is_proposition
                    )

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
                        filename,
                    )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Results exported to {file_path} in CPIDR format",
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
            self,
            "Save CSV File",
            os.path.expanduser("~/depid_dependencies.csv"),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            try:
                export_depid_to_csv(self.current_dependencies, file_path)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Dependency details exported to {file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting dependency details: {str(e)}",
                )

    def export_cpidr_summary_txt(self):
        """Export CPIDR summary results to a TXT file"""
        if not self.file_names:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        if self.input_mode != "file":
            QMessageBox.warning(
                self,
                "Export Error",
                "Summary export is only available in file input mode.",
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Summary TXT File",
            os.path.expanduser("~/cpidr_summary.txt"),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                export_summary_to_txt(
                    "CPIDR",
                    self.file_names,
                    self.cpidr_ideas_counts,
                    self.cpidr_word_counts,
                    self.cpidr_densities,
                    file_path,
                )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Summary exported to {file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting summary: {str(e)}"
                )
                
    def export_cpidr_summary_csv(self):
        """Export CPIDR summary results to a CSV file"""
        if not self.file_names:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        if self.input_mode != "file":
            QMessageBox.warning(
                self,
                "Export Error",
                "Summary export is only available in file input mode.",
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Summary CSV File",
            os.path.expanduser("~/cpidr_summary.csv"),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            try:
                export_summary_to_csv(
                    "CPIDR",
                    self.file_names,
                    self.cpidr_ideas_counts,
                    self.cpidr_word_counts,
                    self.cpidr_densities,
                    file_path,
                )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Summary exported to {file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting summary: {str(e)}"
                )

    def export_depid_summary_txt(self):
        """Export DEPID summary results to a TXT file"""
        if not self.file_names:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        if self.input_mode != "file":
            QMessageBox.warning(
                self,
                "Export Error",
                "Summary export is only available in file input mode.",
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Summary TXT File",
            os.path.expanduser("~/depid_summary.txt"),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                export_summary_to_txt(
                    (
                        self.depid_analyzer_type
                        if hasattr(self, "depid_analyzer_type")
                        else "DEPID"
                    ),
                    self.file_names,
                    self.depid_ideas_counts,
                    self.depid_word_counts,
                    self.depid_densities,
                    file_path,
                )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Summary exported to {file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting summary: {str(e)}"
                )
                
    def export_depid_summary_csv(self):
        """Export DEPID summary results to a CSV file"""
        if not self.file_names:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        if self.input_mode != "file":
            QMessageBox.warning(
                self,
                "Export Error",
                "Summary export is only available in file input mode.",
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Summary CSV File",
            os.path.expanduser("~/depid_summary.csv"),
            "CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            try:
                export_summary_to_csv(
                    (
                        self.depid_analyzer_type
                        if hasattr(self, "depid_analyzer_type")
                        else "DEPID"
                    ),
                    self.file_names,
                    self.depid_ideas_counts,
                    self.depid_word_counts,
                    self.depid_densities,
                    file_path,
                )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Summary exported to {file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Error exporting summary: {str(e)}"
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
            self,
            "Select Text Files",
            os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*)",
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
        self.file_list_widget.setRowCount(0)

        # Add files to table
        for i, file_path in enumerate(self.selected_files):
            # Get file information
            file_name = os.path.basename(file_path)
            file_info = os.path.getsize(file_path)
            file_size = self.format_file_size(file_info)

            # Add new row to table
            row_position = self.file_list_widget.rowCount()
            self.file_list_widget.insertRow(row_position)

            # Delete button (first column)
            delete_cell_widget = QWidget()
            delete_layout = QHBoxLayout(delete_cell_widget)
            delete_layout.setContentsMargins(2, 2, 2, 2)
            delete_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            delete_btn = QToolButton()
            delete_btn.setToolTip("Remove file")
            delete_btn.setProperty("file_index", i)
            delete_btn.clicked.connect(self.remove_file)
            delete_btn.setIconSize(QSize(16, 16))

            # Try to use system trash icon first
            icon_set = False
            if QIcon.hasThemeIcon("user-trash"):
                delete_btn.setIcon(QIcon.fromTheme("user-trash"))
                icon_set = True
            elif QIcon.hasThemeIcon("trash-empty"):
                delete_btn.setIcon(QIcon.fromTheme("trash-empty"))
                icon_set = True
            elif QIcon.hasThemeIcon("edit-delete"):
                delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
                icon_set = True
            
            # If no system icon, use text alternative
            if not icon_set:
                delete_btn.setText("🗑️")
                delete_btn.setStyleSheet(
                    """
                    QToolButton {
                        border: none;
                        font-size: 16px;
                        color: #ff4757;
                    }
                    QToolButton:hover {
                        color: #ff6b6b;
                    }
                """
                )

            # File name
            self.file_list_widget.setItem(row_position, 1, QTableWidgetItem(file_name))

            # File size
            self.file_list_widget.setItem(row_position, 2, QTableWidgetItem(file_size))

            # Full path
            self.file_list_widget.setItem(row_position, 3, QTableWidgetItem(file_path))

            delete_layout.addWidget(delete_btn)
            self.file_list_widget.setCellWidget(row_position, 0, delete_cell_widget)

    def format_file_size(self, size_bytes):
        """Format file size from bytes to human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"

    def remove_file(self):
        """Remove a file from the list"""
        btn = self.sender()
        index = btn.property("file_index")

        if 0 <= index < len(self.selected_files):
            del self.selected_files[index]
            self.update_file_display()  # This will rebuild the table with updated indices

    # Removed setup_file_filter method since we now include the dropdown directly in each section

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
        else:
            # Adjust for 0-based index and the "All files" item
            file_index = selected_index - 1
            if file_index < len(self.file_dependencies):
                dependencies = self.file_dependencies[file_index]
            else:
                dependencies = self.current_dependencies

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
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_text = f.read()
                        file_texts.append(file_text)
                        valid_file_paths.append(file_path)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "File Error",
                        f"Error reading file {os.path.basename(file_path)}: {str(e)}",
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
        with open(file_path, "r", encoding="utf-8") as file:
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

        parser.add_argument(
            "--version",
            action=VersionAction,
            nargs=0,
            help="Show version information and exit",
        )

        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument("--text", nargs="+", help="The text to analyze")
        input_group.add_argument(
            "--file", type=str, help="Path to a file containing text to analyze"
        )
        parser.add_argument(
            "--speech-mode", action="store_true", help="Enable speech mode"
        )
        parser.add_argument(
            "--csv",
            type=str,
            help="Export token details to a CSV file at the specified path",
        )
        parser.add_argument(
            "--txt",
            type=str,
            help="Export results to a TXT file in CPIDR format at the specified path",
        )
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
