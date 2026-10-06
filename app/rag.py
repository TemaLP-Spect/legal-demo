# app/rag.py
import json
import re
from datetime import datetime
from pathlib import Path
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "qwen2.5:7b"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "legal_documents"
TOP_K = 4
SUMMARIES_FILE = "./summaries.json"

LOCAL_PROMPT = """You are a legal research assistant serving qualified legal practitioners.

REGISTER AND TONE (STRICT):
- Always respond in formal, professional legal English (or the user's selected language).
- The user may speak casually, use slang, or write informally. Do NOT mirror it.
- Never use emojis, exclamation marks, or casual phrasing.
- Open with a professional salutation only when greeting. Otherwise begin with the substance.

CONTENT STANDARDS:
- Answer strictly from the provided context.
- Cite source document name and page number.
- If the context lacks the answer, respond EXACTLY: NODOCS
- Never fabricate case law, statutes, or citations.

STRUCTURE:
- Short paragraphs. Formal prose.
- Close substantive answers with: "This response should be independently verified against the primary source."

Context:
{context}
"""

WEB_PROMPT = """You are a legal research assistant. The user's question was not answered by their uploaded documents. Use the web results below to provide preliminary guidance.

REGISTER: Formal, professional legal English. No casual phrasing.

Begin with: "This information is not present in the uploaded documents. The following is preliminary guidance from publicly available sources, and must be independently verified:"

Cite URLs inline. State clearly that this does not constitute legal advice.

Web results:
{web_context}
"""

SUMMARY_PROMPT = """Summarise this legal document in 3 concise points suitable for a legal practitioner. Identify parties, dates, governing law, and key obligations where present.

Text:
{text}

Professional summary:"""

SMALL_TALK_RE = re.compile(
    r"^(how\s*(are|is)\s*(you|u|it|things|everything)|"
    r"how'?s\s*it\s*going|what'?s\s*up|wassup|watsup|"
    r"how\s*you\s*doing|you\s*(good|ok|okay|alright)|"
    r"hope\s*you'?re\s*(good|well)|"
    r"hoe\s*gaan\s*it|hoe\s*is\s*dit|"
    r"unjani|kunjani|ku\s*njani|o\s*kae|le\s*kae|"
    r"o\s*tsogile|le\s*tsogile|o\s*ka\s*tsoga)[\s!.,?]*$", re.I)

GREETING_RE = re.compile(r"^(hi+|hey+|hello+|yo|sup|howdy|hola|greetings|hallo|hiya|heya|good\s*(day|morning|afternoon|evening)|howzit|howzat|aweh|awe|heita|yebo|yebo\s*sawubona|molo|sawubona|dumela|dumelang|thobela|goeie\s*(dag|more|middag|aand)|sharp|ja|jip|jis|cheers|morning|afternoon|evening|hallo\s*daar)[\s!.,?]*$", re.I)
THANKS_RE = re.compile(r"^(thanks?|thank\s*you|thx|ty|ta|cheers|appreciate\s*it|much\s*appreciated|dankie|baie\s*dankie|enkosi|ngiyabonga|ngiyabonga\s*kakhulu|kea\s*leboha|re\s*a\s*leboga|ke\s*a\s*leboga)[\s!.,?]*$", re.I)
BYE_RE = re.compile(r"^(bye+|goodbye|see\s*ya|later|cya|cheers|totsiens|tot\s*siens|hamba\s*kahle|sala\s*kahle|go\s*well)[\s!.,?]*$", re.I)
ACK_RE = re.compile(r"^(ok+|okay+|k|cool|nice|great|got\s*it|alright|sure|fine|reg|sharp|ja|jip|yebo|eish|yoh|nee|no\s*ways|understood|copy\s*that|roger)[\s!.,?]*$", re.I)
ABOUT_RE = re.compile(r"(what\s*(are|is)\s*(you|this)|who\s*are\s*you|what\s*can\s*you\s*do|what\s*do\s*you\s*do|how\s*do\s*you\s*work|what\s*is\s*this\s*(tool|system|app)|tell\s*me\s*about\s*(yourself|this))", re.I)
DISCLAIMER_RE = re.compile(r"(disclaimer|legal\s*advice|can\s*i\s*rely|is\s*this\s*legal\s*advice|terms|privacy|data\s*protection|popia|gdpr|liability|responsibility)", re.I)

TRANSLATIONS = {
    "English": {
        "morning":   "Good morning. How may I assist you with your legal documents?",
        "afternoon": "Good afternoon. How may I assist you with your legal documents?",
        "evening":   "Good evening. How may I assist you with your legal documents?",
        "thanks":    "You are welcome. Please let me know if you require further assistance.",
        "bye":       "Goodbye. Please verify all information before relying on it.",
        "ack":       "Understood.",
        "short":     "Could you please provide further detail?",
        "about":     "I am a legal research assistant. I help practitioners locate and analyse information within the documents they have uploaded to this system.\n\nI do not provide legal advice. I do not replace the judgment of a qualified legal practitioner. Every answer must be independently verified against the primary source before reliance.\n\nI cite the documents I reference. I flag where information is absent. I do not fabricate case law, statutes, or citations.\n\nFor full details, please consult the Settings section in the sidebar.",
        "disclaimer":"Important information:\n\n1. This system is an assistive research tool. It does not constitute legal advice.\n2. Use of this system does not create an attorney-client relationship.\n3. All outputs must be independently verified.\n4. Your documents remain on your premises.\n5. This system processes personal information in accordance with POPIA.\n\nFull details in the Settings section.",
    },
    "Afrikaans": {
        "morning":   "Goeie more. Hoe kan ek u behulpsaam wees met u regsdokumente?",
        "afternoon": "Goeie middag. Hoe kan ek u behulpsaam wees met u regsdokumente?",
        "evening":   "Goeie naand. Hoe kan ek u behulpsaam wees met u regsdokumente?",
        "thanks":    "U is welkom. Laat my asseblief weet indien u verdere bystand benodig.",
        "bye":       "Totsiens. Verifieer asseblief alle inligting voordat u daarop staatmaak.",
        "ack":       "Verstaan.",
        "short":     "Kan u asseblief meer besonderhede verskaf?",
        "about":     "Ek is 'n regsnavorsingsassistent. Ek help praktisyns om inligting in hul opgelaaide dokumente op te spoor en te ontleed.\n\nEk verskaf nie regsadvies nie. Ek vervang nie die oordeel van 'n gekwalifiseerde regspraktisyn nie. Elke antwoord moet onafhanklik teen die primêre bron geverifieer word.\n\nEk sitateer die dokumente waarna ek verwys. Ek dui aan waar inligting ontbreek. Ek versin nie sake, statute of sitate nie.\n\nVir volle besonderhede, raadpleeg die Instellings-afdeling in die systaaf.",
        "disclaimer":"Belangrike inligting:\n\n1. Hierdie stelsel is 'n bystand-navorsingsinstrument. Dit is nie regsadvies nie.\n2. Gebruik van hierdie stelsel skep nie 'n prokureur-kliënt verhouding nie.\n3. Alle uitsette moet onafhanklik geverifieer word.\n4. U dokumente bly op u perseel.\n5. Hierdie stelsel verwerk persoonlike inligting in ooreenstemming met POPIA.\n\nVolle besonderhede in die Instellings-afdeling.",
    },
    "isiZulu": {
        "morning":   "Sawubona ekuseni. Ngingakusiza kanjani ngemibhalo yakho yezomthetho?",
        "afternoon": "Sawubona emini. Ngingakusiza kanjani ngemibhalo yakho yezomthetho?",
        "evening":   "Sawubona kusihlwa. Ngingakusiza kanjani ngemibhalo yakho yezomthetho?",
        "thanks":    "Wamukelekile. Ngicela ungazise uma udinga usizo olwengeziwe.",
        "bye":       "Hamba kahle. Sicela uqinisekise lonke ulwazi ngaphambi kokulusebenzisa.",
        "ack":       "Ngiqonda.",
        "short":     "Ngicela unikeze imininingwane eyengeziwe?",
        "about":     "Ngiwumsizi wocwaningo lwezomthetho. Ngisiza ochwepheshe ukuthola nokuhlaziya ulwazi emibhalweni abayilayishe.\n\nAnginikezi izeluleko zomthetho. Angigudli isahlulelo somuntu oqeqeshiwe kwezomthetho. Zonke izimpendulo kufanele ziqinisekiswe ngokuzimela.\n\nNgicaphuna imibhalo engiyisebenzisayo. Ngikhombisa lapho ulwazi lungatholakali. Angiqambi amacala, imithetho noma izicaphuno.\n\nUkuze uthole imininingwane ephelele, bheka isigaba sezilungiselelo kusihlukanisi eseceleni.",
        "disclaimer":"Ulwazi olubalulekile:\n\n1. Lolu hlelo luyithuluzi losizo locwaningo. Akusilo iseluleko somthetho.\n2. Ukusebenzisa lolu hlelo akudali ubudlelwano bommeli neklayenti.\n3. Yonke imiphumela kufanele iqinisekiswe ngokuzimela.\n4. Imibhalo yakho ihlala endaweni yakho.\n5. Lolu hlelo lucubungula ulwazi lomuntu siqu ngokuhambisana ne-POPIA.\n\nImininingwane ephelele kusigaba sezilungiselelo.",
    },
    "isiXhosa": {
        "morning":   "Molo ngentsasa. Ndingakunceda njani ngezincwadi zakho zomthetho?",
        "afternoon": "Molo emini. Ndingakunceda njani ngezincwadi zakho zomthetho?",
        "evening":   "Molo ngokuhlwa. Ndingakunceda njani ngezincwadi zakho zomthetho?",
        "thanks":    "Wamkelekile. Nceda undazise ukuba ufuna uncedo olungakumbi.",
        "bye":       "Sala kakuhle. Nceda uqinisekise lonke ulwazi phambi kokulusebenzisa.",
        "ack":       "Ndiyaqonda.",
        "short":     "Nceda unike iinkcukacha ezingakumbi?",
        "about":     "Ndingumncedisi wophando lwezomthetho. Ndinceda iingcali ukufumana nokuhlalutya ulwazi kumaxwebhu eziwafakileyo.\n\nAndiniki iingcebiso zomthetho. Andithathi indawo yomgwebi oqeqeshiweyo. Zonke iimpendulo maziqinisekiswe ngokuzimeleyo.\n\nNdicaphula amaxwebhu endiwasebenzisayo. Ndibonisa apho ulwazi lungafumanekiyo. Andiqambi amatyala, imithetho okanye izicatshulwa.\n\nNgeenkcukacha ezipheleleyo, jonga icandelo leeSetingi kwicala lasekhohlo.",
        "disclaimer":"Ulwazi olubalulekileyo:\n\n1. Le nkqubo sisixhobo soncedo lophando. Ayisosicelo sengcebiso yomthetho.\n2. Ukusebenzisa le nkqubo akudali ubudlelwane begqwetha nomxhasi.\n3. Zonke iziphumo maziqinisekiswe ngokuzimeleyo.\n4. Amaxwebhu akho ahlala kwindawo yakho.\n5. Le nkqubo isebenza ngolwazi lobuqu ngokuhambelana ne-POPIA.\n\nIinkcukacha ezipheleleyo kwicandelo leeSetingi.",
    },
    "Sesotho": {
        "morning":   "Dumela hoseng. Nka o thusa jwang ka ditokomane tsa hao tsa molao?",
        "afternoon": "Dumela motsheare. Nka o thusa jwang ka ditokomane tsa hao tsa molao?",
        "evening":   "Dumela mantsiboya. Nka o thusa jwang ka ditokomane tsa hao tsa molao?",
        "thanks":    "O amohelehile. Ka kopo, ntsebise haeba o hloka thuso e eketsehileng.",
        "bye":       "Sala hantle. Ka kopo netefatsa tlhahisoleseding yohle pele o e sebedisa.",
        "ack":       "Ke utlwisisa.",
        "short":     "Ka kopo fana ka dintlha tse eketsehileng?",
        "about":     "Ke mothusi wa dipatlisiso tsa molao. Ke thusa ditsebi ho fumana le ho sekaseka tlhahisoleseding ka har'a ditokomane tseo di kentsweng.\n\nHa ke fane ka keletso ya molao. Ha ke nke sebaka sa moahlodi ya tshwanelehileng. Dikarabo tsohle di tlameha ho netefatswa ka boithaopo.\n\nKe qotsa ditokomane tseo ke di sebelisang. Ke bontsha moo tlhahisoleseding e leng siyo. Ha ke iqe mabaka, melao kapa diqotsulo.\n\nBakeng sa dintlha tse felletseng, sheba karolo ya Diseting lebopong.",
        "disclaimer":"Tlhahisoleseding ya bohlokwa:\n\n1. Sistimi ena ke sesebediswa sa thuso ya dipatlisiso. Ha se keletso ya molao.\n2. Tshebediso ya sistimi ena ha e thehe kamano ya akhente le moreki.\n3. Diphetho tsohle di tlameha ho netefatswa ka boithaopo.\n4. Ditokomane tsa hao di dula sebakeng sa hao.\n5. Sistimi ena e sebetsa tlhahisoleseding ya botho ho latela POPIA.\n\nDintlha tse felletseng karolong ya Diseting.",
    },
    "Setswana": {
        "morning":   "Dumela mo mosong. Nka go thusa jang ka dikwalo tsa gago tsa molao?",
        "afternoon": "Dumela mo maitseboeng. Nka go thusa jang ka dikwalo tsa gago tsa molao?",
        "evening":   "Dumela mo maitseboeng. Nka go thusa jang ka dikwalo tsa gago tsa molao?",
        "thanks":    "O amogelesegile. Tsweetswee nkitsise fa o tlhoka thuso e e oketsegileng.",
        "bye":       "Sala sentle. Tsweetswee netefatsa tshedimosetso yotlhe pele o e dirisa.",
        "ack":       "Ke a tlhaloganya.",
        "short":     "Tsweetswee naya dintlha tse di oketsegileng?",
        "about":     "Ke mothusi wa patlisiso ya molao. Ke thusa baitseanape go bona le go sekaseka tshedimosetso mo dikwalong tse ba di tsenyileng.\n\nGa ke fe kgakololo ya molao. Ga ke tseye sebaka sa moatlhodi yo o tshwanelegileng. Dikarabo tsotlhe di tshwanetse go netefadiwa ka boithaopo.\n\nKe nopola dikwalo tse ke di dirisang. Ke supa kwa tshedimosetso e seyo. Ga ke ipe mabaka, melao kgotsa dinopolo.\n\nGo bona dintlha tse di tletseng, leba karolo ya Diseting kwa letlhakoreng.",
        "disclaimer":"Tshedimosetso ya botlhokwa:\n\n1. Sistimi eno ke sedirisiwa sa thuso ya patlisiso. Ga se kgakololo ya molao.\n2. Tiriso ya sistimi eno ga e bope kamano ya mmueledi le moreki.\n3. Diphelelo tsotlhe di tshwanetse go netefadiwa ka boithaopo.\n4. Dikwalo tsa gago di nna mo lefelong la gago.\n5. Sistimi eno e dira tshedimosetso ya botho go ya ka POPIA.\n\nDintlha tse di tletseng mo karolong ya Diseting.",
    },
    "Sepedi": {
        "morning":   "Thobela. Nka go thuša bjang ka dikwalwa tša gago tša molao?",
        "afternoon": "Thobela. Nka go thuša bjang ka dikwalwa tša gago tša molao?",
        "evening":   "Thobela. Nka go thuša bjang ka dikwalwa tša gago tša molao?",
        "thanks":    "O amogetšwe. Hle ntsebiše ge o nyaka thušo ye nngwe.",
        "bye":       "Šala gabotse. Hle netefatša tshedimošo ka moka pele o e šomiša.",
        "ack":       "Ke a kwešiša.",
        "short":     "Hle fa ka dintlha tše dingwe?",
        "about":     "Ke mothuši wa dinyakišišo tša molao. Ke thuša ditsebi go hwetša le go sekaseka tshedimošo ka gare ga dikwalwa tše ba di lokeleditšego.\n\nGa ke fe keletšo ya molao. Ga ke tšee sebaka sa kahlolo ya setsebi sa molao. Dikarabo ka moka di swanetše go netefatšwa ka boithaopo.\n\nKe tsopola dikwalwa tše ke di šomišago. Ke laetša mo tshedimošo e sego gona. Ga ke ipe mabaka, melao goba ditsopotlo.\n\nGo bona dintlha ka botlalo, lebelela karolo ya Diseting ka lehlakoreng.",
        "disclaimer":"Tshedimošo ya bohlokwa:\n\n1. Sisteme ye ke sedirišwa sa thušo ya dinyakišišo. Ga se keletšo ya molao.\n2. Tirišo ya sisteme ye ga e hlole kamano ya mmueledi le moreki.\n3. Diphetho ka moka di swanetše go netefatšwa ka boithaopo.\n4. Dikwalwa tša gago di dula lefelong la gago.\n5. Sisteme ye e šoma tshedimošo ya motho ka go latela POPIA.\n\nDintlha ka botlalo karolong ya Diseting.",
    },
}

def _t(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, TRANSLATIONS["English"][key])

def _greeting(language="English"):
    h = datetime.now().hour
    if 5 <= h < 12:
        return _t(language, "morning")
    if 12 <= h < 17:
        return _t(language, "afternoon")
    return _t(language, "evening")

_RESPONSE_CACHE = {}

def _strip_greetings(text):
    """Remove leading greeting words so 'hi, how are you' becomes 'how are you'."""
    t = text.strip().lower()
    # Strip common greeting prefixes
    prefixes = ["hi", "hey", "hello", "yo", "sup", "howzit", "howzat",
                "aweh", "awe", "heita", "yebo", "molo", "sawubona",
                "dumela", "dumelang", "thobela", "hallo", "hiya", "heya",
                "morning", "afternoon", "evening", "good morning",
                "good afternoon", "good evening", "good day"]
    changed = True
    while changed:
        changed = False
        for p in prefixes:
            if t.startswith(p):
                rest = t[len(p):].lstrip(" ,.!-—:;?")
                if rest:
                    t = rest
                    changed = True
                    break
    return t

def _fast_reply(question, language="English"):
    q = question.strip()
    stripped = _strip_greetings(q)
    if stripped != q.strip().lower() and stripped:
        # Leading greeting detected — check if the remainder is small talk
        if SMALL_TALK_RE.match(stripped):
            return "I am well. Thank you for asking. How may I assist you with your documents?"
        if not stripped:
            return _greeting(language)
    if not q:
        return _greeting(language)
    if SMALL_TALK_RE.match(q):
        return "I am well. Thank you for asking. How may I assist you with your documents?"
    if GREETING_RE.match(q):
        return _greeting(language)
    if THANKS_RE.match(q):
        return _t(language, "thanks")
    if BYE_RE.match(q):
        return _t(language, "bye")
    if ACK_RE.match(q):
        return _t(language, "ack")
    if ABOUT_RE.search(q):
        return _t(language, "about")
    if DISCLAIMER_RE.search(q):
        return _t(language, "disclaimer")
    if len(q) < 3:
        return _t(language, "short")
    return None

def _has_documents():
    try:
        vs = get_vector_store()
        data = vs.get()
        return len(data.get("ids", []) or []) > 0
    except Exception:
        return False

def get_vector_store():
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(collection_name=COLLECTION_NAME, embedding_function=embeddings, persist_directory=CHROMA_DIR)

def get_llm():
    return ChatOllama(model=LLM_MODEL, base_url=OLLAMA_URL, temperature=0.15)

def build_context(chunks):
    parts = []
    for i, c in enumerate(chunks, 1):
        src = c.metadata.get("source", "unknown")
        pg = c.metadata.get("page", "?")
        parts.append(f"[Source {i}: {src}, page {pg}]\n{c.page_content}")
    return "\n\n".join(parts)

def web_search(query, max_results=5):
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return []
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")})
        return results
    except Exception as e:
        print(f"Web search failed: {e}")
        return []

def _is_not_found(answer):
    a = answer.strip().lower()
    triggers = ["nodocs", "i don't have enough information", "i do not have enough information",
                "not in the context", "not in your documents", "cannot find", "could not find"]
    return any(t in a for t in triggers)

def _build_sources(chunks):
    """Return source list with filename, page, and the actual chunk text."""
    sources = []
    for c in chunks:
        src_path = c.metadata.get("source", "unknown")
        # Strip full path ??? keep only the filename
        filename = src_path.replace("\\", "/").split("/")[-1]
        sources.append({
            "source": src_path,
            "filename": filename,
            "page": c.metadata.get("page", "?"),
            "snippet": c.page_content.strip()[:800],  # cap length
        })
    return sources

def ask(question, language="English", use_web_fallback=False):
    fast = _fast_reply(question, language)
    if fast is not None:
        return {"answer": fast, "sources": [], "used_web": False, "web_sources": []}

    if not _has_documents():
        return {
            "answer": "No documents are currently loaded. Please upload one or more documents in the sidebar before asking a question.",
            "sources": [], "used_web": False, "web_sources": [],
        }

    cache_key = f"{language}|{question.strip().lower()}"
    if cache_key in _RESPONSE_CACHE:
        return _RESPONSE_CACHE[cache_key]

    vs = get_vector_store()
    chunks = vs.similarity_search(question, k=TOP_K)
    context = build_context(chunks) if chunks else ""

    system = LOCAL_PROMPT
    if language != "English":
        system += f"\n\nRespond in {language}. Maintain a formal legal register throughout."

    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{question}")])
    llm = get_llm()
    response = (prompt | llm).invoke({"context": context, "question": question})
    answer = response.content.strip()

    sources = _build_sources(chunks)

    if use_web_fallback and _is_not_found(answer):
        web_results = web_search(question)
        if web_results:
            web_context = "\n\n".join(f"[{r['title']}]({r['url']})\n{r['snippet']}" for r in web_results)
            web_prompt = ChatPromptTemplate.from_messages([("system", WEB_PROMPT), ("human", "{question}")])
            web_response = (web_prompt | llm).invoke({"web_context": web_context, "question": question})
            result = {"answer": web_response.content, "sources": [], "used_web": True,
                      "web_sources": [{"title": r["title"], "url": r["url"]} for r in web_results]}
            _RESPONSE_CACHE[cache_key] = result
            return result

    if _is_not_found(answer):
        result = {"answer": "The uploaded documents do not contain sufficient information to answer this query. Please consult the primary source or a qualified legal practitioner.",
                  "sources": sources, "used_web": False, "web_sources": []}
    else:
        result = {"answer": answer, "sources": sources, "used_web": False, "web_sources": []}

    _RESPONSE_CACHE[cache_key] = result
    return result

def summarize_text(text, max_chars=3000):
    prompt = ChatPromptTemplate.from_messages([("system", SUMMARY_PROMPT), ("human", "{text}")])
    return (prompt | get_llm()).invoke({"text": text[:max_chars]}).content.strip()

def load_summaries():
    p = Path(SUMMARIES_FILE)
    return json.loads(p.read_text()) if p.exists() else {}

def save_summaries(data):
    Path(SUMMARIES_FILE).write_text(json.dumps(data, indent=2))

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is this document about?"
    print(ask(q)["answer"])
