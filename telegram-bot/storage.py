import json
from pathlib import Path

STORAGE_FILE = Path("dati.json")


def _carica():
    if STORAGE_FILE.exists():
        try:
            return json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"clienti": {}}


def _salva(dati):
    STORAGE_FILE.write_text(
        json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_clienti(chat_id):
    return _carica().get("clienti", {}).get(str(chat_id), {})


def get_cliente(chat_id, nome):
    return get_clienti(chat_id).get(nome, {})


def salva_cliente(chat_id, nome, profilo):
    dati = _carica()
    dati.setdefault("clienti", {}).setdefault(str(chat_id), {})[nome] = profilo
    _salva(dati)


def elimina_cliente(chat_id, nome):
    dati = _carica()
    dati.get("clienti", {}).get(str(chat_id), {}).pop(nome, None)
    _salva(dati)
