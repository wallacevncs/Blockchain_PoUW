import os
import re
import datetime
import hashlib
import json
import requests
from urllib.parse import urlparse
from matching.games import HospitalResident

class Blockchain:

    def __init__(self, s3_manager):
        self.s3_manager  = s3_manager
        self.chain       = []
        self.nodes       = set()

    def create_block(self, poUW, previous_hash, edition):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'previous_hash': previous_hash,
                 'edition': edition,
                 'result': poUW}

        self.chain.append(block)
        return block

    def get_previous_block(self):
        if not self.chain:
            return None
        return self.chain[-1]

    def is_chain_valid(self, chain):

        last_block = self.get_previous_block()
        for i in range(len(chain) - 1, -1, -1):
            current_block = chain[i]
            year_match    = re.compile(r'\d{4}').search(current_block['edition'])
            if not year_match:
                continue

            edition_year   = year_match.group(0)
            residents_file = 'residentsPreferences_{}.json'.format(edition_year)
            hospitals_file = 'hospitalsPreferences_{}.json'.format(edition_year)

            # Compares the last result found between the 2 chains
            if current_block['edition'] == last_block['edition'] and current_block['result'] != last_block['result']:

                residents_file_id  = self.s3_manager.get_file_id(residents_file)
                hospitals_file_id  = self.s3_manager.get_file_id(hospitals_file)

                # Restores objects to be mined again
                if not residents_file_id:
                    self.s3_manager.delete_file(residents_file, residents_file_id)

                if not hospitals_file_id:
                    self.s3_manager.delete_file(hospitals_file, hospitals_file_id)

                # Remove last block
                self.chain.pop() 
                return False

            if i == len(chain) - 1:
                residents_file_id  = self.s3_manager.get_file_id(residents_file)
                hospitals_file_id  = self.s3_manager.get_file_id(hospitals_file)

                if not residents_file_id or not hospitals_file_id:
                    self.chain.pop()
                    return False

            if i == 0:
                continue

            previous_block = chain[i-1]
            if current_block['previous_hash'] != self.hash(previous_block):
                return False
            
        return True

    def update_chain(self):
        network             = self.nodes
        updated_chain       = None
        max_length          = len(self.chain)
        current_timestamp   = None

        if self.chain and 'timestamp' in self.chain[-1]:
            current_timestamp = datetime.datetime.strptime(self.chain[-1]['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

        for node in network:
            response   = requests.get(f'http://{node}/get_chain')

            if response.status_code == 200:
                length         = response.json()['length']
                chain          = response.json()['chain']

                if(len(chain) == 0):
                    continue

                node_timestamp = None
                if chain and 'timestamp' in chain[-1]:
                    node_timestamp = datetime.datetime.strptime(chain[-1]['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

                if not self.is_chain_valid(chain):
                    continue

                if length > max_length:
                    max_length    = length
                    updated_chain = chain
                elif length == max_length and current_timestamp > node_timestamp:
                    updated_chain = chain

        if updated_chain:
            self.chain = updated_chain
            return True
        
        return False

    def proof_of_work(self, residents_file_path, hospitals_file_path):

        with open(residents_file_path, 'r') as file:
            residents_json = json.load(file)

        with open(hospitals_file_path, 'r') as file:
            hospitals_json = json.load(file)

        resident_prefs = {}
        for item in residents_json['Preferences']:
            name                   = item['Name']
            preferences            = item['Preferences']
            resident_prefs[name]   = preferences

        hospital_prefs = {}
        hospitals_cap  = {}
        for item in hospitals_json['Hospitals']:
            program                 = item['Program']
            preferences             = item['Preferences']
            hospital_prefs[program] = preferences
            hospitals_cap[program]  = item['Capacity']

        game     = HospitalResident.create_from_dictionaries(
            resident_prefs, hospital_prefs, hospitals_cap)
        
        matching = game.solve()
        if not game.check_validity() or not game.check_stability():
            return None

        matching_as_dict = {str(key): str(value) for key, value in matching.items()}

        return json.dumps(matching_as_dict)

    def hash(self, block):
        if block is None:
            return None

        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def delete_file(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)