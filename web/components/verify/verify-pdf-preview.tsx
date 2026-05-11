'use client';

import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type VerifyPdfPreviewProps = {
  file: File;
  width?: number;
  className?: string;
};

const VerifyPdfPreview = ({
  file,
  width = 240,
  className = "",
}: VerifyPdfPreviewProps) => {
  const [numPages, setNumPages] = useState(0);

  return (
    <div className={`h-full w-full overflow-auto ${className}`}>
      <Document
        file={file}
        onLoadSuccess={({ numPages: loadedPages }) => setNumPages(loadedPages)}
        loading={<p className="text-sm text-gray">Loading PDF preview...</p>}
        error={<p className="text-sm text-danger">Unable to preview this PDF.</p>}
        className="grid min-w-full justify-items-center gap-4"
      >
        {Array.from({ length: numPages }, (_, index) => (
          <Page
            key={`pdf-page-${index + 1}`}
            pageNumber={index + 1}
            width={width}
            renderAnnotationLayer={false}
            renderTextLayer={false}
          />
        ))}
      </Document>
    </div>
  );
};

export default VerifyPdfPreview;
