import boto3

session = boto3.Session()

credentials = session.get_credentials()

print("Region:", session.region_name)
print("Credenciales encontradas:", credentials is not None)

dynamodb = boto3.client("dynamodb")

response = dynamodb.list_tables()

print("Tablas:", response["TableNames"])