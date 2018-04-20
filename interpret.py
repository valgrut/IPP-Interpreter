#!/usr/bin/env python
#coding=UTF-8
from sys import stdin
import xml.etree.ElementTree as ET
import sys
import getopt
import re

SUCCESS = 0
SEMANTIC_ERROR = 52
RUNTIME_ERROR_BAD_OPERAND_TYPES  = 53
RUNTIME_ERROR_UNDEFINED_VARIABLE = 54
RUNTIME_ERROR_UNDEFINED_FRAME    = 55
RUNTIME_ERROR_UNDEFINED_VALUE    = 56
RUNTIME_ERROR_DIVIDE_BY_ZERO     = 57
RUNTIME_ERROR_STRING_OPERATION   = 58

# trida reprezentujici konkretni promennou. Promenne jsou ulozene v ramcich
class Variable:
    def __init__(self):
        self.__typ = "" #None
        self.__name = None
        self.__value = None
        return

    def getType(self):
        return self.__typ

    def getName(self):
        return self.__name

    def getValue(self):
        if self.__value is None:
            return ('')
        return self.__value

    def setType(self, typ):
        self.__typ = typ

    def setName(self, name):
        self.__name = name

    def setValue(self, val):
        #self.__value = str(val)
        if self.getType() == "string":
            self.__value = replaceEscape(val, escapes)
        else:
            self.__value = val

    def printVariable(self):
        sys.stderr.write("     "+self.getType().ljust(10, ' ') + self.getName().ljust(20, ' ') + str(self.getValue()).ljust(25, ' ')+"\n")


# ramec pro promenne
class Frame:
    def __init__(self):
        #print("Trida frame vytvorena")
        self.variables = {}

    def insertVariable(self, obj):
        #print("InsertVariable: ", obj.getName())
        self.variables[obj.getName()] = obj

    def variableExists(self, varName):
        if varName in self.variables.keys():
            return True
        return False

    def getVariableObj(self, varName):
        if(self.variableExists(varName)):
            #print ("Promenna ", varName, " existuje")
            return self.variables[varName]
        else:
            sys.stderr.write("ERR: Nelze vratit objekt promenne, neexistuje\n")
            return None

    def setVariableValue(self, varName, value):
        if(self.variableExists(varName)):
            self.variables[varName].setValue(value)
        else:
            sys.stderr.write(("ERR: Promenna "+ varName+ " neexistuje v tomto ramci.\n"))
            return False

    def printVariables(self):
        sys.stderr.write("     "+"typ".ljust(10, ' ') + "jmeno".ljust(20, ' ') + "hodnota".ljust(25, ' ')+"\n\n")
        for key in self.variables.values():
            key.printVariable()

    def empty(self):
        if len(self.variables) == 0:
            return True
        else:
            return False

    def clearFrame(self):
        self.variables.clear()

# Trida reprezentujici zasobnik lokalnich ramcu
class LocalFrameContainer:
    def __init__(self):
        self.__localFrames = []

    def pushFrame(self, frame):
        self.__localFrames.append(frame)

    def popFrame(self):
        if len(self.__localFrames) > 0:
            self.__localFrames.pop()
        else:
            exit(55)

    def topFrame(self):
        if len(self.__localFrames) > 0:
            return self.__localFrames[len(self.__localFrames)-1]
        else:
            sys.stderr.write("Chyba: localFrameCont empty\n")
            exit(55)

    def getVariableObj(self, varName):
        top = self.topFrame()
        obj = top.getVariableObj(varName)
        if obj is not None:
            return obj
        else:
            sys.stderr.write("ERR: Nelze vratit objekt promenne, neexistuje\n")
            return None

    def countFrames(self):
        return len(self.__localFrames)

    def variableExistsOnTop(self, variable):
        # projit TOP frame a zjistit, jestli je zde hledana promenna
        # vyuzit funkci ve Frame class - variableExists()
        pass

    def insertVariable(self, variable):
        top = self.topFrame()
        top.insertVariable(variable)

    def printAllFrames(self):
        i = 0
        for frame in self.__localFrames:
            sys.stderr.write(str(i)+". Layer: \n")
            frame.printVariables()
            i += 1

# Trida reprezentujici konkretni instrukci
# obsahuje operace pro manipulaci s argumenty v dane instrukci
class Instruction:
    def __init__(self):
        self.__args = []
        self.__opcode = None

    def setOpcode(self, opcode):
        self.__opcode = opcode

    def getOpcode(self):
        return self.__opcode

    def appendArg(self, arg):
        self.__args.append(arg)

    def getArgs(self):
        return self.__args


# rozdeli na cast pred prvnim vyskytem '@' a za @-> (typ, hodnota) nebo (frame, promenna)
def splitOnHalf(symb):
    return symb.split('@', 1)

# vlozi do zadaneho framu instanci promenne
def insertToFrame(frame, varObj):
    global globalFrame
    global localFrameContainer
    global tmpFrame
    if(frame == "GF"):
        globalFrame.insertVariable(varObj)
        #print("Vlozeno do GF")

    elif(frame == "LF"):
        localFrameContainer.insertVariable(varObj)
        #print("Vlozeno do LF")

    elif(frame == "TF"):
        if tmpFrame != None:
            tmpFrame.insertVariable(varObj)
        else:
            sys.stderr.write("Temp frame nebyl vytvoren\n")
            exit(55)

# vrati z framu promennou (instanci) podle jejiho jmena
def getFromFrame(frame, varName):
    global globalFrame
    global localFrameContainer
    global tmpFrame
    if(frame == "GF"):
        return globalFrame.getVariableObj(varName)

    elif(frame == "LF"):
        return localFrameContainer.getVariableObj(varName)

    elif(frame == "TF"):
        if tmpFrame != None:
            return tmpFrame.getVariableObj(varName)
        else:
            sys.stderr.write("TMP frame nebyl vytvoren\n")
            exit(55)
    return None

# vrati index (radek), ktery je oznacen labelem label
def getIndexByLabel(label):
    global labels
    if label in labels:
        return labels[label]
    else:
        sys.stderr.write("Neexistujici label.\n")
        exit(56) #TODO ??

# vstup je promenna. podle hodnoty pred @ zjisti, jestli je to var nebo hodnota
def isSymbVariable(symb):
    if symb in ["GF", "LF", "TF"]:
        return True
    return False

# prohleda patricny ramec podle prefixu promenne (GF/LF..) a vrati tento objekt
def processVar(var):
    split = splitOnHalf(var)

    obj = getFromFrame(split[0], split[1])
    if obj is None:
        sys.stderr.write("Cilova promenna "+split[1]+" neexistuje v tomto ramci\n")
        exit(54)

    return obj #vracime objekt promenne

# kontrola spravneho formatu cisla, retezce...
def checkFormat(operand, expectedType):
    both = splitOnHalf(operand)
    #print ("t: " + both[0])

    t = both[0]
    v = (both[1] if len(both) == 2 else None)

    #type or label
    if len(both) == 1:
        if t in ("int", "bool", "string"):
            if expectedType == "type":
                return "type"
            elif expectedType == "label":
                return "label"
            else:
                return None
        else:
            obj = re.match(r'^[a-zA-Z_\-$&%*][a-zA-Z0-9_\-$&%*]*$', t)
            return ("label" if obj is not None else None)

    #int | bool | string | GF | LF | TF
    if len(both) == 2:
        #constanta
        if t in ("int", "bool", "string"):
            if t == "int":
                #print ("int")
                obj = re.match(r'^[+|-]{0,1}[0-9]+$', v)
                return ("int" if obj is not None else None)

            if t == "string":
                #print ("string")
                obj = re.match(r'^(\\[0-9]{3}|[^\s #\\])*$', v)
                return ("string" if obj is not None else None)

            if t == "bool":
                #print ("bool")
                obj = re.match(r'^(true|false)$', v)
                return ("bool" if obj is not None else None)

        if t in ("GF", "LF", "TF"):
            #print ("promenna")
            obj = re.match(r'^[a-zA-Z_\-$&%*][a-zA-Z0-9_\-$&%*]*$', v)
            return ("var" if obj is not None else None)

    return None

# nahradi substringy tvaru \xxx, kde xxx je cislo od 000 po 035 (092) a nahradi je jejich reprezentaci
def replaceEscape(text, dic):
    for key, value in dic.items():
        text = text.replace(key, value)
    return text

#vypis bsah vseho
def printAll():
    global globalFrame
    global localFrameContainer
    global tmpFrame
    global dataStack
    sys.stderr.write("\n")

    sys.stderr.write("GLOBAL FRAME:\n")
    globalFrame.printVariables()
    sys.stderr.write("\n")

    sys.stderr.write("LOCAL Frame:\n")
    localFrameContainer.printAllFrames()
    sys.stderr.write("\n")

    sys.stderr.write("TMP Frame:\n")
    tmpFrame.printVariables() if tmpFrame is not None else sys.stderr.write("     TMP frame je prazdny.\n")
    sys.stderr.write("\n")

    sys.stderr.write("Data Stack:\n")
    if len(dataStack) != 0:
        for index, data in enumerate(dataStack):

            if index == len(dataStack) - 1:
                sys.stderr.write(" TOP " + str(index) + "  " + data +"\n")
            else:
                sys.stderr.write("     " + str(index) + "  " + data +"\n")
    else:
        sys.stderr.write("     Zasobnik je prazdny.\n")


def printHelp():
    print("interpret.py")
    print("Usage: ")
    print("  --help          vypise napovedu a ukonci program")
    print("  --source=input  vstupni soubor s xml-encoded zdrojovym kodem")
    print("  --stats=file    vystupni soubor pro zapis statistik")
    print("  --vars          do statistik zahrnout pocet inicializovanyhc promennych")
    print("  --insts         do statistik zahrnout pocet provedenych instrukci")
    exit(0)

# vrati dvojici [typ, hodnota] vstupniho symb - nezavisle na tom, jestli je symb promenna nebo value
def getSymbData(symb):
    inputSymb = splitOnHalf(symb)

    if isSymbVariable(inputSymb[0]):
        inputObj = processVar(symb)
        v = inputObj.getValue()
        t = inputObj.getType()
    else:
        v = replaceEscape(inputSymb[1], escapes)
        t = inputSymb[0]

        if t == "int":
            v = int(v)

    return [t, v]

# -------------------------------------------------------------------------------------------------------
# -------------------- INSTRUKCE ------------------------------------------------------------------------
def MOVE(var, symb):
    global localFrameContainer
    global globalFrame

    outputObj = processVar(var)

    inputSymb = splitOnHalf(symb)
    if isSymbVariable(inputSymb[0]):
        inputObj = processVar(symb)
        outputObj.setValue(inputObj.getValue())
        outputObj.setType(inputObj.getType())
    else:
        #print("Typ: ", inputSymb)
        outputObj.setType(inputSymb[0])
        if len(inputSymb) > 1:
            if inputSymb[0] == "int":
                outputObj.setValue(int(inputSymb[1]))
                return
            outputObj.setValue(inputSymb[1])
        else:
            outputObj.setValue("")
    return

def CREATEFRAME():
    global tmpFrame
    tmpFrame = Frame()

def PUSHFRAME():
    global tmpFrame
    global localFrameContainer
    if tmpFrame is not None:
        localFrameContainer.pushFrame(tmpFrame)
        tmpFrame = None
    else:
        sys.stderr.write("ERR: tmpFrame je prazdny")
        exit(55)


def POPFRAME():
    global localFrameContainer
    global tmpFrame
    if localFrameContainer.countFrames() > 0:
        tmpFrame = localFrameContainer.topFrame()
        localFrameContainer.popFrame()
    else:
        exit(55)

def DEFVAR(var):
    splitVar = splitOnHalf(var)
    newVar = Variable()
    newVar.setName(splitVar[1])

    insertToFrame(splitVar[0], newVar)

def CALL(label):
    global callStack
    global PC
    callStack.append(PC+1)
    PC = getIndexByLabel(label)

def RETURN():
    global PC
    global callStack
    if len(callStack) > 0:
        PC = callStack.pop() - 1
    else:
        sys.stderr.write("RETURN: zasobnik volani je prazdny.\n")
        exit(56)

def PUSHS(symb):
    global dataStack
    t1, v1 = getSymbData(symb)
    dataStack.append(str(t1)+'@'+str(v1))
    return

def POPS(var):
    global dataStack

    destObj = processVar(var)

    if not dataStack:
        sys.stderr.write("POPS - prazdny zasobnik\n")
        exit(56)
    symb = dataStack.pop()

    t1, v1 = getSymbData(symb)
    destObj.setType(t1)
    destObj.setValue(v1)

def ADD(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 != "int" and t2 != "int":
        sys.stderr.write("ADD: typy se nerovnaji nebo nejsou int\n")
        exit(53)

    outputVar = processVar(var)
    outputVar.setType("int")
    outputVar.setValue(v1+v2)
    return

def SUB(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 != "int" and t2 != "int":
        sys.stderr.write("SUB: typy se nerovnaji nebo nejsou int\n")
        exit(53)

    outputVar = processVar(var)
    outputVar.setType("int")
    outputVar.setValue(v1-v2)
    return

def MUL(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 != t2 != "int":
        sys.stderr.write("MUL: typy se nerovnaji nebo nejsou int\n")
        exit(53)

    outputVar = processVar(var)
    outputVar.setType("int")
    outputVar.setValue(v1*v2)
    return

def IDIV(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if v2 == 0:
        sys.stderr.write("Chyba: Deleni nulou!\n")
        exit(57)

    if t1 != t2 != "int":
        sys.stderr.write("IDIV: typy se nerovnaji nebo nejsou int\n")
        exit(53)

    outputVar = processVar(var)
    outputVar.setType("int")
    outputVar.setValue(v1//v2)
    return

def LT(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    outputVar = processVar(var)

    if t1 != t2:
        sys.stderr.write("LT: typy se nerovnaji\n")
        exit(53)

    outputVar.setValue(v1 < v2)
    outputVar.setType("bool")
    return

def GT(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    outputVar = processVar(var)

    if t1 != t2:
        sys.stderr.write("LT: typy se nerovnaji\n")
        exit(53)

    outputVar.setValue(v1 > v2)
    outputVar.setType("bool")
    return

def EQ(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    outputVar = processVar(var)

    if t1 != t2:
        sys.stderr.write("LT: typy se nerovnaji\n")
        exit(53)

    outputVar.setValue(v1 == v2)
    outputVar.setType("bool")
    return

def AND(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    outputVar = processVar(var)

    if t1 != t2 != outputVar.getType() != "bool":
        sys.stderr.write("AND: typy se nerovnaji nebo nejsou bool\n")
        exit(53)

    outputVar.setValue(v1 & v2)
    return

def OR(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    outputVar = processVar(var)

    if t1 != t2 != outputVar.getType() != "bool":
        sys.stderr.write("AND: typy se nerovnaji nebo nejsou bool\n")
        exit(53)

    outputVar.setValue(v1 | v2)
    return

def NOT(var, symb1):
    t1, v1 = getSymbData(symb1)

    outputVar = processVar(var)

    if t1 != outputVar.getType() != "bool":
        sys.stderr.write("AND: typy se nerovnaji nebo nejsou bool\n")
        exit(53)

    outputVar.setValue(~v1)
    return

def INT2CHAR(var, symb):
    t1, v1 = getSymbData(symb)

    if int(v1) >= 0:
        outputVar = processVar(var)
        outputVar.setValue(chr(int(v1)))
        outputVar.setType("string")
    else:
        exit(58)
    return

def STRI2INT(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)
    if t2 != "int":
        sys.stderr.write("STRI2INT: index neni typu int\n")
        exit(53)

    inputlen = len(v1)
    if v2 >= 0 and v2 < inputlen:
        char = v1[v2]
    else:
        sys.stderr.write("STRI2INT: index "+ str(v2) + " mimo meze retezce\n")
        exit(58)

    outputVar = processVar(var)
    outputVar.setType("int")
    outputVar.setValue(ord(char))

    return

def READ(var, type):
    outputVar = processVar(var)

    value = input()

    if type == "int":
        # TODO kontrola
        try:
            intValue = int(value)
        except ValueError:
            #sys.stderr.write("Ocekavano cislo!\n")
            #exit(53)
            intValue = 0
        outputVar.setValue(intValue)
    elif type == "string":
        if '#' in value:
            outputVar.setValue(str(""))
        #elif '\\' in replaced:
        #    outputVar.setValue(str(""))
        else:
            outputVar.setValue(str(replaceEscape(value, escapes)))
    elif type == "bool":
        if value == "true":
            outputVar.setValue("true")
        else:
            outputVar.setValue("false")
        return
    else:
        sys.stderr.write("CHYBA: neexistujici typ byl zadan\n")
        exit(53)

    outputVar.setType(type)
    return


def WRITE(symb):
    inputSymb = splitOnHalf(symb)

    if isSymbVariable(inputSymb[0]):
        inputObj = processVar(symb)

        #print('.', end='')
        #print(inputObj.getValue())

        print(str(inputObj.getValue()))
        #sys.stdout.write(str(inputObj.getValue()))
        #sys.stdout.flush()
    else:
        print(replaceEscape(inputSymb[1], escapes))
        #sys.stdout.write(replaceEscape(inputSymb[1], escapes))
        #sys.stdout.flush()
    return


def CONCAT(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 != t2 != "string":
        sys.stderr.write("Concat: typy se nerovnaji a nejsou string\n")
        exit(53)

    outputVar = processVar(var)
    outputVar.setValue(v1+v2)
    return

def STRLEN(var, symb):
    destObj = processVar(var)

    t1, v1 = getSymbData(symb)

    if t1 != "string":
        sys.stderr.write("STRLEN: typy se nerovnaji a nejsou string\n")
        exit(53)

    stringlen = len(v1)

    outputVar = processVar(var)
    outputVar.setValue(stringlen)
    outputVar.setType("int")
    return

def GETCHAR(var, symb1, symb2):
    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)
    v2 = int(v2)

    if t1 != "string":
        sys.stderr.write("GETCHAR: typy se nerovnaji a nejsou string\n")
        exit(53)

    if t2 != "int":
        sys.stderr.write("GETCHAR: index neni typu int\n")
        exit(53)

    inputlen = len(v1)
    if v2 >= 0 and v2 < inputlen:
        char = v1[v2]
    else:
        sys.stderr.write("GETCHAR: index "+ str(v2) + " mimo meze retezce\n")
        exit(58)

    outputVar = processVar(var)
    outputVar.setValue(char)
    outputVar.setType("string")
    return

def SETCHAR(var, symb2, symb1):
    inputSymb1 = splitOnHalf(symb1)

    #znak
    if isSymbVariable(inputSymb1[0]):
        inputObj1 = processVar(symb1)
        v1 = inputObj1.getValue()[0] if len(inputObj1.getValue()) > 1 else inputObj1.getValue()
        t1 = inputObj1.getType()
    else:
        v1 = inputSymb1[1][0] if len(inputSymb1[1]) > 1 else inputSymb1[1]
        t1 = inputSymb1[0]

    if t1 != "string":
        sys.stderr.write("SETCHAR: typy se nerovnaji a nejsou string\n")
        exit(53)

    #index
    t2, v2 = getSymbData(symb2)

    if t2 != "int":
        sys.stderr.write("SETCHAR: index neni typu int\n")
        exit(53)

    outputVar = processVar(var)
    inputlen = len(outputVar.getValue())
    if v2 >= 0 and v2 < inputlen:
        string = outputVar.getValue()
    else:
        sys.stderr.write("SETCHAR: index "+ str(v2) + " mimo meze retezce\n")
        exit(58)

    stringList = list(string)
    stringList[v2] = v1
    outputVar.setValue("".join(stringList))
    outputVar.setType("string")
    return


def TYPE(var, symb):
    # cilova promenna
    destObj = processVar(var)

    # promenna ze zasovniku
    inputSymb = splitOnHalf(symb)
    if isSymbVariable(inputSymb[0]):
        inputObj = processVar(symb)
        if inputObj.getValue() is None:
            destObj.setValue("")
        else:
            destObj.setValue(inputObj.getType())
    else:
        destObj.setValue(inputSymb[0])

    destObj.setType("string")
    return


def LABEL(label):
    #global labels
    #global PC
    #if label not in labels:
    #    pass
    #else:
    #    pass
    return

def JUMP(label):
    global PC
    global labels
    PC = getIndexByLabel(label)
    return

def JUMPIFEQ(label, symb1, symb2):
    global PC
    global labels

    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 == t2:
        if v1 == v2:
            PC = getIndexByLabel(label) -1 # ?
            return
    else:
        exit(53)

    return

def JUMPIFNEQ(label, symb1, symb2):
    global PC
    global labels

    t1, v1 = getSymbData(symb1)
    t2, v2 = getSymbData(symb2)

    if t1 == t2:
        if v1 != v2:
            PC = getIndexByLabel(label)
    else:
        exit(53)
    return

def DPRINT(symb):
    inputSymb = splitOnHalf(symb)

    if isSymbVariable(inputSymb[0]):
        inputObj = processVar(symb)

        sys.stderr.write(str(inputObj.getValue()))
        sys.stderr.flush()
    else:
        sys.stderr.write(replaceEscape(inputSymb[1], escapes))
        sys.stderr.flush()

    return

def BREAK():
    sys.stderr.write("\n<---------------------BREAK--------------------->\n")
    sys.stderr.write("Celkem provedenych instrukci: " + str(callCounter) + "\n")
    sys.stderr.write("Programovy citac - PC: " + str(PC) + "\n")
    printAll()
    sys.stderr.write("<---------------------\BREAK--------------------->\n")
    return

# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
# ---------------------------------------------- MAIN -------------------------------------------
# -----------------------------------------------------------------------------------------------

instrukctionCall = {
    "MOVE"          : [ MOVE, ["var", "symb"] ],
    "CREATEFRAME"   : [ CREATEFRAME, []],
    "PUSHFRAME"     : [ PUSHFRAME, []],
    "POPFRAME"      : [ POPFRAME, []],
    "DEFVAR"        : [ DEFVAR,["var"]],
    "CALL"          : [ CALL,["label"]],
    "RETURN"        : [ RETURN,[]],
    "PUSHS"         : [ PUSHS,["symb"]],
    "POPS"          : [ POPS,["var"]],
    "ADD"           : [ ADD,["var", "symb", "symb"]],
    "SUB"           : [ SUB,["var", "symb", "symb"]],
    "MUL"           : [ MUL,["var", "symb", "symb"]],
    "IDIV"          : [ IDIV,["var", "symb", "symb"]],
    "LT"            : [ LT,["var", "symb", "symb"]],
    "GT"            : [ GT,["var", "symb", "symb"]],
    "EQ"            : [ EQ,["var", "symb", "symb"]],
    "AND"           : [ AND,["var", "symb", "symb"]],
    "OR"            : [ OR,["var", "symb", "symb"]],
    "NOT"           : [ NOT,["var", "symb"]],
    "INT2CHAR"      : [ INT2CHAR,["var", "symb"]],
    "STRI2INT"      : [ STRI2INT,["var", "symb", "symb"]],
    "READ"          : [ READ,["var", "type"]],
    "WRITE"         : [ WRITE,["symb"]],
    "CONCAT"        : [ CONCAT,["var", "symb", "symb"]],
    "STRLEN"        : [ STRLEN,["var", "symb"]],
    "GETCHAR"       : [ GETCHAR,["var", "symb", "symb"]],
    "SETCHAR"       : [ SETCHAR,["var", "symb", "symb"]],
    "TYPE"          : [ TYPE,["var", "symb"]],
    "LABEL"         : [ LABEL,["label"]],
    "JUMP"          : [ JUMP,["label"]],
    "JUMPIFEQ"      : [ JUMPIFEQ,["label", "symb", "symb"]],
    "JUMPIFNEQ"     : [ JUMPIFNEQ,["label", "symb", "symb"]],
    "DPRINT"        : [ DPRINT,["symb"]],
    "BREAK"         : [ BREAK, []]
}

escapes = {
    "\\000" : chr(0), # null
    "\\001" : chr(1), # start of heading
    "\\002" : chr(2), # start of text
    "\\003" : chr(3), # end of text
    "\\004" : chr(4), # end of transmission
    "\\005" : chr(5), # enquiry
    "\\006" : chr(6), # acknowledge
    "\\007" : chr(7), # bell
    "\\008" : chr(8), # backspace
    "\\009" : chr(9), # horizontal tab
    "\\010" : chr(10), # new line
    "\\011" : chr(11), # vertical tab
    "\\012" : chr(12), # NP form feed, new page
    "\\013" : chr(13), # carriage return
    "\\014" : chr(14), # shift out
    "\\015" : chr(15), # shift in
    "\\016" : chr(16), # data link escape
    "\\017" : chr(17), # device control 1
    "\\018" : chr(18), # device control 2
    "\\019" : chr(19), # device control 3
    "\\020" : chr(20), # device control 4
    "\\021" : chr(21), # negative acknowledge
    "\\022" : chr(22), # synchronous idle
    "\\023" : chr(23), # end of trans. block
    "\\024" : chr(24), # cancel
    "\\025" : chr(25), # end of medium
    "\\026" : chr(26), # substitute
    "\\027" : chr(27), # escape
    "\\028" : chr(28), # file separator
    "\\029" : chr(29), # group separator
    "\\030" : chr(30), # record separator
    "\\031" : chr(31), # unit separator
    "\\032" : chr(32), # space
    "\\035" : chr(35), # mrizka #
    "\\092" : chr(92) # backslash \
}


# argumenty programu
inputXml  = None
statsOpt  = False
statsFile = None
varsOpt   = False
instOpt   = False
helpOpt   = False

#nacteni parametru programu
try:
    options, values = getopt.getopt(sys.argv[1:], "", ["source=", "help", "stats=", "vars", "insts"])
except Exception:
    sys.stderr.write("Chybejici hodnota u parametru\n")
    exit(10)

for opt, arg in options:
    if opt == "--source":
        inputXml = arg
    elif opt == "--help":
        #printHelp()
        helpOpt = True
    elif opt == "--stats":
        statsOpt = True
        statsFile = arg
    elif opt == "--vars":
        varsOpt = True
    elif opt == "--insts":
        instOpt = True

#kontrola kombinaci parametruuu
if helpOpt:
    if len(options) == 1:
        printHelp()
        exit(0)
    else:
        exit(10)

if varsOpt or instOpt:
    if not statsOpt:
        sys.stderr.write("Nepovolena kombinace argumentu programu\n")
        exit(10)

if inputXml is None:
    sys.stderr.write("Nebyl zadan vstupni soubor\n")
    exit(11)



try:
    handle = open(inputXml, "r")
except IOError:
    sys.stderr.write("Soubor s xml se nepovedlo otevrit\n")
    exit(11)

# nacteni zdrojoveho XML ze souboru
xmlSource = "";
for line in handle:
    xmlSource = xmlSource+line

handle.close()

# nacteni korene xml stromu
try:
    root = ET.fromstring(xmlSource)
except Exception:
    sys.stderr.write("Spatny format vstupniho XML!!!\n")
    exit(31)

# inicializace promennych
PC = 0
callCounter = 0 #pocet provedenych instrukci
callStack = []
dataStack = []
program   = []
labels    = {} #labelName = indexNaPasce
programName = ""
programDescription = ""

# ramce
globalFrame = Frame()
localFrameContainer = LocalFrameContainer()
tmpFrame = None


# Vytvoreni struktury s vyslednym kodem
line = 0 # aktualne nacitany radek vstupniho programu - k inicializaci labelu
expectedOpcode = 0 # kontrola, jestli ve vstupnim XML neni prohazene poradi isntrukci


if "name" in root.attrib:
    programName = root.attrib["name"]

if "description" in root.attrib:
    programDescription = root.attrib["description"]

for instruction in root:
    newInstruction = Instruction()

    #TODO zde kontrola poctu argumentu (given vs expected) ????? ZDE NEBO AZ PRI INTERPRETACI???
    #print("Instukce: ", instruction.attrib["opcode"])

    # Kontrola spravneho poradi order
    '''
    if instruction.attrib["order"] != expectedOpcode:
        sys.stderr.write("Vyskytlo se neocekavane cislo instrukce (ORDER).\n")
        exit(32) # TODO JAKY navratovy kod???
    expectedOpcode += 1
    '''

    for argument in instruction:
        # konstanta
        if argument.attrib["type"] in ["int", "string", "bool"]:
            value = ""
            if argument.text is None:
                value = argument.attrib["type"] + "@"
            else:
                value = argument.attrib["type"] + "@" + argument.text if argument.text else ""

            #TODO tady kontrola??
            #print("  ", value , " - ", checkFormat(value, argument.attrib["type"]))
            if checkFormat(value, argument.attrib["type"]) != argument.attrib["type"]:
                sys.stderr.write("Chyba behem prvotni analyzy-int, string, bool\n")
                exit(32)

            newInstruction.appendArg(value)

        # label
        elif argument.attrib["type"] in ["label"]:
            #TODO tady kontrola??
            #print("  ",argument.text , " - ", checkFormat(argument.text, argument.attrib["type"]))
            if checkFormat(argument.text, argument.attrib["type"]) != argument.attrib["type"]:
                sys.stderr.write("Chyba behem prvotni analyzy- label\n")
                exit(32)

            newInstruction.appendArg(argument.text)

            # inicializace LABELu
            if instruction.attrib["opcode"] == "LABEL":
                if argument.text not in labels:
                    labels[argument.text] = line
                else:
                    sys.stderr.write("chyba: Tento Label jiz byl definovan!\n")
                    exit(55)

        # variable
        else:
            #TODO tady kontrola??
            #print("  ",argument.text , " - ", checkFormat(argument.text, argument.attrib["type"]))
            if checkFormat(argument.text, argument.attrib["type"]) != argument.attrib["type"]:
                exit(32)

            newInstruction.appendArg(argument.text)

    newInstruction.setOpcode(instruction.attrib["opcode"])
    program.append(newInstruction)
    line+=1



#EXECUTING of given program
#print("POCET RADKU INSTRUKCI: ", len(program))
while(PC < len(program)):
    #print ("PC: ", PC, "   | Instrukce: ", program[PC].getOpcode())
    opCode = program[PC].getOpcode()

    # parametry, ktere predam nasledne instrukci (funkci reprezentujici instrukci)
    currentParams = program[PC].getArgs()

    #TODO bude to vubec tady???
    if opCode in instrukctionCall:
        #kontrola poctu a nasledne typu operandu pro aktualni instrukci
        numberOfGivenParam = len(currentParams)
        numberOfRequiredParam = len(instrukctionCall[opCode][1])
        if numberOfRequiredParam != numberOfGivenParam:
            sys.stderr.write("Chyba: Instrukce ("+opCode+") ocekava presne "+ str(numberOfRequiredParam)+" operand(u). Dano " + str(numberOfGivenParam) + "\n")
            exit(32) #TODO

        #TODO pokud se to ma vse kontrolovat --ZA BEHU-- tak bych to mohl kontrolovat tady.
        # kontrolor(instrukctionCall[opCode][1], currentParams) //zjisti pro danou isntrukci predane typy a porovna je
        # tzn v sobe bude volat jest neco co podle formatu zjisti prislusny typ (var, symb, type, label - jak v php)
        # --- checkFormat(operand)
        # NEBO pri analyze kodu precteneho z xml
        #for i in numberOfOperands:
        #    if currentParams[i] !=

        #v1 - nutno takhle, kvuli potrebnym kontrolams
        instrukctionCall[opCode][0](*currentParams)
    else:
        sys.stderr.write("Chyba: Volana instrukce ("+opCode+") neexistuje.\n")
        exit(32)

    PC += 1
    callCounter += 1
    continue
# KONEC provadeni programu


#zapis do stats.txt - TODO podle poradi prepinacu!!!
if statsOpt:
    handle = open(statsFile, "w")
    #handle.write("Statistiky:\n")
    if instOpt:
        #handle.write("Pocet vykonanych instrukci: " + str(callCounter) + "\n")
        handle.write(str(callCounter)+"\n")
    if varsOpt:
        #handle.write("Pocet inicializovanych promennych: XXXX\n")
        handle.write("666\n")

    handle.close()

exit(0)
