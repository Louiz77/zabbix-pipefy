from flask import Flask, request, current_app, jsonify
import requests
import json

class WhatsappService:
    def __init__(self):
        self.api_url = current_app.config['WHATSAPP_API_URL']
        self.headers = {
            "Content-Type": "application/json"
        }
    def sendMessage(self, message, session_id):
        payload = json.dumps({
            "sessionId": session_id,
            "to": "120363339322672895@g.us",
            "message": str(message)
        })

        response = requests.request("POST", self.api_url, headers=self.headers, data=payload)
        print("Response Whatsapp: ", response)
        return jsonify({'message': 'Finalizado'}), 200

    def sendMessageResolved(self, message, session_id):
        payload = json.dumps({
            "sessionId": session_id,
            "to": "120363339322672895@g.us",
            "message": str(message)
        })

        response = requests.request("POST", self.api_url, headers=self.headers, data=payload)
        print("Response Whatsapp ",response)
        return jsonify({'message': 'Finalizado'}), 200
