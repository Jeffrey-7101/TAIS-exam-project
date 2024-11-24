import json
from io import BytesIO
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
outbound_notes_table = dynamodb.Table('OutboundNotes')
products_table = dynamodb.Table('Products')


def add_outbound_note(event, context):
    """Agregar una nota de salida."""
    body = json.loads(event['body'])
    note_id = body["NoteID"]
    product_ids = body["ProductIDs"]
    quantities = body["Quantities"]

    if len(product_ids) != len(quantities):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "The length of ProductIDs and Quantities must match."})
        }

    # Obtener los detalles de los productos desde la tabla Products
    products = []
    total_quantity = 0
    total_price = 0

    for idx, product_id in enumerate(product_ids):
        response = products_table.get_item(Key={"ProductID": product_id})
        if "Item" not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": f"Product with ID {product_id} not found."})
            }
        product = response["Item"]
        product["Quantity"] = Decimal(quantities[idx])
        product["UnitPrice"] = Decimal(product["UnitPrice"])
        product["TotalPrice"] = product["Quantity"] * product["UnitPrice"]

        products.append(product)
        total_quantity += product["Quantity"]
        total_price += product["TotalPrice"]

    # Crear la nota de salida
    note = {
        "NoteID": note_id,
        "Products": products,
        "TotalQuantity": Decimal(total_quantity),
        "TotalPrice": Decimal(total_price)
    }
    outbound_notes_table.put_item(Item=note)

    return {"statusCode": 201, "body": json.dumps({"message": "Outbound note added"})}

def get_all_outbound_notes(event, context):
    """Obtener todas las notas de salida."""
    response = outbound_notes_table.scan()
    items = response['Items']  # Obtiene todas las notas
    return {
        "statusCode": 200,
        "body": json.dumps(items, default=str)  # Convierte los datos a JSON serializable
    }


def delete_outbound_note(event, context):
    """Eliminar una nota de entrada."""
    note_id = event['pathParameters']['note_id']
    response = outbound_notes_table.get_item(Key={"NoteID": note_id})
    if "Item" not in response:
        return {"statusCode": 404, "body": json.dumps({"message": "outbound note not found"})}

    outbound_notes_table.delete_item(Key={"NoteID": note_id})
    return {"statusCode": 200, "body": json.dumps({"message": "outbound note deleted successfully"})}
