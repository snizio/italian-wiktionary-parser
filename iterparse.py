from xml.etree.ElementTree import iterparse
import re
from tqdm import tqdm
import pandas as pd
import json
import sys
import gzip



def prepend_ns(s):
    """This prepend the namespace to each tag. It's useful to retrieve tags with the xml module."""
    return NAMESPACE + s 

def remove_list_tokens(line):
    """Recursively removes special tokens (*, #, :) at the beginning of a line in a list."""
    if line == "":
        return line
    if line[0] in ["*", "#", ":"]:
        return remove_list_tokens(line[1:])
    else:
        return line
    
def remove_punct_at_start(line):
    """Recursively removes punctuation at the beginning of a string often resulting from the text cleaning"""
    if line == "":
        return line
    elif line[0] in punctuation:
        return remove_punct_at_start(line[1:])
    else:
        return line

def remove_punct_at_end(line):
    """Recursively removes punctuation at the end of a string often resulting from the text cleaning"""
    reverse_line = line[::-1]
    if line == "":
        return line
    elif reverse_line[0] in punctuation:
        return remove_punct_at_start(reverse_line[1:])[::-1]
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
            parsed_dict[lemma] = {"meta": {"ipa": [], "sill": [], "etim": "", "sin": [], "ant": []}, "meanings": {}}
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

def sill_splitter(line):
    """Split the syllables """

    sill = []
    current_sill = ""
    line = line.strip()
    line = line.replace("'", "")
    line = re.sub(closing_tag_pattern, "", line)
    for i in range(len(line)):
        char = line[i]
        if char == " ":
            continue
        elif char == "|" and current_sill != "":
            sill.append(current_sill)
            current_sill = ""
        elif char in ["-", "–"] and current_sill != "":
            sill.append(current_sill)
            sill.append("-")
            current_sill = ""
        elif i == len(line)-1:
            current_sill += char
            sill.append(current_sill)
        else:
            current_sill += char
    
    sill = [x for x in sill if x != ""]

    return sill
    
def get_sill(line, lemma):
    """Extracts the syllables from a line"""
    if line[0] == ";": 
        line = line[1:]
        if line == " &lt;!-- inserire dopo le ; la sillabazione indicando l'accento e dividendo con un | come nell'esempio: sol | dà | to --&gt;": # common placeholder for wrong syllabation
            return False
        sill_split = sill_splitter(line) # it splits the sill string into ["ca", "sa"] for example, handles multi word lemmas too (usually separated with "-")
        if sill_split == [""] or len(max(sill_split, key=len, default="")) > 7:
            return False
        parsed_dict[lemma]["meta"]["sill"] = sill_split
        return True
    else:
        return False

def unk_pos(lemma):
    """Adds the "unk" (unknown) PoS tag to a lemma"""
    pos = "unk" # default option due to inconsistencies in the italian wiktionary tag system
    parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":"", "examples": ""}
    return pos

def check_pos(lemma, line, i_pos, current_pos):
    """Checks for the PoS pattern and retrieves the available PoS"""
    match = re.search(pos_pattern, line) # pos
    if match != None:
        pos = match.group(1)
        if pos in ["sill", "noconf", "pron", "trad", "alter", "ant", "etim"]:
            return current_pos
        if pos in pos_converter_dict:
            pos = pos_converter_dict[pos]
        pos = re.sub(white_spaces_pattern, " ", pos)
        pos = pos.strip() + f"_{i_pos}"
        if pos != current_pos and pos != f"Varie lingue_{i_pos}":
            current_pos = pos
            parsed_dict[lemma]["meanings"][pos] = {"morpho":"", "glossa":"", "examples": ""}
            if "unk" in parsed_dict[lemma]["meanings"]:
                del parsed_dict[lemma]["meanings"]["unk"] # if we find a PoS we delete the "unk" one
        return pos
    else:
        return current_pos
    
def morpho_check(line, lemma, pos):
    """Checks and extracts morphological metadata (i.e. "f sing" from a typical morpho line: {{Pn|w}} ''f sing'' )"""
    match = re.search(morpho_pattern, line) # informazioni morfologiche
    if match != None:
        morpho = ""
        for group in match.groups():
            if group != None:
                if morpho == "":
                    morpho += group
                else:
                    morpho += " e "+group
        morpho = remove_punct_at_start(morpho.strip())
        morpho = re.sub(white_spaces_pattern, "", morpho)
        parsed_dict[lemma]["meanings"][pos]["morpho"] = morpho
        return True

def etim_check(line):
    """Checks for the {{etim}} tag"""
    match = re.search(etim_pattern, line)
    if match != None:
        return True

def noetim_check(line):
    """Checks for the {{Noetim|it}} tag. Usually used when the etim is missing"""
    match = re.search(noetim_pattern, line)
    if match != None:
        return True

def sin_ant_check(line):
    match = re.search(sin_ant_pattern, line)
    tag = ""
    if match != None:
        for g in match.groups():
            if g != None:
                tag = g
        return tag
    else:
        return False

def nodef_check(line):
    """Checks for the {{Nodef|it}} tag. Usually used when the glossa is missing"""
    match = re.search(nodef_pattern, line)
    if match != None:
        return True

def template_utili_check(line):
    """Checks for the "template utili" line"""
    match = re.search(template_utili_pattern, line)
    if match != None:
        return True
    else:
        return False
    
def other_tags_check(line):
    """Tags that usually follows the one we are interested in. So if we find them we break. The order is taken from https://it.wiktionary.org/wiki/Wikizionario:Altri_titoli"""
    other_tag = ["{{-der-}}", "{{-rel-}}", "{{-var-}}", "{{-alter-}}", "{{-ipon-}}", "{{-iperon-}}", "{{-noconf-}}", "{{-prov-}}", "{{-trad-}}", "{{Trad1}}", "{{Trad2}}", "{{-ref-}}", "==Altri progetti==", "{{interprogetto}}"]
    line = line.strip()
    for tag in other_tag:
        if tag == line:
            return True

def string_cleaner(line, lemma):
    """Cleans a string from the usual wikimedia tags"""
    line = remove_list_tokens(line)
    cleaned_line = re.sub("{{Pn}}|{{pn}}", lemma, line)
    cleaned_line = re.sub(ref_pattern, "", cleaned_line)
    cleaned_line = re.sub(file_pattern, "", cleaned_line)
    cleaned_line = re.sub(vedi_pattern, lambda m: "vedi " + m.group(1).split("|")[1] if "|" in m.group(1) else "vedi " + m.group(1) , cleaned_line) # {{Vd|Afghanistan#Italiano|Afghanistan}} ---> vedi Afghanistan
    cleaned_line = re.sub(etimlink_pattern, lambda m: f"vedi {m.group(1)}", cleaned_line)
    cleaned_line = re.sub(lang_pointer_pattern, lambda m: lang_dict.get(m.group(1), m.group(0)), cleaned_line)
    # cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(tag_term_pattern, r"##\1##", cleaned_line)
    cleaned_line = re.sub("({{\w*?}})", lambda m: ambito_dict.get(m.group(0)), cleaned_line)
    cleaned_line = re.sub("{{.*?}}", "", cleaned_line)
    cleaned_line = re.sub(special_redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(redirect_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub("\[\[\w.*?\]\]", "", cleaned_line)
    cleaned_line = re.sub(quote_marks_pattern, "", cleaned_line)
    cleaned_line = re.sub(general_tag_pattern, r"\1", cleaned_line)
    cleaned_line = re.sub(white_spaces_pattern, " ", cleaned_line)
    cleaned_line = remove_punct_at_start(cleaned_line)
    cleaned_line = cleaned_line.strip()
    
    return cleaned_line

def get_etim(line, lemma):
    """Extracts and parses the etim"""
    cleaned_line = string_cleaner(line, lemma)
    if cleaned_line == "":
        return
    if parsed_dict[lemma]["meta"]["etim"] == "":
        parsed_dict[lemma]["meta"]["etim"] += cleaned_line
    else:
        parsed_dict[lemma]["meta"]["etim"] += "\n"+cleaned_line

def split_sin_ant(text):
    inside_parentheses = False
    parts = []
    current_part = []

    for char in text:
        if char == '(':
            inside_parentheses = True
        elif char == ')':
            inside_parentheses = False

        if char == ',' and not inside_parentheses:
            parts.append(''.join(current_part).strip())
            current_part = []
        else:
            current_part.append(char)

    # Adding the last part
    parts.append(''.join(current_part).strip())
    
    return parts

def get_sin_ant(line, lemma, sin_ant):
    """Extracts and parses the synonym and antonym informations"""
    cleaned_line = string_cleaner(line, lemma)
    cleaned_line = remove_punct_at_end(cleaned_line)
    if cleaned_line == "":
        return
    parsed_dict[lemma]["meta"][sin_ant].extend(split_sin_ant(cleaned_line))
    parsed_dict[lemma]["meta"][sin_ant] = parsed_dict[lemma]["meta"][sin_ant]
    
def glossa_check(line, lemma, pos):
    """Extracts and parses the glossa"""
    cleaned_line = string_cleaner(line, lemma)
    if cleaned_line == "":
        return
    if parsed_dict[lemma]["meanings"][pos]["glossa"] == "":
        parsed_dict[lemma]["meanings"][pos]["glossa"] += cleaned_line
    else:
        parsed_dict[lemma]["meanings"][pos]["glossa"] += "\n"+cleaned_line

def get_examples(line, lemma, pos):
    """Extracts and parses usage examples from the glossa"""
    cleaned_line = string_cleaner(line, lemma)
    if cleaned_line == "":
        return
    if parsed_dict[lemma]["meanings"][pos]["examples"] == "":
        parsed_dict[lemma]["meanings"][pos]["examples"] += cleaned_line
    else:
        parsed_dict[lemma]["meanings"][pos]["examples"] += "\n"+cleaned_line


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
                    sin_ant_flag = False
                    i_pos = 0

                    try:
                        lines = glossa.splitlines()
                        for i in range(len(lines)):
                            line = lines[i]

                            if line == "":
                                sin_ant_flag = False
                                sill_flag = False
                                etim_flag = False
                                pron_flag = False
                                continue

                            if line[0] == "<":
                                if template_utili_check(line): # line usually found at the end of a glossa referencing templates
                                    break # we break it here since a lot of template tags could trigger the boolean flags 

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
                            
                            if sin_ant_flag != False:
                                if line[0] == "*":
                                    get_sin_ant(line, lemma, sin_ant_flag)
                                    continue
                                else:
                                    sin_ant_flag = False

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
                            
                            if line.strip()[:2] == "{{":
                                if other_tags_check(line):
                                    break
                            
                            pos = check_pos(lemma, line, i_pos, current_pos)
                            if pos == "sill": # there are 4 cases where the sill tag is written like a PoS, this if statement handles this. (Due to bad annotation)
                                sill_flag = True
                                continue
                            elif pos == "pron": # only one case (also bad annotation)
                                pron_flag = True
                                continue
                            elif pos == "etim":
                                etim_flag = True
                                continue
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

                            sin_ant_flag = sin_ant_check(line)
                            if sin_ant_flag != False:
                                elenco_flag = False
                                continue

                            if line[0] == "#": # glossa
                                if nodef_check(line):
                                    continue
                                if line[-1] == ":": # it introduces a list (usually...)
                                    elenco_flag = True
                                try:
                                    if line[1] in ["*", ":"] and not elenco_flag: # examples
                                        get_examples(line, lemma, current_pos)
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

    # use the following dictionary as a PoS converter. The following key value pairs handles some tag errors made by users 
    pos_converter_dict = {"suffissoide": "suff",
                          "voce verb": "verb",
                          "verbm form": "verb form",
                          "adj": "agg",
                          "adj form": "agg form",
                          "prefissoide": "pref"}
    
    ambito_dict = {"{{Est}}": "(per estensione)",
                    "{{Lett}}": "(letteralmente)",
                    "{{Fig}}": "(senso figurato)"}

    parsed_dict = {} # dictionary

    context = iterparse(sys.argv[1], events=("start", "end"))

    # Get the root element
    _, root = next(context)

    # Extract the namespace from the root element
    NAMESPACE = root.tag.split("}")[0] + "}"
    del context

    punctuation = '!"$%&\')*+,-./:;<=>?@[\\]^_`{|}~ ' # all punct + white space excluding the "#" special character used for Term tags

    # compiling regex
    lang_pattern = re.compile("=={{-?(.+?)-?}}==")
    vedi_pattern = re.compile("{{[Vv]d\|(.*?)}}")
    pos_pattern = re.compile("{{-(.*?)-\|(?:\|?.*?)*}}")
    morpho_pattern = re.compile("{{[Pp][Nn].*?}}(?:\s{1,5})?''\s?((?:m|f|inv).*?)\s?''\s?(?: e ''((?:m|f|inv).*?)\s?'')?") 
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
    general_tag_pattern = re.compile("<.+?>(.+?)<\/.+?>") 
    closing_tag_pattern = re.compile("<.+?/>")
    lang_pointer_pattern = re.compile("{{(\w+)}}")
    tag_term_pattern = re.compile("\{\{[Tt]erm\|([\w ]+)(?:\|it)?(?:[\|\w ])*\}\}")
    white_spaces_pattern = re.compile("\s{2,}")
    char_pattern = re.compile("[a-zA-Z]")
    template_utili_pattern = re.compile("<!-- altri template utili:") # line usually found at the end of a glossa referencing templates
    sin_ant_pattern = re.compile("{{-(sin)-}}|{{-(ant)-}}")

    main(sys.argv[1])

    print(f"The xml dump was completely parsed! {len(parsed_dict)} lemmas were extracted.\nSaving the file (this can take some seconds depending on the size of the dictionary)...")

    json_str = json.dumps(parsed_dict).encode('utf-8')  # Convert to string and then to bytes
    with gzip.GzipFile(sys.argv[2], 'wb') as f:
        f.write(json_str)

    print(f"Compressed file saved at {sys.argv[2]}.")

# from command line: python iterparse.py xml_dump_path out_path