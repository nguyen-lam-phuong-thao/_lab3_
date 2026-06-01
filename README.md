# Lab 3 Baseline Chatbot

Project này là chatbot baseline đơn giản cho dataset văn học local.

Bot làm 3 việc:
- `search`: tìm tác phẩm theo tên, tác giả, thể loại, khu vực
- `recommend`: gợi ý tác phẩm tương tự theo metadata
- `summarize`: giới thiệu ngắn về tác phẩm hoặc tác giả

## Chạy

Linux/macOS:

```bash
cd /mnt/d/thao/d/Vin-AI/_lab3_
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 chatbot.py
python3 chatbot.py --query "Giới thiệu Nam Cao"
```

Windows PowerShell:

```powershell
cd D:\thao\d\Vin-AI\_lab3_
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python chatbot.py
python chatbot.py --query "Giới thiệu Nam Cao"
```

## File quan trọng

- `logs/YYYY-MM-DD.log`: log JSON đơn giản, mỗi lượt chat là 1 dòng
- `reports/chat_history.txt`: lịch sử hỏi đáp dễ đọc
- `tests/test_chatbot.py`: test cơ bản

## Xem nhanh kết quả đã chạy

```bash
python3 evaluate_logs.py
```

Windows PowerShell:

```powershell
python evaluate_logs.py
```

Nếu muốn lưu summary ra file:

```bash
python3 evaluate_logs.py --output ./reports/evaluation_summary.txt
```
