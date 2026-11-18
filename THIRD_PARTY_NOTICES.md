# Third-party notices

This repository holds only the API code (MIT, see `LICENSE`). It contains no model
weights and no copy of iApp's runtime. `scripts/install.sh` downloads them into
`models/OpenThai2.1-OCR-Text-20261118/` (git-ignored), where they keep their own licence and
`NOTICE` file.

## iapp/OpenThai2.1-OCR-Text-20261118 (model and runtime)

- Source: https://huggingface.co/iapp/OpenThai2.1-OCR-Text-20261118
  (revision `7092cacf4561679ff9ed19de6821faeb9c96d894`)
- Authors: iApp Technology Co., Ltd. This project did not create or train the model.
- Licence: Apache License 2.0 — http://www.apache.org/licenses/LICENSE-2.0
- Files used (runtime 2.2.0): `det.onnx`, `det.yml`, `rec.onnx`, `rec2.onnx`, `rec_dict.txt`, `config.json`,
  `runtime/__init__.py`, `runtime/line_engine.py`, `runtime/thai_norm.py`, `runtime/dewarp.py`, `NOTICE`.
  `pytorch/rec_weights.pt` (fine-tuning weights) is not downloaded.
- The runtime is imported unchanged under an isolated package namespace and its `LineOCR` is called,
  as in iApp's guide: https://iapp.co.th/en/blog/openthai2p0-ocr-how-to-run

The model's `NOTICE` reads:

> This model includes or is derived from the following Apache-2.0 licensed work:
> PP-OCRv6_tiny_det, PP-OCRv6_tiny_rec, th_PP-OCRv5_mobile_rec (character list),
> Copyright (c) PaddlePaddle Authors, https://huggingface.co/PaddlePaddle,
> Licensed under the Apache License, Version 2.0.
> det.onnx is PP-OCRv6_tiny_det as distributed. rec.onnx is a fine-tune of
> PP-OCRv6_tiny_rec with a replaced Thai classifier, trained by iApp.

## PaddlePaddle PP-OCRv6-tiny (detector, and base of the recognizer)

- Source: https://huggingface.co/PaddlePaddle
- Copyright (c) PaddlePaddle Authors
- Licence: Apache License 2.0

## Notes

- If you redistribute the model files (for example in a Docker image), include the
  Apache-2.0 licence text and the model's `NOTICE` unchanged.
- Python libraries (FastAPI, Uvicorn, ONNX Runtime, OpenCV, pyclipper, NumPy, Pillow,
  pypdfium2, huggingface_hub and others) are installed from PyPI under their own licences.
