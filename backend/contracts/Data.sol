// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Data {
    uint public speedLimit;
    uint public speed;
    bool public noHornArea;
    bool public didWeHorned;
    bool public hump;
    bool public fourWheeler;
    bool public seatbelt;

    constructor(uint _speedLimit, uint _speed) {
        speedLimit = _speedLimit;
        speed = _speed;
        noHornArea = false;
        didWeHorned = false;
        hump = false;
        fourWheeler = false;
        seatbelt = false;
    }

    function setSpeedLimit(uint _speedLimit) public {
        speedLimit = _speedLimit;
    }

    function setSpeed(uint _speed) public {
        speed = _speed;
    }

    function setNoHornArea(bool _noHornArea) public {
        noHornArea = _noHornArea;
    }

    function setDidWeHorned(bool _didWeHorned) public {
        didWeHorned = _didWeHorned;
    }

    function setHump(bool _hump) public {
        hump = _hump;
    }

    function setFourWheeler(bool _fourWheeler) public {
        fourWheeler = _fourWheeler;
    }

    function setSeatbelt(bool _seatbelt) public {
        seatbelt = _seatbelt;
    }
}