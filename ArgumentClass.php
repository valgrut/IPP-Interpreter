<?php

/*
 * Autor: Jiri Peska
 * Login: xpeska05
 *
 */

class Argument
{
	private $_argType;
	private $_argValue;

	public function __construct() {}

	public function getArgType() {return $this->_argType;}
	public function getArgValue() {return $this->_argValue;}

	public function setArgType($type) {$this->_argType = $type;}
	public function setArgValue($value) {$this->_argValue = $value;}


	/*
	 * @return
	 *
	 */
	public function parseArgument($sourceParam)
	{
		$parsedParam = explode("@", $sourceParam, 2);

                return $parsedParam;
                /*
		if(count($parsedParam) == 1)
		{
			$this->setArgType("label");
			$this->setArgValue($parsedParam[0]);
		}
		else
		{
			$this->setArgType($parsedParam[0]);
			$this->setArgValue($parsedParam[1]);
		}
                */
	}
}
