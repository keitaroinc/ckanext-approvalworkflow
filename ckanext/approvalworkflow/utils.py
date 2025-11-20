import ckanext.approvalworkflow.db as db


def initdb():
    db.init_db()


def dropdb():
    db.drop_db()
