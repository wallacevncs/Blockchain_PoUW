import os
import re
import datetime
import hashlib
import json
from urllib.parse import urlparse
from matching.games import HospitalResident

class Blockchain:

    def __init__(self):
        self.chain = []
        self.nodes = set()

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

    def list_files(self, folder_path):
        files_by_year = {}

        # List all files in the folder
        files = os.listdir(folder_path)

        year_pattern = re.compile(r'\d{4}')

        for file in files:
            # Try to find a year in the file name
            result = year_pattern.search(file)

            if result:
                year = result.group(0)
                full_path = os.path.join(folder_path, file)

                if year not in files_by_year:
                    files_by_year[year] = []

                # Add to the dictionary with the year as the key and the path as the value
                files_by_year[year].append(full_path)

        return files_by_year