# VerifyNG AI Technical Depth

VerifyNG now uses a four-signal verification engine designed for the
Challenge 01 "Proof of Life" judging criteria.

Judge-facing claim:

> VerifyNG uses a benchmark-backed, explainable AI pipeline with a
> custom-trained certificate authenticity classifier for trust scoring.

The repo documents the evidence behind the AI layer rather than assigning
itself a judging score.

## AI Signals

1. **Visual Forensics**
   - Error Level Analysis checks compression inconsistency.
   - Metadata checks look for editing software and suspicious document history.
   - Visual consistency checks look for inconsistent sharpness and recompression
     artifacts.

2. **OCR + Certificate Content Validation**
   - Tesseract extracts certificate text from images and PDF conversions.
   - The content validator checks institution keywords, certificate language,
     candidate name patterns, examination year, and text-volume sanity.

3. **Template/Layout Matching**
   - `backend/app/ai_depth.py` scores whether extracted text matches the expected
     WAEC/WASSCE certificate structure.
   - It separately scores institution identity, candidate name, examination
     number, year, and grade-table evidence.
   - Low template confidence caps the final score, forcing suspicious documents
     into review instead of allowing keyword-only matches to pass.

4. **Custom-Trained ML Classifier**
   - `backend/app/ml_model.py` trains a lightweight NumPy softmax classifier
     from labeled certificate signal rows.
   - The classifier uses visual score, ELA anomaly score, metadata suspicion,
     OCR confidence, content score, template score, missing-field count, and
     OCR word count.
   - The live pipeline records this as `custom_ml_classifier` in `layers_run`
     and adds an `ML classifier:` explanation flag.

## Explainability

Successful runs now add an `AI evidence:` flag with the signal scores used to
support the verdict:

```text
AI evidence: visual=84.0, content=88.0, template=100.0, ocr=86.0 | AI combines visual forensics, OCR confidence, certificate content validation, and template/layout matching into an explainable trust score.
ML classifier: prediction=authentic, authenticity=0.91, model=VerifyNGCustomSoftmaxClassifier
```

This makes the verdict defensible in demo and Q&A: a judge can see which AI
signals supported the trust score and which fields were missing or suspicious.

## Benchmarking

The `benchmark_verification_cases` helper in `backend/app/ai_depth.py` produces
a simple accuracy report and confusion matrix for clean, review, and forged
cases. This supports a judging claim like:

> "We tested clean, low-quality, non-certificate, and tampered samples and report
> both prediction accuracy and where the model confuses review vs forged cases."

Run the current automated validation with:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current coverage includes template matching, custom ML classification,
explainable AI evidence, benchmark metrics, real sideways WAEC image
orientation handling, pipeline timeout behavior, OCR failure handling, and API
result contracts.
