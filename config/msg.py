import json
import os
from pathlib import Path

msg = json.loads(Path(__file__).with_name("response_msg.json").read_text())
