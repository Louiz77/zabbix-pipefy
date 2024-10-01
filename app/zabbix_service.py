import json
import os

class ZabbixService:
    def __init__(self):
        self.mapping_file = 'trigger_card_mapping.json'
        self.mapping_data = {}

    # Carregar mapeamentos do arquivo JSON ao iniciar o serviço
    def load_mapping_from_file(self):
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                self.mapping_data = json.load(f)
        else:
            self.mapping_data = {}

    # Salvar o mapeamento do trigger_id e card_id no arquivo JSON
    def save_card_mapping(self, trigger_id, card_id):
        self.mapping_data[trigger_id] = card_id
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mapping_data, f)

    # Recuperar o card_id usando o trigger_id
    def get_card_id_by_trigger(self, trigger_id):
        return self.mapping_data.get(trigger_id)
