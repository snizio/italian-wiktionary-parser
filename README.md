# italian-wiktionary-parser
This repository contains a python script for parsing the xml dump of the Italian Wiktionary (Wikizionario). It also contains the parsed dictionary in a json file with 370k lemmas circa. As far as I'm concerned, this is the first repo ever offering an italian dictionary as a free resource. This was made available to enhance NLP tasks that needs similar type of corpora. Since the Wiktionary is multilingual, here I kept only words that has an Italian tag definition =={{it}}== (that is, Italian words and frequently used non-Italian words). The dictionary is in a json file and each lemma is structured as follows (i.e lemma "neologismo"):

{'meta': {'ipa': ['neoloˈd͡ʒizmo'],
  'sill': ['ne', 'o', 'lo', 'gì', 'smo'],
  'etim': 'composto dal prefisso neo-  (che proviene dal Greco Moderno νεο- ossia "nuovo"), dal Greco Moderno λόγος cioè "parola", e dal suffisso "-ismo" per indicare l\'origine, ricalcando il Francese néologisme'},
 'meanings': {'sost_0': {'morpho': 'm sing',
   'glossa': 'termine, concetto o costrutto introdotto di recente nella lingua'}}}

There are inconsistencies due to shallow tagging by the wiktionary users and the weird complexity of the tag system. The dumps are taken from https://dumps.wikimedia.org/itwiktionary/20230701/.

If you want to run the parser on your xml dump, run it from command line with the following statement: 
python iterparse.py xml_dump_path out_path