import pandas as pd
import numpy as np
import pyodbc
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Database configuration for KEVSER server
DB_CONFIG = {
    'DRIVER': '{SQL Server}',
    'SERVER': 'KEVSER', 
    'DATABASE': 'gonullupusula',  
    'Trusted_Connection': 'yes'
}

# Global variables to store model data
event_vectors = None
vectorizer = None
knn = None
user_event_matrix = None
events = None
participation = None
users = None
event_features = None  # Global variable for event features

# Function to fetch data from SQL Server
def fetch_data():
    try:
        connection_string = (
            f"mssql+pyodbc://{DB_CONFIG['SERVER']}/{DB_CONFIG['DATABASE']}?"
            f"driver={DB_CONFIG['DRIVER'][1:-1]}&trusted_connection={DB_CONFIG['Trusted_Connection']}"
        )
        engine = create_engine(connection_string)
        
        queries = {
            "users": "SELECT * FROM Kullanicilar",
            "events": "SELECT * FROM Etkinlikler",
            "participation": "SELECT * FROM Katilimlar",
            "categories": "SELECT * FROM Kullanici_Kategorileri"
        }
        
        data = {key: pd.read_sql(query, engine) for key, query in queries.items()}
        return data
    
    except Exception as e:
        print("Database connection error:", e)
        return None

# Function to initialize recommendation models
def initialize_models():
    global event_vectors, vectorizer, knn, user_event_matrix, events, participation, users, event_features
    
    data = fetch_data()
    if not data:
        raise ValueError("Failed to fetch data! Check connection.")
    
    users, events, participation, categories = data.values()
    
    # Content-based recommendation setup
    event_features = events[['Etkinlik_ID', 'E_Aciklama']].fillna("")
    event_features['combined'] = event_features['E_Aciklama']
    
    vectorizer = TfidfVectorizer()
    event_vectors = vectorizer.fit_transform(event_features['combined'])
    
    # Collaborative filtering setup
    user_event_matrix = participation.pivot(index='Kullanici_ID', columns='Etkinlik_ID', values='Tarih').fillna(0)
    user_event_matrix = user_event_matrix.reindex(users['Kullanici_ID'], fill_value=0)
    user_event_matrix = user_event_matrix.map(lambda x: 1 if x != 0 else 0)
    user_event_matrix = user_event_matrix.astype(bool).astype(int)
    
    knn = NearestNeighbors(metric='cosine', algorithm='brute')
    knn.fit(user_event_matrix)
    
    print("Models initialized successfully!")

# Content-based recommendation function
def content_based_recommendation(event_id, top_n=5):
    try:
        similarities = cosine_similarity(event_vectors)
        event_idx = events[events['Etkinlik_ID'] == event_id].index[0]
        similar_indices = similarities[event_idx].argsort()[-top_n-1:-1][::-1]
        return events.iloc[similar_indices]['Etkinlik_ID'].tolist()
    except Exception as e:
        print(f"Content-based recommendation error: {e}")
        return []

# Department-based recommendation function
def department_based_recommendation(user_id, top_n=5):
    try:
        user_dept = users.loc[users['Kullanici_ID'] == user_id, 'Bolum'].values[0]
        if pd.isna(user_dept) or user_dept == '':
            return []
            
        combined_dept = event_features['combined'] + " " + user_dept
        vectorizer_dept = TfidfVectorizer()
        event_vectors_dept = vectorizer_dept.fit_transform(combined_dept)
        similarities_dept = cosine_similarity(event_vectors_dept)
        avg_similarities = similarities_dept.mean(axis=0)
        recommended_indices = avg_similarities.argsort()[-top_n:][::-1]
        return events.iloc[recommended_indices]['Etkinlik_ID'].tolist()
    except Exception as e:
        print(f"Department-based recommendation error: {e}")
        return []

# Collaborative filtering recommendation function
def collaborative_recommendation(user_id, top_n=5):
    try:
        if user_id not in user_event_matrix.index:
            return []
        
        n_samples = user_event_matrix.shape[0]
        n_neighbors = min(top_n + 1, n_samples)
        
        distances, indices = knn.kneighbors(user_event_matrix.loc[[user_id]], n_neighbors=n_neighbors)
        recommended_events = set()
        
        for i in range(1, indices.shape[1]):
            similar_user_id = user_event_matrix.index[indices.flatten()[i]]
            similar_user_events = participation.loc[participation['Kullanici_ID'] == similar_user_id, 'Etkinlik_ID'].tolist()
            recommended_events.update(similar_user_events)
        
        return list(recommended_events)[:top_n]
    except Exception as e:
        print(f"Collaborative filtering error: {e}")
        return []

# Department-based collaborative filtering function
def collaborative_recommendation_with_dept(user_id, top_n=5):
    try:
        try:
            user_dept = users.loc[users['Kullanici_ID'] == user_id, 'Bolum'].values[0]
        except IndexError:
            return []
        if pd.isna(user_dept) or user_dept == '':
            return []
        similar_dept_users = users.loc[users['Bolum'] == user_dept, 'Kullanici_ID'].tolist()
        dept_user_events = participation[participation['Kullanici_ID'].isin(similar_dept_users)]
        
        user_event_matrix_dept = dept_user_events.pivot(index='Kullanici_ID', columns='Etkinlik_ID', values='Tarih').fillna(0)
        user_event_matrix_dept = (user_event_matrix_dept != 0).astype(int)
        
        if user_id not in user_event_matrix_dept.index or user_event_matrix_dept.shape[0] < 2:
            return []
        
        n_samples = user_event_matrix_dept.shape[0]
        n_neighbors = min(top_n + 1, n_samples)
        knn_dept = NearestNeighbors(metric='cosine', algorithm='brute')
        knn_dept.fit(user_event_matrix_dept)
        
        distances, indices = knn_dept.kneighbors(user_event_matrix_dept.loc[[user_id]], n_neighbors=n_neighbors)
        recommended_events = set()
        for i in range(1, n_neighbors):
            similar_user_id = user_event_matrix_dept.index[indices.flatten()[i]]
            similar_user_events = participation.loc[participation['Kullanici_ID'] == similar_user_id, 'Etkinlik_ID'].tolist()
            recommended_events.update(similar_user_events)
        return list(recommended_events)[:top_n]
    except Exception as e:
        print(f"Department-based collaborative filtering error: {e}")
        return []

# Hybrid recommendation function
def hybrid_recommendation(user_id, top_n=5):
    try:
        user_participations = participation.loc[participation['Kullanici_ID'] == user_id, 'Etkinlik_ID'].tolist()
        
        content_based_results = []
        for event_id in user_participations:
            content_based_results.extend(content_based_recommendation(event_id, top_n))
        
        collaborative_results = collaborative_recommendation(user_id, top_n)
        dept_based_results = department_based_recommendation(user_id, top_n)
        collaborative_dept_results = collaborative_recommendation_with_dept(user_id, top_n)
        
        all_recommendations = set(content_based_results + collaborative_results + dept_based_results + collaborative_dept_results)
        
        # Remove events the user has already participated in
        final_results = [event for event in all_recommendations if event not in user_participations]
        
        return final_results[:top_n]
    except Exception as e:
        print(f"Hybrid recommendation error: {e}")
        return []

# Function to convert event data to Flutter model format
def format_event_for_flutter(event_id):
    event = events[events['Etkinlik_ID'] == event_id].iloc[0]
    
    city = event.get('Sehir', 'Unknown')
    title = event.get('E_Adi', 'Unknown')
    description = event.get('E_Aciklama', 'Unknown')
    date_range = event.get('Tarih', 'Unknown')
    address = event.get('Adres', 'Unknown')
    
    return {
        "city": city,
        "title": title,
        "description": description,
        "dateRange": date_range,
        "address": address
    }

# API endpoint for event recommendations
@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    try:
        user_id = request.args.get('user_id', type=int)
        count = request.args.get('count', default=5, type=int)
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        if user_id not in users['Kullanici_ID'].values:
            return jsonify({"error": "User not found"}), 404
        
        recommended_event_ids = hybrid_recommendation(user_id, count)
        recommended_events = [format_event_for_flutter(event_id) for event_id in recommended_event_ids]
        
        return jsonify({"events": recommended_events})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Run the Flask application
if __name__ == '__main__':
    # Directly initialize models before running the server
    initialize_models()
    app.run(debug=True, host='0.0.0.0', port=5000)
