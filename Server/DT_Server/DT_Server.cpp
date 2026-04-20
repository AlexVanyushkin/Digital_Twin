#include <cstdlib>
#include <drogon/drogon.h>
#include <drogon/utils/Utilities.h>
#include <iostream>
#include <json/json.h>
#include <string>
#include <array>
#include <fstream>
#include <libpq-fe.h>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <random>
#include <openssl/hmac.h>
#include <openssl/evp.h>
#include <openssl/bio.h>
#include <openssl/buffer.h>

using namespace drogon;

typedef std::function<void(const HttpResponsePtr&)> Callback;

// Реализация JWT
class JWTHandler {
private:
    static const std::string SECRET_KEY;
    static const int TOKEN_EXPIRY_HOURS = 24;

    // Base64 кодирование (URL-safe)
    static std::string base64UrlEncode(const std::string& input) {
        // Стандартное Base64 кодирование
        BIO* b64 = BIO_new(BIO_f_base64());
        BIO* bmem = BIO_new(BIO_s_mem());
        BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL);
        b64 = BIO_push(b64, bmem);
        BIO_write(b64, input.c_str(), input.length());
        BIO_flush(b64);

        BUF_MEM* bptr;
        BIO_get_mem_ptr(b64, &bptr);

        std::string result(bptr->data, bptr->length);
        BIO_free_all(b64);

        // Преобразуем в URL-safe Base64
        for (char& c : result) {
            if (c == '+') c = '-';
            else if (c == '/') c = '_';
        }

        // Удаляем padding
        while (!result.empty() && result.back() == '=') {
            result.pop_back();
        }

        return result;
    }

    // Base64 декодирование (URL-safe)
    static std::string base64UrlDecode(const std::string& input) {
        std::string padded = input;

        // Восстанавливаем стандартный Base64
        for (char& c : padded) {
            if (c == '-') c = '+';
            else if (c == '_') c = '/';
        }

        // Добавляем padding
        while (padded.length() % 4 != 0) {
            padded += '=';
        }

        BIO* b64 = BIO_new(BIO_f_base64());
        BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL);
        BIO* bmem = BIO_new_mem_buf(padded.c_str(), padded.length());
        bmem = BIO_push(b64, bmem);

        // Используем вектор вместо VLA
        size_t max_len = padded.length();
        std::vector<char> buffer(max_len);

        int len = BIO_read(bmem, buffer.data(), max_len);
        BIO_free_all(bmem);

        return std::string(buffer.data(), len);
    }

    // Создание HMAC-SHA256 подписи
    static std::string createSignature(const std::string& data) {
        unsigned int len = 32; // SHA256 produces 32 bytes
        std::vector<unsigned char> result(32);

        HMAC(EVP_sha256(),
            SECRET_KEY.c_str(), SECRET_KEY.length(),
            reinterpret_cast<const unsigned char*>(data.c_str()),
            data.length(),
            result.data(), &len);

        return std::string(reinterpret_cast<char*>(result.data()), len);
    }

public:
    static std::string createToken(const std::string& login, const std::string& role = "admin") {
        // Создаем header
        Json::Value header;
        header["alg"] = "HS256";
        header["typ"] = "JWT";

        Json::FastWriter writer;
        std::string header_json = writer.write(header);
        // Удаляем перенос строки в конце
        if (!header_json.empty() && header_json.back() == '\n') {
            header_json.pop_back();
        }
        std::string header_encoded = base64UrlEncode(header_json);

        // Создаем payload
        Json::Value payload;
        payload["login"] = login;
        payload["role"] = role;

        auto now = std::chrono::system_clock::now();
        auto exp_time = now + std::chrono::hours(TOKEN_EXPIRY_HOURS);
        auto iat_timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()).count();
        auto exp_timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            exp_time.time_since_epoch()).count();

        payload["iat"] = static_cast<Json::Int64>(iat_timestamp);
        payload["exp"] = static_cast<Json::Int64>(exp_timestamp);

        std::string payload_json = writer.write(payload);
        if (!payload_json.empty() && payload_json.back() == '\n') {
            payload_json.pop_back();
        }
        std::string payload_encoded = base64UrlEncode(payload_json);

        // Создаем подпись
        std::string signature_input = header_encoded + "." + payload_encoded;
        std::string signature = createSignature(signature_input);
        std::string signature_encoded = base64UrlEncode(signature);

        return header_encoded + "." + payload_encoded + "." + signature_encoded;
    }

    static bool verifyToken(const std::string& token, std::string& login) {
        try {
            // Разбиваем токен на части
            size_t first_dot = token.find('.');
            size_t second_dot = token.find('.', first_dot + 1);

            if (first_dot == std::string::npos || second_dot == std::string::npos) {
                std::cerr << "Invalid token format" << std::endl;
                return false;
            }

            std::string header_encoded = token.substr(0, first_dot);
            std::string payload_encoded = token.substr(first_dot + 1, second_dot - first_dot - 1);
            std::string signature_encoded = token.substr(second_dot + 1);

            // Проверяем подпись
            std::string signature_input = header_encoded + "." + payload_encoded;
            std::string expected_signature = createSignature(signature_input);
            std::string expected_signature_encoded = base64UrlEncode(expected_signature);

            if (expected_signature_encoded != signature_encoded) {
                std::cerr << "Invalid signature" << std::endl;
                return false;
            }

            // Декодируем payload
            std::string payload_json = base64UrlDecode(payload_encoded);

            Json::Value payload;
            Json::Reader reader;

            if (!reader.parse(payload_json, payload)) {
                std::cerr << "Failed to parse payload JSON" << std::endl;
                return false;
            }

            // Проверяем срок действия
            if (payload.isMember("exp")) {
                auto exp_timestamp = payload["exp"].asInt64();
                auto now = std::chrono::duration_cast<std::chrono::seconds>(
                    std::chrono::system_clock::now().time_since_epoch()
                ).count();

                if (now > exp_timestamp) {
                    std::cerr << "Token expired" << std::endl;
                    return false;
                }
            }

            // Извлекаем логин
            if (payload.isMember("login")) {
                login = payload["login"].asString();
                return true;
            }

            std::cerr << "No login in payload" << std::endl;
            return false;

        }
        catch (const std::exception& e) {
            std::cerr << "Token verification error: " << e.what() << std::endl;
            return false;
        }
    }

    static std::string extractTokenFromHeader(const HttpRequestPtr& request) {
        auto auth_header = request->getHeader("Authorization");

        if (auth_header.empty()) {
            return "";
        }

        const std::string bearer_prefix = "Bearer ";
        if (auth_header.length() > bearer_prefix.length() &&
            auth_header.substr(0, bearer_prefix.length()) == bearer_prefix) {
            return auth_header.substr(bearer_prefix.length());
        }

        return "";
    }
};

// Секретный ключ для JWT (в production должен быть в конфиге)
const std::string JWTHandler::SECRET_KEY = "your-secret-key-change-this-in-production-2024-min-32-chars!";

// Класс для работы с PostgreSQL через libpq
class PostgresDB {
private:
    PGconn* conn_;

public:
    PostgresDB() : conn_(nullptr) {}

    ~PostgresDB() {
        if (conn_) {
            PQfinish(conn_);
        }
    }

    bool connect(const std::string& host,
        int port,
        const std::string& dbname,
        const std::string& user,
        const std::string& password) {

        std::string conninfo = "host=" + host +
            " port=" + std::to_string(port) +
            " dbname=" + dbname +
            " user=" + user +
            " password=" + password;

        conn_ = PQconnectdb(conninfo.c_str());

        if (PQstatus(conn_) != CONNECTION_OK) {
            std::cerr << "Connection to database failed: " << PQerrorMessage(conn_) << std::endl;
            return false;
        }

        std::cout << "Successfully connected to database: " << dbname << std::endl;
        return true;
    }

    bool checkAdminCredentials(const std::string& login, const std::string& password) {
        if (!conn_) {
            std::cerr << "Database not connected" << std::endl;
            return false;
        }

        // Используем параметризованный запрос для защиты от SQL инъекций
        const char* paramValues[2] = { login.c_str(), password.c_str() };
        int paramLengths[2] = { (int)login.length(), (int)password.length() };
        int paramFormats[2] = { 0, 0 }; // текстовый формат

        PGresult* res = PQexecParams(conn_,
            "SELECT COUNT(*) FROM users WHERE login = $1 AND password = $2",
            2,           // количество параметров
            nullptr,     // типы параметров (NULL = автоматическое определение)
            paramValues,
            paramLengths,
            paramFormats,
            0            // текстовый формат результата
        );

        if (PQresultStatus(res) != PGRES_TUPLES_OK) {
            std::cerr << "Query failed: " << PQerrorMessage(conn_) << std::endl;
            PQclear(res);
            return false;
        }

        int count = atoi(PQgetvalue(res, 0, 0));
        PQclear(res);

        return count > 0;
    }
};

// Глобальный объект для работы с БД
PostgresDB g_db;

void indexHandler(const HttpRequestPtr& request, Callback&& callback) {
    Json::Value jsonBody;

    // Получаем JSON из тела запроса
    auto requestBody = request->getJsonObject();

    // Для отправки файлов
    std::string current_file = "./current7.pdf";
    std::string voltage_file = "./speed7.pdf";

    // Для формирования консольной строки
    std::string cmd_string;

    // Для входных данных для расчета
    int power;
    int voltage;

    //---ОБРАБОТКА-ОШИБОК------------------------------------------
    if (requestBody == nullptr) {
        jsonBody["type"] = "error";
        jsonBody["message"] = "body is required";

        auto response = HttpResponse::newHttpJsonResponse(jsonBody);
        response->setStatusCode(HttpStatusCode::k400BadRequest);

        callback(response);
        return;
    }
    //------------------------------------------------------------------------

    // Получаем тип запроса из тела запроса
    auto request_type = requestBody->get("request_type", "").asString();

    // Обработка запроса авторизации
    if (request_type == "auth") {
        if (!requestBody->isMember("login") || !requestBody->isMember("password")) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "fields `login` and `password` are required for auth";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k400BadRequest);
            callback(response);
            return;
        }

        std::string login = (*requestBody)["login"].asString();
        std::string password = (*requestBody)["password"].asString();

        if (g_db.checkAdminCredentials(login, password)) {
            // Создаем JWT токен
            std::string token = JWTHandler::createToken(login);

            jsonBody["type"] = "success";
            jsonBody["message"] = "Authentication successful";
            jsonBody["token"] = token;

            std::cout << "User " << login << " authenticated successfully" << std::endl;

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k200OK);
            callback(response);
        }
        else {
            jsonBody["type"] = "error";
            jsonBody["message"] = "Invalid login or password";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k401Unauthorized);
            callback(response);
        }
        return;
    }

    // Формируем базовый ответ
    jsonBody["type"] = "success";
    jsonBody["message"] = "Accepted!";

    // Если запросили просто вычисление
    if (request_type == "calculate")
    {
        // Проверяем наличие полей power и voltage
        if (!requestBody->isMember("power") || !requestBody->isMember("voltage")) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "fields `power` and `voltage` are required for calculate";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k400BadRequest);
            callback(response);
            return;
        }

        power = (*requestBody)["power"].asInt();
        voltage = (*requestBody)["voltage"].asInt();

        cmd_string = "python data_predict.py " + std::to_string(power) + " " + std::to_string(voltage);
        system(cmd_string.c_str());

        // Для чтения json буфера для работы скриптов python
        Json::Value root;
        Json::Reader reader;

        // Открытие и чтение JSON файла
        std::ifstream file("data_buffer.json");
        if (!file.is_open()) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "Could not open data_buffer.json";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k500InternalServerError);
            callback(response);
            return;
        }

        // Парсинг файла
        if (reader.parse(file, root)) {
            // Извлечение значений
            int rotation_speed = root["rotation_speed"].asInt();
            int current = root["current"].asInt();

            jsonBody["prediction"]["rotation_speed"] = rotation_speed;
            jsonBody["prediction"]["current"] = current;
        }
        else {
            jsonBody["type"] = "error";
            jsonBody["message"] = "Failed to parse JSON file";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k500InternalServerError);
            callback(response);
            return;
        }

        auto response = HttpResponse::newHttpJsonResponse(jsonBody);
        callback(response);
        return;
    }

    // Если запросили график тока
    if (request_type == "get_graph_current_pdf")
    {
        system("python data_plot.py");

        std::ifstream file(current_file, std::ios::binary);
        if (!file.is_open()) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "required files do not exist";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k404NotFound);
            callback(response);
            return;
        }

        file.seekg(0, std::ios::end);
        size_t file_size = file.tellg();
        file.seekg(0, std::ios::beg);

        std::string fileContent(file_size, '\0');
        if (!file.read(&fileContent[0], file_size))
        {
            jsonBody["type"] = "error";
            jsonBody["message"] = "error opening file";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k500InternalServerError);
            callback(response);
            return;
        }
        file.close();

        auto response = HttpResponse::newHttpResponse();
        response->setContentTypeCode(CT_APPLICATION_PDF);
        response->addHeader("Content-Disposition", "inline; filename=\"current7.pdf\"");
        response->setBody(fileContent);
        callback(response);
        return;
    }

    // Если запросили график оборотов
    if (request_type == "get_graph_speed_pdf")
    {
        system("python data_plot.py");

        std::ifstream file(voltage_file, std::ios::binary);
        if (!file.is_open()) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "required files do not exist";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k404NotFound);
            callback(response);
            return;
        }

        file.seekg(0, std::ios::end);
        size_t file_size = file.tellg();
        file.seekg(0, std::ios::beg);

        std::string fileContent(file_size, '\0');
        if (!file.read(&fileContent[0], file_size))
        {
            jsonBody["type"] = "error";
            jsonBody["message"] = "error opening file";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k500InternalServerError);
            callback(response);
            return;
        }
        file.close();

        auto response = HttpResponse::newHttpResponse();
        response->setContentTypeCode(CT_APPLICATION_PDF);
        response->addHeader("Content-Disposition", "inline; filename=\"speed7.pdf\"");
        response->setBody(fileContent);
        callback(response);
        return;
    }

    // Если запросили переобучение модели (ТОЛЬКО С ВАЛИДНЫМ JWT)
    if (request_type == "retrain") {
        // Проверяем JWT токен из заголовка Authorization
        std::string token = JWTHandler::extractTokenFromHeader(request);

        if (token.empty()) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "JWT token is required for retrain operation";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k401Unauthorized);
            callback(response);
            return;
        }

        std::string login;
        if (!JWTHandler::verifyToken(token, login)) {
            jsonBody["type"] = "error";
            jsonBody["message"] = "Invalid or expired JWT token";

            auto response = HttpResponse::newHttpJsonResponse(jsonBody);
            response->setStatusCode(HttpStatusCode::k401Unauthorized);
            callback(response);
            return;
        }

        // Токен валиден, можно выполнять переобучение
        std::cout << "Admin " << login << " requested model retraining (JWT verified)" << std::endl;

        // Получаем дополнительные параметры для переобучения (если есть)
        if (requestBody->isMember("voltage") && requestBody->isMember("power")) {
            double retrain_voltage = (*requestBody)["voltage"].asDouble();
            double retrain_power = (*requestBody)["power"].asDouble();

            std::cout << "Retraining with parameters: voltage=" << retrain_voltage
                << ", power=" << retrain_power << std::endl;

            cmd_string = "python retrain_model.py " +
                std::to_string(retrain_voltage) + " " +
                std::to_string(retrain_power);
        }
        else {
            cmd_string = "python retrain_model.py";
        }

        // Запускаем переобучение
        int ret = system(cmd_string.c_str());

        if (ret == 0) {
            jsonBody["type"] = "success";
            jsonBody["message"] = "Model retrained successfully";
        }
        else {
            jsonBody["type"] = "error";
            jsonBody["message"] = "Model retraining failed";
        }

        auto response = HttpResponse::newHttpJsonResponse(jsonBody);
        callback(response);
        return;
    }

    // Если тип запроса не распознан
    jsonBody["type"] = "error";
    jsonBody["message"] = "Unknown request_type";
    auto response = HttpResponse::newHttpJsonResponse(jsonBody);
    response->setStatusCode(HttpStatusCode::k400BadRequest);
    callback(response);
}

int main() {
    std::cout << "Server is running with JWT authentication (OpenSSL only)..." << std::endl;

    // Подключаемся к базе данных
    if (!g_db.connect("localhost", 5432, "admin_users", "postgres", "pitonist0620")) {
        std::cerr << "Failed to connect to database. Server will continue without DB support." << std::endl;
        std::cerr << "Authentication will not work." << std::endl;
    }

    // Загружаем конфигурацию Drogon
    app()
        .loadConfigFile("./config.json")
        .registerHandler("/", &indexHandler, { Post })
        .run();

    return EXIT_SUCCESS;
}