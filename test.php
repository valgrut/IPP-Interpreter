<?php


/* ----------------------------------------------------------------------------*/
/*  Parsovani argumentu  */
$param_flags = array("DETAILS" => 0);

$param_directory_file = ".";
$param_directory = false;
$param_recursive = false;
$param_parse_script = false;
$param_parse_script_file = "parse.php";
$param_int_script = false;
$param_int_script_file = "interpret.py";

$testResults = array();

//pole moznych parametru
$param_long = array(
	"help",
	"directory:",
    "recursive",
	"parse-script:",
	"int-script:",
);

if($argc > 1)
{
	$params = getopt(NULL, $param_long);
	$param_count = count($params);

	if(array_key_exists("help", $params) && ($param_count > 1 || $argc > 2) )
	{
		fwrite(STDERR, "Chyba: Nepovolena kombinace parametru programu!\n");
		exit(10);
	}

	if(array_key_exists("help", $params))
	{
		echo "usage:\n";
		echo "    --help\n";
		echo "    --directory=file    Testy bude hledat v tomto adresari\n";
		echo "    --recursive         Testy bude hledat rekurzivne i v podadresarich\n";
		echo "    --parse-script=file Jiny nazev scriptu parse\n";
        echo "    --int-script=file   Jiny nazev scriptu interpreter\n";
		return 0;
	}

	//neexitujici nebo neuplny nebo duplicitni parametr
	if($argc > 1 && $param_count != $argc-1)
	{
		fwrite(STDERR, "Chyba: Neexistujici nebo neuplny parametr\n");
		exit(10);
	}

	// stats, loc, comment
	if(array_key_exists("directory", $params))
	{
		$param_directory = True;
		$param_directory_file = $params["directory"];
	}
	if(array_key_exists("recursive", $params))
	{
		$param_recursive = True;
	}
	if(array_key_exists("parse-script", $params))
	{
		$param_parse_script = True;
		$param_parse_script_file = $params["parse-script"];
        if(! file_exists($param_parse_script_file))
        {
            fwrite(STDERR, "Chyba: Soubor $param_parse_script_file neexistuje.\n");
    		exit(11);
        }
	}
	if(array_key_exists("int-script", $params))
	{
		$param_int_script = true;
		$param_int_script_file = $params["int-script"];
        if(! file_exists($param_int_script_file))
        {
            fwrite(STDERR, "Chyba: Soubor $param_int_script_file neexistuje.\n");
            exit(11);
        }
	}
}

# 4 soubory ve stejnem adresari: .src   .in   .out   .rc
# .src  - zdrojak v IPPcode18
# .in   - vstup
# .out  - vystup a ocekavany navratovy kod interpretace a analyzy
# .rc   - referencni vystup a ocekavany prvni navratovy kod interpretace a analyzy

if($param_recursive)
{
    //echo "path to test file: ".$param_directory_file."\n";
	$dir  = new RecursiveDirectoryIterator($param_directory_file, RecursiveDirectoryIterator::SKIP_DOTS);
	$files = new RecursiveIteratorIterator($dir, RecursiveIteratorIterator::SELF_FIRST);
    $cwd = NULL;
	foreach($files as $test)
	{
        if(is_dir($test))
        {
            $cwd = $test;
            //echo "Dir: $test\n\n";
        }
        if(is_file($test)) // Kdyz najdeme soubor a ne slozku.
        {
            // hledame .src soubor, ktery predame parseru a interpretu
            if(! preg_match("/.src$/", $test))
                continue;

            $xml_output = null;
            $parse_exit_value = "";
            $interpret_result = "";

            $testname = basename($test, '.src');

            // pokud neexistuje .out, .in nebo .rc, vytvori se
            checkExistence($cwd, $testname);

            /*  -------------------- Volani parseru  --------------------  */
            exec("php5.6 -d open_basedir="." -f $param_parse_script_file < $test 2>/dev/null", $xml_output, $parse_exit_value);

            /* otevru vystupni soubor pro zapis*/
            $outputFile = fopen("$cwd/$testname.out", "w");

            # fail parseru (nepovede se pretypovat)
            if((int)$parse_exit_value != 0)
            {
                // konečná pro aktuálně provedený test - konec.
                //echo "Parse TERMINATED with exit code: $parse_exit_value\n";
                fwrite($outputFile, $parse_exit_value);

                diffTests($cwd, $testname, $testResults);

                fclose($outputFile);
                continue;
            }

            /*  Parse SUCCEEDED  */
            // zapisu xml do docasneho souboru, ktery pak predam interpretu k provedeni a pak ho smazu
            $xmlFile = fopen("$cwd/$testname.xml", "w");
            writeArray($xmlFile, $xml_output);
            fclose($xmlFile);


            /*   Volani interpretu    */
            exec("python3.6 $param_int_script_file --source=$cwd/$testname.xml < $cwd/$testname.in 2>/dev/null", $interpret_result, $interpret_exit_value);
            shell_exec("rm $cwd/$testname.xml");

            /*  zapiseme do vystupniho souboru navratovou hodnotu interpretu a vysledek  */
            if((int)$interpret_exit_value != 0)
            {
                fwrite($outputFile, $interpret_exit_value);
                diffTests($cwd, $testname, $testResults);
                fclose($outputFile);
                continue;
            }

            fwrite($outputFile, $interpret_exit_value."\n");
            writeArray($outputFile, $interpret_result);
            fclose($outputFile);

            /*  porovnani vystupu s referencnim vystupem   */
            diffTests($cwd, $testname, $testResults);
        }
	}
}
else
{
    //echo "Nerekurzivni pruchod.\n";
    $dir = scandir($param_directory_file);

    foreach($dir as $test)
    {

        if($test == "." || $test == "..")
    	{
            continue;
    	}

        if(is_file("$param_directory_file/$test")) // Kdyz najdeme soubor a ne slozku.
        {
            // hledame .src soubor, ktery predame parseru a interpretu
            if(! preg_match("/.src$/", $test))
                continue;

            // deinicializace promennych
            $xml_output = null;
            $parse_exit_value = "";
            $interpret_result = "";

            $testname = basename($test, '.src');
            //echo "Nyni se provadi TEST s nazvem: ".$testname."\n";

            // pokud neexistuje .out, .in nebo .rc, vytvori se
            checkExistence($param_directory_file, $testname);

            $fulltestname = "$param_directory_file/$testname";

            /*  -------------------- Volani parseru  --------------------  */
            exec("php5.6 -d open_basedir="." -f $param_parse_script_file < $fulltestname.src 2>/dev/null", $xml_output, $parse_exit_value);

            /* otevru vystupni soubor pro zapis*/
            $outputFile = fopen("$fulltestname.out", "w");

            # fail parseru (nepovede se pretypovat)
            if((int)$parse_exit_value != 0)
            {
                // konečná pro aktuálně provedený test - konec.
                //echo "Parse TERMINATED with exit code: $parse_exit_value\n";
                fwrite($outputFile, $parse_exit_value);

                diffTests($param_directory_file, $testname, $testResults);
                fclose($outputFile);
                continue;
            }


            /*  Parse SUCCEEDED  */
            // zapisu xml do docasneho souboru, ktery pak predam interpretu k provedeni a pak ho smazu
            $xmlFile = fopen("$fulltestname.xml", "w");
            writeArray($xmlFile, $xml_output);
            fclose($xmlFile);


            /*   Volani interpretu  */
            exec("python3.6 $param_int_script_file --source=$fulltestname.xml < $fulltestname.in 2>/dev/null", $interpret_result, $interpret_exit_value);
            shell_exec("rm $fulltestname.xml");

            /*  zapiseme do vystupniho souboru navratovou hodnotu interpretu a vysledek  */
            if((int)$interpret_exit_value != 0)
            {
                fwrite($outputFile, $interpret_exit_value);
                diffTests($param_directory_file, $testname, $testResults);
                fclose($outputFile);
                continue;
            }

            fwrite($outputFile, $interpret_exit_value."\n");
            writeArray($outputFile, $interpret_result);
            fclose($outputFile);

            /*  porovnani vystupu s referencnim vystupem   */
            diffTests($param_directory_file, $testname, $testResults);
        }
    }
}

generateHTML($testResults);

return 0;
// konec scriptu


/* ---------------------------------------------------------------------------------------------------------------------------------------*/
function generateHTML($testResults)
{
    // TODO delete this
    /*
    echo "Final results:\n";
    foreach($testResults as $key => $result)
    {
        echo str_pad($key, 20, " ")."$result\n";
    }
    */
    // ...

    $celkem_testu = count($testResults);
    $successed_tests = 0;
    $failed_tests = 0;
    $percentage = "0"."%";
    foreach($testResults as $key => $result)
    {
        $background = "#99ff33";
        if($result == "OK")
        {
            $successed_tests++;
        }
        else
        {
            $failed_tests++;
        }
    }
    if($celkem_testu != 0)
        $percentage = round(($successed_tests / $celkem_testu * 100), 2) . "% testu uspelo.";

    echo "
<!DOCTYPE html>
<html>
    <head>
        <title>Vysledky jednotlivych testu</title>
    </head>
    <body>
        <h2>Vysledky testu ze scriptu test.php</h2>
        <table>
                <tr><td>Pocet testu</td><td>$celkem_testu</td></tr>
                <tr><td>Uspesnych testu</td><td>$successed_tests</td></tr>
                <tr><td>Neuspesnych testu</td><td>$failed_tests</td></tr>
                <tr><th colspan='2'>$percentage</td></tr>
        </table>
        <hr>
        <table>
            <tr><th>Jmeno testu</th><th>Vysledek testu</th></tr>
";
        if( ! empty($testResults))
        {
            foreach($testResults as $key => $result)
            {
                $background = "#99ff33";
                if($result == "OK")
                {
                    $background = "#99ff33";
                }
                else
                {
                    $background = "#ff0000";
                }
                echo "          <tr style='background-color:$background;'><td style='padding: 4px;'>$key</td><td style='padding: 4px;'>$result</td></tr>\n";
            }
        }
        else
        {
            echo "          <tr><td colspan='2' style='padding: 4px;'>Nebyly nalezeny zadne testy v tomto adresari.</td></tr>\n";
        }

    echo "
        </table>
    </body>
</html>
";
}

function writeExitCode($cwd, $exitcode)
{
    $out = fopen("$cwd/output.out", "w");
    fwrite($out, $exitcode);
    fclose($out);
    return 0;
}


function writeArray($fileHandle, $array)
{
    foreach($array as $line)
    {
        fwrite($fileHandle, $line."\n");
    }
}

function checkExistence($pathToDir, $test)
{
    if( ! file_exists("$pathToDir/$test.in"))
    {
        $inputFile = fopen("$pathToDir/$test.in", "w");
        fclose($inputFile);
    }

    if( ! file_exists("$pathToDir/$test.out"))
    {
        $outputFile = fopen("$pathToDir/$test.out", "w");
        fclose($outputFile);
    }

    if( ! file_exists("$pathToDir/$test.rc"))
    {
        $rcFile = fopen("$pathToDir/$test.rc", "w");
        fwrite($rcFile, "0");
        fclose($rcFile);
    }

    return;
}

/*
 * Funkce porovnava vystup programu s referencnim vystupem programu a rozhodne, zdali se shoduji nebo ne.
 * Podle toho nastavi prislusnou hodnotu pro dany test
 */
function diffTests($thisdir, $testName, &$testResultsArray)
{
    $diff_result = shell_exec("diff --ignore-all-space $thisdir/$testName.out $thisdir/$testName.rc");
    if(empty($diff_result))
    {
        //echo "=====> TEST $thisdir OK. Soubor se shoduje s referencnim.\n";
        $testResultsArray["$thisdir/$testName"] = "OK";
        return true;
    }
    else
    {
        //echo "=====> TEST $thisdir FAILED. neshoduje se s referencnim.\n";
        //echo "<Diff>\n$diff_result\n</DIFF>\n";
        $testResultsArray["$thisdir/$testName"] = "FAIL";
        return false;
    }
}

?>
