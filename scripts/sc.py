import csv
import os
import sys
from html_creator import *
from enum import Enum

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

# simlab related imports
from sim import sim_card
from sim import sim_router
from util import types
from sim import sim_shell
from sim import sim_reader
from optparse import OptionParser
from prettytable import PrettyTable

# file structure identifiers
C_FILE_STRUCTURE_TRANSPARENT = 0
C_FILE_STRUCTURE_LINEAR_FIXED = 1
C_FILE_STRUCTURE_CYCLIC = 3
C_FILE_STRUCTURE_UNKNOWN = 4

# defining the dictionary which will indicate index of the attributes in an specific csv file
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
    Unknown = 4


class ExpectedAccessCondition:
    read_condition = ()
    update_condition = ()
    increase_condition = ()
    activate_condition = ()
    deactivate_condition = ()

    def __init__(self):
        pass


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


def find_df_root_address(address, shell):
    add = address.split("/")
    df_name = add[len(add) - 1]

    # removing the csv from end of the file
    if df_name.endswith(".csv"):
        df_name = df_name[:-4]

    # getting the df address
    return shell.getAbsolutePath(df_name)


def check_file_exists(shell, path):
    sw1, sw2, data = shell.simCtrl.selectFileByPath(path)
    if sw1 == 0x90 and sw2 == 0x00:
        return True
    else:
        return False


def rule0_file_existence(shell, html, path):
    if check_file_exists(shell, path):
        return True, HtmlMessages.rule0_file_size_succeed_message
    else:
        return False, HtmlMessages.rule0_file_size_failed_message


def translate_ef_structure(structure):
    structure = structure.upper()
    if structure == "T" or structure == "TRANSPARENT":
        return C_FILE_STRUCTURE_TRANSPARENT, "Transparent"
    elif structure == "C" or structure == "CYCLIC":
        return C_FILE_STRUCTURE_CYCLIC, "Cyclic"
    elif structure == "L" or structure == "LINEAR" or structure == "LINEAR_FIXED" or structure == "FIXED":
        return C_FILE_STRUCTURE_LINEAR_FIXED, "Linear Fixed"
    else:
        return C_FILE_STRUCTURE_UNKNOWN, "Unknown"


def rule1_ef_structure_check(shell, html, path, expected_structure):
    structure = translate_ef_structure(expected_structure)

    structure_in_string = {C_FILE_STRUCTURE_TRANSPARENT: "Transparent",
                           C_FILE_STRUCTURE_CYCLIC: "Cyclic",
                           C_FILE_STRUCTURE_LINEAR_FIXED: "Linear Fixed",
                           C_FILE_STRUCTURE_UNKNOWN: "Unknown"}

    # getting the structure of the file
    sw1, sw2, data = shell.simCtrl.selectFileByPath(path)
    res = shell.simCtrl.getFileStructure(data)

    if res == structure[0]:
        return True, HtmlMessages.rule1_file_structure_succeed_message(
            structure_in_string[structure[0]] + " as expected")
    else:
        return False, HtmlMessages.rule1_file_structure_failed_message(
            "expected " + structure_in_string[structure[0]] + " got " + structure_in_string[res])


def translate_expecting_security_rule(read_condition,
                                      update_condition,
                                      increase_condition,
                                      activate_condition,
                                      deactivate_condition):
    def get_security_condition_tuple(strings):
        res = ()
        for i in strings:
            i = i.upper()
            if i == "ALWAYS" or i == "ALW":
                res += (types.AC_ALWAYS,)
            if i == "PIN" or i == "PIN1":
                res += (types.AC_CHV1,)
            if i == "PIN2":
                res += (types.AC_CHV2,)
            if i == "ADM1":
                res += (types.AC_ADM1,)
            if i == "ADM2":
                res += (types.AC_ADM2,)
            if i == "ADM3":
                res += (types.AC_ADM3,)
            if i == "ADM4":
                res += (types.AC_ADM4,)
            if i == "ADM5":
                res += (types.AC_ADM5,)
            if i == "NEV" or i == "NEVER":
                res += (types.AC_NEVER,)

    result = ExpectedAccessCondition()

    temp = read_condition.split("/")
    result.read_condition += get_security_condition_tuple(temp)

    temp = update_condition.split("/")
    result.update_condition += get_security_condition_tuple(temp)

    temp = increase_condition.split("/")
    result.increase_condition += get_security_condition_tuple(temp)

    temp = activate_condition.split("/")
    result.activate_condition += get_security_condition_tuple(temp)

    temp = deactivate_condition.split("/")
    result.deactivate_condition += get_security_condition_tuple(temp)

    return result


def rule2_security_check(shell, html, path, expected_security_condition):
    arrRecord, arrValue = shell.simCtrl.getArrRecordForFile(path)
    res = (True, "")

    tmp = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_READ)
    for condition in conditions:
        for expected in expected_security_condition.read_condition:
            if expected == condition:
                tmp = True

    tmp = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_UPDATE)
    for condition in conditions:
        for expected in expected_security_condition.update_condition:
            if expected == condition:
                tmp = True

    tmp = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_DEACTIVATE)
    for condition in conditions:
        for expected in expected_security_condition.deactivate_condition:
            if expected == condition:
                tmp = True

    tmp = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_ACTIVATE)
    for condition in conditions:
        for expected in expected_security_condition.activate_condition:
            if expected == condition:
                tmp = True


def analyze_metric_file(metric, shell, html):
    # getting header of the csv file
    csv_file = open(metric)
    csv_reader = csv.reader(csv_file, delimiter=",")

    # finding index of different attribute in the metric file
    set_the_map_indexes(csv_reader.next())

    # printing index of attributes in the metric file
    print(Attribute_Index)

    # getting  the address of the root DF, according to the name of the metric file
    root_address = find_df_root_address(metric, shell)

    # moving in the metric file
    for ef in csv_reader:
        tmp = root_address + "/" + ef[Attribute_Index[MetricKeys.File_ID]]

        rule0_res = rule0_file_existence(shell, html, tmp)

        rule1_res = ()
        if rule0_res[0]:
            res = rule1_ef_structure_check(shell, html, tmp, ef[Attribute_Index[MetricKeys.Structure]])
            rule1_res += res

        rule2_res = ()
        if rule0_res[0]:
            expected_security_condition = translate_expecting_security_rule(ef[Attribute_Index[MetricKeys.Read]],
                                                                            ef[Attribute_Index[MetricKeys.Update]],
                                                                            ef[Attribute_Index[MetricKeys.Increase]],
                                                                            ef[Attribute_Index[MetricKeys.Activate]],
                                                                            ef[Attribute_Index[MetricKeys.Deactivate]])

            rule2_res += rule2_security_check(shell, html, tmp, expected_security_condition)

        html.init_list_item(ef[Attribute_Index[MetricKeys.File_Name]] + ", " + tmp.replace("/", " | "), rule0_res[0])
        html.addtohtml(rule0_res[1])
        if rule1_res is not ():
            html.addtohtml(rule1_res[1])
        if rule2_res is not ():
            html.addtohtml(rule2_res[1])
        html.terminate_list_item()

    print("root address for the " + metric + " file is " + root_address)


def main():
    get_metric_files()

    # listing the metric files
    print("metric files are as below")
    print("----------------------------------------")
    for i in Metric_Files:
        print(i)
    print("----------------------------------------")

    # initializing the report output html
    html = HtmlCreator("IRMCI")

    # initializing the simLab utils
    my_sim = sim_card.SimCard(mode=sim_reader.MODE_PYSCARD)
    my_sim.removeAllReaders()
    my_sim.connect(0)
    my_router = sim_router.SimRouter(cards=[my_sim], type=types.TYPE_USIM, mode=sim_router.SIMTRACE_OFFLINE)
    my_router.run(mode=sim_router.ROUTER_MODE_DISABLED)
    my_shell = my_router.shell

    # initializing the html output
    html.init_html_tree()

    for Metric in Metric_Files:
        analyze_metric_file(Metric, my_shell, html)

    # terminating the html list tree
    html.terminate_html_tree()

    # disposing the resources
    my_sim.disconnect()
    my_sim.stop()

    html.terminate(TestResult.failed, "all passed", "./sample/res.html")


if __name__ == "__main__":
    main()
    # print(os.getcwd())
