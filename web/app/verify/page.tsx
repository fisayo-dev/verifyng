import { DocumentIcon } from "@heroicons/react/24/outline";
import VerifyUploadDropzone from "./verify-upload-dropzone";

const VerifyPage = () => {
  return (
    <div className="w-full h-100 place-content-center text-center mb-20">
      <div className="app-container grid gap-6">
        <div className="flex flex-col gap-3">
          <h2 className="text-4xl font-extrabold">Upload Certificate</h2>
          <p className="text-sm px-5 py-2 rounded-full bg-gray/20 w-fit mx-auto flex items-center gap-2">
            <DocumentIcon className="w-5 h-5" />
            <span>Image/PDF</span>
          </p>
        </div>
        <VerifyUploadDropzone />
      </div>
    </div>
  );
};

export default VerifyPage;
