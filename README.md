# italian-wiktionary-parser
This repository contains a python script for parsing the xml dump of the Italian Wiktionary (Wikizionario). It also contains the parsed dictionary in a json file with 370k lemmas circa. As far as I'm concerned, this is the first repo ever offering an italian dictionary as a free resource. This was made available to enhance NLP tasks that needs similar type of corpora. Since the Wiktionary is multilingual, here I kept only words that has an Italian tag definition =={{-it-}}== (that is, Italian words and frequently used non-Italian words with Italian definitions). 

Each lemma is made by a dictionary with two keys: "meta" and "meanings":

- "meta":
  - "ipa": the IPA phonetic transcription (as a list since there can be more IPA for a single lemma).
  - "sill": hyphenation (also as a list of syllables).
  - "etim": etymology.
- "meanings":
  - Each meaning is disambiguated by the Part of Speech (PoS) as reported by Wiktionary. So for each PoS we have:
    - "morpho": the morphological information (if available, usually never available for verbs).
    - "glossa": each definition is separated by a "\n". Examples are discarded. Tags entries, like i.e. {{Term|Astrologia|it}}, are kept (like this ##Astrologia##) since they add an interesting categorization.

For example, the lemma "grana" will be structured as follows:

```
{'meta': {'ipa': ['ˈɡrana'],
  'sill': ['grà', 'na'],
  'etim': 'da "(formaggio) di grana"'},
 'meanings': {'sost_0': {'morpho': 'f sing',
   'glossa': 'oggetto granuloso\n##familiare## seccatura'},
  'sost_1': {'morpho': 'm inv',
   'glossa': "##gastronomia## formaggio caratteristico dell'Emilia e della Lombardia"},
  'sost_2': {'morpho': 'f inv', 'glossa': '##gergale## ##popolare## soldi'}}}
```

There are inconsistencies due to shallow tagging by the wiktionary users and the weird complexity of the tag system. Right now, of the 370k lemmas, 4k have no glossa and 14k no etymology (mostly because absent from the Wiktionary, rarely due to parsing errors).
The dumps are taken from https://dumps.wikimedia.org/itwiktionary/20230701/.

If you want to run the parser on your xml dump, run it from command line with the following statement: 
python iterparse.py xml_dump_path out_path