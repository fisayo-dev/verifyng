'use client';

import Image from "next/image";
import { PhotoIcon } from "@heroicons/react/24/outline";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { useDropzone } from "react-dropzone";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const VerifyUploadDropzone = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const [firstFile] = acceptedFiles;
    setSelectedFile(firstFile ?? null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/*": [],
      "application/pdf": [".pdf"],
    },
  });

  const isImage = selectedFile?.type.startsWith("image/") ?? false;
  const isPdf = selectedFile?.type === "application/pdf";
  const hasPreview = isImage || isPdf;
  const imagePreviewUrl = useMemo(() => {
    if (!selectedFile || !isImage) {
      return null;
    }

    return URL.createObjectURL(selectedFile);
  }, [isImage, selectedFile]);

  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  return (
    <div
      {...getRootProps()}
      className={`mx-auto grid h-80 w-full cursor-pointer overflow-hidden rounded-2xl border text-center transition-colors md:w-3xl ${
        isDragActive
          ? "border-dashed border-gray"
          : "border-gray/30 hover:border-gray"
      } ${
        hasPreview ? "place-items-stretch p-4" : "place-content-center p-20"
      }`}
    >
      <input {...getInputProps()} />
      {hasPreview ? (
        <div className="grid h-full min-h-0 grid-rows-[minmax(0,1fr)_auto] gap-3">
          <div className="relative flex min-h-0 items-center justify-center overflow-hidden rounded-xl bg-black/5 p-3">
            {isImage && imagePreviewUrl ? (
              <div className="relative h-full w-full">
                <Image
                  src={imagePreviewUrl}
                  alt={selectedFile?.name ?? "Selected upload preview"}
                  fill
                  unoptimized
                  className="object-contain"
                />
              </div>
            ) : null}
            {isPdf && selectedFile ? (
              <div className="flex h-full w-full items-center justify-center overflow-hidden">
                <Document
                  file={selectedFile}
                  loading={
                    <p className="text-sm text-gray">Loading PDF preview...</p>
                  }
                >
                  <Page
                    pageNumber={1}
                    width={Math.min(280, typeof window === "undefined" ? 280 : window.innerWidth - 96)}
                    renderAnnotationLayer={false}
                    renderTextLayer={false}
                  />
                </Document>
              </div>
            ) : null}
          </div>
          <div className="grid min-h-0 gap-1 px-1">
            <p className="truncate text-base font-medium">{selectedFile?.name}</p>
            <p className="text-sm text-gray">
              Click or drop another file to replace it
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          <PhotoIcon className="mx-auto h-12 w-12 text-gray" />
          <div className="grid gap-2">
            <p className="text-base font-medium">
              Click to upload or drag and drop
            </p>
            <p className="text-sm text-gray">
              Supports images and PDF files
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default VerifyUploadDropzone;
