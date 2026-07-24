# Al-Aziz Voting Bot — SQLite versiya

Bu versiyada **PostgreSQL kerak emas**. Baza avtomatik ravishda quyidagi faylda yaratiladi:

```text
data/alaziz_voting.db
```

## Eng oson ishga tushirish

1. ZIP faylni oddiy papkaga chiqaring.
2. `START_BOT.bat` faylini ikki marta bosing.
3. Birinchi ishga tushishda Notepad ochiladi.
4. `.env` ichida faqat quyidagilarni to‘g‘rilang:

```env
BOT_TOKEN=BotFather_bergan_token
ADMIN_IDS=sizning_telegram_id
```

5. Faylni saqlang va Notepadni yoping.
6. Bot avtomatik ishga tushadi.

## PowerShell orqali

```powershell
cd "C:\Users\User\Desktop\alaziz-voting-bot-sqlite"
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python bot.py
```

Alohida `alembic upgrade head` buyrug‘i shart emas. Jadvallar bot ishga tushganda avtomatik yaratiladi.

## Keyingi safar

`START_BOT.bat` faylini ikki marta bosing yoki:

```powershell
.\.venv\Scripts\Activate.ps1
python bot.py
```

## Muhim

- Botni ZIP/RAR ichidan ishlatmang.
- Telegram tokenni hech kimga yubormang.
- Bazani zaxiralash uchun `data/alaziz_voting.db` faylini nusxalash kifoya.
- Bazani noldan boshlash uchun botni to‘xtatib, `data/alaziz_voting.db` faylini o‘chiring.

## Majburiy 2 ta kanalga obuna

`.env` ichiga quyidagilarni kiriting:

```env
REQUIRED_CHANNEL_1_ID=@alaziz_academy
REQUIRED_CHANNEL_1_NAME=Al-Aziz Academy
REQUIRED_CHANNEL_1_URL=https://t.me/alaziz_academy
REQUIRED_CHANNEL_2_ID=@abdulaziz_avazovichY
REQUIRED_CHANNEL_2_NAME=Abdulaziz Avazovich
REQUIRED_CHANNEL_2_URL=https://t.me/abdulaziz_avazovichY
```

Botni ikkala kanalga administrator qiling. Aks holda bot foydalanuvchining obunasini ishonchli tekshira olmaydi.

## Railway uchun tayyor sozlama

Bu ZIP Railway uchun tayyorlangan. Batafsil yo‘riqnoma: `RAILWAYGA_JOYLASH_UZ.md`.

Majburiy kanallar:

- https://t.me/alaziz_academy
- https://t.me/abdulaziz_avazovichY

Railway'da SQLite ma'lumotlari saqlanishi uchun Volume mount path: `/app/data`.
