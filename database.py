import psycopg2
import configparser

# Charger le fichier de configuration
config = configparser.ConfigParser()
config.read("config.ini")
def get_db_connection():
    db_config = config["database"]
    return psycopg2.connect(
        dbname=db_config["DB_NAME"],
        user=db_config["DB_USER"],
        password=db_config["DB_PASSWORD"],
        host=db_config["DB_HOST"],
        port=db_config.getint("PORT")
    )
