# Biomedical NER Model Architecture and Workflow

## Overview
This project performs Named Entity Recognition (NER) on biomedical text using a hybrid architecture that combines a spaCy base model with custom entity recognition components for diseases, chemicals, and genes. The system is designed to recognize biomedical entities with high accuracy and flexibility, leveraging both pre-trained language models and domain-specific processors.

---

## 1. Base Model: spaCy `en_core_web_sm`
- The core NLP pipeline is built on top of spaCy's `en_core_web_sm` model.
- This model provides basic English tokenization, part-of-speech tagging, and a general-purpose NER component.
- In this project, the default NER and some other components are excluded or replaced to allow for custom biomedical entity recognition.

**Code:**
```python
import spacy
nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "lemmatizer"])
```

---

## 2. Custom NER Components
Three custom processors are layered on top of the spaCy pipeline:
- `DiseaseProcessor`
- `ChemicalProcessor`
- `GeneProcessor`

These are implemented as Python classes (see `bionlp/processors/`) and are responsible for:
- Detecting domain-specific entities in text (diseases, chemicals, genes)
- Providing normalization and metadata lookup (via Solr)

### How They Are Integrated
A custom spaCy pipeline component called `ner_custom` is registered and added to the pipeline:

**Code:**
```python
@Language.factory("ner_custom")
def create_ner_model(nlp: Language, name: str):
    return NERComponent(nlp)

class NERComponent:
    def __init__(self, nlp: Language):
        self.entities = None
    def __call__(self, doc: Doc) -> Doc:
        self.entities = Entities(doc)
        process_by_paragraph(doc, self.entities)
        self.entities.postprocessing()
        return doc
```

- The `NERComponent` uses the three processors to scan each paragraph and add biomedical entities to the spaCy `Doc` object.
- The pipeline is further extended with regex-based postprocessing components for COVID and chemical suffixes.

**Pipeline assembly:**
```python
nlp.add_pipe('ner_custom', before='ner')
nlp.add_pipe('postprocessing_covid', before='ner')
nlp.add_pipe('postprocessing_chems', before='postprocessing_covid')
```

---

## 3. Model Configuration and Selection
Each processor can use either a local model or a remote (HuggingFace) model, depending on what is available:
- If a local model directory exists (e.g., `./models/Disease`), it is loaded.
- Otherwise, a remote model is used (e.g., `alvaroalon2/biobert_diseases_ner`).

**Example:**
```python
if check_existant_model('Disease'):
    disease_service = DiseaseProcessor('./models/Disease')
else:
    disease_service = DiseaseProcessor('alvaroalon2/biobert_diseases_ner')
```

This logic applies to all three processors.

---

## 4. Architecture Workflow

1. **Text Input**: User submits biomedical text to the API.
2. **spaCy Preprocessing**: Text is tokenized and processed by the base spaCy pipeline.
3. **Custom NER**: The `ner_custom` component applies the Disease, Chemical, and Gene processors to detect entities.
4. **Postprocessing**: Regex-based components add/expand COVID and chemical entities.
5. **Entity Normalization**: Detected entities are normalized using Solr lookups (not part of prediction, but for metadata enrichment).
6. **Output**: The API returns detected entities and their normalized forms (if available).

**Diagram:**
```
[Input Text]
     |
     v
[spaCy en_core_web_sm]
     |
     v
[ner_custom (DiseaseProcessor, ChemicalProcessor, GeneProcessor)]
     |
     v
[postprocessing_covid]
     |
     v
[postprocessing_chems]
     |
     v
[Entities Extracted]
     |
     v
[Solr Normalization (optional)]
     |
     v
[API Output]
```

---

## 5. Example Configuration and Usage

**Example: Running the NER Pipeline**
```python
from bionlp import nlp
text = "COVID-19 is caused by SARS-CoV-2. Aspirin is used for pain. Mutations in BRCA1 are linked to cancer."
doc = nlp(text)
for ent in doc.ents:
    print(ent.text, ent.label_)
```

**Sample Output:**
```
COVID-19 DISEASE
SARS-CoV-2 DISEASE
Aspirin CHEMICAL
BRCA1 GENETIC
cancer DISEASE
```

---

## 6. Customization and Extensibility
- You can add new entity types by extending the processor classes and registering new spaCy pipeline components.
- The system is designed to fall back to remote models if local models are not present, making it portable and robust.

---

## 7. Summary Table
| Component         | Model Used                        | Purpose                |
|-------------------|-----------------------------------|------------------------|
| spaCy base        | en_core_web_sm                    | Tokenization, POS, etc |
| DiseaseProcessor  | ./models/Disease or biobert_diseases_ner | Disease NER           |
| ChemicalProcessor | ./models/Chemical or biobert_chemical_ner | Chemical NER          |
| GeneProcessor     | ./models/Gene or biobert_genetic_ner      | Gene NER              |
| Postprocessing    | Regex patterns                    | COVID, chemical suffix |

---

## 8. References
- [spaCy documentation](https://spacy.io/)
- [HuggingFace Transformers](https://huggingface.co/)
- [Project source code: bionlp/NER_processing.py, bionlp/processors/]

---

## 9. Solr + Docker (Normalization backend)

This project separates entity *detection* (NER) from *normalization* (mapping entity strings to canonical records). Solr is used as the normalization backend: after the NER model finds entity spans (e.g., "COVID", "Aspirin", "BRCA1"), the processors call Solr to find matching canonical records, identifiers, cross-references, and other metadata.

Why Solr?
- Solr is a high-performance, schema-driven search engine built on Lucene. It supports fast full-text search, faceting, and flexible query syntax which makes it well-suited for normalization lookups (fuzzy matches, alternate labels, cross-references).
- Solr's Schema API lets us add fields and tune analyzers for biomedical text (tokenization, lowercasing, n-grams, etc.) so lookups can be made robust against synonyms and formatting variations.

Why Docker for Solr?
- Docker simplifies running a consistent Solr instance across development and deployment: the same container image and configuration can be used locally and in CI/CD or production.
- Using Docker Compose lets you pre-create cores, mount configuration files, and run initialization scripts (schema updates, sample data indexing) reproducibly.
- Docker avoids host-level dependency/version issues and keeps Solr isolated from the developer machine.
- That said, Docker is optional — you can run Solr directly on a host OS if you prefer. The project scripts and docs assume a Docker-based Solr for convenience.

Solr cores used by this project
- The project expects the following Solr cores (names used by the code and scripts):
     - `bioner-diseases`
     - `bioner-drugs` (chemical/drug database)
     - `bioner-genetic` (gene/protein database)
     - `bioner-covid` (COVID-specific records)

Where do these cores come from?
- The repository includes `Solr` helpers and `docker-compose.yml` that start a Solr container and pre-create these cores. In production or bulk indexing workflows, the cores are populated by indexing scripts (e.g., `Solr/index_docs.sh` or other ETL scripts under `Solr/data_processing/`).
- The data sources used to populate these cores are project-specific and typically come from biomedical databases (e.g., PubChem, ChEBI, MeSH, UniProt, RefSeq) or curated project CSV/JSON files. The `Solr/data_processing/` folder contains notebooks and scripts demonstrating how to create these datasets.

How Solr supports normalization
- After the NER model extracts entity text (e.g., `"Aspirin"`), the corresponding processor (e.g., `ChemicalProcessor`) will:
     1. Build a Solr query that searches the appropriate core and fields (exact form, label, synonyms, other normalized keys).
     2. Execute the query via HTTP (the project uses `pysolr` or direct `curl` calls in scripts).
     3. Parse the Solr response and select the best match (by score, exact match preference, or heuristic rules).
     4. Return a normalized object with canonical `id`, preferred `label`, `synonyms`, `cross_references`, and other metadata.

Typical Solr query flow (example pseudocode):
```python
# Given entity_text = "aspirin" and core = 'bioner-drugs'
query = f'label:"{entity_text}" OR synonyms:"{entity_text}" OR id:"{entity_text}"'
resp = solr.search(core, q=query, rows=5)
if resp.hits:
          candidate = choose_best(resp.docs)
          normalized = { 'id': candidate['id'], 'label': candidate.get('label'), 'xref': candidate.get('cross_references', []) }
else:
          normalized = None
```

Notes on analyzers and schema
- For biomedical text, it's common to use analyzers that preserve punctuation (for gene names like `BRCA1`), apply case-insensitive matching, and index synonyms. The `create_schemas.sh` (or `create_schemas_clean.sh`) scripts in `Solr/` configure the cores' managed-schema with the fields used by the processors (e.g., `label`, `synonyms`, `mesh_id`, `inchikey`, `chebi_id`, etc.).

Docker vs. bare-metal Solr
- Using Docker is convenient and reproducible. It packages Solr, configuration, and scripts into a portable setup. Docker Compose in the repo pre-creates cores and runs any init scripts.
- You can instead install Solr natively on a server and run the same schema definition and indexing scripts against it. The code expects the Solr base URL (environment `SOLR_URL`) and core names; if you point `SOLR_URL` to a native Solr instance, everything should work the same.
- The only differences are operational: Docker makes it easy to spin up an isolated Solr instance locally and ensure the correct Solr version. Native installs may require manual configuration and matching Solr versions.

External sources for cores
- The repository does not hardcode a single external "download" URL for cores, but the `Solr/data_processing/` folder contains notebooks and scripts that show how to build the cores from public datasets (examples: PubChem, ChEBI, MeSH, UniProt). These data sources are commonly used to populate the `bioner-*` cores.

In some deployments, pre-built core backups (Solr core directories or Solr `snapshot`/`backup`) may be hosted on an artifact server or cloud storage; the `docker-compose.yml` can mount or restore those backups during container initialization.

### How the named cores help normalization

- `bioner-diseases`: contains disease names, synonyms, MeSH IDs, ICD codes and other disease metadata. Used to normalize disease mentions to canonical identifiers and provide preferred labels and ontological links.
- `bioner-drugs`: contains drug/chemical names, synonyms, ChEBI/CID/InChI/INCHIKEY, MeSH headings and cross references used to normalize chemical mentions.
- `bioner-genetic`: contains gene/protein names, synonyms and accession mappings used to normalize genetic mentions (e.g., BRCA1 -> canonical gene id).
- `bioner-covid`: focused COVID-specific records and variant lineage identifiers to support COVID-related normalization.

### Example: normalization end-to-end

1. NER extracts `"BRCA1"` and labels it `GENETIC`.
2. `GeneProcessor` constructs a Solr query against core `bioner-genetic` searching `label`, `synonyms`, and `aliases` fields.
3. Solr returns candidate documents; the processor picks the best candidate (exact match or highest score) and returns a normalized object like `{id: 'GENE:672', label: 'BRCA1', synonyms: ['BRCA-1'], cross_references: ['HGNC:1100', 'NCBI:672']}`.
4. The API response includes both the detected entity text and the normalized metadata.

### Quick commands and dev tips

- Start Solr (docker compose in `Solr/`):

```bash
cd Solr
docker compose up -d
```

- Apply schema fields (script is included in `Solr/`):

```bash
cd Solr
chmod +x create_schemas_clean.sh
./create_schemas_clean.sh
```

- Check core status:

```bash
curl -s 'http://localhost:8983/solr/admin/cores?action=STATUS&wt=json' | jq .
curl -s 'http://localhost:8983/solr/bioner-diseases/admin/ping' | jq .
```

### Summary

- Solr is used exclusively for normalization and enrichment of detected entities, not for prediction.
- Docker simplifies running Solr consistently during development and deployment but is optional if you install Solr natively and configure `SOLR_URL` accordingly.
- The important cores are `bioner-diseases`, `bioner-drugs`, `bioner-genetic`, and `bioner-covid` — they store canonical records used to convert detected entity strings into structured, cross-referenced normalized results.

## 10. Offline Mode: making the NER fully local

This project supports running the entire NER pipeline locally without contacting external model registries. The processors will load local model directories under `./models/` when present. To make the system fully offline by default, follow these steps and use the provided helper scripts.

What the repo expects
- Local model layout for each entity (example `models/Disease/`): `pytorch_model.bin`, `config.json`, `tokenizer_config.json`, `vocab.txt` (or the tokenizer files produced by HF tokenizers). The code's `check_existant_model()` uses these names to detect local models.
- The spaCy model `en_core_web_sm` must be installed into the environment (or saved and installed from a wheel).

Provided automation
- `scripts/download_models.sh`: downloads the three HF models used as fallbacks and saves them into `models/Disease`, `models/Chemical`, `models/Gene` (run this once while online).
- `scripts/activate_offline.sh`: exports environment variables to force offline behavior (`TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`) and sets `SOLR_URL` to a localhost value.

How it works at runtime
- On import, `bionlp/NER_processing.py` calls `check_existant_model('Disease')` etc. If a local directory is found, the processors are constructed with that path (e.g., `DiseaseProcessor('./models/Disease')`) and the `transformers` loader will read from disk.
- We also patch the Transformers calls to prefer `local_files_only=True` when running offline or when `model_name` is a local path. This avoids accidental network calls.

Recommended workflow (one-time, online)
1. Activate your target environment (e.g., `raredis-nlp-py312`).
2. Run the download script (provided):

```bash
bash scripts/download_models.sh
```

3. Install spaCy and the small English model in the environment (run once online):

```bash
pip install -U spacy
python -m spacy download en_core_web_sm
```

4. Activate offline mode before running the app:

```bash
source scripts/activate_offline.sh
python app.py 5050
```

Testing offline
- Run the offline test: `pytest tests/offline_test.py` (this script verifies each model loads from the saved `models/` directory and runs one sample inference).

If you prefer I can create a Docker image that includes all models preloaded, or I can vendor the models into the repo if you want them checked into local storage (not recommended due to size).

For a minimal quick-start (how to start the server offline on port 5050) see the small snippet in the project `README.md` under "Quick: Run Offline (local models)".
