import joblib
import pandas as pd

model = joblib.load("model/cancellation_model.pkl")
feature_cols = joblib.load("model/feature_cols.pkl")

def predict(order_value, order_hour, delivery_minutes, restaurant_rating, cuisine, device):
    row = pd.DataFrame([{
        "order_value": order_value,
        "order_hour": order_hour,
        "delivery_minutes": delivery_minutes,
        "restaurant_rating": restaurant_rating,
        "cuisine": cuisine,
        "device": device,
    }])
    row_encoded = pd.get_dummies(row, columns=["cuisine", "device"])
    for col in feature_cols:
        if col not in row_encoded.columns:
            row_encoded[col] = 0
    row_encoded = row_encoded[feature_cols]

    prediction = model.predict(row_encoded)[0]
    probability = model.predict_proba(row_encoded)[0][1]
    return bool(prediction), round(probability, 3)


if __name__ == "__main__":
    result = predict(1200, 22, 55, 3.2, "Biryani", "android")
    print(f"Will cancel: {result[0]}, probability: {result[1]}")