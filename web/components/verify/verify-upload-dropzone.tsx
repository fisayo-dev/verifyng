'use client';

import Image from "next/image";
import dynamic from "next/dynamic";
import {
  ArrowsPointingOutIcon,
  PhotoIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";

const VerifyPdfPreview = dynamic(() => import("./verify-pdf-preview"), {
  ssr: false,
  loading: () => <p className="text-sm text-gray">Loading PDF preview...</p>,
});

const VerifyUploadDropzone = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const [firstFile] = acceptedFiles;
    setSelectedFile(firstFile ?? null);
    setIsPreviewOpen(false);
  }, []);

  const isImage = selectedFile?.type.startsWith("image/") ?? false;
  const isPdf = selectedFile?.type === "application/pdf";
  const hasPreview = isImage || isPdf;

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    multiple: false,
    noClick: hasPreview,
    accept: {
      "image/*": [],
      "application/pdf": [".pdf"],
    },
  });
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

  useEffect(() => {
    if (!isPreviewOpen) {
      return;
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsPreviewOpen(false);
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isPreviewOpen]);

  return (
    <>
      <div
        {...getRootProps()}
        className={`mx-auto grid h-100 w-full cursor-pointer overflow-hidden rounded-2xl border text-center transition-colors md:w-3xl ${
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
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                setIsPreviewOpen(true);
              }}
              className="relative flex min-h-0 items-center justify-center overflow-hidden rounded-xl bg-black/5 p-3"
            >
              <span className="absolute right-3 top-3 z-10 rounded-full bg-white/90 p-2 text-foreground shadow-sm">
                <ArrowsPointingOutIcon className="h-4 w-4" />
              </span>
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
                <div className="h-full w-full overflow-hidden">
                  <VerifyPdfPreview file={selectedFile} className="px-2 py-3" />
                </div>
              ) : null}
            </button>
            <div className="grid min-h-0 gap-2 px-1">
              <p className="truncate text-base font-medium">{selectedFile?.name}</p>
              <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-gray">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    setIsPreviewOpen(true);
                  }}
                  className="text-foreground underline underline-offset-4"
                >
                  Preview larger
                </button>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    open();
                  }}
                  className="underline underline-offset-4"
                >
                  Replace file
                </button>
              </div>
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
      {isPreviewOpen && selectedFile ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-5"
          onClick={() => setIsPreviewOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Expanded file preview"
        >
          <div
            className="grid h-[min(85vh,48rem)] w-full max-w-4xl grid-rows-[auto_minmax(0,1fr)] gap-4 rounded-3xl bg-background p-5 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between gap-4">
              <p className="truncate text-left text-lg font-semibold">
                {selectedFile.name}
              </p>
              <button
                type="button"
                onClick={() => setIsPreviewOpen(false)}
                className="rounded-full border border-gray/20 p-2 text-gray transition-colors hover:border-gray hover:text-foreground"
                aria-label="Close preview"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="relative min-h-0 overflow-hidden rounded-2xl bg-black/5 p-4">
              {isImage && imagePreviewUrl ? (
                <div className="relative h-full w-full">
                  <Image
                    src={imagePreviewUrl}
                    alt={selectedFile.name}
                    fill
                    unoptimized
                    className="object-contain"
                  />
                </div>
              ) : null}
              {isPdf ? (
                <div className="h-full w-full overflow-hidden">
                  <VerifyPdfPreview
                    file={selectedFile}
                    width={560}
                    className="px-4 py-2"
                  />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
};

export default VerifyUploadDropzone;
