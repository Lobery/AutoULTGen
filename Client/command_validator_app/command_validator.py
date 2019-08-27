import sys
import os
import re
import shutil
import copy
from functools import partial
import time
from PySide2.QtCore import QCoreApplication, Slot, Qt, QRegExp
from PySide2.QtWidgets import *
from PySide2.QtGui import QColor, QKeySequence, QValidator, QRegExpValidator
from lxml import etree
import xml.etree.ElementTree as ET
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
        self.ui.pushButtonDC.clicked.connect(self.deleteCase)
        #self.ui.pushButtonGAll.clicked.connect(lambda : self.ui.tabWidget.setCurrentIndex(1))
        self.ui.pushButtonUpdate.clicked.connect(self.input_goru)

        self.media_path = [] # text split by ';'
        self.pre_media_path = [] # text split by ';', used to save last media_path. Judge if updated. 
        self.pre_ringinfo_path = ''
        self.base_media = '' # end in file /source
        self.media_path2 = '' # end in Source/media
        self.Buf = None 
        self.obj = None     #save cmd obj
        self.command_info = []
        self.command_tags = ('DW0_dwlen', 'class', 'def_dwSize', 'index', 'input_dwsize', 'name')
        self.dword_tags = ('NO', 'value', 'class', 'cmdarraysize', 'otherCMD', 'arrayname', 'unmappedstr')
        #self.command_filter = {'MI_NOOP_CMD', 'MI_NOOP'}
        self.platform_list = []
        self.ringinfo_path = ''
        self.output_path = ''
        self.command_xml = ''
        self.test_name = ''
        self.platform = ''
        self.frame_num = 0
        self.row_num = 0
        self.GUID = ''
        self.pre_component1 = ''
        self.form = FormCommandInfo(self)
        self.Addpath = Addpath(self)
        self.pathlist = self.Addpath.ui.listWidget
        self.update_cmd_check_state = True
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
        self.ui.InputPathText.setReadOnly(True)
        self.ui.Component_input.setReadOnly(True)
        self.ui.lineEditMediaPath.textChanged.connect(self.update_platform_list)
        #self.ui.lineEditRinginfoPath.textChanged.connect(self.read_test_name)
        self.ui.comboBoxPlatform.currentIndexChanged.connect(self.fillinput_platform)
        self.ui.comboBoxComponent.currentIndexChanged.connect(self.fillinput_component)

        self.ui.GUID_input.editingFinished.connect(self.checkGUID)
        self.ui.lineEditRinginfoPath.editingFinished.connect(partial(self.fillframenum,'Main'))
        self.ui.lineEditDDIInputPath.editingFinished.connect(partial(self.fillframenum,'Input'))
        self.ui.Height_input.editingFinished.connect(partial(self.checkhw, 'Height'))
        self.ui.Width_input.editingFinished.connect(partial(self.checkhw, 'Width'))
        self.ui.lineEditTestName.editingFinished.connect(self.checkTestName)

        
        #self.ui.lineEditTestName.setText('encodeHevcCQP')
        #self.ui.lineEditMediaPath.setText(r'C:\Users\sunling\gfx\gfx-driver\Source\media;C:\Users\sunling\gfx\gfx-driver\Source\media\media_embargo\ult\agnostic\test\gen12_tglhp\hw;C:\projects\hevctest\Source\media\media_embargo\agnostic\gen12_tglhp\hw')
        #self.ui.lineEditDDIInputPath.setText(r'C:\projects\github\AutoULTGen\Client\command_validator_app\vcstringinfo\HEVC-VDENC-grits-WP-2125\DDI_Input')
        #self.ui.lineEditRinginfoPath.setText(r'C:\projects\github\AutoULTGen\Client\command_validator_app\vcstringinfo\HEVC-VDENC-grits-WP-2125\VcsRingInfo')
        self.ui.lineEditComponent.setText(self.ui.comboBoxComponent.currentText())
        self.ui.lineEditPlatform.setText(self.ui.comboBoxPlatform.currentText())

#        self.ui.comboBoxEncFunc = ExtendedComboBox(self.ui.comboBoxEncFunc)
#        self.ui.comboBoxResF = ExtendedComboBox(self.ui.comboBoxResF)
#        self.ui.comboBoxResTT = ExtendedComboBox(self.ui.comboBoxResTT)
#        self.ui.comboBoxRawF = ExtendedComboBox(self.ui.comboBoxRawF)
#        self.ui.comboBoxRawTT = ExtendedComboBox(self.ui.comboBoxRawTT)

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
                self.ui.Width_input.clear()
               
       
    @Slot()
    def checkTestName(self):
        # remove white space at start and end
        text = self.ui.lineEditTestName.text().strip()
        # pure white space should not be detected as input
        if not text:
            return
        # test name should only contain _, number, letter
        words = text.split('_')
        for word in words:
            # ignore \n
            if not word:
                continue
            elif word.isalpha() or word.isalnum():
                continue
            else:
                msgBox = QMessageBox()
                msgBox.setText("Test Name contains invalid character!")
                msgBox.exec_()
                self.ui.lineEditTestName.clear()

    @Slot()
    def checkComboBoxEnvFunc(self):
        value = self.ui.comboBoxEncFunc.currentText().strip()
        if len(value) == 0:
            return
        valid = True
        if value.isdigit():
            value = int(value)
            for key in list(self.input_combo_obj.output['tagENCODE_FUNC'].keys()):
                if value == self.input_combo_obj.output['tagENCODE_FUNC'][key]:
                    self.ui.comboBoxEncFunc.setCurrentText(key)
                    return
            valid = False
        elif value not in list(self.input_combo_obj.output['tagENCODE_FUNC'].keys()):
            valid = False
        if not valid:
            msgBox = QMessageBox()
            msgBox.setText("Incorrect Type or Value!")
            msgBox.exec_()
            self.ui.comboBoxEncFunc.setCurrentText("")

    @Slot()
    def checkComboBoxResF(self):
        value = self.ui.comboBoxResF.currentText().strip()
        if len(value) == 0:
            return
        valid = True
        if value.isdigit():
            value = int(value)
            for key in list(self.input_combo_obj.output['_MOS_FORMAT'].keys()):
                if value == self.input_combo_obj.output['_MOS_FORMAT'][key]:
                    self.ui.comboBoxResF.setCurrentText(key)
                    return
            valid = False
        elif value not in list(self.input_combo_obj.output['_MOS_FORMAT'].keys()):
            valid = False
        if not valid:
            msgBox = QMessageBox()
            msgBox.setText("Incorrect Type or Value!")
            msgBox.exec_()
            self.ui.comboBoxResF.setCurrentText("")

    @Slot()
    def checkComboBoxResTT(self):
        value = self.ui.comboBoxResTT.currentText().strip()
        if len(value) == 0:
            return
        valid = True
        if value.isdigit():
            value = int(value)
            for key in list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()):
                if value == self.input_combo_obj.output['_MOS_TILE_TYPE'][key]:
                    self.ui.comboBoxResTT.setCurrentText(key)
                    return
            valid = False
        elif value not in list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()):
            valid = False
        if not valid:
            msgBox = QMessageBox()
            msgBox.setText("Incorrect Type or Value!")
            msgBox.exec_()
            self.ui.comboBoxResTT.setCurrentText("")

    @Slot()
    def checkComboBoxRawF(self):
        value = self.ui.comboBoxRawF.currentText().strip()
        if len(value) == 0:
            return
        valid = True
        if value.isdigit():
            value = int(value)
            for key in list(self.input_combo_obj.output['_MOS_FORMAT'].keys()):
                if value == self.input_combo_obj.output['_MOS_FORMAT'][key]:
                    self.ui.comboBoxRawF.setCurrentText(key)
                    return
            valid = False
        elif value not in list(self.input_combo_obj.output['_MOS_FORMAT'].keys()):
            valid = False
        if not valid:
            msgBox = QMessageBox()
            msgBox.setText("Incorrect Type or Value!")
            msgBox.exec_()
            self.ui.comboBoxRawF.setCurrentText("")
       
    @Slot()
    def checkComboBoxRawTT(self):
        value = self.ui.comboBoxRawTT.currentText().strip()
        if len(value) == 0:
            return
        valid = True
        if value.isdigit():
            value = int(value)
            for key in list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()):
                if value == self.input_combo_obj.output['_MOS_TILE_TYPE'][key]:
                    self.ui.comboBoxRawTT.setCurrentText(key)
                    return
            valid = False
        elif value not in list(self.input_combo_obj.output['_MOS_TILE_TYPE'].keys()):
            valid = False
        if not valid:
            msgBox = QMessageBox()
            msgBox.setText("Incorrect Type or Value!")
            msgBox.exec_()
            self.ui.comboBoxRawTT.setCurrentText("")
        

    @Slot()
    def checkGUID(self):
        self.GUID = self.ui.GUID_input.text()
        if not self.read_test_cfg_cpp('GUID'):
            
            self.ui.GUID_input.setText(self.pre_GUID)

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
    def fillframenum(self, name, flag = True):
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

        if flag and self.ui.lineEditFrame.text().strip() and self.ui.FrameNum_input.text().strip() and self.ui.lineEditFrame.text() != self.ui.FrameNum_input.text():
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
            prePlatformName = self.ui.comboBoxPlatform.currentText()
            self.ui.comboBoxPlatform.clear()
            self.ui.comboBoxPlatform.addItems(self.platform_list)
            if prePlatformName in self.platform_list :
                self.ui.comboBoxPlatform.setCurrentText(prePlatformName)

            print('update platform list according to igfxfmid.h\n')
        except:
            pass

    def checkMainPageInput(self):
        msgBox = QMessageBox()
        if not self.ui.lineEditTestName.text().strip():
            msgBox.setText("Please input a valid Test Name!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditMediaPath.text():
            msgBox.setText("Please input a valid Command Path!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditRinginfoPath.text():
            msgBox.setText("Please input a valid Ringinfo Path!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditDDIInputPath.text():
            msgBox.setText("Please input a valid DDI Input Path!")
            msgBox.exec_()
            return False
        if self.ui.lineEditPlatform.text() == "IGFX_UNKNOWN":
            msgBox.setText("Please input a valid Platform!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditComponent.text():
            msgBox.setText("Please input a valid Component!")
            msgBox.exec_()
            return False

        return True
    
    def checkDeleteCase(self):
        #TODO
        #CHECK input is not empty
        msgBox = QMessageBox()
        if not self.ui.lineEditTestName.text().strip():
            msgBox.setText("Please input a valid Test Name!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditMediaPath.text():
            msgBox.setText("Please input a valid Command Path!")
            msgBox.exec_()
            return False
        if self.ui.lineEditPlatform.text() == "IGFX_UNKNOWN":
            msgBox.setText("Please input a valid Platform!")
            msgBox.exec_()
            return False
        if not self.ui.lineEditComponent.text():
            msgBox.setText("Please input a valid Component!")
            msgBox.exec_()
            return False
        # Get Testname, platform, component
        self.test_name = self.ui.lineEditTestName.text().strip()
        self.platform = self.ui.lineEditPlatform.text()
        self.component = self.ui.comboBoxComponent.currentText()
        #If component is not encode, return false
        if self.component != 'Encode':
            msgBox.setText("Only Encode is supported!")
            msgBox.exec_()
            return False
        # Get Workspace
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
            self.rootdir = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\vp\test')
            self.workspace = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\vp\test\test_data')
        else:
            self.rootdir = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\codec\test')
            self.workspace = os.path.join(self.base_media, r'media\media_embargo\media_driver_next\ult\windows\codec\test\test_data')
        #Find whether its in component_xxx.cpp, if not return false
        cppFileName = self.component.lower() + "_integrated_test_cfg.cpp"
        cppFileFullName = os.path.join(self.rootdir, cppFileName)
        with open(cppFileFullName, 'r') as f:
            lines = f.read()
        try:
            parse_test_name = self.test_name[0].upper() + self.test_name[1:]
            startIndex = lines.find('"' + parse_test_name + '",')
            lines = lines[startIndex:]
            if startIndex < 0:
                msgBox.setText("Test not find!")
                msgBox.exec_()
                return False
            #Check in cpp file whether platform is same, if not return false
            platformStartIndex = lines.find('{"')
            platformStartIndex += 2
            platformEndIndex = lines.find('"}', platformStartIndex)
            cppPlatform = lines[platformStartIndex:platformEndIndex].strip()
            if cppPlatform != self.platform:
                msgBox.setText("Test with same name and component but different platform!")
                msgBox.exec_()
                return False
            # get IDR_ENCODEHEVCCQP_REFERENCE
            referenceStartIndex = lines.find("{")
            referenceStartIndex += 1
            referenceEndIndex = lines.find(",", referenceStartIndex)
            self.cppReference = lines[referenceStartIndex:referenceEndIndex].strip()
            commentIndex = self.cppReference.find("/*")
            if commentIndex >= 0:
                self.cppReference = lines[:commentIndex].strip()
            # get IDR_ENCODEHEVCCQP_INPUT
            inputStartIndex = referenceEndIndex + 1
            inputEndIndex = lines.find(',', inputStartIndex)
            self.cppInput = lines[inputStartIndex:inputEndIndex].strip()
            commentIndex = self.cppInput.find("/*")
            if commentIndex >= 0:
                self.cppInput = lines[:commentIndex].strip()
            #Else find same case, return true
        except:
            print("cpp file parse error")
            return False
        return True

    @Slot()
    def deleteCase(self):
        if not self.checkDeleteCase():
            return

        # DELETE lines in encode_integrated_test.cpp
        cppFileName = self.component.lower() + "_integrated_test.cpp"
        cppFileFullName = os.path.join(self.rootdir, cppFileName)
        with open(cppFileFullName, 'r') as f:
            lines = f.readlines()
        try:
            for line_idx, line in enumerate(lines):
                parse_test_name = self.test_name[0].upper() + self.test_name[1:]
                if line.find("TEST_CASE_DEFINE(MediaEncodeItTest, " + parse_test_name + ")") >= 0:
                    del lines[line_idx]
                    break
        except:
            print("cpp file parse error")
            return
        with open(cppFileFullName, 'w') as f:
            f.writelines(lines)

        # DELETE lines in encode_integrated_test_cfg.cpp
        cppFileName = self.component.lower() + "_integrated_test_cfg.cpp"
        cppFileFullName = os.path.join(self.rootdir, cppFileName)
        with open(cppFileFullName, 'r') as f:
            lines = f.readlines()
        try:
            for line_idx, line in enumerate(lines):
                parse_test_name = self.test_name[0].upper() + self.test_name[1:]
                if line.lstrip().startswith('{"' + parse_test_name):
                    testLineStartIndex = line_idx
                    break
            deletedLines = lines[:testLineStartIndex] + lines[testLineStartIndex+6:]
            #commaIndex = deletedLines[testLineStartIndex-1].find(',')
            #if commaIndex >= 0:
            #    deletedLines[testLineStartIndex - 1] = deletedLines[testLineStartIndex - 1][:commaIndex] + deletedLines[testLineStartIndex - 1][commaIndex+1:]
        except:
            print("cpp file parse error")
            return
        with open(cppFileFullName, 'w') as f:
            f.writelines(deletedLines)

        # DELETE lines in media_driver_codec_ult.rc
        ultFileName = "media_driver_codec_ult.rc"
        ultFileFullName = os.path.join(self.workspace, ultFileName)
        with open(ultFileFullName, 'r') as f:
            lines = f.readlines()
        try:
            for line_idx, line in enumerate(lines):
                if line.find(self.test_name.upper()) >= 0:
                    del lines[line_idx]
                    del lines[line_idx]
                    break
        except:
            print("rc file parse error")
            return
        with open(ultFileFullName, 'w') as f:
            f.writelines(lines)

        # DELETE lines in resource.h
        resourceFileName = "resource.h"
        resourceFileFullName = os.path.join(self.workspace, resourceFileName)
        with open(resourceFileFullName, 'r') as f:
            lines = f.readlines()
        try:
            for line_idx, line in enumerate(lines):
                if line.find(self.test_name.upper()) >= 0:
                    del lines[line_idx]
                    del lines[line_idx]
                    break
        except:
            print("resource file parse error")
            return
        with open(resourceFileFullName, 'w') as f:
            f.writelines(lines)

        # DELETE FOLDER test_data\test_name
        try:
            test_folder = os.path.join(self.workspace, self.test_name)
            shutil.rmtree(test_folder)
        except:
            print("remove test folder error")
            return

        msgBox = QMessageBox()
        msgBox.setText("Test " + self.test_name + " deleted successfully!")
        msgBox.exec_()

    @Slot()
    def fillinput(self):
        blank = []
        flag = True
        if False == self.checkMainPageInput():
            return
        if not self.ui.lineEditRinginfoPath.text():
            self.ui.lineEditRinginfoPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('Ringinfo')
        else:
            flag = False
            self.fillframenum('Main')
        if not self.ui.lineEditDDIInputPath.text():
            self.ui.lineEditDDIInputPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('DDIInput')
        else:
            self.fillframenum('Input',flag)
        if not self.ui.lineEditMediaPath.text():
            self.ui.lineEditMediaPath.setStyleSheet('QLineEdit {background-color: rgb(255, 242, 0);}')
            blank.append('Media')
        if blank:
            msgBox = QMessageBox()
            str = ', '.join(blank)
            msgBox.setText("Please fill %s Path!"% str)
            msgBox.exec_()
        elif self.read_info_from_ui():

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
                if self.ui.lineEditComponent.text() != pattern.group(1):
                    msgBox = QMessageBox()
                    msgBox.setWindowTitle('Testname Error')
                    msgBox.setInformativeText('Current Component %s is different from previous configuration: %s\n' %(self.ui.lineEditComponent.text(), pattern.group(1)))
                    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    msgBox.setDefaultButton(QMessageBox.Cancel)
                    buttonY = msgBox.button(QMessageBox.Ok)
                    buttonY.setText('Rewrite')
                    buttonN = msgBox.button(QMessageBox.Cancel)
                    buttonN.setText('Discard')
                    msgBox.exec_()
                    self.activateWindow()
                    if msgBox.clickedButton() == buttonN:
                        self.ui.comboBoxComponent.setCurrentText(pattern.group(1))
                        return
                    if msgBox.clickedButton() == buttonY:
                        self.ui.Component_input.setText(self.ui.lineEditComponent.text())
                else:
                    self.ui.Component_input.setText(pattern.group(1))
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


    def delete_items_in_combobox(self, combobox):
        for i in range(combobox.count()):
            combobox.removeItem(0)

    def fillcombobox(self):

        self.ui.comboBoxEncFunc.currentTextChanged.connect(partial(self.selectbox,'EncFunc'))
        self.ui.comboBoxResF.currentTextChanged.connect(partial(self.selectbox,'ResFormat'))
        self.ui.comboBoxResTT.currentTextChanged.connect(partial(self.selectbox,'ResTileType'))
        self.ui.comboBoxRawF.currentTextChanged.connect(partial(self.selectbox,'RawFormat'))
        self.ui.comboBoxRawTT.currentTextChanged.connect(partial(self.selectbox,'RawTileType'))

        self.input_combo_obj = GetEnumMember(self.base_media)
        self.input_combo_obj.read_files()
        #self.ui.comboBoxEncFunc = ExtendedComboBox(self.ui.comboBoxEncFunc)

        self.ui.comboBoxEncFunc.lineEdit().editingFinished.connect(self.checkComboBoxEnvFunc)
        self.ui.comboBoxResF.lineEdit().editingFinished.connect(self.checkComboBoxResF)
        self.ui.comboBoxResTT.lineEdit().editingFinished.connect(self.checkComboBoxResTT)
        self.ui.comboBoxRawF.lineEdit().editingFinished.connect(self.checkComboBoxRawF)
        self.ui.comboBoxRawTT.lineEdit().editingFinished.connect(self.checkComboBoxRawTT)
        
        self.delete_items_in_combobox(self.ui.comboBoxEncFunc)
        self.delete_items_in_combobox(self.ui.comboBoxResF)
        self.delete_items_in_combobox(self.ui.comboBoxResTT)
        self.delete_items_in_combobox(self.ui.comboBoxRawF)
        self.delete_items_in_combobox(self.ui.comboBoxRawTT)

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
                # CMD_HCP_VP9_RDOQ_STATE has no dwords
                #if len(command['dwords']) == 0:
                #    if command_item.checkState(0) == Qt.CheckState.Checked:
                #        command['check'] = 'Y'
                #    else:
                #        command['check'] = 'N'
                for dword_idx, dword in enumerate(command['dwords']):
                    ##print('dword ' + str(dword_idx) + '\n')
                    #if 'unmappedstr' in dword and dword['unmappedstr']:
                    #    continue
                    if i_row >= table.rowCount():
                        table.insertRow(i_row)
                    table.setItem(i_row, 1, QTableWidgetItem('dword' + dword['NO']))
                    if not dword['fields']:
                        if dword['value']:
                            table.setItem(i_row, 5, QTableWidgetItem(dword['value']))
                        if dword['arrayname']:
                            table.setItem(i_row, 2, QTableWidgetItem(dword['arrayname']))
                        if dword['unmappedstr']:
                            table.setItem(i_row, 5, QTableWidgetItem(dword['unmappedstr']))
                        self.form.row_command_map.append(
                            {'frame_idx': idx['frame_idx'], 'command_idx': command['index'], 'dword_idx': dword_idx})
                        i_row += 1

                    dword_item = command_item.child(dword_idx)

                    for field_idx, field in enumerate(dword['fields']):
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
                                
                                if ('field_name' in obj_field) and (not obj_field['field_name'].startswith('Reserved')) and command_item.checkState(0) == Qt.CheckState.Checked and dword_item.checkState(0) == Qt.CheckState.Checked:
                                    checkBox.setCheckState(Qt.CheckState.Checked)
                                if ('obj_field_name' in obj_field) and (not obj_field['obj_field_name'].startswith('Reserved')) and command_item.checkState(0) == Qt.CheckState.Checked and dword_item.checkState(0) == Qt.CheckState.Checked:
                                    checkBox.setCheckState(Qt.CheckState.Checked)
                                #if ('field_name' in obj_field) and (not obj_field['field_name'].startswith('Reserved')) and (command_item.checkState(0) == Qt.CheckState.Unchecked or dword_item.checkState(0) == Qt.CheckState.Unchecked) and field['CHECK'] == 'N':
                                #    checkBox.setCheckState(Qt.CheckState.Unchecked)
                                #if ('obj_field_name' in obj_field) and (not obj_field['obj_field_name'].startswith('Reserved')) and (command_item.checkState(0) == Qt.CheckState.Unchecked or dword_item.checkState(0) == Qt.CheckState.Unchecked) and field['CHECK'] == 'N':
                                #    checkBox.setCheckState(Qt.CheckState.Unchecked)
                                # checkBox.stateChanged.connect(self.check_box_change)
                                table.setCellWidget(i_row, 7, checkBox)
                                if self.form.mode == 'bin':
                                    table.setItem(i_row, 5, QTableWidgetItem(bin(int(obj_field['default_value'], 16))))
                                    table.setItem(i_row, 6, QTableWidgetItem(bin(int(obj_field['value'], 16))))
                                    table.setItem(i_row, 9, QTableWidgetItem(bin(int(obj_field['min_value'], 16))))
                                    table.setItem(i_row, 10, QTableWidgetItem(bin(int(obj_field['max_value'], 16))))
                                elif self.form.mode == 'dec':
                                    table.setItem(i_row, 5, QTableWidgetItem(str(int(obj_field['default_value'], 16))))
                                    table.setItem(i_row, 6, QTableWidgetItem(str(int(obj_field['value'], 16))))
                                    table.setItem(i_row, 9, QTableWidgetItem(str(int(obj_field['min_value'], 16))))
                                    table.setItem(i_row, 10, QTableWidgetItem(str(int(obj_field['max_value'], 16))))
                                else:
                                    table.setItem(i_row, 5, QTableWidgetItem(obj_field['default_value']))
                                    table.setItem(i_row, 6, QTableWidgetItem(obj_field['value']))
                                    table.setItem(i_row, 9, QTableWidgetItem(obj_field['min_value']))
                                    table.setItem(i_row, 10, QTableWidgetItem(obj_field['max_value']))
                                if 'Address' in field:
                                    table.setItem(i_row, 8, QTableWidgetItem(obj_field['Address']))
                                else:
                                    table.setItem(i_row, 8, QTableWidgetItem('N'))
                                table.setItem(i_row, 3, QTableWidgetItem(obj_field['bitfield_l']))
                                table.setItem(i_row, 4, QTableWidgetItem(obj_field['bitfield_h']))
                                table.item(i_row, 3).setFlags(Qt.NoItemFlags)
                                table.item(i_row, 4).setFlags(Qt.NoItemFlags)
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
                        field_item = dword_item.child(field_idx)
                        if command_item.checkState(0) == Qt.CheckState.Checked and dword_item.checkState(0) == Qt.CheckState.Checked and field_item.checkState(0) == Qt.CheckState.Checked:
                            #field['CHECK'] == 'Y'
                            checkBox.setCheckState(Qt.CheckState.Checked)
                        else:
                            #field['CHECK'] == 'N'
                            checkBox.setCheckState(Qt.CheckState.Unchecked)
                        # checkBox.stateChanged.connect(self.check_box_change)
                        table.setCellWidget(i_row, 7, checkBox)
                        if self.form.mode == 'bin':
                            table.setItem(i_row, 5, QTableWidgetItem(bin(int(field['default_value'], 16))))
                            table.setItem(i_row, 6, QTableWidgetItem(bin(int(field['value'], 16))))
                            table.setItem(i_row, 9, QTableWidgetItem(bin(int(field['min_value'], 16))))
                            table.setItem(i_row, 10, QTableWidgetItem(bin(int(field['max_value'], 16))))
                        elif self.form.mode == 'dec':
                            table.setItem(i_row, 5, QTableWidgetItem(str(int(field['default_value'], 16))))
                            table.setItem(i_row, 6, QTableWidgetItem(str(int(field['value'], 16))))
                            table.setItem(i_row, 9, QTableWidgetItem(str(int(field['min_value'], 16))))
                            table.setItem(i_row, 10, QTableWidgetItem(str(int(field['max_value'], 16))))
                        else:
                            table.setItem(i_row, 5, QTableWidgetItem(field['default_value']))
                            table.setItem(i_row, 6, QTableWidgetItem(field['value']))
                            table.setItem(i_row, 9, QTableWidgetItem(field['min_value']))
                            table.setItem(i_row, 10, QTableWidgetItem(field['max_value']))
                        table.item(i_row, 5).setFlags(Qt.NoItemFlags)
                        if 'Address' in field:
                            table.setItem(i_row, 8, QTableWidgetItem(field['Address']))
                        else:
                            table.setItem(i_row, 8, QTableWidgetItem('N'))
                        table.setItem(i_row, 3, QTableWidgetItem(field['bitfield_l']))
                        table.item(i_row, 3).setFlags(Qt.NoItemFlags)
                        table.setItem(i_row, 4, QTableWidgetItem(field['bitfield_h']))
                        table.item(i_row, 4).setFlags(Qt.NoItemFlags)
                        self.form.row_command_map.append({'frame_idx': idx['frame_idx'],'command_idx': command['index'], 'dword_idx': dword_idx})
                        i_row += 1

            table.resizeColumnsToContents()
            table.resizeRowsToContents()

    @Slot()
    def show_command_info(self):
        self.form.ui.tableWidgetCmd.clearContents()
        self.form.ui.tableWidgetCmd.setRowCount(0)
        self.form.setWindowTitle(self.test_name)
        tree = self.form.ui.treeWidgetCmd
        tree.clear()
        header = self.form.ui.treeWidgetCmd.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)

        test = QTreeWidgetItem(tree)
        test.setText(0, self.test_name)
        for frame_idx in range(len(self.command_info)):
            ##print('frame idx:' + str(frame_idx))
            frame = QTreeWidgetItem(test)
            frame.setText(0, 'frame' + str(frame_idx))
            frame.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': 'all'})
            for command_idx, command in enumerate(self.command_info[frame_idx]):
                cmd = QTreeWidgetItem(frame)
                cmd.setText(0, command['name'])
                cmd.setCheckState(0,Qt.CheckState.Unchecked)
                #self.command_info[frame_idx][command_idx]['check'] = 'N'
                #if command['name'] in self.command_filter:
                #    cmd.setCheckState(0, Qt.CheckState.Unchecked)
                #else:
                #    cmd.setCheckState(0, Qt.CheckState.Checked)
                cmd.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': command_idx})
                # 'CMD_HCP_VP9_RDOQ_STATE' has no dword
                if len(command['dwords']) == 0:
                    if self.command_info[frame_idx][command_idx]['check'] == 'Y':
                        cmd.setCheckState(0, Qt.CheckState.Checked)
                    #cmd.setCheckState(0, Qt.CheckState.Checked)
                    #self.command_info[frame_idx][command_idx]['check'] = 'Y'
                for dword_idx in range(len(command['dwords'])):
                    dword = QTreeWidgetItem(cmd)
                    #print('dword_idx' + str(dword_idx))
                    dword.setText(0, 'dword' + command['dwords'][dword_idx]['NO'])
                    if len(command['dwords'][dword_idx]['fields'])==0:
                        dword.setCheckState(0,Qt.CheckState.Unchecked)   
                    for field in command['dwords'][dword_idx]['fields']:
                        # field in MI_BATCH_BUFFER_START_CMD command may have a different structure  
                        if command['name'] == "MI_BATCH_BUFFER_START_CMD" and 'obj_fields' in field:
                            #checkState = Qt.CheckState.Unchecked
                            field_item = QTreeWidgetItem(dword)
                            field_item.setText(0, field['field_name'])
                            for obj_field in field["obj_fields"]:
                                obj_field_item = QTreeWidgetItem(field_item)
                                obj_field_item.setText(0, obj_field['obj_field_name'])
                                if obj_field['CHECK'] == 'Y':
                                    obj_field_item.setCheckState(0, Qt.CheckState.Checked)
                                    field_item.setCheckState(0, Qt.CheckState.Checked)
                                    dword.setCheckState(0, Qt.CheckState.Checked)
                                    cmd.setCheckState(0, Qt.CheckState.Checked)
                                    self.command_info[frame_idx][command_idx]['check'] = 'Y'
                                else:
                                    obj_field_item.setCheckState(0, Qt.CheckState.Unchecked)
                            continue
                        if 'CHECK' in field and field['CHECK']=='Y':
                            cmd.setCheckState(0,Qt.CheckState.Checked)
                            self.command_info[frame_idx][command_idx]['check'] = 'Y'
                            dword.setCheckState(0,Qt.CheckState.Checked)
                        continue

                    #if command['name'] in self.command_filter:
                    #    dword.setCheckState(0, Qt.CheckState.Unchecked)
                    #else:
                    #    dword.setCheckState(0, Qt.CheckState.Checked)
                    if command['name'] == "MI_BATCH_BUFFER_START_CMD" and 'obj_fields' in field:
                        continue
                    dword.setData(2, 1, {'frame_idx': frame_idx, 'cmd_idx': command_idx, 'dword_idx': dword_idx})
                    for field_obj in command['dwords'][dword_idx]['fields']:
                        if 'field_name' in field_obj:
                            field = QTreeWidgetItem(dword)
                            field.setText(0, field_obj['field_name'])
                            if 'CHECK' in field_obj and field_obj['CHECK'] == 'Y':
                                field.setCheckState(0, Qt.CheckState.Checked)
                            else:
                                field.setCheckState(0, Qt.CheckState.Unchecked)
        self.form.show()
        self.form.activateWindow()

    def parse_command_file(self):
        #print('begin parse command file')
        self.ui.logBrowser.append('Begin parse vcs ring info\n')
        self.ui.logBrowser.append('It may take about 30 seconds to finish parsing.\n')
        QCoreApplication.processEvents()

        # build CMDFinder obj
        if not self.obj:
            self.obj = CmdFinder(self.media_path, 12, self.ringinfo_path)
        start = time.clock()
        #Judge if it is update media path case
        if self.pre_media_path and self.pre_media_path != self.media_path: #sequence matters!
            self.obj.source = self.media_path 
        if not self.pre_ringinfo_path or self.pre_ringinfo_path != self.ringinfo_path: #extract vcsringinfo at the first time or redo this step if path changes
            self.obj.extractfull()

        self.pre_media_path = self.media_path ##save current media path to history
        self.pre_ringinfo_path = self.ringinfo_path ##save current ringinfo path to history

        self.Buf = self.obj.h2xml()
        
        self.obj.updatexml()
        #self.obj.writexml(self.output_path)
        elapsed = (time.clock() - start)
        print("Total Time used:",elapsed)


    def read_info_from_ui(self):
        if self.ui.lineEditComponent.text():
            self.component = self.ui.lineEditComponent.text()
        else:
            self.component = self.ui.comboBoxComponent.currentText()
        if self.ui.lineEditComponent.text() != 'Encode':
            msgBox = QMessageBox()
            msgBox.setText("Only support Encode!")
            msgBox.exec_()
            return False
        if self.ui.lineEditPlatform.text():
            self.platform = self.ui.lineEditPlatform.text()
        else:
            self.platform = self.ui.comboBoxPlatform.currentText()
        self.test_name = self.ui.lineEditTestName.text().strip()
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
            self.media_path = self.ui.lineEditMediaPath.text().split(';')

        # create single folder for each testname
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        else:
            ## check if platform is same with one testname
            # load previous info first
            if not self.read_test_cfg_cpp('platform'):
                self.ui.comboBoxPlatform.setCurrentText(self.pre_platform)
                return False
        self.ui.logBrowser.append('All the following output will be saved in workspace:\n%s\n'  %self.output_path)
        self.ringinfo_path = self.ui.lineEditRinginfoPath.text()
        return True

        

    def read_command_info_from_xml(self, show = True):
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
                if command.attrib['name'] in ('MI_NOOP_CMD', 'HCP_PAK_INSERT_OBJECT_CMD') or command.attrib['name'].endswith('_SURFACE_STATE_CMD'):
                    info['check'] = 'N'
                else:
                    info['check'] = 'Y'
                for command_tag in self.command_tags:
                    info[command_tag] = command.get(command_tag)
                #if info['name'] in self.command_filter:
                #    info['check'] = 'N'
                #else:
                #    info['check'] = 'Y'
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

                    if info['check'] == 'Y':
                        dword_info['check'] = 'Y'
                    else:
                        dword_info['check'] = 'N'
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
                            if 'field_name' in field_info:
                                name = field_info['field_name']
                                field_info['CHECK'] = 'Y'
                                if info['check'] == 'N':
                                    field_info['CHECK'] = 'N'
                                if name in ('BaseAddressIndexToMemoryObjectControlStateMocsTables', 'MemoryObjectControlState') or name.endswith('CacheSelect') or name.startswith('Reserved'):
                                    field_info['CHECK'] = 'N'
                        dword_info['fields'].append(field_info)
                    info['dwords'].append(dword_info)
                # if not f_other_cmd:
                commands.append(info)
            # for command_idx, command in enumerate(commands):
            #     command['index'] = command_idx
            frames.append(commands)
        self.command_info = frames
        #self.dw_length_check()  #finish this part in cmdlist
        
        self.form.info = self.command_info
        if show:
            self.show_command_info()


    def dw_length_check(self):
        s = ''
        for frame_idx, frame in enumerate(self.command_info):
            for command_idx, command in enumerate(frame):
                input_dwsize = 0
                if 'input_dwsize' in command and command['input_dwsize']:
                    input_dwsize = int(command['input_dwsize'])
                if 'def_dwsize' in command and command['def_dwSize']:
                    def_dwsize = int(command['def_dwSize'])
                if command['dwords']:
                    last_dword_no = command['dwords'][-1]['NO']
                    if last_dword_no.find('_') != -1:
                        idx = last_dword_no.rfind('_')
                        last_dword_no = last_dword_no[idx + 1:]
                    last_dword_no = int(last_dword_no)
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
        command_info_cp = copy.deepcopy(self.command_info)
        for frame_idx, frame in enumerate(command_info_cp):
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
        return command_info_cp

    @Slot()
    def generate_xml(self):
        if not self.command_info:
            pass
        if self.platform == "IGFX_UNKNOWN":
            self.show_message('Fail to generate the reference. \nPlease check the Platform setting in the main page.', '')
            return
        
        command_info_cp = self.split_dword()
        lines = ['<?xml version="1.0"?>\n']
        lines.append('<' + self.test_name + '>\n')
        lines.append('  <Platform name="' + self.platform + '">\n')
        for frame_idx, frame in enumerate(command_info_cp):
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
                    # if all field uncheck, dwrod uncheck
                    #if cmd['name'] == "MI_BATCH_BUFFER_START_CMD" and len(dword['fields']) > 0 and "obj_fields" in dword['fields'][0]:
                    #    #flag = False
                        #for field in dword['fields']:
                        #    if any(obj_field['CHECK'] == 'Y' for obj_field in field["obj_fields"] if 'CHECK' in obj_field):
                        #        flag = True
                        #        break
                        #if not flag:
                        #    dword['check'] = 'N'
                    #elif all(field['CHECK'] == 'N' for field in dword['fields'] if 'CHECK' in field):
                    #    dword['check'] = 'N'

                    for key, value in dword.items():
                        if key != 'fields' and value:
                            s_dword = s_dword + ' ' + key + '="' + str(value) + '"'
                    s_dword = s_dword + '>\n'
                    lines.append(s_dword)

                    if 'check' in dword and dword['check'] == 'Y':
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
                                continue
                            if 'CHECK' in field and field['CHECK'] == 'Y':
                            #if not field['field_name'].startswith('Reserve'):
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
        file_name = self.test_name + 'Reference.xml'
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
        self.update_cmd_check_state = False
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
            self.parse_command_file()
            self.read_command_info_from_xml(False)        
            if self.sameTest:
                if self.sameCommandList():
                    msgBox = QMessageBox()
                    msgBox.setText("Do you want to reload previous check state?")
                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    ret = msgBox.exec();
                    if ret == QMessageBox.Yes:
                        self.loadCheckState()
            self.show_command_info()
            self.form.showcmdlist()
        self.update_cmd_check_state = True
    
    # RETURN TRUE if current command_info has same frame and same command with previous command_info loaded from generated xml
    def sameCommandList(self):
        testname = self.ui.lineEditTestName.text()
        fileFullName = self.output_path + '\\' + testname + 'Reference.xml'
        if not os.path.exists(fileFullName):
            return False
        tree = ET.parse(fileFullName) 
        root = tree.getroot()       
        frames = root.findall(".//Frame")
        if len(self.command_info) != len(frames):
            return False
        for frame_idx, frame in enumerate(frames):
            # check cmd number
            if len(self.command_info[frame_idx]) != len(frame):
                return False
            # check cmd name
            for cmd_idx, cmd in enumerate(frame):
                if cmd.attrib['name'] != self.command_info[frame_idx][cmd_idx]['name']:
                    return False
        return True

    def loadCheckState(self):
        testname = self.ui.lineEditTestName.text()
        fileFullName = self.output_path + '\\' + testname + 'Reference.xml'
        if not os.path.exists(fileFullName):
            return
        tree = ET.parse(fileFullName) 
        root = tree.getroot()       
        pre_frames = root.findall(".//Frame")
        for frame_idx, frame in enumerate(self.command_info):
            pre_frame = pre_frames[frame_idx]
            pre_commands = pre_frame.findall("CMD")
            for cmd_idx, command in enumerate(frame):
                check = True
                command['check'] = pre_commands[cmd_idx].attrib['check']
                if command['check'] == 'N':
                    check = False
                pre_dwords = pre_commands[cmd_idx].findall("dword")
                pre_dwords_index = 0
                for dword_idx, dword in enumerate(command['dwords']):
                    if not check:
                        dword['check'] = 'N'
                    else:
                        dword['check'] = pre_dwords[pre_dwords_index].attrib['check']
                        # when dword['NO'] is a single number or latter number, add index
                        if dword['NO'] == pre_dwords[pre_dwords_index].attrib['NO'] or dword['NO'].endswith(pre_dwords[pre_dwords_index].attrib['NO']):
                            pre_dwords_index += 1
                        if dword['check'] == 'N':
                            check = False
                    pre_fields = list(pre_dwords[dword_idx])
                    pre_fields_index = 0
                    for field_idx, field in enumerate(dword['fields']):
                        if command['name'] == 'MI_BATCH_BUFFER_START_CMD' and 'obj_fields' in field:
                            for obj_field_idx, obj_field in enumerate(field['obj_fields']):
                                if not check:
                                    obj_field['CHECK'] = 'N'
                                    continue
                                if pre_fields[pre_fields_index].tag != obj_field['obj_field_name']:
                                    continue
                                obj_field['CHECK'] = pre_fields[pre_fields_index].attrib['CHECK']
                            continue
                        if not check:
                            field['CHECK'] = 'N'
                        else:
                            if pre_fields_index >= len(pre_fields):
                                break
                            if pre_fields[pre_fields_index].tag != field['field_name']:
                                continue
                            field['CHECK'] = pre_fields[pre_fields_index].attrib['CHECK']
                            pre_fields_index += 1


        #for frame_idx, frame in enumerate(frames):
        #    for cmd_idx, cmd in enumerate(frame):
        #        self.command_info[frame_idx][cmd_idx]['CHECK'] = cmd.attrib['check']
        #        check = True
        #        if cmd.attrib['check'] = 'N':
        #            check =

        #        for dword_idx, dword in enumerate(cmd):
        #            self.command_info[frame_idx][cmd_idx]['dwords'][dword_idx]['CHECK'] = dword.attrib['check']
        #            for field_idx, field in enumerate(dword):
        #                self.command_info[frame_idx][cmd_idx]['dwords'][dword_idx]['fields'][field_idx] = field.attrib['check']
        #return True

    @Slot()
    def cpfiles(self):
        l = [self.inputpath, self.ringinfo_path]
        for i in l:
            dstdir = os.path.join(self.output_path, os.path.basename(i))
            #delete former folder first
            shutil.rmtree(dstdir, ignore_errors=True)
            os.makedirs(dstdir) # create directories, raise an error if it already exists
            for f in os.listdir(i):
                full_f = os.path.join(i, f)
                if full_f.find('.txt') != -1 or full_f.find('.dat') != -1:
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
GUID = {self.GUID}
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
                f_integrated_cfg_cpp = os.path.join(os.path.dirname(self.workspace), 'encode_integrated_test_cfg.cpp')
                with open(f_integrated_cfg_cpp, 'r') as fin:
                    lines = fin.readlines()
                
                newlines = []
                newlines.append('    {"' + self.capitalize_word(self.test_name) + '",' + ' ' * (50 - len(self.test_name)) + '{   IDR_' + self.test_name.upper() + '_REFERENCE,\n')
                newlines.append(' '*62 + 'IDR_' + self.test_name.upper() + '_INPUT,\n')
                newlines.append(' '*62 + '{"' + self.platform + '"},\n')
                newlines.append(' '*62 + self.GUID + '\n')
                newlines.append(' '*58 + '}\n')
                newlines.append('    },\n')
                

                for idx, line in enumerate(lines):
                    if re.search(f'\s*{{"{self.capitalize_word(self.test_name)}",\s*' , line):
                    ###update existed testname
                        newlines = lines[:idx] + newlines + lines[idx+6:]
                        break

                    if line.strip() == '};':
                        if lines[idx-1].strip() == '}':
                            lines[idx-1] = '    },\n'
                        newlines = lines[:idx] + newlines + [line]
                        break

                if newlines[-2].strip() == '},':
                    newlines[-2] = '    }\n'

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



    def read_test_cfg_cpp(self, name, component='encode'):
        if component == 'encode':
            f_integrated_cfg_cpp = os.path.join(os.path.dirname(self.workspace), 'encode_integrated_test_cfg.cpp')
            with open(f_integrated_cfg_cpp, 'r') as fin:
                lines = fin.readlines()
                
            idx = [idx for idx, line in enumerate(lines) if re.search(f'\s*{{"{self.capitalize_word(self.test_name)}",\s*' , line)]
            # self.sameTest records whether previous test exist with same testname,guid,platform,frame,command_list
            self.sameTest = False
            if idx:
                self.pre_platform = re.match('{"(.*)"}', lines[idx[0]+2].strip()).group(1)
                self.pre_GUID = lines[idx[0]+3].strip()
                fg = []
                if self.pre_platform != self.platform:
                    fg.append(0)
                if self.GUID and self.GUID != self.pre_GUID:
                    fg.append(1)
                
                if not fg:
                    self.sameTest = True

                if fg:
                    text = ''
                    if 1 in fg and name == 'GUID':
                        text = 'Current GUID %s is different from previous configuration: %s\n' %(self.GUID, self.pre_GUID)
                    elif 0 in fg and name == 'platform':
                        text = 'Current platform %s is different from previous configuration: %s\n' %(self.platform, self.pre_platform)
                    fg = [] #clear
                    if text:
                        msgBox = QMessageBox()
                        msgBox.setWindowTitle('Testname Error')
                        msgBox.setInformativeText(text)
                        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                        msgBox.setDefaultButton(QMessageBox.Cancel)
                        buttonY = msgBox.button(QMessageBox.Ok)
                        buttonY.setText('Rewrite')
                        buttonN = msgBox.button(QMessageBox.Cancel)
                        buttonN.setText('Discard')
                        msgBox.exec_()
                        self.activateWindow()
                        if msgBox.clickedButton() == buttonY:
                            return True
                        elif msgBox.clickedButton() == buttonN:
                            return False
     
        return True

class FormCommandInfo(QWidget):
    def __init__(self, main_window):
        super(FormCommandInfo, self).__init__()
        self.ui = Ui_FormCommandInfo()
        self.ui.setupUi(self)
        self.info = []
        self.main_window = main_window
        self.ui.pushButtonGen.clicked.connect(self.save)
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
        #used for loading cmdlist history
        self.pre_testname = ''
        self.pre_platform = ''
        self.pre_platform1 = ''
        self.pre_component = ''
        self.pre_ringinfopath = ''
        #
        self.ui.stackedWidget.setCurrentIndex(1)   #set the all infomation page as default page
        self.ui.pushButtonSCL.clicked.connect(self.showcmdlist)  #show cmd name list
        self.ui.pushButtonSA.clicked.connect(lambda : self.ui.stackedWidget.setCurrentIndex(0))  #show cmd name list
        self.ui.pushButtonSU.clicked.connect(self.updateinfo)
        self.ui.tableWidgetCmdlist.cellDoubleClicked.connect(self.modifycmd)

        self.ui.treeWidgetCmd.itemDoubleClicked.connect(self.main_window.show_command_table)
        self.ui.treeWidgetCmd.itemChanged.connect(self.update_tree_checkstate)
        self.ui.treeWidgetCmd.itemDoubleClicked.connect(self.save)
        
        self.ui.treeWidgetCmd.itemClicked.connect(self.main_window.show_command_table)
        self.ui.treeWidgetCmd.itemClicked.connect(self.save)
        
        

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
            if table.cellWidget(i, 7) and table.cellWidget(i, 7).isChecked():
                command = self.info[int(self.row_command_map[i]['frame_idx'])][int(self.row_command_map[i]['command_idx'])]
                dword = 'dword' + command['dwords'][int(self.row_command_map[i]['dword_idx'])]['NO']
                field = table.item(i, 2).text()
                value = self.item_text_to_dec(table.item(i, 6).text())
                min_value = self.item_text_to_dec(table.item(i, 9).text())
                max_value = self.item_text_to_dec(table.item(i, 10).text())
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

    def item_text_to_dec(self, s):
        if s:
            if self.mode == 'hex':
                return int(s, 16)
            if self.mode == 'bin':
                return int(s,2)
            if self.mode == 'dec':
                return int(s)

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
        if len(self.row_command_map) == 0 or 'frame_idx' not in self.row_command_map[0] or 'command_idx' not in self.row_command_map[0]:
            return
        frame_idx = int(self.row_command_map[0]['frame_idx'])
        command_idx = int(self.row_command_map[0]['command_idx'])
        #dwords = self.info[frame_idx][command_idx]['dwords']
        #fields = []
        #for dword in dwords:
        #    for field in dword['fields']:
        #        if 'obj_fields' in field:
        #            fields.extend(field['obj_fields'])
        #        else:
        #            fields.append(field)
        #dword_index = -1
        cmd_item = tree.topLevelItem(0).child(frame_idx).child(command_idx)
        if cmd_item.checkState(0) == Qt.CheckState.Checked:
            self.info[frame_idx][command_idx]['check'] = 'Y'
        else:
            self.info[frame_idx][command_idx]['check'] = 'N'
        dword_check_states = []
        for i in range(cmd_item.childCount()):
            if cmd_item.child(i).checkState(0) == Qt.CheckState.Checked:
                dword_check_states.append('Y')
            else:
                dword_check_states.append('N')
        for i in range(table.rowCount()):
            #dword_index += 1
            #dword = self.info[int(self.row_command_map[i]['frame_idx'])][int(self.row_command_map[i]['command_idx'])]['dwords'][int(self.row_command_map[i]['dword_idx'])]
            #if dword:
            if not table.item(i, 2):
                continue
            field_name = str(table.item(i, 2).text())
            dword_index = int(self.row_command_map[i]['dword_idx'])
            if dword_index < len(self.info[frame_idx][command_idx]['dwords']):
                dword = self.info[frame_idx][command_idx]['dwords'][dword_index]
                target_field = None
                for field in dword['fields']:
                    if 'obj_fields' in field:
                        for obj_field in field['obj_fields']:
                            if obj_field['obj_field_name'] == field_name:
                                target_field = obj_field
                                break
                        if target_field != None:
                            break
                    if field_name == field['field_name']:
                        target_field = field
                        break
                if target_field != None:
                    target_field['value'] = str(table.item(i, 6).text())
                    if table.cellWidget(i, 7).isChecked():
                        target_field['CHECK'] = 'Y'
                        dword_check_states[dword_index] = 'Y'
                    else:
                        target_field['CHECK'] = 'N'
                    if self.mode == 'bin':
                        target_field['value'] = hex(int(str(table.item(i, 6).text()), 2))
                        target_field['min_value'] = hex(int(str(table.item(i, 9).text()), 2))
                        target_field['max_value'] = hex(int(str(table.item(i, 10).text()), 2))
                    elif self.mode == 'dec':
                        target_field['value'] = hex(int(str(table.item(i, 6).text())))
                        target_field['min_value'] = hex(int(str(table.item(i, 9).text())))
                        target_field['max_value'] = hex(int(str(table.item(i, 10).text())))
                    else:
                        target_field['value'] = str(table.item(i, 6).text())
                        target_field['min_value'] = str(table.item(i, 9).text())
                        target_field['max_value'] = str(table.item(i, 10).text())
        # update dword check state
        for dword_idx, dword in enumerate(self.info[frame_idx][command_idx]['dwords']):
            dword['check'] = dword_check_states[dword_idx]
        self.main_window.command_info = self.info

    @Slot(QTreeWidgetItem, int)
    def update_tree_checkstate(self, item, column):
        if not self.main_window.update_cmd_check_state:
            return
        # get frame index
        treeRoot = self.main_window.form.ui.treeWidgetCmd
        frame_item = item.parent()
        while not frame_item.text(0).startswith("frame"):
            frame_item = frame_item.parent()
        frame_idx = int(frame_item.text(0)[5:])
        
        # MI_BATCH_BUFFER_START_CMD can only be unchecked if no cmd in its unit is checked
        if item.text(0) == 'MI_BATCH_BUFFER_START_CMD' and item.checkState(0) == Qt.CheckState.Unchecked:
            if not self.uncheck_MI_BATCH_BUFFER_START_CMD(item, frame_idx):
                item.setCheckState(0, Qt.CheckState.Checked)
                return

        if item.checkState(0) == Qt.CheckState.Checked:
            state = 'Y'
        else:
            state = 'N'
        # change state in self.main_window.command_info
        command_idx = frame_item.indexOfChild(item)
        if command_idx >= 0:
            # if changed item is a command
            self.changeCommandCheckState(state, frame_idx, command_idx, recursive = False)
        else:
            command_idx = frame_item.indexOfChild(item.parent())
            if command_idx >= 0:
                # if changed item is a dword
                dword_idx = item.parent().indexOfChild(item)
                self.changeCommandCheckState(state, frame_idx, command_idx, dword_idx = dword_idx, recursive = False)
            else:
                command_idx = frame_item.indexOfChild(item.parent().parent())
                if command_idx >= 0:
                    # if changed item is a field
                    dword_idx = frame_item.child(command_idx).indexOfChild(item.parent())
                    field_idx = item.parent().indexOfChild(item)
                    self.changeCommandCheckState(state, frame_idx, command_idx, dword_idx = dword_idx, field_idx = field_idx, recursive = False)
                else:
                    # if changed item is a obj_field
                    command_idx = frame_item.indexOfChild(item.parent().parent().parent())
                    dword_idx = frame_item.child(command_idx).indexOfChild(item.parent().parent())
                    obj_idx = frame_item.child(command_idx).child(dword_idx).indexOfChild(item.parent())
                    obj_field_idx = item.parent().indexOfChild(item)
                    self.changeCommandCheckState(state, frame_idx, command_idx, dword_idx = dword_idx, field_idx = obj_idx, obj_field_idx = obj_field_idx, recursive = False)
        
        for i in range(item.childCount()):
            dword = item.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                dword.setCheckState(0, Qt.CheckState.Checked)
            else:
                dword.setCheckState(0, Qt.CheckState.Unchecked)
        # check MI_BATCH_BUFFER_START_CMD of this unit if not checked
        if item.checkState(0) == Qt.CheckState.Checked:
            self.check_MI_BATCH_BUFFER_START_CMD(item, frame_idx)

        #if item.checkState(column) == Qt.CheckState.Checked:
        #    print('Item Checked')
        #elif item.checkState(column) == Qt.CheckState.Unchecked:
        #    print('Item Unchecked')

    def changeCommandCheckState(self, state, frame_idx, cmd_idx, dword_idx = -1, field_idx = -1, obj_field_idx = -1, recursive = True):
        command = self.main_window.command_info[frame_idx][cmd_idx]
        command['check'] = state
        if dword_idx != -1:
            command['dwords'][dword_idx]['check'] = state
        if field_idx != -1:
            if obj_field_idx != -1:
                command['dwords'][dword_idx]['fields'][field_idx]['obj_fields'][obj_field_idx]['CHECK'] = state
            else:
                command['dwords'][dword_idx]['fields'][field_idx]['CHECK'] = state
        if not recursive:
            return
        if dword_idx != -1:
            dwords = [command['dwords'][dword_idx]]
        else:
            dwords = command['dwords']
        for dword in dwords:
            dword['check'] = state
            if field_idx != -1:
                fields = [dword['fields'][field_idx]]
            else:
                fields = dword['fields']
            for field in fields:
                if 'obj_fields' in field:
                    if obj_field_idx != -1:
                        field['obj_fields'][obj_field_idx]['CHECK'] = state
                        return
                    for obj_field in field['obj_fields']:
                        obj_field['CHECK'] = state
                else:
                    field['CHECK'] = state

        

    def uncheck_MI_BATCH_BUFFER_START_CMD(self, item, frame_idx):
    #  if any command in unit start with item(MI_BATCH_BUFFER_START_CMD) is checked, item should be checked
        treeRoot = self.main_window.form.ui.treeWidgetCmd
        frame = treeRoot.topLevelItem(0).child(frame_idx)
        command_idx = frame.indexOfChild(item)
        require_endcmd_num = 1
        for i in range(command_idx+1, frame.childCount()):
            if frame.child(i).checkState(0) == Qt.CheckState.Checked:
                return False
            if frame.child(i).text(0) == 'MI_BATCH_BUFFER_END_CMD':
                require_endcmd_num -= 1
                if require_endcmd_num == 0:
                    return True
            if frame.child(i).text(0) == 'MI_BATCH_BUFFER_START_CMD':
                require_endcmd_num += 1
        return True

    def check_MI_BATCH_BUFFER_START_CMD(self, item, frame_idx):
        treeRoot = self.main_window.form.ui.treeWidgetCmd
        frame = treeRoot.topLevelItem(0).child(frame_idx)
        # get command index when user tick a command
        item_point = item
        command_idx = frame.indexOfChild(item_point)
        # git command index when user tick a dword
        while command_idx < 0:
            item_point = item_point.parent()
            command_idx = frame.indexOfChild(item_point)
        # ignore the last MI_BATCH_BUFFER_END_CMD
        require_startcmd_num = -1
        ignore_startcmd_num = 0
        for i in range(command_idx,frame.childCount()):
            if frame.child(i).text(0) == 'MI_BATCH_BUFFER_END_CMD':
                require_startcmd_num += 1
        for i in reversed(range(command_idx)):
            if frame.child(i).text(0) == 'MI_BATCH_BUFFER_END_CMD':
                ignore_startcmd_num += 1
            if frame.child(i).text(0) == 'MI_BATCH_BUFFER_START_CMD':
                if ignore_startcmd_num > 0:
                    ignore_startcmd_num -= 1
                else:
                    require_startcmd_num -= 1
                    if frame.child(i).checkState(0) == Qt.CheckState.Unchecked:
                        frame.child(i).setCheckState(0, Qt.CheckState.Checked)
                        self.changeCommandCheckState('Y', frame_idx, i)
                    if require_startcmd_num == 0:
                        break

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

        #not update case or modifycmd case
        self.ui.stackedWidget.setCurrentIndex(1)
        if self.main_window.ui.lineEditTestName == self.pre_testname and self.main_window.ui.lineEditPlatform == self.pre_platform1 and \
           self.main_window.ui.lineEditRinginfoPath == self.pre_ringinfopath and self.main_window.ui.lineEditComponent == self.pre_component and \
           not self.modifylist:
            return

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
                #print(self.main_window.obj.size_error)
                warning = 'Size Error in position: '
                for i in self.main_window.obj.size_error_cmd[cmd]:
                    warning += str(i) + ','
                warning = warning.strip(',')
                self.table.setItem(row, 3, QTableWidgetItem(warning))
            #mark newly modified cmd
            if [t for t in self.modifylist if t[1] == cmd]:
                self.table.item(row, 0).setBackground(QColor(255, 242, 0))
            row += 1

        self.pre_platform1 = self.main_window.ui.lineEditPlatform.text()
        self.pre_testname = self.main_window.ui.lineEditTestName.text()
        self.pre_ringinfopath = self.main_window.ui.lineEditRinginfoPath.text()
        self.pre_component = self.main_window.ui.lineEditComponent.text()
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
            if new != cmdname and ok:
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
        
        if dir:
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




if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.activateWindow()
    sys.exit(app.exec_())