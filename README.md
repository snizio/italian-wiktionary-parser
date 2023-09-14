# italian-wiktionary-parser
This repository contains a python script for parsing the xml dump of the Italian Wiktionary (Wikizionario). It also contains the parsed dictionary in a compressed json file (it-dictionary.gz) with 370k lemmas circa. As far as I'm concerned, this is the first repo ever offering an italian dictionary as a free resource. This was made available to enhance NLP tasks that needs similar type of corpora. Since the Wiktionary is multilingual, here I kept only words that has an Italian tag definition =={{-it-}}== (that is, Italian words and frequently used non-Italian words with Italian definitions). 

Each lemma is structured in a dictionary with two keys: "meta" and "meanings":

- "meta":
  - "ipa": the IPA phonetic transcription (as a list since there can be more IPA for a single lemma).
  - "sill": hyphenation (also as a list of syllables).
  - "etim": etymology.
  - "sin" and "ant": list of synonyms and antonyms.
- "meanings":
  - Each meaning is disambiguated by the Part of Speech (PoS) as reported by Wiktionary. So for each PoS we have:
    - "morpho": the morphological information (if available, usually never available for verbs).
    - "glossa": each definition is separated by a "\n". Examples are discarded most of the time. Tags entries, like i.e. {{Term|Astrologia|it}}, are kept (like this ##Astrologia##) since they add an interesting categorization.

For example, the lemma "neologismo" will be structured as follows:

```
{'meta': {'ipa': ['neoloˈd͡ʒizmo'],
  'sill': ['ne', 'o', 'lo', 'gì', 'smo'],
  'etim': 'composto dal prefisso neo- (che proviene dal Greco Moderno νεο- ossia "nuovo"), dal Greco Moderno λόγος cioè "parola", e dal suffisso "-ismo" per indicare l\'origine, ricalcando il Francese néologisme',
  'sin': ['parola nuova, parola recente, nuovo vocabolo, nuovo termine',
   'neologia'],
  'ant': ['arcaismo']},
 'meanings': {'sost_0': {'morpho': 'm sing',
   'glossa': '##linguistica## termine, concetto o costrutto introdotto di recente nella lingua',
   'examples': 'il neologismo può essere riferito a nuovi concetti come nel lemma allunaggio\nil neologismo è inerente ad oggetti o prodotti innovativi come musicassetta\nil neologismo può assumere nuovi significati come la "pantera della polizia" cioè l\'auto di pronto intervento della Polizia\nil neologismo può derivare da parole straniere come scannerizzare\nil neologismo può essere creato dalla composizione di parole già esistenti come mangia e nastri da cui il lemma mangianastri\nil neologismo può essere frutto di parole totalmente nuove come quark'}}
```

There are inconsistencies due to shallow tagging by the wiktionary users and the weird complexity of the tag system. Right now, of the 370k lemmas, 4k have no glossa and 14k no etymology (mostly because absent from the Wiktionary, rarely due to parsing errors).
The dumps are taken from https://dumps.wikimedia.org/itwiktionary/20230701/.

If you want to run the parser on your xml dump, run it from command line with the following statement: 

```
python iterparse.py xml_dump_path out_path
```

To decompress and save the compressed dictionary into .json file run the following command:

```
python decompress_and_save.py compressed_dictionary json_out_path
```

The repository also contains vdb_lemmas.txt wich is a list of around 7k most frequent and foundamental lemmas in the italian lexicon extracted from the "Nuovo vocabolario di base della lingua italiana", De Mauro (1). This resource was extracted in order to assess the Wikizionario coverage of the VdB lemmas, wich is, as august 2023, of 97.67%.


(1) De Mauro, Tullio, and I. Chiari. "Il Nuovo vocabolario di base della lingua italiana." Internazionale.[28/11/2020]. https://www.internazionale.it/opinione/tullio-de-mauro/2016/12/23/il-nuovo-vocabolario-di-base-della-lingua-italiana (2016).