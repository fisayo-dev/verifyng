"use client";

import Link from "next/link";
import { useState } from "react";
import { DocumentIcon, SparklesIcon } from "@heroicons/react/24/outline";
import Button from "@/components/general/button";
import VerifyUploadDropzone from "@/components/verify/verify-upload-dropzone";

const demoJobId = process.env.NEXT_PUBLIC_TEST_JOB_ID?.trim() ?? "";

const VerifyWorkspace = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  return (
    <div className="app-container grid gap-8 pb-20">
      <div className="grid gap-3 text-center">
        <h2 className="text-4xl font-extrabold">Upload Certificate</h2>
        <p className="inline-flex mx-auto w-fit items-center gap-2 rounded-full border border-primary/15 bg-white px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/5">
          <DocumentIcon className="h-5 w-5" />
          <span>Image/PDF</span>
        </p>
      </div>

      <div className="grid gap-6 ">
        <section className="grid gap-5 rounded-4xl border border-foreground/8 bg-white p-6 shadow-[0_20px_60px_-48px_rgba(23,23,23,0.35)]">
          <VerifyUploadDropzone onFileSelect={setSelectedFile} />
          

          {demoJobId ? (
            <Link
              href={`/results/${encodeURIComponent(demoJobId)}`}
              className="inline-flex mx-auto w-fit items-center justify-center rounded-full border border-primary/20 px-5 py-3 font-medium text-primary transition-colors hover:bg-primary/10"
            >
              Open demo result
            </Link>
          ) : null}
        </section>
      </div>
    </div>
  );
};

export default VerifyWorkspace;
