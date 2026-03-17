from sklearn.preprocessing import PolynomialFeatures
import numpy as np
import csv
import matplotlib.pyplot as plt
import joblib

polinom_degree = 7
# load model
model_file_name = f'model{polinom_degree}.pkl'
model = joblib.load(model_file_name)


# import data
import_data = []
output_data = []
input_data  = []

with open('data.csv', newline='') as File:  
    import_data = csv.reader(File)
    for column in import_data:
        input_data.append( list(map(float, column[0:2])))
        output_data.append(list(map(float, column[2:4])))


# prepare input data for regression
poly = PolynomialFeatures(degree=polinom_degree)
X = poly.fit_transform(input_data)

voltage = [8, 9, 10, 11, 12]
eps = 0.001
# inputs
x1_0 = []
x1_1 = []
x1_2 = []
x1_3 = []
x1_4 = []

# outputs
y1_0 = []
y1_1 = []
y1_2 = []
y1_3 = []
y1_4 = []

y2_0 = []
y2_1 = []
y2_2 = []
y2_3 = []
y2_4 = []

# predictions
z1_0 = []
z1_1 = []
z1_2 = []
z1_3 = []
z1_4 = []

z2_0 = []
z2_1 = []
z2_2 = []
z2_3 = []
z2_4 = []

for i in range(len(output_data)):
    if abs(input_data[i][1] - voltage[0]) < eps:
        x1_0.append([input_data[i][0]])
        y1_0.append([output_data[i][0]])
        z1_0.append([model.predict([X[i]])[0][0]])
        
        y2_0.append([output_data[i][1]])
        z2_0.append([model.predict([X[i]])[0][1]])
    if abs(input_data[i][1] - voltage[1]) < eps:
        x1_1.append([input_data[i][0]])
        y1_1.append([output_data[i][0]])
        z1_1.append([model.predict([X[i]])[0][0]])
        
        y2_1.append([output_data[i][1]])
        z2_1.append([model.predict([X[i]])[0][1]])
    if abs(input_data[i][1] - voltage[2]) < eps:
        x1_2.append([input_data[i][0]])
        y1_2.append([output_data[i][0]])
        z1_2.append([model.predict([X[i]])[0][0]])
        
        y2_2.append([output_data[i][1]])
        z2_2.append([model.predict([X[i]])[0][1]])
    if abs(input_data[i][1] - voltage[3]) < eps:
        x1_3.append([input_data[i][0]])
        y1_3.append([output_data[i][0]])
        z1_3.append([model.predict([X[i]])[0][0]])
        
        y2_3.append([output_data[i][1]])
        z2_3.append([model.predict([X[i]])[0][1]])
        
    if abs(input_data[i][1] - voltage[4]) < eps:
        x1_4.append([input_data[i][0]])
        y1_4.append([output_data[i][0]])
        z1_4.append([model.predict([X[i]])[0][0]])
        
        y2_4.append([output_data[i][1]])
        z2_4.append([model.predict([X[i]])[0][1]])

plt.rcParams.update({'font.size': 9})

plt.figure(figsize=(4.25, 4.25*0.7), dpi=1920)

plt.plot(x1_0, y1_0, color='black', label='Эталонные данные')
plt.plot(x1_1, y1_1, x1_2, y1_2, x1_3, y1_3, color='black')
plt.plot(x1_0, z1_0, color='red', linestyle='dashed', label='Прогноз')
plt.plot(x1_1, z1_1, x1_2, z1_2, x1_3, z1_3, color='red', linestyle='dashed')

plt.minorticks_on()

plt.xlabel("Мощность (P), Вт")
plt.ylabel("Скорость (n), об/мин")
plt.legend(loc=4)
plt.grid(which='major', color='0.8', linestyle=':')
plt.grid(which='minor', color='0.8', linestyle=':')

plt.savefig(f'd:\Documents\Stage_2_Rush\Projects\НОЦ\ВНГ\Ванюшкин\НТИ-2022\speed{polinom_degree}.pdf', format='pdf')
plt.show()


plt.figure(figsize=(4.25, 4.25*0.7), dpi=1920)

plt.plot(x1_0, y2_0, color='black', label='Эталонные данные')
plt.plot(x1_1, y2_1, x1_2, y2_2, x1_3, y2_3, color='black')
plt.plot(x1_0, z2_0, color='red', linestyle='dashed', label='Прогноз')
plt.plot(x1_1, z2_1, x1_2, z2_2, x1_3, z2_3, color='red', linestyle='dashed')

plt.minorticks_on()

plt.xlabel("Мощность (P), Вт")
plt.ylabel("Сила тока (I), А")
plt.legend(loc=4)
plt.grid(which='major', color='0.8', linestyle=':')
plt.grid(which='minor', color='0.8', linestyle=':')

plt.savefig(f'd:\Documents\Stage_2_Rush\Projects\НОЦ\ВНГ\Ванюшкин\НТИ-2022\current{polinom_degree}.pdf', format='pdf')
plt.show()

summ = 0
N = len(y1_0)
for i in range(N):
    summ += ((y1_0[i][0] - z1_0[i][0]) / y1_0[i][0])**2
err1_0 = np.sqrt(summ / N) * 100

summ = 0
N = len(y1_1)
for i in range(N):
    summ += ((y1_1[i][0] - z1_1[i][0]) / y1_1[i][0])**2
err1_1 = np.sqrt(summ / N) * 100

summ = 0
N = len(y1_2)
for i in range(N):
    summ += ((y1_2[i][0] - z1_2[i][0]) / y1_2[i][0])**2
err1_2 = np.sqrt(summ / N) * 100

summ = 0
N = len(y1_3)
for i in range(N):
    summ += ((y1_3[i][0] - z1_3[i][0]) / y1_3[i][0])**2
err1_3 = np.sqrt(summ / N) * 100

summ = 0
N = len(y1_4)
for i in range(N):
    summ += ((y1_4[i][0] - z1_4[i][0]) / y1_4[i][0])**2
err1_4 = np.sqrt(summ / N) * 100




summ = 0
N = len(y2_0)
for i in range(N):
    summ += ((y2_0[i][0] - z2_0[i][0]) / y2_0[i][0])**2
err2_0 = np.sqrt(summ / N) * 100

summ = 0
N = len(y2_1)
for i in range(N):
    summ += ((y2_1[i][0] - z2_1[i][0]) / y2_1[i][0])**2
err2_1 = np.sqrt(summ / N) * 100

summ = 0
N = len(y2_2)
for i in range(N):
    summ += ((y2_2[i][0] - z2_2[i][0]) / y2_2[i][0])**2
err2_2 = np.sqrt(summ / N) * 100

summ = 0
N = len(y2_3)
for i in range(N):
    summ += ((y2_3[i][0] - z2_3[i][0]) / y2_3[i][0])**2
err2_3 = np.sqrt(summ / N) * 100

summ = 0
N = len(y2_4)
for i in range(N):
    summ += ((y2_4[i][0] - z2_4[i][0]) / y2_4[i][0])**2
err2_4 = np.sqrt(summ / N) * 100

print('SPEED error:')
print(f'{voltage[0]} V')
print(format(err1_0, '.2f'))
print(f'{voltage[1]} V')
print(format(err1_1, '.2f'))
print(f'{voltage[2]} V')
print(format(err1_2, '.2f'))
print(f'{voltage[3]} V')
print(format(err1_3, '.2f'))
print(f'{voltage[4]} V')
print(format(err1_4, '.2f'))

print('==========================================')

print('CURRENT error:')
print(f'{voltage[0]} V')
print(format(err2_0, '.2f'))
print(f'{voltage[1]} V')
print(format(err2_1, '.2f'))
print(f'{voltage[2]} V')
print(format(err2_2, '.2f'))
print(f'{voltage[3]} V')
print(format(err2_3, '.2f'))
print(f'{voltage[4]} V')
print(format(err2_4, '.2f'))
