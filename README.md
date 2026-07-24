# Al-Aziz Academy Voting Bot — SQLite

Al-Aziz Academy o‘quvchilari o‘rtasidagi ovoz berish tanlovini boshqaruvchi Telegram bot.

## Muhim o‘zgarish

Ushbu versiya **PostgreSQL ishlatmaydi**. Ma’lumotlar SQLite faylida saqlanadi:

```text
data/alaziz_voting.db
```

Baza va barcha jadvallar bot birinchi marta ishga tushganda avtomatik yaratiladi.

## Asosiy imkoniyatlar

- Fan → 1–6 / 7–11 → o‘quvchi tartibida filiallararo ovoz berish
- Har bir Telegram foydalanuvchisi har bir Fan + Sinf guruhida faqat bitta ovoz beradi
- SQLite unique constraint orqali takroriy ovozni bloklash
- O‘quvchilarni admin panel yoki Excel orqali qo‘shish
- Real vaqt statistikasi, foiz va reyting
- Tanlovni boshlash, pauza qilish, davom ettirish va yakunlash
- Excel import va ko‘p listli Excel hisobot
- Matn, rasm va video ommaviy xabarlar
- 3 kun, 1 kun, 1 soat qolganida avtomatik xabar
- Asia/Tashkent vaqt zonasi
- `IT-dasturlash` o‘quvchilari `IT` faniga birlashtirilgan
- Vaqt tugagach ovoz berish avtomatik yopiladi, statistika ochiq qoladi
- Admin `/result` orqali Fan + Sinf kesimida 1–2–3-o‘rinlar Excelini oladi

## Eng oson ishga tushirish

1. ZIP faylni oddiy papkaga chiqaring.
2. `START_BOT.bat` faylini ikki marta bosing.
3. Birinchi ishga tushishda `.env` fayli Notepad’da ochiladi.
4. Quyidagi ikkita qiymatni kiriting:

```env
BOT_TOKEN=BotFather_bergan_token
ADMIN_IDS=sizning_telegram_id
```

5. Faylni saqlang va Notepad’ni yoping.
6. Bot avtomatik ishga tushadi.

## Windows PowerShell orqali

```powershell
cd "C:\Users\User\Desktop\alaziz-voting-bot-sqlite"
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python bot.py
```

`alembic upgrade head` buyrug‘i shart emas.

## `.env` namunasi

```env
BOT_TOKEN=1234567890:BOTFATHER_TOKEN
DATABASE_URL=sqlite:///data/alaziz_voting.db
ADMIN_IDS=123456789
TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO
SEED_DEMO_COMPETITION=false
SCHEDULER_INTERVAL_SECONDS=60
```

## Keyingi safar ishga tushirish

`START_BOT.bat` faylini oching yoki PowerShell’da:

```powershell
cd "C:\Users\User\Desktop\alaziz-voting-bot-sqlite"
.\.venv\Scripts\Activate.ps1
python bot.py
```

## Birinchi sozlash

1. Telegram botga `/admin` yuboring.
2. `👥 O‘quvchilar` bo‘limidan o‘quvchi qo‘shing yoki Excel import qiling.
3. `🗳 Tanlovlar` → `➕ Tanlov yaratish` orqali tanlov yarating.
4. Boshlanish sanasini `DD.MM.YYYY HH:MM` ko‘rinishida kiriting.
5. Davomiylik uchun masalan `7` kiriting.
6. `▶️ Asosiy qilib boshlash` tugmasini bosing.


## `/result` yakuniy Excel

Admin Telegram’da `/result` yuborsa, bot quyidagi varaqlardan iborat Excel yuboradi:

- `1-2-3 orinlar` — barcha fan va sinf guruhlarining sovrinli o‘rinlari
- `1-6-sinflar` — faqat 1–6 guruh g‘oliblari
- `7-11-sinflar` — faqat 7–11 guruh g‘oliblari
- har bir fan uchun alohida varaq: `Ingliz tili`, `Rus tili`, `IT` va boshqalar

Fan varaqlarida shu fandagi **barcha faol o‘quvchilar**, filial, sinf guruhi,
ovozlar soni, guruh jami ovozi, foiz va o‘rin ko‘rsatiladi. 0 ovozli o‘quvchilar
ham ro‘yxatda qoladi, lekin ularga sovrinli o‘rin berilmaydi.

## Excel import

Namuna fayl:

```text
templates/students_import_template.xlsx
```

Ustunlar:

| Ism | Familiya | Filial | Fan | Sinf |
|---|---|---|---|---|
| Ali | Valiyev | Niyozbosh | Ingliz tili | 4 |

## Baza bilan ishlash

Bazani zaxiralash uchun botni to‘xtating va quyidagi faylni nusxalang:

```text
data/alaziz_voting.db
```

Bazani noldan boshlash uchun botni to‘xtatib, shu faylni o‘chiring. Keyingi ishga tushishda yangi baza avtomatik yaratiladi.

## Railway’ga joylash

Loyiha Railway uchun tayyor: `railway.json` va `start_railway.sh` mavjud.
Batafsil bosqichlar `RAILWAYGA_JOYLASH_UZ.md` faylida yozilgan.

Railway’da SQLite ovozlari saqlanishi uchun bot service’ga Volume ulang:

```text
/app/data
```

Railway Variables ichida kamida `BOT_TOKEN` va `ADMIN_IDS` bo‘lishi kerak.
Majburiy kanallar kodda tayyor qo‘yilgan:

- `@alaziz_academy`
- `@abdulaziz_avazovichY`

Volume ulanmasa, yangi deploydan keyin SQLite baza yo‘qolishi mumkin.

## Tekshirish

```powershell
python -m compileall app bot.py migrations
pytest -q
```

## Xavfsizlik

- `.env` faylini GitHub’ga yubormang.
- Bot tokenini hech kimga bermang.
- Admin huquqi faqat `ADMIN_IDS` ichidagi Telegram ID’larga beriladi.
- Botning faqat bitta nusxasini ishga tushiring.

## Dinamik o‘quvchilar soni

Bot har bir fan va sinf bo‘limida bazada nechta faol o‘quvchi bo‘lsa, aynan
shuncha o‘quvchini ko‘rsatadi. O‘quvchilar soni 10 taga majburlanmaydi.
Admin qo‘shgan yoki o‘chirgan o‘quvchilar bot qayta ishga tushganda saqlanadi.
Ovoz berilgach, popup chiqmaydi: “Ovoz qabul qilindi” yoki “Ovoz qabul
qilinmadi” xabari va barcha o‘quvchilarning ovoz/foiz natijalari chat ichida
ko‘rsatiladi.
