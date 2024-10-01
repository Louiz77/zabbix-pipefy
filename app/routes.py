from flask import Blueprint, request, jsonify
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService
from .whatsapp_service import WhatsappService

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()


@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    data = request.json

    title = data.get('problem')
    description = f"Host: {data.get('host')} - Trigger ID: {data.get('trigger_id')} - Trigger Status: {data.get('trigger_status')}"

    pipefy_service = PipefyService()
    whatsapp_service = WhatsappService()

    #card no Pipefy
    response = pipefy_service.create_card(title, description)
    print(f"Response from Pipefy API: {response}")

    if not response or 'errors' in response:
        return jsonify({'error': 'Failed to create card in Pipefy', 'details': response}), 500

    try:
        card_id = response['data']['createCard']['card']['id']
        zabbix_service.save_card_mapping(data.get('trigger_id'), card_id)
    except (KeyError, TypeError) as e:
        return jsonify({'error': 'Unexpected response structure from Pipefy', 'details': str(e)}), 500

    session_id = f"1"
    message = f"{title} - {description}"
    whatsapp_service.sendMessage(message, session_id)

    return jsonify({'message': 'Card created successfully', 'card_id': card_id}), 200


@zabbix_bp.route('/zabbix-resolved', methods=['POST'])
def handle_zabbix_resolved():
    data = request.json
    trigger_id = data.get('trigger_id')

    title = data.get('problem')
    description = f"Host: {data.get('host')} - Trigger ID: {data.get('trigger_id')} - Trigger Status: {data.get('trigger_status')}"

    whatsapp_service = WhatsappService()

    # Buscar o card_id relacionado ao trigger_id
    card_id = zabbix_service.get_card_id_by_trigger(trigger_id)

    if not card_id:
        return jsonify({'error': 'Card ID not found for the given trigger ID'}), 404

    pipefy_service = PipefyService()

    response = pipefy_service.move_card_to_phase(card_id)

    if 'errors' in response:
        return jsonify({'error': 'Failed to move card in Pipefy', 'details': response}), 500

    session_id = f"1"
    message = f"PROBLEMA RESOLVIDO - {title} - {description}"
    whatsapp_service.sendMessageResolved(message, session_id)

    return jsonify({'message': 'Card moved successfully'}), 200