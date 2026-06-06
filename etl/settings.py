import os
from dotenv import load_dotenv

load_dotenv()

PG_DSN = os.environ["PG_DSN"]
# e.g. postgresql://user:pass@host:5432/bplus_central
