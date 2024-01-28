import os
import shutil
import re
import datetime
import hashlib
import json
import requests
from collections import OrderedDict
from urllib.parse import urlparse
from matching.games import HospitalResident

class Blockchain:

    def __init__(self, path, trash_path):
        self.path        = path
        self.trash_path  = trash_path
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

    def is_chain_valid(self, chain, block):

        last_block = self.get_previous_block()
        for i in range(len(chain) - 1, -1, -1):
            current_block = chain[i]
            year_match    = re.compile(r'\d{4}').search(current_block['edition'])
            if not year_match:
                continue

            edition_year  = year_match.group(0)

            # Compares the last result found between the 2 chains
            if current_block['edition'] == last_block['edition'] and current_block['result'] != last_block['result']:
                
                residentsPreferencesFilePath  = '{}/residentsPreferences_{}.json'.format(self.trash_path, edition_year)
                hospitalsPreferencesFilePath  = '{}/hospitalsPreferences_{}.json'.format(self.trash_path, edition_year)
                
                # Returns files to be reprocessed
                self.move_files(residentsPreferencesFilePath, self.path)
                self.move_files(hospitalsPreferencesFilePath, self.path)

                # Remove the last block
                self.chain.pop()

                return False
            
            files = self.list_files(self.trash_path, edition_year)
            if not files and i == len(chain) - 1:
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

                if not self.is_chain_valid(chain, chain[-1]):
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

    def proof_of_work(self, residentsPreferencesFilePath, hospitalsPreferencesFilePath):

        with open(residentsPreferencesFilePath, 'r') as file:
            residentsJson = json.load(file)

        with open(hospitalsPreferencesFilePath, 'r') as file:
            hospitalsJson = json.load(file)

        resident_prefs = {}
        for item in residentsJson['Preferences']:
            name = item['Name']
            preferences = item['Preferences']
            resident_prefs[name] = preferences

        hospital_prefs = {}
        hospitals_cap = {}
        for item in hospitalsJson['Hospitals']:
            program = item['Program']
            preferences = item['Preferences']
            hospital_prefs[program] = preferences
            hospitals_cap[program] = item['Capacity']

        game = HospitalResident.create_from_dictionaries(
            resident_prefs, hospital_prefs, hospitals_cap)
        
        matching = game.solve()

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

    def list_files(self, folder_path, year=None):
        files_by_year = OrderedDict()

        # List all files in the folder
        files = os.listdir(folder_path)

        year_pattern = re.compile(r'\d{4}')

        for file in files:
            # Try to find a year in the file name
            result = year_pattern.search(file)

            if result:
                file_year = result.group(0)

                if year and file_year != year:
                    continue

                full_path = os.path.join(folder_path, file)

                if file_year not in files_by_year:
                    files_by_year[file_year] = []

                # Add to the dictionary with the year as the key and the path as the value
                files_by_year[file_year].append(full_path)

        files_by_year = OrderedDict(sorted(files_by_year.items(), key=lambda x: x[0], reverse=True))

        return files_by_year
    
    def move_files(self, current_path, subdirectory_path):
        os.makedirs(subdirectory_path, exist_ok=True)

        if os.path.exists(current_path):
            destination_path = os.path.join(subdirectory_path, os.path.basename(current_path))
            shutil.move(current_path, destination_path)