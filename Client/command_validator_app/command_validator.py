import sys
import os
import re
import shutil
import copy
from functools import partial
import time
from PySide2.QtCore import QCoreApplication, Slot, Qt
from PySide2.QtWidgets import *
from PySide2.QtGui import QColor, QKeySequence
from lxml import etree
#----------
from ui_command_info import Ui_FormCommandInfo
from ui_mainwindow import Ui_mainWindow
from ui_Addpath import Ui_Addpath
from get_enum_member import GetEnumMember
from extended_combobox import ExtendedComboBox
from htoxml.cmdfinder import CmdFinder
#import webgenxml   #not used, read from bspec


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        self.ui.pushButtonGAll.clicked.connect(self.fillinput)
        #self.ui.pushButtonGAll.clicked.connect(lambda : self.ui.tabWidget.setCurrentIndex(1))
        self.ui.pushButtonUpdate.clicked.connect(self.input_goru)

        self.media_path = '' # split by ';'
        self.base_media = '' # end in file /source
        self.media_path2 = '' # end in Source/media
        self.Buf = None 
        self.command_info = []
        self.command_tags = ('DW0_dwlen', 'class', 'def_dwSize', 'index', 'input_dwsize', 'name')
        self.dword_tags = ('NO', 'value', 'class', 'cmdarraysize', 'otherCMD', 'arrayname', 'unmappedstr')
        self.command_filter = {'MI_NOOP_CMD', 'MI_NOOP'}
        self.platform_list = []
        self.ringinfo_path = ''
        self.output_path = ''
        self.command_xml = ''
        self.test_name = ''
        self.platform = ''
        self.frame_num = 0
        self.row_num = 0
        self.workspace = ''
        self.form = FormCommandInfo(self)
        self.Addpath = Addpath(self)
        self.pathlist = self.Addpath.ui.listWidget
        #
        self.last_dir = ''
        self.ui.SelectMediaPath.clicked.connect(self.showAddpath)
        self.ui.SelectRinginfoPath.clicked.connect(partial(self.selectpath,'Ringinfo'))
        self.ui.SelectDDIInputPath.clicked.connect(partial(self.selectpath,'DDIInput'))
        self.ui.lineEditRinginfoPath.textChanged.connect(partial(self.changebg,'Ringinfo'))
        self.ui.lineEditMediaPath.textChanged.connect(partial(self.changebg,'Media'))
        self.ui.lineEditDDIInputPath.textChanged.connect(partial(self.changebg,'DDIInput'))
        self.ui.comboBoxPlatform.currentTextChanged.connect(partial(self.selectbox,'Platform'))
        self.ui.comboBoxComponent.currentTextChanged.connect(partial(self.selectbox,'Component'))


        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.FrameNum_input.setReadOnly(True)
        self.ui.lineEditFrame.setReadOnly(True)
        self.ui.lineEditMediaPath.textChanged.connect(self.update_platform_list)
        #self.ui.lineEditRinginfoPath.textChanged.connect(self.read_test_name)
        self.ui.comboBoxPlatform.currentIndexChanged.connect(self.fillinput_platform)
        self.ui.comboBoxComponent.currentIndexChanged.connect(self.fillinput_component)

        self.ui.lineEditRinginfoPath.editingFinished.connect(partial(self.fillframenum,'Main'))
        self.ui.lineEditDDIInputPath.editingFinished.connect(partial(self.fillframenum,'Input'))
        self.ui.Height_input.editingFinished.connect(partial(self.checkhw, 'Height'))
        self.ui.Width_input.editingFinished.connect(partial(self.checkhw, 'Width'))

        #self.ui.lineEditTestName.setText('encodeHevcCQP')
        self.ui.lineEditMediaPath.setText(r'C:\Users\jiny\gfx\gfx-driver\Source\media;C:\Users\jiny\gfx\gfx-driver\Source\media\media_embargo\agnostic\gen12\hw')
        self.ui.lineEditDDIInputPath.setText(r'C:\projects\github\AutoULTGen\Client\command_validator_app\vcstringinfo\HEVC-VDENC-grits-WP-2125\DDI_Input')
        self.ui.lineEditRinginfoPath.setText(r'C:\projects\github\AutoULTGen\Client\command_validator_app\vcstringinfo\HEVC-VDENC-grits-WP-2125\VcsRingInfo')
        self.ui.lineEditComponent.setText(self.ui.comboBoxComponent.currentText())
        self.ui.lineEditPlatform.setText(self.ui.comboBoxPlatform.currentText())

        self.ui.comboBoxEncFunc = ExtendedComboBox(self.ui.comboBoxEncFunc)
        self.ui.comboBoxResF = ExtendedComboBox(self.ui.comboBoxResF)
        self.ui.comboBoxResTT = ExtendedComboBox(self.ui.comboBoxResTT)
        self.ui.comboBoxRawF = ExtendedComboBox(self.ui.comboBoxRawF)
        self.ui.comboBoxRawTT = ExtendedComboBox(self.ui.comboBoxRawTT)

    @Slot()
    def checkhw(self, name):
        
        if name == 'Height':
            try:
                text = self.ui.Height_input.text()
                if '0x' in text:
                    self.Height = int(text, 16)
                else:
                    self.Height = int(text)
            except ValueError:
                msgBox = QMessageBox()
                msgBox.setText("%s should be int!" %name)
                msgBox.exec_()
                self.ui.Height_input.clear()
        if name == 'Width':
            try:
                text = self.ui.Width_input.text()
                if '0x' in text:
                    self.Width = int(text, 16)
                else:
                    self.Width = int(text)
            except ValueError:
                msgBox = QMessageBox()
                msgBox.setText("%s should be int!" %name)
                msgBox.exec_()



    @Slot()
    def read_test_name(self):
        try:
            # print('read_test_name')
            self.ringinfo_path = self.ui.lineEditRinginfoPath.text()
            cur_dir = os.getcwd()
            for r,d,f in os.walk(self.ringinfo_path):
                os.chdir(r)
                file_list = [file for file in f if re.search('-VcsRingInfo_0_0.txt', file)]
                # print(file_list)
                if file_list:
                    idx = file_list[0].find('-')
                    if idx != -1:
                        self.test_name = file_list[0][:idx]
                        self.ui.lineEditTestName.setText(self.test_name)
                        # print(self.test_name)
            os.chdir(cur_dir)
        except:
            pass


    @Slot()
    def showAddpath(self):
        
        self.Addpath.show()
        self.Addpath.activateWindow()
        self.pathlist.clear()
        if self.ui.lineEditMediaPath.text():
            self.pathlist.addItems(self.ui.lineEditMediaPath.text().split(';'))
    
    @Slot()
    def selectbox(self, name, text):
        if name == 'Platform':
            self.ui.lineEditPlatform.setText(self.ui.comboBoxPlatform.currentText())
        if name == 'Component':
            self.ui.lineEditComponent.setText(self.ui.comboBoxComponent.currentText())
        if name == 'RawTileType':
            if self.ui.comboBoxRawTT.currentText() in self.input_combo_obj.output['_MOS_TILE_TYPE']:
                self.ui.RawTT_value.setText(str(self.input_combo_obj.output['_MOS_TILE_TYPE'][self.ui.comboBoxRawTT.currentText()]))
            else:
                self.ui.RawTT_value.setText('')
        if name == 'ResTileType':
            if self.ui.comboBoxResTT.currentText() in self.input_combo_obj.output['_MOS_TILE_TYPE']:
                self.ui.ResTT_value.setText(str(self.input_combo_obj.output['_MOS_TILE_TYPE'][self.ui.comboBoxResTT.currentText()]))
            else:
                self.ui.ResTT_value.setText('')
        if name == 'RawFormat':
            if self.ui.comboBoxRawF.currentText() in self.input_combo_obj.output['_MOS_FORMAT']:
                self.ui.RawF_value.setText(str(self.input_combo_obj.output['_MOS_FORMAT'][self.ui.comboBoxRawF.currentText()]))
            else:
                self.ui.RawF_value.setText('')
        if name == 'ResFormat':
            if self.ui.comboBoxResF.currentText() in self.input_combo_obj.output['_MOS_FORMAT']:
                self.ui.ResF_value.setText(str(self.input_combo_obj.output['_MOS_FORMAT'][self.ui.comboBoxResF.currentText()]))
            else:
                self.ui.ResF_value.setText('')
        if name == 'EncFunc':
            if self.ui.comboBoxEncFunc.currentText() in self.input_combo_obj.output['tagENCODE_FUNC']:
                self.ui.EncFunc_value.setText(str(self.input_combo_obj.output['tagENCODE_FUNC'][self.ui.comboBoxEncFunc.currentText()]))
            else:
                self.ui.EncFunc_value.setText('')

    @Slot()
    def changebg(self, name, text):
        if name == 'Media':
            self.ui.lineEditMediaPath.setStyleSheet('QLineEdit {background-color: rgb(255, 255, 255);}')
        if name == 'DDIInput':
            self.ui.lineEditDDIInputPath.setStyleSheet('QLineEdit {background-color: rgb(255, 255, 255);}')
        if name == 'Ringinfo':
            self.ui.lineEditRinginfoPath.setStyleSheet('QLineEdit {background-color: rgb(255, 255, 255);}')

    @Slot()
    def fillframenum(self, name):
        if name == 'Input' and self.ui.lineEditDDIInputPath.text():
            Frameset = set()
            for f in os.listdir(self.ui.lineEditDDIInputPath.text()):
                pattern = re.search('^(\d)-0.*DDIEnc_(.*)Params_._Frame', f)
                if pattern:
                    Frameset.add(int(pattern.group(1)))
            if not Frameset:
                msgBox = QMessageBox()
                msgBox.setText("Input path doesn't contain target files!(e.g. 0-0_1_DDIEnc_SlcParams_I_Frame.dat)")
                msgBox.exec_()
            self.FrameNumdiff = min(Frameset) - 0
            self.ui.FrameNum_input.setText(str(len(Frameset)))
        if name == 'Main' and self.ui.lineEditRinginfoPath.text():
            file_list = [file for file in os.listdir(self.ui.lineEditRinginfoPath.text()) if re.search('VcsRingInfo_0_0.txt', file)]
            if len(file_list) > 1:
                frame_no_list = [int(re.search('(\d)-VcsRingInfo_0_0.txt', file).group(1)) for file in file_list]
            elif len(file_list) == 1:
                frame_no_list = [0]
            else:
                msgBox = QMessageBox()
                msgBox.setText("Ringinfo path doesn't contain target files!(e.g. 1-VcsRingInfo_0_0.txt)")
                msgBox.exec_()
            self.ringfilelist = file_list
            numset = set(frame_no_list)
            self.ui.lineEditFrame.setText(str(len(numset)))

        if self.ui.lineEditFrame.text().strip() and self.ui.FrameNum_input.text().strip() and self.ui.lineEditFrame.text() != self.ui.FrameNum_input.text():
            print(self.ui.lineEditFrame.text())
            print(self.ui.FrameNum_input.text())
            msgBox = QMessageBox()
            msgBox.setText("Inconsistent Frame number!")
            msgBox.exec_()


    @Slot()
    def update_platform_list(self):
        self.media_path2 = self.ui.lineEditMediaPath.text().replace('/', '\\').strip().split(';')
        if self.media_path2:
            self.media_path2 = self.media_path2[0]
        idx = self.media_path2.find('\\media\\')
        if idx != -1:
            self.media_path2 = self.media_path2[:idx+7]
        dir = os.getcwd()
        try:
            os.chdir(self.media_path2)
            os.chdir('..\\inc\\common')
            with open('igfxfmid.h', 'r') as fin:
                lines = fin.readlines()
            idx1 = 0
            idx2 = 0
            for idx, line in enumerate(lines):
                if line.strip().find('typedef enum {') != -1:
                    idx1 = idx
                if line.strip().find(' PRODUCT_FAMILY;') != -1:
                    idx2 = idx
                    break
            for idx in range(idx1+1, idx2):
                line = lines[idx]
                if line.find('=') != -1:
                    platform_name = line[:line.find('=')].strip()
                    if platform_name.startswith('IGFX'):
                        self.platform_list.append(platform_name)
                elif line.find(',') != -1:
                    platform_name = line[:line.find(',')].strip()
                    if platform_name.startswith('IGFX'):
                        self.platform_list.append(platform_name)

            self.ui.comboBoxPlatform.clear()
            self.ui.comboBoxPlatform.addItems(self.platform_list)
            print('update platform list according to igfxfmid.h\n')
        except:
            pass

    @Slot()
    def fillinput(self):
        blank = []
        if not self.ui.lineEditRinginfoPath.text():
            self.ui.lineEditRinginfoPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('Ringinfo')
        else:
            self.fillframenum('Main')
        if not self.ui.lineEditDDIInputPath.text():
            self.ui.lineEditDDIInputPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('DDIInput')
        else:
            self.fillframenum('Input')
        if not self.ui.lineEditMediaPath.text():
            self.ui.lineEditMediaPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('Media')
        if blank:
            msgBox = QMessageBox()
            str = ', '.join(blank)
            msgBox.setText("Please fill %s Path!"% str)
            msgBox.exec_()
        else:
            self.read_info_from_ui()
            self.fillcombobox()
            self.checkinputexist()

            self.ui.InputPathText.setText(self.ui.lineEditDDIInputPath.text())
            self.ui.Component_input.setText(self.ui.lineEditComponent.text())
            #self.ui.GUID_input.setText('DXVA2_Intel_LowpowerEncode_HEVC_Main')
            #self.ui.Width_input.setText('256')
            #self.ui.Height_input.setText('192')

            #self.ui.FrameNum_input.setText('1')
            self.ui.tabWidget.setCurrentIndex(1)
    
    def checkinputexist(self):
        self.inputfilename = self.test_name+'Input.dat'
        lines = []
        try:
            with open(os.path.join(self.output_path, self.inputfilename), 'r',  encoding="ISO-8859-1") as fin:
                lines = fin.readlines()
        except FileNotFoundError:
            print('Not Found %s' %self.inputfilename)
            self.ui.pushButtonUpdate.setText('Generate')
            # Keep preset values

        if lines:
            pattern = re.search('''<Header>
Component = ([a-zA-Z0-9_\-]*)
GUID = ([a-zA-Z0-9_\-]*)
Width = ([a-zA-Z0-9_\-]*)
Height = ([a-zA-Z0-9_\-]*)
#([a-zA-Z0-9_\-]*)
RawTileType = ([a-zA-Z0-9_\-]*)
#([a-zA-Z0-9_\-]*)
RawFormat = ([a-zA-Z0-9_\-]*)
#([a-zA-Z0-9_\-]*)
ResTileType = ([a-zA-Z0-9_\-]*)
#([a-zA-Z0-9_\-]*)
ResFormat = ([a-zA-Z0-9_\-]*)
#([a-zA-Z0-9_\-]*)
EncFunc = ([a-zA-Z0-9_\-]*)
FrameNum = ([a-zA-Z0-9_\-]*)
''', ''.join(lines))
            if pattern and len(pattern.groups()) == 15:
                self.ui.Component_input.setText(pattern.group(1))
                if pattern.group(1) != self.ui.lineEditComponent.text():
                    self.ui.Component_input.setStyleSheet('QLineEdit {background-color: rgb(255, 255, 255);}')
                self.ui.GUID_input.setText(pattern.group(2))
                self.ui.Width_input.setText(pattern.group(3))
                self.ui.Height_input.setText(pattern.group(4))
                self.ui.comboBoxRawTT.setCurrentText(pattern.group(5))
                self.ui.comboBoxRawF.setCurrentText(pattern.group(7))
                self.ui.comboBoxResTT.setCurrentText(pattern.group(9))
                self.ui.comboBoxResF.setCurrentText(pattern.group(11))
                self.ui.comboBoxEncFunc.setCurrentText(pattern.group(13))
                self.ui.FrameNum_input.setText(pattern.group(15))
            else:
                self.ui.pushButtonUpdate.setText('Generate')
    @Slot()
    def fillinput_platform(self):
        self.ui.lineEditPlatform.setText(self.ui.comboBoxPlatform.currentText())

    @Slot()
    def fillinput_component(self):
        self.ui.lineEditComponent.setText(self.ui.comboBoxComponent.currentText())


    def fillcombobox(self):

        self.ui.comboBoxEncFunc.currentTextChanged.connect(partial(self.selectbox,'EncFunc'))
        self.ui.comboBoxResF.currentTextChanged.connect(partial(self.selectbox,'ResFormat'))
        self.ui.comboBoxResTT.currentTextChanged.connect(partial(self.selectbox,'ResTileType'))
        self.ui.comboBoxRawF.currentTextChanged.connect(partial(self.selectbox,'RawFormat'))
        self.ui.comboBoxRawTT.currentTextChanged.connect(partial(self.selectbox,'RawTileType'))

        self.input_combo_obj = GetEnumMember(self.base_media)
        self.input_combo_obj.read_files()
        #self.ui.comboBoxEncFunc = ExtendedComboBox(self.ui.comboBoxEncFunc)
        self.ui.comboBoxEncFunc.addItems([''] + list(self.input_combo_obj.output['tagENCODE_FUNC'].keys()))
        self.ui.comboBoxResF.addItems([''] + list(self.input_combo_obj.output['_MOS_FORMAT'].keys()))
        self.ui.comboBoxResTT.addItems([''] + list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()))
        self.ui.comboBoxRawF.addItems([''] + list(self.input_combo_obj.output['_MOS_FORMAT'].keys()))
        self.ui.comboBoxRawTT.addItems([''] + list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()))

    @Slot()
    def show_command_table(self, item, column = 0):
        self.form.current_item = item
        f_frame = False
        if item.data(2, 1):
            idx = item.data(2, 1)
            if idx['cmd_idx'] == 'all':
                self.form.current_frame = self.command_info[idx['frame_idx']]
                self.form.current_command = 'all'
                command_list = self.command_info[idx['frame_idx']]
                f_frame = True
            else:
                self.form.current_frame = self.command_info[idx['frame_idx']]
                self.form.current_command = self.command_info[idx['frame_idx']][idx['cmd_idx']]
                command_list = [self.command_info[idx['frame_idx']][idx['cmd_idx']]]
                if 'dword_idx' in idx:
                    command_item = item.parent()
                else:
                    command_item = item

            table = self.form.ui.tableWidgetCmd
            table.clearContents()
            self.form.row_command_map = []
            table.setRowCount(0)
            i_row = 0
            ##print(f_frame)
            for command_idx, command in enumerate(command_list):
                ##print('command ' + str(command_idx) + '\n')
                QCoreApplication.processEvents()
                if f_frame:
                    command_item = item.child(command_idx)

                if i_row >= table.rowCount():
                    table.insertRow(i_row)
                table.setItem(i_row, 0, QTableWidgetItem(command['name']))
                for dword_idx, dword in enumerate(command['dwords']):
                    ##print('dword ' + str(dword_idx) + '\n')
                    #if 'unmappedstr' in dword and dword['unmappedstr']:
                    #    continue
                    if i_row >= table.rowCount():
                        table.insertRow(i_row)
                    table.setItem(i_row, 1, QTableWidgetItem('dword' + dword['NO']))
                    if not dword['fields']:
                        if dword['value']:
                            table.setItem(i_row, 3, QTableWidgetItem(dword['value']))
                        if dword['arrayname']:
                            table.setItem(i_row, 2, QTableWidgetItem(dword['arrayname']))
                        if dword['unmappedstr']:
                            table.setItem(i_row, 3, QTableWidgetItem(dword['unmappedstr']))
                        self.form.row_command_map.append(
                            {'frame_idx': idx['frame_idx'], 'command_idx': command['index'], 'dword_idx': dword_idx})
                        i_row += 1

                    dword_item = command_item.child(dword_idx)

                    for field in dword['fields']:
                        if field['field_name'].startswith('Obj'):
                            if i_row >= table.rowCount():
                                table.insertRow(i_row)
                            table.setItem(i_row, 1, QTableWidgetItem('dword' + dword['NO'] + '_' + field['field_name']))
                            for obj_field in field['obj_fields']:
                                if obj_field['obj_field_name'].startswith('Reserved') and self.form.ui.checkBoxReserved.isChecked():
                                    continue
                                if i_row >= table.rowCount():
                                    table.insertRow(i_row)
                                table.setItem(i_row, 2, QTableWidgetItem(obj_field['obj_field_name']))
                                checkBox = QCheckBox()
                                if (not obj_field['obj_field_name'].startswith('Reserved')) and command_item.checkState(0) == Qt.CheckState.Checked and dword_item.checkState(0) == Qt.CheckState.Checked:
                                    checkBox.setCheckState(Qt.CheckState.Checked)
                                # checkBox.stateChanged.connect(self.check_box_change)
                                table.setCellWidget(i_row, 5, checkBox)
                                if self.form.mode == 'bin':
                                    table.setItem(i_row, 3, QTableWidgetItem(bin(int(obj_field['default_value'], 16))))
                                    table.setItem(i_row, 4, QTableWidgetItem(bin(int(obj_field['value'], 16))))
                                    table.setItem(i_row, 7, QTableWidgetItem(bin(int(obj_field['min_value'], 16))))
                                    table.setItem(i_row, 8, QTableWidgetItem(bin(int(obj_field['max_value'], 16))))
                                elif self.form.mode == 'dec':
                                    table.setItem(i_row, 3, QTableWidgetItem(str(int(obj_field['default_value'], 16))))
                                    table.setItem(i_row, 4, QTableWidgetItem(str(int(obj_field['value'], 16))))
                                    table.setItem(i_row, 7, QTableWidgetItem(str(int(obj_field['min_value'], 16))))
                                    table.setItem(i_row, 8, QTableWidgetItem(str(int(obj_field['max_value'], 16))))
                                else:
                                    table.setItem(i_row, 3, QTableWidgetItem(obj_field['default_value']))
                                    table.setItem(i_row, 4, QTableWidgetItem(obj_field['value']))
                                    table.setItem(i_row, 7, QTableWidgetItem(obj_field['min_value']))
                                    table.setItem(i_row, 8, QTableWidgetItem(obj_field['max_value']))
                                if 'Address' in field:
                                    table.setItem(i_row, 6, QTableWidgetItem(obj_field['Address']))
                                else:
                                    table.setItem(i_row, 6, QTableWidgetItem('N'))
                                table.item(i_row, 3).setFlags(Qt.NoItemFlags)
                                table.setItem(i_row, 9, QTableWidgetItem(obj_field['bitfield_l']))
                                table.setItem(i_row, 10, QTableWidgetItem(obj_field['bitfield_h']))
                                table.item(i_row, 9).setFlags(Qt.NoItemFlags)
                                table.item(i_row, 10).setFlags(Qt.NoItemFlags)
                                self.form.row_command_map.append(
                                    {'frame_idx': idx['frame_idx'], 'command_idx': command['index'],
                                     'dword_idx': dword_idx})
                                i_row += 1
                            continue

                        if field['field_name'].startswith('Reserved') and self.form.ui.checkBoxReserved.isChecked():
                            continue

                        if i_row >= table.rowCount():
                            table.insertRow(i_row)
                        table.setItem(i_row, 2, QTableWidgetItem(field['field_name']))
                        checkBox = QCheckBox()
                        if (not field['field_name'].startswith('Reserved')) and command_item.checkState(0) == Qt.CheckState.Checked and dword_item.checkState(0) == Qt.CheckState.Checked and field['CHECK'] == 'Y':
                            checkBox.setCheckState(Qt.CheckState.Checked)
                        # checkBox.stateChanged.connect(self.check_box_change)
                        table.setCellWidget(i_row, 5, checkBox)
                        if self.form.mode == 'bin':
                            table.setItem(i_row, 3, QTableWidgetItem(bin(int(field['default_value'], 16))))
                            table.setItem(i_row, 4, QTableWidgetItem(bin(int(field['value'], 16))))
                            table.setItem(i_row, 7, QTableWidgetItem(bin(int(field['min_value'], 16))))
                            table.setItem(i_row, 8, QTableWidgetItem(bin(int(field['max_value'], 16))))
                        elif self.form.mode == 'dec':
                            table.setItem(i_row, 3, QTableWidgetItem(str(int(field['default_value'], 16))))
                            table.setItem(i_row, 4, QTableWidgetItem(str(int(field['value'], 16))))
                            table.setItem(i_row, 7, QTableWidgetItem(str(int(field['min_value'], 16))))
                            table.setItem(i_row, 8, QTableWidgetItem(str(int(field['max_value'], 16))))
                        else:
                            table.setItem(i_row, 3, QTableWidgetItem(field['default_value']))
                            table.setItem(i_row, 4, QTableWidgetItem(field['value']))
                            table.setItem(i_row, 7, QTableWidgetItem(field['min_value']))
                            table.setItem(i_row, 8, QTableWidgetItem(field['max_value']))
                        table.item(i_row, 3).setFlags(Qt.NoItemFlags)
                        if 'Address' in field:
                            table.setItem(i_row, 6, QTableWidgetItem(field['Address']))
                        else:
                            table.setItem(i_row, 6, QTableWidgetItem('N'))
                        table.setItem(i_row, 9, QTableWidgetItem(field['bitfield_l']))
                        table.item(i_row, 9).setFlags(Qt.NoItemFlags)
                        table.setItem(i_row, 10, QTableWidgetItem(field['bitfield_h']))
                        table.item(i_row, 10).setFlags(Qt.NoItemFlags)
                        self.form.row_command_map.append({'frame_idx': idx['frame_idx'],'command_idx': command['index'], 'dword_idx': dword_idx})
                        i_row += 1

            table.resizeColumnsToContents()
            table.resizeRowsToContents()

    @Slot()
    def show_command_info(self):
        # self.form.ui = Form()
        # self.form.ui.setupUi(self.form)
        self.form.setWindowTitle(self.test_name)
        tree = self.form.ui.treeWidgetCmd
        header = self.form.ui.treeWidgetCmd.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        
        tree.itemDoubleClicked.connect(self.form.save)
        tree.itemDoubleClicked.connect(self.show_command_table)
        tree.itemClicked.connect(self.form.save)
        tree.itemClicked.connect(self.show_command_table)
        tree.itemChanged.connect(self.form.update_tree_checkstate)
        # tree.itemChanged.connect(self.show_command_table)
        test = QTreeWidgetItem(tree)
        test.setText(0, self.test_name)
        for frame_idx in range(len(self.command_info)):
            ##print('frame idx:' + str(frame_idx))
            frame = QTreeWidgetItem(test)
            frame.setText(0, 'frame' + str(frame_idx))
            frame.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': 'all'})
            for command_idx, command in enumerate(self.command_info[frame_idx]):
                # #print(command_idx)
                ##print('command idx:' + str(command_idx))
                cmd = QTreeWidgetItem(frame)
                cmd.setText(0, command['name'])
                if command['name'] in self.command_filter:
                    cmd.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    cmd.setCheckState(0, Qt.CheckState.Checked)
                cmd.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': command_idx})
                for dword_idx in range(len(command['dwords'])):
                    dword = QTreeWidgetItem(cmd)
                    #print('dword_idx' + str(dword_idx))
                    dword.setText(0, 'dword' + command['dwords'][dword_idx]['NO'])
                    if command['name'] in self.command_filter:
                        dword.setCheckState(0, Qt.CheckState.Unchecked)
                    else:
                        dword.setCheckState(0, Qt.CheckState.Checked)
                    dword.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': command_idx, 'dword_idx': dword_idx})
                    for field_obj in command['dwords'][dword_idx]['fields']:
                        if 'field_name' in field_obj:
                            field = QTreeWidgetItem(dword)
                            field.setText(0, field_obj['field_name'])
        self.form.show()
        self.form.activateWindow()

    def parse_command_file(self):
        #print('begin parse command file')
        self.ui.logBrowser.append('Begin parse vcs ring info\n')
        self.ui.logBrowser.append('It may take about 30 seconds to finish parsing.\n')
        QCoreApplication.processEvents()
        #self.ringinfo_path = self.ringinfo_path.strip()
        #if self.ringinfo_path[-1] != '\\':
        #    self.ringinfo_path = self.ringinfo_path + '\\'

        ## read xml from file: uncomment this to see the original output
        #self.command_xml = os.path.join(self.ringinfo_path, 'mapringinfo.xml')


        #init
        start = time.clock()
        #self.obj = CmdFinder(self.media_path, 12, self.ringinfo_path)
        if not self.Buf:
            self.Buf = self.obj.h2xml()
        self.obj.extractfull()
        if not self.obj.Frame_Num:
            msgBox = QMessageBox()
            msgBox.setText("Ringinfo path doesn't contain target files!(e.g. 1-VcsRingInfo_0_0.txt)")
            msgBox.exec_()
        self.obj.updatexml()
        #self.obj.writexml(self.output_path)
        elapsed = (time.clock() - start)
        print("Total Time used:",elapsed)
        #
        #print('end parse command file')
        #self.ui.logBrowser.append("Total Time used:"+ str(elapsed) +'\n')
        #self.ui.logBrowser.append('End parse vcs ring info\n')
        #self.ui.logBrowser.append('Save xml in '+ self.ringinfo_path + '\n')
        #self.ui.logBrowser.append('Save original mapringinfo.xml\n')

    def read_info_from_ui(self):
        if self.ui.lineEditComponent.text():
            self.component = self.ui.lineEditComponent.text()
        else:
            self.component = self.ui.comboBoxComponent.currentText()
        if self.ui.lineEditPlatform.text():
            self.platform = self.ui.lineEditPlatform.text()
        else:
            self.platform = self.ui.comboBoxPlatform.currentText()
        self.test_name = self.ui.lineEditTestName.text()
        #self.source_path = self.ui.lineEditMediaPath.text().replace('/', '\\').strip()
        self.media_path = self.ui.lineEditMediaPath.text().split(';')
        path = os.path.normpath(self.media_path[0])
        path_list = path.split(os.sep)
        base_media = path_list[0]
        for i in path_list[1:]:
            base_media = os.path.join(base_media, i)
            if i == 'Source':
                break
        self.base_media = base_media.replace(':', ':\\')

        if self.component in ('vp', 'VP'):
            self.workspace = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\vp\test\test_data')
        else:
            self.workspace = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\codec\test\test_data')
        
        self.output_path = os.path.join(self.workspace, self.test_name)
        # in case user left this folder, with '_x.h' header file
        base_folder = os.path.join(self.base_media, r'media\media_embargo\agnostic\gen12\hw')
        self.pathlist.clear()
        if self.ui.lineEditMediaPath.text():
            self.pathlist.addItems(self.ui.lineEditMediaPath.text().split(';'))
        if not self.pathlist.findItems(base_folder, Qt.MatchExactly):
            self.pathlist.addItem(base_folder)
            self.ui.lineEditMediaPath.setText(self.ui.lineEditMediaPath.text() + ';' + base_folder)

        # create single folder for each testname
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        self.ui.logBrowser.append('All the following output will be saved in workspace:\n%s\n'  %self.output_path)
        self.ringinfo_path = self.ui.lineEditRinginfoPath.text()

        

    def read_command_info_from_xml(self):
        # read from xml file 
        #tree = etree.parse(self.command_xml)
        #root = tree.getroot()[0]
        #for frame in tree:

        # read from xml elem
        tree = self.obj.TestName
        frames = []
        
        for frame in tree.findall(".//Frame"):
            ##print(frame.tag)
            commands = []
            # self.test_class_name = root.get('name')
            for command in frame:
                info = {'dwords': []}
                for command_tag in self.command_tags:
                    info[command_tag] = command.get(command_tag)
                if info['name'] in self.command_filter:
                    info['check'] = 'N'
                else:
                    info['check'] = 'Y'
                # f_other_cmd = False

                for dword in command:
                    # dword_t = {}
                    # dword_t['value'] = dword.get('value')
                    # dword_t['NO'] = dword.get('NO')
                    # if dword.get('otherCMD'):
                    #     f_other_cmd = True
                    #     other_cmd = {'name': dword.get('otherCMD'), 'class': command.get('class'), 'dwords': []}
                    #     dword_t['NO'] = '0'
                    #     for field in dword:
                    #         dword_t[field.tag] = {}
                    #         if field.tag.startswith('Obj'):
                    #             for obj_field in field:
                    #                 dword_t[field.tag][obj_field.tag] = {}
                    #                 for key, value in obj_field.items():
                    #                     dword_t[field.tag][obj_field.tag][key] = value
                    #         else:
                    #             for key, value in field.items():
                    #                 dword_t[field.tag][key] = value
                    #     other_cmd['dwords'].append(dword_t)
                    #     commands.append(other_cmd)
                    # if not dword_t['value']:
                    #     dword_t['unmappedstr'] = dword.get('unmappedstr')
                    dword_info = {'fields': []}
                    for dword_tag in self.dword_tags:
                        dword_info[dword_tag] = dword.get(dword_tag)

                    if dword_info['NO'] == '0':
                        dword_info['check'] = 'Y'
                    else:
                        dword_info['check'] = 'Y'
                    # if dword_info['otherCMD']:
                    #     f_other_cmd = True

                    for field in dword:
                        field_info = {'field_name': field.tag}
                        if field.tag.startswith('Obj'):
                            field_info = {'value': field.get('value'), 'obj_fields': [], 'field_name': field.tag}
                            for obj_field in field:
                                obj_field_info = {'obj_field_name': obj_field.tag}
                                for key, value in obj_field.items():
                                    obj_field_info[key] = value
                                if 'default_value' in obj_field_info:
                                    obj_field_info['value'] = obj_field_info['default_value']
                                field_info['obj_fields'].append(obj_field_info)
                        else:
                            for key, value in field.items():
                                field_info[key] = value
                            if 'default_value' in field_info:
                                field_info['value'] = field_info['default_value']
                        dword_info['fields'].append(field_info)
                    info['dwords'].append(dword_info)
                # if not f_other_cmd:
                commands.append(info)
            # for command_idx, command in enumerate(commands):
            #     command['index'] = command_idx
            frames.append(commands)
        self.command_info = frames
        self.dw_length_check()
        #self.ui.lineEditFrame.setText(str(len(frames)))

        #self.ui.logBrowser.append('Read infomation from mapringinfo.xml\n')
        self.form.info = self.command_info
        ##print(self.command_info)
        self.show_command_info()
        # self.update_cmd_list()


    def dw_length_check(self):
        s = ''
        for frame_idx, frame in enumerate(self.command_info):
            for command_idx, command in enumerate(frame):
                # DW0_dwlen = item_text_to_dec(command['input_dwsize'])
                input_dwsize = 0
                if 'input_dwsize' in command and command['input_dwsize']:
                    input_dwsize = item_text_to_dec(command['input_dwsize'])
                if 'def_dwsize' in command and command['def_dwSize']:
                    def_dwsize = item_text_to_dec(command['def_dwSize'])
                if command['dwords']:
                    last_dword_no = command['dwords'][-1]['NO']
                    if last_dword_no.find('_') != -1:
                        idx = last_dword_no.rfind('_')
                        last_dword_no = last_dword_no[idx + 1:]
                    last_dword_no = int(last_dword_no)
                    # #print(last_dword_no)
                    # #print(input_dwsize)
                    ##print(command['input_dwsize'])
                    if last_dword_no and input_dwsize and last_dword_no > input_dwsize:
                        s = 'frame ' + str(frame_idx) + ' command ' + str(command_idx) + ' ' + command['name'] + 'wrong dword length. \n'
                        s = s + 'Suggest ' + str(hex(last_dword_no)) + ' intstead\n\n'
        if s:
            self.show_message(s, 'Error')


    def show_message(self, inf, title):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setInformativeText(inf)
        msgBox.exec_()

    def split_dword(self):
        for frame_idx, frame in enumerate(self.command_info):
            for cmd_idx, cmd in enumerate(frame):
                for dword_idx, dword in enumerate(cmd['dwords']):
                    if dword['NO'].find('_') != -1:
                        ##print(dword_idx)
                        ##print(dword['NO'])
                        idx = dword['NO'].find('_')
                        l = dword['NO'][:idx]
                        r = dword['NO'][idx+1:]
                        cmd['dwords'][dword_idx]['NO'] = l
                        next_dword = copy.deepcopy(dword)
                        next_dword['NO'] = r
                        next_dword['value'] = '0x' + dword['value'][10:]
                        if next_dword['value'] == '0x':
                            next_dword['value'] = '0x0'
                        dword['value'] = dword['value'][:10]
                        split_field_idx = -1
                        for field_idx, field in enumerate(dword['fields']):
                            if int(field['bitfield_h'])> 31 and int(field['bitfield_l']) <= 31:
                                split_field_idx = field_idx
                                break
                        if split_field_idx >= 0:
                            dword['fields'][split_field_idx]['bitfield_h'] = '31'
                            dword['fields'] = dword['fields'][:split_field_idx + 1]
                            dword['fields'][split_field_idx]['have_following'] = 'Y'
                            next_dword['fields'][split_field_idx]['bitfield_l'] = '32'
                            next_dword['fields'] = next_dword['fields'][split_field_idx:]
                            next_dword['fields'][0]['have_precursor'] = 'Y'
                            ##print('have_precursor')
                            for field in next_dword['fields']:
                                field['bitfield_l'] = str(int(field['bitfield_l']) - 32)
                                field['bitfield_h'] = str(int(field['bitfield_h']) - 32)
                            len1 = int(dword['fields'][split_field_idx]['bitfield_h']) - int(dword['fields'][split_field_idx]['bitfield_l'])
                            len1 = len1//4
                            if dword['fields'][split_field_idx]['default_value'] != 0:
                                dword['fields'][split_field_idx]['default_value'] = dword['fields'][split_field_idx]['default_value'][:2+len1]
                                dword['fields'][split_field_idx]['value'] = dword['fields'][split_field_idx]['default_value']
                                dword['fields'][split_field_idx]['min_value'] = dword['fields'][split_field_idx]['default_value']
                                dword['fields'][split_field_idx]['max_value'] = dword['fields'][split_field_idx]['default_value']
                                next_dword['fields'][0]['default_value'] = '0x' + next_dword['fields'][0]['default_value'][2+len1:]
                                next_dword['fields'][0]['value'] = next_dword['fields'][0]['default_value']
                                next_dword['fields'][0]['min_value'] = next_dword['fields'][0]['default_value']
                                next_dword['fields'][0]['max_value'] = next_dword['fields'][0]['default_value']
                        cmd['dwords'].insert(dword_idx+1, next_dword)

    @Slot()
    def generate_xml(self):
        if not self.command_info:
            pass
        self.split_dword()
        lines = ['<?xml version="1.0"?>\n']
        lines.append('<' + self.test_name + '>\n')
        lines.append('  <Platform name="' + self.platform + '">\n')
        for frame_idx, frame in enumerate(self.command_info):
            # #print('frame' + str(frame_idx))
            lines.append('    <Frame NO="' + str(frame_idx) + '">\n')
            for cmd_idx, cmd in enumerate(frame):
                # #print('cmd' + str(cmd_idx))
                s_cmd = '      <CMD'
                for key, value in cmd.items():
                    if key != 'dwords' and value:
                        s_cmd = s_cmd + ' ' + key + '="' + str(value) + '"'
                s_cmd  = s_cmd + '>\n'
                lines.append(s_cmd)
                # lines.append('      <CMD index="' + str(cmd_idx) + '" name="' + cmd['name'] + '" class="' + cmd['class'] + '">\n ')
                for dword_idx, dword in enumerate(cmd['dwords']):
                    s_dword = '        <dword'
                    for key, value in dword.items():
                        if key != 'fields' and value:
                            s_dword = s_dword + ' ' + key + '="' + str(value) + '"'
                    s_dword = s_dword + '>\n'
                    lines.append(s_dword)

                    for field in dword['fields']:
                        if field['field_name'].startswith('Obj'):
                            for obj_field in field['obj_fields']:
                                #if field['obj_fields'].startswith('Reserve'):
                                #    continue
                                s_field = '          <' + obj_field['obj_field_name']
                                for key, value in obj_field.items():
                                    if key != 'obj_field_name':
                                        s_field = s_field + ' ' + key + '="' + str(value) + '"'
                                s_field = s_field + '/>\n'
                                lines.append(s_field)
                            break
                        if 'CHECK' in field and field['CHECK'] == 'Y':
                        # if not field['field_name'].startswith('Reserve'):
                            s_field = '          <' + field['field_name']
                            for key, value in field.items():
                                if key != 'field_name':
                                    s_field = s_field + ' ' + key + '="' + str(value) + '"'
                            s_field = s_field + '/>\n'
                            lines.append(s_field)
                    lines.append('        </dword>\n')
                lines.append('      </CMD>\n')
            lines.append('    </Frame>\n')
        lines.append('  </Platform>\n')
        lines.append('</' + self.test_name + '>\n')
        file_name = self.test_name + '_reference.xml'
        with open(self.output_path + '\\' + file_name, 'w') as fout:
            fout.writelines(lines)
        self.ui.logBrowser.append('Generating modified command xml' + self.output_path + '\\' + file_name + '\n')
        self.show_message('Generating modified command xml' + self.output_path + '\\' + file_name + '\n', '')

    @Slot()
    def selectpath(self, name):
        #open file dialog and display directory in the text edit area
        dialog = QFileDialog(self)
        #dialog.setFileMode(QFileDialog.AnyFile)
        #dialog.setOptions(QFileDialog.DontUseNativeDialog)
        if self.last_dir:
            dir = dialog.getExistingDirectory(self, "Select %s Directory" % name,
                                           self.last_dir) 
        else:
            dir = dialog.getExistingDirectory(self, "Select %s Directory" % name,
                                           "/home")
        self.last_dir = dir
        if name == 'Media':
            self.ui.lineEditMediaPath.setText(dir)
        if name == 'DDIInput':
            self.ui.lineEditDDIInputPath.setText(dir)
            self.fillframenum('Input')
        if name == 'Ringinfo':
            self.ui.lineEditRinginfoPath.setText(dir)
            self.fillframenum('Main')

    @Slot()
    def input_goru(self):
        # click OK, generate xml header
        #self.read_info_from_ui()
        
        self.Component = self.ui.Component_input.text().strip()
        self.GUID = self.ui.GUID_input.text().strip()
        self.Width = self.ui.Width_input.text().strip()
        self.Height = self.ui.Height_input.text().strip()
        self.FrameNum = self.ui.FrameNum_input.text().strip()
        self.inputpath = self.ui.InputPathText.text().strip()
        self.RawTileType = self.ui.RawTT_value.text().strip()
        self.RawFormat = self.ui.RawF_value.text().strip()
        self.ResTileType = self.ui.ResTT_value.text().strip()
        self.ResFormat = self.ui.ResF_value.text().strip()
        self.EncFunc = self.ui.EncFunc_value.text().strip()
        self.update_test_code()
        # get real Frame Number according to input files
        self.cpfiles()
        
        if not (self.Component and self.GUID and self.Width and self.Height and self.inputpath and self.RawTileType and self.RawFormat and self.ResTileType and 
                self.ResFormat and self.EncFunc):
            msgBox = QMessageBox()
            msgBox.setText("Please don't leave blank!")
            msgBox.exec_()
        else:
            # combine input files and parameters
            self.combine()
            self.ui.logBrowser.append("Generate input file: %s\n" %self.inputfilename)
            #pop out message box
            #msgBox = QMessageBox()
            #msgBox.setText("The input file has been generated.")
            #msgBox.exec_()


            # build CMDFinder obj
            if self.Buf:
                self.obj = CmdFinder(self.media_path, 12, self.ringinfo_path, self.Buf, self.output_path)
            else:
                self.obj = CmdFinder(self.media_path, 12, self.ringinfo_path, self.Buf, self.output_path)

            self.parse_command_file()
            self.read_command_info_from_xml()
            self.ui.tabWidget.setCurrentIndex(0)
            self.form.showcmdlist()
        
    
    @Slot()
    def cpfiles(self):
        l = [self.inputpath, self.ringinfo_path]
        for i in l:
            dstdir = os.path.join(self.output_path, os.path.basename(i))
            shutil.rmtree(dstdir, ignore_errors=True)
            if not os.path.exists(dstdir):
                os.makedirs(dstdir) # create directories, raise an error if it already exists
            for f in os.listdir(i):
                full_f = os.path.join(i, f)
                shutil.copy(full_f, dstdir)

    @Slot()
    def reject(self):
        # click cancel, exit
        sys.exit(app.exec_())
        

    def combine(self):
        #combine ddi_input text files and add header infomation
        
        with open(os.path.join(self.output_path, self.inputfilename),'w') as wfd:
            #wfd.write('<Header Component=%s  GUID=%s Width=%s Height=%s OutputFormat=%s>\n' % (self.Component, self.GUID, self.Width, self.Height, self.OutputFormat))
            wfd.write(f'''<Header>
Component = {self.Component}
GUID = DXVA2_Intel_LowpowerEncode_HEVC_Main
Width = {self.Width}
Height = {self.Height}
#{self.ui.comboBoxRawTT.currentText()}
RawTileType = {self.RawTileType}
#{self.ui.comboBoxRawF.currentText()}
RawFormat = {self.RawFormat}
#{self.ui.comboBoxResTT.currentText()}
ResTileType = {self.ResTileType}
#{self.ui.comboBoxResF.currentText()}
ResFormat = {self.ResFormat}
#{self.ui.comboBoxEncFunc.currentText()}
EncFunc = {self.EncFunc}
FrameNum = {self.FrameNum}
''')
            #wfd.write('</Header>')
             
            for f in os.listdir(self.inputpath):
                pattern = re.search('^(\d)-0_(\d)?.*DDIEnc_(.*)Params_._Frame', f)
                
                if pattern:
                    length = len(pattern.groups())
                    FrameNo = str(int(pattern.group(1))-self.FrameNumdiff)
                    ParaGroup = pattern.group(length)
                    if length == 3:
                        slcindex = pattern.group(2)
                        wfd.write('<Frame No=%s  Param=%s Index=%s>\n' % (FrameNo, ParaGroup, slcindex))
                    else:
                        wfd.write('<Frame No=%s  Param=%s >\n' % (FrameNo, ParaGroup))
                    with open(os.path.join(self.inputpath, f), 'r') as file:
                        content = file.readlines()
                        new_content = []
                        for line in content:
                            clean_line = line.replace('\00', '')
                            new_content.append(clean_line)
                    wfd.writelines(new_content)
                    #wfd.write('</Frame>\n')

    def update_test_code(self):
        self.update_integrated_test_cpp()
        self.update_integrated_test_cfg_cpp()
        self.update_ult_rc()
        self.update_resource_h()

    def update_integrated_test_cpp(self, component='encode'):
        try:
            if component == 'encode':
                f_integrated_cpp = self.workspace[:-9] + 'encode_integrated_test.cpp'
                with open(f_integrated_cpp, 'r') as fin:
                    lines = fin.readlines()

                f_find = False
                new_line = 'TEST_CASE_DEFINE(MediaEncodeItTest, ' + self.capitalize_word(self.test_name) + ')\n'
                for line in lines:
                    if line.find(new_line) != -1:
                        return
                for idx, line in enumerate(lines):
                    if line.strip().startswith('TEST_CASE_DEFINE'):
                        f_find = True
                    elif f_find and not line.strip():
                        lines.insert(idx, new_line)
                        break
                if not f_find:
                    lines.append(new_line)

                with open(f_integrated_cpp, 'w') as fout:
                    fout.writelines(lines)
        except:
            self.show_message('update encode_integrated_test.cpp error', 'error')

    def update_integrated_test_cfg_cpp(self, component='encode'):
        try:
            if component == 'encode':
                f_integrated_cfg_cpp = self.workspace[:-9] + 'encode_integrated_test_cfg.cpp'
                with open(f_integrated_cfg_cpp, 'r') as fin:
                    lines = fin.readlines()
                s0 = '    {"' + self.capitalize_word(self.test_name) + '",' + ' ' * (20 - len(self.test_name)) + '{   IDR_' + self.test_name.upper() + '_REFERENCE,\n'
                for line in lines:
                    if line.find(s0) != -1:
                        return
                newlines = []
                newlines.append('    {"' + self.capitalize_word(self.test_name) + '",' + ' ' * (20 - len(self.test_name)) + '{   IDR_' + self.test_name.upper() + '_REFERENCE,\n')
                newlines.append('                                IDR_' + self.test_name.upper() + '_INPUT,\n')
                newlines.append('                                {"' + self.platform + '"},\n')
                newlines.append('                                ' + self.GUID + '\n')
                newlines.append('                            }\n')
                newlines.append('    }\n')
                newlines.append('};\n')
                f_find = False
                for idx, line in enumerate(lines):
                    if line.strip() == '};':
                        f_find = True
                        newlines = lines[:idx] + newlines
                        if newlines[idx-1].strip() == '}':
                            newlines[idx-1] = '    },\n'
                if f_find:
                    with open(f_integrated_cfg_cpp, 'w') as fout:
                        fout.writelines(newlines)
        except:
            self.show_message('update encode_integrated_test_cfg.cpp error', 'error')

    def update_ult_rc(self, component='encode'):
        try:
            if component == 'encode':
                f_ult_rc = self.workspace + '\\media_driver_codec_ult.rc'
                with open(f_ult_rc, 'r') as fin:
                    lines = fin.readlines()
                s0 = 'IDR_' + self.test_name.upper() + '_REFERENCE' + ' ' * (31 - len(self.test_name)) + 'TEST_DATA     "' + self.test_name + '/' + self.capitalize_word(self.test_name) + 'Reference.xml"\n'
                for line in lines:
                    if line.find(s0) != -1:
                        return
                while not lines[-1].strip():
                    lines = lines[:-1]
                if lines[-1][-1] != '\n':
                    lines.append('\n')
                lines.append('IDR_' + self.test_name.upper() + '_REFERENCE' + ' ' * (31 - len(self.test_name)) + 'TEST_DATA     "' + self.test_name + '/' + self.capitalize_word(self.test_name) + 'Reference.xml"\n')
                lines.append('IDR_' + self.test_name.upper() + '_INPUT' + ' ' * (35 - len(self.test_name)) + 'TEST_DATA     "' + self.test_name + '/' + self.capitalize_word(self.test_name) + 'Input.dat"\n')
                with open(f_ult_rc, 'w') as fout:
                    fout.writelines(lines)
        except:
            self.show_message('update media_driver_codec_ult.rc error', 'error')

    def update_resource_h(self, component='encode'):
        try:
            if component == 'encode':
                f_resource_h = self.workspace + '\\resource.h'
                with open(f_resource_h, 'r') as fin:
                    lines = fin.readlines()
                s0 = '#define IDR_' + self.test_name.upper() + '_REFERENCE' + ' ' * (33 - len(self.test_name))
                for line in lines:
                    if line.find(s0) != -1:
                        return
                while not lines[-1].strip():
                    lines = lines[:-1]
                if lines:
                    last_num = int(lines[-1].strip().split(' ')[-1])
                else:
                    last_num = 100
                if lines[-1][-1] != '\n':
                    lines.append('\n')
                last_num += 1
                lines.append('#define IDR_' + self.test_name.upper() + '_REFERENCE' + ' ' * (33 - len(self.test_name)) + str(last_num) + '\n')
                last_num += 1
                lines.append('#define IDR_' + self.test_name.upper() + '_INPUT' + ' ' * (37 - len(self.test_name)) + str(last_num) + '\n')
                with open(f_resource_h, 'w') as fout:
                    fout.writelines(lines)
        except:
            self.show_message('update resource.h error', 'error')

    def capitalize_word(self, s):
        if s:
            return s[0].upper() + s[1:]
        else:
            return s

class FormCommandInfo(QWidget):
    def __init__(self, main_window):
        super(FormCommandInfo, self).__init__()
        self.ui = Ui_FormCommandInfo()
        self.ui.setupUi(self)
        self.info = []
        self.main_window = main_window
        self.ui.pushButtonSave.clicked.connect(self.save)
        self.ui.pushButtonGen.clicked.connect(self.main_window.generate_xml)
        self.current_frame = 0
        self.current_command = ''
        self.mode = 'hex'
        self.first = True
        self.row_command_map = []
        self.ui.checkBoxHex.stateChanged.connect(self.update_data_mode_hex)
        self.ui.checkBoxDec.stateChanged.connect(self.update_data_mode_dec)
        self.ui.checkBoxBinary.stateChanged.connect(self.update_data_mode_bin)
        self.ui.checkBoxReserved.stateChanged.connect(self.update_reserve_show)
        self.current_item = None
        self.modifylist = []
        #
        self.ui.stackedWidget.setCurrentIndex(1)   #set the all infomation page as default page
        self.ui.pushButtonSCL.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(1))  #show cmd name list
        self.ui.pushButtonSCL.clicked.connect(self.showcmdlist)  #show cmd name list
        self.ui.pushButtonSA.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(0))  #show cmd name list
        self.ui.pushButtonSU.clicked.connect(self.updateinfo)
        self.ui.tableWidgetCmdlist.cellDoubleClicked.connect(self.modifycmd)
        

    def show_message(self, inf, title):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(title)
        if title == 'Save':
            msgBox.addButton(QMessageBox.Ok)
            msgBox.addButton(QMessageBox.No)
        msgBox.setInformativeText(inf)
        msgBox.exec_()

    def check(self):
        s = ''
        table = self.ui.tableWidgetCmd
        for i in range(table.rowCount()):
            if not table.item(i, 2):
                continue
            if table.cellWidget(i, 5) and table.cellWidget(i, 5).isChecked():
                command = self.info[int(self.row_command_map[i]['frame_idx'])][int(self.row_command_map[i]['command_idx'])]
                dword = 'dword' + command['dwords'][int(self.row_command_map[i]['dword_idx'])]['NO']
                field = str(table.item(i, 2).text())
                value = str(table.item(i, 4).text())

                min_value = str(table.item(i, 7).text())
                max_value = str(table.item(i, 8).text())
                # value = item_text_to_dec(value)
                # min_value = item_text_to_dec(min_value)
                # max_value = item_text_to_dec(max_value)
                if max_value < min_value:
                    s = s + 'Command ' + command['name'] + ' ' + dword + ' max value smaller than min value\n\n'
                    # s = s + 'Row' + str(i) + ' max value smaller than min value\n\n'
                if value < min_value:
                    s = s + 'Command ' + command['name'] + ' ' + dword + ' value smaller than min value\n\n'
                if value > max_value:
                    s = s + 'Command ' + command['name'] + ' ' + dword + ' value larger than max value\n\n'

        if s:
            self.show_message(s, 'Error')
            return -1
        else:
            return 0


    @Slot()
    def save(self):
        table = self.ui.tableWidgetCmd
        tree = self.ui.treeWidgetCmd
        if not self.first:
            # self.show_message('Save information', 'Save')
            pass
        else:
            self.first = False
        if self.check() != 0:
            return
        for i in range(table.rowCount()):
            dword = self.info[int(self.row_command_map[i]['frame_idx'])][int(self.row_command_map[i]['command_idx'])]['dwords'][int(self.row_command_map[i]['dword_idx'])]
            if dword:
                if not table.item(i, 2):
                    continue
                field_name = str(table.item(i, 2).text())
                for field in dword['fields']:
                    if field['field_name'] == field_name:
                        field['value'] = str(table.item(i, 4).text())
                        if table.cellWidget(i, 5).isChecked():
                            field['CHECK'] = 'Y'
                        else:
                            field['CHECK'] = 'N'
                        if self.mode == 'bin':
                            field['value'] = hex(int(str(table.item(i, 4).text()), 2))
                            field['min_value'] = hex(int(str(table.item(i, 7).text()), 2))
                            field['max_value'] = hex(int(str(table.item(i, 8).text()), 2))
                        elif self.mode == 'dec':
                            field['value'] = hex(int(str(table.item(i, 4).text())))
                            field['min_value'] = hex(int(str(table.item(i, 7).text())))
                            field['max_value'] = hex(int(str(table.item(i, 8).text())))
                        else:
                            field['value'] = str(table.item(i, 4).text())
                            field['min_value'] = str(table.item(i, 7).text())
                            field['max_value'] = str(table.item(i, 8).text())
        self.main_window.command_info = self.info

    @Slot(QTreeWidgetItem, int)
    def update_tree_checkstate(self, item, column):
        for i in range(item.childCount()):
            dword = item.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                dword.setCheckState(0, Qt.CheckState.Checked)
            else:
                dword.setCheckState(0, Qt.CheckState.Unchecked)


    @Slot()
    def update_data_mode_hex(self):
        if self.ui.checkBoxHex.isChecked():
            self.mode = 'hex'
            self.ui.checkBoxDec.setCheckState(Qt.CheckState.Unchecked)
            self.ui.checkBoxBinary.setCheckState(Qt.CheckState.Unchecked)
            if self.current_item:
              self.main_window.show_command_table(self.current_item)

    @Slot()
    def update_data_mode_dec(self):
        if self.ui.checkBoxDec.isChecked():
            self.mode = 'dec'
            self.ui.checkBoxHex.setCheckState(Qt.CheckState.Unchecked)
            self.ui.checkBoxBinary.setCheckState(Qt.CheckState.Unchecked)
            if self.current_item:
              self.main_window.show_command_table(self.current_item)

    @Slot()
    def update_reserve_show(self):
        if self.current_item:
            self.main_window.show_command_table(self.current_item)

    @Slot()
    def update_data_mode_bin(self):
        if self.ui.checkBoxBinary.isChecked():
            self.mode = 'bin'
            self.ui.checkBoxDec.setCheckState(Qt.CheckState.Unchecked)
            self.ui.checkBoxHex.setCheckState(Qt.CheckState.Unchecked)
            if self.current_item:
              self.main_window.show_command_table(self.current_item)

    @Slot()
    def showcmdlist(self):
        #print(self.main_window.obj.size_error_cmd)
        #print(self.main_window.obj.size_error)
        self.ui.tableWidgetCmdlist.clearContents()
        self.ui.tableWidgetCmdlist.setRowCount(0)
        self.table = self.ui.tableWidgetCmdlist
        
        row = 0
        ##print(self.main_window.obj.ringcmddic)
        for cmd, index in self.main_window.obj.ringcmddic.items():
            if cmd == 'MI_NOOP':
                continue
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cmd))
            self.table.setItem(row, 1, QTableWidgetItem(self.main_window.obj.ringcmdclass[cmd]))
            self.table.setItem(row, 2, QTableWidgetItem(str(index)))
            if cmd in self.main_window.obj.notfoundset:
                self.table.setItem(row, 1, QTableWidgetItem('Not Found'))
                self.table.setItem(row, 3, QTableWidgetItem('Not Found'))
            if cmd in self.main_window.obj.bitfield_error_cmd:
                self.table.setItem(row, 3, QTableWidgetItem('Bitfield Error'))
            elif self.main_window.obj.size_error_cmd[cmd]:
                print(self.main_window.obj.size_error)
                warning = 'Size Error in position: '
                for i in self.main_window.obj.size_error_cmd[cmd]:
                    warning += str(i) + ','
                warning = warning.strip(',')
                self.table.setItem(row, 3, QTableWidgetItem(warning))
            #mark newly modified cmd
            if [t for t in self.modifylist if t[1] == cmd]:
                self.table.item(row, 0).setBackground(QColor(255, 242, 0))
            row += 1
        

        self.cmdlistrow = row
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    @Slot()
    def modifycmd(self, row, column):
        ##print("Row %d and Column %d was clicked" % (row, column))
        if column == 0 or column == 2:
            item = self.table.item(row, column)
            cmdname = self.table.item(row, 0).text()
            ##print(item.text())
            minimum_value = 1
            maximum_value = int(self.table.item(row, 2).text())
            index = ''
            new = ''
            #if column == 0:
            #    new, ok = QInputDialog.getText(self.table,  "Modify", "CMD Name", QLineEdit.Normal, item.text())
            #    if ok:
            #        if new != cmdname:
            #            self.table.setItem(row, 0, QTableWidgetItem(new))
            #            self.table.item(row, 0).setTextColor(QColor(255,0,0))
            #            index = 'all'
            #if column == 1:
            new, ok = QInputDialog.getText(self.table,  "Modify", "CMD Name", QLineEdit.Normal, self.table.item(row, 0).text())
            if ok:
                input_index, ok = QInputDialog.getText(self.table,  "Modify", "\tScope(1-%s)\n(e.g. 1-4,6)" %maximum_value, QLineEdit.Normal, 'Apply to All')
                if input_index != 'Apply to All':
                    index = []
                    list = input_index.strip().split(',')
                    for i in list:
                        if '-' in i:
                            i = i.split('-')
                            index = list(range(int(i[0]), int(i[1])+1))
                        else:
                            index.append(int(i))
                    length = len(index)
                    if int(maximum_value) > length:
                        self.table.setItem(row, 2, QTableWidgetItem(str(maximum_value-length)))
                        self.table.item(row, 2).setTextColor(QColor(255,0,0))
                        self.table.insertRow(row+1)
                        self.table.setItem(row+1, 2, QTableWidgetItem(str(length)))
                        self.table.item(row+1, 2).setTextColor(QColor(255,0,0))
                        self.table.setItem(row+1, 0, QTableWidgetItem(new))
                        self.table.item(row+1, 0).setTextColor(QColor(255,0,0))
                        self.cmdlistrow += 1
                    elif int(maximum_value) == length:
                        index = 'all'
                else:
                    index = 'all'
                if new != cmdname and index == 'all':
                    self.table.setItem(row, 0, QTableWidgetItem(new))
                    self.table.item(row, 0).setTextColor(QColor(255,0,0))
            
            if new and index:

                self.modifylist.append((cmdname, new, index))
                #print(self.main_window.obj.ringcmddic)
                #self.main_window.obj.modifyringcmd(cmdname, new, index)
                #print(self.main_window.obj.ringcmddic)

    @Slot()
    def updateinfo(self):
        for cmdname, new, index in self.modifylist:
            self.main_window.obj.modifyringcmd(cmdname, new, index)
        self.main_window.obj.undate_full_ringinfo()
        self.main_window.obj.updatexml()
        self.main_window.ui.logBrowser.append('Update xml\n')
        self.ui.tableWidgetCmd.clearContents()
        self.ui.treeWidgetCmd.clear()
        self.main_window.ui.logBrowser.append('Reload...\n')
        #pop out message box
        msgBox = QMessageBox()
        msgBox.setText("Success!")
        msgBox.exec_()
        self.main_window.read_command_info_from_xml()
        self.showcmdlist()
        self.modifylist = [] #clear

class Addpath(QWidget):
    def __init__(self, main_window):
        super(Addpath, self).__init__()
        self.ui = Ui_Addpath()
        self.ui.setupUi(self)
        self.main_window = main_window
        self.list = self.ui.listWidget
        self.list.itemSelectionChanged.connect(self.selectionChanged)
        self.last_dir = ''
        self.currentrow = None
        self.selected = None

        self.ui.pushButtonAF.clicked.connect(self.AddFolder)
        self.ui.pushButtonRemove.clicked.connect(self.RemoveFolder)
        deleteShortcut = QShortcut(QKeySequence(Qt.Key_Delete), self) #add delete shortcut for list widget
        deleteShortcut.activated.connect(self.RemoveFolder)
        self.ui.pushButtonMtoT.clicked.connect(self.MovetoTop)
        self.ui.pushButtonMU.clicked.connect(self.MoveUp)
        self.ui.pushButtonMD.clicked.connect(self.MoveDown)
        self.ui.pushButtonMtoB.clicked.connect(self.MovetoBottom)
        self.ui.pushButtonSave.clicked.connect(self.Save)
        #self.ui.pushButtonClose.clicked.connect(self.Close)
    

    def closeEvent(self, event):
        event.accept()
        self.main_window.activateWindow()


    def selectionChanged(self):
        #print("Selected items: ", self.list.selectedItems())
        self.selected = self.list.selectedItems()
        #self.list.setCurrentItem(self.list.selectedItems())


    @Slot()
    def AddFolder(self):
        dialog = QFileDialog(self)
        if self.last_dir:
            dir = dialog.getExistingDirectory(self, "Add Search Folder",
                                           self.last_dir) 
        elif self.main_window.ui.lineEditMediaPath.text():
            dir = dialog.getExistingDirectory(self, "Add Search Folder",
                                           self.main_window.ui.lineEditMediaPath.text().split(';')[-1]) 
        else:
            dir = dialog.getExistingDirectory(self, "Add Search Folder",
                                           "/home")
        self.last_dir = dir
        if self.list.count() > 1 and os.path.basename(dir) != 'hw':
            msgBox = QMessageBox()
            msgBox.setText("Path should End in hw!")
            msgBox.exec_()
        else:
            self.list.insertItem(0, dir)

    @Slot()
    def RemoveFolder(self):
        if self.selected:
            self.list.setCurrentItem(self.selected[0])
            currentRow = self.list.currentRow()
            currentItem = self.list.takeItem(currentRow)

    @Slot()
    def MovetoTop(self):
        if self.selected:
            self.list.setCurrentItem(self.selected[0])
            currentRow = self.list.currentRow()
            currentItem = self.list.takeItem(currentRow)
            self.list.insertItem(0, currentItem)
            currentItem.setSelected(True)

    @Slot()
    def MoveUp(self):
        if self.selected:
            self.list.setCurrentItem(self.selected[0])
            currentRow = self.list.currentRow()
            currentItem = self.list.takeItem(currentRow)
            self.list.insertItem(currentRow - 1, currentItem)
            currentItem.setSelected(True)

    @Slot()
    def MoveDown(self):
        if self.selected:
            self.list.setCurrentItem(self.selected[0])
            currentRow = self.list.currentRow()
            currentItem = self.list.takeItem(currentRow)
            self.list.insertItem(currentRow + 1, currentItem)
            currentItem.setSelected(True)

    @Slot()
    def MovetoBottom(self):
        if self.selected:
            self.list.setCurrentItem(self.selected[0])
            currentRow = self.list.currentRow()
            currentItem = self.list.takeItem(currentRow)
            self.list.insertItem(self.list.count(), currentItem)
            currentItem.setSelected(True)

    @Slot()
    def Save(self):
        items = []
        for i in range(self.list.count()):
            items.append(self.list.item(i).text())
        self.main_window.ui.lineEditMediaPath.setText(';'.join(items))

    @Slot()
    def Close(self):
        pass

def item_text_to_dec(s):
    if s.startswith('0x'):
        return int(s, 16)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.activateWindow()
    sys.exit(app.exec_())
