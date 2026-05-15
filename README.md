# VerifyNG

AI-powered academic certificate verification for Nigerian employers,
institutions, and recruiters.

VerifyNG helps users verify academic certificates in under a minute. A user
uploads a document, pays through Squad, and receives an explainable AI trust
score with a verdict and risk flags.

Built for **Squad Hackathon 3.0** by Team Finsense.

## Live Links

- Frontend: [verifyng-three.vercel.app](https://verifyng-three.vercel.app)
- Backend API: [olatunjitobi-verifyng-api.hf.space](https://olatunjitobi-verifyng-api.hf.space)
- Health check: [API /health](https://olatunjitobi-verifyng-api.hf.space/health)

## Problem

Certificate fraud affects hiring, admissions, and government employment across
Nigeria. Manual verification is slow, expensive, and difficult to scale.
VerifyNG gives organizations a faster first-pass screening tool by combining
document analysis, payment-gated verification, and interpretable AI scoring.

## Core Flow

1. A user uploads a certificate on the frontend.
2. Squad payment is initiated for the verification fee.
3. After payment confirmation, the webhook triggers the AI pipeline.
4. The backend downloads the uploaded file and analyzes it.
5. The result endpoint returns status, trust score, verdict, confidence, and
   flags.
6. The frontend polls the result endpoint and displays the outcome.

## Squad Integration

Squad is not decorative in this project. It gates the verification workflow:

- No confirmed payment means no AI verification run.
- The payment/webhook flow updates verification status in Supabase.
- The AI pipeline runs only after the verification is marked ready for
  processing.

## AI Verification Engine

VerifyNG uses a four-signal AI pipeline:

1. **Visual Forensics**
   - Error Level Analysis for image tampering signals.
   - Metadata and visual consistency checks.

2. **OCR + Content Validation**
   - Tesseract extracts certificate text.
   - Extracted text is checked for institution keywords, candidate patterns,
     certificate language, and valid year signals.

3. **Template/Layout Matching**
   - WAEC/WASSCE-specific structure checks.
   - Scores institution identity, candidate name, examination number, year, and
     grade-table evidence.

4. **Custom ML Classifier**
   - Lightweight NumPy classifier trained on certificate signal rows.
   - Uses visual score, OCR confidence, template score, metadata suspicion,
     ELA anomaly score, and content score.

See [AI_TECHNICAL_DEPTH.md](AI_TECHNICAL_DEPTH.md) for the detailed AI layer,
explainability output, and benchmark evidence.

## Result Contract

### `GET /api/result/{verification_id}`

While processing:

```json
{
  "verification_id": "uuid",
  "status": "PROCESSING",
  "message": "AI is analyzing your certificate..."
}
```

When complete:

```json
{
  "verification_id": "uuid",
  "status": "COMPLETE",
  "trust_score": 87,
  "verdict": "LIKELY AUTHENTIC",
  "flags": [],
  "confidence": "HIGH",
  "layers_run": ["visual_forensics", "content_validation"],
  "report_url": null
}
```

When failed:

```json
{
  "verification_id": "uuid",
  "status": "FAILED",
  "message": "Verification failed. Please contact support.",
  "refund_eligible": true
}
```

### `POST /api/trigger/{verification_id}`

Manual testing endpoint. Requires:

```http
X-API-Key: <API_KEY>
```

This bypasses payment only for integration testing. Divine's production webhook
calls `trigger_ai_pipeline(verification_id)` after payment confirmation.

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Axios
- React Dropzone
- React PDF

### Backend

- FastAPI
- Supabase
- HuggingFace Spaces
- Tesseract OCR
- OpenCV
- Pillow
- NumPy

## Repository Structure

```text
verifyng-backend/
+-- backend/
|   +-- app/
|   |   +-- main.py
|   |   +-- result.py
|   |   +-- pipeline.py
|   |   +-- ocr.py
|   |   +-- ela.py
|   |   +-- content_validator.py
|   |   +-- ai_depth.py
|   |   +-- ml_model.py
|   |   +-- database.py
|   +-- requirements.txt
+-- web/
|   +-- app/
|   +-- components/
|   +-- lib/
|   +-- package.json
+-- tests/
+-- AI_TECHNICAL_DEPTH.md
+-- README.md
```

## Backend Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload
```

Required backend environment variables:

```text
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
API_KEY=
```

## Frontend Setup

```bash
cd web
npm install
npm run dev
```

Required frontend environment variable:

```text
NEXT_PUBLIC_BACKEND_URL=https://olatunjitobi-verifyng-api.hf.space
```

## Testing

Run the backend test suite:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current automated coverage includes:

- AI template matching
- OCR edge cases
- ELA scoring
- Custom ML classifier
- Pipeline timeout handling
- Missing file and failed download handling
- Result endpoint contracts
- Manual trigger authorization
- Supabase update payloads

## Team

- **Olatunji Tobiloba** - AI pipeline, backend integration, deployment
- **Fisayo Obadina** - Frontend and result experience
- **Divine Aghulor** - Upload, Squad payment, webhook flow

## Demo Pitch

VerifyNG turns certificate verification into a payment-gated, AI-powered
workflow. Squad confirms payment, the AI pipeline analyzes the document, and the
user receives an explainable trust score with clear risk flags.

No payment. No verification. Squad is the gatekeeper.
