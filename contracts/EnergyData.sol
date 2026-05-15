// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnergyData {

    string public dataHash;

    function storeHash(string memory _hash) public {
        dataHash = _hash;
    }

    function getHash() public view returns(string memory){
        return dataHash;
    }
}