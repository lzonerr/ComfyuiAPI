import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

    #log
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    # COMFYUI_LOG_FILE = os.getenv('COMFYUI_LOG_FILE', 'comfyui.log')
    # CHATGPT_LOG_FILE = os.getenv('CHATGPT_LOG_FILE', 'chatgpt.log')
    LOG_PATH = 'logs'
    MAX_LOG_SIZE = 10 * 1024 * 1024 # 10MB
    BACKUP_COUNT = 3 # 保留3个备份日志

    # request time
    R_TIMEOUT = 100

    # Maximum number of pictures generated
    IMG_GEN_MAX = 4


    # receive worktype
    GEN_IMAGE = '1'
    GEN_MANEQUIN = '2'
    GEN_MATTING = '3'
    GEN_PICRST = '4'
    GEN_EXPIC = '5'


    # img path
    IMAGES_TMP = "tmp"

    #support image format
    IMG_FORMAT = ['bmp','ico','jpeg','jpg','png','psd','tga','tiff','webp']

    #Minio info
    MINIO_URL="42.194.158.22:9000"
    MINIO_ROOT_USER='super'
    MINIO_ROOT_PASSWORD='supersuper'
    UPLOAD_MINIO_BUCKET_NAME = 'upcomfyui'
    GENERATED_MINIO_BUCKET_NAME='gencomfyui'
    GENERATED_TMP_MINIO_BUCKET_NAME='gentmpcomfyui'


    SHARE_MINIO_URL_PRX = 'http://42.194.158.22:9000/gencomfyui/'
    SHARE_MINIO_URL_TMP_PRX = 'http://42.194.158.22:9000/gentmpcomfyui/'
    SHARE_RES_API = 'http://127.0.0.1:8702/api/outer/order/orderResult'

    TESTING = False

    def __str__(self):
        return "/".join([k+": "+v for k, v in vars(self.__class__).items() if not k.startswith('_')])


    @staticmethod
    def create_directories():
        savePath = [Config.IMAGES_TMP]
        for sp in savePath:
            if not os.path.exists(sp):
                print(f'{sp} create ')
                os.makedirs(sp)



class ProductionConfig(Config):
    DATABASE_URI = ''
    LOGGING_FILENAME = 'production.log'

class DevelopmentConfig(Config):
    DATABASE_URI = ''
    LOGGING_FILENAME = 'development.log'

class TestingConfig(Config):
    TESTING = True
    DATABASE_URI = ''
    LOGGING_FILENAME = 'testing.log'






Config.create_directories()