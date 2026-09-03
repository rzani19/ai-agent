from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("TEST_VALUE"))
