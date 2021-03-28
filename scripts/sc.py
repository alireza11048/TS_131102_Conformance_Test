import csv
import os
from html_creator import *
from enum import Enum


# defining the dictionary which will indiate index of the attributes in an specific csv file
Attribute_Index = {}

# defining the default folder to read metrics from it
Metrics_Folder = "./metrics"

# a list to store metric file addresses
Metric_Files = []


# defining the keys which should be used in the metric.csv file
class MetricKeys:
    File_Name = "File Name"
    File_ID = "File ID"
    Structure = "Structure"
    Record_Size = "Record Size"
    Record_Size_Co = "Record Size Co"
    Record_Num = "Record Num"
    Transparent_File_Size = "Transparent File Size"
    Transparent_File_Size_Co = "Transparent File Size Co"
    Read = "Read"
    Update = "Update"
    Deactivate = "Deactivate"
    Activate = "Activate"
    Increase = "Increase"
    SFI = "SFI"


class EFStructure(Enum):
    Transparent = 1
    LinearFixed = 2
    Cyclic = 3


def set_the_map_indexes(header_list):
    keys_name = dir(MetricKeys)
    for key in keys_name:
        if not key.startswith('_'):
            temp = getattr(MetricKeys, key)
            index = -1
            for i in range(0, len(header_list)):
                if header_list[i] == temp:
                    index = i
                    break
            Attribute_Index[temp] = index


def get_metric_files():
    files = os.listdir(Metrics_Folder)
    for file in files:
        if file.endswith(".csv"):
            Metric_Files.append(Metrics_Folder + "/" + file)


def main():
    get_metric_files()

    # listing the metric files
    print("metric files are as below")
    print("----------------------------------------")
    for i in Metric_Files:
        print(i)
    print("----------------------------------------")

    for Metric in Metric_Files:
        # getting header of the csv file
        csv_file = open(Metric)
        csv_reader = csv.reader(csv_file, delimiter=",")
        set_the_map_indexes(csv_reader.next())
        print(Attribute_Index)

    html = HtmlCreator("IRMCI")
    html.terminate(TestResult.failed, "all passed", "./sample/res.html")


if __name__ == "__main__":
    main()
    #print(os.getcwd())

