# QR Generator
## Comandos de Serverless Framework

### Instalar Serverless Framework
`npm install -g serverless`

### Crear proyecto
`mkdir qr-generator-api && cd qr-generator-api`

### Instalar dependencias
`npm install`

### Configurar AWS
`aws configure`

### Desplegar
`serverless deploy`

### Ver logs
`serverless logs -f generateQR -t`

### Eliminar
`serverless remove`

## Endpoints

### Generar QR
```
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/qr/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "https://example.com"}'
```

### Obtener info de QR
`curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/qr/qr_20240716_143022_abc12345.png`


### Listar QRs
`curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/qr`

### Respuesta
```
{
  "success": true,
  "message": "Código QR generado exitosamente",
  "qr_url": "https://qr-generator-api-qr-images-dev.s3.us-east-1.amazonaws.com/qr_20240716_143022_abc12345.png",
  "filename": "qr_20240716_143022_abc12345.png",
  "text": "https://example.com",
  "timestamp": "20240716_143022"
}
```
