import xlrd
from xlrd.sheet import ctype_text

cols_name = ["Code", "Villa/Land", "Location type", "Location", "Year built", "Land size, are", "Building Size, sqm", "Bedrooms", "Bathrooms", "Status", "Distance to beach", "Distance to airport", "Distance to market", "Lease time", "Price", "Per are", "Per unit", "Per are per year", "Per unit per year"]

book = xlrd.open_workbook("table.xls", formatting_info=True)
sheets = book.sheet_names()
print ("sheets are:", sheets)
for index, sh in enumerate(sheets):
    sheet = book.sheet_by_index(index)
    print ("Sheet:", sheet.name)
    rows, cols = sheet.nrows, sheet.ncols
    print ("Number of rows: %s   Number of cols: %s" % (rows, cols))

    # Iterate through rows, and print out the column values
    row_vals = []
    for row_idx in range(0, sheet.nrows):
        print('Row ', row_idx)
        for col_idx in range(len(cols_name)):
            cell_obj = sheet.cell(row_idx, col_idx)
            cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
            print("\t(%s): %s" % (cols_name[col_idx], cell_obj.value))

        xfx = sheet.cell_xf_index(row_idx, 0)
        xf = book.xf_list[xfx]
        bgx = xf.background.pattern_colour_index
        print ("\t\tColor %d" % bgx)
        #row_vals.append(cell_obj.value)