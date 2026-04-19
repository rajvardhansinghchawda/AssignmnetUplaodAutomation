import { useState, useRef } from 'react';
import { UploadCloud, FileText } from 'lucide-react';

const FileDropZone = ({ onFileSelect }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsHovered(true);
  };

  const handleDragLeave = () => {
    setIsHovered(false);
  };

  const handleSetFile = (file) => {
    setSelectedFile(file);
    if (onFileSelect) onFileSelect(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsHovered(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSetFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold mb-2 text-on_surface flex items-center gap-2">
        <UploadCloud className="w-4 h-4 text-primary" />
        Assignment File
      </h3>

      <div
        className={`w-full border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer ${isHovered
            ? 'border-primary bg-primary_fixed text-on_primary_fixed_variant'
            : 'border-outline_variant bg-surface_container_highest text-on_surface_variant hover:border-primary hover:bg-surface_container_low'
          }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.doc,.docx,.zip"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center">
            <FileText className="w-10 h-10 mb-2 text-primary" />
            <p className="font-medium text-sm text-on_surface text-center">
              Selected: {selectedFile.name}
            </p>
            <p className="text-xs mt-1 text-on_surface_variant">
              ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <UploadCloud className="w-10 h-10 mb-3 opacity-50" />
            <p className="text-sm font-medium mb-1">
              📄 Drop PDF / file here, or <span className="text-primary hover:underline">Browse</span>
            </p>
            <p className="text-xs opacity-70">Supports .pdf, .docx, .zip up to 10MB</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileDropZone;
