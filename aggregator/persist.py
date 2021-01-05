from tempfile import gettempdir
from os import getenv, remove
import json

files_path = getenv('TEMP_FILES_PATH', gettempdir())
# format = '.json'


def load(project_id): 
    try:
        return json.loads(open(f'{files_path}/{project_id}.json').read())
    except:
        return {}


def write(project_id, content):
    """Write project info"""
    open(f'{files_path}/{project_id}.json', 'w').write(json.dumps(content))


def delete(project_id):
    """Deletes an readed project"""
    remove(f'{files_path}/{project_id}.json')
