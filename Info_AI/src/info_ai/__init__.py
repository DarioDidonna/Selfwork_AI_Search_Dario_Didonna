import chainlit as cl
from openai import AsyncOpenAI
from tavily import TavilyClient

from info_ai.config import settings
from info_ai import prompts

# Inizializzazione dei client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None


async def search_web(query: str, max_results: int = 5) -> str:
    """Esegue la ricerca Web con Tavily e formatta i risultati in testo semplice con relative fonti."""
    if not tavily_client:
        return "TAVILY_API_KEY non configurata nel file .env."

    try:
        search_fn = cl.make_async(tavily_client.search)
        response = await search_fn(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False
        )
        
        results = response.get("results", [])
        if not results:
            return "Nessun risultato rilevante trovato sul Web."

        formatted_context = []
        for item in results:
            title = item.get("title", "Senza Titolo")
            url = item.get("url", "")
            content = item.get("content", "")
            formatted_context.append(f"Fonte: [{title}]({url})\nContenuto: {content}\n")

        return "\n---\n".join(formatted_context)

    except Exception as e:
        return f"Errore durante la ricerca Web: {str(e)}"


async def ask_llm(system_prompt: str, user_prompt: str) -> str:
    """Funzione di supporto per ottenere risposte sintetiche e complete da OpenAI."""
    response = await openai_client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=settings.TEMPERATURE
    )
    return response.choices[0].message.content or ""


@cl.on_chat_start
async def start():
    await cl.Message(
        content="Ciao! Sono il tuo assistente Info. Elaborerò la tua richiesta in due fasi per fornirti la miglior risposta approfondita.",
        author="assistant"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    user_query = message.content

    # Inizializziamo il messaggio principale che aggiorneremo man mano
    final_msg = cl.Message(content=" **Avvio analisi e ricerca in tempo reale...**\n", author="assistant")
    await final_msg.send()

    # FASE 1: Ricerca Iniziale
    async with cl.Step(name="1. Ricerca Web Iniziale", type="tool") as step1:
        step1.input = user_query
        context_fase1 = await search_web(query=user_query)
        step1.output = context_fase1

    prompt_fase1 = (
        f"Domanda utente: {user_query}\n\n"
        f"Risultati Web Fase 1:\n{context_fase1}\n\n"
        "Fornisci una risposta chiara ed esaustiva citando esplicitamente le fonti (link Markdown) trovate."
    )
    risposta_fase1 = await ask_llm(prompts.SYSTEM_PROMPT, prompt_fase1)

    prompt_riassunto1 = f"Sintetizza in 2-3 punti chiave la seguente risposta:\n\n{risposta_fase1}"
    riassunto1 = await ask_llm("Sei un assistente specializzato in sintesi chiare.", prompt_riassunto1)

    # Aggiornamento progressivo dell'UI
    final_msg.content = (
        "### 📌 1. Risposta Iniziale e Fonti\n"
        f"{risposta_fase1}\n\n"
        "---\n\n"
        "### 📝 Primo Riassunto\n"
        f"{riassunto1}\n\n"
        "---\n\n"
        " *Ricerca di approfondimento in corso...*"
    )
    await final_msg.update()

    # FASE 2: Ricerca di Miglioramento / Approfondimento
    query_approfondimento = f"{user_query} dettagli approfondimenti normative linee guida"
    async with cl.Step(name="2. Ricerca di Approfondimento", type="tool") as step2:
        step2.input = query_approfondimento
        context_fase2 = await search_web(query=query_approfondimento)
        step2.output = context_fase2

    prompt_fase2 = (
        f"Domanda originale: {user_query}\n"
        f"Prima analisi: {riassunto1}\n\n"
        f"Nuovi risultati Web di approfondimento:\n{context_fase2}\n\n"
        "Fornisci un approfondimento dettagliato sugli aspetti non trattati prima, con relative fonti (link Markdown)."
    )
    risposta_fase2 = await ask_llm(prompts.SYSTEM_PROMPT, prompt_fase2)

    prompt_riassunto2 = f"Sintetizza in 2-3 punti chiave questo approfondimento:\n\n{risposta_fase2}"
    riassunto2 = await ask_llm("Sei un assistente specializzato in sintesi chiare.", prompt_riassunto2)

    # Aggiornamento progressivo dell'UI
    final_msg.content = (
        "### 📌 1. Risposta Iniziale e Fonti\n"
        f"{risposta_fase1}\n\n"
        "---\n\n"
        "### 📝 Primo Riassunto\n"
        f"{riassunto1}\n\n"
        "---\n\n"
        "### 🔍 2. Ricerca di Miglioramento e Approfondimento\n"
        f"{risposta_fase2}\n\n"
        "---\n\n"
        "### 📝 Secondo Riassunto (Approfondimento)\n"
        f"{riassunto2}\n\n"
        "---\n\n"
        " *Generazione della risposta finale integrata...*"
    )
    await final_msg.update()

    # FASE 3: Generazione della Sintesi Finale
    prompt_sintesi_finale = (
        f"Domanda dell'utente: {user_query}\n\n"
        f"Sintesi Prima Fase:\n{riassunto1}\n\n"
        f"Sintesi Seconda Fase:\n{riassunto2}\n\n"
        "Crea una RISPOSTA FINALE integrata, fluida, completa ed elegante che risponda in modo definitivo all'utente."
    )
    risposta_finale = await ask_llm(prompts.SYSTEM_PROMPT, prompt_sintesi_finale)

    # Report finale completo
    final_msg.content = (
        "### 📌 1. Risposta Iniziale e Fonti\n"
        f"{risposta_fase1}\n\n"
        "---\n\n"
        "### 📝 Primo Riassunto\n"
        f"{riassunto1}\n\n"
        "---\n\n"
        "### 🔍 2. Ricerca di Miglioramento e Approfondimento\n"
        f"{risposta_fase2}\n\n"
        "---\n\n"
        "### 📝 Secondo Riassunto (Approfondimento)\n"
        f"{riassunto2}\n\n"
        "---\n\n"
        "# 🎯 Risposta Finale Definitiva\n"
        f"{risposta_finale}"
    )
    await final_msg.update()
    user_query = message.content

    # Inizializza il messaggio di output che verrà aggiornato in streaming/fasi
    final_msg = cl.Message(content="", author="assistant")
    await final_msg.send()

    # FASE 1: Ricerca Iniziale
    async with cl.Step(name="1. Ricerca Web Iniziale", type="tool") as step1:
        step1.input = user_query
        context_fase1 = await search_web(query=user_query)
        step1.output = context_fase1

    prompt_fase1 = (
        f"Domanda utente: {user_query}\n\n"
        f"Risultati Web Fase 1:\n{context_fase1}\n\n"
        "Fornisci una risposta chiara ed esaustiva citando esplicitamente le fonti (link Markdown) trovate."
    )
    risposta_fase1 = await ask_llm(prompts.SYSTEM_PROMPT, prompt_fase1)

    prompt_riassunto1 = f"Sintetizza in 2-3 punti chiave la seguente risposta:\n\n{risposta_fase1}"
    riassunto1 = await ask_llm("Sei un assistente specializzato in sintesi chiare.", prompt_riassunto1)

    # FASE 2: Ricerca di Miglioramento / Approfondimento
    query_approfondimento = f"{user_query} dettagli approfondimenti normative linee guida"
    async with cl.Step(name="2. Ricerca di Approfondimento", type="tool") as step2:
        step2.input = query_approfondimento
        context_fase2 = await search_web(query=query_approfondimento)
        step2.output = context_fase2

    prompt_fase2 = (
        f"Domanda originale: {user_query}\n"
        f"Prima analisi: {riassunto1}\n\n"
        f"Nuovi risultati Web di approfondimento:\n{context_fase2}\n\n"
        "Fornisci un approfondimento dettagliato sugli aspetti non trattati prima, con relative fonti (link Markdown)."
    )
    risposta_fase2 = await ask_llm(prompts.SYSTEM_PROMPT, prompt_fase2)

    prompt_riassunto2 = f"Sintetizza in 2-3 punti chiave questo approfondimento:\n\n{risposta_fase2}"
    riassunto2 = await ask_llm("Sei un assistente specializzato in sintesi chiare.", prompt_riassunto2)

    # FASE 3: Generazione del Riassunto Finale Integrato
    prompt_sintesi_finale = (
        f"Domanda dell'utente: {user_query}\n\n"
        f"Sintesi Prima Fase:\n{riassunto1}\n\n"
        f"Sintesi Seconda Fase:\n{riassunto2}\n\n"
        "Crea una RISPOSTA FINALE integrata, fluida, completa ed elegante che risponda in modo definitivo all'utente."
    )
    risposta_finale = await ask_llm(prompts.SYSTEM_PROMPT, prompt_sintesi_finale)

    # COSTRUZIONE DEL REPORT FINALE 
    report_finale = (
        "### 📌 1. Risposta Iniziale e Fonti\n"
        f"{risposta_fase1}\n\n"
        "---\n\n"
        "### 📝 Primo Riassunto\n"
        f"{riassunto1}\n\n"
        "---\n\n"
        "### 🔍 2. Ricerca di Miglioramento e Approfondimento\n"
        f"{risposta_fase2}\n\n"
        "---\n\n"
        "### 📝 Secondo Riassunto (Approfondimento)\n"
        f"{riassunto2}\n\n"
        "---\n\n"
        "# 🎯 Risposta Finale Definitiva\n"
        f"{risposta_finale}"
    )

    final_msg.content = report_finale
    await final_msg.update()