import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from PIL import Image
from io import BytesIO

# Configuration de la page Streamlit
st.set_page_config(page_title="Top IMDb Films", page_icon=":clapper:", layout="wide")

@st.cache_data
def scrape_imdb(url):
    # Création de l'en-tête pour la requête HTTP afin de mimer un navigateur et éviter le blocage par IMDb
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraction des informations des films
    films = soup.find_all('li', class_='ipc-metadata-list-summary-item')
    
    titles = []
    annees_films = []
    duree_films = []
    restrictions = []
    acteurs_films = []
    realisateur_films = []
    score_films = []
    metacritic_films = []
    posters = []
    imdb_links = []

    for film in films:
        # Extraction des titres
        title_tag = film.find('h3', class_='ipc-title__text')
        if title_tag:
            titles.append(title_tag.text.strip())
            # Extraction du lien IMDb
            link_tag = title_tag.find('a')
            if link_tag and 'href' in link_tag.attrs:
                imdb_links.append("https://www.imdb.com" + link_tag['href'])
            else:
                imdb_links.append(None)
        else:
            titles.append(None)
            imdb_links.append(None)

        # Extraction des autres informations (année, durée, restrictions)
        metadata = film.find('div', class_='sc-5bc66c50-5 hVarDB dli-title-metadata')
        if metadata:
            spans = metadata.find_all('span', class_='sc-5bc66c50-6 OOdsw dli-title-metadata-item')
            # Année du film
            if len(spans) > 0:
                annees_films.append(spans[0].text.strip())
            else:
                annees_films.append(None)
            # Durée du film
            if len(spans) > 1:
                duree_films.append(spans[1].text.strip())
            else:
                duree_films.append(None)
            # Restrictions d'âge du film
            if len(spans) > 2:
                restrictions.append(spans[2].text.strip())
            else:
                restrictions.append(None)
        else:
            annees_films.append(None)
            duree_films.append(None)
            restrictions.append(None)

        # Extraction des acteurs principaux (les 3 premiers)
        acteurs = film.find_all('a', class_='ipc-link ipc-link--base dli-cast-item')
        acteurs_text = [acteur.text.strip() for acteur in acteurs[:3]]  # Limiter à 3 acteurs
        acteurs_films.append(', '.join(acteurs_text))

        # Extraction du réalisateur
        realisateur = film.find('a', class_='ipc-link ipc-link--base dli-director-item')
        if realisateur:
            realisateur_films.append(realisateur.text.strip())
        else:
            realisateur_films.append(None)

        # Extraction du score du film
        score_tag = film.find('span', class_='sc-b0901df4-0 bXIOoL metacritic-score-box')
        if score_tag:
            score_films.append(score_tag.text.strip())
        else:
            score_films.append(None)

        # Extraction du score Metacritic
        metacritic_tag = film.find('span', class_='metacritic-score-label')
        if metacritic_tag:
            metacritic_films.append(metacritic_tag.text.strip())
        else:
            metacritic_films.append(None)

        # Extraction de l'affiche du film
        poster_tag = film.find('div', class_='ipc-poster ipc-poster--base ipc-poster--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2')
        if poster_tag:
            poster_img_tag = poster_tag.find('img')
            if poster_img_tag and 'src' in poster_img_tag.attrs:
                posters.append(poster_img_tag['src'])
            else:
                posters.append(None)
        else:
            posters.append(None)

    # Créer un DataFrame avec les informations extraites
    movies_df = pd.DataFrame({
        'Title': titles,  # Titre du film
        'Year': annees_films,  # Année de sortie du film
        'Runtime': duree_films,  # Durée du film
        'Restrictions': restrictions,  # Restrictions d'âge du film
        'Director': realisateur_films,  # Réalisateur du film
        'Actors': acteurs_films,  # Acteurs principaux du film
        'Score': score_films,  # Score du film
        'Metacritic': metacritic_films,  # Score Metacritic du film
        'Poster': posters,  # Affiche du film
        'IMDb Link': imdb_links  # Lien vers la page IMDb
    })

    return movies_df

# Application Streamlit
st.title("Top 50 Films selon IMDb")
st.sidebar.header("Options de Scraping")

# Input URL IMDb par l'utilisateur
user_url = st.sidebar.text_input("Entrer l'URL IMDb à scraper :", value="https://www.imdb.com/list/ls055386972/")

# Ajouter un slider pour filtrer par année de sortie
year_filter = st.sidebar.slider("Année de sortie", 1970, 2024, (1970, 2024))

# Barre de recherche pour les films, acteurs ou réalisateurs
search_term = st.sidebar.text_input("Rechercher un film, un acteur ou un réalisateur :")

# Bouton de scraping
if st.sidebar.button("Scraper les données"):
    movies_df = scrape_imdb(user_url)

    # Filtrer les films sortis à partir de l'année spécifiée dans le slider
    filtered_movies_df = movies_df[movies_df['Year'].apply(lambda x: x.isdigit() and year_filter[0] <= int(x) <= year_filter[1] if x else False)]

    # Filtrer par terme de recherche
    if search_term:
        filtered_movies_df = filtered_movies_df[filtered_movies_df.apply(lambda row: search_term.lower() in str(row['Title']).lower() or search_term.lower() in str(row['Actors']).lower() or search_term.lower() in str(row['Director']).lower(), axis=1)]

    # Affichage du DataFrame filtré avec les affiches des films
    for index, row in filtered_movies_df.iterrows():
        cols = st.columns([1, 3])
        with cols[0]:
            if row['Poster']:
                response = requests.get(row['Poster'])
                img = Image.open(BytesIO(response.content))
                st.image(img, caption=row['Title'], use_column_width=True)
        with cols[1]:
            st.subheader(row['Title'])
            st.write(f"Année de sortie : {row['Year']}")
            st.write(f"Durée : {row['Runtime']}")
            st.write(f"Restrictions : {row['Restrictions']}")
            st.write(f"Réalisateur : {row['Director']}")
            st.write(f"Acteurs : {row['Actors']}")
            st.write(f"Score : {row['Score']}")
            st.write(f"Metacritic : {row['Metacritic']}")
            if row['IMDb Link']:
                st.markdown(f"[Voir sur IMDb]({row['IMDb Link']})")
            user_note = st.text_area(f"Votre note pour '{row['Title']}'", key=f"note_{index}")

    # Bouton pour télécharger les données au format CSV
    csv = filtered_movies_df.to_csv(index=False)
    st.download_button(label="Télécharger les données en CSV", data=csv, file_name='imdb_movies.csv', mime='text/csv')

    # Animation lors du chargement des données
    with st.spinner('Scraping en cours... Merci de patienter...'):
        st.success('Scraping terminé avec succès!')
else:
    st.write("Cliquez sur le bouton de la barre latérale pour lancer le scraping.")