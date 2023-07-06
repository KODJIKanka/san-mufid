// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract FileStorage {
    struct File {
        string name;
        string hash;
    }
    
    File[] public files;
    
    function addFile(string memory _name, string memory _hash) public {
        files.push(File(_name, _hash));
    }
    
    function getFileHash(string memory _name) public view returns (string memory) {
        for (uint i = 0; i < files.length; i++) {
            if (keccak256(bytes(files[i].name)) == keccak256(bytes(_name))) {
                return files[i].hash;
            }
        }
        revert("File not found");
    }
    
    function getFile(string memory _name) public view returns (string memory, string memory) {
        for (uint i = 0; i < files.length; i++) {
            if (keccak256(bytes(files[i].name)) == keccak256(bytes(_name))) {
                return (files[i].name, files[i].hash);
            }
        }
        revert("File not found");
    }
}