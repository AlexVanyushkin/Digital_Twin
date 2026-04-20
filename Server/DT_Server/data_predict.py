from sklearn.preprocessing import PolynomialFeatures
import numpy as np
import joblib
import json
import sys


rotation_speed_polinom_degree = 3
current_polinom_degree = 5

# load model
model_file_name = f'model{rotation_speed_polinom_degree}.pkl'
rotation_speed_model = joblib.load(model_file_name)

model_file_name = f'model{current_polinom_degree}.pkl'
current_model = joblib.load(model_file_name)


#input
#input_data = [[float(input('Введите потребляемую мощность:')), float(input('Введите напряжение:'))]]
input_data = [[float(sys.argv[1]), float(sys.argv[2])]]

# prepare input data for regression
poly_rotation_speed = PolynomialFeatures(degree=rotation_speed_polinom_degree)
X_rotation_speed = poly_rotation_speed.fit_transform(input_data)

poly_current = PolynomialFeatures(degree=current_polinom_degree)
X_current = poly_current.fit_transform(input_data)

out_rotation_speed = rotation_speed_model.predict(X_rotation_speed)[0][0]
out_current = current_model.predict(X_current)[0][1]
#print('.')
#print('.')
#print('.')
#print(f'Предсказанное количество оборотов двигателя: {round(out_rotation_speed)} об./мин')
#print(f'Предсказанный электрический ток: {round(out_current, 2)} А')
data = {
    "rotation_speed": round(out_rotation_speed),
    "current": round(out_current, 2)
}
with open("data_buffer.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
#print(round(out_rotation_speed), round(out_current, 2))
