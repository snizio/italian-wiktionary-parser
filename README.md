# italian-wiktionary-parser
This repository contains a python script for parsing an xml dump of italian wiktionary (wikizionario). It also contains the parsed dictionary in a json file with 369k lemmas circa. As far as i'm concerned this is the first repo ever offering an italian dictionary as a free resource. This was made available to enhance NLP tasks that needs similar type of corpora. The dictionary is in a json file and each lemma is structured as follows:

{'meta': {'ipa': ['siɡaˈretta'], 'sill': ['si', 'ga', 'rét', 'ta'], 'etim': 'diminutivo di sigaro, similmente al francese cigarette'}, 'meanings': {'sost_0': {'morpho': 'f sing', 'glossa': 'rotolino di forma cilindrica contenente tabacco trinciato avvolto in una cartina destinato ad essere fumato\nqualsiasi oggetto avente forma simile a quella di una sigaretta\npiccola bobina di cartoncino attorno a cui è avvolto filo per cucire'}}}

There are inconsistencies due to shallow tagging by the wiktionary users and the weird complexity of the tag system. The dumps are taken from https://dumps.wikimedia.org/itwiktionary/20230701/.


from command line: 
python iterparse.py xml_dump_path out_path