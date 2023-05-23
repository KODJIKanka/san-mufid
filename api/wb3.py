from fastapi import FastAPI
from sqlalchemy import Boolean
from web3 import Web3
from typing import List
from pydantic import BaseModel

app = FastAPI()

w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))

contract_adress = '0x406A1b1e6c9A4152B7798B53768e7a09b4E0f712'

abi = [
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "name",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "fileType",
          "type": "string"
        }
      ],
      "name": "addFile",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "getFilesByOwner",
      "outputs": [
        {
          "components": [
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "fileType",
              "type": "string"
            },
            {
              "internalType": "address",
              "name": "owner",
              "type": "address"
            }
          ],
          "internalType": "struct FileStorage.File[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [],
      "name": "getAllFiles",
      "outputs": [
        {
          "components": [
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "fileType",
              "type": "string"
            },
            {
              "internalType": "address",
              "name": "owner",
              "type": "address"
            }
          ],
          "internalType": "struct FileStorage.File[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    }
  ]

contrat = w3.eth.contract(address=contract_adress, abi=abi)

@app.post("/files")
def add_file(name: str, fileType: str):
    tx_hash = contrat.functions.addFile(name, fileType).transact()

    w3.eth.send_raw_transaction(tx_hash)

    return {'message' : 'Data set successfully'}

@app.get("/files")
def get_all_files():
    return contrat.functions.getAllFiles()

@app.get("/files/{owner}")
def get_files_by_owner(owner: str):
    return contrat.functions.getFilesByOwner(owner)