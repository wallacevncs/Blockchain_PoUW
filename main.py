import sys
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
from blockchain import Blockchain

sys.setrecursionlimit(5000)

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_address = str(uuid4()).replace('-', '')

blockchain = Blockchain()

path = "/mnt/c/Users/walla/Documents/Faculdade/Projeto Final/Files/INPUT"


@app.route('/mine_block', methods=['GET'])
def mine_block():
    files = blockchain.list_files(path)
    if not files:
        return jsonify({'message': 'There are no files to be mined.'}), 204
    
    year    = next(iter(files), None)
    edition = 'NRMP_{}'.format(year)
    residentsPreferencesFilePath = '{}/residentsPreferences_{}.json'.format(path, year)
    hospitalsPreferencesFilePath = '{}/hospitalsPreferences_{}.json'.format(path, year)

    poUW           = blockchain.proof_of_work(residentsPreferencesFilePath, hospitalsPreferencesFilePath)
    previous_block = blockchain.get_previous_block()
    previous_hash  = blockchain.hash(previous_block)

    block = blockchain.create_block(poUW, previous_hash, edition)
    response = {'message': 'block successfully mined!',
                'index':         block['index'],
                'timestamp':     block['timestamp'],
                'edition':       block['edition'],
                'previous_hash': block['previous_hash'],
                'result':        block['result']}
    
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


app.run(host='0.0.0.0', port=5001)