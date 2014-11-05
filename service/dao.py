from octopus.modules.es import dao
from portality.core import app

class MyDAO(dao.ESDAO):
    __type__ = 'myobj'
