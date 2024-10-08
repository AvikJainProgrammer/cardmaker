import genanki
import yaml
import random
import html

class AnkiDeckGenerator:
    def __init__(self, input_file, output_file, deck_name):
        self.input_file = input_file
        self.output_file = output_file
        self.deck_name = deck_name
        self.deck = self.create_deck(deck_name)

    def generate_model(self, model_id, model_name, fields, templates, css, is_cloze=False):
        if is_cloze:
            return genanki.Model(
                model_id,
                model_name,
                fields=fields,
                templates=templates,
                css=css,
                model_type=genanki.Model.CLOZE
            )
        else:
            return genanki.Model(
                model_id,
                model_name,
                fields=fields,
                templates=templates,
                css=css
            )

    def create_deck(self, deck_name):
        deck_id = random.randrange(1 << 30, 1 << 31)
        return genanki.Deck(deck_id, deck_name)

    def left_align_text(self, text):
        return f'<div style="text-align:left;">{text}</div>'

    def escape_html(self, text):
        return html.escape(text)

    def load_yaml_data(self):
        with open(self.input_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def process_cards(self, cards_data):
        basic_model = self.generate_model(
            model_id=1607392319,
            model_name='Basic Model',
            fields=[{'name': 'Front'}, {'name': 'Back'}],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}',
                    'afmt': '{{FrontSide}}\n\n<hr id="answer">\n{{Back}}',
                },
            ],
            css='''
                .card {
                    white-space: pre-wrap;
                    font-family: arial;
                    font-size: 20px;
                    text-align: left;
                    color: black;
                    background-color: white;
                }
            '''
        )

        type_in_model = self.generate_model(
            model_id=1234567890,
            model_name='Type-in-the-Answer Model',
            fields=[{'name': 'Front'}, {'name': 'Back'}],
            templates=[
                {
                    'name': 'Type-in-the-Answer Card',
                    'qfmt': '{{Front}}<br><br>{{type:Back}}',
                    'afmt': '{{FrontSide}}\n\n<hr id="answer">\n{{Back}}',
                },
            ],
            css='''
                .card {
                    white-space: pre-wrap;
                    font-family: arial;
                    font-size: 20px;
                    text-align: left;
                    color: black;
                    background-color: white;
                }
            '''
        )

        cloze_model = self.generate_model(
            model_id=99887766,
            model_name='Cloze Model',
            fields=[{'name': 'Text'}],
            templates=[
                {
                    'name': 'Cloze Card',
                    'qfmt': '{{cloze:Text}}',
                    'afmt': '{{cloze:Text}}',
                },
            ],
            css='''
                .card {
                    white-space: pre-wrap;
                    font-family: arial;
                    font-size: 20px;
                    text-align: left;
                    color: black;
                    background-color: white;
                }
            ''',
            is_cloze=True
        )

        for card in cards_data:
            card_type = card.get('type')
            if card_type == 'basic':
                front = self.left_align_text(self.escape_html(card['front']))
                back = self.left_align_text(self.escape_html(card['back']))
                note = genanki.Note(
                    model=basic_model,
                    fields=[front, back]
                )
                self.deck.add_note(note)
            elif card_type == 'type-in-the-answer':
                front = self.left_align_text(self.escape_html(card['front']))
                back = card['back']  # Keep back field as is for type-in-the-answer
                note = genanki.Note(
                    model=type_in_model,
                    fields=[front, back]
                )
                self.deck.add_note(note)
            elif card_type == 'cloze':
                text = self.left_align_text(self.escape_html(card['text']))
                note = genanki.Note(
                    model=cloze_model,
                    fields=[text],
                    guid=genanki.guid_for(text)
                )
                self.deck.add_note(note)
            else:
                print(f"Unknown card type: {card_type}")

    def generate_deck(self):
        cards_data = self.load_yaml_data()
        self.process_cards(cards_data)
        genanki.Package(self.deck).write_to_file(self.output_file)
        print(f"Anki deck '{self.deck_name}' has been generated and saved to {self.output_file}")

# Example usage:
# generator = AnkiDeckGenerator('input.yaml', 'output.apkg', 'My Deck Name')
# generator.generate_deck()
