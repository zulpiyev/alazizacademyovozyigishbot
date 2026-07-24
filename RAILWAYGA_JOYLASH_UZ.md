# Al-Aziz Voting Bot — Railway'ga joylash

## Tayyor majburiy kanallar

1. `https://t.me/alaziz_academy`
2. `https://t.me/abdulaziz_avazovichY`

**Muhim:** botni ikkala kanalga ham administrator qiling. Aks holda foydalanuvchi obunasini tekshirish ishlamaydi.

## 1. GitHub'ga yuklash

Loyiha papkasida PowerShell oching:

```powershell
git init
git add .
git commit -m "Railway ready voting bot"
git branch -M main
git remote add origin SIZNING_GITHUB_REPO_URL
git push -u origin main
```

`.env` GitHub'ga yuborilmaydi. Tokenni faqat Railway Variables ichiga yozing.

## 2. Railway service yaratish

1. Railway'da **New Project** bosing.
2. **Deploy from GitHub repo** ni tanlang.
3. Bot repositorysini tanlang.
4. Railway `railway.json` orqali `bash start_railway.sh` buyrug‘ini avtomatik ishlatadi.

## 3. Railway Variables

Service ichidagi **Variables → RAW Editor** ga quyidagini kiriting:

```env
BOT_TOKEN=BOTFATHER_BERGAN_TOKEN
ADMIN_IDS=SIZNING_TELEGRAM_ID
TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO
SEED_DEMO_COMPETITION=false
SCHEDULER_INTERVAL_SECONDS=60

REQUIRED_CHANNEL_1_ID=@alaziz_academy
REQUIRED_CHANNEL_1_NAME=Al-Aziz Academy
REQUIRED_CHANNEL_1_URL=https://t.me/alaziz_academy
REQUIRED_CHANNEL_2_ID=@abdulaziz_avazovichY
REQUIRED_CHANNEL_2_NAME=Abdulaziz Avazovich
REQUIRED_CHANNEL_2_URL=https://t.me/abdulaziz_avazovichY
INSTAGRAM_NAME=Instagram — @alazizacademy
INSTAGRAM_URL=https://www.instagram.com/alazizacademy/
```

`BOT_TOKEN` va `ADMIN_IDS` ni o‘zingiznikiga almashtiring. `DATABASE_URL` yozish shart emas — start skript Volume yo‘lini avtomatik ishlatadi.

## 4. SQLite baza yo‘qolmasligi uchun Volume

1. Railway project canvasida bot service ustiga bosing.
2. **Add Volume** ni tanlang.
3. Mount path sifatida aynan quyidagini kiriting:

```text
/app/data
```

Volume qo‘shilmasa, qayta deploy bo‘lganda ovozlar yo‘qolishi mumkin.

## 5. Deploy

Variables va Volume qo‘shilgach **Deploy** yoki **Redeploy** bosing.

Logda quyidagilar chiqishi kerak:

```text
Al-Aziz Voting Bot Railway'da ishga tushmoqda...
Al-Aziz Voting Bot ishga tushdi
```

## Tekshirish

1. Telegram'da botga `/start` yuboring.
2. Ikki kanal tugmasi chiqishini tekshiring.
3. Ikkala kanalga obuna bo‘lib, `Obunani tekshirish` tugmasini bosing.
4. Admin hisobidan `/result` yuborib Excel fayl kelishini tekshiring.

## Muhim sozlamalar

- Railway'da bitta replica ishlating. Ikki replica long polling conflict beradi.
- Railway Start Command: `bash start_railway.sh`
- Railway Volume mount path: `/app/data`
- Botni ikkala majburiy kanalga administrator qiling.
- Tokenni GitHub yoki chatga yubormang.
