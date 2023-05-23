// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract FileStorage {
  mapping (uint256 => string) public name;

  function addFile(uint256 _id, string memory _name) public {
    name[_id] = _name;
  }

  function getFile(uint256 _id) public view returns (string memory) {
        return name[_id];
    }
}
