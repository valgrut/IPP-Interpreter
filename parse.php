<?php

/*
 * parse.php
 * IPP 2018/19
 * Autor: Jiri Peska
 * Login: xpeska05
 *
 */

	require_once("ParserClass.php");

$param_stats = false;
$param_stats_output = NULL;
$param_loc = false;
$param_comments = false;

#poradi vlozenych prepinacu
$paramOrder = array();

//pole moznych parametru
$param_long = array(
	"help",
	"stats:",
	"loc",
	"comments",
);

//pokud jsou nejake parametry, ulozime do pole
if($argc > 1)
{
	$params = getopt(NULL, $param_long);
	$param_count = count($params);

	//pokud je zde help, tak nesmi byt nic jineho
	if(array_key_exists("help", $params) && ($param_count > 1 || $argc > 2) )
	{
		fwrite(STDERR, "Chyba: Nepovolena kombinace parametru programu!\n");
		exit(10);
	}

	if(array_key_exists("help", $params))
	{
	  echo "usage:\n";
		echo "    parse.php [--help] [--stats=file [--loc] [--comments]]\n\n";
		echo "  --help          Vypise napovedu a ukonci program.\n";
		echo "  --stats = file  Slouzi k zadani vystupniho souboru pro statistiky.\n";
		echo "  --loc           Do souboru pro statistiky se vypise pocet instrukci nacteneho programu.\n";
		echo "  --comments      Do souboru pro statistiky se vypise pocet komentaru v nactenem programu.\n";
		/*
		echo "parse.php\n\n";
		echo "NAME\n";
		echo "    parse.php - Ze zdrojoveho kodu na standartnim vstupu vygeneruje na standartni vystup XML.\n\n";
		echo "SYNOPSIS\n";
		echo "    parse.php < source.ippcode18 [--help] [--stats=file [--loc] [--comments]]\n\n";
		echo "DESCRIPTION\n";
		echo "    V zakladu program zpracuje vstupni zdrojovy kod a na standartni vystup vygeneruje xml.\n\n";
		echo "OPTIONS\n";
		echo "  --help\n";
		echo "      Vypise napovedu a ukonci program.\n";
		echo "  --stats = file\n";
		echo "      Slouzi k zadani vystupniho souboru pro statistiky.\n";
		echo "  --loc\n";
		echo "      Do souboru pro statistiky se vypise pocet instrukci nacteneho programu.\n";
		echo "  --comments\n";
		echo "      Do souboru pro statistiky se vypise pocet komentaru v nactenem programu.\n";
		*/
    exit(0);
	}

	//neexitujici nebo neuplny nebo duplicitni parametr
	if($argc > 1 && $param_count != $argc-1)
	{
		fwrite(STDERR, "Chyba: Neexistujici nebo neuplny parametr\n");
    exit(10);
	}

	// stats, loc, comment
	if(array_key_exists("stats", $params))
	{
		$param_stats = true;
		$param_stats_output = $params["stats"];
	}
	if(array_key_exists("loc", $params))
	{
		$param_loc = true;
		$paramOrder[array_search("loc",array_keys($params))] = "loc";
	}
	if(array_key_exists("comments", $params))
	{
		$param_comments = true;
		$paramOrder[array_search("comments",array_keys($params))] = "comments";
	}

	//kontrola, jestli nenastane nejaka nepovolena kombinace parametru
	if($param_stats == false)
	{
		if($param_loc || $param_comments)
		{
			fwrite(STDERR, "Chyba: Loc nebo Comments je pritomny, ale neni pritomny stats parametr\n");
			exit(10);
		}
	}
}

/*
TODO
Mozna udelat tridu ProgramParameter
ktera se bude starat o parsovani parametru, a pak ji jednoduse predam v konstruktoru tride ParseClass
*/

$parser = new Parser();
$parser->parseSourceCode();
if($param_stats) {$parser->printStatistics($param_stats_output, $paramOrder);}
$parser->toXML();


?>
