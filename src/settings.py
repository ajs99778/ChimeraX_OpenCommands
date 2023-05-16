from pathlib import Path

from Qt.QtCore import Qt, QSize
from Qt.QtGui import QIcon, QPixmap
from Qt.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QStyle,
    QPushButton,
    QHeaderView,
    QApplication,
)

from chimerax import app_dirs, app_data_dir
from chimerax.ui.options import Option
from chimerax.core.settings import Settings


class _openCommandsSettings(Settings):
    EXPLICIT_SAVE = {
        "DATA": [],
    }
    AUTO_SAVE = {
        "version": 1,
    }


class _cmd_widget(QWidget):
    def __init__(self, *args, available_formats=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if available_formats is None:
            available_formats = list()
        
        self._layout = QFormLayout(self)
        self._layout.addRow(QLabel("#X will be replaced with the model's specifier for commands"))
        self._layout.addRow(QLabel("for Python code, use 'model' for the model object"))

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["file type", "name RegEx", "type", "apply to", "execute", "remove"]
        )
        self._table.cellClicked.connect(
            self._table_clicked,
        )
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.resizeColumnToContents(2)
        self._table.resizeColumnToContents(3)
        self._table.resizeColumnToContents(5)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self._layout.addRow(self._table)
        
        button = QPushButton("add new condition")
        button.clicked.connect(self.addRow)
        self._layout.addRow(button)
        
        self._available_formats = sorted(available_formats, key=lambda x: x.name)

    def _table_clicked(self, row, col):
        if col == 5:
            self._table.removeRow(row)

    def addRow(self):
        rows = self._table.rowCount()
        self._table.insertRow(rows)
        
        combobox = QComboBox()
        formats = ["%s (%s)" % (fmt.name, ",".join("*%s" % suffix for suffix in fmt.suffixes)) for fmt in self._available_formats]
        combobox.addItems(["Any", *formats])
        combobox.setItemData(0, "Any")
        for i, fmt in enumerate(self._available_formats):
            combobox.setItemData(i + 1, fmt.name, role=Qt.UserRole)
        self._table.setCellWidget(rows, 0, combobox)
        
        regex = QLineEdit()
        regex.setPlaceholderText("optional")
        self._table.setCellWidget(rows, 1, regex)

        dim = int(1.5 * regex.fontMetrics().boundingRect("Q").height())

        cmd_type = QComboBox()
        icon_path = Path(app_data_dir, "%s-icon512.png" % app_dirs.appname)
        if icon_path.exists():
            cmd_icon = QIcon(str(icon_path))
            cmd_type.addItem(cmd_icon, "")
        else:
            cmd_type.addItem("command")
        # icon size doesn't seem to scale with system font size
        cmd_type.setIconSize(QSize(int(dim / 1.4), int(dim / 1.4)))
        cmd_type.setItemData(0, "command", role=Qt.UserRole)
        
        icon_path = Path(app_data_dir, "jupyter", "kernels", "python3", "logo-64x64.png")
        if icon_path.exists():
            python_icon = QIcon(str(icon_path))
            cmd_type.addItem(python_icon, "")
        else:
            cmd_type.addItem("python")
        cmd_type.setItemData(1, "python", role=Qt.UserRole)
        self._table.setCellWidget(rows, 2, cmd_type)
        
        apply_to_type = QComboBox()
        apply_to_type.addItems(["parent", "children", "any"])
        self._table.setCellWidget(rows, 3, apply_to_type)
        
        item = QPlainTextEdit()
        item.setPlaceholderText("click to edit commands/code")
        self._table.setCellWidget(rows, 4, item)

        widget_that_lets_me_horizontally_align_an_icon = QWidget()
        widget_layout = QHBoxLayout(widget_that_lets_me_horizontally_align_an_icon)
        section_remove = QLabel()
        section_remove.setPixmap(
            QIcon(section_remove.style().standardIcon(
                QStyle.SP_DialogDiscardButton)
            ).pixmap(dim, dim)
        )
        widget_layout.addWidget(section_remove, 0, Qt.AlignHCenter)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        self._table.setCellWidget(
            rows, 5, widget_that_lets_me_horizontally_align_an_icon
        )
        self._table.resizeColumnToContents(3)


class OpenCommandOption(Option):
    def __init__(self, *args, available_formats=None, **kwargs):
        self._available_formats = available_formats
        super().__init__(*args, **kwargs)
    
    def set_multiple(self):
        pass

    def get_value(self):
        data = list()
        for row in range(0, self.widget._table.rowCount()):
            file_type = self.widget._table.cellWidget(row, 0).currentData(role=Qt.UserRole)
            regex = self.widget._table.cellWidget(row, 1).text()
            cmd_type = self.widget._table.cellWidget(row, 2).currentData(role=Qt.UserRole)
            model_group = self.widget._table.cellWidget(row, 3). currentText()
            commands = self.widget._table.cellWidget(row, 4).toPlainText()
            data.append(
                [file_type, regex, cmd_type, commands, model_group]
            )
        
        return data
    
    def set_value(self, value):
        self.widget._table.setRowCount(0)
        for row, (file_type, regex, cmd_type, commands, mdl_group) in enumerate(value):
            self.widget.addRow()
            file_type_option = self.widget._table.cellWidget(row, 0)
            ndx = file_type_option.findData(file_type, role=Qt.UserRole, flags=Qt.MatchExactly)
            if ndx >= 0:
                file_type_option.setCurrentIndex(ndx)
            else:
                file_type_option.addItem(file_type)
                file_type_option.setCurrentIndex(file_type_option.count() - 1)
            
            regex_option = self.widget._table.cellWidget(row, 1)
            regex_option.setText(regex)
            
            cmd_type_option = self.widget._table.cellWidget(row, 2)
            ndx = cmd_type_option.findData(cmd_type, role=Qt.UserRole, flags=Qt.MatchExactly)
            cmd_type_option.setCurrentIndex(ndx)
            
            apply_to_type = self.widget._table.cellWidget(row, 3)
            ndx = apply_to_type.findText(mdl_group, flags=Qt.MatchExactly)
            apply_to_type.setCurrentIndex(ndx)
            
            command_option = self.widget._table.cellWidget(row, 4)
            command_option.setPlainText(commands)
    
    value = property(get_value, set_value)

    def _make_widget(self):
        self.widget = _cmd_widget(available_formats=self._available_formats)


def register_settings_options(session):
        def _opt_cb(opt, ses=session):
            setting = opt.attr_name
            val = opt.value
            setattr(opt.settings, setting, val)
        
        session.ui.main_window.add_settings_option(
            "Open Commands",
            OpenCommandOption(
                "", settings.DATA, _opt_cb,
                available_formats=session.open_command.open_data_formats,
                settings=settings,
                attr_name="DATA",
            )
        )
