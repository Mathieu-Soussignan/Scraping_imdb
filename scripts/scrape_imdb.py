import requests
from bs4 import BeautifulSoup
import pandas as pd
import h5py

# URL de la page IMDb contenant les 50 films les mieux notés
url = "https://www.imdb.com/list/ls055386972/"

# Création de l'en-tête pour la requête HTTP afin de mimer un navigateur et éviter le blocage par IMDb
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Initialisation des listes pour stocker les informations
titles = []
user_votes = []
mean_ratings = []

# Extraction des informations des films
films = soup.find_all('li', class_='ipc-metadata-list-summary-item')

for film in films:
    # Extraction des titres
    title_tag = film.find('h3', class_='ipc-title__text')
    if title_tag:
        titles.append(title_tag.text.strip())
    else:
        titles.append(None)

    # Extraction du nombre de votes d'utilisateurs
    votes_tag = film.find('span', 'ipc-rating-star--voteCount')
    if votes_tag:
        cleaned_votes = votes_tag.text.replace("M", "000000").replace("K", "000").replace(",", "").replace("(", "").replace(")", "").strip()
        user_votes.append(cleaned_votes)
    else:
        user_votes.append(None)

    # Extraction de la note moyenne
    rating_tag = film.find('span', class_='ipc-rating-star--rating')
    if rating_tag:
        mean_ratings.append(rating_tag.text.strip())
    else:
        mean_ratings.append(None)

# Créer des DataFrames avec les informations extraites
movies_df = pd.DataFrame({
    'Title': titles
})

popularity_df = pd.DataFrame({
    'Title': titles,
    'User Votes': user_votes,
    'Mean Rating': mean_ratings
})

# Sauvegarder les DataFrames dans un fichier HDF5
with h5py.File('../data/movies_data.h5', 'w') as f:
    f.create_dataset("movies", data=movies_df.to_numpy(dtype='S'))
    f.create_dataset("popularity", data=popularity_df.to_numpy(dtype='S'))