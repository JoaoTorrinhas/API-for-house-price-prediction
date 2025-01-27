from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Query 
from fastapi.middleware.cors import CORSMiddleware
from training_model import *
import psycopg2, logging
import json

app = FastAPI()

DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "db"
DB_PORT = "5432"
DB_DATABASE = "houses"

# TODO: Ver como criar um script para retirar info das casas em um site (scrapping) e adicionar a um json para importar.
# TODO: Ver variaveis de ambiente.
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    while not connect_db():
        continue

# Database Connection
def connect_db():
    global connection, cursor
    try:
        connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_DATABASE)

        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            
        logger.info(f"Connected to {db_version[0]}")
        create_tables()
        return True
    
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while connecting to PostgreSQL: {error}")
        return False
    
def create_tables():
    try:
        global connection, cursor

        with connection.cursor() as cursor:
            # Create the 'users' table
            create_users_table = """
                CREATE TABLE IF NOT EXISTS houses (
                    house_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    city VARCHAR NOT NULL,
                    address VARCHAR NOT NULL,
                    age INT,
                    num_bedrooms INT,
                    num_bathrooms INT,
                    area INT,
                    is_apartment BOOLEAN,
                    has_pool BOOLEAN,
                    garage BOOLEAN,
                    price INT
                );
            """
            cursor.execute(create_users_table)
            connection.commit()
            logger.info("Table houses created successfully in PostgreSQL database")

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error creating table: {error}")


@app.get("/house/predict/")
async def predict_house_price(
    city: str = Form(None),
    address: str = Form(None),
    age: int = Form(None),
    num_bedrooms: int = Form(None),
    num_bathrooms: int = Form(None),
    area: int = Form(None),
    is_apartment: bool = Form(None),
    has_pool: bool = Form(None),
    garage: bool = Form(None)
):
    global connection 
    
    if city is None or address is None or age is None or num_bedrooms is None or num_bathrooms is None or area is None or is_apartment is None or has_pool is None or garage is None:
        raise HTTPException(status_code=400, detail="All fields must be filled")
    
    # Train the model to get the price
    house_price = price_predict(city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, connection)
    if house_price:
        return {'price': house_price}
    
    raise HTTPException(status_code=500, detail="Could not estimate the house price")


# Add a House (Adicionar informações de casas reais a uma base de dados para treinar o modelo)
@app.post("/house/")
async def add_house(
    city: str = Form(None),
    address: str = Form(None),
    age: int = Form(None),
    num_bedrooms: int = Form(None),
    num_bathrooms: int = Form(None),
    area: int = Form(None),
    is_apartment: bool = Form(None),
    has_pool: bool = Form(None),
    garage: bool = Form(None),
    price: int = Form(None)
):
    if city is None or address is None or age is None or num_bedrooms is None or num_bathrooms is None or area is None or is_apartment is None or has_pool is None or garage is None or price is None:
        raise HTTPException(status_code=400, detail="All fields must be filled")
    
    # Add the house to the database
    global connection
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO houses (city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price)
            )
            connection.commit()
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error adding house to the database: {error}")
        raise HTTPException(status_code=500, detail="Could not add the house to the database")
    
    return {"message": "House added successfully."}

# Add houses inside of a json file to the database
@app.post("/houses/import/")
async def import_houses(file_import: UploadFile = File(...)):
    global connection
    
    if file_import.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    try:
        # Carregar e processar o arquivo JSON
        content = await file_import.read()
        list_houses_import = json.loads(content)  # Parse do JSON para um dicionário/lista
        
        # Validar e adicionar casas à base de dados
        with connection.cursor() as cursor:
            for house in list_houses_import:
                # Validar os campos necessários
                required_fields = ["city", "address", "age", "num_bedrooms", "num_bathrooms", "area", "is_apartment", "has_pool", "garage", "price"]
                if not all(field in house for field in required_fields):
                    raise HTTPException(status_code=400, detail=f"Missing fields in house data: {house}")
                
                # Adicionar casa ao banco de dados
                cursor.execute(
                    """
                    INSERT INTO houses (city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        house["city"], house["address"], house["age"], house["num_bedrooms"],
                        house["num_bathrooms"], house["area"], house["is_apartment"],
                        house["has_pool"], house["garage"], house["price"]
                    )
                )
            connection.commit()
        
        return {"message": "Houses imported successfully."}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error importing houses: {error}")
        raise HTTPException(status_code=500, detail="Could not import houses into the database")
    
@app.delete("/houses/remove/")
async def remove_houses():
    global connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM houses")
            connection.commit()
        return {"message": "All houses removed successfully."}
    
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error removing houses: {error}")
        raise HTTPException(status_code=500, detail="Could not remove the houses from the database")

# Delete a House
# @app.delete("/house/{email}")
# def delete_house(
#     email: str = Form(None),
#     city: str = Form(None),
#     age: int = Form(None),
#     num_bedrooms: int = Form(None),
#     num_bathrooms: int = Form(None),
#     area: int = Form(None),
#     is_apartment: bool = Form(None),
#     has_pool: bool = Form(None),
#     price: int = Form(None)
# ):
    
#     return {"message": "House deleted successfully."}

# Get all Houses (Auxiliary function)
@app.get("/houses/")
def get_houses():
    try:
        global connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM houses")
            houses = cursor.fetchall()
            return houses
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error getting houses from the database: {error}")
        raise HTTPException(status_code=500, detail="Could not get the houses from the database")






