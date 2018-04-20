<?php

/*
 * Autor: Jiri Peska
 * Login: xpeska05
 * 
 */

class Instruction
{
	private static $_orderCounter = 0; //-1
        private $_order = 0; //-1
	private $_opcode;
	private $_argArray = array();
	
	public function __construct()
	{
		self::$_orderCounter++;
                $this->_order = self::$_orderCounter;
		$this->_opcode = NULL;		
	}
	
	public function getArgArray() 	{return $this->_argArray;}
	public function insertNewArgument($newArgument)
	{
		if(is_object($newArgument))
		{
			$this->_argArray[] = $newArgument;
		}
	}

	//public function setOrder($order) {$this->_order = $order;}
	public function getOrder() {return $this->_order;}
	
	public function setOpcode($opcode) {$this->_opcode = $opcode;}
	public function getOpcode() {return $this->_opcode;}
}
