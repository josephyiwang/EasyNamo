# all imports are native to Python (no third party libraries).
import string
import json
from collections import OrderedDict
from datetime import datetime, timezone
import re
import ast

class Parser:
    cursor = 0
    file_string = ""
    arrayPattern = r'^[\s]*{([\s\S]*?)}[\s]*$'
    objectPattern = r'"(.+)"[\s]*:[\s]*{[\s]*"([\s]*?(N|S|NULL|BOOL)[\s]*?)":[\s]*"(.+)"[\s]*}|"(.+)"[\s]*:[\s]*{[\s]*"L"[\s]*:[\s]*\[([\s\S]+?)\][\s]*}|"(.+)"[\s]*:[\s]*{[\s]*"M":[\s]*({[\s\S]+?})[\s]*}'
    listItemPattern = r'{[\s]*"[\s]*(.+?)[\s]*"[\s]*:[\s]*"[\s]*(.+?)[\s]*"[\s]*}'
    backingArray = []

    arrayRE = re.compile(arrayPattern)
    objectRE = re.compile(objectPattern)
    listItemPatternRE = re.compile(listItemPattern)

    def parse_file(self, file_name):
        self.cursor = 0
        self.backingList = []

        with open(file_name, 'r') as file:
            self.file_string = file.read().strip()

        arrayResults = self.arrayRE.findall(self.file_string)
        for array in arrayResults:
            objectResults = self.objectRE.findall(array)
            backingObject = OrderedDict()
            for objectResult in objectResults:
                self.processObject(objectResult, backingObject)
            self.backingArray.append(dict(sorted(backingObject.items())))
        print(json.dumps(self.backingArray))
        return (self.backingArray)
    
    def processObject(self, objectResult, backingObject):
        parsedName = objectResult[0].strip()
        match (objectResult[1].strip()):
                case "S":
                    parsedString = objectResult[3].strip()
                    dateConversion = self.is_rfc3339(parsedString)
                    if dateConversion > 0:
                        backingObject[parsedName] = dateConversion
                    elif parsedString != "":
                        backingObject[parsedName] = parsedString
                case "N":
                    parsedString = objectResult[3].strip().lstrip('0')
                    try:
                        # Try to evaluate to a number, otherwise don't add the result.
                        backingObject[parsedName] = ast.literal_eval(parsedString)
                    except:
                        return
                case "BOOL":
                    parsedString = objectResult[3].strip()
                    if parsedString in {"1", "t", "T", "TRUE", "true", "True"}:
                        backingObject[parsedName] = True
                    elif parsedString in {"0", "f", "F", "FALSE", "false", "False"}:
                        backingObject[parsedName] = False
                case "NULL":
                    parsedString = objectResult[3].strip()
                    if parsedString in {"1", "t", "T", "TRUE", "true", "True"}:
                        backingObject[parsedName] = None
                case "":
                    listString = objectResult[4].strip()
                    mapString = objectResult[6].strip()
                    if listString != "":
                        self.processList(objectResult, backingObject, listString)
                    elif mapString != "":
                        self.processMap(objectResult, backingObject, mapString)

                case _:
                    print ('unrecognized type')

    def processList(self, listResult, backingObject, listString):
       
       listItems = self.listItemPatternRE.findall(listResult[5])
       backingList = []
       listString = listResult[4].strip()
       for item in listItems:
            match (item[0].strip()):
                case "S":
                    parsedString = item[1].strip()
                    dateConversion = self.is_rfc3339(parsedString)
                    if dateConversion > 0:
                        backingList.append(dateConversion)
                    elif parsedString != "":
                        backingList.append(parsedString)
                case "N":
                    parsedString = item[1].strip().lstrip("0")
                    try:
                        # Try to evaluate to a number, otherwise don't add the result.
                        backingList.append(ast.literal_eval(parsedString))
                    except:
                        continue
                case "BOOL":
                    parsedString = item[1].strip()
                    if parsedString in {"1", "t", "T", "TRUE", "true", "True"}:
                        backingList.append(True)
                    elif parsedString in {"0", "f", "F", "FALSE", "false", "False"}:
                        backingList.append(False)
                case "NULL":
                    parsedString = item[1].strip()
                    if parsedString in {"1", "t", "T", "TRUE", "true", "True"}:
                        backingList.append(None)
       if len(backingList) > 0:
           backingObject[listString] = backingList

    def processMap(self, mapResult, backingObject, mapString): 
        backingMap = OrderedDict()
        mapObjects = self.objectRE.findall(mapResult[7])
        for mapObject in mapObjects:
            self.processObject(mapObject, backingMap)
        if len(backingMap.keys()) > 0:
            backingObject[mapString] = dict(sorted(backingMap.items()))
        
    def is_rfc3339(self, string):
        try:
            # Attempt to parse the string as a RFC3339 datetime
            return int(datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            return -1

def main():
    # Example usage:
    # file_path = 'example.txt'
    file_path = input("Please enter a filename to transform: ")
    example_parser = Parser()
    parsed_data = example_parser.parse_file(file_path)



if __name__ == "__main__":
    main()