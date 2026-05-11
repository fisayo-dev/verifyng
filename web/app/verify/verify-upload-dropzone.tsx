'use client';

import { PhotoIcon } from "@heroicons/react/24/outline";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

const VerifyUploadDropzone = () => {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const [firstFile] = acceptedFiles;
    setSelectedFileName(firstFile?.name ?? null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/*": [],
      "application/pdf": [".pdf"],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`grid h-80 w-full cursor-pointer place-content-center rounded-2xl border p-20 text-center transition-colors md:w-3xl mx-auto ${
        isDragActive
          ? "border-dashed border-gray"
          : "border-gray/30 hover:border-gray"
      }`}
    >
      <input {...getInputProps()} />
      <div className="grid gap-4">
        <PhotoIcon className="mx-auto h-12 w-12 text-gray" />
        <div className="grid gap-2">
          <p className="text-base font-medium">
            {selectedFileName ?? "Click to upload or drag and drop"}
          </p>
          <p className="text-sm text-gray">
            Supports images and PDF files
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerifyUploadDropzone;
