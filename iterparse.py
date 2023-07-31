from xml.etree.ElementTree import iterparse
import re
from tqdm import tqdm
import pandas as pd
import json
import sys



def prepend_ns(s):
    """This prepend the namespace to each tag. It's useful to retrieve tags with the xml module."""
    return NAMESPACE + s 

def remove_list_tokens(line):
    """Recursively removes special tokens (*, #, :) at the beginning of a line in a list."""
    if line[0] in ["*", "#", ":"]:
        return remove_list_tokens(line[1:])
    else:
        return line

def lang_check(line, lemma):
    """Check for the italian language tag, usually something like =={{-it-}}==."""
    line = line.replace(" ", "") # removing white spaces for conformity
    match =  re.search(lang_pattern, line) 
    if match != None: # if we found a lang tag
        lang = match.group(1)
        if lang == None:
            lang = match.group(2)
        if lang == "it":
            parsed_dict[lemma] = {"meta": {"ipa": [], "sill": [], "etim": ""}, "meanings": {}}
            return lang, True
        else:
            return lang, False
    else:
        return 0, False
    
def pron_check(line):
    """Checks for the pronouce tag {{pron}}"""
    match = re.search(pron_pattern, line)
    if match != None:
        return True

def get_ipa(line, lemma):
    """Extracts IPA from a line"""
    match = re.search(ipa_pattern, line) # ipa
    if match != None:
        ipa = match.group(1)
        parsed_dict[lemma]["meta"]["ipa"].append(ipa)
        return True
    else:
        return False
    
def sill_check(line):
    """Checks for the {{sill}} tag"""
    match = re.search(sill_pattern, line) # sill
    if match != None:
        return True
    
def get_sill(line, lemma):
    """Extracts the syllables from a line"""
    if line[0] == ";": 
        parsed_dict[lemma]["meta"]["sill"] = line[1:].replace(" ", "").split("|") # it splits the sill string into ["ca", "sa"] for example
        return True
    else:
        return False

def unk_pos(lemma):
    """Adds the "unk" (unknown) PoS tag to a lemma"""
    pos = "unk" # default option due to inconsistencies in the italian wiktionary tag system
    parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":""}
    return pos

def check_pos(lemma, line, i_pos, current_pos):
    """Checks for the PoS pattern and retrieves the available PoS"""
    match = re.search(pos_pattern, line) # pos
    if match != None:
        pos = match.group(1) + f"_{i_pos}"
        if pos != current_pos and pos != f"Varie lingue_{i_pos}":
            current_pos = pos
            parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":""}
            if "unk" in parsed_dict[lemma]["meanings"]:
                del parsed_dict[lemma]["meanings"]["unk"] # if we find a PoS we delete the "unk" one
        return pos
    else:
        return current_pos
    
def morpho_check(line, lemma, pos):
    """Checks and extracts morphological metadata (i.e. "f sing" from a typical morpho line: {{Pn|w}} ''f sing'' )"""
    match = re.search(morpho_pattern, line) # informazioni morfologiche
    if match != None:
        morpho = match.group(1).lstrip() # talvolta c'è uno spazio all'inizio
        parsed_dict[lemma]["meanings"][pos]["morpho"] = morpho
        return True

def etim_check(line):
    """Checks for the {{etim}} tag"""
    match = re.search(etim_pattern, line)
    if match != None:
        return True

def noetim_check(line):
    """Checks fot the {{Noetim|it}} tag. Usually used when the etim is missing"""
    match = re.search(noetim_pattern, line)
    if match != None:
        return True
    
def nodef_check(line):
    """Checks fot the {{Nodef|it}} tag. Usually used when the glossa is missing"""
    match = re.search(nodef_pattern, line)
    if match != None:
        return True

def get_etim(line, lemma):
    """Extracts and parses the etim"""
    line = remove_list_tokens(line)
    cleaned_line = re.sub("{{Pn}}|{{pn}}", lemma, line)
    cleaned_line = re.sub(ref_pattern, "", cleaned_line)
    cleaned_line = re.sub(file_pattern, "", cleaned_line)
    cleaned_line = re.sub(vedi_pattern, lambda m: "vedi " + m.group(1).split("|")[1] if "|" in m.group(1) else "vedi " + m.group(1) , cleaned_line) # {{Vd|Afghanistan#Italiano|Afghanistan}} ---> vedi Afghanistan
    cleaned_line = re.sub(etimlink_pattern, lambda m: f"vedi {m.group(1)}", cleaned_line)
    cleaned_line = re.sub(lang_pointer_pattern, lambda m: lang_dict.get(m.group(1), m.group(0)), cleaned_line)
    # cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(tag_term_pattern, r"##\1##", cleaned_line)
    cleaned_line = re.sub("{{.*?}}", "", cleaned_line)
    cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub("\[\[\w.*?\]\]", "", cleaned_line)
    cleaned_line = re.sub(quote_marks_pattern, "", cleaned_line)
    cleaned_line = cleaned_line.lstrip()
    if parsed_dict[lemma]["meta"]["etim"] == "":
        parsed_dict[lemma]["meta"]["etim"] += cleaned_line
    else:
        parsed_dict[lemma]["meta"]["etim"] += "\n"+cleaned_line
    
def glossa_check(line, lemma, pos):
    """Extracts and parses the glossa"""
    line = remove_list_tokens(line)
    cleaned_line = re.sub("{{Pn}}|{{pn}}", lemma, line)
    cleaned_line = re.sub(ref_pattern, "", cleaned_line)
    cleaned_line = re.sub(file_pattern, "", cleaned_line)
    cleaned_line = re.sub(vedi_pattern, lambda m: "vedi " + m.group(1).split("|")[1] if "|" in m.group(1) else "vedi " + m.group(1) , cleaned_line) # {{Vd|Afghanistan#Italiano|Afghanistan}} ---> vedi Afghanistan
    cleaned_line = re.sub(lang_pointer_pattern, lambda m: lang_dict.get(m.group(1), m.group(0)), cleaned_line)
    # cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(tag_term_pattern, r"##\1##", cleaned_line)
    cleaned_line = re.sub("{{.*?}}", "", cleaned_line)
    cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub("\[\[\w.*?\]\]", "", cleaned_line)
    cleaned_line = re.sub(quote_marks_pattern, "", cleaned_line)
    cleaned_line = cleaned_line.lstrip()
    if parsed_dict[lemma]["meanings"][pos]["glossa"] == "":
        parsed_dict[lemma]["meanings"][pos]["glossa"] += cleaned_line
    else:
        parsed_dict[lemma]["meanings"][pos]["glossa"] += "\n"+cleaned_line


def main(xml_dump_path):
    """main function"""

    context = iterparse(xml_dump_path, events=("start", "end")) # iterparse iterator object

    for event, elem in tqdm(context, desc="Parsing XML", unit=" elements"):
        if event == "end":
            if prepend_ns("page") == elem.tag: # if we find a page (usually there is a page for each lemma)
                lemma = elem.find(prepend_ns("title")) # the title tag contains the lemma string
                if lemma != None:
                    lemma = str(lemma.text)
                    if ":" in lemma or lemma in ["Pagina principale", "Pagina principale/Categorie"]:
                        continue
                    revision = elem.find(prepend_ns("revision"))
                    glossa = revision.find(prepend_ns("text")).text # this contains all the metadata for a specific lemma
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
                                continue

                            if pron_flag:
                                pron_flag = get_ipa(line, lemma)
                                if pron_flag:
                                    continue # there can be more than one IPA

                            if sill_flag:
                                found = get_sill(line, lemma)
                                if found:
                                    sill_flag = False
                                    continue
                                else:
                                    sill_flag = False
                            
                            if etim_flag:
                                if noetim_check(line):
                                    etim_flag = False
                                    continue
                                if line[0] == "#" or line[0] == "*" or line[0] == ":":
                                    get_etim(line, lemma)
                                    continue
                                else:
                                    get_etim(line, lemma)
                                    etim_flag = False                              
                                    continue 

                            if line.find("{{Vedi|") != -1:
                                continue
                            if line[0] == "[": # images
                                continue

                            if line[0] == "=":
                                elenco_flag = False
                                lang, lang_found = lang_check(line, lemma)
                                if lang == 0: # if the line starts with "=" but do not contains lang information (rare)
                                    continue
                                if lang != "it":
                                    if parsed_dict.get(lemma, None) != None: # if lang is different form "it" and we already have the lemma in the dict
                                        break # it means we already got an italian tag and we are moving into a different language, so we break
                                    else:
                                        continue # else we keep on iterating hoping to find an italian tag
                                if lang_found:
                                    continue
                            
                            if not lang_found:
                                continue
                            
                            if not unk_pos_flag: # di default si mette sempre una pos unk
                                current_pos = unk_pos(lemma)
                                unk_pos_flag = True
                            
                            pos = check_pos(lemma, line, i_pos, current_pos)
                            if current_pos != pos:
                                elenco_flag = False
                                etim_flag = False
                                i_pos +=1
                                current_pos = pos
                                continue

                            pron_flag = pron_check(line)
                            if pron_flag:
                                elenco_flag = False
                                continue
                            
                            sill_flag = sill_check(line)
                            if sill_flag:
                                elenco_flag = False
                                continue
                            
                            if morpho_check(line, lemma, current_pos):
                                elenco_flag = False
                                continue

                            etim_flag = etim_check(line)
                            if etim_flag:
                                elenco_flag = False
                                continue

                            if line[0] == "#": # glossa
                                if nodef_check(line):
                                    continue
                                if line[-1] == ":": # it introduces a list (usually...)
                                    elenco_flag = True
                                try:
                                    if line[1] in ["*", ":"] and not elenco_flag: # examples
                                        continue
                                except IndexError:
                                    continue # if line[1:] is empty
                                glossa_check(line, lemma, current_pos)
                            else:
                                elenco_flag = False
                                                
                    except Exception as e:
                        print("ERROR at lemma", lemma)
                        raise e

    del context # deleting the context to free memory

if __name__ == "__main__":
    
    # load and convert to dictionary with the most frequent iso 639-1 language codes, those are used by the wiktionary usually like {{la}} ---> Latino
    df = pd.read_csv("lang_list.tsv", sep="\t")
    lang_dict = {k:v for k, v in zip(df["Language Code"], df["Language Name (Italian)"])}

    parsed_dict = {} # dictionary

    context = iterparse(sys.argv[1], events=("start", "end"))

    # Get the root element
    _, root = next(context)

    # Extract the namespace from the root element
    NAMESPACE = root.tag.split("}")[0] + "}"
    del context

    # compiling regex
    lang_pattern = re.compile("=={{-?(.+?)-?}}==")
    vedi_pattern = re.compile("{{[Vv]d\|(.*?)}}")
    pos_pattern = re.compile("{{-(.*?)-\|(?:\|?\w*)*}}")
    morpho_pattern = re.compile("(?:{{Pn.*?}}|{{pn.*?}})(?:\s{1,3})?''(.*?)''") 
    # glossa_pattern = re.compile("\[\[(-?\w*?-?(?:\s?\w*?)*)\]\]|\[\[\w*?(?:#\w*)?\|(.*?)\]\]")
    special_redirect_pattern = re.compile("\[\[[^\[\]]+?\|(.+?)\]\]") # [[:w:.... ... | .... ....]] [[:s:.... ... | .... ....]] 
    redirect_pattern = re.compile("\[\[(.*?)\]\]")  
    quote_marks_pattern = re.compile("'{2,3}")
    ipa_pattern = re.compile("{{IPA\|\/(.*?)\/}}")
    sill_pattern = re.compile("{{-sill-}}")
    etim_pattern = re.compile("{{-etim-}}")
    noetim_pattern = re.compile("{{Noetim\|it}}")
    nodef_pattern = re.compile("{{Nodef\|it}}")
    etimlink_pattern = re.compile("{{Etim-link\|(.*?)}}")
    pron_pattern = re.compile("{{-pron-}}")
    file_pattern = re.compile("\[\[File:.*?\]\]")
    ref_pattern = re.compile("<ref.*?>.*?<\/ref>|<ref.*?\/>")
    lang_pointer_pattern = re.compile("{{(\w+)}}")
    tag_term_pattern = re.compile("\{\{[Tt]erm\|(.*?)\|it\}\}")

    main(sys.argv[1])

    print(f"The xml dump was completely parsed! {len(parsed_dict)} lemmas were extracted.\nSaving the file (this can take some seconds depending on the size of the dictionary)...")

    with open(sys.argv[2], "w") as f:
        json.dump(parsed_dict, f)

    print(f"File saved at {sys.argv[2]}.")

# from command line: python iterparse.py xml_dump_path out_path