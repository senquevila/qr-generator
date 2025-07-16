import json
import boto3
import qrcode
import uuid
import os
from io import BytesIO
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar cliente S3
s3_client = boto3.client("s3")

# Variables de entorno
BUCKET_NAME = os.environ.get("BUCKET_NAME")
REGION = os.environ.get("REGION")


def create_response(status_code: int, body: dict) -> dict:
    """Crear respuesta HTTP estandarizada"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def generate_qr(event, context):
    """
    Genera un código QR y lo almacena en S3
    """
    try:
        # Parsear body
        if "body" in event:
            body = (
                json.loads(event["body"])
                if isinstance(event["body"], str)
                else event["body"]
            )
        else:
            return create_response(400, {"error": "Body requerido"})

        # Validar texto requerido
        if not body.get("text"):
            return create_response(400, {"error": 'El parámetro "text" es requerido'})

        # Extraer parámetros
        text = body["text"]
        size = body.get("size", 10)
        border = body.get("border", 4)
        fill_color = body.get("fill_color", "black")
        back_color = body.get("back_color", "white")
        image_format = body.get("format", "PNG").upper()

        logger.info(f"Generando QR para: {text[:50]}...")

        # Generar QR
        qr_image_data = create_qr_code(
            text=text,
            size=size,
            border=border,
            fill_color=fill_color,
            back_color=back_color,
            image_format=image_format,
        )

        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"qr_{timestamp}_{unique_id}.{image_format.lower()}"

        # Subir a S3
        s3_url = upload_to_s3(qr_image_data, filename, image_format)

        logger.info(f"QR generado exitosamente: {s3_url}")

        return create_response(
            200,
            {
                "success": True,
                "message": "Código QR generado exitosamente",
                "qr_url": s3_url,
                "filename": filename,
                "text": text,
                "timestamp": timestamp,
            },
        )

    except Exception as e:
        logger.error(f"Error generando QR: {str(e)}")
        return create_response(
            500, {"error": "Error interno del servidor", "message": str(e)}
        )


def get_qr_info(event, context):
    """
    Obtiene información de un QR por su filename
    """
    try:
        filename = event.get("pathParameters", {}).get("filename")

        if not filename:
            return create_response(400, {"error": "Filename requerido"})

        # Verificar si existe en S3
        try:
            response = s3_client.head_object(Bucket=BUCKET_NAME, Key=filename)

            return create_response(
                200,
                {
                    "success": True,
                    "filename": filename,
                    "qr_url": f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{filename}",
                    "size": response["ContentLength"],
                    "last_modified": response["LastModified"].isoformat(),
                    "content_type": response["ContentType"],
                },
            )

        except s3_client.exceptions.NoSuchKey:
            return create_response(404, {"error": "QR no encontrado"})

    except Exception as e:
        logger.error(f"Error obteniendo info del QR: {str(e)}")
        return create_response(
            500, {"error": "Error interno del servidor", "message": str(e)}
        )


def list_qrs(event, context):
    """
    Lista QRs almacenados en S3
    """
    try:
        # Parámetros de query
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 20))
        prefix = query_params.get("prefix", "qr_")

        # Listar objetos en S3
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME, Prefix=prefix, MaxKeys=min(limit, 100)
        )

        qrs = []
        for obj in response.get("Contents", []):
            qrs.append(
                {
                    "filename": obj["Key"],
                    "qr_url": f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{obj['Key']}",
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
            )

        return create_response(
            200,
            {
                "success": True,
                "qrs": qrs,
                "count": len(qrs),
                "truncated": response.get("IsTruncated", False),
            },
        )

    except Exception as e:
        logger.error(f"Error listando QRs: {str(e)}")
        return create_response(
            500, {"error": "Error interno del servidor", "message": str(e)}
        )


def create_qr_code(
    text: str,
    size: int,
    border: int,
    fill_color: str,
    back_color: str,
    image_format: str,
) -> bytes:
    """Crea el código QR"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )

    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    img_buffer = BytesIO()
    img.save(img_buffer, format=image_format)
    img_buffer.seek(0)

    return img_buffer.getvalue()


def upload_to_s3(image_data: bytes, filename: str, image_format: str) -> str:
    """Sube imagen a S3"""
    content_type = f"image/{image_format.lower()}"
    if image_format.upper() == "JPEG":
        content_type = "image/jpeg"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
        ACL="public-read",
    )

    return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{filename}"
