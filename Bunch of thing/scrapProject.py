import json
import re

import psycopg2
import requests
from bs4 import BeautifulSoup

# Remplacez par vos propres informations de connexion
conn = psycopg2.connect(
    host="localhost",
    database="math_graph",
    user="tristanrigaud-humbert",
    port="5432",
    password=""
)
cursor = conn.cursor()


def get_final_wikipedia_page(title:str) -> str:
    url = f"https://fr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "redirects": 1,
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()

    page = list(data["query"]["pages"].values())[0]
    return page.get("title", title)  # Renvoie le titre final après redirection




# Renvoie le Html sous forme de chaine de caractère d'une page wikipédia à partir de son nom
def get_wikipedia_page(title: str, lang='fr'):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "error" in data:
        print(f"Erreur : {data['error']['info']}")
        return None
    return data.get('parse', {}).get('text', {}).get('*', '')


def convert_to_latex(formula):
    """Convertit une équation en LaTeX si possible."""
    if formula.startswith("Image Equation:"):
        return f"\\({formula.replace('Image Equation: ', '')}\\)"
    return f"\\[{formula}\\]"


def get_section_text(soup):
    section = soup.find(id="Énoncé")
    if not section:
        return None  # La section n'existe pas

    content = []
    elem = section.parent.find_next_sibling()  # Premier élément après le h3

    while elem and elem.name != "div":  # Tant qu'on n'atteint pas un autre h3
        # Extraire texte brut
        text_part = elem.get_text(" ", strip=True)
        # Récupérer les formules mathématiques
        math_expressions = elem.find_all(class_="mwe-math-element")
        for math1 in math_expressions:
            math2 = math1.find("math")
            # Convertir MathML en texte (simplifié)
            latex_code = f" $$ {math2.get('alttext')} $$ "
            text_part = text_part.replace(math1.get_text(" ", strip=True), latex_code)

        content.append(text_part)
        elem = elem.find_next_sibling()  # Passer à l'élément suivant

    return "\n".join(content)


# Query pour obtenir l'énoncé du théorème
def getEnonce(theo):
    soup = BeautifulSoup(theo, "html.parser")
    title = soup.find(class_="theoreme")
    if title:
        a = title.find(class_="theoreme-nom")
        b = title.find(class_="theoreme-tiret")
        if a:
            a.decompose()
        if b:
            b.decompose()

        content = []
        text_part = title.get_text(" ", strip=True)

        # Récupérer les formules mathématiques
        math_expressions = title.find_all(class_="mwe-math-element")
        for math1 in math_expressions:
            math2 = math1.find("math")
            # Convertir MathML en texte (simplifié)
            latex_code = f" $$ {math2.get('alttext')} $$ "

            text_part = text_part.replace(math1.get_text(" ", strip=True), latex_code)

        # Supprimer les {\displaystyle ...}
        text_part = re.sub(r'{\\displaystyle\s*([^}]*)}', r'\1', text_part)

        # Supprimer les espaces mal placés
        text_part = re.sub(r'\s+', ' ', text_part).strip()
        return text_part
    else:
         enonce = get_section_text(soup)
         return enonce

a = get_wikipedia_page("Lemme de Levi")
b = getEnonce(a)
print(b)
# Revoie le dictionnaire des langues avec le nom de la page donnée en entrée traduit
def get_translations(page_title: str):
    url = "https://fr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "langlinks",
        "lllimit": "max",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Récupérer les pages
    pages = data['query']['pages']
    translations = {}

    for page_id, page in pages.items():
        if 'langlinks' in page:
            for ll in page['langlinks']:
                translations[ll['lang']] = ll['*']  # Langue et titre de la traduction

    return translations


# Crée un json à partir de la liste des théorèmes de wikipédia
def ListeTheo():
    # URL de l'API de Wikipédia pour la page "Liste de théorèmes"
    url = "https://fr.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": "Liste_de_théorèmes",
        "prop": "text",
        "format": "json"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Extraire le contenu HTML de la page
    html_content = data['parse']['text']['*']

    # Analyser le contenu HTML pour extraire les noms des théorèmes
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')

    # Trouver tous les éléments de liste (<li>) contenant des liens (<a>)
    theoremes = []
    for li in soup.find_all('li'):
        a_tag = li.find('a')
        if a_tag and 'title' in a_tag.attrs:
            theoremes.append(a_tag.attrs['title'])

    # Enregistrer les noms des théorèmes dans un fichier JSON
    with open('../JSONFILE/theoremes.json', 'w', encoding='utf-8') as json_file:
        json.dump(theoremes, json_file, ensure_ascii=False, indent=4)

    print("Liste des théorèmes enregistrée dans 'theoremes.json'")

def ListeLemme():
    # URL de l'API de Wikipédia pour la page "Liste de théorèmes"
    url = "https://fr.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": "Liste_de_lemmes",
        "prop": "text",
        "format": "json"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Extraire le contenu HTML de la page
    html_content = data['parse']['text']['*']

    # Analyser le contenu HTML pour extraire les noms des théorèmes
    soup = BeautifulSoup(html_content, 'html.parser')

    # Trouver tous les éléments de liste (<li>) contenant des liens (<a>)
    lemme = []
    for li in soup.find_all('li'):
        a_tag = li.find('a')
        if a_tag and 'title' in a_tag.attrs:
            lemme.append(a_tag.attrs['title'])

    # Enregistrer les noms des théorèmes dans un fichier JSON
    with open('../JSONFILE/lemme.json', 'w', encoding='utf-8') as json_file:
        json.dump(lemme, json_file, ensure_ascii=False, indent=4)

    print("Liste des lemme enregistrée dans 'lemme.json'")


# Sépare en Deux la liste des théorèmes en fonction de l'existence de leur page wikipédia
def SeparationThoreme():
    theoremeCODE = open("../JSONFILE/theoremes.json")
    theoremes = json.load(theoremeCODE)
    theoremeListe1 = []
    theoremeListe2 = []

    print(theoremes)
    for i in theoremes:
        if ("inexistante" not in i):
            theoremeListe1.append(i)
        else:
            theoremeListe2.append(i)

    with open('../JSONFILE/theoremesExiste.json', 'w', encoding='utf-8') as json_file:
        json.dump(theoremeListe1, json_file, ensure_ascii=False, indent=4)
    with open('../JSONFILE/theoremesPageVide.json', 'w', encoding='utf-8') as json_file:
        json.dump(theoremeListe2, json_file, ensure_ascii=False, indent=4)
    return

def SeparationLemme():
    lemmeCode = open("../JSONFILE/lemme.json")
    lemme = json.load(lemmeCode)
    theoremeListe1 = []
    theoremeListe2 = []

    print(lemme)
    for i in lemme:
        if ("inexistante" not in i):
            theoremeListe1.append(i)
        else:
            theoremeListe2.append(i)

    with open('../JSONFILE/lemmeExiste.json', 'w', encoding='utf-8') as json_file:
        json.dump(theoremeListe1, json_file, ensure_ascii=False, indent=4)
    with open('../JSONFILE/lemmePageVide.json', 'w', encoding='utf-8') as json_file:
        json.dump(theoremeListe2, json_file, ensure_ascii=False, indent=4)
    return


"""
page_title = "Théorème_de_Pythagore"
translations = get_translations(page_title)

# Afficher les traductions
for lang, title in translations.items():
    print(f"Langue: {lang}, Titre: {title}")
"""
L = []


def Inject(nom:str, typeMath:str):
    nom = get_final_wikipedia_page(nom)
    cursor.execute("SELECT nom FROM concepts WHERE nom = %s", (nom,))
    result = cursor.fetchone()
    if result is None:  # Le Théorème n'est pas encore dans la base de donnée
        pageHTML = get_wikipedia_page(nom)
        enonce: str = getEnonce(pageHTML)
        if enonce:  # On vérifie que l'énoncé n'est pas None
            cursor.execute("INSERT INTO concepts (nom,type,enonce) VALUES (%s, %s,%s)", (nom, typeMath, enonce))
            tradDict = get_translations(nom)
            keysTrad = list(tradDict.keys())
            for key in keysTrad:
                cursor.execute("""INSERT INTO foreign_name ("Nom francais","Nom étranger",langue) VALUES (%s, %s,%s)""",
                               (nom, tradDict[key], key))
            cursor.execute("SELECT * FROM concepts WHERE nom = %s", (nom,))
            result = cursor.fetchone()
            if result:
                print(f"Insertion confirmée : {result}")
            else:
                print("Échec de l’insertion.")
                L.append(nom)
        else:
            print(nom + " : Pas d'énoncé")
            L.append(nom)
        conn.commit()  # Valide la transaction


def AutomatisationTheoremeJson(file):
    fileJ = json.load(file)
    i = 0
    for nom in fileJ:
        Inject(nom,"théorème")
        i += 1
        print(i)


def AutomatisationLemmeJson(file):
    fileJ = json.load(file)
    i = 0
    for nom in fileJ:
        Inject(nom,"lemme")
        i += 1
        print(i)


AutomatisationLemmeJson(open("../JSONFILE/lemmeExiste.json"))
# Fonction pour obtenir le vrai nom d'une page en cas de redirection




#AutomatisationJson(open("TheoremeRestant2.json"))




""" Extrait les théorèmes et démos du site les-mathématiques
url="https://les-mathematiques.net/lexique_mathematique?combine=Th%C3%A9or%C3%A8me"
f = open('math.txt', 'r', encoding='utf-8')
soup = BeautifulSoup(f,'html.parser')
a = soup.find(class_="row")
while a :
    titre = a.find(class_="term").getText().strip()
    lien = a.find('a')
    lien.extract()
    elem = a.find(class_="chapo")
    enonce = elem.get_text(" ", strip=True)
    a = a.find_next_sibling()
    cursor.execute("SELECT nom FROM concepts WHERE nom = %s", (titre,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO concepts (nom,type,enonce) VALUES (%s, %s,%s)", (titre, "théorème", enonce))
    cursor.execute("SELECT * FROM concepts WHERE nom = %s", (titre,))
    result = cursor.fetchone()
    if result:
        print(f"Insertion confirmée : {result}")
    else:
        print("Échec de l’insertion.")
"""
conn.commit()  # Valide la transaction



with open('../JSONFILE/LemmeRestant.json', 'w', encoding='utf-8') as json_file:
    json.dump(L, json_file, ensure_ascii=False, indent=4)

# Fermeture de la connexion
cursor.close()
conn.close()
