import flask
from flask import request, jsonify, abort
from flask import render_template
from flask_cors import CORS, cross_origin
try:
    from flaskext.markdown import Markdown
except Exception:
    # Flask 3 removed `Markup` import used by Flask-Markdown; provide a no-op
    # fallback so the app can run under newer Flask versions. Features that
    # require Markdown rendering will be disabled when this fallback is used.
    class Markdown:  # simple shim
        def __init__(self, app=None):
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            # register a dummy filter that returns the input unchanged
            @app.template_filter('markdown')
            def _markdown_noop(s):
                return s

from bionlp import nlp, disease_service, chemical_service, genetic_service

from spacy import displacy

colors = {"DISEASE": "linear-gradient(90deg, #aa9cfc, #fc9ce7)",
          "CHEMICAL": "linear-gradient(90deg, #ffa17f, #3575ad)",
          "GENETIC": "linear-gradient(90deg, #c21500, #ffc500)"}

app = flask.Flask(__name__)
Markdown(app)
CORS(app, support_credentials=True, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/', methods=['GET'])
@cross_origin()
def home():
    return render_template('index.html')



##################################################################################################
######
######          Bio NLP
######
##################################################################################################


@app.route('/bio-ner/entities', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def post_search_entities():
    if not request.json or not 'text' in request.json:
        abort(400)
    sequence = request.json['text']
    doc = nlp(sequence)

    entities_html = displacy.render(doc, style="ent",
                                    options={"ents": ["DISEASE", "CHEMICAL", "GENETIC", "DATE","GPE", "COVID LINEAGE"],
                                             "colors": colors})

    chemicals = [f.text for f in doc.ents if f.label_ == 'CHEMICAL']
    diseases = [f.text for f in doc.ents if f.label_ == 'DISEASE']
    genetics = [f.text for f in doc.ents if f.label_ == 'GENETIC']

    normalized_chems = chemical_service.normalize_chemical_entities(chemicals)
    normalized_dis = disease_service.normalize_disease_entities(diseases)
    normalized_gen = genetic_service.normalize_genetic_entities(genetics)
    normalized_covid = genetic_service.normalize_covid_entities(genetics+chemicals)

    normalized_ents = {'diseases': normalized_dis, 'chemicals': normalized_chems, 'genetics': normalized_gen,
                       'covid': normalized_covid}

    return jsonify(html=entities_html, entities=normalized_ents)


# health endpoint for monitoring / readiness checks
@app.route('/health', methods=['GET'])
@cross_origin()
def health():
    return jsonify(status='ok')


import os
import sys
if __name__ == '__main__':
    # Print runtime versions to help debug binary/API mismatches
    try:
        import torch as _torch
        import transformers as _trans
        print(f"torch version: {_torch.__version__}, transformers version: {_trans.__version__}")
        # Simple heuristic warning for major mismatches
        t_major = int(_torch.__version__.split('.')[0]) if _torch.__version__ else 0
        tr_major = int(_trans.__version__.split('.')[0]) if _trans.__version__ else 0
        if t_major < 2 and tr_major >= 4:
            print('WARNING: Detected older torch version; consider using torch>=2.0 for best compatibility with transformers')
    except Exception:
        print('Could not import torch/transformers for version check')
    # Priority: command-line argument > environment variable > default 5000
    port = 5000
    # Check for command-line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    # Check for environment variable
    port = int(os.environ.get('PORT', port))
    app.run(debug=True, host='0.0.0.0', port=port)
