import os
import sys
import boto3
from flask import Flask, jsonify, request
from uuid import uuid4
from blockchain import Blockchain
from s3Manager import S3Manager

sys.setrecursionlimit(5000)

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_address = str(uuid4()).replace('-', '')

s3          = boto3.client(service_name='s3')
s3Manager   = S3Manager(s3, 'nrmp-input')
blockchain  = Blockchain(s3Manager)

@app.route('/mine_block', methods=['GET'])
def mine_block():
    
    blockchain.update_chain()

    files   = s3Manager.list_files()
    if not files:
        return jsonify({'message': 'There are no files to be mined.'}), 204

    year    = next(iter(files), None)
    edition = 'NRMP_{}'.format(year)

    previous_block = blockchain.get_previous_block()
    previous_hash  = blockchain.hash(previous_block)

    if previous_block is not None and previous_block.get('edition') == edition:
        blockchain.chain.pop() # Avoid reprocessing same edition
        previous_block = blockchain.get_previous_block()
        previous_hash  = blockchain.hash(previous_block)

    residents_file = 'residentsPreferences_{}.json'.format(year)
    hospitals_file = 'hospitalsPreferences_{}.json'.format(year)

    residentsPreferencesFilePath = os.path.join(os.getcwd(), os.path.basename(residents_file))
    hospitalsPreferencesFilePath = os.path.join(os.getcwd(), os.path.basename(hospitals_file))

    s3Manager.download_file(residents_file, residentsPreferencesFilePath)
    s3Manager.download_file(hospitals_file, hospitalsPreferencesFilePath)

    poUW           = blockchain.proof_of_work(residentsPreferencesFilePath, hospitalsPreferencesFilePath)       
    block          = blockchain.create_block(poUW, previous_hash, edition)
    response = {'message': 'block successfully mined!',
                'index':         block['index'],
                'timestamp':     block['timestamp'],
                'edition':       block['edition'],
                'previous_hash': block['previous_hash'],
                'result':        block['result']}

    blockchain.delete_file(residentsPreferencesFilePath)
    blockchain.delete_file(hospitalsPreferencesFilePath)

    residents_file_id = s3Manager.get_file_id(residents_file)
    hospitals_file_id = s3Manager.get_file_id(hospitals_file)

    if not residents_file_id:
        s3Manager.delete_file(residents_file)

    if not hospitals_file_id:
        s3Manager.delete_file(hospitals_file)

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
