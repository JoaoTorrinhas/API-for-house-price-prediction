import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import psycopg2
import numpy as np
from fastapi import HTTPException

def price_predict(city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, connection):
    try:
        query = "SELECT city, address, age, num_bedrooms, num_bathrooms, area, is_apartment, has_pool, garage, price FROM houses"
        df = pd.read_sql(query, connection)

        df = pd.get_dummies(df, columns=['city', 'address'], drop_first=True)
        
        X = df.drop('price', axis=1)
        y = df['price']

        # Trainning the model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Create input data frame
        house_data = {
            'city': city,
            'address': address,
            'age': age,
            'num_bedrooms': num_bedrooms,
            'num_bathrooms': num_bathrooms,
            'area': area,
            'is_apartment': is_apartment,
            'has_pool': has_pool,
            'garage': garage
        }

        city_dummies = pd.get_dummies(pd.Series([city]), prefix='city')
        address_dummies = pd.get_dummies(pd.Series([address]), prefix='address')

        house_data.update(city_dummies.to_dict(orient='list'))
        house_data.update(address_dummies.to_dict(orient='list'))

        house_df = pd.DataFrame(house_data)

        house_df = house_df.reindex(columns=X.columns, fill_value=0)

        price_prediction = model.predict(house_df)
        return price_prediction[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while training and predicting: {e}")