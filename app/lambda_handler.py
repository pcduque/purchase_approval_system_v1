from mangum import Mangum

from app.main import app


handler = Mangum(app, api_gateway_base_path="/default")
