from flask import Blueprint, request, jsonify
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService
from .whatsapp_service import WhatsappService
import json
import re

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()

def clean_json_string(json_string):
    """
    Substitui apenas aspas duplas internas duplicadas em valores específicos do JSON por aspas simples,
    sem adicionar caracteres de escape.
    """
    # Substitui aspas duplas internas nos campos 'problem' e 'item_name' por aspas simples
    json_string = re.sub(r'("problem":\s*")([^"]*?)"([^"]*?)"([^"]*?")', r'\1\2\3 \4', json_string)
    json_string = re.sub(r'("item_name":\s*")([^"]*?)"([^"]*?)"([^"]*?")', r'\1\2\3 \4', json_string)
    return json_string

@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    try:
        raw_data = request.data.decode('utf-8')
        print("JSON bruto recebido:", raw_data)

        cleaned_data_str = clean_json_string(raw_data)
        print("JSON após limpeza:", cleaned_data_str)

        data = json.loads(cleaned_data_str)
    except json.JSONDecodeError as e:
        # Erro específico de JSON
        print("Erro ao decodificar JSON:", e)
        return jsonify({'error': 'Falha ao decodificar JSON', 'details': str(e)}), 400
    except Exception as e:
        # Outros erros genéricos
        print("Erro ao processar dados:", e)
        return jsonify({'error': 'Falha ao processar dados', 'details': str(e)}), 500

    host_ip = data.get('host_ip', 'IP nao disponivel')
    host_description = data.get('host_description', 'Descricao nao disponivel')
    severity = data.get('severity', 'Severidade nao disponivel')
    item_name = data.get('item_name', 'Item monitorado nao disponivel')
    item_value = data.get('item_value', 'Valor atual nao disponivel')
    problem_duration = data.get('problem_duration', 'Duracao nao disponivel')
    last_check_in = data.get('last_check_in', 'Ultimo check-in nao disponivel')	

    problem = data.get('problem', '')
    problem_escaped = problem.replace('"', '\\"')

    title = problem_escaped

    description = (
	f"🚨 *ALERTA DE PROBLEMA* 🚨\n\n"
	f"⚠️ *Status*: _{data.get('trigger_status', 'Status nao disponivel')}_\n"
	f"🔧 *Titulo do Problema*: _{title}_\n"
        f"🖥️ *Host*: _{data.get('host', 'Host nao disponivel')}_\n"
        f"🌐 *IP*: _{host_ip}_\n"
        f"🏷️ *Descricao da Maquina*: _{host_description}_\n"
        f"📍 *Trigger ID*: _{data.get('trigger_id', 'ID nao disponivel')}_\n"
        f"📊 *Severidade*: _{severity}_\n"
        f"🕵️ *Item Monitorado*: _{item_name}_\n"
        f"📈 *Valor Atual*: _{item_value}_\n"
        f"🔁 *Duracao do Problema*: _{problem_duration}_\n"
        f"📅 *Ultimo Check-In do Host*: _{last_check_in}_\n"
    )
    pipefy_service = PipefyService()
    whatsapp_service = WhatsappService()

    #card no Pipefy
    try:
        response = pipefy_service.create_card(title, description)
        print(f"Response from Pipefy API: {response}")
    except Exception as e:
        print(e)

    if not response or 'errors' in response:
        print(f"Response: {response}")
        return jsonify({'error': 'Failed to create card in Pipefy', 'details': response}), 500

    try:
        card_id = response['data']['createCard']['card']['id']
        zabbix_service.save_card_mapping(data.get('trigger_id'), card_id)
    except (KeyError, TypeError) as e:
        print(f"Response: {response}")
        return jsonify({'error': 'Unexpected response structure from Pipefy', 'details': str(e)}), 500

    session_id = f"1"
    message = f"{description}"
    print(message)
    whatsapp_service.sendMessage(message, session_id)

    print(f"Response: {response}")
    return jsonify({'message': 'Card created successfully', 'card_id': card_id}), 200


@zabbix_bp.route('/zabbix-resolved', methods=['POST'])
def handle_zabbix_resolved():
    data = request.json

    host_ip = data.get('ip', 'IP nao disponivel')
    host_description = data.get('description', 'Descricao nao disponivel')

    problem = data.get('problem', '')
    problem_escaped = problem.replace('"', '\\"')

    title = problem_escaped

    description = (
        f"\n\n*PROBLEMA RESOLVIDO!!*\n\nHost: {data.get('host')} \n"
        f"IP: {host_ip} \n"
        f"Descricao: {host_description} \n"
        f"Trigger ID: {data.get('trigger_id')} \n"
        f"Trigger Status: *{data.get('trigger_status')}*"
    )

    whatsapp_service = WhatsappService()

    # Buscar o card_id relacionado ao trigger_id
    card_id = zabbix_service.get_card_id_by_trigger(data.get('trigger_id'))

    if not card_id:
        return jsonify({'error': 'Card ID not found for the given trigger ID'}), 404

    pipefy_service = PipefyService()

    response = pipefy_service.move_card_to_phase(card_id)

    if 'errors' in response:
        print(f"Response: {response}")
        return jsonify({'error': 'Failed to move card in Pipefy', 'details': response}), 500

    session_id = f"1"
    message = f"{title} - {description}"
    whatsapp_service.sendMessageResolved(message, session_id)

    return jsonify({'message': 'Card moved successfully'}), 200
