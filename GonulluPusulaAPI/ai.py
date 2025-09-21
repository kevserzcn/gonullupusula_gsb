import pandas as pd
import numpy as np
import pyodbc
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# 📌 MSSQL Bağlantı Bilgileri (Windows Authentication ile)
DB_CONFIG = {
    'DRIVER': '{SQL Server}',
    'SERVER': 'KEVSER',  # MSSQL Sunucu Adı
    'DATABASE': 'gonullupusula',
    'Trusted_Connection': 'yes'
}

# 📌 Verileri Çekme Fonksiyonu
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
        print("Bağlantı hatası:", e)
        return None

# 📌 Veriyi Çekme
data = fetch_data()
if data:
    users, events, participation, categories = data.values()
else:
    raise ValueError("Veriler çekilemedi! Bağlantıyı kontrol edin.")

# 📌 Kullanıcı Profilleri Oluşturma (İlgi Alanlarına Göre)
user_profiles = categories.groupby('Kullanici_ID')['Kategori_ID'].apply(list).reset_index()

# 📌 Kullanıcı Katılımlarıyla Profilleri Birleştirme
user_event_matrix = participation.pivot(index='Kullanici_ID', columns='Etkinlik_ID', values='Tarih').fillna(0)
user_event_matrix = user_event_matrix.reindex(users['Kullanici_ID'], fill_value=0)
user_event_matrix = user_event_matrix.map(lambda x: 1 if x != 0 else 0)
user_event_matrix = user_event_matrix.astype(bool).astype(int)


# 📌 İçerik Tabanlı Öneri Sistemi
event_features = events[['Etkinlik_ID', 'E_Aciklama']].fillna("")
event_features['combined'] = event_features['E_Aciklama']

vectorizer = TfidfVectorizer()
event_vectors = vectorizer.fit_transform(event_features['combined'])

def content_based_recommendation(event_id, top_n=5):
    try:
        similarities = cosine_similarity(event_vectors)
        event_idx = events[events['Etkinlik_ID'] == event_id].index[0]
        similar_indices = similarities[event_idx].argsort()[-top_n-1:-1][::-1]
        return events.iloc[similar_indices]['Etkinlik_ID'].tolist()
    except Exception as e:
        print(f"İçerik tabanlı öneri hatası: {e}")
        return []

# 📌 İş Birlikçi Filtreleme (KNN Kullanımı)
knn = NearestNeighbors(metric='cosine', algorithm='brute')
knn.fit(user_event_matrix)

def collaborative_recommendation(user_id, top_n=5):
    try:
        if user_id not in user_event_matrix.index:
            raise ValueError(f"Kullanıcı {user_id} için yeterli veri yok.")
        distances, indices = knn.kneighbors(user_event_matrix.loc[[user_id]], n_neighbors=min(top_n+1, user_event_matrix.shape[0]))
        recommended_events = set()
        for i in range(1, indices.shape[1]):
            similar_user_id = user_event_matrix.index[indices.flatten()[i]]
            similar_user_events = participation.loc[participation['Kullanici_ID'] == similar_user_id, 'Etkinlik_ID'].tolist()
            recommended_events.update(similar_user_events)
        return list(recommended_events)[:top_n]
    except Exception as e:
        print(f"İş birlikçi filtreleme hatası: {e}")
        return []

# 📌 Bölüm Tabanlı Öneri Fonksiyonu
def department_based_recommendation(user_id, top_n=5):
    try:
        user_dept = users.loc[users['Kullanici_ID'] == user_id, 'Bolum'].values[0]
        combined_dept = event_features['combined'] + " " + user_dept
        vectorizer_dept = TfidfVectorizer()
        event_vectors_dept = vectorizer_dept.fit_transform(combined_dept)
        similarities_dept = cosine_similarity(event_vectors_dept)
        avg_similarities = similarities_dept.mean(axis=0)
        recommended_indices = avg_similarities.argsort()[-top_n:][::-1]
        return events.iloc[recommended_indices]['Etkinlik_ID'].tolist()
    except Exception as e:
        print(f"Bölüm tabanlı öneri hatası: {e}")
        return []

# 📌 Güncellenmiş Bölüme Dayalı İş Birlikçi Filtreleme Fonksiyonu
def collaborative_recommendation_with_dept(user_id, top_n=5):
    try:
        # Kullanıcının bölümünü al
        user_dept = users.loc[users['Kullanici_ID'] == user_id, 'Bolum'].values[0]
    except IndexError:
        return []  # Eğer kullanıcı bulunamazsa boş liste döndür

    similar_dept_users = users.loc[users['Bolum'] == user_dept, 'Kullanici_ID'].tolist()
    dept_user_events = participation[participation['Kullanici_ID'].isin(similar_dept_users)]
    
    # Pivot tablosunu oluştur ve vektörleştirilmiş dönüşümü kullan
    user_event_matrix_dept = dept_user_events.pivot(index='Kullanici_ID', columns='Etkinlik_ID', values='Tarih').fillna(0)
    user_event_matrix_dept = (user_event_matrix_dept != 0).astype(int)
    
    # Yeterli veri yoksa hata vermek yerine boş liste döndür
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


# 📌 Hibrit Öneri Sistemi (İçerik + İş Birlikçi + Bölüm Bazlı)
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
        return list(all_recommendations)[:top_n]
    except Exception as e:
        print(f"Hibrit öneri hatası: {e}")
        return []

# 📌 Önerileri Test Etme
for user_id in users['Kullanici_ID']:
    print(f"Kullanıcı {user_id} için önerilen etkinlikler:", hybrid_recommendation(user_id))
