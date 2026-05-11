'use client';

import { Document, Page, pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type VerifyPdfPreviewProps = {
  file: File;
  width?: number;
};

const VerifyPdfPreview = ({ file, width = 240 }: VerifyPdfPreviewProps) => {
  return (
    <Document
      file={file}
      loading={<p className="text-sm text-gray">Loading PDF preview...</p>}
      error={<p className="text-sm text-danger">Unable to preview this PDF.</p>}
    >
      <Page
        pageNumber={1}
        width={width}
        renderAnnotationLayer={false}
        renderTextLayer={false}
      />
    </Document>
  );
};

export default VerifyPdfPreview;
