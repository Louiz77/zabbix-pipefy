import json

class ZabbixService:
    def __init__(self):
        self.event_to_card_map = {}

    def map_event_to_card(self, event_id, card_id):
        """
        Mapeia o ID do evento do Zabbix ao ID do card do Pipefy.
        """
        self.event_to_card_map[event_id] = card_id

    def get_card_id_by_event(self, event_id):
        """
        Retorna o ID do card no Pipefy baseado no evento do Zabbix.
        """
        return self.event_to_card_map.get(event_id)

    def delete_event_mapping(self, event_id):
        """
        Remove o mapeamento do evento quando o card for fechado.
        """
        if event_id in self.event_to_card_map:
            del self.event_to_card_map[event_id]

    def save_mapping_to_file(self, filename="event_to_card_map.json"):
        """
        Salva o mapeamento de eventos para cards em um arquivo JSON para persistência.
        """
        with open(filename, 'w') as f:
            json.dump(self.event_to_card_map, f)

    def load_mapping_from_file(self, filename="event_to_card_map.json"):
        """
        Carrega o mapeamento de eventos de um arquivo JSON, caso exista.
        """
        try:
            with open(filename, 'r') as f:
                self.event_to_card_map = json.load(f)
        except FileNotFoundError:
            self.event_to_card_map = {}
