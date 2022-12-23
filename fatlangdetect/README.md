# fasttext-langdetect
This library is a wrapper for the language detection model trained on fasttext by Facebook. For more information, please visit: https://fasttext.cc/docs/en/language-identification.html


## Supported languages
```
af als am an ar arz as ast av az azb ba bar bcl be bg bh bn bo bpy br bs bxr ca cbk ce cebckb co cs cv cy da de diq dsb dty dv el eml en eo es et eu fa fi fr frr fy ga gd gl gn gom gu gv he hi hif hr hsb ht hu hy ia id ie ilo io is it ja jbo jv ka kk km kn ko krc ku kv kw ky la lb lez li lmo lo lrc lt lv mai mg mhr min mk ml mn mr mrj ms mt mwl my myv mzn nah nap nds ne new nl nn no oc or os pa pam pfl pl pms pnb ps pt qu rm ro ru rue sa sah sc scn sco sd sh si sk sl so sq sr su sv sw ta te tg th tk tl tr tt tyv ug uk ur uz vec vep vi vls vo wa war wuu xal xmf yi yo yue zh
```

## Install
```
pip install fasttext-langdetect
```

## Usage
`detect` method expects UTF-8 data. `low_memory` option enables getting predictions with the compressed version of the fasttext model by sacrificing the accuracy a bit.

```
from ftlangdetect import detect

result = detect(text="Bugün hava çok güzel", low_memory=False)
print(result)
> {'lang': 'tr', 'score': 1.00}

result = detect(text="Bugün hava çok güzel", low_memory=True)
print(result)
> {'lang': 'tr', 'score': 0.9982126951217651}
```

## Benchmark
We benchmarked the fasttext model against [cld2](https://github.com/CLD2Owners/cld2), [langid](https://github.com/saffsd/langid.py), and [langdetect](https://github.com/Mimino666/langdetect) on Wili-2018 dataset.

|                          | fasttext    | langid      | langdetect  | cld2        |
|--------------------------|-------------|-------------|-------------|-------------|
| Average time (ms) | 0,158273381 | 1,726618705 | 12,44604317 | **0,028776978** |
| 139 langs - not weighted   | 76,8        | 61,6        | 37,6        | **80,8**        |
| 139 langs - pop weighted | **95,5**        | 93,1        | 86,6        | 92,7        |
| 44 langs - not weighted    | **93,3**        | 89,2        | 81,6        | 91,5        |
| 44 langs - pop weighted   | **96,6**        | 94,8        | 89,4        | 93,4        |

- `pop weighted` means recall for each language is multipled by [its number of speakers](https://en.wikipedia.org/wiki/List_of_languages_by_total_number_of_speakers).
- 139 languages = all languages with ISO 639-1 2-letter code
- 44 languages = top 44 languages spoken in the world


#### Recall per language
| lang                    | cld2  | fasttext | langdetect | langid |
|-------------------------|-------|----------|------------|--------|
| Afrikaans               | 0,94  | 0,918    | 0,992      | 0,966  |
| Albanian                | 0,958 | 0,966    | 0,964      | 0,954  |
| Amharic                 | 0,976 | 0,982    | 0          | 0,982  |
| Arabic                  | 0,994 | 0,998    | 0,998      | 0,996  |
| Aragonese               | 0     | 0,43     | 0          | 0,788  |
| Armenian                | 0,966 | 0,972    | 0          | 0,968  |
| Assamese                | 0,946 | 0,956    | 0          | 0,14   |
| Avar                    | 0     | 0,626    | 0          | 0      |
| Aymara                  | 0,596 | 0        | 0          | 0      |
| Azerbaijani             | 0,97  | 0,988    | 0          | 0,984  |
| Bashkir                 | 0,97  | 0,97     | 0          | 0      |
| Basque                  | 0,978 | 0,99     | 0          | 0,962  |
| Belarusian              | 0,94  | 0,97     | 0          | 0,964  |
| Bengali                 | 0,898 | 0,922    | 0,904      | 0,942  |
| Bhojpuri                | 0,716 | 0,15     | 0          | 0      |
| Bokmål                  | 0,852 | 0,966    | 0,976      | 0,95   |
| Bosnian                 | 0,422 | 0,108    | 0          | 0,054  |
| Breton                  | 0,946 | 0,974    | 0          | 0,976  |
| Bulgarian               | 0,892 | 0,964    | 0,964      | 0,942  |
| Burmese                 | 0,998 | 0,998    | 0          | 0      |
| Catalan                 | 0,882 | 0,95     | 0,93       | 0,928  |
| Central Khmer           | 0,876 | 0,878    | 0          | 0,876  |
| Chechen                 | 0     | 0,99     | 0          | 0      |
| Chuvash                 | 0     | 0,96     | 0          | 0      |
| Cornish                 | 0     | 0,792    | 0          | 0      |
| Corsican                | 0,88  | 0,016    | 0          | 0      |
| Croatian                | 0,688 | 0,806    | 0,982      | 0,932  |
| Czech                   | 0,978 | 0,986    | 0,984      | 0,982  |
| Danish                  | 0,886 | 0,958    | 0,95       | 0,896  |
| Dhivehi                 | 0,996 | 0,998    | 0          | 0      |
| Dutch                   | 0,9   | 0,978    | 0,968      | 0,97   |
| English                 | 0,992 | 1        | 0,998      | 0,986  |
| Esperanto               | 0,936 | 0,978    | 0          | 0,948  |
| Estonian                | 0,918 | 0,952    | 0,948      | 0,932  |
| Faroese                 | 0,912 | 0        | 0          | 0,618  |
| Finnish                 | 0,988 | 0,998    | 0,998      | 0,994  |
| French                  | 0,946 | 0,996    | 0,99       | 0,992  |
| Galician                | 0,89  | 0,912    | 0          | 0,93   |
| Georgian                | 0,974 | 0,976    | 0          | 0,976  |
| German                  | 0,958 | 0,984    | 0,978      | 0,978  |
| Guarani                 | 0,968 | 0,728    | 0          | 0      |
| Gujarati                | 0,932 | 0,932    | 0,93       | 0,932  |
| Haitian Creole          | 0,988 | 0,536    | 0          | 0,99   |
| Hausa                   | 0,976 | 0        | 0          | 0      |
| Hebrew                  | 0,994 | 0,996    | 0,998      | 0,998  |
| Hindi                   | 0,982 | 0,984    | 0,982      | 0,972  |
| Hungarian               | 0,96  | 0,988    | 0,968      | 0,986  |
| Icelandic               | 0,984 | 0,996    | 0          | 0,996  |
| Ido                     | 0     | 0,76     | 0          | 0      |
| Igbo                    | 0,798 | 0        | 0          | 0      |
| Indonesian              | 0,88  | 0,946    | 0,958      | 0,836  |
| Interlingua             | 0,27  | 0,688    | 0          | 0      |
| Interlingue             | 0,198 | 0,192    | 0          | 0      |
| Irish                   | 0,968 | 0,978    | 0          | 0,984  |
| Italian                 | 0,866 | 0,948    | 0,932      | 0,936  |
| Japanese                | 0,97  | 0,986    | 0,98       | 0,986  |
| Javanese                | 0     | 0,864    | 0          | 0,938  |
| Kannada                 | 0,998 | 0,998    | 0,998      | 0,998  |
| Kazakh                  | 0,978 | 0,992    | 0          | 0,916  |
| Kinyarwanda             | 0,86  | 0        | 0          | 0,44   |
| Kirghiz                 | 0,974 | 0,99     | 0          | 0,408  |
| Komi                    | 0     | 0,544    | 0          | 0      |
| Korean                  | 0,986 | 0,99     | 0,988      | 0,99   |
| Kurdish                 | 0     | 0,972    | 0          | 0,976  |
| Lao                     | 0,84  | 0,842    | 0          | 0,85   |
| Latin                   | 0,778 | 0,864    | 0          | 0,854  |
| Latvian                 | 0,98  | 0,992    | 0,992      | 0,99   |
| Limburgan               | 0     | 0,324    | 0          | 0      |
| Lingala                 | 0,85  | 0        | 0          | 0      |
| Lithuanian              | 0,96  | 0,976    | 0,974      | 0,97   |
| Luganda                 | 0,952 | 0        | 0          | 0      |
| Luxembourgish           | 0,864 | 0,894    | 0          | 0,93   |
| Macedonian              | 0,88  | 0,984    | 0,982      | 0,974  |
| Malagasy                | 0,99  | 0,99     | 0          | 0,988  |
| Malay                   | 0,896 | 0,586    | 0          | 0,39   |
| Malayalam               | 0,988 | 0,988    | 0,988      | 0,988  |
| Maltese                 | 0,962 | 0,966    | 0          | 0,964  |
| Manx                    | 0,972 | 0,294    | 0          | 0      |
| Maori                   | 0,994 | 0        | 0          | 0      |
| Marathi                 | 0,958 | 0,966    | 0,964      | 0,942  |
| Modern Greek            | 0,99  | 0,992    | 0,99       | 0,992  |
| Mongolian               | 0,964 | 0,994    | 0          | 0,996  |
| Navajo                  | 0     | 0        | 0          | 0      |
| Nepali (macrolanguage)  | 0,96  | 0,98     | 0,978      | 0,922  |
| Northern Sami           | 0     | 0        | 0          | 0,866  |
| Norwegian Nynorsk       | 0,94  | 0,79     | 0          | 0,796  |
| Occitan                 | 0,66  | 0,48     | 0          | 0,724  |
| Oriya                   | 0,96  | 0,958    | 0          | 0,96   |
| Oromo                   | 0,956 | 0        | 0          | 0      |
| Ossetian                | 0     | 0,938    | 0          | 0      |
| Panjabi                 | 0,994 | 0,994    | 0,994      | 0,994  |
| Persian                 | 0,992 | 0,998    | 0,996      | 0,998  |
| Polish                  | 0,982 | 0,998    | 0,998      | 0,992  |
| Portuguese              | 0,908 | 0,956    | 0,946      | 0,952  |
| Pushto                  | 0,938 | 0,922    | 0          | 0,754  |
| Quechua                 | 0,926 | 0,808    | 0          | 0,852  |
| Romanian                | 0,932 | 0,986    | 0,984      | 0,984  |
| Romansh                 | 0,934 | 0,328    | 0          | 0      |
| Russian                 | 0,728 | 0,986    | 0,984      | 0,988  |
| Sanskrit                | 0,964 | 0,976    | 0          | 0      |
| Sardinian               | 0     | 0,01     | 0          | 0      |
| Scottish Gaelic         | 0,964 | 0,942    | 0          | 0      |
| Serbian                 | 0,942 | 0,946    | 0          | 0,902  |
| Serbo-Croatian          | 0     | 0,402    | 0          | 0      |
| Shona                   | 0,844 | 0        | 0          | 0      |
| Sindhi                  | 0,978 | 0,982    | 0          | 0      |
| Sinhala                 | 0,962 | 0,962    | 0          | 0,962  |
| Slovak                  | 0,964 | 0,974    | 0,982      | 0,97   |
| Slovene                 | 0,876 | 0,966    | 0,968      | 0,946  |
| Somali                  | 0,924 | 0,696    | 0,956      | 0      |
| Spanish                 | 0,894 | 0,986    | 0,976      | 0,98   |
| Standard Chinese        | 0,946 | 0,984    | 0,746      | 0,978  |
| Sundanese               | 0,91  | 0,854    | 0          | 0      |
| Swahili (macrolanguage) | 0,924 | 0,92     | 0,938      | 0,934  |
| Swedish                 | 0,872 | 0,994    | 0,992      | 0,986  |
| Tagalog                 | 0,928 | 0,972    | 0,974      | 0,964  |
| Tajik                   | 0,82  | 0,85     | 0          | 0      |
| Tamil                   | 0,992 | 0,992    | 0,992      | 0,994  |
| Tatar                   | 0,978 | 0,984    | 0          | 0      |
| Telugu                  | 0,958 | 0,958    | 0,958      | 0,96   |
| Thai                    | 0,988 | 0,988    | 0,988      | 0,988  |
| Tibetan                 | 0,986 | 0,992    | 0          | 0      |
| Tongan                  | 0,968 | 0        | 0          | 0      |
| Tswana                  | 0,928 | 0        | 0          | 0      |
| Turkish                 | 0,968 | 0,986    | 0,982      | 0,976  |
| Turkmen                 | 0,94  | 0,936    | 0          | 0      |
| Uighur                  | 0,978 | 0,986    | 0          | 0,964  |
| Ukrainian               | 0,97  | 0,988    | 0,986      | 0,986  |
| Urdu                    | 0,86  | 0,958    | 0,89       | 0,896  |
| Uzbek                   | 0,984 | 0,99     | 0          | 0      |
| Vietnamese              | 0,978 | 0,986    | 0,984      | 0,984  |
| Volapük                 | 0,994 | 0,982    | 0          | 0,986  |
| Walloon                 | 0     | 0,664    | 0          | 0,98   |
| Welsh                   | 0,98  | 0,992    | 0,992      | 0,984  |
| Western Frisian         | 0,888 | 0,956    | 0          | 0      |
| Wolof                   | 0,926 | 0        | 0          | 0      |
| Xhosa                   | 0,928 | 0        | 0          | 0,912  |
| Yiddish                 | 0,956 | 0,958    | 0          | 0      |
| Yoruba                  | 0,75  | 0,262    | 0          | 0      |


## References
[1] A. Joulin, E. Grave, P. Bojanowski, T. Mikolov, [Bag of Tricks for Efficient Text Classification](https://arxiv.org/abs/1607.01759)

```
@article{joulin2016bag,
  title={Bag of Tricks for Efficient Text Classification},
  author={Joulin, Armand and Grave, Edouard and Bojanowski, Piotr and Mikolov, Tomas},
  journal={arXiv preprint arXiv:1607.01759},
  year={2016}
}
```

[2] A. Joulin, E. Grave, P. Bojanowski, M. Douze, H. Jégou, T. Mikolov, [FastText.zip: Compressing text classification models](https://arxiv.org/abs/1612.03651)

```
@article{joulin2016fasttext,
  title={FastText.zip: Compressing text classification models},
  author={Joulin, Armand and Grave, Edouard and Bojanowski, Piotr and Douze, Matthijs and J{\'e}gou, H{\'e}rve and Mikolov, Tomas},
  journal={arXiv preprint arXiv:1612.03651},
  year={2016}
}
```
