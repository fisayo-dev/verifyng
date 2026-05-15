# VerifyNG

AI-powered academic certificate verification for Nigerian employers, schools,
recruiters, and institutions.

VerifyNG was built by **Team Finsense** for **Squad Hackathon 3.0,
Challenge 01: Proof of Life**. The product helps a user upload an academic
document, pay a verification fee through Squad, and receive an explainable AI
trust score with a verdict, confidence level, and risk flags.

## Live Product

- Frontend: https://verifyng-three.vercel.app
- Backend API: https://olatunjitobi-verifyng-api.hf.space
- Health check: https://olatunjitobi-verifyng-api.hf.space/health
- Repository: https://github.com/fisayo-dev/verifyng

## Why This Exists

The hackathon brief asks teams to build an AI system that helps people,
businesses, or institutions verify, trust, or authenticate something where fraud
or opacity is common. VerifyNG chooses the **education** domain: fake academic
certificates, exam results, and altered scans.

Manual certificate verification is slow, expensive, and difficult to scale.
Employers may need to contact institutions one by one, while applicants and HR
teams wait days for a decision. VerifyNG provides a fast first-pass screening
layer: it does not replace the institution of record, but it helps organizations
identify high-risk documents before they spend time and money on manual review.

## The Core User Journey

1. A user opens the PWA and uploads a certificate or result image.
2. The backend creates a verification job and starts a Squad checkout.
3. The user pays the verification fee through Squad.
4. Squad redirects/calls back to the backend with the transaction reference.
5. The backend confirms the payment, uploads the file to Supabase Storage, and
   triggers the AI pipeline.
6. The AI engine runs visual forensics, OCR/content validation,
   template matching, and a custom ML classifier.
7. The frontend polls the result endpoint until the status is `COMPLETE` or
   `FAILED`.
8. The user sees a trust score, verdict, confidence level, and explanation
   flags.

## Challenge Criteria Fit

| Squad Hackathon Criterion | Weight | How VerifyNG Addresses It |
| --- | ---: | --- |
| AI Technical Depth | 30% | Four-layer verification engine: visual forensics, OCR/content validation, template/layout matching, and a custom NumPy ML classifier. |
| Squad API Integration | 20% | Squad checkout is the gatekeeper for verification. The AI does not run until payment is confirmed. |
| Problem Relevance and Domain Insight | 15% | Targets certificate/result fraud in Nigerian hiring and education workflows, a direct match for the guide's education verification domain. |
| Solution Design and Scalability | 15% | Stateless FastAPI backend, Supabase persistence/storage, Vercel PWA, Hugging Face deployment, idempotent payment handling, timeout-protected AI jobs. |
| Presentation and Demo | 15% | Live PWA and live API demonstrate upload, payment, callback, polling, and result display end to end. |
| Impact Potential Bonus | 10% | Pay-per-check model can expand into employer subscriptions, university partnerships, NYSC screening, and API verification for HR platforms. |

## Four Pillars

| Pillar | VerifyNG Implementation |
| --- | --- |
| AI Automation | The system automatically analyzes visual tampering, extracted text, certificate structure, and ML authenticity signals after payment. |
| Squad APIs | Squad payment initiation and callback/webhook flow sit in the critical path. No payment means no AI run. |
| Use of Data | The trust score is built from OCR confidence, ELA anomaly score, template fields, content validation, metadata signals, and classifier probability. |
| Financial Innovation | Certificate verification becomes a low-cost, payment-gated service that can support pay-per-use, subscriptions, and institutional bulk verification. |

## AI Verification Engine

VerifyNG is not a chatbot wrapper. The AI layer performs the verification work.

### 1. Visual Forensics

- Error Level Analysis checks compression inconsistencies that may indicate
  edits.
- Metadata checks detect missing or suspicious document metadata.
- Visual consistency scoring flags sharpness and pixel-level differences.

### 2. OCR and Content Validation

- Tesseract OCR extracts text from uploaded scans or images.
- The backend checks institution keywords, certificate language, candidate name
  patterns, year signals, and exam/result terminology.
- Low-quality scans still produce an interpretable outcome rather than silently
  failing.

### 3. Template and Layout Matching

- The template layer checks whether the OCR output resembles expected WAEC or
  certificate result structure.
- It scores expected fields such as candidate name, examination number, year,
  institution label, and grade-table evidence.

### 4. Custom ML Classifier

- A lightweight NumPy softmax classifier combines engineered features from the
  previous layers.
- Features include visual score, content score, template score, OCR confidence,
  ELA anomaly score, metadata suspicion, missing field count, and word count.

For deeper AI detail, see [AI_TECHNICAL_DEPTH.md](AI_TECHNICAL_DEPTH.md).

## Explainable Output

Every completed verification returns:

- `trust_score`: 0-100 score
- `verdict`: `LIKELY AUTHENTIC`, `REQUIRES MANUAL REVIEW`, `SUSPICIOUS`, or
  `LIKELY FORGED`
- `confidence`: `HIGH`, `MEDIUM`, or `LOW`
- `flags`: human-readable reasons for the score
- `layers_run`: AI layers that successfully executed

This matters for responsible AI. The system does not claim perfect truth. It
shows evidence, flags uncertainty, and supports manual review when confidence is
not high enough.

## Squad Integration

Squad is central to the product, not a checkbox.

### Payment Flow

1. `POST /api/verify` creates a verification job.
2. The backend calls Squad transaction initiation with:
   - amount in kobo
   - customer email
   - transaction reference: `VNG-{verification_id}`
   - callback URL
   - verification metadata
3. The frontend opens the returned `checkout_url`.
4. Squad confirms payment through the callback/webhook path.
5. The backend marks the payment confirmed and starts AI analysis.

### Why It Is Meaningful

- Squad controls access to the paid verification workflow.
- The business model depends on Squad, because verification compute runs only
  after payment.
- The same architecture can support B2B employer subscriptions, bulk checks, and
  virtual-account based institutional workflows.

## API Contract

The frontend depends on this schema. Do not change these fields without
coordinating with the frontend.

### `POST /api/verify`

Request:

```http
Content-Type: multipart/form-data
file=<certificate image or PDF>
```

Response:

```json
{
  "job_id": "uuid",
  "checkout_url": "https://sandbox-pay.squadco.com/...",
  "status": "PENDING_PAYMENT",
  "poll_url": "https://olatunjitobi-verifyng-api.hf.space/api/result/{job_id}"
}
```

### `GET /api/result/{verification_id}`

Pending payment:

```json
{
  "verification_id": "uuid",
  "status": "PENDING_PAYMENT",
  "message": "Awaiting payment confirmation"
}
```

Processing:

```json
{
  "verification_id": "uuid",
  "status": "PROCESSING",
  "message": "AI is analyzing your certificate..."
}
```

Complete:

```json
{
  "verification_id": "uuid",
  "status": "COMPLETE",
  "trust_score": 87,
  "verdict": "LIKELY AUTHENTIC",
  "flags": [],
  "confidence": "HIGH",
  "layers_run": [
    "visual_forensics",
    "content_validation",
    "template_layout_matching",
    "custom_ml_classifier"
  ],
  "report_url": null
}
```

Failed:

```json
{
  "verification_id": "uuid",
  "status": "FAILED",
  "message": "Verification failed. Please contact support.",
  "refund_eligible": true
}
```

### `GET /api/payment/callback?reference=VNG-{verification_id}`

Handles the browser callback after Squad sandbox payment and redirects the user
to:

```text
https://verifyng-three.vercel.app/results/{verification_id}
```

### `POST /api/webhook/squad`

Handles server-side Squad webhook payloads and queues verification analysis.

### `POST /api/trigger/{verification_id}`

Manual testing endpoint. Requires:

```http
X-API-Key: <API_KEY>
```

This endpoint is for integration testing only. The demo flow should use Squad
payment/callback.

## System Architecture

```text
User
  -> VerifyNG PWA on Vercel
  -> FastAPI backend on Hugging Face Spaces
  -> Squad checkout
  -> Squad callback/webhook
  -> Supabase database + storage
  -> AI pipeline
  -> /api/result polling
  -> Result UI
```

### Production Design Choices

- **Failure-first design:** failed downloads, missing files, timeouts, and bad
  IDs resolve to controlled statuses instead of hanging forever.
- **Stateless API:** FastAPI stores state in Supabase, so the app process can be
  restarted without losing jobs.
- **Idempotency:** payment records are keyed by Squad reference to avoid double
  processing.
- **Backpressure:** AI pipeline has a 90-second timeout to protect demo/runtime
  stability.
- **Security:** API keys and Squad keys are environment secrets, not frontend
  code.
- **Maintainability:** endpoint contracts are tested and documented.
- **Observability:** backend logs show payment initiation, callback, file upload,
  pipeline start, and pipeline completion/failure.

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Axios
- React Dropzone
- React PDF
- PWA manifest/icons
- Vercel

### Backend

- FastAPI
- Uvicorn
- Supabase database
- Supabase Storage
- Hugging Face Spaces
- Squad API
- Tesseract OCR
- OpenCV
- Pillow
- NumPy

## Repository Structure

```text
verifyng/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- verifications.py
|   |   |-- payments.py
|   |   |-- result.py
|   |   |-- webhook.py
|   |   |-- pipeline.py
|   |   |-- ocr.py
|   |   |-- ela.py
|   |   |-- content_validator.py
|   |   |-- ai_depth.py
|   |   |-- ml_model.py
|   |   |-- database.py
|   |-- requirements.txt
|   |-- Dockerfile
|-- web/
|   |-- app/
|   |-- components/
|   |-- lib/
|   |-- types/
|   |-- public/
|   |-- package.json
|-- tests/
|-- AI_TECHNICAL_DEPTH.md
|-- README.md
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
SUPABASE_STORAGE_BUCKET=certificates
SQUAD_API_URL=https://sandbox-api-d.squadco.com
SQUAD_API_KEY=
WEBHOOK_URL=https://olatunjitobi-verifyng-api.hf.space/api/payment/callback
FRONTEND_URL=https://verifyng-three.vercel.app
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
NEXT_PUBLIC_BACKEND_URL=https://olatunjitobi-verifyng-api.hf.space/api
```

## Testing

Run backend tests:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current backend coverage includes:

- `/api/verify` response contract
- Squad amount in kobo
- Squad checkout response parsing
- payment callback queueing
- result endpoint states
- manual trigger authorization
- Supabase missing-row handling
- storage signed URL handling
- duplicate upload prevention
- AI pipeline download failures
- AI pipeline timeout handling
- OCR and template matching
- custom ML classifier behavior

Run frontend checks:

```bash
cd web
npm install
npm run lint
npm run build
```

## Demo Script

Use this flow for judges:

1. Open the PWA.
2. Upload a certificate/result image.
3. Click verify.
4. Show Squad checkout.
5. Complete payment in Squad sandbox.
6. Return to the results page.
7. Explain the AI layers while the result is processing.
8. Show the final trust score, verdict, confidence, flags, and layers run.
9. Run a second upload with a suspicious/fake document to show score contrast.

The strongest demo moment is the contrast:

```text
Clean certificate      -> higher score -> LIKELY AUTHENTIC / manual review
Tampered certificate   -> lower score  -> SUSPICIOUS / LIKELY FORGED
```

## Business Model

VerifyNG can start as a pay-per-check verification service and grow into a B2B
verification infrastructure product.

| Segment | Offer | Revenue Path |
| --- | --- | --- |
| Individuals and small employers | Single verification | N500 per check |
| SMEs and recruiters | Monthly verification bundle | Subscription |
| Universities and exam bodies | Bulk verification dashboard/API | Institutional contract |
| HR platforms | Verification API | Usage-based API pricing |

Every paid verification can flow through Squad.

## Responsible AI and Privacy

- VerifyNG gives a risk score, not an absolute legal declaration.
- Low confidence or suspicious outputs should be manually reviewed.
- Uploaded documents are used for the requested verification workflow.
- Secrets stay in backend/Hugging Face/Supabase environment variables.
- The system is designed to fail closed: if analysis cannot complete, the job is
  marked `FAILED` and the frontend can show a refund/support path.

## Team

- **Olatunji Tobiloba** - AI pipeline, backend, Supabase, Hugging Face deployment
- **Fisayo Obadina** - PWA frontend, upload flow, result experience
- **Divine Aghulor** - Squad API integration, payment callback/webhook flow

## Pitch Summary

VerifyNG turns certificate verification into a fast, payment-gated AI workflow.
Squad powers the transaction layer, FastAPI coordinates the verification job,
Supabase stores the state and uploaded file, and the AI pipeline produces an
explainable trust score. The result is a live product that fits the Proof of
Life challenge: it verifies documents where fraud is common, uses AI as the
core trust engine, integrates Squad as a necessary part of the workflow, and can
scale into a real verification business.

No payment. No verification. Squad is the gatekeeper.
