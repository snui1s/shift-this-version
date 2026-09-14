# 📖 คู่มือการใช้งาน CLI (`shift-this-version`)

คู่มือสรุปคำสั่งและตัวอย่างการใช้งานเครื่องมือ **`shift-this-version`** ผ่าน Terminal แบบละเอียด

---

## 📌 สารบัญ
1. [ตัวช่วยตั้งค่าครั้งแรก (First-Time Setup Wizard)](#1-ตัวช่วยตั้งค่าครั้งแรก-first-time-setup-wizard)
2. [คำสั่งที่ 1: ตรวจสอบสถานะ Repo (`inspect`)](#2-คำสั่ง-inspect)
3. [คำสั่งที่ 2: วิเคราะห์และ Shift เวอร์ชัน (`shift`)](#3-คำสั่ง-shift)
4. [ตัวเลือกการใช้งานระดับสูง (Advanced Options)](#4-ตัวเลือกการใช้งานระดับสูง)
5. [การนำไปใช้ใน CI/CD Pipeline](#5-การนำไปใช้ใน-cicd-pipeline)


---

## 1. ตัวช่วยตั้งค่าครั้งแรก (First-Time Setup Wizard)

ในการใช้งานครั้งแรก เพียงพิมพ์คำสั่งสั้นๆ คำสั่งเดียว ระบบจะแสดงหน้าต่างต้อนรับและช่วยคุณตั้งค่าทันที:

```bash
shift-this-version
```

### สิ่งที่ระบบจะทำ:
1. **ต้อนรับและแนะนำตัว**: อธิบายการทำงานเบื้องต้น
2. **เลือก AI Provider**: ให้คุณเลือก 1) Gemini, 2) OpenRouter, 3) OpenAI, หรือ 4) Ollama
3. **ให้ใส่ API Key**: ซ่อนการพิมพ์เพื่อความปลอดภัย พร้อมบอกลิงก์ไปกดขอ Key ฟรี
4. **บันทึกการตั้งค่า**: บันทึกเก็บไว้ที่ `~/.shift-this-version/config.json` ในเครื่องคุณอย่างปลอดภัย ไม่ต้องพิมพ์ซ้ำอีก
5. **สอนวิธีใช้งานเบื้องต้น (Quick Start Guide)**: สรุปคำสั่งที่จำเป็นให้ดูทันที

> 💡 **ต้องการเปลี่ยน Provider หรือ Key ในภายหลัง?**  
> สามารถพิมพ์ `shift-this-version config` ได้ทุกเมื่อเพื่อตั้งค่าใหม่  
> *(หรือจะใช้ Environment Variables เช่น `GEMINI_API_KEY` ก็ยังรองรับตามเดิมสำหรับระบบ CI/CD)*


---

## 2. คำสั่ง `inspect`

ใช้สำหรับสแกนดูสถานะ Git, ประวัติ Commit, Diff ล่าสุด และตรวจสอบว่าโปรเจกต์มีไฟล์หรือตัวแปรเวอร์ชันใดบ้างที่ระบบตรวจพบ:

```bash
shift-this-version inspect
```

### ตัวอย่างผลลัพธ์:
```text
┌───────────────────────────────── Git State ─────────────────────────────────┐
│ Latest Tag: v0.1.0                                                          │
│ Commits Ahead: 2                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
               Detected Version Targets (Files & Code Variables)               
┌──────────┬─────────────────────────┬──────┬─────────────────┬───────────────┐
│ Type     │ File Path               │ Line │ Current Version │ Snippet       │
├──────────┼─────────────────────────┼──────┼─────────────────┼───────────────┤
│ config   │ pyproject.toml          │    3 │ 0.1.0           │ version = …   │
│ code_var │ frontend/src/config.ts  │    8 │ 0.1.0           │ const VERSION…│
└──────────┴─────────────────────────┴──────┴─────────────────┴───────────────┘

Recent Commits:
  • feat: add Google OAuth login
  • fix: correct button padding

Filtered Diff Size: 1,420 characters
```

---

## 3. คำสั่ง `shift`

ใช้สำหรับส่ง Diff ให้ AI วิเคราะห์ และดำเนินการแก้ไขเลขเวอร์ชันตามประเภท (`major`, `minor`, `patch`)

### 3.1 ทดลองวิเคราะห์โดยไม่แก้ไฟล์จริง (`--dry-run`)
แนะนำให้รันคำสั่งนี้เพื่อตรวจสอบผลการวิเคราะห์ของ AI ก่อนเสมอ:
```bash
shift-this-version shift --dry-run
```

### 3.2 ใช้งานแบบ Interactive (ถามยืนยันก่อนแก้จริง)
```bash
shift-this-version shift
```

**ตัวอย่างขั้นตอนการทำงาน:**
1. AI อ่าน Diff และ Commit
2. แสดงการ์ดสรุปคำแนะนำ:
   ```text
   ╭───────────────────── AI Recommendation: MINOR ──────────────────────╮
   │ Current Version: 0.1.0                                              │
   │ Suggested Version: 0.2.0  (MINOR shift)                             │
   │ Confidence: 95.0%                                                   │
   │                                                                     │
   │ Reasoning:                                                          │
   │ Added OAuth login support without breaking existing endpoints.      │
   │                                                                     │
   │ Key Changes:                                                        │
   │   • Added Google OAuth login handler                                │
   ╰─────────────────────────────────────────────────────────────────────╯

   Files to update:
     📝 pyproject.toml:3 (0.1.0 ➔ 0.2.0)
     📝 frontend/src/config.ts:8 (0.1.0 ➔ 0.2.0)
   ```
3. ระบบจะถามยืนยัน:
   ```text
   Do you want to shift version to 0.2.0 across 2 targets? [Y/n]: y
   ```
4. ระบบทำการอัปเดตไฟล์, ทำ `git commit` และสร้าง `git tag`:
   ```text
     ✅ Updated pyproject.toml
     ✅ Updated frontend/src/config.ts
     📦 Git committed: 'chore(release): shift version to 0.2.0'
     🏷️ Created Git Tag: v0.2.0

   🎉 Successfully shifted version to 0.2.0!
   ```

---

## 4. ตัวเลือกการใช้งานระดับสูง

### เลือก Provider, กำหนด Model หรือ Host URL (แบ่งเป็น 4 กลุ่ม):

#### กลุ่มที่ 1: Direct Cloud Giants
```bash
# Google Gemini
shift-this-version shift -p gemini -m gemini-2.5-flash

# Anthropic Claude
shift-this-version shift -p anthropic -m claude-3-5-sonnet-20241022

# OpenAI
shift-this-version shift -p openai -m gpt-4o
```

#### กลุ่มที่ 2: High-Speed & Value Powerhouses
```bash
# DeepSeek (ฉลาดโค้ด ค่าโทเค็นถูกมาก)
shift-this-version shift -p deepseek -m deepseek-chat

# Groq (เร็วระดับแสง)
shift-this-version shift -p groq -m llama-3.3-70b-versatile
```

#### กลุ่มที่ 3: Universal Hub (OpenRouter รวม 200+ โมเดล)
```bash
# พิมพ์เลือกรุ่นโมเดลที่ต้องการได้อิสระจาก openrouter.ai
shift-this-version shift -p openrouter -m anthropic/claude-3.5-haiku
shift-this-version shift -p openrouter -m deepseek/deepseek-chat
```

#### กลุ่มที่ 4: Local & Self-Hosted (ฟรี & รันในเครื่อง 100%)
```bash
# Ollama: กำหนด Host URL และชื่อ Model ได้ตามต้องการ
shift-this-version shift -p ollama --host http://localhost:11434 -m llama3.2

# Custom OpenAI-Compatible (LM Studio, vLLM, LocalAI)
shift-this-version shift -p custom --host http://localhost:1234/v1 -m local-model
```

### ระบุชื่อตัวแปรในโค้ดเพิ่มเติม (`--var`):
หากโปรเจกต์ของคุณมีตัวแปรชื่อพิเศษที่ไม่ได้ใช้ชื่อมาตรฐาน (เช่น `RELEASE_VER` หรือ `APP_VERSION`):
```bash
shift-this-version shift --var RELEASE_VER --var APP_VERSION
```

### ไม่ต้องการให้ Git Tag หรือ Commit อัตโนมัติ:
```bash
# แค่แก้ไฟล์อย่างเดียว ไม่ต้องสร้าง tag และไม่ต้อง commit
shift-this-version shift --no-tag --no-commit
```

---

## 5. การนำไปใช้ใน CI/CD Pipeline

หากต้องการนำไปรันใน GitHub Actions หรือ GitLab CI โดยไม่ต้องมีคนมารอกด `Y`:

```bash
shift-this-version shift -p gemini --yes
```

### ตัวอย่าง GitHub Actions Workflow (`.github/workflows/release.yml`):
```yaml
name: AI Version Shift

on:
  push:
    branches:
      - main

jobs:
  shift-version:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # ดึง git tags ทั้งหมด

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install shift-this-version
        run: pip install shift-this-version

      - name: Run AI Shift
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          shift-this-version shift --yes -p gemini
          git push --tags
```
