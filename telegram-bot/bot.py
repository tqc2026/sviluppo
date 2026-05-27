import os
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ai = Anthropic()

# In-memory storage per la demo
clienti = {}      # {chat_id: {nome, settore, tono, piattaforme}}
sessioni = {}     # {chat_id: stato corrente}
contenuti = {}    # {chat_id: lista post generati}

# ─── COMANDI BASE ────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(msg):
    testo = (
        "👋 Benvenuto nel sistema di automazione contenuti!\n\n"
        "Cosa puoi fare:\n"
        "• /nuovo_cliente — aggiungi un cliente\n"
        "• /clienti — lista clienti salvati\n"
        "• /crea — genera post social per un cliente\n\n"
        "Inizia con /nuovo_cliente"
    )
    bot.send_message(msg.chat.id, testo)


@bot.message_handler(commands=["clienti"])
def lista_clienti(msg):
    cid = msg.chat.id
    if not clienti.get(cid):
        bot.send_message(cid, "Nessun cliente ancora. Usa /nuovo_cliente")
        return
    testo = "📋 Clienti salvati:\n\n"
    for nome, dati in clienti[cid].items():
        testo += f"• *{nome}* — {dati['settore']} ({', '.join(dati['piattaforme'])})\n"
    bot.send_message(cid, testo, parse_mode="Markdown")


# ─── NUOVO CLIENTE ───────────────────────────────────────────────────────────

@bot.message_handler(commands=["nuovo_cliente"])
def nuovo_cliente(msg):
    cid = msg.chat.id
    sessioni[cid] = {"step": "nome_cliente"}
    bot.send_message(cid, "Come si chiama il cliente (o il brand)?")


# ─── CREA CONTENUTO ──────────────────────────────────────────────────────────

@bot.message_handler(commands=["crea"])
def crea_contenuto(msg):
    cid = msg.chat.id
    if not clienti.get(cid):
        bot.send_message(cid, "Nessun cliente salvato. Usa prima /nuovo_cliente")
        return
    sessioni[cid] = {"step": "scelta_cliente_crea"}
    kb = InlineKeyboardMarkup()
    for nome in clienti[cid]:
        kb.add(InlineKeyboardButton(nome, callback_data=f"cliente_crea:{nome}"))
    bot.send_message(cid, "Per quale cliente creo i contenuti?", reply_markup=kb)


# ─── GESTIONE MESSAGGI TESTO (macchina a stati) ──────────────────────────────

@bot.message_handler(content_types=["text"])
def gestisci_testo(msg):
    cid = msg.chat.id
    stato = sessioni.get(cid, {})
    step = stato.get("step")

    if step == "nome_cliente":
        stato["nome"] = msg.text.strip()
        stato["step"] = "settore_cliente"
        sessioni[cid] = stato
        bot.send_message(cid, f"Settore o tipo di attività di *{msg.text.strip()}*?", parse_mode="Markdown")

    elif step == "settore_cliente":
        stato["settore"] = msg.text.strip()
        stato["step"] = "tono_cliente"
        sessioni[cid] = stato
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Accessibile e diretto", callback_data="tono:accessibile"),
            InlineKeyboardButton("Professionale e formale", callback_data="tono:professionale"),
            InlineKeyboardButton("Motivazionale", callback_data="tono:motivazionale"),
            InlineKeyboardButton("Tecnico ed esperto", callback_data="tono:tecnico"),
        )
        bot.send_message(cid, "Che tono deve avere la comunicazione?", reply_markup=kb)

    elif step == "topic_post":
        nome = stato.get("cliente_selezionato")
        dati = clienti[cid][nome]
        topic = msg.text.strip()
        bot.send_message(cid, "⏳ Genero i post, un momento...")
        posts = genera_posts(nome, dati, topic)
        contenuti[cid] = posts
        mostra_posts(cid, posts)
        sessioni.pop(cid, None)

    else:
        bot.send_message(cid, "Usa /start per vedere i comandi disponibili.")


# ─── CALLBACK BOTTONI ────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def gestisci_callback(call):
    cid = call.message.chat.id
    data = call.data
    stato = sessioni.get(cid, {})

    if data.startswith("tono:"):
        tono = data.split(":")[1]
        stato["tono"] = tono
        stato["step"] = "piattaforme_cliente"
        sessioni[cid] = stato
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Facebook", callback_data="piatt:Facebook"),
            InlineKeyboardButton("LinkedIn", callback_data="piatt:LinkedIn"),
            InlineKeyboardButton("Instagram", callback_data="piatt:Instagram"),
            InlineKeyboardButton("✅ Fatto", callback_data="piatt:fatto"),
        )
        stato.setdefault("piattaforme", [])
        bot.edit_message_text(f"Tono scelto: *{tono}*\nSu quali piattaforme pubblichiamo? (seleziona e poi ✅ Fatto)", cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

    elif data.startswith("piatt:"):
        val = data.split(":")[1]
        if val == "fatto":
            piattaforme = stato.get("piattaforme", ["Facebook"])
            nome = stato["nome"]
            if cid not in clienti:
                clienti[cid] = {}
            clienti[cid][nome] = {
                "settore": stato["settore"],
                "tono": stato["tono"],
                "piattaforme": piattaforme,
            }
            sessioni.pop(cid, None)
            bot.edit_message_text(
                f"✅ Cliente *{nome}* salvato!\n\nSettore: {stato['settore']}\nTono: {stato['tono']}\nPiattaforme: {', '.join(piattaforme)}\n\nUsa /crea per generare i primi contenuti.",
                cid, call.message.message_id, parse_mode="Markdown"
            )
        else:
            piattaforme = stato.setdefault("piattaforme", [])
            if val not in piattaforme:
                piattaforme.append(val)
            sessioni[cid] = stato
            bot.answer_callback_query(call.id, f"{val} aggiunto ✓")

    elif data.startswith("cliente_crea:"):
        nome = data.split(":", 1)[1]
        stato["cliente_selezionato"] = nome
        stato["step"] = "topic_post"
        sessioni[cid] = stato
        bot.edit_message_text(
            f"Cliente: *{nome}*\n\nDescrivimi l'argomento o incollami il testo su cui creare i post:",
            cid, call.message.message_id, parse_mode="Markdown"
        )

    elif data.startswith("approva:"):
        idx = int(data.split(":")[1])
        posts = contenuti.get(cid, [])
        if idx < len(posts):
            posts[idx]["stato"] = "approvato"
            bot.answer_callback_query(call.id, "✅ Post approvato!")
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=stato_approvato(idx))

    elif data.startswith("scarta:"):
        idx = int(data.split(":")[1])
        posts = contenuti.get(cid, [])
        if idx < len(posts):
            posts[idx]["stato"] = "scartato"
            bot.answer_callback_query(call.id, "❌ Post scartato")
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=stato_scartato(idx))

    elif data.startswith("rigenera:"):
        idx = int(data.split(":")[1])
        bot.answer_callback_query(call.id, "⏳ Rigenerazione in corso...")
        posts = contenuti.get(cid, [])
        nome = posts[idx].get("cliente", "")
        dati = clienti[cid].get(nome, {})
        topic = posts[idx].get("topic", "")
        nuovo = genera_posts(nome, dati, topic, n=1)
        if nuovo:
            posts[idx] = nuovo[0]
            contenuti[cid] = posts
            kb = kb_post(idx)
            bot.edit_message_text(
                f"🔄 *Post {idx+1} rigenerato*\n\n{nuovo[0]['testo']}",
                cid, call.message.message_id, parse_mode="Markdown", reply_markup=kb
            )


# ─── GENERAZIONE AI ──────────────────────────────────────────────────────────

def genera_posts(nome_cliente, dati, topic, n=3):
    piattaforme = ", ".join(dati.get("piattaforme", ["Facebook"]))
    tono = dati.get("tono", "accessibile")
    settore = dati.get("settore", "")

    prompt = f"""Sei un copywriter esperto di social media marketing.
Genera {n} post distinti per il brand "{nome_cliente}" nel settore "{settore}".
Tono: {tono}.
Piattaforme: {piattaforme}.
Argomento: {topic}

Ogni post deve:
- Avere un hook forte nella prima riga
- Essere conciso (max 150 parole)
- Avere 3-5 hashtag pertinenti in fondo
- Essere adatto al tono e al settore indicati

Rispondi SOLO con un JSON array, senza testo aggiuntivo:
[
  {{"testo": "testo completo del post con hashtag"}},
  ...
]"""

    try:
        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text
        start = raw.find("[")
        end = raw.rfind("]") + 1
        from json_repair import repair_json
        posts_data = json.loads(repair_json(raw[start:end]))
        return [
            {"testo": p["testo"], "stato": "in_attesa", "cliente": nome_cliente, "topic": topic}
            for p in posts_data[:n]
        ]
    except Exception as e:
        return [{"testo": f"Errore generazione: {e}", "stato": "errore", "cliente": nome_cliente, "topic": topic}]


def mostra_posts(cid, posts):
    for i, post in enumerate(posts):
        testo = f"📝 *Post {i+1}*\n\n{post['testo']}"
        bot.send_message(cid, testo, parse_mode="Markdown", reply_markup=kb_post(i))


def kb_post(idx):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("✅ Approva", callback_data=f"approva:{idx}"),
        InlineKeyboardButton("🔄 Rigenera", callback_data=f"rigenera:{idx}"),
        InlineKeyboardButton("❌ Scarta", callback_data=f"scarta:{idx}"),
    )
    return kb


def stato_approvato(idx):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Approvato", callback_data=f"noop:{idx}"))
    return kb


def stato_scartato(idx):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Scartato", callback_data=f"noop:{idx}"))
    return kb


# ─── AVVIO ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Bot avviato...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
