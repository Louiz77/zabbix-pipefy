from flask import Blueprint, request, jsonify
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()

@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    data = request.json
    title = data.get('problem')
    description = f"Host: {data.get('host')} - Trigger ID: {data.get('trigger_id')} - Trigger Status: {data.get('trigger_status')}"

    pipefy_service = PipefyService()

    response = pipefy_service.create_card(title, description)

    print(f"Response from Pipefy API: {response}")

    if not response or 'errors' in response:
        return jsonify({'error': 'Failed to create card in Pipefy', 'details': response}), 500

    try:
        card_id = response['data']['createCard']['card']['id']
    except (KeyError, TypeError) as e:
        return jsonify({'error': 'Unexpected response structure from Pipefy', 'details': str(e)}), 500


    return jsonify({'message': 'Card created successfully', 'card_id': card_id}), 200
