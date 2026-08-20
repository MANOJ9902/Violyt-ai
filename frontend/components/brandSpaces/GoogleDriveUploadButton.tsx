"use client";

import { createContext, type ReactNode, useContext, useMemo, useState } from "react";
import axios from "axios";
import { Cloud, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import { apiClient } from "@/lib/api/client";


type GoogleDriveContextValue = {
    brandId?: string;
    disabled?: boolean;
};

type GoogleDriveOAuthMessage = {
    type?: string;
    status?: string;
    nonce?: string;
    brandId?: string;
    fileIds?: unknown;
    message?: string;
};

const GoogleDriveUploadContext = createContext<GoogleDriveContextValue>({});

export function BrandSpaceDriveUploadProvider({
    brandId,
    disabled,
    children,
}: GoogleDriveContextValue & { children: ReactNode }) {
    const value = useMemo(() => ({ brandId, disabled }), [brandId, disabled]);
    return <GoogleDriveUploadContext.Provider value={value}>{children}</GoogleDriveUploadContext.Provider>;
}

function messageFromError(error: unknown, fallback: string) {
    if (axios.isAxiosError(error)) {
        return String(error.response?.data?.detail || error.message || fallback);
    }
    return error instanceof Error ? error.message : fallback;
}

function apiOrigin() {
    return new URL(apiClient.defaults.baseURL || window.location.origin, window.location.origin).origin;
}

function fileNameFromResponse(response: { headers: unknown }, fallback: string) {
    const headers = response.headers as Record<string, string | undefined>;
    const driveName = headers["x-drive-file-name"];
    if (driveName) {
        return driveName.replaceAll("&quot;", '"').replaceAll("&amp;", "&");
    }
    const contentDisposition = headers["content-disposition"];
    const filenameMatch = contentDisposition?.match(/filename="?([^";]+)"?/i);
    return filenameMatch?.[1] || fallback;
}

function acceptsFormat(file: File, acceptedFormats: string) {
    const extension = file.name.includes(".") ? file.name.split(".").pop()?.toLowerCase() || "" : "";
    return acceptedFormats.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean).includes(extension);
}

function selectedFileIds(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return [];
    }
    return value.filter((fileId): fileId is string => typeof fileId === "string" && /^[A-Za-z0-9_-]{1,255}$/.test(fileId));
}

export function GoogleDriveUploadButton({
    acceptedFormats,
    onFiles,
    multiple = true,
    className,
}: {
    acceptedFormats: string;
    onFiles: (files: File[]) => void;
    multiple?: boolean;
    className?: string;
}) {
    const { brandId, disabled } = useContext(GoogleDriveUploadContext);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isImporting, setIsImporting] = useState(false);

    const waitForGooglePicker = (
        popup: Window,
        nonce: string,
    ) => new Promise<string[]>((resolve, reject) => {
        const expectedOrigin = apiOrigin();
        let completed = false;
        const timeout = window.setTimeout(() => complete(new Error("Google Drive selection timed out.")), 10 * 60 * 1000);
        const poll = window.setInterval(() => {
            if (popup.closed) {
                window.setTimeout(() => complete(new Error("Google Drive selection was cancelled.")), 250);
            }
        }, 400);
        const receiveMessage = (event: MessageEvent) => {
            const payload = event.data as GoogleDriveOAuthMessage;
            if (event.origin !== expectedOrigin || payload?.type !== "violyt:google-drive-oauth" || payload.nonce !== nonce) {
                return;
            }
            if (payload.status === "picked" && payload.brandId === brandId) {
                complete(undefined, selectedFileIds(payload.fileIds));
                return;
            }
            complete(new Error(payload.message || "Google Drive selection was cancelled."));
        };
        const complete = (error?: Error, fileIds: string[] = []) => {
            if (completed) {
                return;
            }
            completed = true;
            window.clearTimeout(timeout);
            window.clearInterval(poll);
            window.removeEventListener("message", receiveMessage);
            if (!popup.closed) {
                popup.close();
            }
            if (error) {
                reject(error);
            } else {
                resolve(fileIds);
            }
        };
        window.addEventListener("message", receiveMessage);
    });

    const importSelectedFiles = async (fileIds: string[]) => {
        if (!brandId || !fileIds.length) {
            return;
        }
        setIsImporting(true);
        try {
            const results = await Promise.allSettled(
                fileIds.map(async (fileId, index) => {
                    const response = await apiClient.get<Blob>(
                        `/api/v1/brands/${brandId}/google-drive/files/${encodeURIComponent(fileId)}/download`,
                        { responseType: "blob" },
                    );
                    return new File([response.data], fileNameFromResponse(response, `google-drive-file-${index + 1}`), {
                        type: response.data.type || "application/octet-stream",
                    });
                }),
            );
            const downloaded = results
                .filter((result): result is PromiseFulfilledResult<File> => result.status === "fulfilled")
                .map((result) => result.value);
            const supported = downloaded.filter((file) => acceptsFormat(file, acceptedFormats));
            const skipped = fileIds.length - supported.length;
            if (!supported.length) {
                throw new Error("None of the selected Google Drive files match this upload section's accepted formats.");
            }
            onFiles(multiple ? supported : supported.slice(0, 1));
            toast({ title: "Google Drive files added", description: "The files were added to this upload section and will follow the normal upload workflow.", variant: "success" });
            if (skipped) {
                toast({ title: "Some Drive files were skipped", description: `${skipped} selected file(s) could not be imported because they are unsupported or unavailable.`, variant: "warning" });
            }
        } catch (error) {
            toast({ title: "Google Drive import failed", description: messageFromError(error, "Unable to import the selected Drive files."), variant: "destructive" });
        } finally {
            setIsImporting(false);
        }
    };

    const openGooglePicker = async () => {
        if (!brandId) {
            toast({ title: "Save a draft first", description: "Create or save the Brand Space before importing from Google Drive.", variant: "warning" });
            return;
        }
        setIsConnecting(true);
        try {
            const response = await apiClient.post<{ authorization_url: string; nonce: string }>(
                `/api/v1/brands/${brandId}/google-drive/authorize`,
                undefined,
                { params: { allow_multiple: multiple } },
            );
            const popup = window.open(response.data.authorization_url, "violyt-google-drive", "popup=yes,width=960,height=720");
            if (!popup) {
                throw new Error("Your browser blocked the Google Drive selection window.");
            }
            const fileIds = await waitForGooglePicker(popup, response.data.nonce);
            if (!fileIds.length) {
                throw new Error("No Google Drive files were selected.");
            }
            await importSelectedFiles(fileIds);
        } catch (error) {
            toast({ title: "Google Drive selection cancelled", description: messageFromError(error, "Unable to select files from Google Drive."), variant: "warning" });
        } finally {
            setIsConnecting(false);
        }
    };

    return (
        <Button
            type="button"
            variant="outline"
            disabled={Boolean(disabled) || isConnecting || isImporting}
            onClick={() => void openGooglePicker()}
            className={className || "flex h-20 w-60 flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#D8E2EC] bg-white text-sm text-slate-600 hover:border-primary/40 hover:bg-slate-50"}
        >
            {isConnecting || isImporting ? <Loader2 className="mb-2 h-4 w-4 animate-spin" /> : <Cloud className="mb-2 h-4 w-4" />}
            Upload from Google Drive
        </Button>
    );
}