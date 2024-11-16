import logging
import os
from comfyui_web.config import Config, ProductionConfig, DevelopmentConfig, TestingConfig
from logging.handlers import RotatingFileHandler

"""
logging.NOTSET   当在日志记录器上设置时，表示将查询上级日志记录器以确定生效的级别。 如果仍被解析为 NOTSET，则会记录所有事件。 在处理器上设置时，所有事件都将被处理。
logging.DEBUG    详细的信息，通常只有试图诊断问题的开发人员才会感兴趣。
logging.INFO     确认程序按预期运行。
logging.WARNING  表明发生了意外情况，或近期有可能发生问题（例如‘磁盘空间不足’）。 软件仍会按预期工作。
logging.ERROR    由于严重的问题，程序的某些功能已经不能正常执行
logging.CRITICAL 严重的错误，表明程序已不能继续执行
"""

def setup_logger(log_file_name,  log_level, name='my_app_logger'):
    """设置日志记录器，并为每个应用分别指定不同的日志文件"""

    # 创建全局日志记录器
    logger = logging.getLogger(name)

    #
    logger.setLevel(log_level)

    # 确保日志目录存在
    if not os.path.exists(Config.LOG_PATH):
        os.makedirs(Config.LOG_PATH)

    # 创建日志文件路径
    log_file = os.path.join(Config.LOG_PATH, log_file_name)

    # 创建文件处理器（使用日志轮转）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=Config.MAX_LOG_SIZE, backupCount=Config.BACKUP_COUNT,encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 设置控制台处理器的日志级别
    console_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



# get flask environment variable
e = os.environ.get('FLASK_ENV', 'production')  # default flask environment is production

# set running mode
if e == 'dev':
    log_level = logging.DEBUG
    log_file_name = DevelopmentConfig.LOGGING_FILENAME
elif e == 'testing':
    log_level = logging.DEBUG
    log_file_name = TestingConfig.LOGGING_FILENAME
else:  # production as default
    log_level = logging.INFO
    log_file_name = ProductionConfig.LOGGING_FILENAME


# 创建comfyui的日志记录器
comfyui_loggerr = setup_logger(name='comfyui_logger',log_level=log_level, log_file_name='comfyui_'+log_file_name)
comfyui_loggerr.info("comfyui_logger logger initialized")

# 创建chatgpt的日志记录器
# chatgpt_loggerr = setup_logger(name='chatgpt_logger',log_level=log_level, log_file_name=Config.CHATGPT_LOG_FILE)
# chatgpt_loggerr.info("chatgpt_loggerr logger initialized")
