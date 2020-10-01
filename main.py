import xlrd
from xlrd.sheet import ctype_text
import xlwt
from enum import Enum
#from termcolor import colored
from requests import get
from bs4 import BeautifulSoup

from copy import deepcopy
import re
import os

from link_worker import get_links # as long as xlwt/xlwr do not support hyperlinks, we have to get them 'manually' using xmldump

cols_name = ["Code", "Villa/Land", "Price change", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year", "Link"]

def just_nums (s: str):
    res = str()
    for c in s:
        if (c.isnumeric()):
            res += c
    return res

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

# Database dependent functions
def prepare_data(property_containers):
    cpy = ' '.join([x for x in str(property_containers[0]).split(' ') if x != ''])
    cpy = cpy.replace('<ul>','')
    cpy = cpy.replace('</ul>','')
    cpy = cpy.replace('<li>','')
    cpy = cpy.replace('</li>','')
    s = str()
    f = (cpy[0] == False)
    for c in cpy:
        if (c == '\n' and f or c != '\n'):
            s += c
        f = (c == '>')
    cpy = s[::-1]
    s = str()
    f = (cpy[0] == False)
    for c in cpy:
        if (c == '\n' and f or c != '\n'):
            s += c
        f = (c == '<')
    s = s[::-1]
    ls = s.splitlines()[1:-1]
    return ls

def get_box(property_containers: str):
    keys = ['code', 'location', 'land size', 'status', 'length_of_lease', 'year built', 'building size', 'price', 'beach', 'airport', 'market', 'hotel', 'shower', 'villa']
    d = dict()
    for key in keys:
        d[key] = None
    for ln in property_containers.splitlines():
        srt = ln.find('>') + 1
        fsh = ln.find('<', 1)
        key = ln[srt:(fsh - 2)].strip().lower()
        srt = ln.find('<strong>') + len('<strong>')
        fsh = ln.find('</strong>')
        value = ln[srt:fsh].strip()
        d[key] = value
    return d

def get_main_details(property_containers):
    ls = prepare_data(property_containers)
    keys = ['code', 'location', 'land size', 'status', 'length_of_lease', 'year built', 'building size', 'price', 'beach', 'airport', 'market', 'hotel', 'shower', 'villa']
    d = dict()
    for key in keys:
        d[key] = None
    for i in range(0, len(ls), 2):
        r = ls[i].rfind('<')
        l = ls[i].rfind('>', 0, -1)
        key = ls[i][l + 1:r].strip()
        value = str()
        if (key.lower() == 'status'):
            rv = ls[i + 1].rfind('<')
            lv = ls[i + 1].rfind('>', 0, -1)
            value = ls[i + 1][lv + 1:rv].strip()
            key = ' '.join(value.split()[0:2])
            if (key.lower() == 'free hold'):
                value = -1
            else:
                value = value.split()[-2]
            #print(value)
        elif (key.lower() == 'building size' or key.lower() == 'land size'):
            rv = ls[i + 1].find('<i>')
            lv = ls[i + 1].find('>')
            value = ls[i + 1][lv + 1:rv].strip()
            #print(value)
        else:
            rv = ls[i + 1].rfind('<')
            lv = ls[i + 1].rfind('>', 0, -1)
            value = ls[i + 1][lv + 1:rv].strip()
            #print(value)
        d[key.lower()] = value
    return d

class Color(Enum):
    RED = 10
    YELLOW = 13
    GREEN = 57
    WHITE = 9

class Property:
    def __init__(self):
        self.code = str()
        self.villa = str()
        self.loc_type = str()
        self.place = str()
        self.year = int()
        self.land_size = float()
        self.build_size = float()
        self.bedrooms = int()
        self.bathrooms = int()
        self.status = str()
        self.d_beach = int()
        self.d_airport = int()
        self.d_market = int()
        self.time = int()
        self.price = int()
        self.per_acre = int()
        self.per_unit = int()
        self.per_acre_a_year = str()
        self.per_unit_a_year = str()
        self.link = str()

    def update(self, d):
        if d['code']:
            self.code = d['code']
        if d['location']:
            self.place = d['location']
        if d['land size']:
            self.land_size = float(d['land size'])
        if d['status']:
            self.status = d['status']
            if self.status.lower() == 'lease hold':
                self.time = int(d['length_of_lease'])
                if self.time > 100:
                    self.time = None
        if d['year built']:
            try:
                self.year = int(d['year built'])
            except ValueError:
                lst = d['year built'].split()
                for val in reversed(lst):
                    try:
                        self.year = int(val)
                        break
                    except ValueError:
                        continue
                else:
                    self.year = None
        if d['building size']:
            self.build_size = float(d['building size'])
        if d['price'] and just_nums(d['price']):
            self.price = int(d['price'])
        if d['beach']:
            try:
                self.d_beach = int(just_nums(d['beach']))
            except ValueError:
                self.d_beach = None
        if d['airport']:
            try:
                self.d_airport = int(just_nums(d['airport']))
            except ValueError:
                self.d_airport = None
        if d['market']:
            try:
                self.d_market = int(just_nums(d['market']))
            except ValueError:
                self.d_market = None
        if d['Link']:
            self.link = d['Link']
        if d['hotel']:
            self.bedrooms = int(d['hotel'])
        if d['shower']:
            self.bathrooms = int(d['shower'])
        self.villa = d['villa']
        if self.land_size:
            self.per_acre = int(float(self.price) / self.land_size)
        if self.bedrooms:
            self.per_unit = int(float(self.price) / self.bedrooms)
        if self.time and self.per_acre:
            if self.time != 0:
                self.per_acre_a_year = "%.2f" % round(float(self.per_acre) / self.time, 2)
            else:
                self.per_acre_a_year = None
        if self.time and self.per_unit:
            if self.time != 0:
                self.per_unit_a_year = "%.2f" % round(float(self.per_unit) / self.time, 2)
            else:
                self.per_unit_a_year = None

    def update_from_table(self, d):
        cols = ["Code", "Villa/Land", "Price change", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year"]
        self.code = d[cols[0]]
        self.villa = (d[cols[1]] == 'Villa')
        self.loc_type = d[cols[2]]
        self.place = d[cols[3]]
        self.year = d[cols[4]]
        self.land_size = d[cols[5]]
        self.build_size = d[cols[6]]
        self.bedrooms = d[cols[7]]
        self.bathrooms = d[cols[8]]
        self.status = d[cols[9]]
        self.d_beach = d[cols[10]]
        self.d_airport = d[cols[11]]
        self.d_market = d[cols[12]]
        self.time = d[cols[13]]
        if d[cols[14]]:
            self.price = int(str(d[cols[14]])[:str(d[cols[14]]).find('USD')])
        self.link = d['Link']

    def dictify(self):
        d = dict()
        cols = ["Code", "Villa/Land", "Price change", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year", "Link"]
        d[cols[0]] = self.code
        d[cols[1]] = 'Villa' if self.villa else 'Land'
        d[cols[2]] = self.loc_type
        d[cols[3]] = self.place
        d[cols[4]] = self.year
        d[cols[5]] = self.land_size
        d[cols[6]] = self.build_size
        d[cols[7]] = self.bedrooms
        d[cols[8]] = self.bathrooms
        d[cols[9]] = self.status
        d[cols[10]] = self.d_beach
        d[cols[11]] = self.d_airport
        d[cols[12]] = self.d_market
        d[cols[13]] = self.time
        if self.price:
            d[cols[14]] = str(self.price) + " USD"
        else:
            d[cols[14]] = None
        if self.per_acre:
            d[cols[15]] = str(self.per_acre) + " USD"
        else:
            d[cols[15]] = None
        if self.per_unit:
            d[cols[16]] = str(self.per_unit) + " USD"
        else:
            d[cols[16]] = None
        if self.per_acre_a_year:
            d[cols[17]] = str(self.per_acre_a_year) + " USD"
        else:
            d[cols[17]] = None
        if self.per_unit_a_year:
            d[cols[18]] = str(self.per_unit_a_year) + " USD"
        else:
            d[cols[18]] = None
        d['Link'] = self.link
        return d
    
    def nil (self):
        return (self.price == self.year == 0 and self.land_size == self.build_size == 0.0)

class ColoredProperty:
    def __init__(self, color, prop: Property, changes: list):
        self.color = color
        self.property = deepcopy(prop)
        if changes:
            self.changes = deepcopy(changes)
        else:
            self.changes = None

class Cell:
    def __init__(self, data, color):
        self.data = data
        self.color = color

    def __repr__(self):
        if not self.data:
            self.data = str()
        else:
            self.data = str(self.data)
        return self.data
    
class Row:
    def __init__(self, row_num):
        self.data = [Cell(None, Color.WHITE)]*len(cols_name)
        self.row_num = row_num

    def update_cell(self, idx, data, color):
        self.data[idx] = Cell(data, color)

    def red(self):
        color = Color.WHITE
        for cell in self.data:
            if cell and cell.color != Color.WHITE:
                color = cell.color
        return color == Color.RED

    def from_prop(self, prop: Property, color):
        d = prop.dictify()
        for num in range(len(self.data)):
            if d[cols_name[num]]:
                self.data[num] = Cell(d[cols_name[num]], color)
            else:
                self.data[num] = Cell(None, color)
    
    def equal(self, rw):
        for num in range(len(self.data)):
            if rw.data[num].data != self.data[num].data:
                return False
        return True

    def redraw(self, color):
        for cell in self.data:
            if cell:
                cell.color = color

    def coloredProperty(self):
        d = dict()
        color = Color.WHITE
        changes = None
        for num, cell in enumerate(self.data):
            d[cols_name[num]] = cell.data
            if cell.color == Color.YELLOW:
                if not changes:
                    changes = list()
                changes.append(num)
            if cell.color != Color.WHITE:
                color = cell.color
        pr = Property()
        #print(d)
        pr.update_from_table(d)
        cp = ColoredProperty(color, pr, changes)
        return cp

    def __repr__(self):
        s = str()
        for cell in self.data:
            s += str(cell) + '\t'
        return s

class Table:
    def __init__(self):
        self.list = list()

    def append(self, row: Row):
        self.list.append(row)

    def __repr__(self):
        s = str()
        for row in self.list:
            s += str(row) + '\n'
        return s

    def row_by_code(self, code):
        for row in self.list:
            if row.data[0].data == code:
                return deepcopy(row)

    def update(self, upd: list):
        table_from_upd = Table()
        i = 0
        for u_property in upd:
            row = Row(i)
            row.from_prop(u_property, Color.WHITE)
            table_from_upd.append(row)

        old_codes = set()
        for row in self.list:
            if row.data[0].color != Color.RED:
                old_codes.add(row.data[0].data)

        new_codes = set()
        for row in table_from_upd.list:
            new_codes.add(row.data[0].data)

        changed_or_not_changed = old_codes.intersection(new_codes)
        deleted = old_codes.difference(changed_or_not_changed)
        new = new_codes.difference(changed_or_not_changed)

        table_to_return = Table()
        row_num = 0
        for code in changed_or_not_changed:
            old_row = self.row_by_code(code)
            new_row = table_from_upd.row_by_code(code)
            row_for_return_table = Row(row_num)
            cell_num = 0
            for new_cell, old_cell in zip(new_row.data, old_row.data):
                cl = deepcopy(new_cell)
                if new_cell != old_cell:
                    if cell_num == 14:
                        cl.color = Color.YELLOW
                        if old_cell.data:
                            old_pr = int(old_cell.data[0:int(old_cell.data.find('USD') - 1)])
                            new_pr = int(new_cell.data[0:int(new_cell.data.find('USD') - 1)])
                            pr_cd = deepcopy(cl)
                            if old_pr < new_pr:
                                pr_cd.data = '▲' + str(new_pr - old_pr) + ' USD'
                                row_for_return_table.update_cell(2, pr_cd.data, pr_cd.color)
                            elif old_pr == new_pr:
                                row_for_return_table.update_cell(2, None, Color.WHITE)
                            else:
                                pr_cd.data = '▼' + str(old_pr - new_pr) + ' USD'
                                row_for_return_table.update_cell(2, pr_cd.data, pr_cd.color)
                    else:
                        cl.color = Color.WHITE
                else:
                    row_for_return_table.update_cell(2, None, Color.WHITE)
                    cl.color = Color.WHITE
                row_for_return_table.update_cell(cell_num, cl.data, cl.color)
                cell_num += 1
            table_to_return.append(row_for_return_table)
            row_num += 1

        for code in deleted:
            old_row = self.row_by_code(code)
            row_for_return_table = Row(row_num)
            cell_num = 0
            for cell in old_row.data:
                row_for_return_table.update_cell(cell_num, cell.data, Color.RED)
                cell_num += 1
            table_to_return.append(row_for_return_table)
            row_num += 1

        for code in new:
            new_row = table_from_upd.row_by_code(code)
            row_for_return_table = Row(row_num)
            cell_num = 0
            for cell in new_row.data:
                row_for_return_table.update_cell(cell_num, cell.data, Color.GREEN)
                cell_num += 1
            table_to_return.append(row_for_return_table)
            row_num += 1
        return table_to_return
                
        

    def write_out(self, filename):
        # Initialize a workbook
        book = xlwt.Workbook(style_compression=2)
        # Add a sheet to the workbook
        sheet1 = book.add_sheet("Sheet1")
        # The data
        cols = ["Code", "Villa/Land", "Price change", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year", "Link"]
        # Loop over the rows and columns and fill in the values
        row = sheet1.row(0)
        for index, col in enumerate(cols):
            row.write(index, col)
        print("Writing data to the XLS table:")
        num = 1
        printProgressBar(num, len(self.list), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for tbl_row in self.list:
            row = sheet1.row(num)
            #print(tbl_row)
            if tbl_row:
                try:
                    d = tbl_row.coloredProperty().property.dictify()
                except AttributeError:
                    continue
                for index, cell in enumerate(tbl_row.data):
                    if index != len(tbl_row.data) - 1:
                        value = cell.data
                        style = xlwt.XFStyle()
                        pattern = xlwt.Pattern()
                        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
                        if cell.color == Color.WHITE:
                            pattern.pattern_fore_colour = 9
                        elif cell.color == Color.YELLOW:
                            pattern.pattern_fore_colour = 13
                        elif cell.color == Color.GREEN:
                            pattern.pattern_fore_colour = 57
                        else:
                            pattern.pattern_fore_colour = 10
                        style.pattern = pattern
                        row.write(index, value, style)
                row.write(len(cols) - 1, xlwt.Formula('HYPERLINK("%s";"Link")' % d['Link']))
                num += 1
                printProgressBar(num, len(self.list), prefix = 'Progress:', suffix = 'Complete', length = 50)
        printProgressBar(len(self.list), len(self.list), prefix = 'Progress:', suffix = 'Complete', length = 50)
        print()
        # Save the result
        book.save(filename)
    
def load_file(file_name):
    book = xlrd.open_workbook(file_name, formatting_info=True)
    sheets = book.sheet_names()
    #print ("sheets are:", sheets)
    links = get_links(file_name)
    for index, sh in enumerate(sheets):
        sheet = book.sheet_by_index(index)
        #print ("Sheet:", sheet.name)
        rows, cols = sheet.nrows, sheet.ncols
        #print ("Number of rows: %s   Number of cols: %s" % (rows, cols))

        # Iterate through rows, and print out the column values
        tbl = Table()
        #print(sheet.nrows)
        for row_idx in range(1, sheet.nrows):
            #print('Row ', row_idx)
            row = Row(row_idx)
            for col_idx in range(len(cols_name)):
                cell_obj = sheet.cell(row_idx, col_idx)
                cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
                #print("\t(%s): %s" % (cols_name[col_idx], cell_obj.value))
                if col_idx == len(cols_name) - 1:
                    try:
                        value = links[row_idx + 1][11:-9]
                    except KeyError:
                        value = None
                        continue
                else:
                    value = str(cell_obj.value)
                xfx = sheet.cell_xf_index(row_idx, col_idx)
                xf = book.xf_list[xfx]
                bgx = xf.background.pattern_colour_index
                #print ("\t\tColor %d" % bgx)
                
                color = None
                if bgx == 10:
                    color = Color.RED
                elif bgx == 13:
                    color = Color.YELLOW
                elif bgx == 57:
                    color = Color.GREEN
                else:
                    color = Color.WHITE

                row.update_cell(col_idx, value, color)
            tbl.append(row)
    return tbl

def get_update():
    print("Enter the quantity of pages on the website https://www.villabalisale.com/search/villas-for-sale")
    quantity = int(input())
    properties = set()
    print("Getting the links to the properties:")
    printProgressBar(0, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
    with open("property_url.txt", "w") as f:
        for i in range(quantity):
            url = 'https://www.villabalisale.com/search/villas-for-sale?page={}'.format(i) # going through pages.
            response = get(url)
            html_soup = BeautifulSoup(response.text, 'html.parser')
            property_containers = html_soup.find_all('a', href=True)
            for pr in property_containers:
                s = str(pr['href']).strip()
                if (s.find("https://www.villabalisale.com/property/") == 0):
                    if s not in properties:
                        f.write(s + "\n")
                        properties.add(s)
            printProgressBar(i, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
    printProgressBar(quantity, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
    print()

    print("Collecting data from the properties' websites.")

    i = 0
    first = 0
    second = 0
    third = 0
    failed = list()
    succeed = list()
    quantity = file_len("property_url.txt")
    printProgressBar(0, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
    with open("property_url.txt", "r") as f:
        for url in f.readlines():
            #print(url.strip())
            response = get(url.strip())
            srt = response.text.find('<div class="main-detail">')
            fsh = response.text.find('<div class="box-links-detail">')
            if not(srt != -1 and fsh != -1):
                ind = response.text.find('<p>Land Size: <strong>')
            else:
                cpy = prepare_data(response.text[srt:fsh])
            if (srt != -1 and fsh != -1):
                first += 1
                d = get_main_details (str(cpy))
                #print(cpy)
            elif (ind != -1):
                second += 1
                #ind = response.text.find('<p>Land Size: <strong>')
                #print(ind)
                cpy = response.text[:ind] + response.text[ind:].replace('\n', '', 1)
                srt = cpy.find('<p>Code: <strong>')
                fsh = cpy.find("<p>Building Size: ")
                fsh = cpy.find('\n', fsh)
                '''
                with open("prop"+str(i)+"v.txt", "w") as fw:
                    fw.write(cpy)
                '''
                property_containers = '\n'.join([x.strip() for x in cpy[srt:fsh].splitlines()])
                d = get_box(property_containers)
                srt = cpy.find('<input type="hidden" name="price" value="') + len('<input type="hidden" name="price" value="')
                fsh = cpy.find('"', srt)
                d['price'] = cpy[srt:fsh]
                srt = cpy.find('<div class="property-description-column flexbox flexbox-wrap double">') + len(('<div class="property-description-column flexbox flexbox-wrap double">'))
                srt = cpy.find('<div class="property-description-column flexbox flexbox-wrap double">', srt) + len(('<div class="property-description-column flexbox flexbox-wrap double">'))
                srt = cpy.find('<div class="property-description-column flexbox flexbox-wrap double">', srt) + len(('<div class="property-description-column flexbox flexbox-wrap double">'))
                fsh = cpy.find('</div>', srt)
                for x in cpy[srt:fsh].splitlines():
                    ln = x.strip()
                    if ln:
                        l = ln.find('>') + 1
                        r = ln.find('<', 1)
                        l_ = ln.find('<strong>') + len('<strong>')
                        r_ = ln.find('</strong>')
                        #print(ln, l,r,l_,r_)
                        try:
                            d[ln[l:r].strip()[:-1]] = ln[l_:r_].split()[0]
                        except IndexError:
                            d[ln[l:r].strip()[:-1]] = None
                srt = cpy.find('<div class="available ">')
                srt = cpy.find('<i class="material-icons icon">hotel</i>', srt) + len('<i class="material-icons icon">hotel</i>')
                srt_ = cpy.find('<p>', srt)
                fsh_ = cpy.find('</p>', srt_)
                d['hotel'] = re.sub("[^0-9]", "", str(cpy[srt_:fsh_]))
                srt = cpy.find('<div class="available ">')
                srt = cpy.find('<i class="shower"></i>', srt) + len('<i class="shower"></i>')
                srt_ = cpy.find('<p>', srt)
                fsh_ = cpy.find('</p>', srt_)
                d['shower'] = re.sub("[^0-9]", "", str(cpy[srt_:fsh_]))
                if not d['location']:
                    srt = cpy.find('<input type="hidden" name="data-area" value="') + len('<input type="hidden" name="data-area" value="')
                    fsh = cpy.find('"', srt)
                    d['location'] = cpy[srt:fsh].capitalize()
                if (d['status'] == 'lease hold'):
                    srt = cpy.find('<p style="text-transform: capitalize;">lease hold</p>') + len('<p style="text-transform: capitalize;">lease hold</p>')
                    srt = cpy.find('<p>/', srt) + len('<p>/')
                    fsh = cpy.find('</p>', srt)
                    d['length_of_lease'] = re.sub("[^0-9]", "", cpy[srt:fsh])
                srt = cpy.find('<title>') + len('<title>')
                fsh = cpy.find('</title>')
                if cpy.lower().find('villa'):
                    d['villa'] = True
                else:
                    d['villa'] = False
                    
            else:
                third += 1
            if not d:
                failed.append(url)
            #print(d)
            i += 1
            current_property = Property()
            if d:
                d['Link'] = url.strip()
                current_property.update(d)
                succeed.append(deepcopy(current_property))
            printProgressBar(i + 1, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
            html_soup = None
            response = None
            property_containers = None
            d = None
    printProgressBar(quantity, quantity, prefix = 'Progress:', suffix = 'Complete', length = 50)
    print()

    with open("failed.txt", "w") as fw:
        fw.writelines(failed)

    return deepcopy(succeed)

FILENAME_IN = "table.xls"
FILENAME_OUT = 'table_out.xls'
tbl = load_file(FILENAME_IN)
#tbl = Table()
#print(tbl)
succeed = get_update()
ret_t = tbl.update(succeed)
ret_t.write_out(FILENAME_OUT)
os.remove(FILENAME_IN + 'x')
os.remove(FILENAME_IN)
#os.rename(FILENAME_OUT, FILENAME_IN)

#for pr in succeed:
    #print(pr.dictify())

#new_tlb = tbl.update(succeed)
#new_tlb.write_out('table_new.xls')