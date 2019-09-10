from xml.etree.ElementTree import (
    Element, SubElement, tostring, XML,
)
import xml.etree.ElementTree as ET
from ElementTree_pretty import prettify
import os
import re

class HeaderParser(object):
    """

    """

    def __init__(self, name, path):
        """

        :param name:
        :param path:
        """
        self.name = name
        self.path = path
        self.lines = []
        self.methods = []
        self.methods_info = []
        self.constructor = []
        self.destructor = []
        self.includes = set()
        self.elpredef = set()       
        self.basic_type = {'int', 'bool', 'double', 'float', 'dword', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t', 'size_t','char'}
        self.datastructure = {'class', 'struct', 'union', 'enum' , 'namespace' }
        self.prefixset = {'static', 'constexpr', 'const', 'unsigned', '*', '&'}
        self.member_accessors = {'public:', 'protected:', 'private:' }
        self.vars = []

    
    def read_file(self, name=None, path=None):
        """
        read file from given name and path
        """
        if name:
            self.name = name
        if path:
            self.path = path
        with open(os.path.join(self.path, self.name), 'r',  encoding="ISO-8859-1") as fin:
            self.lines = fin.readlines()

    def write_xml(self, name=None, path=None ):
        #write xml for given header file
        #final step of the usage
        #This function could also be used if you would like to see clearly whether the final output xml string is as expected 
        if name:
            self.name = name
        if path:
            self.path = path
        with open(os.path.join(self.path, self.name) + '.xml', 'w') as fout:
            fout.write(self.parse_file_info())

    def get_datastructure(self, line):
        #datastructure = {'class', 'struct', 'union', 'enum' }
        #parse 3 conditions:
        #1: 'struct xxx'
        #2: 'struct'
        #3: 'stuct xxx : public xxx'

        #init
        structure_type = ''
        structure_name = ''
        super_structure_type = ''
        super_structure_name = ''

        line_clr=line.strip()
        item_list=line_clr.split(' ')

        #1: 'struct xxx'
        if len(item_list) == 2:
            structure_type = item_list[0]
            structure_name = item_list[1]

        #2: 'struct'
        elif len(item_list) == 1:
            structure_type = item_list[0]
    
        #3: 'stuct xxx : public xxx'
        elif line.find(':') != -1:
            structure_type = item_list[0]   
            structure_name = item_list[1]
            methods = {'public', 'protected', 'private'}
            for i in methods:
                if i in line:
                    super_structure_type = i
                    super_struc_index = item_list.index(i)
                    super_structure_name = ''.join(item_list[super_struc_index+1: ])   # multiple super structure name not considered yet

        return structure_type , structure_name , super_structure_type , super_structure_name

    def parse_basictype(self, line):
        #parse basic type, maybe with prefix
        #prefix = {'static', 'constexpr', 'const', 'unsigned', '*', '&'}
        #basic_type = {'int', 'bool', 'dword', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t', 'size_t', 'char'}
        #parse 6 conditions
        #1: 'uint32_t                     Value;' or 'uint32_t                 SumSadHaarForBestMbChoice                                                        ;'
        #2: 'uint32_t                 AddressUpperDword                                : __CODEGEN_BITFIELD( 0, 15)    ; ' 
        #3: 'static const size_t dwSize = 1;'
        #4: 'uint8_t*            lockAddress,'
        #5: 'uint8_t HevcGetU62ModeCost ( double mcost ) '  part of a function
        #6: 'uint32_t                                 Quantizermatrix[32];'
        #init
        prefix = ''
        type = ''
        name = ''
        arraysize = ''
        address = ''  #save as '0, 15' for '__CODEGEN_BITFIELD( 0, 15)'
        value = ''
        para_name = []
        para_type = []

        line_clr=line.strip().strip(';').strip()
        line_clr=line_clr.strip().strip(',').strip()
        if '*' in line_clr:
            prefix = 'pointer'
            line_clr = line_clr.replace('*', '')
        if '&' in line_clr:
            prefix = 'addr'
            line_clr = line_clr.replace('&', '')
            
        item_list=line_clr.split()

        #1: 'uint32_t                     Value;'
        #4: 'uint8_t*            lockAddress,'
        #6: 'uint32_t                                 Quantizermatrix[32];'
        if len(item_list) == 2:
            type = item_list[0]
            name = item_list[1]
            if re.search('\[\d+\]',name):
                arraysize = re.search('\[\d+\]', name)[0].strip('[').strip(']')
            
        elif len(item_list) > 2:
            #2.1: 'uint32_t                 AddressUpperDword                                : __CODEGEN_BITFIELD( 0, 15)    ; ' 
            #2.2: 'uint32_t                 AddressUpperDword:                                 __CODEGEN_BITFIELD( 0, 15)    ; '
            if line.find('CODEGEN_BITFIELD') != -1 :
                type = item_list[0]
                name = item_list[1].strip(':').strip()
                address = line_clr[line_clr.find('(')+1 : line_clr.find(')') ].strip()
                

            #3: 'static const size_t dwSize = 1;'
            elif line.find('=') != -1:
                idx = line_clr.find('=')
                if '=' in item_list:
                    list_idx = item_list.index('=')
                    value = line_clr[ idx+1 : ].strip()

                else:
                    equal_type = [i for i in item_list if '=' in i][0]
                    list_idx = item_list.index(equal_type)
                    value = equal_type + line_clr[ idx+1 : ].strip()

                name = item_list[list_idx - 1]  #right before '='
                type = item_list[list_idx - 2]  #right before name
                if list_idx > 3:    #prefix exists
                    prefix = line_clr[ : line_clr.find(type)].strip()

            #5: 'uint8_t HevcGetU62ModeCost ( double mcost ) '  part of a function
            elif line.find('(') !=-1:
                idx = line_clr.find('(')
                list_idx = item_list.index('(')
                name = item_list[list_idx - 1]  #right before '('
                type = item_list[0]  
                if line.find(')') !=-1:
                    list_idx2 = item_list.index(')')
                    if list_idx2- list_idx == 3:
                        para_type.append(item_list[list_idx + 1])
                        para_name.append(item_list[list_idx2 - 1])
                    elif list_idx2- list_idx > 3:
                        # para more than 1
                        indices = [i for i, x in enumerate(item_list) if x==',']
                        for i in indices:
                            para_type.append(item_list[i - 2])
                            para_type.append(item_list[i - 1])

        return type, name, arraysize, address, prefix, value, para_name, para_type
    
    def parse_file_info(self):
        # parse mhw header file to xml, ignore comment, predefined part...
        # need to modified if mhw header file code structure changes
        if not self.lines:
            print('Please read file first\n')
            return

        f_ignore = False
        method_type = 'private'
        f_method = False
        f_struct = False

        #
        content = Element('content')
        content.set('file', self.name)
        current_group = content

        #init
        unparsed_index = 0
        unparsed_text_id = 0 
        nest_layer=[]    # save current layer
        nest_layer_num = 0  # count nest layer num
        saved_enum_name = ''

        #pretreat texts
        new_lines=[]
        for index, line in enumerate(self.lines):
            line = line.replace('{','\n{\n')    #make sure '{' and '}' be splited
            line = line.replace('(',' ( ')
            line = line.replace(')',' ) ')

            # line = line.replace('}','\n}\n')
            line = line.lstrip()    #delete former blank
            
            if line.startswith('__CODEGEN_BITFIELD'):   #in case unfinished definition
                new_lines[-1] = new_lines[-1].strip('\n') +'  ' +line
            else:
                line = line.split('\n')
                new_lines.extend ( [x.strip() for x in line if x] )   #filter blank in the list
        
        # print(new_lines[373])
        for index, line_clr in enumerate(new_lines):

            # debug part
            #print(index)
            #print('----------------------------------\n')
            #print(prettify(content))   

            #-------------------------------------------------------
            #parse comment part, which can be ignored(cleared)
            if f_ignore:
                idx = line_clr.find('*/')
                if idx == -1:
                    continue
                else:
                    #comment end
                    f_ignore = False
                    line_clr = line_clr[idx+2:]
            if line_clr.startswith('/*'):
                #comment start
                f_ignore = True
                continue                   # continue may ignore the content and cause some problem
            if line_clr.find('//') != -1:
                idx = line_clr.find('//')
                line_clr = line_clr[:idx]
            if not line_clr:
                continue
            #clear comment part, ignore blank line
            #--------------------------------------------------------

            #------------------------------------------------------
            #parse pre-defined parts
            if line_clr.startswith('#include'):
                self.includes.add(line_clr[10:-1])
                continue

            elif line_clr.startswith('#'): 
                self.elpredef.add(line_clr[1:])
                continue
            #-----------------------------------------------------
            
            #--------------------------------------------
            # manage nest layer
            if line_clr.find('{') != -1:
                nest_layer.append(current_group)    #enter child layer， problem occurs when unparse function
                nest_layer_num += 1
                if index - unparsed_index == 2:
                    # parse {} in one line but {} are splited before
                    unparsed_index += 1
                #idx = line_clr.find('{')
                #if line_clr[idx+1]:
                #    line_clr = line_clr[idx+1:]
                #else:
                continue

            #--------------------------------------------------------
                
            #--------------------------------------------
            #parse datastructure = {'class', 'struct', 'union', 'enum' , 'namespace' }
            if any([line_clr.startswith(item) for item in self.datastructure]):
                self.structure_type , self.structure_name , self.super_structure_type , self.super_structure_name = self.get_datastructure(line_clr)
                new_datastruct_group = SubElement(current_group, self.structure_type)
                current_group = new_datastruct_group
                if self.structure_name:
                    current_group.set('name', self.structure_name)
                if self.super_structure_type:
                    current_group.set('super_structure_type', self.super_structure_type)
                    current_group.set('super_structure_name', self.super_structure_name)
                continue   
            #-------------------------------------------------------------

            #-------------------------------------------------------------
            #parse member_accessors = {'public:', 'protected:', 'private:' }
            if line_clr in self.member_accessors :
                member_accessor = line_clr.strip(':')
                new_group = SubElement(current_group,member_accessor )
                current_group = new_group
                nest_layer.append(current_group)
                nest_layer_num += 1
                continue 
            #----------------------------------------------------

            #--------------------------------------------
            #parse basic_type = {'int', 'bool', 'dword', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t', 'char'}
            if any([line_clr.startswith(item)  for item in self.basic_type]):
                self.type , self.basic_name , self.arraysize, self.address , self.prefix, self.value, self.para_name, self.para_type = self.parse_basictype(line_clr)
                if self.basic_name:
                    new_basic_group = SubElement(current_group, self.type, name=self.basic_name)
                    if self.address:
                        new_basic_group.set('bitfield', self.address)
                    if self.arraysize:
                        new_basic_group.set('arraysize', self.arraysize)
                    if self.para_name:

                        ### Problems!!!!
                        # function definition is not related to current command validator requirement, so this part is unfinished
                        for i, para_name in enumerate(self.para_name):
                            new_func_group = SubElement(current_group, 'FUNCTION', {'para_name': para_name,
                                                                                    'para_type': self.para_type[i]})
                        current_group = new_func_group
                continue   

            #parse datatype above, but with prefix
            #e.g.: 'static const size_t dwSize = 1;'
            if any([line_clr.startswith(item) for item in self.prefixset]) and line_clr.find('=') != -1:
                self.type , self.basic_name , self.arraysize, self.address , self.prefix, self.value, self.para_name, self.para_type = self.parse_basictype(line_clr)
                #exclude exceptions 
                if self.type not in self.basic_type:
                    break
                new_basic_group = SubElement(current_group, self.type, name=self.basic_name)
                if self.address:
                    new_basic_group.set('address', self.address)
                if self.prefix:
                    new_basic_group.set('prefix', self.prefix)
                if self.value:
                    new_basic_group.set('value', self.value)
                continue  
            #-------------------------------------------------------------


            #------------------------------------------------------------
            #pase member inside enum{}, always set value?
            #suppose set value
            #e.g. 'FORCEINTRA_ENABLE                                                = 1,'
            if current_group.tag == 'enum':
                if line_clr.find('=') != -1:
                    idx = line_clr.find('=')
                    name = line_clr[  : idx].strip()
                    value = line_clr[ idx+1 : line_clr.find(',')].strip()
                    if current_group.attrib['name'] == saved_enum_name:
                        text_id += 1
                    else:
                        text_id = 0
                    enum_member_group = SubElement(current_group, 'text', id=str(text_id))
                    enum_member_group.set('name', name)
                    enum_member_group.set('value', value)
                    saved_enum_name = current_group.attrib['name']
                    continue
            #------------------------------------------------------------



            #------------------------------------------------------------
            #pase reference member inside struct xxx_CMD{yyy_CMD zzz;}
            #and constructor xxx_CMD{xxx_CMD();}
            #only those endwith '_CMD' 
            #e.g. 'VDENC_64B_Aligned_Lower_Address_CMD LowerAddress
            #      'HUC_VIRTUAL_ADDR_REGION_CMD              HucVirtualAddressRegion[16];  '        
            if line_clr.find('_CMD') != -1:
                if (current_group.tag == 'struct' and 'name' in current_group.attrib and current_group.attrib['name'].endswith('_CMD')) or current_group.tag == 'union': 
                    if 'name' in current_group.attrib :
                        #1: constructor xxx_CMD{xxx_CMD();}
                        constructor = current_group.attrib['name']
                        if line_clr.startswith(constructor) and '(' in line_clr and ')' in line_clr:
                            constructor_group = SubElement(current_group, 'constructor',{'name': constructor})
                            idx1 ='('
                            idx2 =')'
                            line_clr1 = line_clr[line_clr.find(idx1)+1 : line_clr.find(idx2)].strip()
                            if line_clr1:
                                constructor_group.set('text', line_clr1)
                            continue
                    #2: otherstruct yyy_CMD zzz;
                    #3: inside union yyy_CMD zzz;
                    # may have exceptions
                        
                    line_clr1 = line_clr.strip().strip(';').strip()
                    item_list = line_clr1.split()
                    otherCMD = item_list[0]
                    if otherCMD.endswith('_CMD'):
                        name = item_list[1]
                        otherCMD_group = SubElement(current_group, 'otherCMD')

                        if re.search('\[\d+\]',name):
                            arraysize = re.search('\[\d+\]', name)[0].strip('[').strip(']')
                            otherCMD_group.set('arraysize', arraysize)
                        otherCMD_group.set('otherCMD', otherCMD)
                        otherCMD_group.set('name', name)
                        continue
            #------------------------------------------------------------
            
            #------------------------------------------------------------
            # parse 'return xxx;}' and 'return xxx;'
            # error when former function unparsed
            if line_clr.startswith('return'):
                return_value = line_clr.strip('return').strip().strip(';').strip()
                return_group = SubElement(current_group, 'return')
                return_group.set('value', return_value)
            #------------------------------------------------------------

            
            #------------------------------------------------------------
            # manage nest layer, position fixed in the end part
            if line_clr.find('}') != -1:
                nest_layer.pop()    #exit current layer, return to parent
                nest_layer_num -= 1
                if line_clr.find(';') != -1:
                    #current_group = nest_layer[-1]
                    idx1 ='}'
                    idx2 =';'
                    line_clr1 = line_clr[line_clr.find(idx1)+1 : line_clr.find(idx2)].strip()
                    # if'};' simply exit current layer, look like struct definition finished
                    if line_clr1:   # parse '} DW0;', post-positioned name
                        text=line_clr1
                        current_group.set('name', text)

                    # if'xxx;}' xxx maybe parsed above, maybe 'return __CODEGEN_OP_LENGTH(uiLength); }'
                    # if unparsed, will lose xxx; 
                    line_clr2 = line_clr[ : line_clr.find(idx2)].strip()

                    if nest_layer:
                        current_group = nest_layer[-1]
       
                continue
            #------------------------------------------------------------- 
                  
            #-------------------------------------------------------------       
            #consecutive unparsed part save as text
            #if index-unparsed_index != 1 :
            #    unparsed_text = ''
            #print(line_clr)
            #leave function(xx){return xx ;} unparsed
            unparsed_text = line_clr
            unparsed_text_id += 1
            unparsed_text_group = SubElement(current_group, 'unparsedtext', id=str(unparsed_text_id))
            unparsed_text_group.text = unparsed_text

            #test, see each update xml
            #print(prettify(content))
            #-------------------------------------------   

        #print(prettify(content))
        
        return prettify(content)



#test
#filename = 'mhw_vdbox_vdenc_hwcmd_g12_X.h'
#path = r'C:\Users\jiny\gfx\gfx-driver\Source\media\media_embargo\ult\agnostic\test\gen12\hw\vdbox'
#obj = HeaderParser(filename, path)
#obj.read_file()
#obj.write_xml()