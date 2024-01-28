import shutil
import os
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

path        = ''
trash_path  = ''

blockchain  = Blockchain(path, trash_path )

@app.route('/mine_block', methods=['GET'])
def mine_block():

    blockchain.update_chain()

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
    
    # Remove files from the processing queue
    blockchain.move_files(residentsPreferencesFilePath, trash_path)
    blockchain.move_files(hospitalsPreferencesFilePath, trash_path)

    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():

    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "Vazio", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message':  'Connected node. Blockchain contains the following connected nodes:',
                'total_nodes': list(blockchain.nodes)}
    
    return jsonify(response),201

@app.route('/update_chain',methods= ['GET'])
def update_chain():

    if blockchain.update_chain():
        response = {'message': 'Blockchain successfully updated.'}
    else:
        response = {'message': 'Current blockchain version is already updated.'}

    return jsonify(response), 200

app.run(host='0.0.0.0', port=5001)