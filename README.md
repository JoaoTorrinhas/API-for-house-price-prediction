# API-for-house-price-prediction

## About:
This API is designed to predict the price of a house using the **Random Forest Regressor** algorithm. The model is dynamically trained based on data stored in the database, allowing predictions to be adjusted to the specific context of the data provided. After training, it is possible to estimate the price of a new home based on the characteristics provided. An example json was provided with some properties in the Porto district present on the website [Imovirtual](https://www.imovirtual.com/).

### Main features:
- Training the machine learning model with data coming from the database.
- Real estate price prediction based on provided features.
- Support for importing a property database in JSON format.

---

## How to run:

1. Make sure you have **Docker** and **Docker Compose** installed on your machine.

2. Run the docker-compose.yml file:
 ```bash
docker compose up --build