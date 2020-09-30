import subprocess
from xlrd import open_workbook
from xlutils.copy import copy
import os
from shutil import rmtree
import xmltodict

def get_links(file_name):
    dir_path = os.path.dirname(os.path.realpath(file_name))

    subprocess.call(["unzip",str(file_name+"x"),"-d","file_xml"], stdout=open(os.devnull, 'wb'))


    xml_sheet_names = dict()

    with open_workbook(file_name,formatting_info=True) as rb:
        copy(rb)
        workbook_names_list = rb.sheet_names()
        for i,name in enumerate(workbook_names_list):
            xml_sheet_names[name] = "sheet"+str(i+1)

    links = dict()
    for i, k in enumerate(workbook_names_list):
        xmlFile = os.path.join(dir_path,"file_xml/xl/worksheets/{}.xml".format(xml_sheet_names[k]))
        with open(xmlFile) as f:
            xml = f.read()
        #print(json.dumps(xmltodict.parse(xml)['worksheet']["sheetData"]["row"], indent=4))
        n = 0
        for row in xmltodict.parse(xml)['worksheet']["sheetData"]["row"]:
            n += 1
            if n == 1:
                continue
            try:
                links[n] = row["c"][-1]['f']['#text']
            except:
                continue
        rmtree("file_xml/")
        return links

get_links('table.xls')