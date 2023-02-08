import os
from pathlib import Path
# basedir = os.path.abspath(os.path.dirname(__file__))
basedir = Path.cwd()
class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(basedir.joinpath(basedir, 'baangt.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False