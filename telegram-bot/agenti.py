import json
import os
from anthropic import Anthropic
from json_repair import repair_json
from dotenv import load_dotenv

load_dotenv()
ai = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

STRATEGIST_PERSONA = """Sei Marco, senior content strategist con 10 anni di esperienza nel marketing digitale italiano.
Hai lavorato con brand di formazione professionale, liberi professionisti e PMI.
Sei esperto di LinkedIn e Facebook per il mercato italiano.
Conosci la psicologia del target italiano: paure, desideri, blocchi mentali.
Il tuo approccio è concreto: niente buzzword, niente frasi vuote.
Ogni contenuto deve avere un hook forte, un corpo sostanzioso e una CTA chiara.
Quando analizzi un settore vai in profondità: dati reali, dinamiche psicologiche, tattiche che funzionano."""

TIPI_POST = {
    "pillola": {
        "label": "💊 Pillola informativa",
        "istruzioni": (
            "Spiega un concetto chiave in modo semplice e pratico. "
            "Struttura: hook con domanda o dato sorprendente → spiegazione in 3-5 punti numerati → CTA (commenta, salva, segui). "
            "Tono didattico ma accessibile. Max 150 parole corpo + hashtag."
        ),
    },
    "quiz": {
        "label": "❓ Quiz / Domanda",
        "istruzioni": (
            "Crea un post interattivo con una domanda a cui il target voglia rispondere. "
            "Struttura: domanda provocatoria o scenario 'vero o falso' → breve contesto → invito esplicito a commentare la risposta. "
            "Genera curiosità e discussion. Max 100 parole + hashtag."
        ),
    },
    "hook": {
        "label": "🎯 Hook emotivo",
        "istruzioni": (
            "Inizia con una situazione in cui il target si riconosce immediatamente (paura, frustrazione, desiderio). "
            "Struttura: hook empatico sulla situazione reale → amplifica il problema → offri la soluzione/prospettiva → CTA. "
            "Deve colpire allo stomaco nelle prime 2 righe. Max 150 parole + hashtag."
        ),
    },
    "caso": {
        "label": "📖 Caso pratico",
        "istruzioni": (
            "Racconta un esempio concreto o scenario realistico che il target possa riconoscere. "
            "Struttura: situazione iniziale realistica → svolgimento con dettagli concreti → risultato → lezione applicabile subito → CTA. "
            "Usa la seconda persona per coinvolgere. Max 180 parole + hashtag."
        ),
    },
    "novita": {
        "label": "📢 Novità / Aggiornamento",
        "istruzioni": (
            "Comunica un aggiornamento rilevante per il settore con autorevolezza. "
            "Struttura: breaking hook ('NUOVO:', 'ATTENZIONE:', ecc.) → cosa cambia → cosa significa per il target → cosa fare adesso → CTA. "
            "Max 130 parole + hashtag."
        ),
    },
    "motivazionale": {
        "label": "💪 Motivazionale",
        "istruzioni": (
            "Dai energia e speranza al target in un momento di difficoltà. "
            "Struttura: riconosci la fatica/paura del target → ribaltamento positivo con dato o prospettiva reale → azione concreta da fare oggi → CTA incoraggiante. "
            "Autentico, non retorico. Max 140 parole + hashtag."
        ),
    },
}


def _chiedi_ai(system, prompt, max_tokens=2000, model="claude-haiku-4-5-20251001"):
    response = ai.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _parse_json(testo):
    start = testo.find("[") if "[" in testo else testo.find("{")
    end = (testo.rfind("]") + 1) if "[" in testo else (testo.rfind("}") + 1)
    if start == -1 or end <= 0:
        return None
    try:
        return json.loads(repair_json(testo[start:end]))
    except Exception:
        return None


# ─── ANALISI SETTORE ─────────────────────────────────────────────────────────

def analisi_settore(cliente):
    nome = cliente.get("nome", "")
    settore = cliente.get("settore", "")
    target = cliente.get("target", "")
    piattaforme = ", ".join(cliente.get("piattaforme", []))
    obiettivi = cliente.get("obiettivi", "")

    prompt = f"""Analizza in profondità il settore "{settore}" per il brand "{nome}".

Target dichiarato: {target}
Piattaforme: {piattaforme}
Obiettivi: {obiettivi}

Fornisci un'analisi completa e actionable con queste sezioni:

🎯 PSICOLOGIA DEL TARGET
- Paure principali (cosa li tiene svegli la notte)
- Desideri profondi (cosa vogliono davvero ottenere)
- Frustrazioni comuni (cosa li fa arrabbiare nel settore)
- Come si comportano online (dove vanno, cosa cercano, cosa condividono)

✅ COSA FUNZIONA IN QUESTO SETTORE
- Formati di contenuto con più engagement (con spiegazione del perché)
- Temi che generano più reazioni
- Stile di comunicazione vincente
- 3 esempi di hook che funzionano per questo target

❌ COSA NON FUNZIONA
- Errori comuni che fanno perdere follower
- Contenuti che allontanano il target
- Toni e approcci da evitare assolutamente

#️⃣ STRATEGIA HASHTAG per {piattaforme}
- 5 hashtag ad alta rilevanza
- 5 hashtag a media concorrenza
- 3 hashtag di nicchia (bassa concorrenza, alto targeting)

📅 CALENDARIO CONSIGLIATO
- Giorni e orari migliori per ogni piattaforma
- Mix di contenuti consigliato (es. 40% educativo, 30% quiz, ecc.)
- Frequenza ottimale

🚀 OPPORTUNITÀ DI POSIZIONAMENTO
- Come distinguersi dalla concorrenza nel settore
- Angolo unico da sviluppare per "{nome}"
- 3 idee di contenuto originali e specifiche per questo brand

Sii specifico e concreto. Evita generalità. Parla come un esperto che conosce questo settore in profondità."""

    return _chiedi_ai(STRATEGIST_PERSONA, prompt, max_tokens=3000, model="claude-sonnet-4-6")


# ─── GENERA POST ─────────────────────────────────────────────────────────────

def genera_posts(cliente, tipo_key, argomento, n=3):
    nome = cliente.get("nome", "")
    settore = cliente.get("settore", "")
    target = cliente.get("target", "")
    tono = cliente.get("tono", "accessibile")
    piattaforme = ", ".join(cliente.get("piattaforme", []))
    obiettivi = cliente.get("obiettivi", "aumentare follower")
    pillar = cliente.get("pillar", "")
    esempio = cliente.get("esempio_post", "")

    tipo = TIPI_POST.get(tipo_key, TIPI_POST["pillola"])
    istruzioni_tipo = tipo["istruzioni"]

    esempio_section = f"\nEsempio di post che piace al cliente:\n{esempio}\n" if esempio else ""

    prompt = f"""Crea {n} varianti DISTINTE di post social per il brand "{nome}".

PROFILO CLIENTE:
- Settore: {settore}
- Target: {target}
- Tono di voce: {tono}
- Piattaforme: {piattaforme}
- Obiettivo attuale: {obiettivi}
- Argomenti pillar: {pillar}
{esempio_section}
ARGOMENTO DEL POST: {argomento}

TIPO DI POST RICHIESTO: {tipo["label"]}
ISTRUZIONI: {istruzioni_tipo}

IMPORTANTE:
- Ogni variante deve avere un approccio diverso (angolo, hook, struttura)
- Adatta il linguaggio al target e al tono specificato
- Includi sempre 4-6 hashtag pertinenti in fondo
- Le varianti devono essere realmente diverse, non parafrasarsi a vicenda
- Scrivi in italiano

Rispondi SOLO con un JSON array, senza testo aggiuntivo:
[
  {{"variante": 1, "testo": "testo completo del post con hashtag in fondo"}},
  {{"variante": 2, "testo": "..."}},
  {{"variante": 3, "testo": "..."}}
]"""

    raw = _chiedi_ai(STRATEGIST_PERSONA, prompt, max_tokens=2000)
    dati = _parse_json(raw)

    if not dati:
        return [{"variante": 1, "testo": "Errore nella generazione. Riprova.", "tipo": tipo_key}]

    return [
        {
            "variante": i + 1,
            "testo": p.get("testo", ""),
            "tipo": tipo_key,
            "argomento": argomento,
            "cliente": nome,
        }
        for i, p in enumerate(dati[:n])
    ]


# ─── PIANO EDITORIALE ────────────────────────────────────────────────────────

def piano_editoriale(cliente, settimane=1):
    nome = cliente.get("nome", "")
    settore = cliente.get("settore", "")
    target = cliente.get("target", "")
    piattaforme = ", ".join(cliente.get("piattaforme", []))
    frequenza = cliente.get("frequenza", "3 post a settimana")
    pillar = cliente.get("pillar", "")

    prompt = f"""Crea un piano editoriale dettagliato per {settimane} settimana/e per il brand "{nome}".

PROFILO:
- Settore: {settore}
- Target: {target}
- Piattaforme: {piattaforme}
- Frequenza: {frequenza}
- Argomenti pillar: {pillar}

Il piano deve includere per ogni post:
- Giorno e orario consigliato
- Piattaforma
- Tipo di post (pillola/quiz/hook/caso pratico/novità/motivazionale)
- Argomento specifico
- Obiettivo del post (engagement, awareness, conversione)
- Hook suggerito (prima riga del post)

Organizza il piano in modo che ci sia varietà nei tipi di contenuto e progressione logica negli argomenti.
Considera i momenti migliori per ogni piattaforma per il target indicato.

Rispondi con il piano formattato in modo chiaro e leggibile. Usa emoji per rendere visivo il piano."""

    return _chiedi_ai(STRATEGIST_PERSONA, prompt, max_tokens=2500, model="claude-sonnet-4-6")


# ─── MIGLIORA POST ───────────────────────────────────────────────────────────

def migliora_post(testo_originale, feedback, cliente):
    nome = cliente.get("nome", "")
    tono = cliente.get("tono", "accessibile")

    prompt = f"""Migliora questo post per il brand "{nome}" (tono: {tono}).

POST ORIGINALE:
{testo_originale}

FEEDBACK / COSA CAMBIARE:
{feedback}

Mantieni la struttura e l'argomento ma applica le modifiche richieste.
Rispondi SOLO con il testo del post migliorato, senza commenti."""

    return _chiedi_ai(STRATEGIST_PERSONA, prompt, max_tokens=600)


# ─── CONSIGLIO RAPIDO ────────────────────────────────────────────────────────

def consiglio_marketing(domanda, cliente):
    nome = cliente.get("nome", "")
    settore = cliente.get("settore", "")
    target = cliente.get("target", "")

    prompt = f"""Il brand "{nome}" (settore: {settore}, target: {target}) ti pone questa domanda:

{domanda}

Rispondi come un senior content strategist: diretto, concreto, actionable.
Max 200 parole. Niente intro generiche, vai subito al punto."""

    return _chiedi_ai(STRATEGIST_PERSONA, prompt, max_tokens=800, model="claude-sonnet-4-6")
