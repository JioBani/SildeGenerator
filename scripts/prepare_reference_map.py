import json
import sys
from pathlib import Path
source, destination = map(Path, sys.argv[1:])
data = json.loads(source.read_text(encoding='utf-8'))
destination.write_text('window.land=' + json.dumps(data, separators=(',', ':')) + ';', encoding='utf-8')
