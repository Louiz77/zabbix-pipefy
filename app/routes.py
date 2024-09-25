from flask import Blueprint, request, jsonify
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()

cards = {}

@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    data = request.json
    title = data.get('problem')
    description = f"Host: {data.get('host')} - Trigger ID: {data.get('trigger_id')} - Trigger Status: {data.get('trigger_status')}"

    pipefy_service = PipefyService()

    if data.get('trigger_status') == 'PROBLEM':
        # Se for um problema, criar um novo card no Pipefy
        response = pipefy_service.create_card(title, description)
        print(f"Response from Pipefy API (Create Card): {response}")

        if not response or 'errors' in response:
            return jsonify({'error': 'Failed to create card in Pipefy', 'details': response}), 500

        try:
            card_id = response['data']['createCard']['card']['id']
            cards[event_id] = card_id  # Armazenar o ID do card para este evento
        except (KeyError, TypeError) as e:
            return jsonify({'error': 'Unexpected response structure from Pipefy', 'details': str(e)}), 500

        return jsonify({'message': 'Card created successfully', 'card_id': card_id}), 200

    elif data.get('trigger_status') == 'OK':
        # Se o status for "OK", mover o card para a fase de resolução
        card_id = cards.get(event_id)
        if not card_id:
            return jsonify({'error': 'Card ID not found for this event.'}), 404

        # Fase de resolução no Pipefy (substituir com o ID correto da fase de resolução)
        resolution_phase_id = 328586647

        response = pipefy_service.move_card_to_phase(card_id)
        print(f"Response from Pipefy API (Move Card): {response}")

        if not response or 'errors' in response:
            return jsonify({'error': 'Failed to move card in Pipefy', 'details': response}), 500

        return jsonify({'message': 'Card moved successfully', 'card_id': card_id}), 200

    return jsonify({'message': 'Event status not recognized.'}), 400