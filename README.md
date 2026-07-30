# zBot

Bot Zalo viết bằng Python. Hỗ trợ đa nick, phân quyền nhiều cấp..

Bắt đầu phát triển: **20/05/2026**  
Tác giả: **Hoàng Anh Tuấn** (HAT)

---

## Yêu cầu

- Python 3.10+
- pip3
- tmux (Linux) hoặc CMD (Windows)

Cài thư viện:

```bash
pip install -r requirements.txt
```

Hoặc cứ chạy `start.sh` — script tự detect và cài module còn thiếu.

---

## Khởi động

```bash
bash start.sh
```

Linux dùng tmux, Windows tự mở 3 cửa sổ CMD riêng (User / Admin / Main).  
Lần đầu chưa có cookie thì bot hỏi quét QR để đăng nhập.

---

## Cấu trúc thư mục

```
zBot/
├── main.py                  # Entry point, class zrcapis
├── index.py                 # Re-export trung tâm dùng trong lệnh
├── start.sh                 # Script khởi động + auto-install
├── requirements.txt
│
├── api/                     # Zalo API wrapper
│   ├── app/
│   │   ├── apiclient.py     # HTTP client, WebSocket
│   │   ├── appstate.py      # Session / cookie state
│   │   └── event.py         # Parse event từ Zalo
│   ├── methods/
│   │   ├── send.py          # Gửi tin nhắn, sticker, file, reaction…
│   │   ├── fetch.py         # Lấy thông tin user/group/phone
│   │   ├── get.py           # GET requests nội bộ
│   │   ├── upload.py        # Upload media
│   │   ├── account.py       # Thông tin tài khoản
│   │   ├── threadgroup.py   # Quản lý nhóm
│   │   └── user.py          # Quản lý user
│   └── util/
│       ├── Enum.py          # PermissionLevel, MsgStyle, ThreadType
│       ├── msg.py           # Message, Mention, MessageStyle…
│       └── logging.py       # Logger màu terminal
│
├── app/
│   ├── helpers/
│   │   ├── message.py       # MessageHelper: sendSuccess / Warning / Error / Info
│   │   └── methods.py       # userName, groupInfo, get_platform…
│   ├── library/
│   │   └── packages.py      # Import tập trung (os, json, PIL, requests…)
│   ├── login/
│   │   ├── client.py        # Khởi động bot từ session
│   │   ├── data.py          # start_threads, run_bot, clean
│   │   └── qr.py            # Đăng nhập QR
│   └── module/
│       ├── commandLoader.py # Load lệnh động, kiểm tra quyền, cooldown
│       ├── message.py       # Xử lý tin nhắn đến
│       └── utils.py         # Utilsmodule, MediaCache, Listen
│
├── src/
│   ├── command/             # Toàn bộ lệnh bot (load tự động)
│   │   ├── antimanager/     # Chống spam, bot, forward, URL độc hại
│   │   ├── bot_services/    # Quản trị: menu, quyền, alias, restart…
│   │   ├── chat_bot/        # Lệnh chat: QR, sticker, info, dịch thuật…
│   │   └── music/           # Nhạc: Zing MP3, SoundCloud, Audiomack
│   └── services/
│       ├── init/
│       │   └── admin.py     # initAdmin, phân quyền, portal giữa các bot
│       ├── pillow/          # Vẽ ảnh: menu, top chat, info user, bài hát
│       ├── data/            # chatCounter — đếm tin nhắn theo nhóm
│       └── utils/
│           └── jsonio.py    # load_json, save_json, read_settings…
│
├── config/
│   ├── login.json           # Danh sách nick + session cookies
│   ├── bot/Data-{uid}.json  # Config từng bot: lệnh, quyền, alias, cooldown
│   ├── chat_count/          # Số tin nhắn theo nhóm
│   ├── storage-link.json    # Cache link media đã upload
│   └── tempStorage.json     # Lưu tạm (thread restart…)
│
└── assets/
    ├── font/                # Font dùng cho Pillow
    ├── cache/               # Cache media (ảnh, voice, sticker…)
    └── log/error.txt        # Log lỗi runtime
```

---

## Hệ thống quyền

| Cấp | Tên | Mô tả |
|-----|-----|-------|
| 0 | User | Tất cả mọi người |
| 1 | Group Admin | Admin nhóm Zalo |
| 2 | Bot Admin | Admin do chủ bot chỉ định |
| 3 | High Admin | Super admin |
| 4 | Developer | Toàn quyền — chủ bot |

Quyền Developer (`cấp 4`) được tự động gán khi khởi động:
- Nếu là **main bot** → tự add vào `developerAdmin`
- Nếu chỉ chạy **1 nick duy nhất** (không có main bot) → cũng tự nhận Developer, không cần cấu hình thêm
- Nếu là **bot con** trong hệ thống đa nick → resolve UID của main bot qua portal nội bộ (`127.0.0.1:7799`)

---

## Viết lệnh mới

Tạo file `.py` bất kỳ trong `src/command/`, bot tự load khi khởi động.

```python
# src/command/chat_bot/hello.py
from index import *

def run(self, message, data, userId, threadId, type):
    self.sendSuccess("Xin chào!", threadId, type, data)

dependencies = {
    "name":        "hello",
    "description": "Chào hỏi",
    "permission":  0,          # 0=tất cả, 1=group admin, 2=bot admin, 3=high admin, 4=dev
    "cooldown":    3,          # giây, chỉ áp dụng với User (cấp 0)
    "alias":       ["hi"],
    "noPrefix":    False,      # True = không cần prefix để gọi
    "is_main":     False,      # True = chỉ main bot mới load lệnh này
    "main":        run,
}
```

File có `dependencies` → được load. Không có → bỏ qua.  
Lệnh tự động xuất hiện trong menu và được lưu vào `config/bot/Data-{uid}.json`.

---

## Gửi tin nhắn

Shortcut nhanh:

```python
self.sendSuccess("OK rồi!", threadId, type, data)
self.sendWarning("Không tìm thấy.", threadId, type, data)
self.sendError("Lỗi rồi!", threadId, type, data)
self.sendInfo("Thông tin…", threadId, type, data)
```

Hoặc tùy chỉnh style:

```python
self.replyMessageStyle(
    "Nội dung",
    data, threadId, type,
    color="gr",      # gr=xanh, yl=vàng, r=đỏ, o=cam
    title="TITLE",
    userId=userId,   # để @mention
)
```

---

## Cấu hình đa nick

`config/login.json`:

```json
{
  "data": [
    {
      "username": "Bot Chính",
      "author_id": "uid_ở_đây",
      "imei": "...",
      "prefix": ",",
      "session_cookies": { "zpw_sek": "..." },
      "is_main_bot": true,
      "status": true
    },
    {
      "username": "Bot Phụ",
      "author_id": "uid_ở_đây",
      "imei": "...",
      "prefix": ".",
      "session_cookies": { "zpw_sek": "..." },
      "is_main_bot": false,
      "status": true
    }
  ]
}
```

- `is_main_bot: true` → nick đó là chủ hệ thống, tự nhận Developer
- `status: false` → nick đó bị tắt, không load
- `het_han` (tuỳ chọn) → định dạng `"HH:MM:SS/DD/MM/YYYY"`, bot tự tắt khi hết hạn

---

## Import pattern

Trong lệnh:
```python
from app.core.index import * 
```
# cứ chỉ cần có from app.core.index import * là mọi: Message, Mention, MsgStyle, PermissionLevel, json, os… đã đc gọi

Trong module nội bộ:
```python
from app.library.packages import *
from src.services.utils.jsonio import load_json, save_json, read_settings
```