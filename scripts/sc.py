import csv
import os
import sys
from html_creator import *
from enum import Enum

# adding the root of the simLab to the default paths
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

# defining the dictionary which will indicate the index of the attributes in a specific CSV file
Attribute_Index = {}

# defining the default folder to read metrics from it
Metrics_Folder = "./metrics"

# a list to store address of metric files
Metric_Files = []


# defining the keys which can be used in the metric.csv file
class MetricKeys:
    def __init__(self):
        pass

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


# this class contains required conditions for different operations on files
class ExpectedAccessCondition:
    read_condition = ()
    update_condition = ()
    increase_condition = ()
    activate_condition = ()
    deactivate_condition = ()

    def __init__(self):
        pass


# this function initializes the Attribute_Index dictionary, which keeps index of each metric key
def set_the_map_indexes(header_list):
    # getting all members of the MetricKeys class
    keys_name = dir(MetricKeys)

    # moving in the list
    for key in keys_name:
        # we shouldn't check default class members which start with '_' char
        if not key.startswith('_'):
            # catching value of the class member
            temp = getattr(MetricKeys, key)

            # moving in the header of the csv file
            index = -1
            for i in range(0, len(header_list)):
                if header_list[i] == temp:
                    index = i
                    break
            Attribute_Index[temp] = index


# this function  lists all metric files which are exist in the default metric folder
def get_metric_files():
    files = os.listdir(Metrics_Folder)
    for file in files:
        # metric files are csv files
        if file.endswith(".csv"):
            Metric_Files.append(Metrics_Folder + "/" + file)


# every csv file, includes expected properties of all files which are exists in a Dedicated Folder in the simcard,
# which name of the Dedicated Folder is equal to the name of the csv file
# this function receive address of a csv file in computer, and find adress of the Dedicated file in the simcard with
# the simLab tool
def find_df_root_address(address, shell):
    # splitting name of the metric file
    add = address.split("/")
    df_name = add[len(add) - 1]

    # removing the .csv from end of the file
    if df_name.endswith(".csv"):
        df_name = df_name[:-4]

    # getting the df address
    return shell.getAbsolutePath(df_name)


# this function receives address of a EF files and check existence of that in the simCard
def check_file_exists(shell, path):
    # selecting the file
    sw1, sw2, data = shell.simCtrl.selectFileByPath(path)

    # status code is 0x90 0x00, if the file is exists
    if sw1 == 0x90 and sw2 == 0x00:
        return True
    else:
        return False


# implementation of rule0,
def rule0_file_existence(shell, html, path):
    if check_file_exists(shell, path):
        return True, HtmlMessages.rule0_file_size_succeed_message
    else:
        return False, HtmlMessages.rule0_file_size_failed_message


# this function receives abbreviation of file structure and return it's full name and tag
def translate_ef_structure(structure):
    # capitalizing the input name
    structure = structure.upper()

    if structure == "T" or structure == "TRANSPARENT":
        return C_FILE_STRUCTURE_TRANSPARENT, "Transparent"
    elif structure == "C" or structure == "CYCLIC":
        return C_FILE_STRUCTURE_CYCLIC, "Cyclic"
    elif structure == "L" or structure == "LINEAR" or structure == "LINEAR_FIXED" or structure == "FIXED":
        return C_FILE_STRUCTURE_LINEAR_FIXED, "Linear Fixed"
    else:
        return C_FILE_STRUCTURE_UNKNOWN, "Unknown"


# this function is implementation of the rule1, file structure test
def rule1_ef_structure_check(shell, html, path, expected_structure):
    structure = translate_ef_structure(expected_structure)

    structure_in_string = {C_FILE_STRUCTURE_TRANSPARENT: "Transparent",
                           C_FILE_STRUCTURE_CYCLIC: "Cyclic",
                           C_FILE_STRUCTURE_LINEAR_FIXED: "Linear Fixed",
                           C_FILE_STRUCTURE_UNKNOWN: "Unknown"}

    # getting the structure of the file
    sw1, sw2, data = shell.simCtrl.selectFileByPath(path)
    res = shell.simCtrl.getFileStructure(data)

    # checking the result with the expected one
    if res == structure[0]:
        return True, HtmlMessages.rule1_file_structure_succeed_message(
            structure_in_string[structure[0]] + " as expected")
    else:
        return False, HtmlMessages.rule1_file_structure_failed_message(
            "expected " + structure_in_string[structure[0]] + " got " + structure_in_string[res])


# this function receives coded security condition and return decodes it in a ExpectedAccessCondition structure and
# return the result
def translate_expected_security_rule(read_condition,
                                     update_condition,
                                     increase_condition,
                                     activate_condition,
                                     deactivate_condition):
    # function to decode a single rule
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
            if i == "ADM1" or i == "ADM":
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
        return res

    result = ExpectedAccessCondition()

    # decoding read condition
    temp = read_condition.split("/")
    result.read_condition += get_security_condition_tuple(temp)

    # decoding update condition
    temp = update_condition.split("/")
    result.update_condition += get_security_condition_tuple(temp)

    # decoding increase condition
    temp = increase_condition.split("/")
    result.increase_condition += get_security_condition_tuple(temp)

    # decoding activate condition
    temp = activate_condition.split("/")
    result.activate_condition += get_security_condition_tuple(temp)

    # decoding deactivate condition
    temp = deactivate_condition.split("/")
    result.deactivate_condition += get_security_condition_tuple(temp)

    return result


# implementation of the rule2, which check expected security conditions
def rule2_security_check(shell, html, path, expected_security_condition, ef):
    # getting the arr record of the specified file
    arrRecord, arrValue = shell.simCtrl.getArrRecordForFile(path)
    result = True
    output = ""

    # decoding the Read access condition
    read_res = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_READ)
    for condition in conditions:
        for expected in expected_security_condition.read_condition:
            if expected == condition:
                read_res = True

    # decoding the update access condition
    update_res = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_UPDATE)
    for condition in conditions:
        for expected in expected_security_condition.update_condition:
            if expected == condition:
                update_res = True

    # decoding the deactivate access condition
    deactivate_res = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_DEACTIVATE)
    for condition in conditions:
        for expected in expected_security_condition.deactivate_condition:
            if expected == condition:
                deactivate_res = True

    # decoding the activate access condition
    activate_res = False
    conditions, condMode = types.getAccessConditions(arrValue, types.AM_EF_ACTIVATE)
    for condition in conditions:
        for expected in expected_security_condition.activate_condition:
            if expected == condition:
                activate_res = True

    # if any of the conditions did not meet, specifying the result of security check to failed
    if read_res is False or update_res is False or deactivate_res is False or activate_res is False:
        result = False

    # adding header of security rule
    if result is True:
        output = HtmlMessages.rule2_security_check_add_base_succeed()
    else:
        output = HtmlMessages.rule2_security_check_add_base_failed()

    # adding Read operation sub-section
    if read_res:
        output += HtmlMessages.rule2_security_check_add_sub_section(read_res, "Read", ef[
            Attribute_Index[MetricKeys.Read]] + " as expected")
    else:
        output += HtmlMessages.rule2_security_check_add_sub_section(read_res, "Read", "expected " + ef[
            Attribute_Index[MetricKeys.Read]])

    # adding Update operation sub-section
    if update_res:
        output += HtmlMessages.rule2_security_check_add_sub_section(update_res, "Update", ef[
            Attribute_Index[MetricKeys.Update]] + " as expected")
    else:
        output += HtmlMessages.rule2_security_check_add_sub_section(update_res, "Update", "expected " + ef[
            Attribute_Index[MetricKeys.Update]])

    # adding Deactivate operation sub-section
    if deactivate_res:
        output += HtmlMessages.rule2_security_check_add_sub_section(deactivate_res, "Deactivate", ef[
            Attribute_Index[MetricKeys.Deactivate]] + " as expected")
    else:
        output += HtmlMessages.rule2_security_check_add_sub_section(deactivate_res, "Deactivate", "expected " + ef[
            Attribute_Index[MetricKeys.Deactivate]])

    # adding Activate operation sub-section
    if activate_res:
        output += HtmlMessages.rule2_security_check_add_sub_section(activate_res, "Activate", ef[
            Attribute_Index[MetricKeys.Activate]] + " as expected")
    else:
        output += HtmlMessages.rule2_security_check_add_sub_section(activate_res, "Activate", "expected " + ef[
            Attribute_Index[MetricKeys.Activate]])

    # terminating the section
    output += HtmlMessages.rule2_security_check_terminate()

    # returning the result as a tuple
    return result, output


# this function will check the
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
        # getting address of the EF file
        tmp = root_address + "/" + ef[Attribute_Index[MetricKeys.File_ID]]

        # checking rule0, File existence
        rule0_res = rule0_file_existence(shell, html, tmp)

        # checking result1, EF file structure
        rule1_res = ()
        if rule0_res[0]:
            res = rule1_ef_structure_check(shell, html, tmp, ef[Attribute_Index[MetricKeys.Structure]])
            rule1_res += res

        # checking rule2, EF File security
        rule2_res = ()
        if rule0_res[0]:
            expected_security_condition = translate_expected_security_rule(ef[Attribute_Index[MetricKeys.Read]],
                                                                           ef[Attribute_Index[MetricKeys.Update]],
                                                                           ef[Attribute_Index[MetricKeys.Increase]],
                                                                           ef[Attribute_Index[MetricKeys.Activate]],
                                                                           ef[Attribute_Index[MetricKeys.Deactivate]])

            rule2_res += rule2_security_check(shell, html, tmp, expected_security_condition, ef)

        # building the html
        html.init_list_item(ef[Attribute_Index[MetricKeys.File_Name]] + ", " + tmp.replace("/", " | "), rule0_res[0])
        html.addtohtml(rule0_res[1])
        if rule1_res is not ():
            html.addtohtml(rule1_res[1])
        if rule2_res is not ():
            html.addtohtml(rule2_res[1])
        html.terminate_list_item()


def main():
    # getting metric files
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

    # moving in the metric files
    for Metric in Metric_Files:
        analyze_metric_file(Metric, my_shell, html)

    # terminating the html list tree
    html.terminate_html_tree()

    # disposing the resources
    my_sim.disconnect()
    my_sim.stop()

    # terminating the html
    html.terminate(TestResult.failed, "all passed", "./sample/res.html")


if __name__ == "__main__":
    main()
    # print(os.getcwd())
