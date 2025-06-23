# eBay API Integration

Ứng dụng Flask tích hợp với eBay API để tìm kiếm sản phẩm, lấy thông tin chi tiết và phân tích listing.

## Tính năng

- **Tìm kiếm sản phẩm**: Tìm kiếm sản phẩm trên eBay theo từ khóa
- **Thông tin chi tiết**: Lấy thông tin chi tiết của sản phẩm theo ID
- **Gợi ý danh mục**: Gợi ý danh mục dựa trên từ khóa
- **Phân tích listing**: Phân tích URL listing eBay để trích xuất thông tin

## Cài đặt

1. Tạo môi trường ảo:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file `.env` với các biến môi trường:
```
EBAY_APP_ID=your_ebay_app_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
```

## Chạy ứng dụng

### Development
```bash
python app.py
```

### Production với Gunicorn
```bash
gunicorn app:app
```

## API Endpoints

### GET /search
Tìm kiếm sản phẩm trên eBay

**Parameters:**
- `q` (required): Từ khóa tìm kiếm
- `limit` (optional): Số lượng kết quả (mặc định: 5)

### GET /item
Lấy thông tin chi tiết sản phẩm

**Parameters:**
- `id` (required): ID sản phẩm eBay

### GET /category
Gợi ý danh mục

**Parameters:**
- `q` (required): Từ khóa danh mục

### POST /analyze-listing
Phân tích listing eBay

**Body:**
```json
{
  "url": "https://www.ebay.com/itm/..."
}
```

## Swagger Documentation

Truy cập `/apidocs` để xem tài liệu API đầy đủ với Swagger UI.

## Cấu trúc thư mục

```
├── app.py              # Ứng dụng Flask chính
├── requirements.txt    # Dependencies
├── openapi.json       # Cấu hình OpenAPI/Swagger
├── Procfile           # Cấu hình deployment
├── .env               # Biến môi trường (không commit)
└── README.md          # Tài liệu này
```

