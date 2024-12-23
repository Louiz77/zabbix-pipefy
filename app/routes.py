from flask import Blueprint, request, jsonify
from .pipefy_service import PipefyService
from .zabbix_service import ZabbixService
from .whatsapp_service import WhatsappService
import json
import re
from datetime import datetime

zabbix_bp = Blueprint('zabbix', __name__)
zabbix_service = ZabbixService()
zabbix_service.load_mapping_from_file()

def clean_json_string(json_string):
    """
    Limpa e ajusta o JSON bruto recebido do Zabbix:
    - Remove espaços e quebras de linha.
    - Corrige aspas duplas duplicadas e problemáticas.
    - Corrige campos que estão sem vírgula de separação correta.
    - Retorna o JSON como dicionário ou uma string JSON original em caso de erro.
    """
    # Remove espaços extras e quebras de linha
    json_string = re.sub(r'\s+', ' ', json_string)

    # Corrige aspas duplicadas nos campos específicos
    json_string = re.sub(r'("problem":\s*")([^"]*?)"([^"]*?)"([^"]*?")', r'\1\2\3 \4', json_string)
    json_string = re.sub(r'("item_name":\s*")([^"]*?)"([^"]*?)"([^"]*?")', r'\1\2\3 \4', json_string)

    # Insere a vírgula faltante após os valores "problem" e "item_name" quando necessário
    json_string = re.sub(r'("problem":\s*"[^"]+)(,?\s*"host_ip")', r'\1", \2', json_string)
    json_string = re.sub(r'("item_name":\s*"[^"]+)(,?\s*"item_value")', r'\1", \2', json_string)

    # Tenta converter a string JSON limpa em um dicionário Python
    try:
        json_data = json.loads(json_string)
        print("JSON cleaned com êxito.")
        print(json_data)
        return json_data
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}. Retornando JSON bruto.")
        print(json_string)
        return json_string  # Retorna a string JSON original se a conversão falhar

@zabbix_bp.route('/zabbix-webhook', methods=['POST'])
def handle_zabbix_webhook():
    try:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | * Trigger enviado pelo Zabbix | Processo iniciado * \n")
        raw_data = request.data.decode('utf-8')
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Recebendo POST do Zabbix - JSON bruto recebido.\n")

        # Tenta carregar o JSON bruto
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            cleaned_data = clean_json_string(raw_data)
            if isinstance(cleaned_data, str):
                data = json.loads(cleaned_data)
            else:
                data = cleaned_data

    except Exception as e:
        return jsonify({'error': 'Falha ao processar dados', 'details': str(e)}), 500

    # Extrair e logar informações do JSON
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

    # Verificar severidade
    if severity in ['high', 'disaster', 'High', 'Disaster']:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Severidade compativel para criar card\n")
        pipefy_service = PipefyService()
        try:
            response = pipefy_service.create_card(title, description)
            if not response or 'errors' in response:
                raise Exception(f"Erro na API do Pipefy: {response}")

            card_id = response['data']['createCard']['card']['id']
            zabbix_service.save_card_mapping(data.get('trigger_id'), card_id)

            with open("report.log", "a") as my_file:
                my_file.write(
                    f"-{datetime.now()} | Card {card_id} criado no Pipefy para Trigger ID {data.get('trigger_id')}\n")
        except Exception as e:
            with open("report.log", "a") as my_file:
                my_file.write(f"-{datetime.now()} | Erro ao criar card no Pipefy: {e}\n")
            return jsonify({'error': 'Failed to create card in Pipefy', 'details': str(e)}), 500
    else:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Severidade {severity} não é suficiente para criar um card.\n")

    # Enviar mensagem no WhatsApp
    whatsapp_service = WhatsappService()
    session_id = f"undefined"
    try:
        whatsapp_service.sendMessage(description, session_id)
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Mensagem enviada no WhatsApp com sessão {session_id}\n")
    except Exception as e:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro ao enviar mensagem no WhatsApp: {e}\n")

    return jsonify({'message': 'Processamento concluído com sucesso'}), 200

@zabbix_bp.route('/zabbix-resolved', methods=['POST'])
def handle_zabbix_resolved():
    try:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | * Trigger enviado pelo Zabbix | Processo iniciado * \n")
        raw_data = request.data.decode('utf-8')
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Recebendo POST do Zabbix - JSON bruto recebido.\n")

        # Tenta carregar o JSON bruto
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            # Limpa o JSON caso contenha erros
            cleaned_data = clean_json_string(raw_data)
            with open("report.log", "a") as my_file:
                my_file.write(f"-{datetime.now()} | JSON cleaned com êxito.\n{cleaned_data}\n")

            # Verifica se cleaned_data é um dicionário ou string JSON
            if isinstance(cleaned_data, str):
                data = json.loads(cleaned_data)  # Carrega o JSON se ainda for uma string
            else:
                data = cleaned_data  # Usa diretamente se já for um dicionário

    except json.JSONDecodeError as e:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro ao decodificar JSON: {e}\n")
        return jsonify({'error': 'Falha ao decodificar JSON', 'details': str(e)}), 400

    except Exception as e:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro ao processar dados: {e}\n")
        return jsonify({'error': 'Falha ao processar dados', 'details': str(e)}), 500

    host_ip = data.get('ip', 'IP nao disponivel')
    host_description = data.get('host_description', 'Descricao nao disponivel')

    problem = data.get('problem', '')
    problem_escaped = problem.replace('"', '\\"')

    title = problem_escaped
    message = (
        f"✅ *PROBLEMA RESOLVIDO!* ✅\n\n"
        f"🔧 *Título do Problema*: _{title}_\n"
        f"🖥️ *Host*: _{data.get('host', 'Host nao disponivel')}_\n"
        f"🌐 *IP*: _{host_ip}_\n"
        f"🏷️ *Descricao da Maquina*: _{host_description}_\n"
        f"📍 *Trigger ID*: {data.get('trigger_id')}\n"
    )
    whatsapp_service = WhatsappService()

    # Buscar o card_id relacionado ao trigger_id
    card_id = zabbix_service.get_card_id_by_trigger(data.get('trigger_id'))
    if not card_id:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro: Card ID não encontrado para Trigger ID {data.get('trigger_id')}\n")
        return jsonify({'error': 'Card ID not found for the given trigger ID'}), 404

    # Movendo o card para a fase de resolvido
    pipefy_service = PipefyService()
    try:
        response = pipefy_service.move_card_to_phase(card_id)
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Card {card_id} movido para a fase de resolvido\n")
    except Exception as e:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro ao mover card no Pipefy: {e}\n")
        return jsonify({'error': 'Failed to move card in Pipefy', 'details': str(e)}), 500

    # Enviando mensagem no WhatsApp de resolução
    session_id = f"undefined"
    try:
        whatsapp_service.sendMessageResolved(message, session_id)
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Mensagem de resolução enviada no WhatsApp para sessão {session_id}\n")
    except Exception as e:
        with open("report.log", "a") as my_file:
            my_file.write(f"-{datetime.now()} | Erro ao enviar mensagem de resolução no WhatsApp: {e}\n")

    return jsonify({'message': 'Card moved successfully'}), 200
