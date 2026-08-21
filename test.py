import boto3

s3 = boto3.client("s3")

bucket = "purchase-approval-evidence-pcduque"

s3.put_object(
    Bucket=bucket,
    Key="test/test.txt",
    Body=b"hello"
)

print("Subida OK")

response = s3.get_object(
    Bucket=bucket,
    Key="test/test.txt"
)

print(response["Body"].read().decode())