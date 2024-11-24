import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
products_table = dynamodb.Table('Products')

def decimal_default(obj):
    """Convierte objetos Decimal a tipos nativos de Python."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def convert_dynamodb_item(item):
    """Convierte objetos DynamoDB (con Decimal) a tipos JSON serializables."""
    if isinstance(item, list):
        return [convert_dynamodb_item(i) for i in item]
    if isinstance(item, dict):
        return {k: convert_dynamodb_item(v) for k, v in item.items()}
    if isinstance(item, Decimal):
        return int(item) if item % 1 == 0 else float(item)
    return item

def add_product(event, context):
    """Agregar un producto."""
    body = json.loads(event['body'])
    
    try:
        products_table.put_item(
            product = {
                "ProductID": body["ProductID"],
                "Name": body["Name"],
                "Description": body["Description"],
                "Category": body["Category"],
                "Quantity": 0,
                "LastPrice": 0
            },
            ConditionExpression="attribute_not_exists(ProductID)"
        )
        return {
            "statusCode": 201,
            "body": json.dumps({"message": "Product added successfully"})
        }
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "ProductID already exists"})
        }

def get_products(event, context):
    """Obtener todos los productos."""
    response = products_table.scan()
    items = response['Items']
    # Convertir los elementos a tipos serializables
    items_serialized = [convert_dynamodb_item(item) for item in items]

    return {
        "statusCode": 200,
        "body": json.dumps(items_serialized, default=decimal_default)
    }

def update_product(event, context):
    """Actualizar los detalles de un producto."""
    body = json.loads(event['body'])
    product_id = event['pathParameters']['product_id']

    # Validar si el producto existe
    response = products_table.get_item(Key={"ProductID": product_id})
    if "Item" not in response:
        return {"statusCode": 404, "body": json.dumps({"message": "Product not found"})}

    # Actualizar los atributos enviados
    update_expression = "SET "
    expression_attribute_values = {}
    for key, value in body.items():
        update_expression += f"{key} = :{key}, "
        expression_attribute_values[f":{key}"] = value
    update_expression = update_expression.rstrip(", ")

    products_table.update_item(
        Key={"ProductID": product_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    return {"statusCode": 200, "body": json.dumps({"message": "Product updated successfully"})}

def delete_product(event, context):
    """Eliminar un producto."""
    product_id = event['pathParameters']['product_id']

    # Validar si el producto existe
    response = products_table.get_item(Key={"ProductID": product_id})
    if "Item" not in response:
        return {"statusCode": 404, "body": json.dumps({"message": "Product not found"})}

    # Eliminar el producto
    products_table.delete_item(Key={"ProductID": product_id})
    return {"statusCode": 200, "body": json.dumps({"message": "Product deleted successfully"})}
