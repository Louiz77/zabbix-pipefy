import requests
from flask import current_app

class PipefyService:
    def __init__(self):
        self.api_url = current_app.config['PIPEFY_API_URL']
        self.api_token = current_app.config['PIPEFY_API_TOKEN']
        self.pipe_id = current_app.config['PIPEFY_PIPE_ID']
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def create_card(self, title, description):
        query = f'''
        mutation {{
          createCard(input: {{
            pipe_id: {self.pipe_id},
            phase_id: 328586642
            title: "{title}",
            fields_attributes: [
              {{
                field_id: "clique_aqui_para_adicionar_a_justificativa",
                field_value: "{description}"
              }}
            ]
          }}) {{
            card {{
              id
              title
            }}
          }}
        }}
        '''

        response = requests.post(self.api_url, json={'query': query}, headers=self.headers)
        return response.json()

    def move_card_to_phase(self, card_id, phase_id):
        # GraphQL mutation para mover o card para outra fase
        query = f'''
        mutation {{
            moveCardToPhase(input: {{
                card_id: {card_id},
                destination_phase_id: {phase_id}
            }}) {{
                card {{
                    id
                }}
            }}
        }}
        '''
        response = requests.post(self.api_url, json={'query': query}, headers=self.headers)
        return response.json()

    def close_card(self, card_id):
        query = f'''
        mutation {{
            moveCardToPhase(input: {{
                card_id: {card_id},
                destination_phase_id: 328586647
            }}) {{
                card {{
                    id
                }}
            }}
        }}
        '''

        response = requests.post(self.api_url, json={'query': query}, headers=self.headers)
        return response.json()
