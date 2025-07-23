from flask import Flask, request,jsonify, render_template
import pickle
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)


# Function to load movie data
def load_movie_data():
    """Loads the movie list and similarity matrix from pickle files.

    Returns:
        tuple: A tuple containing the movie list and similarity matrix."""
    try:
        with open('C:\\Users\\tarun\\Documents\\Coding\\CinemaScope\\artificats\\movie_list.pkl', 'rb') as f:  # 'rb' mode
            movies = pickle.load(f)

        with open('C:\\Users\\tarun\\Documents\\Coding\\CinemaScope\\artificats\\similarity.pkl', 'rb') as f:  # 'rb' mode
            similarity = pickle.load(f)

        return movies, similarity

    except FileNotFoundError:
        print("Error: Pickle files not found. Please ensure they exist in the 'artifacts' directory.")
        return None, None
def fetch_poster(movie_id, retries=3, backoff_factor=1.5):
    """Fetches the poster image for a given movie ID from TMDb API."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=af2d698601b5dc07afb6a8eef1505bfe&language=en-US"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Check if status code is 4xx or 5xx
            data = response.json()
            
            # Check if the poster_path exists in the response
            poster_path = data.get('poster_path')
            if poster_path:
                full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
                return full_path
            else:
                # Log that the movie has no poster
                print(f"No poster available for movie_id: {movie_id}")
                return "https://via.placeholder.com/500"  # Placeholder for missing posters
        
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:  # API rate limit exceeded
                print("Rate limit exceeded. Retrying after delay...")
                time.sleep(2)  # Short delay before retrying
            else:
                print(f"HTTP error occurred: {http_err}")
        
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                sleep_time = backoff_factor ** attempt
                time.sleep(sleep_time)
            else:
                return "https://via.placeholder.com/500"  # Placeholder in case of failure

    return "https://via.placeholder.com/500"  # Return placeholder if retries fail

# Recommend movies based on similarity
def recommend(movie):
    # Convert the input movie title to uppercase
    movie = movie.upper()
    
    # Find matching movies based on the input (case-insensitive and partial match)
    matching_movies = movies[movies['title'].str.upper().str.contains(movie, na=False)]
    
    if matching_movies.empty:
        print(f"No movies found containing '{movie}'.")
        return [], []  # Return empty lists if no matches found
    
    # Get the index of the first matching movie
    index = matching_movies.index[0]
    
    # Calculate distances based on similarity
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    # Lists to hold recommended movie names and their posters
    recommended_movie_names = []
    recommended_movie_posters = []
    
    # Get the top recommended movies (we want at least 10)
    for i in distances[1:]:  # Start from the second one to exclude the input movie
        movie_id = movies.iloc[i[0]].movie_id  # Assuming movie_id exists in movies
        recommended_movie_posters.append(fetch_poster(movie_id))  # Function to fetch poster
        recommended_movie_names.append(movies.iloc[i[0]].title)  # Get movie title

        if len(recommended_movie_names) >= 10:  # Check if we have at least 10 titles
            break

    # If fewer than 10 titles were found, add duplicates or fallback titles
    while len(recommended_movie_names) < 10:
        recommended_movie_names.append(recommended_movie_names[-1])  # Duplicate the last title
        recommended_movie_posters.append(recommended_movie_posters[-1])  # Duplicate the last poster

    return recommended_movie_names, recommended_movie_posters

# Load movie data globally
movies, similarity = load_movie_data()

@app.route('/index')
def index():
    if movies is None or similarity is None:
        return "Error: Movie data could not be loaded."
    
    movie_list = movies['title'].values
    return render_template('index.html', movie_list=movie_list)

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    movie_name = request.form['movie'].strip()  # Get the movie name and strip whitespace
    recommended_movie_names, recommended_movie_posters = recommend(movie_name)  # Call the recommend function
    print(recommended_movie_names, recommended_movie_posters)  # Debug line

    return render_template(
        'search-results.html',
        movie_name=movie_name,
        recommended_movie_names=recommended_movie_names,
        recommended_movie_posters=recommended_movie_posters
    )

# Corrected route for search results page
@app.route('/search-results')
def search_results():
    query = request.args.get('query', '').strip()  # Get the query and strip whitespace
    
    recommended_movie_names, recommended_movie_posters = recommend(query)
    
    return render_template('search-results.html', 
                           movie_name=query, 
                           recommended_movie_names=recommended_movie_names,
                           recommended_movie_posters=recommended_movie_posters)

@app.route('/')
def home():
    return render_template('index.html')
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def load_data():
    with open('artificats/webseriesdata.pkl', 'rb') as file:
        data = pickle.load(file)
    return data

@app.route('/web_series')
def display_webseries():
    webseries = load_data()  # Load the data from the pickle file
    return render_template('webseries.html', webseries=webseries)


with open('genres_list.pkl', 'rb') as file:
    genres_data = pickle.load(file)

@app.route('/genremovies/<genre>')
def display_movies_by_genre(genre):
    genre = genre.lower()
    # Reload the DataFrame from the pickle file
    movies = pd.read_pickle('genres_list.pkl')
    
    # Filter out rows with missing values in 'Genre' to avoid errors
    genre_movies = movies.dropna(subset=['Genre'])
    genre_movies = genre_movies[genre_movies['Genre'].str.lower().str.contains(genre, na=False)]

    # Convert to dictionary format for easy access in the template
    movies_data = genre_movies.to_dict(orient='records')

    # Render the HTML template
    return render_template('genremovies.html', genre=genre.capitalize(), movies=movies_data)



@app.route('/about_us')
def about_us():
    return render_template('about.html')
@app.route('/contact_us')
def contact_():
    return render_template('contact.html')
@app.route('/question')
def question():
    return render_template('question.html')
@app.route('/policy')
def policy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(debug=True)
