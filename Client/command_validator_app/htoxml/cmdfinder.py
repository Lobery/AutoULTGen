import os
import shutil
from htoxml.Parser.header_parser import HeaderParser
#from Parser.header_parser import HeaderParser #run directly from this file
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import (
    Element, SubElement, XML, Comment
)
from ElementTree_pretty import prettify
import re
import copy
import time


class CmdFinder(object):
    def __init__(self, source, gen, ringpath):
        self.source = source
        self.gen = gen
        self.ringpath = ringpath
        self.ringfilename = ''
        self.ringfilelist = []
        #
        self.ringcmddic = {}  #count each cmd 
        self.ringcmdclass = {}  # record each cmd class
        self.notfoundset = set() #record not found cmd
        self.size_error = set() 
        self.size_error_cmd = {}
        self.bitfield_error_cmd = set()
        self.size_right_cmd = {}
        self.ringcmdmodify = {}
        self.df_dic = {}
        self.full_ringinfo = {}   # {'0':[{'MI_LOAD_REGISTER_IMM': ['1108101d', '00000244']},...]} , '0' is frame_no
        #self.same = [['_ON_OFF','_CHECK'],['VEB','VEBOX'],['COST','COSTS'],['QMS','QM'],['IMAGE','IMG'],['WEIGHTSOFFSETS','WEIGHTS_OFFSETS'], ['CMD_HCP_VP9_RDOQ_STATE', 'HEVC_VP9_RDOQ_STATE_CMD']]
        self.same = [['_ON_OFF','_CHECK'],['VEB','VEBOX'],['COST','COSTS'],['QMS','QM'],['IMAGE','IMG'],['WEIGHTSOFFSETS','WEIGHTS_OFFSETS']]
        self.ignored = ['CMD', 'COMMAND', 'OBJECT', 'MEDIA', 'STATE']

        self.searchpattern = [r'^((?!_x).)*$', 'x'] #first search in class without x, then class with x
        self.TestName = Element('TestName')  #create TestName as result root node
        self.filter = ['mi', 'hcp']
        self.Frame_Num = 0
        self.specialcmd = ['MI_STORE_DATA_IMM', 'MI_FLUSH_DW'] #specialcmd has different dwsize rules
        self.source_dic = {} # {source1:1, source2:2} record source-element index
        self.Buf = Element('Buf')   ##save all the parsed h2xml info 

    def writexml(self, output_path = ''):
        if output_path:
            with open( os.path.join(output_path ,  "mapringinfo.xml") , "w") as f:
                f.write(prettify(self.TestName))
        else:
            with open( os.path.join(self.ringpath ,  "mapringinfo.xml") , "w") as f:
                f.write(prettify(self.TestName))
        return prettify(self.TestName)
    
    def modifyringcmd(self, wrong, right, index = 'all'):
        # record modifycmd operation in UI
        # index == 'all' means changing all cmd
        # index == [1,3] means changing specific index cmd
        #print(self.ringcmdset)
        self.ringcmdmodify[wrong] = (right, index)
        self.ringcmdclass[right] = ''

        #           self.size_right_cmd[ringcmd] = []
        #if ringcmd not in self.size_error_cmd:
        #    self.size_error_cmd[ringcmd] = []
        if index == 'all':
            self.ringcmddic[right] = self.ringcmddic.pop(wrong)
        else:
            self.ringcmddic[wrong] -= len(index)
            if self.ringcmddic[wrong] == 0:
                del self.ringcmddic[wrong]
            if right in self.ringcmdmodify:
                self.ringcmddic[right] += len(index)
            else:
                self.ringcmddic[right] = len(index)

    def undate_full_ringinfo(self):
        # after modify cmd in UI, update full_ringinfo so the entire mapcmd table could also be updated
        # full_ringinfo: {'0':[{'MI_LOAD_REGISTER_IMM': ['1108101d', '00000244']},...]} , '0' is frame_no
        new_full_ringinfo = {}
        dic = {}
        for frame_no, ringinfo in self.full_ringinfo.items():
            new_ringinfo = []
            for pair in ringinfo:
                for ringcmd, value_list in pair.items():
                    if ringcmd in dic:
                        dic[ringcmd] += 1
                    else:
                        dic[ringcmd] = 1
                    if ringcmd in self.ringcmdmodify and (self.ringcmdmodify[ringcmd][1] == 'all' or self.ringcmdmodify[ringcmd][1] != 'all' and dic[ringcmd] in self.ringcmdmodify[ringcmd][1]):
                        new_ringinfo.append({self.ringcmdmodify[ringcmd][0] : value_list})
                    else:
                        new_ringinfo.append(pair)
            new_full_ringinfo[frame_no] = new_ringinfo

        self.ringcmdmodify = {} # clear 
        self.full_ringinfo = new_full_ringinfo
        return new_full_ringinfo

    def updatexml(self, index = 0):
        # after modify cmd in UI, update xml according to the new full_ringinfo
        TestName = self.TestName
        
        # clear
        self.TestName = Element('TestName') 
        self.size_error = set()
        self.size_error_cmd = {}
        self.size_right_cmd = {}
        self.notfoundset = set()
        self.bitfield_error_cmd = set()

        platform_group = SubElement(self.TestName, 'Platform', {'name': ''})
        # full_ringinfo: {'0':[{'MI_LOAD_REGISTER_IMM': ['1108101d', '00000244']},...]} , '0' is frame_no
        for frame_no, ringinfo in self.full_ringinfo.items():
            frame_group = SubElement(platform_group, 'Frame', {'NO': frame_no})
            for pair in ringinfo:
                for ringcmd, value_list in pair.items():
                    if not self.memory(TestName, ringcmd, value_list, frame_group, index):
                        # cal time
                        start1 = time.clock()
                        frame_group = self.mapcmd(ringcmd, value_list, frame_group, index)
                        #print("MAP Time used:", time.clock() - start1, ",  index = ", index)
                    self.cmdsizecheck(ringcmd, index)
                    index += 1

    def cmdsizecheck(self, ringcmd, index):
        #create size_error and size_right cmd index list
        if ringcmd not in self.size_right_cmd:
            self.size_right_cmd[ringcmd] = []
        if ringcmd not in self.size_error_cmd:
            self.size_error_cmd[ringcmd] = []
        if index in self.size_error: #self.size_error records position(index) size_error happens
            #{ringcmd:[size error position index]}
            self.size_error_cmd[ringcmd].append(len(self.size_right_cmd[ringcmd]) + len(self.size_error_cmd[ringcmd]) + 1)
        else:
            #{ringcmd:[size right  position index]}
            self.size_right_cmd[ringcmd].append(len(self.size_right_cmd[ringcmd]) + len(self.size_error_cmd[ringcmd]) + 1)
    
    def setbitfield(self, current_group,structcmdname, fieldname, bit_value, bit_l, bit_h, dw_no, check = ''):
        #set bitfield attributes
        bitfield_group = SubElement(current_group, fieldname, {'default_value': bit_value, 
                                                                        'min_value': bit_value,
                                                                        'max_value': bit_value,
                                                                        'bitfield_l': bit_l,
                                                                        'bitfield_h': bit_h})   #set hex value , which represents defalt value of a bitfield
        
        if 'address' in fieldname.lower() and int(bit_h) - int(bit_l) > 16:
            bitfield_group.set('Address', 'Y')
            bitfield_group.set('CHECK', 'N')
        elif 'Reserved' in fieldname :
            bitfield_group.set('Address', 'N')
            bitfield_group.set('CHECK', 'N')
        #elif dw_no == '0':
        #    bitfield_group.set('CHECK', 'Y')
        else:
            bitfield_group.set('Address', 'N')
            bitfield_group.set('CHECK', 'Y')
        #if check:
            #bitfield_group.set('CHECK', check)
        if 'vdcontrolstatebody' in fieldname.lower():
            bitfield_group.set('CHECK','N')
        
        if 'pak_insert_object' in structcmdname.lower():
            bitfield_group.set('CHECK','N')
        if 'mi_noop_cmd' in structcmdname.lower():
            bitfield_group.set('CHECK','N')
        if 'surface_state_cmd' in structcmdname.lower():
            bitfield_group.set('CHECK','N')
        return current_group

    def memory(self, Element, ringcmd, value_list, node, index):
        #check if ringcmd exists in current testname
        #if so, copy directly to save search time
        binv_list = [ bin(int(i, 16))[2:].zfill(32) for i in value_list ]
        input_dwsize = len(value_list)
        #print(ringcmd + '\n')
        #xpath = ".//CMD[@name='%s']" % ringcmd
        #print(xpath)
        #cmd = self.TestName.find(xpath)
        #cmd = self.TestName.find(".//CMD[@name='MI_FORCE_WAKEUP']")
        start2 = time.clock()
        for source in self.source:
            media_source_idx = self.source_dic.get(source)
            cmd = Element.find(".//CMD[@media_source_idx='%s']" % str(media_source_idx))  #search by media source priority
            if cmd:
                if self.searchkword(ringcmd, cmd.attrib['name']):
                    dupe = copy.deepcopy(cmd)
                
                    #check dwsize
                    if 'def_dwSize' in dupe.attrib:
                        diff = int(dupe.attrib['def_dwSize']) - input_dwsize
                        if not (ringcmd in self.specialcmd and (diff == 0 or diff == 1)):
                            if diff > 0:
                                self.size_error.add(index)

                    dupe.attrib['input_dwsize'] = str(input_dwsize)
                    dupe.attrib['index'] = str(index)

                    for dword_group in dupe.findall("dword"):
                        if 'unmappedstr' not in dword_group.attrib:
                            dw_no = dword_group.attrib['NO']
                            val_str = self.findval(value_list, dw_no)['val_str']
                            dword_group.attrib['value'] = val_str
                        else:
                            #delete previous unmapped str
                            dupe.remove(dword_group)

                        for field in dword_group.findall(".//*[@bitfield_h]"):
                            fieldname, bit_l, bit_h = field.tag, field.attrib['bitfield_l'], field.attrib['bitfield_h']
                            bit_value = self.findbitval(binv_list, list((bit_l, bit_h)), dw_no)[0]
                            field.attrib['default_value'] = bit_value
                            field.attrib['max_value'] = bit_value
                            field.attrib['min_value'] = bit_value
                            if fieldname == "DwordLength":
                                dw_len = int(bit_value,16) 
                                dupe.attrib['DW0_dwlen'] = str(dw_len)
                                if not self.checkdwlen(dw_len, input_dwsize) and ringcmd not in self.specialcmd:
                                    self.size_error.add(index)
                            
                    dupe= self.unmapdw( dupe, dw_no, value_list)
                    node.append(dupe) #insert the new node
                    #print("Search saved xml Time used:", time.clock() - start2)
                    return True

        return False

    def checkdwlen(self, dw_len, input_dwsize):
        if input_dwsize < 2 and dw_len ==0:
            return True
        if dw_len == input_dwsize-2:
            return True
        return False
            
    def mapcmd(self, ringcmd, value_list, node, index):
        # map each ringcmd
        # para ringcmd: in ringcmdinfo cmd stringcmd, e.g.  "CMD_SFC_STATE_OBJECT"
        # para value_list: hex stringcmd stream split in list,  eg. ['75010020', '00000041', '00ff00ff', '00000005', '00080350', '00ff00ff', '00000000', '00ff00ff', '00ff00ff', '00000000', '00000000', '00000000', '00000000', '000003ff', '00020000', '00020000', '00000000', '00f10000', '00000001', '00000000', '00e6b000', '00000001', '0000000e', '001b5000', '00000001', '0000000e', '00000000', '00000000', '00000000', '50000ffb', '00000000', '00000000', '00000000', '00000000']

        # return xml tree which map ringcmdinfo value in cmd struct definition
    

        binv_list = [ bin(int(i, 16))[2:].zfill(32) for i in value_list ]   #each dword length = 32 bits(include leading 0)
        
        #for platform in self.classpath:
        #    for r,d,f in os.walk(self.source):
        #        #filter test folder
        #        if r'\ult\agnostic\test' not in r:
        #            continue
        #        os.chdir(r)
        #        for thing in f:
        #            # find required cmd in xml file
        #            if [i for i in self.filter if i not in ringcmd.lower() or i in ringcmd.lower() and i in thing] :
        #                if thing.startswith('mhw_') and thing.endswith('.h.xml') and platform in thing:
        #                    if  self.gen == 'all' or self.gen != 'all' and str(self.gen) in thing:
                                #tree = ET.parse(thing)
                                #root = tree.getroot()
        
        for source in self.source:
            media_source_idx = self.source_dic.get(source)
            elem = self.Buf.find("./Elem[@index='%s']" % str(media_source_idx))
            for content in elem.findall('./content'):
                for Class in content.findall('./class'):
                    for pattern in self.searchpattern:
                        if 'name' in Class.attrib and re.search(pattern, Class.attrib['name'].lower()) and [i for i in self.filter if i not in ringcmd.lower() or i in ringcmd.lower() and i in Class.attrib['name'].lower()]:
                                        #for Class in root.findall('class'):
                                            for structcmd in Class.iter('struct'):
                                                # search cmd in all the local files
                                                if 'name' in structcmd.attrib and self.searchkword(ringcmd, structcmd.attrib['name']):
                                                    #Class_group = SubElement(ringcmd_group, 'class', {'name' : Class.attrib['name']})  #debug
                                                    input_dwsize = len(value_list)
                                                    structcmd_group = SubElement(node, 'CMD',  {'name' : structcmd.attrib['name'],
                                                                                                'class' : Class.attrib['name'],
                                                                                                'index' : str(index),
                                                                                                'input_dwsize' : str(input_dwsize),
                                                                                                'media_source_idx' : str(media_source_idx)})
                                                    dw_len = 0
                                                    dw_no = ''
                                                    if not self.ringcmdclass[ringcmd]:
                                                        self.ringcmdclass[ringcmd] = Class.attrib['name']
                                                    for unionorcmd in structcmd.findall("./"):  #select all the direct children

                                                        if unionorcmd.tag == 'union' and 'name' in unionorcmd.attrib and 'DW' in unionorcmd.attrib['name']:
                                                            dw_no = unionorcmd.attrib['name'].strip('DW')
                                                            val_str = self.findval(value_list, dw_no)['val_str']
                                                            dword_group = SubElement(structcmd_group, 'dword', {'NO' : dw_no,
                                                                                                                'value': val_str})
                                                            current_group = dword_group
                                                            for s in unionorcmd.findall('struct'):
                                                                # 1 dword has several objs
                                                                if 'name' in s.attrib:
                                                                    obj_group = SubElement(current_group, s.attrib['name'], {'value': val_str})
                                                                    current_group = obj_group

                                                                last_bit_h = -1 #used to check bitfield
                                                                for elem in s.findall("./"):

                                                                    #check bitfield---
                                                                    if last_bit_h>0 and not int(last_bit_h) % 32:
                                                                        #check if last bit field end with 32/64
                                                                        print(ringcmd+' bitfield_h =%s error!\n' % bit_h)
                                                                        self.bitfield_error_cmd.add(ringcmd)
                                                                    last_bit_h = -1 #used to check bitfield
                                                                    #check bitfield end---

                                                                    if 'name' in elem.attrib:
                                                                        fieldname = elem.attrib['name']
                                                                        if 'bitfield' in elem.attrib :
                                                                            bit_item = elem.attrib['bitfield'].split(',')  #bitfield="0,  5"
                                                                        else:
                                                                            bit_item = []
                                                                        bit_value, bit_l, bit_h = self.findbitval(binv_list, bit_item, dw_no)

                                                                        #check bitfield---
                                                                        if last_bit_h == int(bit_l):
                                                                            self.bitfield_error_cmd.add(ringcmd)
                                                                        last_bit_h = int(bit_h)
                                                                        #check bitfield end---

                                                                        current_group=self.setbitfield(current_group, structcmd.attrib['name'], fieldname, bit_value, bit_l, bit_h, dw_no)

                                                                        #if structcmd_group.attrib['name'] == 'MI_NOOP_CMD':
                                                                        #    current_group = self.setbitfield(current_group, fieldname, bit_value, bit_l, bit_h, dw_no, 'N')
                                                                        #else:
                                                                        #    current_group = self.setbitfield(current_group, fieldname, bit_value, bit_l, bit_h, dw_no)

                                                                        #complement undefined dword length, for unmapped buffer stream
                                                                        if fieldname == "DwordLength":
                                                                            dw_len = int(bit_value,16) 
                                                                            structcmd_group.set('DW0_dwlen', str(dw_len))
                                                                            # check dwsize
                                                                            if not self.checkdwlen(dw_len, input_dwsize) and ringcmd not in self.specialcmd:
                                                                                self.size_error.add(index)

                                                                current_group = dword_group
                                                        if unionorcmd.tag == 'otherCMD' and 'otherCMD' in unionorcmd.attrib:
                                                            if 'arraysize' in unionorcmd.attrib:
                                                                structcmd_group, dw_no = self.findcmd(structcmd_group, unionorcmd.attrib['otherCMD'], value_list, dw_no, content, unionorcmd.attrib['arraysize'])
                                                            else:
                                                                structcmd_group, dw_no = self.findcmd(structcmd_group, unionorcmd.attrib['otherCMD'], value_list, dw_no, content)

                                                        if unionorcmd.tag != 'otherCMD' and 'arraysize' in unionorcmd.attrib:
                                                            #filter the same layer containing 'arraysize' attrib with union or othercmd, not including those within union
                                                            asize = unionorcmd.attrib['arraysize']
                                                            if '_' in dw_no:
                                                                pre_dw = int(dw_no.split('_')[1].strip())
                                                            else:
                                                                pre_dw = int(dw_no)
                                                            #dtype: uint8_t, uint16_t, ...
                                                            if re.search('uint\d+_t', unionorcmd.tag):
                                                                uint = int(re.search('\d+', unionorcmd.tag)[0])
                                                            dw_end = pre_dw + int(int(asize)*uint/32)

                                                            for i in range(pre_dw+1, dw_end+1):
                                                                val_str = self.findval(value_list, str(i))['val_str']
                                                                dword_group = SubElement(structcmd_group, 'dword', {'NO' : str(i),
                                                                                                                    'value' : val_str,
                                                                                                                    'arrayname': unionorcmd.attrib['name'],
                                                                                                                    'dtype': unionorcmd.tag})
                                                            dw_no = str(dw_end)

                                                        #read defined dwsize if existed
                                                        if 'name' in unionorcmd.attrib and unionorcmd.attrib['name'] == 'dwSize':
                                                            defined_dwSize = unionorcmd.attrib['value']
                                                            structcmd_group.set('def_dwSize', defined_dwSize)
                                                            # check dwsize
                                                            diff = int(defined_dwSize) - input_dwsize

                                                            if not (ringcmd in self.specialcmd and (diff == 0 or diff == 1)):
                                                                if diff > 0:
                                                                    self.size_error.add(index)

                                                    #print(prettify(Result))
                                                    #break
                                        
                                            
                                                    structcmd_group = self.unmapdw( structcmd_group, dw_no, value_list)
                                                        #compare defined dwSize with real dwSize
                                                        #sub1 = abs(int(defined_dwSize) - dw_len)
                                                        #if sub1 != 1 and sub1 != 2:
                                                        #    structcmd_group.set('dwSizeEqual', 'False')

                                                    structcmd_group = self.checkdw(structcmd_group, value_list)


                                                    return node



        #cmd not found in local file
        ringcmd_group = SubElement(node, 'ringcmd', {'name' : ringcmd, 
                                                    'class' : 'not found',
                                                    'index' : str(index)})
        print(ringcmd + ' not found')
        self.notfoundset.add(ringcmd)
        return node

    def checkdw(self, node, value_list):
        #check if any dword loses or duplicates
        lost_list = []
        dupe_list = []
        current_list = []
        for dw_g in node.findall("dword"):
            no = dw_g.attrib['NO']
            if '_' in no:
                dw_l = int(no.split('_')[0])
                dw_h = int(no.split('_')[1])
                for i in range(dw_l, dw_h+1):
                    current_list.append(i)
            else:
                current_list.append(int(no))
        max_dw = max(current_list)
        seen = {}
        for x in current_list:
            if x not in seen:
                seen[x] = 1
            else:
                if seen[x] == 1:
                    dupe_list.append(str(x))
                seen[x] += 1
        for i in range(max_dw+1):
            if i not in current_list:
                lost_list.append(str(i))

        if lost_list:
            node.set('Lost_dw', ','.join(lost_list))
        if dupe_list:
            node.set('Dupe_dw', ','.join(dupe_list))
        return node

    def unmapdw(self, node, dw_no, value_list):
        #check if all the input dw has been mapped into dw
        dw_len = len(value_list)
        if '_' in dw_no:
            dw_end = int(dw_no.split('_')[-1])
        else:
            dw_end = int(dw_no)
        if dw_end < dw_len-1:
            for i in range(dw_end+1, dw_len):
                val_str = self.findval(value_list, str(i))['val_str']
                dword_group = SubElement(node, 'dword', {'NO' : str(i),
                                                         'unmappedstr' : val_str})
        return node

    def findcmdInContent(self, node, cmd, value_list, base_dw_no, content, arraysize):
        # find cmd according to name, append to node
        binv_list = [ bin(int(i, 16))[2:].zfill(32) for i in value_list ]   #each dword length = 32 bits(include leading 0)
        for Class in content.findall('./class'):
            for pattern in self.searchpattern:
                if 'name' in Class.attrib and re.search(pattern, Class.attrib['name'].lower()) and [i for i in self.filter if i not in cmd.lower() or i in cmd.lower() and i in Class.attrib['name'].lower()]:
                                    for structcmd in Class.iter('struct'):
                                        # search cmd in all the local files
                                        if 'name' in structcmd.attrib and structcmd.attrib['name'] == cmd:
                            
                                            dw_len = 0
                                            dw_no = base_dw_no
                                            #define iteration times according to cmd arraysize
                                            if not arraysize:
                                                times = 1
                                            else:
                                                times = int(arraysize)

                                            for i in range(times):
                                                for unionorcmd in structcmd.findall("./"):  #select all the direct children
                                        
                                                    if unionorcmd.tag == 'union' and 'name' in unionorcmd.attrib and 'DW' in unionorcmd.attrib['name']:
                                                        dword_group = SubElement(node, 'dword', {'otherCMD': cmd,
                                                                                                    'class' : Class.attrib['name']})
                                                        if arraysize:
                                                            dword_group.set('cmdarraysize', arraysize)
                                                            dword_group.set('arrayNO', str(i))
                                                        dw_no = unionorcmd.attrib['name'].strip('DW')
                                                        dic = self.findval(value_list, dw_no, base_dw_no)
                                                        dw_no = dic['dw_no_new']
                                                        dword_group.set('NO' , dw_no)
                                                        dword_group.set('value', dic['val_str'])
                                                        #dword_group = SubElement(structcmd_group, 'dword', {'NO' : dw_no,
                                                        #                                                    'value': val_str})
                                                        current_group = dword_group
                                                        for s in unionorcmd.findall('struct'):
                                                            # 1 dword has several objs
                                                            if 'name' in s.attrib:
                                                                obj_group = SubElement(current_group, s.attrib['name'], {'value': val_str})
                                                                current_group = obj_group
                                                            for elem in s.findall("./"):
                                                                if 'name' in elem.attrib:
                                                                    fieldname = elem.attrib['name']
                                                                    if 'bitfield' in elem.attrib :
                                                                        bit_item = elem.attrib['bitfield'].split(',')  #bitfield="0,  5"
                                                                    else:
                                                                        bit_item = []
                                                                    bit_value, bit_l, bit_h = self.findbitval(binv_list, bit_item, dw_no)

                                                                    current_group=self.setbitfield(current_group, structcmd.attrib['name'], fieldname, bit_value, bit_l, bit_h, dw_no)
                                                                    #if structcmd.attrib['name'] == 'MI_NOOP_CMD':
                                                                    #    current_group = self.setbitfield(current_group, fieldname, bit_value, bit_l, bit_h, dw_no, 'N')
                                                                    #else:
                                                                    #    current_group = self.setbitfield(current_group, fieldname, bit_value, bit_l, bit_h, dw_no)


                                                                    #complement undefined dword length, for unmapped buffer stream
                                                            current_group = dword_group
                                                    if unionorcmd.tag == 'otherCMD' and 'otherCMD' in unionorcmd.attrib:
                                                        node, dw_no = self.findcmd(node, unionorcmd.attrib['otherCMD'], value_list, dw_no, content)
                                                base_dw_no = dw_no
                                            return node, dw_no
        return None, None

    def findcmd(self, node, cmd, value_list, base_dw_no, contentNode, arraysize = ''):
        # find command in current file and include headers
        includes = [contentNode]
        while includes:
            content = includes[0]
            node, dw_no = self.findcmdInContent(node, cmd, value_list, base_dw_no, content, arraysize)
            if node != None:
                return node, dw_no
            with open(os.join.path(content.attrib['path'], content.attrib['file']),'r') as f:
                lines = f.readlines()
            for line in lines:
                if line.find('#include') >= 0:
                    if line.find('"') >= 0:
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if end < 0:
                            continue
                        #includes.append(line[start:end])
                        for content in self.Buf.findall('./Elem/content'):
                            if content.attrib['file'] == line[start:end]:
                                includes.append(content)
    
        # find command in whole file
        for source in self.source:
            elem = self.Buf.find("./Elem[@index='%s']" % str(self.source_dic.get(source)))
            for content in elem.findall('./content'):
                node, dw_no = self.findcmdInContent(node, cmd, value_list, base_dw_no, content, arraysize)
                if node != None:
                    return node, dw_no

        #cmd not found in local file
        dword_group = SubElement(node, 'dword', {'otherCMD': cmd,
                                                'class' : 'not found'})
        return node, base_dw_no

    def extractfull(self):
            # full_ringinfo : {'0':[{'MI_LOAD_REGISTER_IMM': ['1108101d', '00000244']},...]} , '0' is frame_no
            # extract full info from ringinfo text files
            for r,d,f in os.walk(self.ringpath):
                os.chdir(r)
                file_list = [file for file in f if re.search('VcsRingInfo_0_0.txt', file)]
                if len(file_list) > 1:
                    frame_no_list = [int(re.search('(\d)-VcsRingInfo_0_0.txt', file).group(1)) for file in file_list]
                elif len(file_list) == 1:
                    frame_no_list = [0]
                self.ringfilelist = file_list
                numset = set(frame_no_list)
                self.Frame_Num = len(numset)
                self.num_diff = min(numset)
                # if self.ringfilelist:
                #     idx = self.ringfilelist[0].find('-')
                #     if idx != -1:
                #         self.test_name = self.ringfilelist[0][:idx]


                for thing in self.ringfilelist:
                    if self.Frame_Num > 1:
                        frame_no = str(int(re.search('(\d)-VcsRingInfo_0_0.txt', thing).group(1)) - self.num_diff)
                    elif self.Frame_Num == 1:
                        frame_no = '0'
                    self.ringfilename = thing
                    self.txt2df()
                    self.extractdf(frame_no)
            

    def extractdf(self, frame_no, dfname = 'all'):
        #dfname options:
        #           'all': search in all the dfs
        #           'ContextRestore': search in ContextRestore portion
        #           'Workload': search in Workload portion
    
        #full_ringinfo : {'0':[{'MI_LOAD_REGISTER_IMM': ['1108101d', '00000244']},...]} , '0' is frame_no
        self.ringcmddic = {} #clear ringcmd count in dic
        df = self.df_dic[dfname]
        ringinfo = [] #stores single file ringinfo
        skip_next = False
        for i in df.index:
            #ringcmd = []

            if df.loc[i,"Description"] in self.specialcmd and i<len(df.index)-1 and df.loc[i+1,"Description"] == 'MI_NOOP':
                #skip 'mi_noop' after special cmd
                ringinfo.append({df.loc[i,"Description"]:[x for x in df.loc[i, "Header":].values.tolist() if str(x) != 'nan'] + 
                                                         [x for x in df.loc[i+1, "Header":].values.tolist() if str(x) != 'nan']})
                skip_next = True
            elif not skip_next:
                ringinfo.append({df.loc[i,"Description"]:[x for x in df.loc[i,"Header":].values.tolist() if str(x) != 'nan']})
            else:
                #skip 'mi_noop' after special cmd
                skip_next = False
                continue
            if df.loc[i,"Description"] in self.ringcmddic:
                self.ringcmddic[df.loc[i,"Description"]] += 1
            else:
                self.ringcmddic[df.loc[i,"Description"]] = 1
        self.ringcmdclass = dict.fromkeys(self.ringcmddic.keys(),'')
        self.full_ringinfo[frame_no] = ringinfo
            #ringcmd.append([x for x in df.loc[i,"Header":].values.tolist() if str(x) != 'nan'])
            #full_ringinfo.append(ringcmd)
        return self.full_ringinfo, self.ringcmddic

    def txt2df(self):
        #read ringcmdtringcmd text file into pd dataframe, which cmd stringcmd can be easily extracted
        ## only start after cmd "MI_BATCH_BUFFER_START"
        os.chdir(self.ringpath)
        comment_char = ['<', '-']
        # shutil.copy(self.ringfilename, self.output_path)
        with open(self.ringfilename, 'r') as f:
            df = pd.DataFrame()         #initialize
            start = 'MI_BATCH_BUFFER_START'

            start_fg = False

            for index, line in enumerate(f):

                # find header:
                if 'Count' in line:
                    columns = line.strip('-').split()  
                #elif '<ContextRestore' in line:
                #    c_start = in

                # skip the commented lines
                
                elif line[0] in comment_char:
                    continue

                elif start_fg: 
                    df = pd.concat( [df, pd.DataFrame([tuple(line.strip().split())])], ignore_index=True )

                elif not start_fg and start in line:
                    start_fg = True
                
        # 
        last_col = int(columns[-1]) #last dword num
        tar_last_col = len(df.columns) - len(columns) + last_col
        if tar_last_col > last_col:
            columns.extend( [str(i) for i in range(last_col+1,  tar_last_col+1)])
            df.columns = columns
        
        # df = df.iloc[0:0] #clear dataframe memory
        # df.loc[2] #select one column
        # df.loc[:,'Descriptiono'] #select one row

        #print(df)
        #df_dic = {'ContextRestore': df}
        self.df_dic = {'all':df}
        return self.df_dic

    def h2xml(self):
        #convert header to xml
        #use header_parser tool

        for source in self.source:
            index = self.source_dic.get(source)
            ##No need to reparse if this source converted before
            if index:
                continue
            else:
                # new source
                parser_list = []
                elem = Element('Elem')
                index = len(self.source_dic)+1
                self.source_dic[source] = index
                elem.set('index', str(index))

                for r,d,f in os.walk(source):
                    #modify target file
                    #if r'\ult\agnostic\test' not in r:
                    if r'\ult\agnostic\test' in r:
                        continue
                    for thing in f:
                        # filter all mhw cmd header file
                        #if thing.startswith('mhw_') and re.search('g\d', thing) and thing.endswith('.h'):
                        if self.gen != 'all':
                            if thing.startswith('mhw_') and re.search(f'g{self.gen}', thing) and thing.endswith('.h'):
                                parser_list.append(HeaderParser(thing, r))
                        else:
                            if thing.startswith('mhw_') and thing.endswith('.h'):
                                parser_list.append(HeaderParser(thing, r))

                for item in parser_list:
                    item.read_file()
                    #Do not create xml file for each h file, instead save in buf str
                    #item.write_xml()
                    root = ET.fromstring(item.parse_file_info())
                    elem.append(copy.deepcopy(root))
                self.Buf.append(elem)
        return self.Buf

    def findbitval(self, binv_list, bit_item, dw_no, base_dw_no = ''):
        # for otherCMD inside struct cmd, has base_dw_no
        if base_dw_no:
            if '_' in base_dw_no:
                bd = int(base_dw_no.split('_')[1].strip())+1
            else:
                bd = int(base_dw_no)+1
        else:
            bd = 0
        ##----------------------------------------
        if '_' in dw_no:
            dw_no_l = int(dw_no.split('_')[0].strip()) + bd 
            dw_no_h = int(dw_no.split('_')[1].strip()) + bd
        else:
            dw_no_l = int(dw_no) + bd
            dw_no_h = int(dw_no) + bd

        if bit_item:
            #find defalt hex value by field index
            bit_l = int(bit_item[0].strip())
            bit_h = int(bit_item[1].strip())
        else:
            #not have bit attrib
            bit_l = 0
            bit_h = (dw_no_h - dw_no_l + 1)*32 - 1

        if bit_l == 0:
            bit_value_raw =  ''.join(binv_list[dw_no_l: dw_no_h+1])[-bit_h-1 : ]
        else:
            bit_value_raw =  ''.join(binv_list[dw_no_l: dw_no_h+1])[-bit_h-1 : -bit_l]

        if bit_value_raw:
            bit_value = hex(int(bit_value_raw, 2))
        # nothing
        else:
            bit_value = ''

        return bit_value, str(bit_l), str(bit_h)

    def findval(self, value_list, dw_no, base_dw_no = ''):
        # for otherCMD inside struct cmd, has base_dw_no
        if base_dw_no:
            if '_' in base_dw_no:
                bd = int(base_dw_no.split('_')[1].strip()) + 1
            else:
                bd = int(base_dw_no) + 1
        else:
            bd = 0
        ##----------------------------------------
        if '_' in dw_no:
            dw_no_l = int(dw_no.split('_')[0].strip()) + bd
            dw_no_h = int(dw_no.split('_')[1].strip()) + bd
            dw_no_new = str(dw_no_l) + '_' + str(dw_no_h)
        else:
            dw_no_l = int(dw_no) + bd
            dw_no_h = int(dw_no) + bd
            dw_no_new = str(dw_no_h)
        val_str =  ''.join(value_list[dw_no_l: dw_no_h+1])
        if [i for i in val_str if i != '0']:
            val_str = '0x'+val_str
        # all '0'
        elif re.search('^0+$', val_str):
            val_str = '0x0'

        return dict(val_str = val_str, dw_no_new = dw_no_new)

    def searchkword(self, ringcmd, localcmd):
        #ringcmd: in ringcmdinfo "CMD_SFC_STATE_OBJECT"
        #local: in header file "SFC_STATE_CMD"
        #For match purpose
        if self.equal_list(ringcmd, localcmd):
            return True
        else:
            for l in self.same:
                for index, item in enumerate(l):
                    if item in ringcmd:
                        ringcmd_new = ringcmd.replace(item, l[len(l)-1-index])
                        return self.equal_list(ringcmd_new, localcmd)
            return False

    def equal_list(self, str1, str2):
        #split str with '_'
        #compare 2 lists after ignoringcmd some keywords
        l1 = str1.split('_')
        l2 = str2.split('_')
        ignored = set(self.ignored)
        for k1 in l1:
            if k1 not in ignored and k1 not in l2:
                return False
        for k2 in l2:
            if k2 not in ignored and k2 not in l1:
                return False
        return True


#----------------------------------------------------------------
#ringpath = r'C:\projects\github\AutoULTGen\Client\command_validator_app\vcstringinfo\HEVC-VDENC-Grits001-2125\VcsRingInfo'
#gen = 12
#source = [r'C:\Users\jiny\gfx\gfx-driver\Source\media\media_embargo\agnostic\gen12\hw', r'C:\Users\jiny\gfx\gfx-driver\Source\media\media_embargo\ult\agnostic\test\gen12_tglhp\hw']
#----------------------------------------------------------------

#----------------------------------------------------------------
## init
#start = time.clock()
#obj = CmdFinder(source, gen, ringpath)
#Buf = obj.h2xml()
#obj.extractfull()
#obj.updatexml()
#obj.writexml() #write to files
#elapsed = (time.clock() - start)
#print("Total Time used:",elapsed)   #25s 
###----------------------------------------------------------------


###----------------------------------------------------------------
## Update media path
#start = time.clock()
## manage source priority by list
#obj.source = [ r'C:\Users\jiny\gfx\gfx-driver\Source\media\media_embargo\ult\agnostic\test\gen12_tglhp\hw', r'C:\Users\jiny\gfx\gfx-driver\Source\media']
#Buf = obj.h2xml()
#obj.updatexml()
#obj.writexml() #write to files
#elapsed = (time.clock() - start)
#print("Total Time used:",elapsed)   #25s 
##----------------------------------------------------------------


##----------------------------------------------------------------
## show ringcmd if user want to update cmd
#print(obj.ringcmddic)  #show cmd list
#start = time.clock()
#obj.modifyringcmd('CMD_HCP_VP9_RDOQ_STATE', 'HEVC_VP9_RDOQ_STATE_CMD')
#print(obj.ringcmddic)  #show cmd list
#obj.undate_full_ringinfo()
#obj.updatexml()
#obj.writexml() #write to files
#elapsed = (time.clock() - start)
#print("Total Time used:",elapsed)   #13s 
##----------------------------------------------------------------

##----------------------------------------------------------------
##after running once
#start = time.clock()
#obj.ringpath = ...
#obj.extractfull()
#obj.updatexml()
#obj.writexml()
#elapsed = (time.clock() - start)
#print("Total Time used:", elapsed)   #18s 
#----------------------------------------------------------------