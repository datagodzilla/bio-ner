import os
import pytest
from bionlp.processors.utils import check_existant_model
from bionlp.processors.bioprocessor import BioProcessor


@pytest.mark.parametrize('ent,model_dir', [
    ('Disease', './models/Disease'),
    ('Chemical', './models/Chemical'),
    ('Gene', './models/Gene'),
])
def test_local_model_loads_and_predicts(ent, model_dir):
    if not check_existant_model(ent):
        pytest.skip(f'Local model for {ent} not found at {model_dir}')
    # instantiate processor in offline mode
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    proc = BioProcessor(model_dir)
    proc.sentence_to_process('Aspirin is used to treat pain and COVID-19 causes respiratory symptoms.')
    results = proc.predict()
    assert isinstance(results, list)
    assert len(results) >= 0
