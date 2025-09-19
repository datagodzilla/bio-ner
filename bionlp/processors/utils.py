from os import path


def paragraphs(document):
    start = 0
    for token in document:
        if token.is_space and token.text.count("\n") > 1:
            yield document[start:token.i]
            start = token.i
    yield document[start:]


def unique_terms(entities):
    seen = set()
    ents = []
    for item in entities:
        if item.lower() not in seen:
            if len(item) > 1:
                seen.add(item.lower())
                ents.append(item)
    return ents


def check_existant_model(ent):
    flag_ent = False
    model_dir = './models/' + ent + '/'
    # accept either PyTorch bin or safetensors format for model weights
    has_weights = path.isfile(path.join(model_dir, 'pytorch_model.bin')) or path.isfile(path.join(model_dir, 'model.safetensors'))
    # common config/tokenizer files
    has_config = path.isfile(path.join(model_dir, 'config.json'))
    has_tokenizer = path.isfile(path.join(model_dir, 'tokenizer_config.json')) or path.isfile(path.join(model_dir, 'tokenizer.json')) or path.isfile(path.join(model_dir, 'vocab.txt'))
    if has_weights and has_config and has_tokenizer:
        flag_ent = True
    return flag_ent
