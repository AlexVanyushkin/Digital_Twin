from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from sklearn.preprocessing import PolynomialFeatures
import numpy as np
import joblib



rotation_speed_polinom_degree = 3
current_polinom_degree = 5
# load model
model_file_name = f'model{rotation_speed_polinom_degree}.pkl'
rotation_speed_model = joblib.load(model_file_name)

model_file_name = f'model{current_polinom_degree}.pkl'
current_model = joblib.load(model_file_name)




 
class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        MainWindow.resize(422, 255)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
 
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(160, 130, 93, 28))
 
        # For displaying confirmation message along with user's info.
        self.label = QtWidgets.QLabel(self.centralwidget)   
        self.label.setGeometry(QtCore.QRect(170, 40, 201, 111))
 
        # Keeping the text of label empty initially.      
        self.label.setText("")    
 
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
 
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "Предсказать"))
        self.pushButton.clicked.connect(self.takeinputs)
         
    def takeinputs(self):
        voltage, done1 = QtWidgets.QInputDialog.getText(
             self, 'Input Dialog', 'Введите мощность:')#мощность
 
        current, done2 = QtWidgets.QInputDialog.getText(
           self, 'Input Dialog', 'Введите напряжение:')#напряжение

        poly_rotation_speed = PolynomialFeatures(degree=rotation_speed_polinom_degree)
        X_rotation_speed = poly_rotation_speed.fit_transform([[float(voltage), float(current)]])


        poly_current = PolynomialFeatures(degree=current_polinom_degree)
        X_current = poly_current.fit_transform([[float(voltage), float(current)]])



        out_rotation_speed = rotation_speed_model.predict(X_rotation_speed)[0][0]
        out_current = current_model.predict(X_current)[0][1]

        if done1 and done2:
           
             # Showing confirmation message along
             # with information provided by user.
            self.label.setText(f'Обороты:    {round(out_rotation_speed)} Об/мин \n Ток:            {round(out_current, 2)} А')
            # Hide the pushbutton after inputs provided by the use.
            #self.pushButton.hide()     
            
              
              
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
 
    sys.exit(app.exec_())
