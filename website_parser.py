#!/usr/bin/python3

from bs4 import BeautifulSoup
from requests import get
import re
from copy import deepcopy
import xlwt

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

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

def just_nums (s: str):
    res = str()
    for c in s:
        if (c.isnumeric()):
            res += c
    return res

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

    def dictify(self):
        d = dict()
        cols = ["Code", "Villa/Land", "Location type", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year"]
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

print("Reload the links database? (yes/no)")
if (input().strip() == 'yes'):
    print("Enter the quantity of pages on the website https://www.villabalisale.com/")
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
print()

with open("failed.txt", "w") as fw:
    fw.writelines(failed)

# Initialize a workbook
book = xlwt.Workbook()
# Add a sheet to the workbook
sheet1 = book.add_sheet("Sheet1")
# The data
cols = ["Code", "Villa/Land", "Location type", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year"]
# Loop over the rows and columns and fill in the values
row = sheet1.row(0)
for index, col in enumerate(cols):
    value = cols[index]
    row.write(index, value)
row.write(len(cols), 'Links')
print("Writing data to the XLS table:")
num = 1
printProgressBar(num, len(succeed), prefix = 'Progress:', suffix = 'Complete', length = 50)
for pr in succeed:
    row = sheet1.row(num)
    if pr and not pr.nil():
        d = pr.dictify()
        for index, col in enumerate(cols):
            value = d[cols[index]]
            row.write(index, value)
        row.write(len(cols), xlwt.Formula('HYPERLINK("%s";"Link")' % d['Link']))
        num += 1
        printProgressBar(num, len(succeed), prefix = 'Progress:', suffix = 'Complete', length = 50)
printProgressBar(len(succeed), len(succeed), prefix = 'Progress:', suffix = 'Complete', length = 50)
print()
# Save the result
book.save("table.xls")

print("Enter your email:")
receiver_address = input().strip()
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
mail_content = '''Hello,
This is a test mail.
In this mail we are sending some attachments.
The mail is sent using Python SMTP library.
Thank You
'''
#The mail addresses and password
sender_address = 'takerspam3@gmail.com'
sender_pass = 'sergiois123!'

#Setup the MIME
message = MIMEMultipart()
message['From'] = sender_address
message['To'] = receiver_address
message['Subject'] = 'A test mail sent by Python. It has an attachment.'
#The subject line
#The body and the attachments for the mail
message.attach(MIMEText(mail_content, 'plain'))
attach_file_name = 'table.xls'
attach_file = open(attach_file_name, 'rb')  # Open the file as binary mode
payload = MIMEBase('application', 'vnd.ms-excel')
payload.set_payload((attach_file).read())
encoders.encode_base64(payload)  #encode the attachment
#add payload header with filename
payload.add_header('Content-Disposition', 'attachment; filename="{}"'.format(attach_file_name))
message.attach(payload)
#Create SMTP session for sending the mail
session = smtplib.SMTP('smtp.gmail.com', 587)  #use gmail with port
session.starttls()  #enable security
session.login(sender_address, sender_pass)  #login with mail_id and password
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()
print('Mail Sent')
