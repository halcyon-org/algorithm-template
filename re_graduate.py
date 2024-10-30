import math
import requests
import json

def get_altitude(appid, latitude, longitude):
    url = "https://map.yahooapis.jp/alt/V1/getAltitude"
    coordinates = f"{longitude},{latitude}"
    params = {
        'appid': appid,
        'coordinates': coordinates,
        'output': 'json'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if "Feature" in data and len(data["Feature"]) > 0:
            altitude = data["Feature"][0]["Property"]["Altitude"]
            return altitude
        else:
            raise ValueError("標高データが見つかりませんでした。")
    elif response.status_code == 403:
        raise ValueError("APIキーが無効です。正しいAPIキーを使用してください。")
    else:
        raise ValueError(f"エラーが発生しました。ステータスコード: {response.status_code}")

def generate_points(appid, latitude, longitude, precision, radius):
    if precision not in [4, 8, 16, 32, 64, 128]:
        raise ValueError("Precision must be one of: 4, 8, 16, 32, 64, 128")
    if latitude > 90 or latitude <= -90:
        raise ValueError("Latitude must be (-90, 90]")
    if longitude > 180 or longitude <= -180:
        raise ValueError("Longitude must be (-180, 180)")
    if radius <= 0 or radius > 1000:
        raise ValueError("Radius must be a positive value less than or equal to 1000")

    # Get altitude of the input coordinates
    input_altitude = get_altitude(appid, latitude, longitude)

    # Convert latitude and longitude to radians
    lat_radians = math.radians(latitude)
    lon_radians = math.radians(longitude)

    # Calculate angular distance for each point
    num_points = precision
    delta_angle = 2 * math.pi / num_points

    points = []
    slope_vectors = []

    for i in range(num_points):
        # Calculate the angle for this point relative to north (0 degrees)
        angle = delta_angle * i  # Angle in radians

        # Calculate coordinates for the point on the circle
        point_lat_radians = math.asin(math.sin(lat_radians) * math.cos(radius / 6371000) +
                                      math.cos(lat_radians) * math.sin(radius / 6371000) * math.cos(angle))
        point_lon_radians = lon_radians + math.atan2(math.sin(angle) * math.sin(radius / 6371000) * math.cos(lat_radians),
                                                     math.cos(radius / 6371000) - math.sin(lat_radians) * math.sin(point_lat_radians))

        point_lat = math.degrees(point_lat_radians)
        point_lon = math.degrees(point_lon_radians)

        # Generate elevation using the API
        try:
            point_altitude = get_altitude(appid, point_lat, point_lon)
        except ValueError as ve:
            print(f"Error fetching altitude for point ({point_lat}, {point_lon}): {ve}")
            point_altitude = None

        # Calculate slope vector
        if point_altitude is not None:
            absolute_value = (point_altitude - input_altitude) / radius
        else:
            absolute_value = 0.0
        slope_angle = math.degrees(angle)

        # Normalize slope angle to be within [0, 360) degrees
        if slope_angle < 0:
            slope_angle += 360

        slope_vectors.append((absolute_value, slope_angle))

        # Append the point details to the list
        points.append((i + 1, point_lat, point_lon, point_altitude, absolute_value, slope_angle))

    # Calculate average slope vector using complex numbers
    sum_complex = sum(absolute_value * complex(math.cos(math.radians(slope_angle)), math.sin(math.radians(slope_angle)))
                      for absolute_value, slope_angle in slope_vectors)

    avg_absolute_value = abs(sum_complex) / precision
    avg_slope_angle = math.degrees(math.atan2(sum_complex.imag, sum_complex.real))

    # Normalize average slope angle to be within [0, 360) degrees
    if avg_slope_angle < 0:
        avg_slope_angle += 360

    average_slope_vector = (avg_absolute_value, avg_slope_angle)

    return points, average_slope_vector


def makejson(lat, lon):
    # コンテンツの生成
    content = []
    for la in [lat - 200 / 6371000, lat - 100 / 6371000, lat, lat + 100 / 6371000, lat + 200 / 6371000]:
        for lo in [lon - 200 / 6371000, lon - 100 / 6371000, lon, lon + 100 / 6371000, lon + 200 / 6371000]:
            # generate_pointsの結果を単一の数値にする
            value = generate_points("dj00aiZpPTV4SFRid0RpVzNVdiZzPWNvbnN1bWVyc2VjcmV0Jng9YmI-", la, lo, 4, 50)
            
            polygon = {
                "type": "Polygon",
                "coordinates": [
                    [la - 50 / 6371000, lo - 50 / 6371000],
                    [la + 50 / 6371000, lo - 50 / 6371000],
                    [la - 50 / 6371000, lo + 50 / 6371000],
                    [la + 50 / 6371000, lo + 50 / 6371000]
                ],
                "value": value[1]  # 単一の値のみを設定
            }
            content.append(polygon)

    # JSONデータの構造
    json_data = {
        "koyo_data_id": "",
        "koyo_id": "",
        "koyo_scale": "1.0",
        "koyo_data_params": [
            {"key": "緯度", "value": lat},
            {"key": "経度", "value": lon}
        ],
        "content": content,
        "entry_at": "",
        "target_at": "",
        "koyo_name": "傾斜計算アルゴリズム",
        "koyo_description": "ある地点の周囲の平均傾斜を出力します。",
        "need_external": "",
        "koyo_params": [
            {"key": "緯度", "value": "34.8503617"},
            {"key": "経度", "value": "136.582085"}
        ],
        "koyo_scales": "0.1",
        "koyo_data_ids": "",
        "version": "0.0.1",
        "license": "public domain",
        "ext_licenses": "Web Services by Yahoo! JAPAN （https://developer.yahoo.co.jp/sitemap/）",
        "data_type": "0",
        "api_key": "graduate_api",
        "first_entry_at": "",
        "last_entry_at": "",
        "last_updated_at": ""
    }

    # JSON文字列として出力
    return json.dumps(json_data, ensure_ascii=False, indent=4)


def main():
    appid = "dj00aiZpPTV4SFRid0RpVzNVdiZzPWNvbnN1bWVyc2VjcmV0Jng9YmI-"  # ここにあなたのアプリケーションIDを入力してください

    try:
        # Input values
        input_values = input("Enter latitude, longitude, precision, radius (space separated): ")
        lat, lon, prec, rad = map(float, input_values.split())

        # Generate points and average slope vector
        points, avg_slope_vector = generate_points(appid, lat, lon, int(prec), rad)

        # Output points
        for point in points:
            print(f"{point[0]}, {point[1]:.6f}, {point[2]:.6f}, {point[3]}, {point[4]:.6f}, {point[5]:.6f}")

        # Output average slope vector
        print(f"Average Slope Vector: {avg_slope_vector[0]:.6f}, {avg_slope_vector[1]:.6f}")

        print("以下、JSONコード")
        print(makejson(lat, lon))

    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()