import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { UploadCloud, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { ProtectedGate } from "@/components/ProtectedGate";
import { Navbar } from "@/components/Navbar";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";

export const Route = createFileRoute("/profile")({
  head: () => ({ meta: [{ title: "Profile — Job Scout" }] }),
  component: () => (
    <ProtectedGate>
      <ProfilePage />
    </ProtectedGate>
  ),
});

function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Please upload a PDF file");
      return;
    }
    setUploading(true);
    try {
      await api.uploadResume(file);
      if (user) setUser({ ...user, has_resume: true });
      toast.success("Resume uploaded");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      toast.error(msg);
    } finally {
      setUploading(false);
    }
  }

  const hasResume = !!user?.has_resume;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-[600px] px-6 py-10">
        <h1 className="text-[22px] font-semibold">Your Profile</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">{user?.email}</p>

        <div
          className="mt-8 rounded-[12px] p-10 text-center"
          style={{ border: "1px dashed #2a2a2a" }}
        >
          {uploading ? (
            <>
              <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary" />
              <p className="mt-3 text-sm text-muted-foreground">Uploading...</p>
            </>
          ) : hasResume ? (
            <>
              <CheckCircle2
                className="mx-auto h-10 w-10"
                style={{ color: "#22c55e" }}
              />
              <p className="mt-3 text-sm font-medium" style={{ color: "#22c55e" }}>
                Resume uploaded
              </p>
              <p className="mt-1 text-[12px] text-muted-foreground">
                Your jobs are being scored against your profile
              </p>
              <button
                onClick={() => inputRef.current?.click()}
                className="mt-5 rounded-md border border-border px-4 py-2 text-sm hover:border-primary"
              >
                Replace Resume
              </button>
            </>
          ) : (
            <>
              <UploadCloud className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium">Upload your resume PDF</p>
              <p className="mt-1 text-[12px] text-muted-foreground">
                Your resume text is used to score job relevance
              </p>
              <button
                onClick={() => inputRef.current?.click()}
                className="mt-5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Choose PDF file
              </button>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={onFile}
          />
        </div>
      </main>
    </div>
  );
}