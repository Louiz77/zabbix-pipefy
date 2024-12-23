import json
import os

class CardRepository:
    def __init__(self, filepath='card_data.json'):
        self.filepath = filepath
        self.data = self._load_data()

    def _load_data(self):
        # Carrega os dados do arquivo JSON
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as file:
                return json.load(file)
        return {}

    def _save_data(self):
        # Salva os dados no arquivo JSON
        with open(self.filepath, 'w') as file:
            json.dump(self.data, file, indent=4)

    def store_card_id(self, trigger_id, card_id):
        # Armazena o card_id associado ao trigger_id
        self.data[trigger_id] = card_id
        self._save_data()

    def get_card_id(self, trigger_id):
        # Recupera o card_id associado ao trigger_id
        return self.data.get(trigger_id)