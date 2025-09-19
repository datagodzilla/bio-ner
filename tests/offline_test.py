import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bionlp.processors.utils import check_existant_model
from bionlp.processors.bioprocessor import BioProcessor
import spacy


def test_spacy_model_installed():
    # should not raise when loading spaCy small model
    nlp = spacy.load('en_core_web_sm')
    assert nlp is not None


@pytest.mark.parametrize('ent,model_dir,model_name', [
    ('Disease','models/Disease','alvaroalon2/biobert_diseases_ner'),
    ('Chemical','models/Chemical','alvaroalon2/biobert_chemical_ner'),
    ('Gene','models/Gene','alvaroalon2/biobert_genetic_ner'),
])
def test_local_model_loads_and_predicts(ent, model_dir, model_name):
    # If local model exists, use it; otherwise skip the test
    if not check_existant_model(ent):
        pytest.skip(f'Local model for {ent} not found at {model_dir}')
    bp = BioProcessor(model_dir)
    bp.sentence_to_process('COVID causes fever and BRCA1 mutations')
    preds = bp.predict()
    assert isinstance(preds, list)
    # At least an empty list is OK; If tokens recognized, check structure
    if preds:
        p = preds[0]
        assert 'start' in p and 'end' in p and 'entity_group' in p


if __name__ == '__main__':
    print('Run via pytest: pytest tests/offline_test.py')
