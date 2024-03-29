import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import pandas as pd

# This script scrapes the ONLI (Opera del Vocabolario Italiano) dictionary and saves the data in a CSV file. 
# The data includes the lemma, the PoS, the glossa and the examples. To extract also other data, modify this script accordingly.


# Dictionary for converting the ONLI PoS into the Wiktionary PoS
abbreviazioni_pos = {
    "agg.": "agg",
    "agg.le": "agg",
    "art.": "art",
    "avv.": "avv",
    "avv.le": "avv",
    "cong.": "cong",
    "inter.": "inter",
    "loc.": "loc",
    "prep.": "prep",
    "pron.": "pron",
    "s.": "sost",
    "s.le": "sost",
    "v.": "verb"
}

def handle_pos(posses):
    if "loc" in posses and "sost" in posses:
        return "loc nom"
    if "loc" in posses and "agg" in posses:
        return "loc agg"
    if "loc" in posses and "avv" in posses:
        return "loc avv"
    if "loc" in posses and "verb" in posses:
        return "loc verb"
    if "sost" in posses and "agg" in posses:
        return "sost"
    return posses[0]
    

    
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
final_dict = {}
for letter in tqdm(letters, desc=f"Letter", leave=False): # for each letter
    url = f"https://www.iliesi.cnr.it/ONLI/elenca.php?al={letter}%&page=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        pages = int(soup.find_all("td", {"height": "50", "valign": "bottom", "align": "center"})[0].text.strip().split("/")[1]) # get the number of pages for each letter
    except: # if there are no pages
        pages = 1
    for p in tqdm(range(1, pages+1), desc=f"page", leave=False): # for each page
        if p != 1:
            url = f"https://www.iliesi.cnr.it/ONLI/elenca.php?al={letter}%&page={p}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
        # else soup is already defined
        for a in soup.find_all("a", href=True):
            if a.text:
                if a["href"].startswith("entrata.php"):
                    lemma = a.text.strip()
                    lemma_url = "https://www.iliesi.cnr.it/ONLI/" + a["href"]
                    lemma_response = requests.get(lemma_url)
                    lemma_soup = BeautifulSoup(lemma_response.text, "html.parser")

                    # PoS
                    lemma_pos_text = lemma_soup.find_all("div", {"class": "boxentry"})[0].text.strip().split("\r")[0].split(lemma)[-1]
                    posses = [abbreviazioni_pos[pos] for pos in abbreviazioni_pos if pos in lemma_pos_text.split(" ")]
                    lemma_pos = handle_pos(posses)

                    # glossa
                    glossa = lemma_soup.find_all("p")[1].text

                    # examples
                    target_p = lemma_soup.find('p', text=glossa)
                    target_ul = target_p.find_next_sibling('ul')
                    li_elements = target_ul.find_all('li')
                    examples = []
                    for li in li_elements:
                        li_text = li.text
                        examples.append(li_text)

                    # etymology
                    etymology = ""
                    start_element = lemma_soup.find('b', class_='diamondb')
                    etymology += start_element.text

                    for sibling in start_element.next_siblings:
                        if sibling.name == 'br':
                            break
                        etymology += sibling.text

                    new_start_element = lemma_soup.find('b', class_='diamondv')
                    etymology += ", " + new_start_element.text

                    for sibling in new_start_element.next_siblings:
                        if sibling.name == 'br':
                            break
                        etymology += sibling.text

                    final_dict[lemma] = (lemma_pos, glossa.strip(), etymology, examples) # save the data in the dictionary
                    time.sleep(0.1) # to avoid being blocked

lemmas = list(final_dict.keys())
lemmas_pos = [final_dict[lemma][0] for lemma in lemmas]
lemmas_glossa = [final_dict[lemma][1] for lemma in lemmas]
lemmas_etymology = [final_dict[lemma][2] for lemma in lemmas]
lemmas_examples = [" ** ".join(final_dict[lemma][3]) for lemma in lemmas]
df = pd.DataFrame({"lemma": lemmas, "pos": lemmas_pos, "glossa": lemmas_glossa, "examples": lemmas_examples, "etymology": lemmas_etymology}) # create a DataFrame

df.to_csv("ONLI-NEO.csv", index=False) # save the DataFrame as a CSV file