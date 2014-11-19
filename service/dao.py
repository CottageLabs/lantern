from octopus.modules.es import dao

class SpreadsheetJobDAO(dao.ESDAO):
    __type__ = 'spreadsheet'

class RecordDAO(dao.ESDAO):
    __type__ = "record"