import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import agenti
import storage

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

# Sessioni in memoria: {chat_id: {step, dati temporanei}}
sessioni = {}

# Post generati in attesa di revisione: {chat_id: [post]}
bozze = {}


# ═══════════════════════════════════════════════════════════════
# MENU PRINCIPALE
# ═══════════════════════════════════════════════════════════════

def menu_principale(chat_id, testo="Cosa vuoi fare?"):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👤 Gestisci Clienti", callback_data="menu:clienti"),
        InlineKeyboardButton("✍️ Crea Contenuto", callback_data="menu:crea"),
        InlineKeyboardButton("📊 Analisi Settore", callback_data="menu:analisi"),
        InlineKeyboardButton("📅 Piano Editoriale", callback_data="menu:piano"),
        InlineKeyboardButton("💡 Chiedi Consiglio", callback_data="menu:consiglio"),
    )
    bot.send_message(chat_id, testo, reply_markup=kb)


@bot.message_handler(commands=["start", "menu"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "👋 *Benvenuto nel Sistema Agenti per Contenuti Social*\n\n"
        "Gestisco i tuoi clienti, genero post ottimizzati con AI, "
        "analizzo il settore e creo piani editoriali.\n\n"
        "Seleziona un'opzione:",
        parse_mode="Markdown",
    )
    menu_principale(msg.chat.id)


# ═══════════════════════════════════════════════════════════════
# GESTIONE CLIENTI
# ═══════════════════════════════════════════════════════════════

def schermata_clienti(chat_id):
    clienti = storage.get_clienti(chat_id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ Nuovo Cliente", callback_data="cliente:nuovo"))
    if clienti:
        for nome in clienti:
            kb.add(InlineKeyboardButton(f"👤 {nome}", callback_data=f"cliente:vedi:{nome}"))
    kb.add(InlineKeyboardButton("🔙 Menu", callback_data="menu:home"))
    testo = "👥 *I tuoi clienti:*" if clienti else "Nessun cliente ancora."
    bot.send_message(chat_id, testo, reply_markup=kb, parse_mode="Markdown")


def schermata_dettaglio_cliente(chat_id, nome):
    c = storage.get_cliente(chat_id, nome)
    testo = (
        f"👤 *{nome}*\n\n"
        f"🏢 Settore: {c.get('settore', '—')}\n"
        f"🎯 Target: {c.get('target', '—')}\n"
        f"🗣 Tono: {c.get('tono', '—')}\n"
        f"📱 Piattaforme: {', '.join(c.get('piattaforme', []))}\n"
        f"🎪 Obiettivi: {c.get('obiettivi', '—')}\n"
        f"📌 Argomenti pillar: {c.get('pillar', '—')}\n"
        f"📆 Frequenza: {c.get('frequenza', '—')}"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✍️ Crea Post", callback_data=f"crea:cliente:{nome}"),
        InlineKeyboardButton("📊 Analisi", callback_data=f"analisi:cliente:{nome}"),
        InlineKeyboardButton("📅 Piano", callback_data=f"piano:cliente:{nome}"),
        InlineKeyboardButton("🗑 Elimina", callback_data=f"cliente:elimina:{nome}"),
        InlineKeyboardButton("🔙 Clienti", callback_data="menu:clienti"),
    )
    bot.send_message(chat_id, testo, reply_markup=kb, parse_mode="Markdown")


# ─── WIZARD NUOVO CLIENTE ────────────────────────────────────────────────────

WIZARD_STEPS = [
    ("nome",        "Come si chiama il cliente o il brand?"),
    ("settore",     "In che settore opera? (es. formazione, consulenza, e-commerce, ecc.)"),
    ("target",      "Descrivi il target: chi sono, che età hanno, qual è il loro problema principale?"),
    ("obiettivi",   "Qual è l'obiettivo principale sui social?\n(es. aumentare follower, vendere prodotti, generare contatti)"),
    ("pillar",      "Quali sono i 3-5 argomenti principali su cui comunicare?\n(es. diritto amministrativo, Excel, metodo di studio)"),
    ("frequenza",   "Con che frequenza vuoi pubblicare?\n(es. 3 volte a settimana)"),
    ("esempio_post","Hai un esempio di post che ti piace? Incollalo qui.\n(scrivi 'salta' per passare oltre)"),
]

TONI = [
    ("accessibile",    "Accessibile e diretto"),
    ("professionale",  "Professionale e formale"),
    ("motivazionale",  "Energico e motivazionale"),
    ("tecnico",        "Tecnico ed autorevole"),
]

PIATTAFORME_LISTA = ["Facebook", "LinkedIn", "Instagram", "X (Twitter)"]


def avvia_wizard_cliente(chat_id):
    sessioni[chat_id] = {"step": "wizard_cliente", "dati": {}, "wizard_idx": 0}
    domanda = WIZARD_STEPS[0][1]
    bot.send_message(chat_id, f"➕ *Nuovo Cliente*\n\n{domanda}", parse_mode="Markdown")


def wizard_cliente_avanti(chat_id, risposta):
    stato = sessioni.get(chat_id, {})
    dati = stato.get("dati", {})
    idx = stato.get("wizard_idx", 0)

    campo, _ = WIZARD_STEPS[idx]
    dati[campo] = risposta if risposta.lower() != "salta" else ""
    idx += 1
    stato["dati"] = dati
    stato["wizard_idx"] = idx
    sessioni[chat_id] = stato

    if idx < len(WIZARD_STEPS):
        bot.send_message(chat_id, WIZARD_STEPS[idx][1])
    else:
        # Chiedi tono
        stato["step"] = "wizard_tono"
        sessioni[chat_id] = stato
        kb = InlineKeyboardMarkup(row_width=1)
        for key, label in TONI:
            kb.add(InlineKeyboardButton(label, callback_data=f"wizard_tono:{key}"))
        bot.send_message(chat_id, "Che tono di voce deve avere la comunicazione?", reply_markup=kb)


def wizard_scegli_tono(chat_id, tono):
    stato = sessioni.get(chat_id, {})
    stato["dati"]["tono"] = tono
    stato["step"] = "wizard_piattaforme"
    stato["dati"]["piattaforme"] = []
    sessioni[chat_id] = stato
    _mostra_scelta_piattaforme(chat_id)


def _mostra_scelta_piattaforme(chat_id):
    stato = sessioni.get(chat_id, {})
    selezionate = stato.get("dati", {}).get("piattaforme", [])
    kb = InlineKeyboardMarkup(row_width=2)
    for p in PIATTAFORME_LISTA:
        check = "✅ " if p in selezionate else ""
        kb.add(InlineKeyboardButton(f"{check}{p}", callback_data=f"wizard_piatt:{p}"))
    kb.add(InlineKeyboardButton("✔️ Conferma selezione", callback_data="wizard_piatt:conferma"))
    bot.send_message(
        chat_id,
        f"Su quali piattaforme pubblichiamo?\n_(selezionate: {', '.join(selezionate) or 'nessuna'})_",
        reply_markup=kb,
        parse_mode="Markdown",
    )


def wizard_conferma_cliente(chat_id):
    stato = sessioni.get(chat_id, {})
    dati = stato.get("dati", {})
    nome = dati.get("nome", "Cliente")

    storage.salva_cliente(chat_id, nome, dati)
    sessioni.pop(chat_id, None)

    testo = (
        f"✅ *Cliente {nome} salvato!*\n\n"
        f"🏢 Settore: {dati.get('settore')}\n"
        f"🎯 Target: {dati.get('target')}\n"
        f"🗣 Tono: {dati.get('tono')}\n"
        f"📱 Piattaforme: {', '.join(dati.get('piattaforme', []))}\n\n"
        "Ora puoi creare i primi contenuti!"
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✍️ Crea Post", callback_data=f"crea:cliente:{nome}"),
        InlineKeyboardButton("📊 Analisi Settore", callback_data=f"analisi:cliente:{nome}"),
    )
    bot.send_message(chat_id, testo, reply_markup=kb, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
# CREA CONTENUTO
# ═══════════════════════════════════════════════════════════════

def schermata_scegli_cliente(chat_id, azione):
    clienti = storage.get_clienti(chat_id)
    if not clienti:
        bot.send_message(chat_id, "Nessun cliente. Usa prima 👤 Gestisci Clienti.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for nome in clienti:
        kb.add(InlineKeyboardButton(f"👤 {nome}", callback_data=f"{azione}:cliente:{nome}"))
    kb.add(InlineKeyboardButton("🔙 Menu", callback_data="menu:home"))
    bot.send_message(chat_id, "Per quale cliente?", reply_markup=kb)


def schermata_scegli_tipo_post(chat_id, nome_cliente):
    sessioni[chat_id] = {"step": "scegli_tipo_post", "cliente": nome_cliente}
    kb = InlineKeyboardMarkup(row_width=2)
    for key, info in agenti.TIPI_POST.items():
        kb.add(InlineKeyboardButton(info["label"], callback_data=f"tipo_post:{key}"))
    kb.add(InlineKeyboardButton("🔙 Indietro", callback_data="menu:crea"))
    bot.send_message(
        chat_id,
        f"✍️ *Crea contenuto per {nome_cliente}*\n\nChe tipo di post vuoi creare?",
        reply_markup=kb,
        parse_mode="Markdown",
    )


def chiedi_argomento_post(chat_id, tipo_key):
    stato = sessioni.get(chat_id, {})
    stato["tipo_post"] = tipo_key
    stato["step"] = "inserisci_argomento"
    sessioni[chat_id] = stato
    tipo = agenti.TIPI_POST[tipo_key]
    bot.send_message(
        chat_id,
        f"Tipo scelto: *{tipo['label']}*\n\n"
        "Descrivi l'argomento del post.\n"
        "Puoi incollare un testo, un paragrafo di un documento, un concetto da spiegare "
        "o anche solo una parola chiave:",
        parse_mode="Markdown",
    )


def genera_e_mostra_posts(chat_id, argomento):
    stato = sessioni.get(chat_id, {})
    nome = stato.get("cliente", "")
    tipo_key = stato.get("tipo_post", "pillola")
    cliente = storage.get_cliente(chat_id, nome)
    cliente["nome"] = nome

    msg = bot.send_message(chat_id, "⏳ Sto generando i post, un momento...")

    posts = agenti.genera_posts(cliente, tipo_key, argomento, n=3)
    bozze[chat_id] = posts
    sessioni.pop(chat_id, None)

    bot.delete_message(chat_id, msg.message_id)
    bot.send_message(
        chat_id,
        f"✅ *3 varianti generate per {nome}*\n\nScegli cosa fare con ognuna:",
        parse_mode="Markdown",
    )

    for i, post in enumerate(posts):
        bot.send_message(
            chat_id,
            f"📝 *Variante {i + 1}*\n\n{post['testo']}",
            reply_markup=_kb_post(i),
            parse_mode="Markdown",
        )


def _kb_post(idx):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("✅ Approva", callback_data=f"post:approva:{idx}"),
        InlineKeyboardButton("🔄 Rigenera", callback_data=f"post:rigenera:{idx}"),
        InlineKeyboardButton("❌ Scarta", callback_data=f"post:scarta:{idx}"),
        InlineKeyboardButton("✏️ Modifica", callback_data=f"post:modifica:{idx}"),
    )
    return kb


# ═══════════════════════════════════════════════════════════════
# ANALISI SETTORE
# ═══════════════════════════════════════════════════════════════

def avvia_analisi(chat_id, nome_cliente):
    cliente = storage.get_cliente(chat_id, nome_cliente)
    cliente["nome"] = nome_cliente
    msg = bot.send_message(chat_id, f"🔍 Analizzo il settore per *{nome_cliente}*...\n_(può richiedere 20-30 secondi)_", parse_mode="Markdown")
    analisi = agenti.analisi_settore(cliente)
    bot.delete_message(chat_id, msg.message_id)

    # Invia in blocchi se troppo lungo
    _invia_testo_lungo(chat_id, f"📊 *Analisi Settore — {nome_cliente}*\n\n{analisi}")

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✍️ Crea Post", callback_data=f"crea:cliente:{nome_cliente}"),
        InlineKeyboardButton("📅 Piano Editoriale", callback_data=f"piano:cliente:{nome_cliente}"),
        InlineKeyboardButton("🔙 Menu", callback_data="menu:home"),
    )
    bot.send_message(chat_id, "Cosa vuoi fare ora?", reply_markup=kb)


# ═══════════════════════════════════════════════════════════════
# PIANO EDITORIALE
# ═══════════════════════════════════════════════════════════════

def avvia_piano(chat_id, nome_cliente):
    sessioni[chat_id] = {"step": "scegli_settimane_piano", "cliente": nome_cliente}
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("1 settimana", callback_data="piano:settimane:1"),
        InlineKeyboardButton("2 settimane", callback_data="piano:settimane:2"),
        InlineKeyboardButton("4 settimane", callback_data="piano:settimane:4"),
    )
    bot.send_message(chat_id, f"📅 Piano editoriale per *{nome_cliente}*\n\nPer quanto tempo?", reply_markup=kb, parse_mode="Markdown")


def genera_piano(chat_id, nome_cliente, settimane):
    cliente = storage.get_cliente(chat_id, nome_cliente)
    cliente["nome"] = nome_cliente
    msg = bot.send_message(chat_id, f"⏳ Creo il piano editoriale ({settimane} sett.)...")
    piano = agenti.piano_editoriale(cliente, settimane)
    bot.delete_message(chat_id, msg.message_id)
    _invia_testo_lungo(chat_id, f"📅 *Piano Editoriale — {nome_cliente}*\n\n{piano}")

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✍️ Crea un Post dal Piano", callback_data=f"crea:cliente:{nome_cliente}"),
        InlineKeyboardButton("🔙 Menu", callback_data="menu:home"),
    )
    bot.send_message(chat_id, "Vuoi creare subito uno dei post?", reply_markup=kb)


# ═══════════════════════════════════════════════════════════════
# CONSIGLIO MARKETING
# ═══════════════════════════════════════════════════════════════

def avvia_consiglio(chat_id):
    clienti = storage.get_clienti(chat_id)
    if clienti:
        sessioni[chat_id] = {"step": "scegli_cliente_consiglio"}
        kb = InlineKeyboardMarkup(row_width=1)
        for nome in clienti:
            kb.add(InlineKeyboardButton(f"👤 {nome}", callback_data=f"consiglio:cliente:{nome}"))
        kb.add(InlineKeyboardButton("Domanda generica (senza cliente)", callback_data="consiglio:cliente:_generico"))
        bot.send_message(chat_id, "Per quale cliente vuoi il consiglio?", reply_markup=kb)
    else:
        sessioni[chat_id] = {"step": "inserisci_consiglio", "cliente": "_generico"}
        bot.send_message(chat_id, "💡 Fai la tua domanda al content strategist:")


def risposta_consiglio(chat_id, domanda):
    stato = sessioni.get(chat_id, {})
    nome = stato.get("cliente", "_generico")

    if nome == "_generico":
        cliente = {"nome": "brand generico", "settore": "", "target": ""}
    else:
        cliente = storage.get_cliente(chat_id, nome)
        cliente["nome"] = nome

    msg = bot.send_message(chat_id, "💭 Un momento...")
    risposta = agenti.consiglio_marketing(domanda, cliente)
    bot.delete_message(chat_id, msg.message_id)
    bot.send_message(chat_id, f"💡 *Consiglio*\n\n{risposta}", parse_mode="Markdown")
    sessioni.pop(chat_id, None)
    menu_principale(chat_id)


# ═══════════════════════════════════════════════════════════════
# HANDLER MESSAGGI TESTO
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(content_types=["text"])
def gestisci_testo(msg):
    cid = msg.chat.id
    testo = msg.text.strip()
    stato = sessioni.get(cid, {})
    step = stato.get("step", "")

    if step == "wizard_cliente":
        wizard_cliente_avanti(cid, testo)

    elif step == "inserisci_argomento":
        genera_e_mostra_posts(cid, testo)

    elif step == "inserisci_consiglio":
        risposta_consiglio(cid, testo)

    elif step == "modifica_post":
        idx = stato.get("idx_modifica", 0)
        nome = stato.get("cliente", "")
        posts = bozze.get(cid, [])
        cliente = storage.get_cliente(cid, nome)
        cliente["nome"] = nome

        msg_wait = bot.send_message(cid, "⏳ Applico le modifiche...")
        post_orig = posts[idx]["testo"] if idx < len(posts) else ""
        nuovo_testo = agenti.migliora_post(post_orig, testo, cliente)
        bot.delete_message(cid, msg_wait.message_id)

        if idx < len(posts):
            posts[idx]["testo"] = nuovo_testo
            bozze[cid] = posts

        sessioni.pop(cid, None)
        bot.send_message(
            cid,
            f"✏️ *Variante {idx + 1} aggiornata*\n\n{nuovo_testo}",
            reply_markup=_kb_post(idx),
            parse_mode="Markdown",
        )

    else:
        menu_principale(cid, "Usa il menu per navigare:")


# ═══════════════════════════════════════════════════════════════
# HANDLER CALLBACK
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def gestisci_callback(call):
    cid = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    # ─── MENU ────────────────────────────────────────────────
    if data == "menu:home":
        menu_principale(cid)

    elif data == "menu:clienti":
        schermata_clienti(cid)

    elif data == "menu:crea":
        schermata_scegli_cliente(cid, "crea")

    elif data == "menu:analisi":
        schermata_scegli_cliente(cid, "analisi")

    elif data == "menu:piano":
        schermata_scegli_cliente(cid, "piano")

    elif data == "menu:consiglio":
        avvia_consiglio(cid)

    # ─── CLIENTE ─────────────────────────────────────────────
    elif data == "cliente:nuovo":
        avvia_wizard_cliente(cid)

    elif data.startswith("cliente:vedi:"):
        nome = data.split(":", 2)[2]
        schermata_dettaglio_cliente(cid, nome)

    elif data.startswith("cliente:elimina:"):
        nome = data.split(":", 2)[2]
        storage.elimina_cliente(cid, nome)
        bot.edit_message_text(f"🗑 Cliente *{nome}* eliminato.", cid, call.message.message_id, parse_mode="Markdown")
        schermata_clienti(cid)

    # ─── WIZARD ──────────────────────────────────────────────
    elif data.startswith("wizard_tono:"):
        tono = data.split(":", 1)[1]
        wizard_scegli_tono(cid, tono)

    elif data.startswith("wizard_piatt:"):
        val = data.split(":", 1)[1]
        stato = sessioni.get(cid, {})
        if val == "conferma":
            if not stato.get("dati", {}).get("piattaforme"):
                bot.answer_callback_query(call.id, "Seleziona almeno una piattaforma!", show_alert=True)
                return
            wizard_conferma_cliente(cid)
        else:
            piatt = stato.get("dati", {}).setdefault("piattaforme", [])
            if val in piatt:
                piatt.remove(val)
            else:
                piatt.append(val)
            sessioni[cid] = stato
            _mostra_scelta_piattaforme(cid)

    # ─── CREA CONTENUTO ──────────────────────────────────────
    elif data.startswith("crea:cliente:"):
        nome = data.split(":", 2)[2]
        schermata_scegli_tipo_post(cid, nome)

    elif data.startswith("tipo_post:"):
        tipo_key = data.split(":", 1)[1]
        chiedi_argomento_post(cid, tipo_key)

    # ─── ANALISI ─────────────────────────────────────────────
    elif data.startswith("analisi:cliente:"):
        nome = data.split(":", 2)[2]
        avvia_analisi(cid, nome)

    # ─── PIANO ───────────────────────────────────────────────
    elif data.startswith("piano:cliente:"):
        nome = data.split(":", 2)[2]
        avvia_piano(cid, nome)

    elif data.startswith("piano:settimane:"):
        settimane = int(data.split(":", 2)[2])
        stato = sessioni.get(cid, {})
        nome = stato.get("cliente", "")
        sessioni.pop(cid, None)
        genera_piano(cid, nome, settimane)

    # ─── CONSIGLIO ───────────────────────────────────────────
    elif data.startswith("consiglio:cliente:"):
        nome = data.split(":", 2)[2]
        sessioni[cid] = {"step": "inserisci_consiglio", "cliente": nome}
        bot.send_message(cid, "💡 Fai la tua domanda al content strategist:")

    # ─── POST ────────────────────────────────────────────────
    elif data.startswith("post:approva:"):
        idx = int(data.split(":", 2)[2])
        posts = bozze.get(cid, [])
        if idx < len(posts):
            posts[idx]["stato"] = "approvato"
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=_kb_approvato(idx))
        bot.answer_callback_query(call.id, "✅ Post approvato!")

    elif data.startswith("post:scarta:"):
        idx = int(data.split(":", 2)[2])
        posts = bozze.get(cid, [])
        if idx < len(posts):
            posts[idx]["stato"] = "scartato"
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=_kb_scartato(idx))
        bot.answer_callback_query(call.id, "❌ Post scartato")

    elif data.startswith("post:modifica:"):
        idx = int(data.split(":", 2)[2])
        stato = sessioni.get(cid, {})
        nome_cliente = stato.get("cliente") or (bozze.get(cid, [{}])[0].get("cliente", "") if bozze.get(cid) else "")
        sessioni[cid] = {"step": "modifica_post", "idx_modifica": idx, "cliente": nome_cliente}
        bot.send_message(cid, f"✏️ Dimmi cosa vuoi cambiare nella variante {idx + 1}:\n(es. 'rendi più formale', 'aggiungi un dato statistico', 'cambia il hook')")

    elif data.startswith("post:rigenera:"):
        idx = int(data.split(":", 2)[2])
        posts = bozze.get(cid, [])
        if idx >= len(posts):
            return
        post = posts[idx]
        nome = post.get("cliente", "")
        cliente = storage.get_cliente(cid, nome)
        cliente["nome"] = nome
        msg_wait = bot.send_message(cid, "🔄 Rigenero la variante...")
        nuovi = agenti.genera_posts(cliente, post.get("tipo", "pillola"), post.get("argomento", ""), n=1)
        bot.delete_message(cid, msg_wait.message_id)
        if nuovi:
            posts[idx] = nuovi[0]
            bozze[cid] = posts
            bot.edit_message_text(
                f"🔄 *Variante {idx + 1} rigenerata*\n\n{nuovi[0]['testo']}",
                cid, call.message.message_id,
                reply_markup=_kb_post(idx),
                parse_mode="Markdown",
            )


def _kb_approvato(idx):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Approvato", callback_data=f"noop:{idx}"))
    return kb


def _kb_scartato(idx):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Scartato", callback_data=f"noop:{idx}"))
    return kb


# ═══════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════

def _send_safe(chat_id, testo):
    """Invia testo provando Markdown, fallback a plain text se fallisce."""
    try:
        bot.send_message(chat_id, testo, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, testo)


def _invia_testo_lungo(chat_id, testo, max_len=4000):
    """Divide messaggi lunghi in blocchi compatibili con Telegram."""
    while len(testo) > max_len:
        split_at = testo.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        _send_safe(chat_id, testo[:split_at])
        testo = testo[split_at:].lstrip()
    if testo:
        _send_safe(chat_id, testo)


# ═══════════════════════════════════════════════════════════════
# AVVIO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("✅ Bot avviato. Apri Telegram e scrivi /start")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
