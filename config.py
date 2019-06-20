
# SQLALCHEMY_URL = 'postgres://turbobee_pipeline:turbobee_pipeline@localhost:15432/turbobee_pipeline'
SQLALCHEMY_URL = 'sqlite:///'
SQLALCHEMY_ECHO = False


# Configuration of the pipeline; if you start 'vagrant up rabbitmq' 
# container, the port is localhost:8072 - but for production, you 
# want to point to the ADSImport pipeline 
CELERY_BROKER = 'pyamqp://guest:guest@localhost:5682/turbobee_pipeline'
CELERY_INCLUDE = ['adstb.tasks']

# possible values: WARN, INFO, DEBUG
LOGGING_LEVEL = 'DEBUG'


# Access token to be used against ADS API
API_TOKEN = 'empty'


# location of our mini-microservice for fetching HTML pages, it can be deployed
# together with the pipeline (if using eb-deploy) or it can run somewhere else
PUPPETEER_ENDPOINT = 'http://localhost:3001/scrape'


# the turbobee-microservice that accepts objects that our pipelne generates
UPDATE_ENDPOINT = 'https://devapi.adsabs.harvard.edu/v1/store/update'
SEARCH_ENDPOINT = 'https://devapi.adsabs.harvard.edu/v1/search/query'
STORE_SEARCH_ENDPOINT = 'https://devapi.adsabs.harvard.edu/v1/store/search'
LINK_URL_TEMPLATE = 'http://dev.adsabs.harvard.edu/abs/{}'  # used for links in meta tags
