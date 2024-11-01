import requests
import folium
import webbrowser
import os
from geopy.distance import great_circle
from datetime import datetime

# APIキーの取得
API_KEY = 'pk.280f90f3c9ac5340648599e9fa6f6ac8'

# ユーザー入力の取得
def get_location_from_user():
    koyo_location = input("Enter the location or address: ")
    return koyo_location

# 位置情報の取得
def get_lat_lng(koyo_location):
    url = f'https://us1.locationiq.com/v1/search.php?key={API_KEY}&q={koyo_location}&format=json'
    response = requests.get(url)
    data = response.json()
    
    if not data:
        raise ValueError("APIからのデータが空です。指定した場所または住所が見つからない可能性があります。")
    try:
        location_data = data[0]
        koyo_lat = float(location_data.get('lat'))
        koyo_lon = float(location_data.get('lon'))
        return koyo_lat, koyo_lon
    except (IndexError, KeyError, ValueError) as e:
        raise ValueError(f"位置情報データの抽出に失敗しました。エラー内容: {e}")

# 指定避難所のデータを取得
def get_shelter_data(koyo_lat, koyo_lon, radius=10000):
    url = f'https://us1.locationiq.com/v1/nearby.php?key={API_KEY}&lat={koyo_lat}&lon={koyo_lon}&radius={radius}&format=json'
    response = requests.get(url)
    data = response.json()
    
    if not data:
        raise ValueError("APIからの避難所データが空です。指定した位置に避難所が見つからない可能性があります。")

    koyo_shelters = []
    for item in data:
        if 'name' in item and 'lat' in item and 'lon' in item:
            koyo_shelters.append({
                "name": item['name'],
                "lat": float(item['lat']),
                "lon": float(item['lon'])
            })
    return koyo_shelters

# 距離と徒歩での移動時間の計算
def calculate_distance_and_time(koyo_lat, koyo_lon, koyo_shelters):
    average_walking_speed = 5  # km/h
    distances = []
    for shelter in koyo_shelters:
        shelter_lat = shelter['lat']
        shelter_lon = shelter['lon']
        distance = great_circle((koyo_lat, koyo_lon), (shelter_lat, shelter_lon)).kilometers
        time = distance / average_walking_speed  # 時間
        
        # 距離と時間の単位変換
        if distance < 1:
            distance_display = f"{distance * 1000:.0f} m"
        else:
            distance_display = f"{distance:.2f} km"
        
        if time < 1:
            time_display = f"{time * 60:.0f} 分"
        else:
            time_display = f"{time:.2f} 時間"
        
        distances.append({
            "name": shelter['name'],
            "lat": shelter_lat,
            "lon": shelter_lon,
            "distance": distance_display,
            "time": time_display
        })
    return distances

# 地図の生成
def create_map(koyo_lat, koyo_lon, distances):
    zoom_start = 20  
    map_ = folium.Map(location=[koyo_lat, koyo_lon], zoom_start=zoom_start, control_scale=True)
    
    # ユーザー指定位置のマーキング（赤色）
    folium.Marker(
        [koyo_lat, koyo_lon],
        popup='入力した場所',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(map_)
    
    # 避難所のマーキング（青色）
    for item in distances:
        folium.Marker(
            [item['lat'], item['lon']],
            popup=(
                f'<div style="width: 250px; padding: 10px; font-size: 14px;">'
                f'<b>{item["name"]}</b><br>'
                f'<div style="display: flex; justify-content: space-between;">'
                f'<span>距離: {item["distance"]}</span>'
                f'<span>徒歩時間: {item["time"]}</span>'
                f'</div>'
                f'</div>'
            ),
            icon=folium.Icon(color='blue')
        ).add_to(map_)
    return map_

# 地図の保存と表示
def save_and_show_map(map_, filename='map.html'):
    html_content = map_._repr_html_()
    html_content = html_content.replace('<div class="folium-map" id="map_0" ', '<div class="folium-map" id="map_0" style="width: 100vw; height: 100vh;" ')
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print(f"Map saved to {filename}")

    file_path = os.path.abspath(filename)
    webbrowser.open(f'file://{file_path}')

# メイン関数
def main():
    koyo_location = get_location_from_user()
    try:
        koyo_lat, koyo_lon = get_lat_lng(koyo_location)
        koyo_shelters = get_shelter_data(koyo_lat, koyo_lon)
        distances = calculate_distance_and_time(koyo_lat, koyo_lon, koyo_shelters)
        map_ = create_map(koyo_lat, koyo_lon, distances)
        save_and_show_map(map_)
    except ValueError as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
