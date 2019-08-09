import os

class Config(object):
    LDAP_SERVER_URI = os.getenv("LDAP_SERVER_URI")
    PAGE_COUNT = 20
    MEMCACHED_HOST = 'memcached_server'

class DevelopmentConfig(Config):
    PYTHON_LDAP_DEBUG_LVL = "METHOD_W_ARGUMENTS_W_RESULTS"
    LOG_FILE_ADDRESS = "log/develop.log"

class ProductionConfig(Config):
    PYTHON_LDAP_DEBUG_LVL = "METHOD_W_ARGUMENTS"
    LOG_FILE_ADDRESS = "log/production.log"

def set_environment(environment):
    if environment == "production":
        return ProductionConfig()
    return DevelopmentConfig()
