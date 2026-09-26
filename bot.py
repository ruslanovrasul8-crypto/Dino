import os,csv,json,re
from pathlib import Path
from aiogram import Bot,Dispatcher,F
from aiogram.filters import Command
from aiogram.types import Message,InlineKeyboardMarkup,InlineKeyboardButton,CallbackQuery

TOKEN=os.environ["BOT_TOKEN"]
DATA=Path("data"); DATA.mkdir(exist_ok=True)
bot=Bot(TOKEN); dp=Dispatcher(); mode={}

def norm(x): return re.sub(r"[^a-z0-9_@+]","",str(x).lower()).lstrip("@")

def match(row,q):
    q=norm(q)
    return any(q in norm(row.get(k,"")) for k in
               ("username","user","login","phone","telephone","tel","id","telegram_id","tg_id"))

def search(q):
    out=[]
    for p in DATA.iterdir():
        if not p.is_file(): continue
        try:
            if p.suffix.lower()==".csv":
                with p.open(encoding="utf-8-sig",errors="ignore",newline="") as f:
                    for r in csv.DictReader(f):
                        if match(r,q): out.append(dict(r))
                        if len(out)>=20:return out
            elif p.suffix.lower()==".json":
                x=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
                rows=x if isinstance(x,list) else x.get("data",[])
                for r in rows:
                    if isinstance(r,dict) and match(r,q):out.append(r)
                    if len(out)>=20:return out
            elif p.suffix.lower() in (".txt",".log"):
                for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
                    if norm(q) in norm(line):out.append({"record":line[:1000]})
                    if len(out)>=20:return out
        except Exception: pass
    return out

def kb():
    return InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text="👤 Username",callback_data="username"),
       InlineKeyboardButton(text="📞 Номер",callback_data="phone")],
      [InlineKeyboardButton(text="🆔 Telegram ID",callback_data="id")],
      [InlineKeyboardButton(text="📋 Черновик жалобы",callback_data="report")]])

@dp.message(Command("start"))
async def start(m:Message): await m.answer("🔎 Выберите поиск:",reply_markup=kb())

@dp.callback_query(F.data.in_({"username","phone","id"}))
async def choose(c:CallbackQuery):
    mode[c.from_user.id]=c.data
    await c.message.answer("Введите значение для поиска:")
    await c.answer()

@dp.message(F.document)
async def upload(m:Message):
    name=Path(m.document.file_name or "database.txt").name
    if Path(name).suffix.lower() not in (".txt",".csv",".json",".log"):
        return await m.answer("Поддерживаются .txt, .csv, .json, .log")
    f=await bot.get_file(m.document.file_id)
    await bot.download_file(f.file_path,destination=DATA/name)
    await m.answer(f"✅ {name} добавлен.")

@dp.message()
async def find(m:Message):
    if m.from_user.id not in mode:return await m.answer("Нажмите /start.")
    rows=search(m.text.strip())
    if not rows:return await m.answer("🔍 Ничего не найдено.",reply_markup=kb())
    s=f"🔍 Найдено: {len(rows)}\n\n"
    for i,r in enumerate(rows,1):
        s+=f"#{i}\n"+"\n".join(f"{k}: {v}" for k,v in r.items() if v not in ("",None))[:700]+"\n\n"
    await m.answer(s[:3900],reply_markup=kb())

@dp.callback_query(F.data=="report")
async def report(c:CallbackQuery):
    await c.message.answer("📋 Можно сформировать черновик жалобы на основании найденных записей. Автоматическая массовая отправка жалоб не выполняется.")
    await c.answer()

async def main(): await dp.start_polling(bot)
if __name__=="__main__":
 import asyncio;asyncio.run(main())
