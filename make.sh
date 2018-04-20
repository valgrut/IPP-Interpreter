#!/bin/bash

# Pozn.: Script hleda primo v adresari programs/

ERROR_DIRECTORY="." #.Errors
PROGRAM_DIRECTORY=programs
POSTFIX=ippcode

help()
{
    echo "Popis:"
    echo "Script vezme soubor <file> a spusti s nim parse.php,"
    echo "jehoz vystup presmeruje do <file>.xml a tento <file>.xml pouzije jako vstupni soubor"
    echo "pro script interpret.py, jehoz vystup vypise na stdout"
    echo ""
    echo "Usage:"
    echo "  ./make.sh <sourceFile> (BEZ .ippcode, protoze se mi to nechce parsovat)"
    echo "  ./make.sh <sourceFile> [parse | inter] (BEZ .ippcode, protoze se mi to nechce parsovat)"
    echo ""
    echo "Programy dostupne k execnuti:"
    ls -o ${PROGRAM_DIRECTORY}/*.${POSTFIX}
    exit 1
}

# @param1: source.ippcode
callParse()
{
	echo ">>Spoustim parse.php"
	#php parse.php < ${PROGRAM_DIRECTORY}/"$1".${POSTFIX} 1>${PROGRAM_DIRECTORY}/"$1".xml 2>${ERROR_DIRECTORY}/parseErrors.txt
	php5.6 -d open_basedir="." -f parse.php < ${PROGRAM_DIRECTORY}/"$1".${POSTFIX} > ${PROGRAM_DIRECTORY}/"$1".xml
	RET=$?
	if [ ${RET} == 0 ]; then
	    echo ">>Execution of parser SUCCEEDED"
	    rm parseErrors.txt
	else
	    echo ">>parser ukoncen s chybou: ${RET}"
	    if [ ! -d "${ERROR_DIRECTORY}" ]; then
		mkdir ${ERROR_DIRECTORY}
	    fi
	    if [ -f "${ERROR_DIRECTORY}/parseErrors.txt" ]; then
		echo ">>Vypis parseErrors.txt:"
		cat ${ERROR_DIRECTORY}/parseErrors.txt
		echo ">>konec parseErrors.txt"
		rm parseErrors.txt
	    fi
	    exit ${RET}
	fi
	echo ">>Vytvoren $1.xml"

	return
}

# @param1: source.ippcode
callInterpreter()
{
	echo ">>Spoustim interpret.py"
	python3.6 interpret.py --source=${PROGRAM_DIRECTORY}/$1.xml 2>${ERROR_DIRECTORY}/interpreterErrors.txt
	RET=$?
	if [ ${RET} == 0 ]; then
	    echo ">>Execution of interpreter SUCCEEDED"
	    rm interpreterErrors.txt
	    exit 0
	else
	    if [ ! -d "${ERROR_DIRECTORY}" ]; then
		mkdir ${ERROR_DIRECTORY}
	    fi
	    echo ">>Program ukoncen s chybou: ${RET}"
	    if [ -f "${ERROR_DIRECTORY}/interpreterErrors.txt" ]; then
		echo ">>Vypis interpreterErrors.txt"
		cat ${ERROR_DIRECTORY}/interpreterErrors.txt
		echo ">>konec interpreterErrors.txt"
		rm interpreterErrors.txt
	    fi
	    exit ${RET}
	fi

	return
}

# --------------------------MAIN-----------------------------------------------------------------------------------------
if [ $# == 0 ]; then
	help
	exit 0
elif [ $# == 1 ]; then
    if [ ! -f "${PROGRAM_DIRECTORY}/$1.ippcode" ]; then
        printf ">>Zadany soubor \"%s\" neexistuje\n" $1
        exit 666
    fi
    sourcecode=$1
    callParse ${sourcecode}
    echo ""
    callInterpreter ${sourcecode}
    exit 0

elif [ $# == 2 ]; then
    if [ ! -f "${PROGRAM_DIRECTORY}/$1.ippcode" ]; then
        printf ">>Zadany soubor \"%s\" neexistuje\n" $1
        exit 666
    fi
	if [ $2 == "parse" ]; then
		callParse $1
		exit 0
	elif [ $2 == "inter" ]; then
		callInterpreter $1
		exit 0
	else
		exit 0
	fi
else
	help
fi

exit 0
