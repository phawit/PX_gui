#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import pyzbar.pyzbar as pyzbar
import numpy as np
import cv2
from collections import Counter
import operator
import time
import csv
import json
import datetime

from threading import Thread, Lock

Ui_MainWindow, QtBaseClass = uic.loadUiType('main.ui')
Ui_AddWindow, QtBaseClass = uic.loadUiType('add.ui')
Ui_StockWindow, QtBaseClass = uic.loadUiType('stock.ui')
Ui_AddStockWindow, QtBaseClass = uic.loadUiType('addStock.ui')
Ui_FinishWindow, QtBaseClass = uic.loadUiType('finish.ui')
Ui_DateInfoWindow, QtBaseClass = uic.loadUiType('date_info.ui')
Ui_ShortcutWindow, QtBaseClass = uic.loadUiType('shortcut_grid_edit.ui')

date_data = {}

template_json = {u'20180101': 
            {u'Daily Sales': 0,
            u'Item Sales': {},
            u'Stock Adding': {},
            u'Current Stock': {}}
        }

items_list = []

items_info = {'Barcode':'000',
              'Item Name':'000',
              'Price':'000',
              'Unit':'000',
              'Total':'000',
              'Stock':'000'}

def UpdateJSON(key, value):
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    if date_str in date_data:
        pass
    else:
        for k, v in template_json.iteritems():
            old_key = k
        template_json[date_str] = template_json.pop(old_key)
        date_data[unicode(date_str, "utf-8")] = template_json.pop(date_str)

    if key == 'sell':
        date_data[date_str][u'Daily Sales'] += value[2]
        if value[0] in date_data[date_str][u'Item Sales']:
            date_data[date_str][u'Item Sales'][value[0]] = value[1] + date_data[date_str][u'Item Sales'][value[0]]
        else:
            date_data[date_str][u'Item Sales'][value[0]] = value[1]
    elif key == 'stock':
        if value[0] in date_data[date_str][u'Stock Adding']:
            date_data[date_str][u'Stock Adding'][value[0]] = value[1] + date_data[date_str][u'Stock Adding'][value[0]]
        else:
            date_data[date_str][u'Stock Adding'][value[0]] = value[1]

    for item in items_list:
        date_data[date_str][u'Current Stock'][unicode(item['Barcode'], "utf-8")] = int(item['Stock'])

    with open('data.json', 'w') as fp:
        json.dump(date_data, fp, sort_keys=True, indent=4, separators=(',', ': '))

image_viewer_size = (280,210)

class Barcode_process:
    def __init__(self) :
        self.started = False
        self.vs = cv2.VideoCapture(1)
        time.sleep(1)

        self.list_item = []
        self.current_item_frame = []
        self.frame_threshold = 3
        self.skip_frame = -1
        self.num_skip_frame = 50
        self.timeout_frame = 50
        self.timeout = 0

        ret, frame = self.vs.read()
        self.webcam_frame = frame

    def start(self) :
        if self.started :
            print("already started!!")
            return None
        self.started = True
        self.thread = Thread(target=self.run, args=())
        self.thread.start()
        return self

    def run(self):
        while self.started:
            ret, frame = self.vs.read()
            if self.skip_frame > 0:
                self.skip_frame -= 1
            else:
                decodedObjects = pyzbar.decode(frame)
                # Print results
                gotObj = False
                for obj in decodedObjects:
                    print(obj.data)
                    gotObj = True
                    timeout = 0
                    cv2.circle(frame,(25,25), 20, (0,255,0), -1)
                    self.current_item_frame.append(obj.data)
                    if len(self.current_item_frame) < self.frame_threshold:
                        pass
                    else:
                        c = Counter(self.current_item_frame)
                        max_c = max(c.iteritems(), key=operator.itemgetter(1))[0]
                        self.list_item.append(max_c)
                        self.current_item_frame = []
                        self.skip_frame = self.num_skip_frame
                        print('')
                        print('Number of items = ' + str(len(self.list_item)))
                        print(self.list_item)
                        print('')

                if not gotObj:
                    if len(self.current_item_frame) > 0:
                        self.timeout += 1
                        if self.timeout >= self.timeout_frame:
                            c = Counter(self.current_item_frame)
                            max_c = max(c.iteritems(), key=operator.itemgetter(1))[0]
                            self.list_item.append(max_c)
                            self.current_item_frame = []
                            self.skip_frame = self.num_skip_frame
                            print('')
                            print('Number of items = ' + str(len(self.list_item)))
                            print(self.list_item)
                            print('')

            self.webcam_frame = frame

class Stock_window(QtGui.QDialog, Ui_StockWindow):
    def __init__(self, parent=None):
        super(Stock_window, self).__init__(parent)
        self.setupUi(self)

        self.selectedRow = -1
        self.table_stock.clicked.connect(self.updateSelected)

        self.addstock_app = AddStock_window(self)
        self.addStock_button.clicked.connect(self.addStock)

        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน']
        header = [ unicode(h, "utf-8") for h in header]
        self.table_stock.setHorizontalHeaderLabels(header)
        header = self.table_stock.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        for items in items_list:
            item_array = [items['Barcode'], items['Item Name'], items['Price'], items['Stock']]
            r = self.table_stock.rowCount()
            self.table_stock.insertRow(r)
            for i in range(len(item_array)):
                self.table_stock.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                if i > 1:
                    self.table_stock.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

    def addStock(self):
        self.addstock_app.line_barcode.setText('')
        self.addstock_app.line_name.setText('')
        self.addstock_app.line_price.setText('')
        self.addstock_app.line_units.setText('')
        self.addstock_app.show()
        self.addstock_app.activateWindow()

    def updateSelected(self):
        self.selectedRow = self.table_stock.currentRow()

class AddStock_window(QtGui.QDialog, Ui_AddStockWindow):
    def __init__(self, parent=None):
        super(AddStock_window, self).__init__(parent)
        self.setupUi(self)

        self.onlydouble = QDoubleValidator()
        self.onlyint = QIntValidator()
        self.line_price.setValidator(self.onlydouble)
        self.line_units.setValidator(self.onlyint)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateInfo)
        self.timer.start(1000)
        self.row = -1

        self.add_button.clicked.connect(self.AddStock)
        self.line_barcode.textChanged.connect(self.BarcodeChange)

    def BarcodeChange(self):
        for items in items_list:
            if self.line_barcode.text() == items['Barcode']:
                self.line_name.setText(items['Item Name'])
                self.line_price.setText(items['Price'])

    def WriteTable2CSV(self):
        file = open('ItemList.csv','w')
        fcsv = csv.writer(file, lineterminator='\n')
        for items in items_list:
            info = [items['Barcode'], items['Item Name'].encode('utf-8'), items['Price'], items['Stock']]
            fcsv.writerow(info)
        file.close()

    def AddStock(self):
        num_stock = int(self.parent().table_stock.item(self.row, 3).text()) + int(str(self.line_units.text()))
        self.parent().table_stock.setItem(self.row , 3, QtGui.QTableWidgetItem(str(num_stock)))
        self.parent().table_stock.item(self.row, 3).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        
        global items_list
        for ii in range(len(items_list)):
            items = items_list[ii]
            if items['Barcode'] == self.parent().table_stock.item(self.row, 0).text():
                items['Stock'] = str(num_stock)
                UpdateJSON('stock', [items['Barcode'], int(str(self.line_units.text()))])
            items_list[ii] = items
        
        self.WriteTable2CSV()
        self.close()

    def updateInfo(self):
        if self.parent().selectedRow > -1:
            self.row = self.parent().selectedRow
            self.line_barcode.setText(self.parent().table_stock.item(self.row, 0).text())
            self.line_name.setText(self.parent().table_stock.item(self.row, 1).text())
            self.line_price.setText(self.parent().table_stock.item(self.row, 2).text())

class Add_window(QtGui.QDialog, Ui_AddWindow):
    def __init__(self, parent=None):
        super(Add_window, self).__init__(parent)
        self.setupUi(self)
        self.add_button.clicked.connect(self.AddItem)
        self.line_barcode.textChanged.connect(self.BarcodeChange)

        self.onlydouble = QDoubleValidator()
        self.onlyint = QIntValidator()
        self.line_price.setValidator(self.onlydouble)
        self.line_units.setValidator(self.onlyint)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateInfo)
        self.timer.start(1000)
        self.row = -1

    def updateInfo(self):
        if self.parent().selectedRow > -1:
            self.row = self.parent().selectedRow
            self.line_barcode.setText(self.parent().table.item(self.row, 0).text())
            self.line_name.setText(self.parent().table.item(self.row, 1).text())
            self.line_price.setText(self.parent().table.item(self.row, 2).text())

    def BarcodeChange(self):
        for items in items_list:
            if self.line_barcode.text() == items['Barcode']:
                self.line_name.setText(items['Item Name'])
                self.line_price.setText(items['Price'])

    def AddItem(self):
        items_info['Barcode'] = str(self.line_barcode.text())
        items_info['Item Name'] = self.line_name.text()
        items_info['Price'] = "{:.2f}".format(float(self.line_price.text()) )
        items_info['Unit'] = str(self.line_units.text())
        try:
            items_info['Total'] = "{:.2f}".format( int(items_info['Unit'])*float(items_info['Price']) )
        except:
            items_info['Total'] = "{:.2f}".format(0.00)

        # check duplicate in table
        r = self.parent().table.rowCount()
        isDuplicate = -1
        for row in range(r):
            if self.parent().table.item(row, 0).text() == items_info['Barcode']:
                isDuplicate = row
                num_unit = int(items_info['Unit']) + int(self.parent().table.item(row, 3).text())
                items_info['Unit'] = str(num_unit)
                items_info['Total'] = "{:.2f}".format( int(items_info['Unit'])*float(items_info['Price']) )

        item_array = [items_info['Barcode'], items_info['Item Name'], items_info['Price'], items_info['Unit'], items_info['Total']]
        if isDuplicate == -1:
            self.parent().table.insertRow(r)
            for i in range(len(item_array)):
                self.parent().table.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                if i > 1:
                    self.parent().table.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        else:
            row = isDuplicate
            for i in range(len(item_array)):
                self.parent().table.setItem(row , i, QtGui.QTableWidgetItem(item_array[i]))
                if i > 1:
                    self.parent().table.item(row, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        r = self.parent().table.rowCount()
        total_price = 0.0
        for row in range(r):
            total_price += float(self.parent().table.item(row, 4).text())
        self.parent().total_price.setText("{:.2f}".format(total_price))
        self.parent().total_price.setAlignment(QtCore.Qt.AlignRight)
        self.close()
 
class DateInfo_window(QtGui.QDialog, Ui_DateInfoWindow):
    def __init__(self, parent=None):
        super(DateInfo_window, self).__init__(parent)
        self.setupUi(self)

class ShortcutEditor_window(QtGui.QDialog, Ui_ShortcutWindow):
    def __init__(self, parent=None, action='add'):
        super(ShortcutEditor_window, self).__init__(parent)
        self.setupUi(self)

        self.action = action

        self.selectedRow = -1
        self.table_stock.clicked.connect(self.updateSelected)
        self.done_button.clicked.connect(self.editShortcut)

        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน']
        header = [ unicode(h, "utf-8") for h in header]
        self.table_stock.setHorizontalHeaderLabels(header)
        header = self.table_stock.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        # self.parent().buttons = {}
        # self.parent().num_current_button = 0

        for items in items_list:
            item_array = [items['Barcode'], items['Item Name'], items['Price'], items['Stock']]
            r = self.table_stock.rowCount()
            self.table_stock.insertRow(r)
            for i in range(len(item_array)):
                self.table_stock.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                if i > 1:
                    self.table_stock.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

    def updateSelected(self):
        self.selectedRow = self.table_stock.currentRow()

    def editShortcut(self):
        if self.action == 'add':
            empty_slot = -1
            for ll in range(len(self.parent().shortcut_button)):
                label = self.parent().shortcut_button[ll]
                if label == 0:
                    empty_slot = ll
                    break

            if empty_slot == -1:
                row = self.parent().table_shortcut.rowCount()
                col = self.parent().num_shortcut_button % self.parent().button_per_row
                if col == 0:
                    self.parent().table_shortcut.insertRow(row)
                else:
                    row -= 1

                self.parent().shortcut_button.append(QLabel(self.table_stock.item(self.selectedRow, 1).text() + '\n' + self.table_stock.item(self.selectedRow, 0).text() + '\n' + self.table_stock.item(self.selectedRow, 2).text() + u' บาท', self))
                self.parent().shortcut_button[self.parent().num_shortcut_button].setGeometry(QtCore.QRect(70, 80, 300, 100)) 
                self.parent().shortcut_button[self.parent().num_shortcut_button].setAlignment(Qt.AlignCenter)
                if (row+col)%2 == 0:
                    self.parent().shortcut_button[self.parent().num_shortcut_button].setStyleSheet("background-color: rgb(135, 255, 157)")
                else:
                    self.parent().shortcut_button[self.parent().num_shortcut_button].setStyleSheet("background-color: rgb(255, 167, 135)")
                self.parent().table_shortcut.setCellWidget(row, col, self.parent().shortcut_button[self.parent().num_shortcut_button] )
                self.parent().table_shortcut.resizeRowsToContents()
                self.parent().table_shortcut.resizeColumnsToContents()
                self.parent().num_shortcut_button += 1
            else:
                ll = empty_slot
                row = int(ll / self.parent().button_per_row)
                col = ll % self.parent().button_per_row 
                self.parent().shortcut_button[ll] = QLabel(self.table_stock.item(self.selectedRow, 1).text() + '\n' + self.table_stock.item(self.selectedRow, 0).text() + '\n' + self.table_stock.item(self.selectedRow, 2).text() + u' บาท', self)
                self.parent().shortcut_button[ll].setGeometry(QtCore.QRect(70, 80, 300, 100)) 
                if (row+col)%2 == 0:
                    self.parent().shortcut_button[ll].setStyleSheet("background-color: rgb(135, 255, 157)")
                else:
                    self.parent().shortcut_button[ll].setStyleSheet("background-color: rgb(255, 167, 135)")
                self.parent().shortcut_button[ll].setAlignment(Qt.AlignCenter)
                self.parent().table_shortcut.setCellWidget(row, col, self.parent().shortcut_button[ll] )
                self.parent().table_shortcut.resizeRowsToContents()
                self.parent().table_shortcut.resizeColumnsToContents()
                self.parent().num_shortcut_button += 1
        else:
            for ll in range(len(self.parent().shortcut_button)):
                label = self.parent().shortcut_button[ll]
                label_barcode = label.text().split('\n')
                if str(label_barcode[1]) == str(self.table_stock.item(self.selectedRow, 0).text()):
                    # del self.parent().shortcut_button[ll]
                    self.parent().shortcut_button[ll] = 0
                    row = int(ll / self.parent().button_per_row)
                    col = ll % self.parent().button_per_row 
                    self.parent().table_shortcut.removeCellWidget(row,col)
                    self.parent().num_shortcut_button -= 1
                    break

        # row = self.parent().table_shortcut.rowCount()
        # for r in range(row):
        #     for c in range(self.parent().button_per_row):
        #         if r*self.parent().button_per_row+c < len(self.parent().shortcut_button):
        #             if (r+c)%2 == 0:
        #                 self.parent().table_shortcut.item(3, 5).setBackground(QtGui.QColor(135, 255, 157))
        #             else:
        #                 self.parent().table_shortcut.item(3, 5).setBackground(QtGui.QColor(255, 167, 135))

            # if self.parent().num_shortcut_button % self.parent().button_per_row == 0:
            #     row = self.parent().table_shortcut.rowCount()
            #     for c in range(self.parent().button_per_row):
            #         self.parent().table_shortcut.removeCellWidget(row-1,c)
            #     # self.parent().table_shortcut.removeRow(row-1)

            # self.parent().num_shortcut_button = 0
            # for ll in range(len(self.parent().shortcut_button)):
            #     label = self.parent().shortcut_button[ll]
            #     row = int(self.parent().num_shortcut_button / self.parent().button_per_row)
            #     col = self.parent().num_shortcut_button % self.parent().button_per_row 
            #     self.parent().table_shortcut.setCellWidget(row, col, label )
            #     self.parent().num_shortcut_button += 1
        self.close()


class Finish_window(QtGui.QDialog, Ui_FinishWindow):
    def __init__(self, parent=None):
        super(Finish_window, self).__init__(parent)
        self.setupUi(self)

        self.onlydouble = QDoubleValidator()
        self.line_received.setValidator(self.onlydouble)
        self.line_change.setValidator(self.onlydouble)

        self.line_received.textChanged.connect(self.ReceivedChange)
        self.done_button.clicked.connect(self.Done)
        self.cancel_button.clicked.connect(self.Cancel)

        self.line_received.setFocus(True)

    def ReceivedChange(self):
        if self.line_received.text() != '':
            change = float(self.line_received.text()) - float(self.line_total.text())
            change = "{:.2f}".format(change)
            self.line_change.setText(change)
        else:
            self.line_change.setText("{:.2f}".format(-float(self.line_total.text())))
        self.line_change.setAlignment(QtCore.Qt.AlignRight)

    def keyPressEvent(self, qKeyEvent):
        if ( qKeyEvent.key() == QtCore.Qt.Key_Return ) or ( qKeyEvent.key() == QtCore.Qt.Key_Enter ): 
            self.Done()

    def Done(self):
        global items_list
        if float(self.line_change.text()) >= 0:
            self.parent().selectedRow = -1
            r = self.parent().table.rowCount()
            for row in range(r):
                for ii in range(len(items_list)):
                    item = items_list[ii]
                    if self.parent().table.item(row, 0).text() == item['Barcode']:
                        item['Stock'] = str(int(item['Stock']) - int(self.parent().table.item(row, 3).text()))
                        UpdateJSON('sell', [item['Barcode'], int(self.parent().table.item(row, 3).text()), float(self.parent().table.item(row, 4).text())])
                        break

            file = open('ItemList.csv','w')
            fcsv = csv.writer(file, lineterminator='\n')
            for items in items_list:
                info = [items['Barcode'], items['Item Name'].encode('utf-8'), items['Price'], items['Stock']]
                fcsv.writerow(info)
            file.close()

            self.showSuccessDialog()
            self.parent().ClearList()
            # time.sleep(1)
            self.close()
        else:
            self.showErrorDialog()

    def showErrorDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        txtmsg = "ได้รับเงินไม่ครบ ต้องการอีก " + '{:.2f}'.format(-float(self.line_change.text())) + ' บาท'
        txtmsg = unicode(txtmsg, 'utf-8')
        msg.setText(txtmsg)
        msg.setWindowTitle(u"พบข้อผิดพลาด")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def showSuccessDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        txtmsg = "ยอดสินค้า " + self.line_total.text() + ' บาท\nได้รับเงิน ' + '{:.2f}'.format(float(self.line_received.text())) + ' บาท\nทอนเงิน ' + self.line_change.text() + ' บาท'
        txtmsg = unicode(txtmsg, 'utf-8')
        msg.setText(txtmsg)
        msg.setWindowTitle(u"ทำรายการสำเร็จ")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def Cancel(self):
        self.close()

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.BP = Barcode_process().start()

        self.add_shortcut_button.setStyleSheet("background-color: rgb(178, 255, 178)")
        self.remove_shortcut_button.setStyleSheet("background-color: rgb(255, 178, 178)")
        self.num_shortcut_button = 0
        self.shortcut_button = []
        self.button_per_row = 3
        self.table_shortcut.cellClicked.connect(self.shortcut_click)

        self.add_app = Add_window(self)
        self.stock_app = Stock_window(self)
        self.finish_app = Finish_window(self)
        self.date_app = DateInfo_window(self)
       
        self.add_button.clicked.connect(self.OpenAddWindow)
        self.remove_button.clicked.connect(self.RemoveSelectedRow)
        self.clear_button.clicked.connect(self.ClearList)
        self.stock_button.clicked.connect(self.OpenStockWindow)
        self.finish_button.clicked.connect(self.FinishState)
        self.calendar.clicked[QtCore.QDate].connect(self.CalendarClicked)
        self.add_shortcut_button.clicked.connect(self.OpenAddShortcut)
        self.remove_shortcut_button.clicked.connect(self.OpenRemoveShortcut)
        self.date = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateWidget)
        self.timer.start(1000) 

        self.timer_webcam = QtCore.QTimer()
        self.timer_webcam.timeout.connect(self.display_video_stream)
        self.timer_webcam.start(30) 

        self.selectedRow = -1
        self.table.clicked.connect(self.updateSelected)

        self.total_price.setText("{:.2f}".format(0.00))
        self.total_price.setAlignment(QtCore.Qt.AlignRight)

        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน', 'ราคารวม']
        header = [ unicode(h, "utf-8") for h in header]
        self.table.setHorizontalHeaderLabels(header)
        header = self.table.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(4, QtGui.QHeaderView.ResizeToContents)


        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน']
        header = [ unicode(h, "utf-8") for h in header]
        self.date_app.table_sales.setHorizontalHeaderLabels(header)
        header = self.date_app.table_sales.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน']
        header = [ unicode(h, "utf-8") for h in header]
        self.date_app.table_add.setHorizontalHeaderLabels(header)
        header = self.date_app.table_add.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        header = ['รหัสสินค้า', 'ชื่อสินค้า', 'ราคาต่อหน่วย', 'จำนวน']
        header = [ unicode(h, "utf-8") for h in header]
        self.date_app.table_stock.setHorizontalHeaderLabels(header)
        header = self.date_app.table_stock.horizontalHeader()
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)

        header = self.table_shortcut.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        header.setResizeMode(2, QtGui.QHeaderView.Stretch)

    def shortcut_click(self, row, column):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        # if self.table_shortcut.item(row,column)
        if row*self.button_per_row+column < len(self.shortcut_button):
            if self.shortcut_button[row*self.button_per_row+column] != 0:
                txtmsg = "Cell " + str(row) + ', ' + str(column)
                msg.setText(txtmsg)
                msg.setWindowTitle("CellClicked")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        self.table_shortcut.clearSelection()

    def OpenAddShortcut(self):
        self.shortcut_app = ShortcutEditor_window(self, action='add')
        self.shortcut_app.show()
        self.shortcut_app.activateWindow()

    def OpenRemoveShortcut(self):
        self.shortcut_app = ShortcutEditor_window(self, action='remove')
        self.shortcut_app.show()
        self.shortcut_app.activateWindow()

    def CalendarClicked(self,date):
        self.date = date

        r = self.date_app.table_sales.rowCount()
        while r > 0:
            self.date_app.table_sales.removeRow(r-1)
            r = self.date_app.table_sales.rowCount()

        r = self.date_app.table_add.rowCount()
        while r > 0:
            self.date_app.table_add.removeRow(r-1)
            r = self.date_app.table_add.rowCount()

        r = self.date_app.table_stock.rowCount()
        while r > 0:
            self.date_app.table_stock.removeRow(r-1)
            r = self.date_app.table_stock.rowCount()

        date_str = str(date.toString('yyyy-MM-dd'))
        data_str = 'สรุปรายการประจำวันที่ ' + date_str
        data_str = unicode(data_str, 'utf-8')
        self.date_app.label_date.setText(data_str)

        date_str = str(date.toString('yyyyMMdd'))
        if date_str in date_data:
            data_str = 'ยอดขายรวม ' + str(date_data[date_str]['Daily Sales']) + ' บาท'
            data_str = unicode(data_str, 'utf-8')
            self.date_app.label_sales.setText(data_str)

            for key, value in date_data[date_str]['Item Sales'].iteritems():
                if value > 0:
                    for items in items_list:
                        if key == items['Barcode']:
                            item_array = [items['Barcode'], items['Item Name'], items['Price'], str(value)]
                            r = self.date_app.table_sales.rowCount()
                            self.date_app.table_sales.insertRow(r)
                            for i in range(len(item_array)):
                                self.date_app.table_sales.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                                if i > 1:
                                    self.date_app.table_sales.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                            break

            for key, value in date_data[date_str]['Stock Adding'].iteritems():
                if value > 0:
                    for items in items_list:
                        if key == items['Barcode']:
                            item_array = [items['Barcode'], items['Item Name'], items['Price'], str(value)]
                            r = self.date_app.table_add.rowCount()
                            self.date_app.table_add.insertRow(r)
                            for i in range(len(item_array)):
                                self.date_app.table_add.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                                if i > 1:
                                    self.date_app.table_add.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                            break

            for key, value in date_data[date_str]['Current Stock'].iteritems():
                for items in items_list:
                    if key == items['Barcode']:
                        item_array = [items['Barcode'], items['Item Name'], items['Price'], str(value)]
                        r = self.date_app.table_stock.rowCount()
                        self.date_app.table_stock.insertRow(r)
                        for i in range(len(item_array)):
                            self.date_app.table_stock.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                            if i > 1:
                                self.date_app.table_stock.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                        break
        else:
            data_str = 'ไม่พบข้อมูล'
            data_str = unicode(data_str, 'utf-8')
            self.date_app.label_sales.setText(data_str)

        self.date_app.show()
        self.date_app.activateWindow()

    def keyPressEvent(self, qKeyEvent):
        if ( qKeyEvent.key() == QtCore.Qt.Key_Return ) or ( qKeyEvent.key() == QtCore.Qt.Key_Enter ): 
            self.FinishState()

    def display_video_stream(self):
        frame = self.BP.webcam_frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame,image_viewer_size)
        image = QImage(frame, frame.shape[1], frame.shape[0], 
                       frame.strides[0], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def FinishState(self):
        self.finish_app.line_total.setText(self.total_price.toPlainText())
        self.finish_app.line_total.setAlignment(QtCore.Qt.AlignRight)
        self.finish_app.line_received.setText('')
        self.finish_app.line_received.setAlignment(QtCore.Qt.AlignRight)
        self.finish_app.line_change.setText("{:.2f}".format(-float(self.total_price.toPlainText())))
        self.finish_app.line_change.setAlignment(QtCore.Qt.AlignRight)
        self.finish_app.show()
        self.finish_app.activateWindow()

    def ClearList(self):
        self.total_price.setText("{:.2f}".format(0.00))
        self.total_price.setAlignment(QtCore.Qt.AlignRight)

        r = self.table.rowCount()
        while r > 0:
            self.table.removeRow(r-1)
            r = self.table.rowCount()

    def OpenAddWindow(self):
        self.add_app.line_barcode.setText('')
        self.add_app.line_name.setText('')
        self.add_app.line_price.setText('')
        self.add_app.line_units.setText('')
        self.add_app.show()
        self.add_app.activateWindow()

    def OpenStockWindow(self):
        self.stock_app.show()
        self.stock_app.activateWindow()

    def updateSelected(self):
        self.selectedRow = self.table.currentRow()

    def RemoveSelectedRow(self):
        if self.selectedRow > -1:
            self.total_price.setText("{:.2f}".format(float(self.total_price.toPlainText()) - float(self.table.item(self.selectedRow, 4).text())))
            self.total_price.setAlignment(QtCore.Qt.AlignRight)

            self.table.removeRow(self.selectedRow)
            self.table.clearSelection()
            self.selectedRow = -1

    def updateWidget(self):
        for l in self.BP.list_item:
            acquired_item = items_info.copy()
            isInList = False
            for items in items_list:
                if l == items['Barcode']:
                    acquired_item['Barcode'] = items['Barcode']
                    acquired_item['Item Name'] = items['Item Name']
                    acquired_item['Price'] = "{:.2f}".format(float(items['Price']))
                    acquired_item['Unit'] = '1'
                    acquired_item['Total'] = "{:.2f}".format( int(acquired_item['Unit'])*float(acquired_item['Price']) )
                    isInList = True

            if isInList:
                r = self.table.rowCount()
                isDuplicate = -1
                for row in range(r):
                    if self.table.item(row, 0).text() == acquired_item['Barcode']:
                        isDuplicate = row
                        num_unit = int(acquired_item['Unit']) + int(self.table.item(row, 3).text())
                        acquired_item['Unit'] = str(num_unit)
                        acquired_item['Total'] = "{:.2f}".format( int(acquired_item['Unit'])*float(acquired_item['Price']) )

                item_array = [acquired_item['Barcode'], acquired_item['Item Name'], acquired_item['Price'], acquired_item['Unit'], acquired_item['Total']]
                if isDuplicate == -1:
                    self.table.insertRow(r)
                    for i in range(len(item_array)):
                        self.table.setItem(r , i, QtGui.QTableWidgetItem(item_array[i]))
                        if i > 1:
                            self.table.item(r, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                else:
                    row = isDuplicate
                    for i in range(len(item_array)):
                        self.table.setItem(row , i, QtGui.QTableWidgetItem(item_array[i]))
                        if i > 1:
                            self.table.item(row, i).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                r = self.table.rowCount()
                total_price = 0.0
                for row in range(r):
                    total_price += float(self.table.item(row, 4).text())
                self.total_price.setText("{:.2f}".format(total_price))
                self.total_price.setAlignment(QtCore.Qt.AlignRight)
        self.BP.list_item = []

if __name__ == "__main__":
    with open('ItemList.csv','r') as f:
        for line in f:
            line_split = line.strip().split(',')
            (barcode,name,price,stock) = line_split
            items = items_info.copy()
            items['Barcode'] = barcode
            items['Item Name'] = unicode(name, "utf-8")
            items['Price'] = price
            items['Stock'] = stock
            items_list.append(items)

    json_data=open('data.json').read()
    date_data = json.loads(json_data)

    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
