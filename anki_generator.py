import genanki
import yaml  # Use PyYAML to parse YAML files
import random
import sys
import html

def generate_model(model_id, model_name, fields, templates, css, is_cloze=False):
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

def create_deck(deck_name):
    deck_id = random.randrange(1 << 30, 1 << 31)
    return genanki.Deck(deck_id, deck_name)

def left_align_text(text):
    return f'<div style="text-align:left;">{text}</div>'

def escape_html(text):
    return html.escape(text)

def main():
    if len(sys.argv) != 4:
        print("Usage: python anki_generator.py input.yaml output.apkg deck_name")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    deck_name = sys.argv[3]

    # Read YAML data
    with open(input_file, 'r', encoding='utf-8') as f:
        cards_data = yaml.safe_load(f)

    deck = create_deck(deck_name)

    # Define models

    # 1. Basic Model (Normal Cards)
    basic_model = generate_model(
        model_id=1607392319,
        model_name='Basic Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
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

    # 2. Type-in-the-Answer Model
    type_in_model = generate_model(
        model_id=1234567890,
        model_name='Type-in-the-Answer Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
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

    # 3. Cloze Model
    cloze_model = generate_model(
        model_id=99887766,
        model_name='Cloze Model',
        fields=[
            {'name': 'Text'},
        ],
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
        is_cloze=True  # Set the model type to Cloze
    )

    # Process each card
    for card in cards_data:
        card_type = card.get('type')
        if card_type == 'basic':
            front = left_align_text(escape_html(card['front']))
            back = left_align_text(escape_html(card['back']))
            note = genanki.Note(
                model=basic_model,
                fields=[front, back]
            )
            deck.add_note(note)
        elif card_type == 'type-in-the-answer':
            front = left_align_text(escape_html(card['front']))
            back = card['back']  # Keep back field as is for type-in-the-answer
            note = genanki.Note(
                model=type_in_model,
                fields=[front, back]
            )
            deck.add_note(note)
        elif card_type == 'cloze':
            text = left_align_text(escape_html(card['text']))
            note = genanki.Note(
                model=cloze_model,
                fields=[text],
                guid=genanki.guid_for(text)
            )
            deck.add_note(note)
        else:
            print(f"Unknown card type: {card_type}")

    # Generate the deck package
    genanki.Package(deck).write_to_file(output_file)
    print(f"Anki deck '{deck_name}' has been generated and saved to {output_file}")

if __name__ == '__main__':
    main()
