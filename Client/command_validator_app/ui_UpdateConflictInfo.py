# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\UpdateConflictInfo.ui',
# licensing of '.\UpdateConflictInfo.ui' applies.
#
# Created: Fri Sep  6 09:31:48 2019
#      by: pyside2-uic  running on PySide2 5.12.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_UpdateConflictInfo(object):
    def setupUi(self, UpdateConflictInfo):
        UpdateConflictInfo.setObjectName("UpdateConflictInfo")
        UpdateConflictInfo.resize(465, 287)
        UpdateConflictInfo.setAcceptDrops(False)
        self.gridLayout = QtWidgets.QGridLayout(UpdateConflictInfo)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(UpdateConflictInfo)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButtonDiscard = QtWidgets.QPushButton(UpdateConflictInfo)
        self.pushButtonDiscard.setObjectName("pushButtonDiscard")
        self.horizontalLayout.addWidget(self.pushButtonDiscard, alignment=QtCore.Qt.AlignHCenter)
        self.pushButtonUpdate = QtWidgets.QPushButton(UpdateConflictInfo)
        self.pushButtonUpdate.setObjectName("pushButtonUpdate")
        self.horizontalLayout.addWidget(self.pushButtonUpdate, alignment=QtCore.Qt.AlignHCenter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(UpdateConflictInfo)
        QtCore.QMetaObject.connectSlotsByName(UpdateConflictInfo)

    def retranslateUi(self, UpdateConflictInfo):
        UpdateConflictInfo.setWindowTitle(QtWidgets.QApplication.translate("UpdateConflictInfo", "Update Conflict Info", None, -1))
        self.tableWidget.horizontalHeaderItem(0).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "frame Index", None, -1))
        self.tableWidget.horizontalHeaderItem(1).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "command Index", None, -1))
        self.tableWidget.horizontalHeaderItem(2).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "old name", None, -1))
        self.tableWidget.horizontalHeaderItem(3).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "use old", None, -1))
        self.tableWidget.horizontalHeaderItem(4).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "new name", None, -1))
        self.tableWidget.horizontalHeaderItem(5).setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "use new", None, -1))
        self.pushButtonDiscard.setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "Discard", None, -1))
        self.pushButtonUpdate.setText(QtWidgets.QApplication.translate("UpdateConflictInfo", "Update", None, -1))


