import pytest
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, connect_db


@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_db_connection():
    with patch('main.psycopg2.connect') as mock_connect:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        yield mock_connection, mock_cursor
        
        
@pytest.fixture(autouse=True)
def reset_mocks(mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_connection.reset_mock()
    
    # Reset the mock_cursor as well
    mock_cursor.reset_mock()
    yield
        
def test_connect_db_success(mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_connection.cursor.return_value = mock_cursor

    result = connect_db()

    assert result is True
    
    
@pytest.mark.parametrize("city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, expected_status", [
    ("Porto", 41.15706, -8.57466, 0, 3, 3, 100, True, False, False, 200),
    ("Porto", 41.23706, -8.37652, 0, 2, 3, 100, True, False, False, 200),
    ("Porto", 41.23706, -8.37652, 0, 2, 2, 100, False, True, True, 200),
])
def test_predict_house_price_success(test_client, city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, expected_status, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_connection.cursor.return_value = mock_cursor
    
    # Simulation of the behavior of the predict_house_price function
    with patch('main.price_predict') as mock_predict_price:
        mock_predict_price.return_value = 300000  # Simulated price
        
        form_data = {
            'city': city,
            'latitude': latitude,
            'longitude': longitude,
            'age': age,
            'num_bedrooms': num_bedrooms,
            'num_bathrooms': num_bathrooms,
            'area': area,
            'is_apartment': is_apartment,
            'has_pool': has_pool,
            'garage': garage
        }
        
        with patch('main.connection', mock_connection):
            response = test_client.post("/house/predict/", data=form_data)

    assert response.status_code == expected_status
    
    if response.status_code == 200:
        assert "price" in response.json()
        assert response.json()["price"] == 300000
        
        
@pytest.mark.parametrize("city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, expected_status, expected_message", [
    (None, 41.23706, -8.37652, 0, 2, 2, 100, False, True, True, 400, "All fields must be filled"),
    ("Porto", None, -8.57466, 0, 3, 3, 100, True, False, False, 400, "All fields must be filled"),
    ("Porto", 41.23706, None, 0, 2, 3, 100, False, False, False, 400, "All fields must be filled"),
    ("Porto", 41.23706, -8.37652, None, 2, 2, 100, False, True, True, 400, "All fields must be filled"),
    ("Porto", 41.23706, -8.37652, 0, None, 2, 100, False, True, True, 400, "All fields must be filled"),
    ("Porto", 41.23706, -8.37652, 0, None, None, 100, False, True, True, 400, "All fields must be filled"),
    ("Porto", 41.23706, None, 0, None, None, 100, False, True, True, 400, "All fields must be filled"),
])
def test_predict_house_price_bad_request(test_client, city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, expected_status, expected_message, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_connection.cursor.return_value = mock_cursor
    
    form_data = {}
    if city is not None:
        form_data['city'] = city
    if latitude is not None:
        form_data['latitude'] = latitude
    if longitude is not None:
        form_data['longitude'] = longitude
    if age is not None:
        form_data['age'] = age
    if num_bedrooms is not None:
        form_data['num_bedrooms'] = num_bedrooms
    if num_bathrooms is not None:
        form_data['num_bathrooms'] = num_bathrooms
    if area is not None:
        form_data['area'] = area
    if is_apartment is not None:
        form_data['is_apartment'] = is_apartment
    if has_pool is not None:
        form_data['has_pool'] = has_pool 
    if garage is not None:
        form_data['garage'] = garage 
    
    with patch('main.connection', mock_connection):
        response = test_client.post("/house/predict/", data=form_data)
    
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message
    

@pytest.mark.parametrize("city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status", [
    ("Porto", 41.15706, -8.57466, 0, 3, 3, 100, True, False, False, 300000, 200),
    ("Porto", 41.23706, -8.37652, 0, 2, 3, 100, False, False, False, 250000, 200),
    ("Porto", 41.23706, -8.37652, 0, 2, 2, 100, False, True, True, 220000, 200),
])
def test_add_house_success(test_client, city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    
    form_data = {
        'city': city,
        'latitude': latitude,
        'longitude': longitude,
        'age': age,
        'num_bedrooms': num_bedrooms,
        'num_bathrooms': num_bathrooms,
        'area': area,
        'is_apartment': is_apartment,
        'has_pool': has_pool,
        'garage': garage,
        'price': price
    }
    
    mock_cursor.fetchone.return_value = None  # No house with the same parameters
    mock_connection.cursor.return_value = mock_cursor
    
    with patch('main.connection', mock_connection):
        response = test_client.post("/house/", data=form_data)
    
    assert response.status_code == expected_status
    if response.status_code == 200:
        assert response.json()["message"] == "House added successfully."
 
       
       
@pytest.mark.parametrize("city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status, expected_message", [
    # All it takes is for at least one parameter to be None to return an error.
    (None, 41.15706, -8.57466, 0, 3, 3, 100, True, False, False, 300000, 400, "All fields must be filled"),
    ("Porto", None, None, 0, 2, 3, 100, False, False, False, 250000, 400, "All fields must be filled"),
    ("Porto", 41.23706, -8.37652, None, 2, 2, 100, False, True, True, 220000, 400, "All fields must be filled"),
]) 
def test_add_house_bad_request(test_client, city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status, expected_message, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    
    form_data = {}
    if city is not None:
        form_data['city'] = city
    if latitude is not None:
        form_data['latitude'] = latitude
    if longitude is not None:
        form_data['longitude'] = longitude
    if age is not None:
        form_data['age'] = age
    if num_bedrooms is not None:
        form_data['num_bedrooms'] = num_bedrooms
    if num_bathrooms is not None:
        form_data['num_bathrooms'] = num_bathrooms
    if area is not None:
        form_data['area'] = area
    if is_apartment is not None:
        form_data['is_apartment'] = is_apartment 
    if has_pool is not None:
        form_data['has_pool'] = has_pool 
    if garage is not None:
        form_data['garage'] = garage 
    if price is not None:
        form_data['price'] = price
    
    mock_connection.cursor.return_value = mock_cursor
    
    with patch('main.connection', mock_connection):
        response = test_client.post("/house/", data=form_data)
    
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message

    
    
@pytest.mark.parametrize("city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status", [
    ("Porto", 41.15706, -8.57466, 0, 3, 3, 100, True, False, False, 300000, 409)
])
def test_add_house_already_exist(test_client, city, latitude, longitude, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price, expected_status, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    
    form_data = {
        'city': city,
        'latitude': latitude,
        'longitude': longitude,
        'age': age,
        'num_bedrooms': num_bedrooms,
        'num_bathrooms': num_bathrooms,
        'area': area,
        'is_apartment': is_apartment,
        'has_pool': has_pool,
        'garage': garage,
        'price': price
    }
    
    mock_connection.cursor.return_value = mock_cursor
    
    with patch('main.connection', mock_connection):
        response = test_client.post("/house/", data=form_data)
    
    assert response.status_code == expected_status
    assert response.json()["detail"] == "House already exists in the database."
    
    
def test_import_houses_json_success(test_client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    
    json_data = [
        {
            "city": "Porto",
            "latitude": 41.15706,
            "longitude": -8.57466,
            "age": 0,
            "num_bedrooms": 3,
            "num_bathrooms": 3,
            "area": 100,
            "is_apartment": True,
            "has_pool": False,
            "garage": False,
            "price": 250000
        },
        {
            "city": "Porto",
            "latitude": 41.23706,
            "longitude": -8.37652,
            "age": 0,
            "num_bedrooms": 2,
            "num_bathrooms": 3,
            "area": 120,
            "is_apartment": False,
            "has_pool": True,
            "garage": True,
            "price": 280000
        }
    ]
  
    mock_cursor.execute.return_value = None

    with patch('main.connection', mock_connection), patch('main.UploadFile.read', return_value=json.dumps(json_data).encode('utf-8')):
        response = test_client.post("/houses/import/", files={'file_import': ('houses.json', json.dumps(json_data), 'application/json')})

    assert response.status_code == 200
    assert response.json()["message"] == "Houses imported successfully."
    

def import_houses_json_bad_request(test_client, mock_db_connection):
    invalid_file_content = "This is not a JSON file"
    
    response = test_client.post("/houses/import/", files={'file_import': ('invalid.txt', invalid_file_content, 'text/plain')})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Only JSON files are allowed"
    
    
def test_remove_houses_success(test_client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    
    with patch('main.connection', mock_connection):
        response = test_client.delete("/houses/")
    
    assert response.status_code == 200
    assert response.json()["message"] == "All houses removed successfully."
    

    
