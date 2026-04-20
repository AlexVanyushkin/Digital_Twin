from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit
import sys
import requests
import json

class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        MainWindow.resize(500, 450)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        
        # Поле для ввода адреса сервера
        self.serverLabel = QtWidgets.QLabel(self.centralwidget)
        self.serverLabel.setGeometry(QtCore.QRect(50, 10, 100, 28))
        self.serverLabel.setText("Адрес сервера:")
        
        self.serverInput = QtWidgets.QLineEdit(self.centralwidget)
        self.serverInput.setGeometry(QtCore.QRect(150, 10, 200, 28))
        self.serverInput.setText("http://127.0.0.1:3000")
        self.serverInput.textChanged.connect(self.update_server_url)
        
        # Статус авторизации
        self.authStatusLabel = QtWidgets.QLabel(self.centralwidget)
        self.authStatusLabel.setGeometry(QtCore.QRect(50, 50, 280, 28))
        self.authStatusLabel.setText("Не авторизован")
        self.authStatusLabel.setStyleSheet("color: red")
        
        # Кнопка выхода
        self.logoutButton = QtWidgets.QPushButton(self.centralwidget)
        self.logoutButton.setGeometry(QtCore.QRect(350, 50, 120, 28))
        self.logoutButton.setText("Выход")
        self.logoutButton.setEnabled(False)
        self.logoutButton.clicked.connect(self.logout)
        
        # Кнопка предсказания
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(50, 90, 120, 28))
        self.pushButton.setText("Предсказать")
        self.pushButton.clicked.connect(self.takeinputs)
        
        # Кнопка переобучения
        self.retrainButton = QtWidgets.QPushButton(self.centralwidget)
        self.retrainButton.setGeometry(QtCore.QRect(200, 90, 150, 28))
        self.retrainButton.setText("Переобучить модель")
        self.retrainButton.clicked.connect(self.handle_retrain)
        
        # Кнопка получения PDF с графиком тока
        self.currentPdfButton = QtWidgets.QPushButton(self.centralwidget)
        self.currentPdfButton.setGeometry(QtCore.QRect(50, 140, 120, 28))
        self.currentPdfButton.setText("PDF график тока")
        self.currentPdfButton.clicked.connect(lambda: self.get_pdf("get_graph_current_pdf"))
        
        # Кнопка получения PDF с графиком оборотов
        self.speedPdfButton = QtWidgets.QPushButton(self.centralwidget)
        self.speedPdfButton.setGeometry(QtCore.QRect(200, 140, 150, 28))
        self.speedPdfButton.setText("PDF график оборотов")
        self.speedPdfButton.clicked.connect(lambda: self.get_pdf("get_graph_speed_pdf"))
        
        # Группа для отображения результатов
        self.resultsGroup = QtWidgets.QGroupBox(self.centralwidget)
        self.resultsGroup.setGeometry(QtCore.QRect(50, 190, 400, 200))
        self.resultsGroup.setTitle("Результаты расчета")
        
        # Поле для отображения оборотов
        self.speedLabel = QtWidgets.QLabel(self.resultsGroup)
        self.speedLabel.setGeometry(QtCore.QRect(20, 30, 100, 30))
        self.speedLabel.setText("Обороты:")
        self.speedLabel.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.speedValue = QtWidgets.QLabel(self.resultsGroup)
        self.speedValue.setGeometry(QtCore.QRect(130, 30, 250, 30))
        self.speedValue.setText("—")
        self.speedValue.setStyleSheet("font-size: 12px;")
        
        # Разделительная линия
        self.line = QtWidgets.QFrame(self.resultsGroup)
        self.line.setGeometry(QtCore.QRect(20, 70, 360, 3))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        # Поле для отображения тока
        self.currentLabel = QtWidgets.QLabel(self.resultsGroup)
        self.currentLabel.setGeometry(QtCore.QRect(20, 90, 100, 30))
        self.currentLabel.setText("Ток:")
        self.currentLabel.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.currentValue = QtWidgets.QLabel(self.resultsGroup)
        self.currentValue.setGeometry(QtCore.QRect(130, 90, 250, 30))
        self.currentValue.setText("—")
        self.currentValue.setStyleSheet("font-size: 12px;")
        
        # Информационная метка
        self.infoLabel = QtWidgets.QLabel(self.resultsGroup)
        self.infoLabel.setGeometry(QtCore.QRect(20, 150, 360, 30))
        self.infoLabel.setText("Введите данные и нажмите 'Предсказать'")
        self.infoLabel.setStyleSheet("color: gray; font-style: italic;")
        self.infoLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        # Переменные для хранения данных авторизации
        self.login = ""
        self.jwt_token = ""
        self.is_authenticated = False
        self.server_url = "http://127.0.0.1:3000"
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Управление двигателем"))
    
    def update_server_url(self):
        """Обновление URL сервера при изменении текста"""
        self.server_url = self.serverInput.text().strip()
        if not self.server_url.startswith('http'):
            self.server_url = 'http://' + self.server_url
    
    def authenticate(self):
        """Авторизация пользователя"""
        login, ok1 = QInputDialog.getText(self, 'Авторизация', 'Введите логин:')
        if not ok1 or not login:
            return False
            
        password, ok2 = QInputDialog.getText(self, 'Авторизация', 'Введите пароль:', QLineEdit.Password)
        if not ok2 or not password:
            return False
        
        # Отправляем запрос на авторизацию
        auth_data = {
            "request_type": "auth",
            "login": login,
            "password": password
        }
        
        try:
            print(f"Отправка запроса авторизации на {self.server_url}")
            response = requests.post(self.server_url, json=auth_data, timeout=10)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    if response_data.get('type') == 'success' and 'token' in response_data:
                        self.jwt_token = response_data['token']
                        self.login = login
                        self.is_authenticated = True
                        
                        # Обновляем UI
                        self.logoutButton.setEnabled(True)
                        
                        # Обновляем статус
                        self.authStatusLabel.setText(f"Авторизован как: {login}")
                        self.authStatusLabel.setStyleSheet("color: green")
                        
                        QMessageBox.information(self, "Успех", 
                            f"Авторизация успешна!\nПользователь: {login}")
                        
                        return True
                    else:
                        QMessageBox.warning(self, "Ошибка авторизации", 
                            response_data.get('message', 'Неверный логин или пароль'))
                        return False
                        
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Ошибка", "Некорректный ответ от сервера")
                    return False
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}\n{response.text}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self, "Ошибка соединения", 
                f"Не удалось подключиться к серверу {self.server_url}\n\n"
                f"Проверьте:\n"
                f"1. Запущен ли сервер\n"
                f"2. Правильный ли адрес и порт\n"
                f"3. Нет ли блокировки брандмауэром\n\n"
                f"Ошибка: {str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
            return False
    
    def logout(self):
        """Выход из системы"""
        self.login = ""
        self.jwt_token = ""
        self.is_authenticated = False
        
        # Обновляем UI
        self.logoutButton.setEnabled(False)
        
        # Обновляем статус
        self.authStatusLabel.setText("Не авторизован")
        self.authStatusLabel.setStyleSheet("color: red")
        
        QMessageBox.information(self, "Выход", "Вы вышли из системы")
    
    def handle_retrain(self):
        """Обработчик нажатия кнопки переобучения"""
        # Если не авторизован, сначала авторизуемся
        if not self.is_authenticated:
            QMessageBox.information(self, "Требуется авторизация", 
                "Для переобучения модели необходима авторизация.\nПожалуйста, введите логин и пароль.")
            
            if not self.authenticate():
                return  # Если авторизация не удалась, прерываем
        
        # Показываем подтверждение
        reply = QMessageBox.question(self, 'Подтверждение переобучения',
            f'Вы уверены, что хотите переобучить модель?\n\n'
            f'Это действие запустит процесс переобучения на сервере\n'
            f'и может занять некоторое время.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Отправляем запрос на переобучение
            self.retrain_model()
    
    def retrain_model(self):
        """Отправка запроса на переобучение модели"""
        data = {
            "request_type": "retrain"
        }
        
        headers = {}
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        try:
            print(f"Отправка запроса переобучения на {self.server_url}")
            # Показываем сообщение об отправке
            QMessageBox.information(self, "Переобучение", 
                "Запрос на переобучение отправлен.\nОжидайте ответа от сервера...")
            
            response = requests.post(self.server_url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    message = response_data.get('message', 'Модель успешно переобучена')
                    response_type = response_data.get('type', 'success')
                    
                    QMessageBox.information(self, f"Результат: {response_type}", message)
                    
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Ошибка", "Некорректный ответ от сервера")
                    
            elif response.status_code == 401:
                QMessageBox.warning(self, "Ошибка авторизации", 
                    "JWT токен истек или недействителен.\nПожалуйста, авторизуйтесь заново.")
                self.logout()
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}\n{response.text}")
                
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self, "Ошибка соединения", 
                f"Не удалось подключиться к серверу {self.server_url}\n\n"
                f"Проверьте:\n"
                f"1. Запущен ли сервер\n"
                f"2. Правильный ли адрес и порт\n"
                f"3. Нет ли блокировки брандмауэром\n\n"
                f"Ошибка: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
    
    def send_request(self, request_type, voltage=None, power=None):
        """Отправка HTTP запроса на сервер (для обычных операций)"""
        data = {
            "request_type": request_type
        }
        
        if voltage is not None:
            data["voltage"] = voltage
        if power is not None:
            data["power"] = power
            
        try:
            print(f"Отправка запроса {request_type} на {self.server_url}")
            print(f"Данные запроса: {data}")  # Для отладки
            response = requests.post(self.server_url, json=data, timeout=10)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"Ответ сервера: {response_data}")  # Для отладки
                    message = response_data.get('message', 'Запрос выполнен успешно')
                    response_type = response_data.get('type', 'success')
                    
                    if 'prediction' in response_data:
                        prediction = response_data['prediction']
                        
                        # Обновляем отдельные поля
                        rotation_speed = prediction.get('rotation_speed', 'N/A')
                        current = prediction.get('current', 'N/A')
                        
                        # Форматируем значения
                        if rotation_speed != 'N/A':
                            self.speedValue.setText(f"{round(float(rotation_speed))} Об/мин")
                        else:
                            self.speedValue.setText("—")
                            
                        if current != 'N/A':
                            self.currentValue.setText(f"{round(float(current), 2)} А")
                        else:
                            self.currentValue.setText("—")
                        
                        # Обновляем информационную метку
                        self.infoLabel.setText(f"Расчет выполнен успешно")
                        self.infoLabel.setStyleSheet("color: green; font-style: normal;")
                    else:
                        self.speedValue.setText("—")
                        self.currentValue.setText("—")
                        self.infoLabel.setText("Нет данных для отображения")
                        self.infoLabel.setStyleSheet("color: orange; font-style: italic;")
                    
                    QMessageBox.information(self, f"Ответ: {response_type}", message)
                    
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Ошибка", "Некорректный ответ от сервера")
                    self.infoLabel.setText("Ошибка получения данных")
                    self.infoLabel.setStyleSheet("color: red; font-style: italic;")
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}\n{response.text}")
                self.infoLabel.setText(f"Ошибка сервера: {response.status_code}")
                self.infoLabel.setStyleSheet("color: red; font-style: italic;")
                
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self, "Ошибка соединения", 
                f"Не удалось подключиться к серверу {self.server_url}\n\n"
                f"Проверьте:\n"
                f"1. Запущен ли сервер\n"
                f"2. Правильный ли адрес и порт\n"
                f"3. Нет ли блокировки брандмауэром\n\n"
                f"Ошибка: {str(e)}")
            self.infoLabel.setText("Ошибка соединения с сервером")
            self.infoLabel.setStyleSheet("color: red; font-style: italic;")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
            self.infoLabel.setText(f"Ошибка: {str(e)}")
            self.infoLabel.setStyleSheet("color: red; font-style: italic;")
    
    def takeinputs(self):
        # ИСПРАВЛЕНО: Правильный порядок запроса параметров
        power, done1 = QInputDialog.getDouble(
            self, 'Ввод данных', 'Введите мощность (Вт):', decimals=2)
        
        if not done1:
            return
            
        voltage, done2 = QInputDialog.getDouble(
            self, 'Ввод данных', 'Введите напряжение (В):', decimals=2)
        
        if done1 and done2:
            # Очищаем предыдущие результаты
            self.speedValue.setText("Вычисление...")
            self.currentValue.setText("Вычисление...")
            self.infoLabel.setText("Отправка запроса на сервер...")
            self.infoLabel.setStyleSheet("color: blue; font-style: italic;")
            
            # ИСПРАВЛЕНО: Правильный порядок параметров при отправке
            # Отправляем запрос на расчет (без авторизации)
            self.send_request("calculate", voltage=voltage, power=power)
    
    def get_pdf(self, request_type):
        """Получение PDF файла с сервера (без авторизации)"""
        data = {
            "request_type": request_type
        }
        
        try:
            print(f"Отправка запроса PDF на {self.server_url}")
            response = requests.post(self.server_url, json=data, timeout=30)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/pdf':
                    # Сохраняем PDF файл
                    file_name = f"{request_type}_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.pdf"
                    
                    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                        self, "Сохранить PDF файл", file_name, "PDF Files (*.pdf)")
                    
                    if file_path:
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        QMessageBox.information(self, "Успех", f"PDF файл сохранен:\n{file_path}")
                else:
                    try:
                        response_data = response.json()
                        QMessageBox.information(self, f"Ответ: {response_data.get('type', 'info')}", 
                                              response_data.get('message', 'Запрос выполнен'))
                    except:
                        QMessageBox.warning(self, "Ошибка", "Получен некорректный ответ от сервера")
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сервера: {response.status_code}\n{response.text}")
                
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self, "Ошибка соединения", 
                f"Не удалось подключиться к серверу {self.server_url}\n\n"
                f"Проверьте:\n"
                f"1. Запущен ли сервер\n"
                f"2. Правильный ли адрес и порт\n"
                f"3. Нет ли блокировки брандмауэром\n\n"
                f"Ошибка: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    
    sys.exit(app.exec_())