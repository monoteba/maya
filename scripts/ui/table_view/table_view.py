import os
import csv

# PySide2 is for Maya 2017+, PySide is for Maya 2016-(2011 ?)
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance


class MyTable(QTableWidget):
    def __init__(self, rows, columns):
        super(MyTable, self).__init__(rows, columns)
        self.check_for_change = True
        self.init_ui()
    
    def init_ui(self):
        self.cellChanged.connect(self.c_current)
        self.itemSelectionChanged.connect(self.selection_change)
        self.show()
        self.raise_()
    
    def c_current(self):
        if not self.check_for_change:
            return
        
        row = self.currentRow()
        col = self.currentColumn()
        value = self.item(row, col).text()
        print('You set row ', row, ' and col ', col)
        print('Cell value is ', value)

    def selection_change(self):
        pass

    def remove_selected_rows(self):
        rows = set()
        for item in self.selectedIndexes():
            rows.add(item.row())

        for i, row in enumerate(rows):
            self.removeRow(row - i)

        self.clearSelection()

    def read_csv(self):
        self.check_for_change = False
        path = QFileDialog.getOpenFileName(self, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if path[0] != '':
            with open(path[0], 'r') as csv_file:
                self.setRowCount(0)
                self.setColumnCount(0)
                my_file = csv.reader(csv_file, dialect='excel')
                
                for row_data in my_file:
                    row = self.rowCount()
                    self.insertRow(row)
                    self.setColumnCount(len(row_data))
                    for column, val in enumerate(row_data):
                        item = QTableWidgetItem(val)
                        self.setItem(row, column, item)
        
        self.check_for_change = True
    
    def write_csv(self):
        path = QFileDialog.getSaveFileName(self, 'Save CSV', os.getenv('HOME', 'CSV(*.csv)'))
        if path[0] != '':
            with open(path[0], 'w') as csv_file:
                writer = csv.writer(csv_file, dialect='excel')
                for row in range(self.rowCount()):
                    row_data = []
                    for column in range(self.columnCount()):
                        item = self.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)


class MySheet(QMainWindow):
    def __init__(self):
        super(MySheet, self).__init__()
        
        self.form_widget = MyTable(10, 4)
        self.setCentralWidget(self.form_widget)
        
        col_headers = ['A', 'B', 'C', 'D']
        self.form_widget.setHorizontalHeaderLabels(col_headers)
        
        # number = QTableWidgetItem('B-10')
        # self.form_widget.setCurrentCell(9, 1)
        # self.form_widget.setItem(9, 1, number)
        
        # self.form_widget.read_csv()
        
        #self.form_widget.removeRow(2)
        
        self.show()
        self.raise_()


app = qApp
sheet = MySheet()
