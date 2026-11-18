# OCR Text API

API บนเครื่อง (local HTTP) สำหรับอ่านข้อความภาษาไทยและอังกฤษที่เป็นตัวพิมพ์ จากไฟล์ PDF หรือรูปภาพ โดยใช้โมเดล [iapp/OpenThai2.1-OCR-Text-20261118](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118) ของ iApp Technology ซึ่งรันบน CPU ได้ทั้งหมด **เอกสารไม่ถูกส่งออกนอกเครื่อง** และไม่ได้เรียก API ที่ iApp โฮสต์ไว้

มีบริการคู่กันคือ [OCR Markdown API](../ocr-markdown-api/README.md) ที่พอร์ต 8090 สำหรับงานที่ต้องคงรูปแบบหน้า โดยเฉพาะตาราง

อัปเดตโมเดลวันที่ 18 พ.ย. 2569 — runtime **2.2.0**

## ขอบคุณผู้พัฒนาโมเดลต้นทาง (Acknowledgements)

ขอขอบคุณทีม **[iApp Technology](https://iapp.co.th/)** และ **[OpenThai](https://openthai.ai/)** สำหรับการพัฒนาและเผยแพร่ **OpenThai OCR Text** พร้อมน้ำหนักโมเดลและ runtime ให้ชุมชนนำไปใช้งานต่อ เป็นพื้นฐานสำคัญของความสามารถอ่านข้อความภาษาไทยและอังกฤษในโปรเจกต์นี้

ขอขอบคุณทีม **[PaddlePaddle / PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)** สำหรับโมเดลพื้นฐาน **PP-OCRv6-tiny** ซึ่ง iApp ใช้เป็นตัวตรวจจับบรรทัดข้อความและเป็นฐานในการปรับแต่งตัวรู้จำข้อความภาษาไทย ตามรายละเอียดใน [NOTICE ของโมเดลต้นทาง](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118/blob/7092cacf4561679ff9ed19de6821faeb9c96d894/NOTICE)

| ผู้พัฒนา / โครงการ | ผลงานที่โปรเจกต์นี้นำมาใช้ |
| --- | --- |
| iApp Technology / OpenThai | โมเดล OpenThai OCR Text และ runtime สำหรับอ่านข้อความไทย–อังกฤษ รวมถึง recognizer เสริมสำหรับฟอนต์ไทยไม่มีหัว |
| PaddlePaddle / PaddleOCR | `PP-OCRv6_tiny_det` สำหรับตรวจจับบรรทัด และ `PP-OCRv6_tiny_rec` ซึ่งเป็นฐานของ recognizer ที่ iApp นำมาปรับแต่ง |

โปรเจกต์ **OCR Text API** นำโมเดลและ runtime ของต้นทางมาเชื่อมต่อกับ FastAPI, หน้าเว็บ React และ Docker Compose เพื่อให้ติดตั้งและใช้งานได้สะดวกขึ้น เครดิตด้านการพัฒนาและฝึกโมเดลเป็นของผู้พัฒนาต้นทาง โดยโมเดลและ runtime ใช้ไลเซนส์ Apache-2.0 ดูรายละเอียดเพิ่มเติมใน [เอกสารอ้างอิง](#references) และ [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

---

## โมเดลปัจจุบัน: runtime 2.2.0

ชื่อ repository คือ `iapp/OpenThai2.1-OCR-Text-20261118` แต่รุ่น runtime ใน model card คือ **2.2.0** โปรเจกต์ล็อก commit `7092cacf4561679ff9ed19de6821faeb9c96d894` เพื่อไม่ให้ผลเปลี่ยนตาม `main` หรือ tag ที่อาจเลื่อนภายหลัง ดู [ต้นทางที่ commit นี้](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118/tree/7092cacf4561679ff9ed19de6821faeb9c96d894)

- ตรวจรุ่นที่รันด้วย `GET /health`: ฟิลด์ `model` และ `revision` ระบุโมเดล ส่วน `version` เป็นรุ่นของ API wrapper ไม่ใช่รุ่น OCR
- ใช้ detector และ recognizer เดิม ร่วมกับ `rec2.onnx` สำหรับฟอนต์ไทยไม่มีหัว พร้อม runtime ใหม่ที่ปรับวรรณยุกต์ ลำดับคอลัมน์ และตัวเลขในตาราง
- ฟีเจอร์ dewarping ของ 2.2.0 **ปิดอยู่ตามค่าเริ่มต้นของต้นทาง** ไม่ดาวน์โหลดโมเดลเสริม และยังไม่ได้เปิดเป็นตัวเลือกใน API นี้
- cache แยกตาม repository และ revision ใต้ `OCR_MODEL_DIR/snapshots/<source hash>/` พร้อม `.ocr-source.json` ระบุแหล่งที่มา โมเดลในโฟลเดอร์เดิมหรือ snapshot ที่ขาดไฟล์จะไม่ถูกใช้แทนรุ่นใหม่
- runtime แต่ละ snapshot ใช้ Python module namespace แยกกัน เพื่อไม่ใช้โค้ดรุ่นเก่าจาก import cache
- เมื่ออัปเกรดด้วย `docker compose up -d --build` ระบบจะดาวน์โหลด snapshot ใหม่ใน volume เดิม โดยเก็บโฟลเดอร์รุ่นเก่าไว้ ไม่ต้องใช้ `down -v`
- หากมี `.env` เก่า ให้ปรับ `OCR_MODEL_ID`, `OCR_MODEL_REVISION` และ `OCR_MODEL_DIR` ตาม `.env.example` ก่อนเปิดใหม่; Compose กำหนด cache root ภายใน container ให้อยู่ใน volume เสมอ
- `OCR_AUTO_DOWNLOAD=false` ใช้ได้เมื่อเตรียม snapshot และ source marker ของ revision นั้นครบแล้ว หากไม่ครบจะรายงาน error แทนการใช้ไฟล์เก่าหรือดาวน์โหลดเงียบ ๆ

ทดสอบอัปเกรดด้วยภาพและ PDF ตัวอย่าง พร้อมตรวจว่า runtime โหลด recognizer ตัวที่สองจริง ผลทดสอบตัวอย่างเป็น smoke test เพื่อยืนยันการเชื่อมต่อ ไม่ใช่ benchmark ความแม่นยำของเอกสารทุกประเภท

## หน้า GUI และ Docker Compose

หน้าเว็บ React + TypeScript รองรับการลากไฟล์ PDF/รูปภาพมาวาง ดูต้นฉบับคู่กับผล OCR เลือกช่วงหน้า แก้ข้อความรายหน้า คัดลอก และดาวน์โหลด `.txt` ภาษาไทย (UTF-8) โดยยังใช้ API เดิม

### เปิดใช้งานด้วย Docker (แนะนำ)

ติดตั้ง Docker พร้อม Compose v2 (เช่น Docker Desktop บน Mac/Windows หรือ Docker Engine + Compose plugin บน Linux) แล้วรันจากโฟลเดอร์โปรเจกต์:

```bash
docker compose up -d --build
```

เปิด **[http://localhost:8091](http://localhost:8091)** เพื่อใช้งาน GUI หรือ [http://localhost:8091/docs](http://localhost:8091/docs) เพื่อใช้ Swagger หน้าเว็บจะแสดงสถานะระหว่างโหลดโมเดล เมื่อขึ้น “พร้อมใช้งาน” จึงเริ่ม OCR ได้

Swagger ระบุโมเดลและ revision จากค่าที่เซิร์ฟเวอร์ใช้งาน พร้อมอธิบายค่าเริ่มต้น runtime 2.2.0 ขีดจำกัด เครดิตต้นทาง และรหัสข้อผิดพลาด เลข `0.1.0` ข้างชื่อ API เป็นเวอร์ชันของ API wrapper ไม่ใช่เวอร์ชันโมเดล OCR

- ไม่ต้องติดตั้ง Python หรือ Node บนเครื่องปลายทาง: Docker build หน้าเว็บและ API ให้ทั้งหมด
- ครั้งแรกต้องใช้อินเทอร์เน็ตเพื่อดึง base image, dependencies และโมเดลจาก Hugging Face ตาม revision ที่ล็อกไว้ เอกสารที่อัปโหลดไม่ได้ส่งไป Hugging Face
- โมเดลเก็บใน named volume `ocr-models` และใช้ซ้ำหลัง restart/rebuild ส่วนไฟล์และผล OCR ไม่บันทึกเป็นประวัติในแอป
- ใช้ CPU / ONNX Runtime และหนึ่ง worker ทั้งบน Linux และ Docker Desktop; ไม่ต้องมี GPU
- Healthcheck จะเป็น healthy เมื่อโมเดลพร้อมจริง การดาวน์โหลดครั้งแรกอาจใช้เวลาหลายนาที ดูความคืบหน้าจาก logs
- ค่าเริ่มต้นเปิดพอร์ตบน `127.0.0.1` เท่านั้น หากพอร์ต 8091 ถูกใช้งาน ให้เปลี่ยนพอร์ตตามตัวอย่างด้านล่าง

```bash
docker compose ps
docker compose logs -f ocr
docker compose down           # หยุด โดยเก็บโมเดลไว้
# เปลี่ยนพอร์ตเป็น 8092
OCR_PORT=8092 docker compose up -d
```

`docker compose down -v` จะลบ volume โมเดลด้วย จึงต้องดาวน์โหลดใหม่ครั้งถัดไป

### ตั้งค่าสำหรับเครื่องปลายทาง / เครือข่ายภายใน

สร้าง `.env` จาก `.env.example` หากยังไม่มี แล้วตั้งค่าที่ต้องการ เช่น:

```dotenv
OCR_BIND_IP=0.0.0.0
OCR_PORT=8091
OCR_THREADS=1
OCR_MAX_FILE_MB=50
OCR_MAX_PAGES=100
```

จากนั้นรัน `docker compose up -d --build` และเปิด `http://<IP-ของเซิร์ฟเวอร์>:8091` จากเครื่องในเครือข่าย หน้าเว็บเรียก API ผ่าน origin เดียวกันจึงไม่ต้องแก้ URL หรือ CORS ภายใน frontend

ระบบนี้ยังไม่มีระบบ login หากต้องเปิดผ่านอินเทอร์เน็ต ให้ติดตั้ง reverse proxy ที่มี HTTPS และระบบยืนยันตัวตนก่อนใช้งานจริง การคัดลอกข้อความผ่าน Clipboard API ต้องใช้ localhost หรือ HTTPS; หากเข้าผ่าน HTTP บน LAN ให้ดาวน์โหลด TXT หรือเลือกข้อความแล้วคัดลอกแทน

Compose อ่านค่าใน `.env` เพื่อส่งเฉพาะตัวเลือกที่รองรับเข้า container โดยกำหนด `OCR_MODEL_DIR` เป็น path ของ volume, `OCR_BACKEND=onnxruntime`, เปิด preload และฟัง `0.0.0.0:8091` ภายใน container เสมอ ส่วน `OCR_BIND_IP` / `OCR_PORT` ควบคุมพอร์ตฝั่ง host จึงแยกจาก `OCR_HOST` ของสคริปต์ local

หากต้องการใช้โมเดลที่มีอยู่แล้วโดยไม่ดาวน์โหลดตอนเริ่ม container:

```bash
docker compose create
docker compose cp models/OpenThai2.1-OCR-Text-20261118 ocr:/app/models/
docker compose run --rm --no-deps --user root ocr chown -R 10001:10001 /app/models
OCR_AUTO_DOWNLOAD=false docker compose up -d
```

เตรียมโฟลเดอร์นี้ด้วย `OCR_AUTO_DOWNLOAD=true scripts/install.sh` ก่อนคัดลอก ต้องคัดลอกทั้ง `snapshots/` และไฟล์ `.ocr-source.json` ภายใน snapshot ให้ครบและตรง repository/revision ที่ตั้งไว้ การนำไฟล์จาก `hf download` มาวางรวมแบบเดิมจะไม่ผ่านการตรวจ cache การ build image บนเครื่องใหม่ยังต้องเข้าถึง registry ของ dependencies หรือใช้ image ที่ build แล้วโดย `docker save` / `docker load`

### พัฒนา GUI บนเครื่อง

เปิด API ด้วย `scripts/run.sh` แล้วเปิดอีก terminal:

```bash
cd frontend
npm ci
npm run dev
```

เปิด URL ที่ Vite แสดง (ปกติ `http://127.0.0.1:5173`) โดย Vite proxy ไป API พอร์ต 8091 สำหรับ production ใช้ `npm run build` ใน `frontend` แล้ว restart API เพื่อให้ FastAPI เสิร์ฟ `frontend/dist` จาก `/` ได้โดยตรง

### ผลการตรวจสอบ GUI / Docker

ทดสอบบน Docker Desktop / Linux ARM64: build image สำเร็จ, container เป็น healthy, หน้าเว็บและ OpenAPI เปิดได้, อ่าน PDF ตัวอย่างด้วยโมเดลจริงสำเร็จ และทดสอบผ่านเบราว์เซอร์ทั้งอัปโหลด แก้ข้อความ และดาวน์โหลด TXT โดยชุดทดสอบ API/static routes และ model cache มี 24 รายการ

`npm audit --omit=dev` ไม่พบช่องโหว่ใน dependencies ฝั่งใช้งาน ส่วน `npm audit` รวมเครื่องมือ build ยังรายงานช่องโหว่ ReDoS จาก `picomatch` ผ่าน Vite (5 รายการรวมแพ็กเกจที่ได้รับผลกระทบ ณ วันที่พัฒนา) และ registry ที่ตรวจยังไม่มี picomatch รุ่นแก้ไข อย่าเปิด Vite development server ให้บุคคลภายนอกเข้าถึง; image ที่ใช้งานจริงมีเฉพาะ static bundle และ Python ไม่มี Node หรือ Vite server

### การใช้หน้าจอ

1. เลือกไฟล์หนึ่งไฟล์ หรือวางไฟล์ในช่องอัปโหลด
2. ระบุหน้าเริ่มต้นและจำนวนหน้า (เว้นจำนวนหน้าเพื่ออ่านถึงขีดจำกัดของเซิร์ฟเวอร์)
3. กด **เริ่มอ่านข้อความ** แล้วรอผล ไม่มีเปอร์เซ็นต์รายหน้า เพราะ API ตอบเมื่อประมวลผลเสร็จ
4. เลือกแต่ละหน้าในฝั่งผลลัพธ์เพื่อแก้ไข ข้อความรวมและ TXT จะใช้ข้อความที่แก้แล้ว
5. คัดลอกหรือดาวน์โหลดข้อความของหน้าที่เลือก หรือเลือก “ทุกหน้าที่อ่าน” เพื่อส่งออกทั้งหมด

การเปลี่ยนไฟล์ อ่านใหม่ กดล้าง หรือรีเฟรชหน้าเว็บจะล้างผลลัพธ์และข้อความที่แก้ไข เบราว์เซอร์อาจไม่รองรับตัวอย่าง TIFF แต่ยังส่งเข้า OCR ได้ ปุ่มยกเลิกจะหยุดรอผลและตัดการเชื่อมต่อ; เซิร์ฟเวอร์ตรวจการตัดการเชื่อมต่อหลังประมวลผลแต่ละหน้า

---

## ความสามารถของระบบ

- อ่านไฟล์ PDF และรูปภาพ (JPEG, PNG, WebP, TIFF หลายหน้า, BMP) ผ่าน HTTP บนเครื่องนี้ ใช้ CPU อย่างเดียว ไม่ต้องมี GPU
- คืนค่าเป็นข้อความล้วนตามลำดับการอ่าน พร้อมกรอบตำแหน่งและค่าความมั่นใจของทุกบรรทัด
- เลือกช่วงหน้าได้ด้วย `start_page` และ `max_pages` ส่งกรอบระดับคำได้ด้วย `include_words` และบรรทัดที่ถูกกรองทิ้งด้วย `include_dropped`
- จัดการหน้ากลับหัวหรือตะแคง หน้าเอียง หน้า 2–3 คอลัมน์ และตัวอักษรสีอ่อนบนพื้นเข้มได้ (ตามความสามารถของ runtime ของ iApp)
- มีหน้าตรวจสถานะ (`/health`), ข้อมูลระบบ (`/v1/info`) และเอกสารลองเรียกใช้แบบ Swagger ที่ `/docs`
- โมเดลเล็กประมาณ 6.6 MB เก็บในโฟลเดอร์โปรเจกต์ที่ `models/` (ไม่อยู่ใน git) โหลดครั้งแรกประมาณ 18 วินาที หลังจากนั้นอ่านหน้าได้เร็วกว่าหนึ่งวินาที
- รับคำขอจากเบราว์เซอร์บน `localhost` เท่านั้น (CORS) และฟังที่ `127.0.0.1` เป็นค่าเริ่มต้น
- ประมวลผลทีละหน้าในหนึ่งโปรเซส คำขอที่เข้าพร้อมกันจะเข้าคิว

## ต่างจาก ocr-markdown-api อย่างไร

| | **ocr-text-api** (โปรเจกต์นี้) | **ocr-markdown-api** |
| --- | --- | --- |
| พอร์ต | `8091` | `8090` |
| โมเดล | OpenThai2.1-OCR-Text-20261118 / runtime 2.2.0 (ประมาณ 6.6 MB) | OpenThai2.0-OCR-Markdown (ประมาณ 2.5 GB) |
| ผลลัพธ์ | ข้อความล้วนตามลำดับการอ่าน พร้อมกรอบและค่าความมั่นใจของทุกบรรทัด | Markdown ที่มีตารางเป็น HTML คงเซลล์รวมไว้ |
| ความเร็วบนเครื่องนี้ | ไม่ถึงหนึ่งวินาทีต่อหน้า ใช้ CPU อย่างเดียว | ประมาณ 50–70 วินาทีต่อหน้า ใช้ GPU ของชิป Apple |
| เหมาะกับ | ค้นหาข้อความ ดึงข้อความจากสแกน ส่งต่อให้แชตบอต หรืออ่านเอกสารจำนวนมาก | งานที่ต้องคงรูปแบบหน้า โดยเฉพาะตาราง |

สรุปคือ ตัวนี้เป็นตัวอ่านข้อความที่เร็วบน CPU ถ้าต้องการตารางหรือ Markdown ให้เรียก `ocr-markdown-api` ที่พอร์ต 8090 แทน รูปแบบการเรียกเหมือนกัน (`POST /v1/ocr` แบบ multipart ฟิลด์ `file`, `start_page`, `max_pages`) จึงสลับกันได้ง่าย

## สรุปสั้น ๆ

| | |
|---|---|
| โฟลเดอร์ | `/Users/ninetea/Projects/nhso/ocr-text-api` |
| ที่อยู่ API | `http://127.0.0.1:8091` |
| เอกสาร API (Swagger) | `http://127.0.0.1:8091/docs` |
| ไฟล์ที่รับ | PDF, JPEG, PNG, WebP, TIFF (หลายหน้าได้), BMP |
| ขีดจำกัดเริ่มต้น | ไฟล์ไม่เกิน 50 MB, ไม่เกิน 100 หน้าต่อคำขอ |
| โมเดล | `iapp/OpenThai2.1-OCR-Text-20261118` รุ่น `7092cacf4561679ff9ed19de6821faeb9c96d894` (ล็อกรุ่นไว้) ประมาณ 6.6 MB ใต้ `models/OpenThai2.1-OCR-Text-20261118/snapshots/` |
| ความเร็ว | ดูผลทดสอบรุ่นปัจจุบันและข้อจำกัดด้านล่าง; ผลวันที่ 12 พ.ย. เป็นรุ่นเดิม 2.0 |

## ติดตั้ง (ครั้งแรก)

```bash
cd /Users/ninetea/Projects/nhso/ocr-text-api
scripts/install.sh
```

สคริปต์จะ

1. สร้าง `.venv` ของโปรเจกต์นี้เอง (ใช้ `uv` และ Python 3.13 ถ้ามี) โดยไม่ยุ่งกับ venv ของ ocr-markdown-api และไม่ใช้ Python 3.15 ของระบบ
2. ติดตั้ง `onnxruntime opencv-python-headless pyclipper numpy pillow pypdfium2 huggingface_hub` ตาม [คู่มือทางการของ iApp](https://iapp.co.th/blog/openthai2p0-ocr-how-to-run) พร้อม FastAPI และ Uvicorn
3. ดาวน์โหลดโมเดลประมาณ 6.6 MB ไปไว้ใต้ `models/OpenThai2.1-OCR-Text-20261118/snapshots/` โดยข้าม `pytorch/rec_weights.pt` ที่ใช้สำหรับเทรนต่อเท่านั้น

เวอร์ชันที่ติดตั้งจริงบนเครื่องนี้บันทึกไว้ใน `requirements.lock.txt` ถ้าไม่ได้รันสคริปต์นี้ เซิร์ฟเวอร์จะโหลดโมเดลให้เองตอนเริ่มทำงาน (`OCR_AUTO_DOWNLOAD=true`)

## เปิดและปิดเซิร์ฟเวอร์

### เปิดแบบเห็นในเทอร์มินัล

```bash
cd /Users/ninetea/Projects/nhso/ocr-text-api
scripts/run.sh
```

เซิร์ฟเวอร์เปิดที่ `http://127.0.0.1:8091` แล้วโหลดโมเดลในเบื้องหลัง ประมาณ 18 วินาทีในครั้งแรก ระหว่างนี้ `GET /health` จะตอบ `"model_state": "loading"` เมื่อพร้อมแล้วจะเป็น `"ready"`

หยุดด้วยการกด `Ctrl+C` ในเทอร์มินัลนั้น

### เปิดไว้เบื้องหลัง (ปิดหน้าต่างเทอร์มินัลได้)

```bash
cd /Users/ninetea/Projects/nhso/ocr-text-api
mkdir -p logs
nohup scripts/run.sh > logs/server.log 2>&1 &
```

บันทึกการทำงานอยู่ที่ `logs/server.log`

### ตรวจสถานะ

```bash
# โมเดลพร้อมเมื่อมี "ready" ในผลลัพธ์
curl http://127.0.0.1:8091/health

# มีโปรเซสฟังพอร์ต 8091 อยู่หรือไม่
lsof -nP -iTCP:8091 -sTCP:LISTEN
```

รอจนพร้อมแล้วค่อยส่งไฟล์

```bash
until curl -sf http://127.0.0.1:8091/health | grep -q '"ready"'; do sleep 2; done
echo ready
```

ลองเรียกใช้แบบมีหน้าจอได้ที่ [http://127.0.0.1:8091/docs](http://127.0.0.1:8091/docs)

### ปิดเซิร์ฟเวอร์

- ถ้าเปิดแบบเห็นในเทอร์มินัล: กด `Ctrl+C`
- ถ้าเปิดไว้เบื้องหลัง หรือไม่แน่ใจว่าเปิดจากหน้าต่างไหน:

```bash
kill $(lsof -ti tcp:8091)
```

ตรวจว่าปิดแล้วด้วย `curl http://127.0.0.1:8091/health` ซึ่งจะเชื่อมต่อไม่ได้ คำสั่งนี้ปิดเฉพาะพอร์ต 8091 ไม่กระทบ OCR Markdown API ที่พอร์ต 8090

## คู่มือการใช้งาน

1. เปิดเซิร์ฟเวอร์ตามด้านบน และรอจน `/health` เป็น `ready`
2. ส่งไฟล์เข้า `POST /v1/ocr` ด้วยวิธีใดวิธีหนึ่งด้านล่าง
3. ผลอยู่ในฟิลด์ `text` (ทุกหน้าต่อกัน คั่นด้วยบรรทัดว่าง) และ `pages[]` (ข้อความ กรอบ และค่าความมั่นใจรายบรรทัด)

### ลองจากเบราว์เซอร์

เปิด [http://127.0.0.1:8091/docs](http://127.0.0.1:8091/docs) เลือก `POST /v1/ocr` กด Try it out อัปโหลดไฟล์ แล้วกด Execute

### curl

```bash
# สถานะ
curl http://127.0.0.1:8091/health

# อ่านรูปหรือ PDF แล้วรับ JSON ทั้งหมด
curl -F "file=@document.pdf" http://127.0.0.1:8091/v1/ocr

# เฉพาะหน้า 2 ถึง 4 แล้วพิมพ์เฉพาะข้อความ
curl -s -F "file=@document.pdf" -F start_page=2 -F max_pages=3 http://127.0.0.1:8091/v1/ocr \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["text"])'
```

หรือใช้สคริปต์ตัวอย่าง

```bash
scripts/make_sample.py     # สร้าง samples/thai_letter.png และ .pdf
examples/curl.sh samples/thai_letter.png
.venv/bin/python examples/client.py samples/thai_letter.pdf
```

### Python

ดูฉบับเต็มที่ `examples/client.py`

```python
# เรียกด้วย: .venv/bin/python examples/client.py document.pdf
```

## API

| Method | Path | ใช้ทำอะไร |
| --- | --- | --- |
| GET | `/health` | สถานะเซิร์ฟเวอร์ โหลดโมเดลแล้วหรือยัง, `device` (cpu), `backend` (onnxruntime หรือ openvino), รุ่นโมเดล |
| GET | `/v1/info` | ข้อมูลข้างต้น พร้อมชนิดไฟล์ที่รับ ขีดจำกัด และลิงก์ไป API Markdown |
| POST | `/v1/ocr` | อ่านไฟล์ (multipart) |

ฟิลด์ของ `POST /v1/ocr`

- `file` (จำเป็น): PDF, JPEG, PNG, WebP, TIFF (หลายหน้าได้) หรือ BMP
- `start_page` หน้าแรกที่จะอ่าน เริ่มนับจาก 1 (ค่าเริ่มต้น 1)
- `max_pages` จำนวนหน้าที่จะอ่าน (ไม่เกิน `OCR_MAX_PAGES`)
- `include_words=true` ส่งกรอบระดับคำของแต่ละบรรทัดมาด้วย
- `include_dropped=true` ส่งบรรทัดที่ runtime กรองทิ้งมาด้วย (เช่นค่าความมั่นใจต่ำ)

ผลลัพธ์

```json
{
  "model": "iapp/OpenThai2.1-OCR-Text-20261118",
  "revision": "7092cacf4561679ff9ed19de6821faeb9c96d894",
  "backend": "onnxruntime",
  "filename": "document.pdf",
  "file_type": "pdf",
  "total_pages": 3,
  "page_count": 1,
  "pages": [
    {
      "page": 1, "width": 1654, "height": 2339,
      "text": "บันทึกข้อความ\n...",
      "lines": [{"text": "บันทึกข้อความ", "confidence": 0.99, "row": 0,
                 "box": [[120, 80], [480, 80], [480, 130], [120, 130]], "words": null, "reason": null}],
      "dropped": null,
      "rotation": 0,
      "text_angle": 0.0,
      "error": null,
      "elapsed_ms": 400
    }
  ],
  "text": "ข้อความของทุกหน้า คั่นด้วยบรรทัดว่าง",
  "elapsed_ms": 420
}
```

- `box` คือมุมทั้งสี่ `[x, y]` เป็นพิกเซลของภาพหน้านั้น (PDF ถูกวาดเป็นภาพที่ 200 dpi)
- `rotation` คือการหมุนที่ runtime ทำให้ (0, 90, 180, 270) และ `text_angle` คือมุมเอียงของข้อความเป็นองศา
- ถ้าหน้าใดอ่านไม่ได้ จะมีข้อความใน `error` ของหน้านั้น แล้วอ่านหน้าถัดไปต่อ
- รหัสผิดพลาด: 413 ไฟล์ใหญ่เกิน, 415 ชนิดไฟล์ไม่รองรับ, 400 `start_page` เกินจำนวนหน้า, 503 โมเดลยังใช้ไม่ได้

## ตั้งค่า

คัดลอก `.env.example` เป็น `.env` แล้วแก้ค่าที่ต้องการ (ไม่มีค่าลับ) หรือส่งตัวแปร `OCR_*` ตอนเปิดเซิร์ฟเวอร์

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
| --- | --- | --- |
| `OCR_HOST` | `127.0.0.1` | รับเฉพาะในเครื่อง ถ้าจะให้เครื่องอื่นในวงแลนเรียก ให้ตั้งเป็น `0.0.0.0` (API ไม่มีระบบล็อกอิน ควรใช้ในเครือข่ายที่ไว้ใจได้เท่านั้น) |
| `OCR_PORT` | `8091` | พอร์ต |
| `OCR_MODEL_ID` | `iapp/OpenThai2.1-OCR-Text-20261118` | |
| `OCR_MODEL_REVISION` | `7092cacf…` | ล็อกรุ่นของโมเดลไว้ |
| `OCR_MODEL_DIR` | `models/OpenThai2.1-OCR-Text-20261118` | ราก cache; ไฟล์อยู่ใต้ `snapshots/<source hash>/` (ไม่อยู่ใน git) |
| `OCR_AUTO_DOWNLOAD` | `true` | โหลดโมเดลให้เองถ้ายังไม่มี |
| `OCR_BACKEND` | `auto` | `auto`, `onnxruntime` หรือ `openvino` |
| `OCR_THREADS` | `1` | เธรดต่อการอ่านหนึ่งครั้ง |
| `OCR_PRELOAD` | `true` | โหลดโมเดลตั้งแต่เปิดเซิร์ฟเวอร์ |
| `OCR_MAX_FILE_MB` | `50` | ขนาดไฟล์สูงสุด |
| `OCR_MAX_PAGES` | `100` | จำนวนหน้าสูงสุดต่อคำขอ |
| `OCR_PDF_DPI` | `200` | ความละเอียดตอนวาดหน้า PDF ตามคู่มือทางการ |

**เรื่อง backend:** runtime ของ iApp เลือก OpenVINO ถ้าติดตั้งไว้ ไม่อย่างนั้นใช้ ONNX Runtime คู่มือทางการสำหรับ Mac ใช้ `onnxruntime` โปรเจกต์นี้จึงติดตั้งแค่ตัวนั้น ความเร็ว bf16 ที่ประกาศไว้ต้องใช้ CPU Intel ที่มี AMX ซึ่ง Mac ไม่มี จึงไม่ได้ประโยชน์จาก OpenVINO

**เรื่องความเร็วและการรองรับงานพร้อมกัน:** หนึ่งโปรเซสอ่านทีละหน้า คำขอที่เข้ามาพร้อมกันจะรอคิว ใช้หน่วยความจำประมาณ 450 MB ต่อโปรเซส สำหรับใช้ในเครื่องหนึ่งโปรเซสก็เพียงพอ ถ้าต้องอ่านจำนวนมาก iApp แนะนำให้รันหนึ่งโปรเซสต่อหนึ่งคอร์ด้วย `OCR_THREADS=1` เช่นเปิดหลายพอร์ต (8091, 8092, …) แล้วกระจายไฟล์ เพราะในโปรเซสเดียวเพิ่มเธรดเกินประมาณ 2 แล้วไม่เร็วขึ้น (ติด GIL ของ Python) ถ้าใช้โปรเซสเดียวจะตั้ง `OCR_THREADS=2` แบบสคริปต์ในคู่มือก็ได้

## หมายเหตุจากการทดสอบจริงของรุ่นเดิม 2.0 (12 พ.ย. 2569)

ผลทดสอบบน MacBook Air M1 นี้ (ONNX Runtime, `OCR_THREADS=1`): ครั้งแรกโหลดโมเดลประมาณ 18 วินาที อ่านหน้า A4 เต็มหน้า (1654×2339 พิกเซล) ประมาณ 0.46 วินาทีต่อหน้า และหน้าครึ่ง A4 ประมาณ 0.45–0.55 วินาทีต่อหน้า

`scripts/make_sample.py` วาดภาพด้วย Pillow ซึ่งบน Mac ไม่มี libraqm จึงวาดวรรณยุกต์ที่ซ้อนบนสระบนหาย (เช่น «เพื่อ» กลายเป็น «เพือ» ตั้งแต่ในภาพ) ผลอ่านที่ขาดวรรณยุกต์ตรงนั้นจึงมาจากภาพตัวอย่าง ไม่ใช่จากโมเดล ควรทดสอบความแม่นด้วยเอกสารจริงหรือ PDF ที่สร้างจากโปรแกรมเอกสาร

## ข้อจำกัดของโมเดล

- อ่านได้ดีเฉพาะตัวพิมพ์ ลายมือและข้อความในภาพถ่ายฉากทั่วไปอ่านได้ไม่ดี (คะแนนลายมือ 10.3) ถ้าเป็นลายมือให้ใช้ ocr-markdown-api
- ไม่สร้างตารางหรือ Markdown ตารางจะออกมาเป็นข้อความเรียงตามแถว
- ฟอนต์ตกแต่งมาก ๆ อาจอ่านผิด ตราประทับจะถูกอ่านออกมาเป็นข้อความด้วย
- runtime จัดการหน้ากลับหัวหรือตะแคง หน้าเอียง หน้า 2–3 คอลัมน์ และตัวอักษรสีอ่อนบนพื้นเข้มได้
- ผล benchmark ที่ iApp รายงานสำหรับสาย 2.1: เฉลี่ย 88.3 จากชุดเอกสารพิมพ์ 12 ชุด (เดิม 87.8); 2.2.0 ใช้ผลลัพธ์เหมือน 2.1.4 เมื่อไม่เปิด dewarping ดู [model card ที่ล็อก commit](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118/blob/7092cacf4561679ff9ed19de6821faeb9c96d894/README.md)

## แก้ปัญหาเบื้องต้น

| อาการ | สิ่งที่ควรทำ |
|---|---|
| เชื่อมต่อไม่ได้ / เหมือนเซิร์ฟเวอร์ลง | เปิดด้วย `scripts/run.sh` แล้วตรวจด้วย `curl http://127.0.0.1:8091/health` |
| `/health` ตอบ `"loading"` นาน | รอประมาณ 20 วินาทีตอนเปิดครั้งแรก ถ้ายังไม่เป็น `ready` ให้ดู `logs/server.log` |
| ได้รหัส `503` หรือ `"model_state": "error"` | ดูฟิลด์ `model_error` ใน `/health` และบันทึกในล็อก ถ้าโมเดลยังไม่มีให้รัน `scripts/install.sh` |
| แจ้งว่าพอร์ตถูกใช้แล้ว | มีเซิร์ฟเวอร์เปิดอยู่แล้ว ใช้ได้เลย หรือปิดด้วย `kill $(lsof -ti tcp:8091)` แล้วเปิดใหม่ |
| ผลจากไฟล์ตัวอย่างขาดวรรณยุกต์ | เป็นข้อจำกัดของการวาดภาพตัวอย่าง ไม่ใช่โมเดล ให้ลองกับเอกสารจริง |
| ต้องการตารางหรือ Markdown | เรียก [ocr-markdown-api](../ocr-markdown-api/README.md) ที่พอร์ต 8090 แทน |

## ทดสอบ

```bash
cd /Users/ninetea/Projects/nhso/ocr-text-api
.venv/bin/python -m pytest -q
```

ชุดทดสอบใช้ engine จำลอง จึงรันได้แม้ยังไม่มีโมเดล ครอบคลุมการตรวจชนิดไฟล์ ขนาดไฟล์ การแยกหน้า PDF ช่วงหน้า หน้าที่อ่านพลาดแล้วอ่านต่อ และ CORS

## โครงสร้างโปรเจกต์

```
app/        main.py (FastAPI), config.py, schemas.py, engine.py (เรียก LineOCR ของ iApp), pages.py (แยกหน้า PDF ด้วย pypdfium2)
scripts/    install.sh, run.sh, make_sample.py
examples/   curl.sh, client.py
tests/      test_api.py
models/     โมเดลที่ดาวน์โหลดมา (ไม่อยู่ใน git)
samples/    หน้าเอกสารตัวอย่างที่สร้างขึ้นเอง ไม่มีข้อมูลส่วนบุคคล
```

## ไลเซนส์

- โค้ดของ API นี้ใช้ MIT ดูไฟล์ `LICENSE`
- โมเดลและ runtime เป็นผลงานของ iApp Technology ภายใต้ Apache-2.0 ส่วนตัวตรวจจับบรรทัดคือ PP-OCRv6-tiny ของ PaddlePaddle ภายใต้ Apache-2.0 เช่นกัน โปรเจกต์นี้ไม่ได้สร้างหรือเทรนโมเดล และไม่ได้แก้ runtime ของ iApp รายละเอียดและ NOTICE อยู่ใน `THIRD_PARTY_NOTICES.md`

## References

1. **iApp Technology — OpenThai OCR Text: model card และไฟล์โมเดลที่ใช้งานจริง** — [revision `7092cacf4561679ff9ed19de6821faeb9c96d894` (runtime 2.2.0)](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118/tree/7092cacf4561679ff9ed19de6821faeb9c96d894) ระบุสถาปัตยกรรม วิธีใช้งาน ผลประเมิน และข้อจำกัดของโมเดล
2. **iApp Technology — ประกาศ OpenThai 2.1 OCR** — [รายละเอียดการปรับปรุงจากผู้พัฒนา](https://iapp.co.th/blog/openthai2p1-ocr-release) เป็นประกาศของสายรุ่น 2.1; รุ่น runtime ที่โปรเจกต์นี้ล็อกไว้ให้อ้างอิง model card ในข้อ 1
3. **PaddlePaddle — PP-OCRv6_tiny_det** — [โมเดลพื้นฐานสำหรับตรวจจับบรรทัดข้อความ](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_det)
4. **PaddlePaddle — PP-OCRv6_tiny_rec** — [โมเดลพื้นฐานของตัวรู้จำข้อความที่ iApp นำมาปรับแต่ง](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_rec)
5. **PaddlePaddle / PaddleOCR** — [repository ทางการ](https://github.com/PaddlePaddle/PaddleOCR) สำหรับโครงการและเอกสารของโมเดลพื้นฐาน
6. **iApp Technology — NOTICE ของโมเดล** — [เครดิตและไลเซนส์ ณ revision ที่ใช้งาน](https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118/blob/7092cacf4561679ff9ed19de6821faeb9c96d894/NOTICE) และ [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) สำหรับรายละเอียดการนำมาใช้ในโปรเจกต์นี้
