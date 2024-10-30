from flask import Blueprint, request, jsonify
import time
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService
from .whatsapp_service import WhatsappService

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()

RETRY_LIMIT = 5
# Número máximo de tentativas

RETRY_DELAY = 5
# Tempo de espera entre as tentativas (em segundos)

def attempt_with_retries(func, *args, **kwargs):
    """Tenta executar uma função com um limite de tentativas em caso de falha."""
    attempts = 0
    while attempts < RETRY_LIMIT:
        response = func(*args, **kwargs)
        if response.get("status_code", 200) == 200:
            # Se o status for 200, retorna a resposta
            return response
        attempts += 1
        print(f"Attempt {attempts} failed. Retrying in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
    return response
    # Retorna a última resposta após atingir o limite de tentativas

@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    data = request.json

    host_ip = data.get('ip', 'IP nao disponivel')
    host_description = data.get('description', 'Descricao nao disponivel')
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
    response = attempt_with_retries(pipefy_service.create_card, title, description)
    if 'errors' in response:
        message = f"Nao foi possível criar o card no Pipefy\n\nErro: {response}"
        whatsapp_service.sendMessage(message, session_id="1")
        return jsonify({'error': 'Failed to create card in Pipefy', 'details': response}), 500

    try:
        card_id = response['data']['createCard']['card']['id']
        zabbix_service.save_card_mapping(data.get('trigger_id'), card_id)
    except (KeyError, TypeError) as e:
        message = f"Nao foi possível criar o card no Pipefy\n\nErro: {str(e)}"
        whatsapp_service.sendMessage(message, session_id="1")
        return jsonify({'error': 'Unexpected response structure from Pipefy', 'details': str(e)}), 500

    # Enviar mensagem no WhatsApp com tentativas de reenvio
    message = f"{description}"
    attempt_with_retries(whatsapp_service.sendMessage, message, session_id="1")

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
        session_id = f"1"
        message = f"Nao foi possível mover o card para concluido no Pipefy\n\nErro: ID do card não foi encontrado"
        whatsapp_service.sendMessage(message, session_id)
        return jsonify({'error': 'Card ID not found for the given trigger ID'}), 404

    pipefy_service = PipefyService()

    response = attempt_with_retries(pipefy_service.move_card_to_phase, card_id)
    if 'errors' in response:
        message = f"Erro ao mover o card no pipefy\n\nErro: {response}"
        whatsapp_service.sendMessage(message, session_id="1")
        return jsonify({'error': 'Failed to move card in Pipefy', 'details': response}), 500

    # Enviar mensagem de resolução no WhatsApp com tentativas de reenvio
    message = f"{title} - {description}"
    attempt_with_retries(whatsapp_service.sendMessageResolved, message, session_id="1")

    return jsonify({'message': 'Card moved successfully'}), 200
