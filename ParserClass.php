<?php

require_once("InstructionClass.php");
require_once("ArgumentClass.php");

/*
 * Autor: Jiri Peska
 * Login: xpeska05
 */

/*
 * Trida, ktera parsuje vstupni program v ippcode18 a provadi kontrolu formatu operandu a instrukci.
 * Ke kontrole vyuziva regularni vyrazy, pole instrukci, ktere obsahuje ocekavane operandy pro kazdou instrukci a funkce pro prevod vysledne 
 * struktury do XML.
 * Cyklus: radek po radku nacita vstupni program, radky parsuje, kontroluje validitu naparsovanych dat a vytvari objekty pro instrukce a jeji parametry.
 * Pokud vse probehne v poradku, tak se vysledna struktura preda funkci, ktera vytvori XML.
 */
class Parser
{
	private $_source;
	private $_programName;
	private $_sourceCode = array();
	private $_instructionArray = array(); // pole objektu Instrukce
	private $_numberOfComments = 0;

	private $_numberOfInstructions = 0;

	private $_validTypes = array("int", "bool", "string", "label", "type", "var", "GF", "LF", "TF");
  	private $_basicTypes = array("int", "bool", "string", "float");

	private $_validInstructions = array(
		"MOVE" => array("var", "symb"),
		"CREATEFRAME" => array(),
		"PUSHFRAME" => array(),
		"POPFRAME" => array(),
		"DEFVAR" => array("var"),
		"CALL" => array("label"),
		"RETURN" => array(),
		"PUSHS" => array("symb"),
		"POPS" => array("var"),
		"ADD" => array("var", "symb", "symb"),
		"SUB" => array("var", "symb", "symb"),
		"MUL" => array("var", "symb", "symb"),
		"IDIV" => array("var", "symb", "symb"),
		"LT" => array("var", "symb", "symb"),
		"GT" => array("var", "symb", "symb"),
		"EQ" => array("var", "symb", "symb"),
		"AND" => array("var", "symb", "symb"),
		"OR" => array("var", "symb", "symb"),
		"NOT" => array("var", "symb"),
		"INT2CHAR" => array("var", "symb"),
		"STRI2INT" => array("var", "symb", "symb"),
		"READ" => array("var", "type"),
		"WRITE" => array("symb"),
		"CONCAT" => array("var", "symb", "symb"),
		"STRLEN" => array("var", "symb"),
		"GETCHAR" => array("var", "symb", "symb"),
		"SETCHAR" => array("var", "symb", "symb"),
		"TYPE" => array("var", "symb"),
		"LABEL" => array("label"),
		"JUMP" => array("label"),
		"JUMPIFEQ" => array("label", "symb", "symb"),
		"JUMPIFNEQ" => array("label", "symb", "symb"),
		"DPRINT" => array("symb"),
		"BREAK" => array()
	);

	public function __construct()
	{
		//fwrite(STDERR, "Parser vytvoren\n");
		$this->_source = STDIN;
	}

	/*
	 * Nahraje do bufferu radek po radku vstupni zdrojovy kod
	 */
	private function loadSource()
	{
		while($line = fgets($this->_source))
		{
			$this->_sourceCode[] = $line;
		}
	}

	// hlavni funkce, ktera parsuje ten program
	public function parseSourceCode()
	{
			// prvni radek
			$firstLine = $this->getLineOfCode();

			$this->_programName = trim($firstLine, " \x00..\x1F");
			$this->_programName = $this->trimLine($this->_programName);

			$programName = strtolower($this->_programName);
			if($programName != ".ippcode18")
			{
				fwrite(STDERR, "Hodnota \"" . $programName . "\" neni validni nazev programu. Soubor je mozna prazdny.\n");
				exit(21);
			}

			$this->_programName = "IPPcode18";


			//nacteme do pole jednotlive radky kodu
			$this->loadSource();

			foreach($this->_sourceCode as $line)
			{
					$this->parseLineOfCode($line);
			}
	}

	public function printStatistics($file, $order)
	{
			//if (file_exists($file))
			//{
				try {
					$handle = fopen($file, "w");
					if ( ! $handle)
					{
						throw new Exception("Otevreni souboru pro zapis se nezdarilo.");
					}
				}
				catch(Exception $e)
				{
					fwrite(STDERR, "Nepovedlo se otevrit soubor pro zapsani statistik.\n");
					exit(12);
				}

				//fwrite($handle, "parse.php Statistiky:\n");
				if(! empty($order))
				{
					ksort($order);
					foreach($order as $key)
					{
						if($key == "comments")
						{
							//fwrite($handle, "  Pocet komentaru: ".$this->_numberOfComments."\n");
							fwrite($handle, $this->_numberOfComments."\n");
						}
						elseif($key == "loc")
						{
							//fwrite($handle, "  Pocet instrukci: ".$this->_numberOfInstructions."\n");
							fwrite($handle, $this->_numberOfInstructions."\n");
						}
					}
				}
				fclose($handle);
			//}
	}

	private function getLineOfCode()
	{
			return fgets($this->_source);
	}

	private function parseLineOfCode($line)
	{
			// nacitame znaky z puvodniho retezce a kdyz narazi na komentar, tak se zapocita a cyklus skonci
			$newLine = $this->trimLine($line);
			if($newLine == NULL)
			{
					return;
			}

			// rozdelime radek s triadresnym kodem na casti podle space
			$rozdelene = explode(" ", $newLine);


			// zbavime se prazdnych znaku u instrukci, operandu atd...
			for($i = 0; $i < count($rozdelene); $i++)
			{
				$rozdelene[$i] = trim($rozdelene[$i], " \t\n\r\0\x0B");
			}

			// odstraneni prazdnych hodnot
			$rozdelene = array_filter($rozdelene, 'strlen');

			//reindexace
			$rozdelene = array_values($rozdelene);


			$rozdelene[0] = strtoupper($rozdelene[0]);

			// kontrola existence instrukce
			if(array_key_exists($rozdelene[0], $this->_validInstructions) == false)
			{
					fwrite(STDERR, "Instrukce " . $rozdelene[0] . " neexistuje.\n");
					exit(21);
			}

			//kontrola, zda-li za instrukci nasleduje spravny pocet parametru
			if((count($rozdelene)-1) != count($this->_validInstructions[$rozdelene[0]]))
			{
					fwrite(STDERR, "Instrukci \"" . $rozdelene[0] . "\" nebyl predan spravny pocet operandu (".(count($rozdelene)-1).", ocekavany ".count($this->_validInstructions[$rozdelene[0]]).").\n");
					exit(21);
			}

			// instrukce
			$this->_numberOfInstructions++;
			$novaInstrukce = new Instruction();
			$novaInstrukce->setOpcode($rozdelene[0]);

			//zpracujeme parametry isntrukce
			for($idxParam = 1; $idxParam < count($rozdelene); $idxParam++)
			{
					// zpracovani argumentu
					$newParam = new Argument;

					$parsedParam = explode("@", $rozdelene[$idxParam], 2);

					// kontrola datoveho typu a hodnoty
					if(count($parsedParam) == 1)
					{
							# TODO SOLVED !!! Nebude tady problem, pokud bude label jmenem int, string, bool? mozna bych se mel podivat,
							#  jestli na danem miste je ocekavan type nebo label a podle toho se rozhodnout.
							if(in_array($parsedParam[0], array("int", "string", "bool")) && $novaInstrukce->getOpcode() != "LABEL")
							{
									#$newParam->setArgType($parsedParam[0]);
									$newParam->setArgType("type");
									$newParam->setArgValue($parsedParam[0]);
							}
							else
							{
									$newParam->setArgType("label");

									// kontrola hodnoty labelu
									if( ! $this->checkFormat($parsedParam[0]))
									{
											fwrite(STDERR, "Label \"" . $parsedParam[0] . "\" nevyhovuje regularnimu vyrazu.\n");
											exit(21);
									}

									$newParam->setArgValue($parsedParam[0]);
							}
					}
					else if(in_array($parsedParam[0], array("GF", "LF", "TF")))
					{
							$newParam->setArgType("var");

							// kontrola hodnoty(nazvu) promenne
							if( ! $this->checkFormat($parsedParam[1]))
							{
									fwrite(STDERR, "Promenna \"" . $parsedParam[1] . "\" nevyhovuje regularnimu vyrazu.\n");
									exit(21);
							}

							$newParam->setArgValue($parsedParam[0]."@".$parsedParam[1]);
					}
					else
					{
							// kontrola existence datoveho typu
							if(in_array($parsedParam[0], $this->_validTypes))
							{
									$newParam->setArgType($parsedParam[0]);
							}

							// kontrola hodnoty bool
							if($parsedParam[0] == "bool")
							{
									//if( ! in_array(strtolower($parsedParam[1]), array("true", "false")))
									if( ! in_array($parsedParam[1], array("true", "false")))
									{
										  fwrite(STDERR, "Hodnota typu bool \"" . $parsedParam[1] . "\" neobsahuje povolenou hodnotu(true, false).\n");
										  exit(21);
									}
							}

							// kontrola hodnoty string
							if($parsedParam[0] == "string")
							{
									if( ! preg_match("/^(\\\[0-9]{3}|[^\s #\\\])*$/", $parsedParam[1]))
									{
										  fwrite(STDERR, "Hodnota typu string \"" . $parsedParam[1] . "\" neobsahuje povolenou hodnotu(true, false).\n");
										  exit(21);
									}
							}

							// kontrola hodnoty int
							if($parsedParam[0] == "int")
							{

									if( ! preg_match("/^[+-]?[0-9]+$/", $parsedParam[1]))
									{
										  fwrite(STDERR, "Hodnota typu int \"" . $parsedParam[1] . "\" neobsahuje povolenou hodnot.\n");
										  exit(21);
									}


							}

							$newParam->setArgValue($parsedParam[1]);
					}


					// zjistime typ n-teho parametru podle instrukce (symb, label, var, type) a porovname s typem aktualniho operandu
					$typAtributu = $this->_validInstructions[$novaInstrukce->getOpcode()];
					if( ! empty($typAtributu))
					{
							$typAtributu = $typAtributu[$idxParam-1];

							if( ! $this->checkOperandType($typAtributu, $newParam->getArgType()))
							{
								  fwrite(STDERR, "Typ aktualniho operandu nesouhlasi s ocekavanym typem operandu na dane pozici.\n");
								  exit(21);
							}
					}

					// vlozime do pole k aktualni instrukci
					$novaInstrukce->insertNewArgument($newParam);
			}

			// vlozime kompletni objekt instrukce do pole
			$this->_instructionArray[] = $novaInstrukce;
    }

    /*
     * Funkce odstrani z retezce $line komentare zacinajici # a escape sekvence
     * Vraci novy retezec bez komentaru a bez escape sekvenci a white spaces
     */
    private function trimLine($line)
    {
            $newLine = "";
            for($i = 0; $i < strlen($line); $i++)
            {
                if($line[$i] == "#")
                {
                    $this->_numberOfComments++;
                    break;
                }

                $newLine .= $line[$i];
            }

            // pokud je retezec prazdny, znamena to, ze se jednalo o celoradkovy komentar
            if(empty($newLine))
            {
                return NULL;
            }

            // odstranime z retezce escape sekvence a bile znaky
            $newLine = trim($newLine, " \x00..\x1F");

            return $newLine;
    }

    /*
     * Zkontroluje, zda-li $var vyhovuje predepsanemu formatu
     */
    public function checkFormat($var)
    {
		//return preg_match("/^[a-zA-Z_\-$&%*][a-zA-Z0-9_\-$&%*]*$/", $var);
		return preg_match("/^[a-zA-Z_\\-$&%*][a-zA-Z0-9_\\-$&%*]*$/", $var);
    }

    /*
     * Zjisti, jestli je na danem miste parametru dovoleny operand
     */
    public function checkOperandType($operand, $actualOperand)
    {
        switch($operand)
        {
            case "var":
                if($actualOperand == "var")
                {
                    return true;
                }
                return false;
                break;

            case "symb":
                if(in_array($actualOperand, $this->_basicTypes) || $actualOperand == "var")
                {
                    return true;
                }
                return false;
                break;

            case "label":
                if($actualOperand == "label")
                {
                    return true;
                }
                return false;
                break;

			case "type":
					if(in_array($actualOperand, $this->_basicTypes) || $actualOperand == "type")
					{
							return true;
					}
					return false;
					break;
        }
    }

	/*
	* Tiskne instrukce a jejich obsah (hodnoty argumentuuu...)
	*/
	public function printAll()
	{
			echo "\n\n";
			echo "_____________________________________________________________\n";

			echo "Instrukce v poli: ". count($this->_instructionArray) . "\n\n";

			foreach($this->_instructionArray as $instruction)
			{
					echo "Instrukce: " . $instruction->getOpcode() . "\n";
					echo "Order: ".$instruction->getOrder() . "\n";
					foreach($instruction->getArgArray() as $arg)
					{
							echo $arg->getArgType() . " -> " . $arg->getArgValue() . "\n";
					}
					echo "\n";
			}

			echo "_____________________________________________________________\n";
	}

    public function toXML()
    {
        $writer = new XMLWriter();
        $writer->openURI("php://stdout");
        $writer->startDocument('1.0', 'UTF-8');
        $writer->setIndent(true);
        $writer->setIndentString("      ");

        $writer->startElement('program');
        $writer->writeAttribute('language', $this->_programName);

        foreach($this->_instructionArray as $instruction)
        {
            $writer->startElement('instruction');
            $writer->writeAttribute('order', $instruction->getOrder());
            $writer->writeAttribute('opcode', $instruction->getOpcode());

            $argCnt = 1;
            foreach($instruction->getArgArray() as $arg)
            {
                    $writer->startElement('arg'.$argCnt);
                    $writer->writeAttribute('type', $arg->getArgType());
                    $writer->text($arg->getArgValue());
                    $writer->endElement();

                    $argCnt++;
            }

            $writer->endElement();
        }

        $writer->endElement();
    }
}
