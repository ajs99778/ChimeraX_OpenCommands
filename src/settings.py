from Qt.QtCore import Qt
from Qt.QtGui import QIcon
from Qt.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QStyle,
    QPushButton,
    QHeaderView,
)

from chimerax.ui.options import Option
from chimerax.core.settings import Settings


# 'settings' module attribute will be set by manager initialization
class _openCommandsSettings(Settings):
    EXPLICIT_SAVE = {
        "DATA": [],
    }


class _cmd_widget(QWidget):
    def __init__(self, *args, available_formats=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if available_formats is None:
            available_formats = list()
        
        self._layout = QFormLayout(self)
        self._layout.addRow(QLabel("enter commands when opening specific file types"))
        self._layout.addRow(QLabel("${i} will be replaced with the model's specifier"))

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["file type", "name RegEx", "commands", "remove"]
        )
        self._table.cellClicked.connect(
            self._table_clicked,
        )
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.resizeColumnToContents(3)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        w = int(0.75 * self.width() - self._table.columnWidth(3)) / 3
        for i in range(0, 3):
            self._table.setColumnWidth(i, w)
        self._layout.addRow(self._table)
        
        button = QPushButton("add new condition")
        button.clicked.connect(self.addRow)
        self._layout.addRow(button)
        
        self._available_formats = sorted(available_formats, key=lambda x: x.name)

    def _table_clicked(self, row, col):
        if col == 3:
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
        
        item = QLineEdit()
        item.setPlaceholderText("click to edit commands")
        self._table.setCellWidget(rows, 2, item)
        
        widget_that_lets_me_horizontally_align_an_icon = QWidget()
        widget_layout = QHBoxLayout(widget_that_lets_me_horizontally_align_an_icon)
        section_remove = QLabel()
        dim = int(1.5 * section_remove.fontMetrics().boundingRect("Q").height())
        section_remove.setPixmap(
            QIcon(section_remove.style().standardIcon(
                QStyle.SP_DialogDiscardButton)
            ).pixmap(dim, dim)
        )
        widget_layout.addWidget(section_remove, 0, Qt.AlignHCenter)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        self._table.setCellWidget(
            rows, 3, widget_that_lets_me_horizontally_align_an_icon
        )


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
            commands = self.widget._table.cellWidget(row, 2).text()
            data.append(
                [file_type, regex, commands]
            )
        
        return data
    
    def set_value(self, value):
        self.widget._table.setRowCount(0)
        for row, (file_type, regex, commands) in enumerate(value):
            self.widget.addRow()
            file_type_option = self.widget._table.cellWidget(row, 0)
            ndx = file_type_option.findData(file_type, role=Qt.UserRole, flags=Qt.MatchExactly)
            if ndx >= 0:
                file_type_option.setCurrentIndex(ndx)
            else:
                file_type_option.addItem(file_type)
            
            regex_option = self.widget._table.cellWidget(row, 1)
            regex_option.setText(regex)
            
            command_option = self.widget._table.cellWidget(row, 2)
            command_option.setText(commands)
    
    value = property(get_value, set_value)

    def _make_widget(self):
        self.widget = _cmd_widget(available_formats=self._available_formats)


def register_settings_options(session):
        def _opt_cb(opt, ses=session):
            setting = opt.attr_name
            val = opt.value
            setattr(opt.settings, setting, val)
        
        session.ui.main_window.add_settings_option(
            "Open Models",
            OpenCommandOption(
                "", settings.DATA, _opt_cb,
                available_formats=session.open_command.open_data_formats,
                settings=settings,
                attr_name="DATA",
            )
        )
