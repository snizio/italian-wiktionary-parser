from xml.etree.ElementTree import iterparse
import re
from tqdm import tqdm
import pandas as pd
import json
import sys



def prepend_ns(s):
    return '{http://www.mediawiki.org/xml/export-0.10/}' + s # automate the ns find

def lang_check(line, lemma):
    line = line.replace(" ", "") # eliminiamo gli spazi per conformità
    match =  re.search(lang_pattern, line) # lingua
    if match != None:
        lang = match.group(1)
        if lang == None:
            lang = match.group(2)
        if lang == "it":
            parsed_dict[lemma] = {"meta": {"ipa": [], "sill": [], "etim": ""}, "meanings": {}}
            return True
        else:
            return False
    else:
        return False
    
def pron_check(line):
    match = re.search(pron_pattern, line)
    if match != None:
        return True

def get_ipa(line, lemma):
    match = re.search(ipa_pattern, line) # ipa
    if match != None:
        ipa = match.group(1)
        parsed_dict[lemma]["meta"]["ipa"].append(ipa)
        return True
    else:
        return False
    
def sill_check(line):
    """To check if the sill token is present in the line"""
    match = re.search(sill_pattern, line) # sill
    if match != None:
        return True
    
def get_sill(line, lemma):
    if line[0] == ";":
        parsed_dict[lemma]["meta"]["sill"] = line[1:].replace(" ", "").split("|")
        return True
    else:
        return False

def pos_check(line):
    match = re.search(pos_pattern, line) # pos
    if match != None:
        return True
    else:
        return False

def unk_pos(lemma):
    pos = "unk" # opzione di default (poichè il formato non è consistente)
    parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":""}
    return pos

def check_pos(lemma, line, i_pos, current_pos):
    match = re.search(pos_pattern, line) # pos
    if match != None:
        pos = match.group(1) + f"_{i_pos}"
        if pos != current_pos and pos != f"Varie lingue_{i_pos}":
            current_pos = pos
            parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":""}
            if "unk" in parsed_dict[lemma]["meanings"]:
                del parsed_dict[lemma]["meanings"]["unk"] # se dopo aver messo unk si trova una pos si elimina unk
        return pos
    else:
        return current_pos
    
def morpho_check(line, lemma, pos):
    match = re.search(morpho_pattern, line) # informazioni morfologiche
    if match != None:
        morpho = match.group(1).lstrip() # talvolta c'è uno spazio all'inizio
        parsed_dict[lemma]["meanings"][pos]["morpho"] = morpho
        return True

def etim_check(line):
    match = re.search(etim_pattern, line)
    if match != None:
        return True

def get_etim(line, lemma):
    cleaned_line = re.sub("{{Pn}}", lemma, line)
    cleaned_line = re.sub(lang_pointer_pattern, lambda m: lang_dict.get(m.group(1), m.group(0)), cleaned_line)
    cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub("{{.*?}}", "", cleaned_line)
    cleaned_line = re.sub(glossa_pattern, lambda m: m.group(1) if m.group(2) is None else m.group(2), cleaned_line) # rimuove [[...]] o [[...|...]] tenendo la prima parola
    cleaned_line = re.sub("\[\[\w.*?\]\]", "", cleaned_line)
    cleaned_line = re.sub(quote_marks_pattern, "", cleaned_line)
    cleaned_line = cleaned_line.lstrip()
    if parsed_dict[lemma]["meta"]["etim"] == "":
        parsed_dict[lemma]["meta"]["etim"] += cleaned_line
    else:
        parsed_dict[lemma]["meta"]["etim"] += "\n"+cleaned_line
    
def glossa_check(line, lemma, pos):
    line = line[1:]
    cleaned_line = re.sub("{{Pn}}", lemma, line)
    cleaned_line = re.sub(lang_pointer_pattern, lambda m: lang_dict.get(m.group(1), m.group(0)), cleaned_line)
    cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub("{{.*?}}", "", cleaned_line)
    cleaned_line = re.sub(glossa_pattern, lambda m: m.group(1) if m.group(2) is None else m.group(2), cleaned_line) # rimuove [[...]] o [[...|...]] tenendo la prima parola
    cleaned_line = re.sub("\[\[\w.*?\]\]", "", cleaned_line)
    cleaned_line = re.sub(quote_marks_pattern, "", cleaned_line)
    cleaned_line = cleaned_line.lstrip()
    if parsed_dict[lemma]["meanings"][pos]["glossa"] == "":
        parsed_dict[lemma]["meanings"][pos]["glossa"] += cleaned_line
    else:
        parsed_dict[lemma]["meanings"][pos]["glossa"] += "\n"+cleaned_line


def main(xml_dump_path):

    context = iterparse(xml_dump_path, events=("start", "end"))

    for event, elem in tqdm(context, desc="Parsing XML", unit=" elements"):
        if event == "end":
            if prepend_ns("page") == elem.tag:
                lemma = elem.find(prepend_ns("title"))
                if lemma != None:
                    lemma = str(lemma.text)
                    if ":" in lemma or lemma in ["Pagina principale", "Pagina principale/Categorie"]:
                        continue
                    revision = elem.find(prepend_ns("revision"))
                    glossa = revision.find(prepend_ns("text")).text
                    current_pos = ""
                    lang_found = False
                    sill_flag = False
                    unk_pos_flag = False
                    elenco_flag = False
                    etim_flag = False
                    pron_flag = False
                    i_pos = 0

                    try:
                        lines = glossa.splitlines()
                        for i in range(len(lines)):
                            line = lines[i]

                            if line == "":
                                etim_flag = False
                                pron_flag = False
                                sill_flag = False
                                continue

                            if pron_flag:
                                pron_flag = get_ipa(line, lemma)
                                if pron_flag:
                                    continue # di ipa possono essercene più di una

                            if sill_flag:
                                found = get_sill(line, lemma)
                                if found:
                                    sill_flag = False
                                    continue
                                else:
                                    sill_flag = False
                            
                            if etim_flag:
                                if line[0] == "#" or line[0] == "*" or line[0] == ":":
                                    get_etim(line[1:], lemma)
                                    continue
                                else:
                                    get_etim(line, lemma)
                                    etim_flag = False                              
                                    continue 

                            if line.find("{{Vedi|") != -1:
                                continue
                            if line[0] == "[": #immagini
                                continue

                            if line[0] == "=":
                                lang_found = lang_check(line, lemma)
                            if not lang_found:
                                continue
                            
                            if not unk_pos_flag: # di default si mette sempre una pos unk
                                current_pos = unk_pos(lemma)
                                unk_pos_flag = True
                            
                            pos = check_pos(lemma, line, i_pos, current_pos)
                            if current_pos != pos:
                                etim_flag = False
                                i_pos +=1
                                current_pos = pos

                            pron_flag = pron_check(line)
                            if pron_flag:
                                continue
                            
                            sill_flag = sill_check(line)
                            if sill_flag:
                                continue # se trovo il token della sill allora passo alla iter successiva
                            
                            if morpho_check(line, lemma, current_pos):
                                continue

                            etim_flag = etim_check(line)
                            if etim_flag:
                                continue

                            if line[0] == "#": # glossa
                                if line[-1] == ":": # introduce elenco
                                    elenco_flag = True
                                try:
                                    if line[1] == "*" and not elenco_flag: # esempio
                                        continue
                                except IndexError:
                                    continue # linea[1:] è vuota
                                glossa_check(line, lemma, current_pos)
                            else:
                                elenco_flag = False # se dopo un elenco puntato ho una lista di esempi?
                                                
                    except Exception as e:
                        print("ERRORE al lemma", lemma)
                        raise

    del context

if __name__ == "__main__":
    
    # load and convert to dictionary with the most frequent iso 639-1 language codes, those are used by wikitionary usually {{la}} ---> Latino
    df = pd.read_csv("lang_list.tsv", sep="\t")
    lang_dict = {k:v for k, v in zip(df["Language Code"], df["Language Name (Italian)"])}

    parsed_dict = {} # dictionary

    lang_pattern = re.compile("=={{-?(.+?)-?}}==")
    pos_pattern = re.compile("{{-(.*?)-\|(?:\|?\w*)*}}")
    morpho_pattern = re.compile("{{Pn.*?}}(?:\s{1,3})?''(.*?)''") # a volte ci sono più (o non ci sono) spazi prima della morpho
    glossa_pattern = re.compile("\[\[(\w*?(?:\s\w*?)?)\]\]|\[\[\w*?(?:#\w*)?\|(.*?)\]\]")
    special_redirect_pattern = re.compile("\[\[:?\w+:\w*\s?\w*\|(\w*\s?\w*)\]\]") # [[:w:.... ... | .... ....]] 
    quote_marks_pattern = re.compile("'{2,3}") # rimuove le virgolette se doppie o triple, notazione di wikipedia per il reindirizzamento
    ipa_pattern = re.compile("{{IPA\|\/(.*?)\/}}")
    sill_pattern = re.compile("{{-sill-}}")
    etim_pattern = re.compile("{{-etim-}}")
    pron_pattern = re.compile("{{-pron-}}")
    frequent_pos = ['verb form', 'sost', 'sost form', 'agg form', 'agg', 'verb', 'nome', 'avv', 'loc nom', 'acron', 'agg num', 'espr', 'pref', 'card', 'suff', 'inter', 'cong', 'prep', 'pronome']
    lang_pointer_pattern = re.compile("{{(\w+)}}")

    main(sys.argv[1])

    print("The xml dump was completely parsed!\nSaving the file (this can take some seconds depending on the size of the dictionary)...")

    with open(sys.argv[2], "w") as f:
        json.dump(parsed_dict, f)

# from command line: python iterparse.py xml_dump_path out_path