# italian-wiktionary-parser
This repository contains a python script for parsing the xml dump of the Italian Wiktionary (Wikizionario). It also contains the parsed dictionary (august 2023) in a compressed json file (it-dictionary.gz) with 370k lemmas circa. As far as I'm concerned, this is the first repo ever offering an italian dictionary as a free resource. This was made available to enhance NLP tasks that needs similar type of corpora. Since the Wiktionary is inherently multilingual, here I kept only words that has an Italian tag definition =={{-it-}}== (that is, Italian words and frequently used non-Italian words in the Italian lexicon). 

Each lemma is structured in a dictionary with two keys: "meta" and "meanings":

- "meta":
  - "ipa": the IPA phonetic transcription (as a list since there can be more IPA for a single lemma).
  - "sill": hyphenation (also as a list of syllables).
  - "etim": etymology.
  - "sin" and "ant": list of synonyms and antonyms.
- "meanings":
  - Each meaning is disambiguated by the Part of Speech (PoS) as reported by Wiktionary. So for each PoS we have:
    - "morpho": the morphological information (if available, usually never available for verbs).
    - "glossa": each definition is separated by a "\n". Tags entries, like i.e. {{Term|Astrologia|it}}, are kept (like this ##Astrologia##) since they add an interesting categorization. Usage examples are added in the form: [ESEMPIO: ...]

For example, the word "passo" will be structured as follows:

```

{'meta': {'ipa': ['ˈpasso'],
  'sill': ['pàs', 'so'],
  'etim': 'dal latino passus derivazione di pandĕre ossia "aprire, stendere"',
  'sin': ['appassito, secco, seccato, vizzo, avvizzito',
   '(di un territorio) ** attraversamento, transito',
   '(luogo ove si passa) ** passaggio, varco',
   '(insellatura) ** valico',
   '(maniera di camminare) ** andatura',
   '(rumore dei piedi) ** scalpiccio',
   'camminata, marcia, andatura mossa',
   '(senso figurato) ** attività, iniziativa, azione, atto, mossa, provvedimento, decisione, risoluzione, tentativo',
   'orma, impronta',
   'breve distanza',
   'brano, luogo, passaggio, pezzo, citazione',
   '(nel ciclismo) ##sport## ** andatura'],
  'ant': ['fresco']},
 'meanings': {'agg_0': {'morpho': 'm sing',
   'glossa': "##obsoleto se non al femminile singolare## che è appassito, che ha perso tutta l'acqua precedentemente contenuta, detto generalmente di frutti[ESEMPIO: uva passa]"},
  'sost_1': {'morpho': 'm sing',
   'glossa': "##fisica## movimento dei piedi o di altri oggetti semoventi in avanti oppure all' indietro[ESEMPIO: fece un passo verso di lei][ESEMPIO: dalla paura fece un passo indietro]\n##meccanica## ##tecnologia## ##ingegneria## distanza costante tra due punti successivi[ESEMPIO: il passo della filettatura è la distanza tra i profili]\n##geografia## il punto di passaggio tra due valli di un percorso stradale[ESEMPIO: passo dello Stelvio]"},
  'verb form_2': {'morpho': '',
   'glossa': "prima persona singolare dell'indicativo predente di passare[ESEMPIO: tra un'ora passo da te]"}}}

```

There are inconsistencies due to shallow tagging by the wiktionary users and the weird complexity of the tag system. Right now, of the 370k lemmas, 4k have no glossa and 14k no etymology (mostly because absent from the Wiktionary, rarely due to parsing errors). The logic behind the parser is, therefore, tricky and not easy to understand. Also, changes in the dictionary tag schema can break the parser.
The dump is taken from https://dumps.wikimedia.org/itwiktionary/20230701/.

If you want to run the parser on your xml dump, run it from command line with the following statement: 

```
python iterparse.py xml_dump_path out_path
```

To decompress and save the compressed dictionary into .json file run the following command:

```
python decompress_and_save.py compressed_dictionary json_out_path
```

The repository also contains a script (onli-scraper.py) for parsing the ONLI database of Italian neologisms. The ONLI-NEO.csv files already contains all the scraped data consisting of 2986 lexical entries annotated with PoS (translated to the Wikizionario style), glosses and usage examples (if there are more examples they are separated by " ** ").

The repository also contains vdb_lemmas.txt wich is a list of around 7k most frequent and foundamental lemmas in the italian lexicon extracted from the "Nuovo vocabolario di base della lingua italiana", De Mauro (1). This resource was extracted in order to assess the Wikizionario coverage of the VdB lemmas, wich is, as august 2023, of 97.67%.


(1) ONLI (Osservatorio Neologico della Lingua Italiana): https://www.iliesi.cnr.it/ONLI/

(2) De Mauro, Tullio, and I. Chiari. "Il Nuovo vocabolario di base della lingua italiana." Internazionale.[28/11/2020]. https://www.internazionale.it/opinione/tullio-de-mauro/2016/12/23/il-nuovo-vocabolario-di-base-della-lingua-italiana (2016).