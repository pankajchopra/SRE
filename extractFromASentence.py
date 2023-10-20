from vosk import Model, KaldiRecognizer
import sys
import json
import spacy
from spacy.pipeline import EntityRuler
entity_rules = [
    {"label": "application", "pattern": "account"},
    {"label": "application", "pattern": "account detail"},
    {"label": "application", "pattern": "household"},
    {"label": "application", "pattern": "stock chart"},
    {"label": "application", "pattern": "date or time or datetime"},
    {"label": "application", "pattern": "stock news"},
    {"label": "ORG", "pattern": "Amazon"},
    {"label": "ORG", "pattern": "wellsfargo"}
]


class ExtractFromASentence:
    def extract_entities(sentence):
        """Extracts entities from a sentence using NLP.
      Args:
        sentence: A string containing the sentence to extract entities from.
      Returns:
        A list of dictionaries containing the entities extracted from the sentence,
        where each dictionary contains the following keys:
          * `text`: The text of the entity.
          * `label`: The label of the entity, such as `PERSON`, `ORGANIZATION`,
            or `LOCATION`.
      """
        # Create a spaCy EntityRuler object.
        # entity_ruler = EntityRuler(nlp, overwrite_ents=True)



        # Load the spaCy English language model.
        nlp = spacy.load("en_core_web_sm")
        entity_ruler = nlp.add_pipe("entity_ruler")
        # Add the custom entity rules to the EntityRuler object.
        for rule in entity_rules:
            entity_ruler.add_patterns([rule])

        # Process the sentence using the spaCy NLP pipeline.
        doc = nlp(sentence)

        # Extract all of the named entities from the sentence.
        entities = []
        for ent in doc.ents:
            entity = {
                "text": ent.text,
                "label": ent.label_,
            }
            entities.append(entity)

        # Return the list of entities.
        return entities