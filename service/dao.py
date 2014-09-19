import esprit
from portality.core import app

class MyDAO(esprit.dao.DomainObject):
    __type__ = 'index'
    __conn__ = esprit.raw.Connection(app.config.get('ELASTIC_SEARCH_HOST'), app.config.get('ELASTIC_SEARCH_INDEX'))