from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np
import csv
import joblib

# range
data_exclude = 8
data_limit_min = 2
data_limit_max = 10.8
eps = 0.001

# importing data
import_data = []
output_data = []
input_data  = []

data_file_name = 'data.csv'

with open(data_file_name, newline='') as File:  
    import_data = csv.reader(File)
    for column in import_data:
        if (list(map(float, column[0:2]))[1] >= (data_limit_min-eps) ) and (list(map(float, column[0:2]))[1] <= (data_limit_max+eps) ) \
            and ( abs(list(map(float, column[0:2]))[1] - data_exclude) > eps) :
            input_data.append( list(map(float, column[0:2])))
            output_data.append(list(map(float, column[2:4])))
#print(input_data)

polinom_degree = 1

# prepare input data for regression
poly = PolynomialFeatures(degree=polinom_degree)
input_data= poly.fit_transform(input_data)

# regression
model = LinearRegression(fit_intercept=False)
model = model.fit(input_data, output_data)
#print(model.coef_)

# save model parameters
model_file_name = f'model{polinom_degree}.pkl'
joblib.dump(model, model_file_name, compress=9)