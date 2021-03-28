from enum import Enum
import shutil


class TestResult(Enum):
    failed = 1
    succed = 2


class HtmlCreator:
    htmlcode = ""
    htmlmiddle = ""
    css_base_address = "htmlfiles\\listree.min.css"
    jvc_base_address = "htmlfiles\\listree.umd.min.js"

    def __init__(self, name):
        self.htmlcode = "" \
                        "<!DOCTYPE html>" \
                        "<html>" \
                        "<head>" \
                        "<link rel=\"stylesheet\" href=\"listree.min.css\"/>"

        self.htmlcode += "<title>LisTree</title>"

        self.htmlcode += "" \
                         "</head>" \
                         "<body>" \
                         "<h1>"

        self.htmlcode += name + "</h1>"

    def addtohtml(self, code):
        self.htmlmiddle += code

    def terminate(self, test_result, report, address):
        self.htmlcode += "<h2> Summary </h2>"

        if test_result == TestResult.failed:
            self.htmlcode += "<h3 class=\"failed2\"> failed </h3>"
        else:
            self.htmlcode += "<h3 class=\"succeed\"> succeed </h3>"

        self.htmlcode += "<p>" + report + "</p>"

        self.htmlcode += "<hr>"

        self.htmlcode += self.htmlmiddle

        self.htmlcode += "" \
                         "<script src=\"listree.umd.min.js\"></script>" \
                         "<script>" \
                         "listree();" \
                         "</script>" \
                         "</body>" \
                         "</html>"

        f = open(address, "a")
        f.write(self.htmlcode)
        f.close()

        res = address.split("\\")
        res = res[0:len(res) - 1]
        target = "\\".join(res)

        shutil.copy2(self.css_base_address, target)
        shutil.copy2(self.jvc_base_address, target)
