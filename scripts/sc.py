import csv

csv_file = open("D:\\Alireza\\My documents\\ts_131_102_conformance\\metrics\\EFs_Under_USMI_ADF.csv")
csv_reader = csv.reader(csv_file, delimiter=",")

header = []
file_detail = []
line_counter = 0

for row in csv_reader:
    if(line_counter == 0):
        header = row
    else:
        file_detail = row
    line_counter += 1
    
print(header)
print(file_detail)
