// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract FileStorage {
    struct File {
        string name;
        bytes32 hash;
    }
    
    File[] private files;
    
    function addFile(string memory _name, bytes32 _hash) public {
        files.push(File(_name, _hash));
    }
    
    function getFileHash(string memory _name) public view returns (bytes32) {
        for (uint i = 0; i < files.length; i++) {
            if (keccak256(bytes(files[i].name)) == keccak256(bytes(_name))) {
                return files[i].hash;
            }
        }
        revert("File not found");
    }
    
    function getFile(string memory _name) public view returns (string memory, bytes32) {
        for (uint i = 0; i < files.length; i++) {
            if (keccak256(bytes(files[i].name)) == keccak256(bytes(_name))) {
                return (files[i].name, files[i].hash);
            }
        }
        revert("File not found");
    }
}